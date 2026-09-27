import pytest


@pytest.fixture(autouse=True)
def isolated_accounts_database(tmp_path, monkeypatch):
    """Tests must never create or modify real client/admin identities."""
    monkeypatch.setenv("DATAFLOW_DB_PATH", str(tmp_path / "accounts.sqlite3"))
