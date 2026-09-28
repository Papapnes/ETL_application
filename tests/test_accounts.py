"""Identical account contract against SQLite and an explicit disposable PostgreSQL DB."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event, Lock
from uuid import uuid4

import pytest

from accounts.service import HASHER, AccountError, Accounts, token_hash

PASSWORD = "Synthetic-test-password-2026"


def register(service, email="client@example.com"):
    service.register("Test Client", email, PASSWORD, client=email)
    return service.login(email, PASSWORD, client=email)


def admin(service):
    service.bootstrap_admin("Test Admin", "admin@example.com", PASSWORD)
    return service.login("admin@example.com", PASSWORD)


def fake_etl(monkeypatch):
    monkeypatch.setattr("accounts.service.run", lambda *args: {"report": {}})


def test_registration_login_logout_and_persistence(account_service):
    service = account_service
    token = register(service, "Client@Example.com")
    user = service.identity(token)
    assert user["role"] == "FREE"
    assert user["email"] == "client@example.com"
    assert service.quota(token)["limit"] == 5
    with service.connection() as db:
        row = db.execute("SELECT * FROM users WHERE user_id=?", (user["user_id"],)).fetchone()
        assert row["password_hash"].startswith("$argon2")
        assert HASHER.verify(row["password_hash"], PASSWORD)
        session = db.execute("SELECT * FROM sessions").fetchone()
        assert session["token_hash"] == token_hash(token) and session["token_hash"] != token
    restarted = Accounts(service.database.config)
    assert restarted.identity(token)["user_id"] == user["user_id"]
    restarted.logout(token)
    with pytest.raises(AccountError):
        service.identity(token)


def test_wrong_credentials_and_server_admin_gate(account_service):
    service = account_service
    free = register(service)
    for email, password in [("client@example.com", "wrong"), ("missing@example.com", PASSWORD)]:
        with pytest.raises(AccountError, match="Identifiants incorrects"):
            service.login(email, password)
    with pytest.raises(AccountError, match="administrateur"):
        service.admin_data(free)
    with pytest.raises(AccountError):
        service.update_user(free, service.identity(free)["user_id"], "ADMIN", "ACTIVE")
    token = admin(service)
    assert service.identity(token)["role"] == "ADMIN"
    assert len(service.admin_data(token)["users"]) == 2


def test_roles_disable_and_last_admin(account_service):
    service = account_service
    owner = admin(service)
    token = register(service)
    uid = service.identity(token)["user_id"]
    service.update_user(owner, uid, "PRO", "ACTIVE")
    assert service.identity(token)["role"] == "PRO"
    assert service.quota(token)["limit"] == 50
    service.update_user(owner, uid, "PRO", "ACTIVE", 7)
    assert service.quota(token)["limit"] == 7
    service.update_user(owner, uid, "FREE", "DISABLED")
    with pytest.raises(AccountError):
        service.identity(token)
    with pytest.raises(AccountError):
        service.login("client@example.com", PASSWORD)
    with pytest.raises(AccountError, match="dernier administrateur"):
        service.update_user(owner, service.identity(owner)["user_id"], "FREE", "ACTIVE")


def test_password_reset_revokes_sessions_and_is_single_use(account_service):
    service = account_service
    old_session = register(service)
    messages = []
    service.request_password_reset("client@example.com", lambda *args: messages.append(args))
    recipient, code = messages[0]
    assert recipient == "client@example.com"
    with service.connection() as db:
        row = db.execute("SELECT token_hash FROM password_resets").fetchone()
        assert row["token_hash"] == token_hash(code)
    service.reset_password(code, PASSWORD + "-new")
    with pytest.raises(AccountError):
        service.identity(old_session)
    with pytest.raises(AccountError):
        service.reset_password(code, PASSWORD)
    with pytest.raises(AccountError):
        service.login(recipient, PASSWORD)
    assert service.identity(service.login(recipient, PASSWORD + "-new"))["email"] == recipient


def test_free_quota_failed_runs_duplicate_ids_and_admin_unlimited(account_service, monkeypatch):
    service = account_service
    token = register(service)
    owner = admin(service)
    failed_id = str(uuid4())

    def fail(*args):
        raise ValueError("Synthetic ETL error")

    monkeypatch.setattr("accounts.service.run", fail)
    with pytest.raises(ValueError):
        service.execute_etl(token, failed_id, [], {})
    assert service.quota(token)["used"] == 0
    assert service.quota(token)["pending"] == 0
    fake_etl(monkeypatch)
    with pytest.raises(AccountError, match="déjà"):
        service.execute_etl(token, failed_id, [], {})
    execution = str(uuid4())
    service.execute_etl(token, execution, [], {})
    with pytest.raises(AccountError, match="déjà"):
        service.execute_etl(token, execution, [], {})
    for _ in range(4):
        service.execute_etl(token, str(uuid4()), [], {})
    with pytest.raises(AccountError, match="Quota"):
        service.execute_etl(token, str(uuid4()), [], {})
    for _ in range(7):
        service.execute_etl(owner, str(uuid4()), [], {})
    assert service.quota(owner)["remaining"] is None
    assert service.quota(owner)["used"] == 7


def test_toronto_midnight_resets_counts(account_service, monkeypatch):
    service = account_service
    service.clock = lambda: datetime(2026, 3, 8, 4, 59, tzinfo=timezone.utc)
    token = register(service)
    fake_etl(monkeypatch)
    service.execute_etl(token, str(uuid4()), [], {})
    assert service.quota(token)["date"] == "2026-03-07"
    service.clock = lambda: datetime(2026, 3, 8, 5, 1, tzinfo=timezone.utc)
    assert service.quota(token)["used"] == 0
    assert service.quota(token)["remaining"] == 5
    assert service.quota(token)["next_reset"].endswith("-04:00")


def test_concurrent_requests_cannot_exceed_free_quota(account_service, monkeypatch):
    service = account_service
    token = register(service)
    release, full = Event(), Event()
    mutex = Lock()
    count = 0

    def slow_etl(*args):
        nonlocal count
        with mutex:
            count += 1
            if count == 5:
                full.set()
        assert release.wait(20)
        return {"report": {}}

    monkeypatch.setattr("accounts.service.run", slow_etl)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(service.execute_etl, token, str(uuid4()), [], {}) for _ in range(8)]
        try:
            assert full.wait(15)
            assert service.quota(token)["pending"] == 5
        finally:
            release.set()
        successes = failures = 0
        for future in futures:
            try:
                future.result(timeout=20)
                successes += 1
            except AccountError:
                failures += 1
    assert (successes, failures) == (5, 3)
    assert service.quota(token)["used"] == 5


def test_user_sessions_and_usage_are_isolated(account_service, monkeypatch):
    service = account_service
    alice, bob = register(service, "alice@example.com"), register(service, "bob@example.com")
    fake_etl(monkeypatch)
    service.execute_etl(alice, str(uuid4()), [], {})
    assert service.quota(alice)["used"] == 1
    assert service.quota(bob)["used"] == 0
    service.logout(alice)
    assert service.identity(bob)["email"] == "bob@example.com"
    with pytest.raises(AccountError):
        service.identity(alice)
