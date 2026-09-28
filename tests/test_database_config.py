import traceback

import psycopg
import pytest

from accounts.config import DatabaseConfig, database_config
from accounts.database import Database
from accounts.errors import DatabaseError


def test_cloud_requires_explicit_database(monkeypatch):
    monkeypatch.delenv("DATAFLOW_DB_BACKEND")
    with pytest.raises(DatabaseError):
        database_config()


def test_empty_or_invalid_url_never_falls_back_to_sqlite(monkeypatch):
    for value in ["", "sqlite:///temporary.db", "secret-invalid-url"]:
        monkeypatch.setenv("DATAFLOW_DATABASE_URL", value)
        with pytest.raises(DatabaseError):
            database_config()


def test_local_secrets_and_environment_precedence(tmp_path, monkeypatch):
    directory = tmp_path / ".streamlit"
    directory.mkdir()
    (directory / "secrets.toml").write_text(
        'DATAFLOW_DATABASE_URL = "postgresql://app:local-secret@localhost/dataflow_test"\n', encoding="utf-8"
    )
    assert database_config().backend == "postgresql"
    monkeypatch.setenv("DATAFLOW_DATABASE_URL", "postgresql://app:env-secret@localhost/dataflow_test")
    assert "env-secret" in database_config().target
    assert "secret" not in repr(database_config())
    with pytest.raises(DatabaseError):
        database_config(migration=True)


def test_tls_cannot_be_disabled_and_errors_are_redacted(monkeypatch):
    uri = "postgresql://app:secret-password@localhost/dataflow_test"
    called = []

    def unavailable(*args, **kwargs):
        called.append(kwargs)
        raise psycopg.OperationalError(uri)

    monkeypatch.setattr("accounts.database.psycopg.connect", unavailable)
    with pytest.raises(DatabaseError):
        with Database(DatabaseConfig("postgresql", uri + "?sslmode=disable")).connection():
            pass
    assert not called
    with pytest.raises(DatabaseError) as caught:
        with Database(DatabaseConfig("postgresql", uri)).connection():
            pass
    assert called[0]["sslmode"] == "verify-full"
    assert called[0]["sslrootcert"] == "system"
    assert "secret-password" not in "".join(traceback.format_exception(caught.value))
