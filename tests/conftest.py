import os

import pytest
from psycopg.conninfo import conninfo_to_dict

from accounts.config import DatabaseConfig
from accounts.database import Database
from accounts.migrate import migrate_schema
from accounts.service import Accounts


@pytest.fixture(autouse=True)
def isolated_accounts_database(tmp_path, monkeypatch):
    """Tests must never create or modify real client/admin identities."""
    monkeypatch.setenv("DATAFLOW_DB_PATH", str(tmp_path / "accounts.sqlite3"))
    monkeypatch.setenv("DATAFLOW_DB_BACKEND", "sqlite")
    monkeypatch.delenv("DATAFLOW_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATAFLOW_MIGRATION_DATABASE_URL", raising=False)
    # Never read real local credentials in tests.
    monkeypatch.setattr("accounts.config.ROOT", tmp_path)
    monkeypatch.setattr("streamlit.secrets", {})


@pytest.fixture(params=["sqlite", "postgresql"])
def account_service(request, tmp_path):
    if request.param == "sqlite":
        config = DatabaseConfig("sqlite", str(tmp_path / "contract.sqlite3"))
    else:
        admin_url = os.environ.get("DATAFLOW_TEST_ADMIN_URL")
        app_url = os.environ.get("DATAFLOW_TEST_APP_URL")
        if not admin_url or not app_url:
            pytest.skip("Disposable PostgreSQL TLS server not configured")
        # Never clear a remote Supabase database or an arbitrary local database.
        for url in (admin_url, app_url):
            parsed = conninfo_to_dict(url)
            assert parsed.get("host") in {"localhost", "127.0.0.1"}
            assert parsed.get("dbname") == "dataflow_test"
        rootcert = os.environ["DATAFLOW_TEST_ROOT_CERT"]
        admin_config = DatabaseConfig("postgresql", admin_url, rootcert)
        migrate_schema(admin_config)
        with Database(admin_config).transaction() as db:
            db.execute("TRUNCATE audit_log, usage, password_resets, sessions, users, rate_limits")
            db.execute("UPDATE plans SET daily_limit=5,is_active=1 WHERE plan_name='FREE'")
            db.execute("UPDATE plans SET daily_limit=50,is_active=1 WHERE plan_name='PRO'")
        config = DatabaseConfig("postgresql", app_url, rootcert)
    return Accounts(config)
