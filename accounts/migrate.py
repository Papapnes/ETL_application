"""Explicit operator-only schema and account migration. Never called by the UI."""

import sqlite3
from pathlib import Path

from argon2 import extract_parameters

from accounts.database import Database
from accounts.errors import DatabaseError
from accounts.service import AccountError, Accounts, email_address

MIGRATIONS = Path(__file__).with_name("migrations")
USER_COLUMNS = (
    "user_id",
    "full_name",
    "email",
    "password_hash",
    "role",
    "account_status",
    "custom_daily_limit",
    "created_at",
)


def migrate_schema(config):
    if config.backend != "postgresql":
        raise DatabaseError("Cette commande nécessite PostgreSQL.")
    database = Database(config)
    applied = []
    with database.transaction() as db:
        exists = db.execute("SELECT to_regclass('dataflow.schema_version') AS name").fetchone()["name"]
        version = (
            db.execute("SELECT MAX(version) AS version FROM schema_version").fetchone()["version"]
            if exists
            else 0
        )
        if version not in {0, 1, 2}:
            raise DatabaseError("Version de schéma inconnue : migration interrompue.")
        for path in sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")):
            number = int(path.name[:3])
            if number > version:
                db.raw.execute(path.read_text(encoding="utf-8"), prepare=False)
                applied.append(number)
    return applied


def import_admin(config, source, email, *, replace=False):
    if config.backend != "postgresql":
        raise DatabaseError("La destination doit être PostgreSQL.")
    address = email_address(email)
    try:
        # Read-only mode also prevents creating an empty DB if the path is wrong.
        with sqlite3.connect(Path(source).resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                f"SELECT {','.join(USER_COLUMNS)} FROM users WHERE lower(email)=?", (address,)
            ).fetchall()
            if len(rows) != 1 or rows[0]["role"] != "ADMIN":
                raise AccountError("Compte ADMIN source introuvable ou ambigu.")
            user = dict(rows[0])
    except sqlite3.Error:
        raise DatabaseError("Impossible de lire la base SQLite source.") from None
    try:
        extract_parameters(user["password_hash"])
    except Exception:
        raise AccountError("Le compte source ne contient pas un hachage Argon2 valide.") from None
    target = Accounts(config)
    with target.transaction() as db:
        matches = db.execute(
            "SELECT * FROM users WHERE user_id=? OR lower(email)=?", (user["user_id"], address)
        ).fetchall()
        if matches:
            if len(matches) != 1 or matches[0]["user_id"] != user["user_id"]:
                raise AccountError("Conflit d’identité : aucun compte existant n’a été modifié.")
            if all(matches[0][key] == user[key] for key in USER_COLUMNS):
                return "unchanged"
            if not replace:
                raise AccountError("Compte existant différent. Remplacement explicite requis (--replace).")
            db.execute(
                "UPDATE users SET " + ",".join(f"{key}=?" for key in USER_COLUMNS[1:]) + " WHERE user_id=?",
                tuple(user[key] for key in USER_COLUMNS[1:]) + (user["user_id"],),
            )
            db.execute("DELETE FROM sessions WHERE user_id=?", (user["user_id"],))
            db.execute("DELETE FROM password_resets WHERE user_id=?", (user["user_id"],))
            outcome = "replaced"
        else:
            db.execute(
                f"INSERT INTO users({','.join(USER_COLUMNS)}) VALUES({','.join('?' for _ in USER_COLUMNS)})",
                tuple(user[key] for key in USER_COLUMNS),
            )
            outcome = "imported"
        target._audit(
            db, user["user_id"], "import_admin", user["user_id"], {"source": "sqlite", "outcome": outcome}
        )
    return outcome
