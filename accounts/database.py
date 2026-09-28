"""Small DB-API boundary for the existing service; no automatic cloud DDL."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from accounts.config import DatabaseConfig
from accounts.errors import DatabaseError
from accounts.sqlite_schema import SCHEMA

# Shared by schema migrations and short account transactions. It preserves the
# existing BEGIN IMMEDIATE semantics, including last-admin and rate-limit races.
ACCOUNT_LOCK = 724390215
UNAVAILABLE = "La base de comptes est indisponible. Vérifiez sa configuration ou réessayez plus tard."


class PostgresConnection:
    def __init__(self, connection):
        self.raw = connection

    def execute(self, query, params=()):
        # Only service-owned SQL templates cross this boundary; values stay bound.
        return self.raw.execute(query.replace("?", "%s"), params)


class Database:
    def __init__(self, config):
        self.config = config if isinstance(config, DatabaseConfig) else DatabaseConfig("sqlite", str(config))
        if self.config.backend not in {"sqlite", "postgresql"}:
            raise DatabaseError("Type de base de données invalide.")

    @contextmanager
    def connection(self):
        db = None
        try:
            if self.config.backend == "postgresql":
                try:
                    options = conninfo_to_dict(self.config.target)
                    if not options.get("host") or options["host"].startswith("/"):
                        raise ValueError
                    if options.get("sslmode", "verify-full") != "verify-full":
                        raise ValueError
                except (psycopg.Error, ValueError):
                    raise DatabaseError(
                        "Configuration PostgreSQL invalide : TLS verify-full requis."
                    ) from None
                db = psycopg.connect(
                    self.config.target,
                    sslmode="verify-full",
                    sslrootcert=self.config.rootcert,
                    gssencmode="disable",
                    connect_timeout=10,
                    autocommit=True,
                    row_factory=dict_row,
                    prepare_threshold=None,
                )
                db.execute("SET search_path TO dataflow, pg_catalog")
                db.execute("SET statement_timeout TO '30s'")
                db.execute("SET lock_timeout TO '15s'")
                yield PostgresConnection(db)
            else:
                db = sqlite3.connect(self.config.target, timeout=30, isolation_level=None)
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA foreign_keys=ON")
                yield db
        except (psycopg.Error, sqlite3.Error):
            # Driver exceptions may contain hostnames, SQL values or credentials.
            raise DatabaseError(UNAVAILABLE) from None
        finally:
            if db is not None:
                db.close()

    @contextmanager
    def transaction(self):
        with self.connection() as db:
            if self.config.backend == "postgresql":
                with db.raw.transaction():
                    db.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                    db.execute("SELECT pg_advisory_xact_lock(?)", (ACCOUNT_LOCK,))
                    yield db
            else:
                db.execute("BEGIN IMMEDIATE")
                try:
                    yield db
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise

    def check_schema(self):
        if self.config.backend == "sqlite":
            Path(self.config.target).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            if self.config.backend == "sqlite":
                db.execute("PRAGMA journal_mode=WAL")
                db.executescript(SCHEMA)
            row = db.execute("SELECT MAX(version) AS version FROM schema_version").fetchone()
            expected = 2 if self.config.backend == "postgresql" else 1
            if row["version"] != expected:
                raise DatabaseError(
                    "Version de base incompatible. Exécutez les migrations avant le démarrage."
                )
