import os
from dataclasses import replace

import pytest

from accounts.config import DatabaseConfig
from accounts.database import Database
from accounts.errors import DatabaseError
from accounts.migrate import USER_COLUMNS, import_admin, migrate_schema
from accounts.service import AccountError, Accounts
from tests.test_accounts import PASSWORD


def migration_config(service):
    if service.database.config.backend != "postgresql":
        pytest.skip("PostgreSQL migration contract")
    return DatabaseConfig(
        "postgresql", os.environ["DATAFLOW_TEST_ADMIN_URL"], os.environ["DATAFLOW_TEST_ROOT_CERT"]
    )


def test_admin_transfer_is_idempotent_preserves_hash_and_omits_sessions(account_service, tmp_path):
    config = migration_config(account_service)
    source_path = tmp_path / "source.sqlite3"
    source = Accounts(source_path)
    uid = source.bootstrap_admin("Original Admin", "admin@example.com", PASSWORD)
    old_token = source.login("admin@example.com", PASSWORD)
    with source.connection() as db:
        original = dict(db.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone())
    assert import_admin(config, source_path, "ADMIN@example.com") == "imported"
    assert import_admin(config, source_path, "admin@example.com") == "unchanged"
    with account_service.connection() as db:
        transferred = dict(db.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone())
        assert {key: transferred[key] for key in USER_COLUMNS} == {key: original[key] for key in USER_COLUMNS}
        assert db.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"] == 0
    with pytest.raises(AccountError):
        account_service.identity(old_token)
    token = account_service.login("admin@example.com", PASSWORD)
    assert account_service.identity(token)["role"] == "ADMIN"
    with account_service.transaction() as db:
        db.execute("UPDATE users SET full_name='Changed in cloud' WHERE user_id=?", (uid,))
    with pytest.raises(AccountError, match="Remplacement"):
        import_admin(config, source_path, "admin@example.com")
    assert import_admin(config, source_path, "admin@example.com", replace=True) == "replaced"
    with pytest.raises(AccountError):
        account_service.identity(token)
    assert source.identity(old_token)["user_id"] == uid  # Source DB untouched.


def test_conflicting_email_does_not_overwrite_another_identity(account_service, tmp_path):
    config = migration_config(account_service)
    source_path = tmp_path / "source.sqlite3"
    source = Accounts(source_path)
    source.bootstrap_admin("Source Admin", "admin@example.com", PASSWORD)
    account_service.register("Target Client", "admin@example.com", PASSWORD)
    with pytest.raises(AccountError, match="Conflit"):
        import_admin(config, source_path, "admin@example.com", replace=True)
    token = account_service.login("admin@example.com", PASSWORD)
    assert account_service.identity(token)["role"] == "FREE"


def test_schema_rerun_preserves_accounts_and_runtime_role_cannot_ddl(account_service):
    config = migration_config(account_service)
    account_service.register("Preserved Client", "client@example.com", PASSWORD)
    assert migrate_schema(config) == []
    token = account_service.login("client@example.com", PASSWORD)
    assert account_service.identity(token)["role"] == "FREE"
    for query in [
        "CREATE TABLE dataflow.forbidden(id INTEGER)",
        "UPDATE schema_version SET version=99",
        "DELETE FROM users",
        "DELETE FROM audit_log",
    ]:
        with pytest.raises(DatabaseError):
            with account_service.transaction() as db:
                db.execute(query)


def test_tls_is_used_and_hostname_and_untrusted_ca_are_rejected(account_service, tmp_path):
    migration_config(account_service)
    config = account_service.database.config
    with account_service.connection() as db:
        assert db.raw.pgconn.ssl_in_use
    bad_ca = tmp_path / "invalid-ca.crt"
    bad_ca.write_text("not a trusted certificate", encoding="utf-8")
    with pytest.raises(DatabaseError):
        with Database(replace(config, rootcert=str(bad_ca))).connection():
            pass
    # The disposable server certificate only covers localhost, not 127.0.0.1.
    wrong_host = config.target.replace("@localhost:", "@127.0.0.1:")
    assert wrong_host != config.target
    with pytest.raises(DatabaseError):
        with Database(replace(config, target=wrong_host)).connection():
            pass
