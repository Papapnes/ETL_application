from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from email_validator import EmailNotValidError, validate_email

from etl.engine import run

TORONTO = ZoneInfo("America/Toronto")
HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
PUBLIC_USER = "user_id, full_name, email, role, account_status, custom_daily_limit, created_at"
SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES(1);
CREATE TABLE IF NOT EXISTS plans(
    plan_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL UNIQUE CHECK(plan_name IN ('FREE','PRO','ADMIN')),
    daily_limit INTEGER CHECK(daily_limit >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    CHECK((plan_name='ADMIN' AND daily_limit IS NULL) OR (plan_name!='ADMIN' AND daily_limit IS NOT NULL))
);
INSERT OR IGNORE INTO plans VALUES('free','FREE',5,1);
INSERT OR IGNORE INTO plans VALUES('pro','PRO',50,1);
INSERT OR IGNORE INTO plans VALUES('admin','ADMIN',NULL,1);
CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY, full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'FREE' REFERENCES plans(plan_name),
    account_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(account_status IN ('ACTIVE','DISABLED')),
    custom_daily_limit INTEGER CHECK(custom_daily_limit >= 0),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions(
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
    created_at REAL NOT NULL, expires_at REAL NOT NULL, last_seen REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS password_resets(
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
    expires_at REAL NOT NULL, used_at REAL
);
CREATE TABLE IF NOT EXISTS usage(
    usage_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
    execution_id TEXT NOT NULL, execution_date TEXT NOT NULL,
    execution_status TEXT NOT NULL CHECK(execution_status IN ('RUNNING','SUCCESS','FAILED')),
    created_at TEXT NOT NULL, finished_at TEXT, error_code TEXT,
    UNIQUE(user_id,execution_id)
);
CREATE INDEX IF NOT EXISTS usage_daily ON usage(user_id,execution_date,execution_status);
CREATE TABLE IF NOT EXISTS rate_limits(
    bucket TEXT PRIMARY KEY, started_at REAL NOT NULL, attempts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log(
    audit_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL REFERENCES users(user_id),
    action TEXT NOT NULL, target_id TEXT, details TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class AccountError(ValueError):
    """Safe, translatable message for the user."""


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def email_address(value):
    try:
        if not isinstance(value, str) or len(value) > 254:
            raise ValueError
        return validate_email(value.strip(), check_deliverability=False).normalized.casefold()
    except (EmailNotValidError, ValueError):
        raise AccountError("Adresse courriel invalide.") from None


def validate_password(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        raise AccountError("Le mot de passe doit contenir entre 12 et 128 caractères.")


class Accounts:
    def __init__(self, path, clock=None):
        self.path = str(Path(path).resolve())
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(SCHEMA)
            if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] != 1:
                raise RuntimeError("Unsupported accounts schema version")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def now(self):
        value = self.clock()
        if value.tzinfo is None:
            raise ValueError("Clock must be timezone-aware")
        return value.astimezone(timezone.utc)

    def _rate_limit(self, action, subject, limit, seconds=900):
        now = self.now().timestamp()
        bucket = action + ":" + token_hash(str(subject))
        with self.transaction() as db:
            row = db.execute("SELECT * FROM rate_limits WHERE bucket=?", (bucket,)).fetchone()
            if row is None or row["started_at"] + seconds <= now:
                db.execute("INSERT OR REPLACE INTO rate_limits VALUES(?,?,1)", (bucket, now))
            elif row["attempts"] >= limit:
                raise AccountError("Trop de tentatives. Réessayez dans 15 minutes.")
            else:
                db.execute("UPDATE rate_limits SET attempts=attempts+1 WHERE bucket=?", (bucket,))
            db.execute("DELETE FROM rate_limits WHERE started_at < ?", (now - 86400,))

    def _new_user(self, db, name, email, password_hash, role="FREE"):
        uid = str(uuid4())
        db.execute(
            "INSERT INTO users(user_id,full_name,email,password_hash,role,created_at) VALUES(?,?,?,?,?,?)",
            (uid, name, email, password_hash, role, self.now().isoformat()),
        )
        return uid

    def register(self, full_name, email, password, client="local"):
        self._rate_limit("register-client", client, 10)
        name = str(full_name).strip()
        if not 2 <= len(name) <= 120 or any(ord(c) < 32 for c in name):
            raise AccountError("Le nom doit contenir entre 2 et 120 caractères.")
        email = email_address(email)
        validate_password(password)
        hashed = HASHER.hash(password)
        with self.transaction() as db:
            if not db.execute("SELECT is_active FROM plans WHERE plan_name='FREE'").fetchone()[0]:
                raise AccountError("Les inscriptions sont temporairement suspendues.")
            # Never accept a role, status, quota or user ID from the registration form.
            if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
                return
            self._new_user(db, name, email, hashed)

    def bootstrap_admin(self, full_name, email, password):
        """Operator-only CLI entry point, never called by a public UI."""
        email = email_address(email)
        validate_password(password)
        name = full_name.strip()
        if not 2 <= len(name) <= 120:
            raise AccountError("Le nom doit contenir entre 2 et 120 caractères.")
        hashed = HASHER.hash(password)
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM users WHERE role='ADMIN'").fetchone():
                raise AccountError("Un administrateur existe déjà. Utilisez son espace de gestion.")
            if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
                raise AccountError(
                    "Cette adresse existe déjà. Choisissez une adresse administrateur distincte."
                )
            uid = self._new_user(db, name, email, hashed, "ADMIN")
            self._audit(db, uid, "bootstrap_admin", uid, {})
            return uid

    def login(self, email, password, client="local"):
        self._rate_limit("login-client", client, 60)
        # Invalid addresses take the same generic path as unknown identities.
        candidate = str(email).strip().casefold()[:254]
        self._rate_limit("login-email", candidate, 10)
        with self.connection() as db:
            row = db.execute("SELECT * FROM users WHERE email=?", (candidate,)).fetchone()
        hashed = row["password_hash"] if row else DUMMY_HASH
        supplied = password if isinstance(password, str) and len(password) <= 128 else ""
        try:
            verified = HASHER.verify(hashed, supplied)
        except (VerificationError, InvalidHashError):
            verified = False
        if not verified or row is None or row["account_status"] != "ACTIVE":
            raise AccountError("Identifiants incorrects ou compte indisponible.")
        token, now = secrets.token_urlsafe(32), self.now().timestamp()
        with self.transaction() as db:
            # Recheck after hashing: concurrent disable/reset must win.
            current = db.execute("SELECT * FROM users WHERE user_id=?", (row["user_id"],)).fetchone()
            if current["account_status"] != "ACTIVE" or current["password_hash"] != hashed:
                raise AccountError("Identifiants incorrects ou compte indisponible.")
            if HASHER.check_needs_rehash(hashed):
                db.execute(
                    "UPDATE users SET password_hash=? WHERE user_id=?",
                    (HASHER.hash(supplied), row["user_id"]),
                )
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?,?,?)",
                (token_hash(token), row["user_id"], now, now + 8 * 3600, now),
            )
            db.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        return token

    def _identity(self, db, token, admin=False):
        if not isinstance(token, str) or not 20 <= len(token) <= 128:
            raise AccountError("Votre session a expiré. Reconnectez-vous.")
        now = self.now().timestamp()
        session = db.execute("SELECT * FROM sessions WHERE token_hash=?", (token_hash(token),)).fetchone()
        if session is None or session["expires_at"] <= now or session["last_seen"] + 3600 <= now:
            raise AccountError("Votre session a expiré. Reconnectez-vous.")
        user = db.execute(
            f"SELECT {PUBLIC_USER} FROM users WHERE user_id=?", (session["user_id"],)
        ).fetchone()
        if user is None or user["account_status"] != "ACTIVE":
            raise AccountError("Compte désactivé. Contactez l’administrateur.")
        if admin and user["role"] != "ADMIN":
            raise AccountError("Accès administrateur requis.")
        db.execute("UPDATE sessions SET last_seen=? WHERE token_hash=?", (now, token_hash(token)))
        return dict(user)

    def identity(self, token):
        with self.transaction() as db:
            return self._identity(db, token)

    def logout(self, token):
        if isinstance(token, str):
            with self.transaction() as db:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(token),))

    def _quota(self, db, user):
        today = self.now().astimezone(TORONTO).date()
        plan = db.execute("SELECT * FROM plans WHERE plan_name=?", (user["role"],)).fetchone()
        limit = (
            None
            if user["role"] == "ADMIN"
            else (
                user["custom_daily_limit"] if user["custom_daily_limit"] is not None else plan["daily_limit"]
            )
        )
        counts = {
            r["execution_status"]: r["n"]
            for r in db.execute(
                "SELECT execution_status,COUNT(*) n FROM usage WHERE user_id=? AND execution_date=? GROUP BY execution_status",
                (user["user_id"], today.isoformat()),
            )
        }
        used, pending = counts.get("SUCCESS", 0), counts.get("RUNNING", 0)
        renewal = datetime.combine(today + timedelta(days=1), time.min, TORONTO)
        return dict(
            used=used,
            pending=pending,
            limit=limit,
            remaining=None if limit is None else max(0, limit - used - pending),
            next_reset=renewal.isoformat(),
            date=today.isoformat(),
            plan_active=bool(plan["is_active"]) or user["role"] == "ADMIN",
        )

    def quota(self, token):
        with self.transaction() as db:
            user = self._identity(db, token)
            return self._quota(db, user)

    def execute_etl(self, token, execution_id, datasets, recipe, reviewed=None):
        try:
            execution_id = str(UUID(execution_id))
        except (ValueError, TypeError, AttributeError):
            raise AccountError("Identifiant d’exécution invalide.") from None
        with self.transaction() as db:
            user = self._identity(db, token)
            prior = db.execute(
                "SELECT execution_status FROM usage WHERE user_id=? AND execution_id=?",
                (user["user_id"], execution_id),
            ).fetchone()
            if prior:
                raise AccountError(
                    "Ce traitement a déjà été soumis. Consultez son résultat ou lancez un nouveau traitement."
                )
            quota = self._quota(db, user)
            if not quota["plan_active"]:
                raise AccountError("Votre plan est temporairement suspendu.")
            if quota["remaining"] == 0:
                raise AccountError("Quota quotidien atteint ou réservé par des traitements en cours.")
            db.execute(
                "INSERT INTO usage VALUES(?,?,?,?,?,?,NULL,NULL)",
                (
                    str(uuid4()),
                    user["user_id"],
                    execution_id,
                    quota["date"],
                    "RUNNING",
                    self.now().isoformat(),
                ),
            )
        # No client-provided role or counter reaches this boundary. A short write
        # transaction above serializes competing reservations, not the ETL work.
        try:
            result = run(datasets, recipe, reviewed)
            with self.transaction() as db:
                db.execute(
                    "UPDATE usage SET execution_status='SUCCESS',finished_at=? WHERE user_id=? AND execution_id=? AND execution_status='RUNNING'",
                    (self.now().isoformat(), user["user_id"], execution_id),
                )
        except Exception as exc:
            with self.transaction() as db:
                db.execute(
                    "UPDATE usage SET execution_status='FAILED',finished_at=?,error_code=? WHERE user_id=? AND execution_id=? AND execution_status='RUNNING'",
                    (self.now().isoformat(), type(exc).__name__, user["user_id"], execution_id),
                )
            raise
        result["report"]["execution_id"] = execution_id
        result["report"]["quota_date"] = quota["date"]
        return result

    def request_password_reset(self, email, sender, client="local"):
        self._rate_limit("reset-client", client, 15)
        candidate = str(email).strip().casefold()[:254]
        self._rate_limit("reset-email", candidate, 3)
        token = secrets.token_urlsafe(32)
        with self.transaction() as db:
            user = db.execute(
                "SELECT user_id,email FROM users WHERE email=? AND account_status='ACTIVE'", (candidate,)
            ).fetchone()
            if not user:
                return
            db.execute("DELETE FROM password_resets WHERE user_id=?", (user["user_id"],))
            db.execute(
                "INSERT INTO password_resets VALUES(?,?,?,NULL)",
                (token_hash(token), user["user_id"], self.now().timestamp() + 1800),
            )
        # Sender is server configuration, never supplied by an HTTP client.
        # No token in logs or browser URLs; the user enters the emailed code.
        try:
            sender(user["email"], token)
        except Exception:
            with self.transaction() as db:
                db.execute("DELETE FROM password_resets WHERE token_hash=?", (token_hash(token),))
            raise AccountError("Le service de courriel est indisponible. Réessayez plus tard.") from None

    def reset_password(self, token, password, client="local"):
        self._rate_limit("reset-confirm-client", client, 15)
        validate_password(password)
        if not isinstance(token, str) or not 20 <= len(token) <= 128:
            raise AccountError("Code de récupération invalide ou expiré.")
        hashed = HASHER.hash(password)
        now = self.now().timestamp()
        with self.transaction() as db:
            row = db.execute(
                "SELECT r.*,u.account_status FROM password_resets r JOIN users u ON u.user_id=r.user_id WHERE token_hash=?",
                (token_hash(token),),
            ).fetchone()
            if (
                row is None
                or row["used_at"] is not None
                or row["expires_at"] <= now
                or row["account_status"] != "ACTIVE"
            ):
                raise AccountError("Code de récupération invalide ou expiré.")
            db.execute("UPDATE users SET password_hash=? WHERE user_id=?", (hashed, row["user_id"]))
            db.execute("UPDATE password_resets SET used_at=? WHERE user_id=?", (now, row["user_id"]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (row["user_id"],))

    def _audit(self, db, actor, action, target, details):
        db.execute(
            "INSERT INTO audit_log VALUES(?,?,?,?,?,?)",
            (str(uuid4()), actor, action, target, json.dumps(details), self.now().isoformat()),
        )

    def update_user(self, token, user_id, role, status, custom_limit=None):
        if role not in {"FREE", "PRO", "ADMIN"} or status not in {"ACTIVE", "DISABLED"}:
            raise AccountError("Rôle ou statut invalide.")
        if custom_limit is not None and (type(custom_limit) is not int or not 0 <= custom_limit <= 1_000_000):
            raise AccountError("Le quota doit être un entier entre 0 et 1 000 000.")
        with self.transaction() as db:
            actor = self._identity(db, token, admin=True)
            target = db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
            if target is None:
                raise AccountError("Utilisateur introuvable.")
            if (
                target["role"] == "ADMIN"
                and target["account_status"] == "ACTIVE"
                and (role != "ADMIN" or status != "ACTIVE")
            ):
                count = db.execute(
                    "SELECT COUNT(*) FROM users WHERE role='ADMIN' AND account_status='ACTIVE'"
                ).fetchone()[0]
                if count <= 1:
                    raise AccountError("Le dernier administrateur actif ne peut pas être retiré.")
            custom_limit = None if role == "ADMIN" else custom_limit
            db.execute(
                "UPDATE users SET role=?,account_status=?,custom_daily_limit=? WHERE user_id=?",
                (role, status, custom_limit, user_id),
            )
            if status == "DISABLED":
                db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
                db.execute("DELETE FROM password_resets WHERE user_id=?", (user_id,))
            self._audit(
                db,
                actor["user_id"],
                "update_user",
                user_id,
                dict(role=role, status=status, custom_daily_limit=custom_limit),
            )

    def update_plan(self, token, plan, daily_limit, active=True):
        if (
            plan not in {"FREE", "PRO"}
            or type(daily_limit) is not int
            or not 0 <= daily_limit <= 1_000_000
            or type(active) is not bool
        ):
            raise AccountError("Configuration de plan invalide.")
        with self.transaction() as db:
            actor = self._identity(db, token, admin=True)
            db.execute(
                "UPDATE plans SET daily_limit=?,is_active=? WHERE plan_name=?",
                (daily_limit, int(active), plan),
            )
            self._audit(
                db, actor["user_id"], "update_plan", plan, dict(daily_limit=daily_limit, active=active)
            )

    def admin_data(self, token):
        with self.transaction() as db:
            self._identity(db, token, admin=True)
            users = [
                dict(row) for row in db.execute(f"SELECT {PUBLIC_USER} FROM users ORDER BY created_at DESC")
            ]
            for user in users:
                quota = self._quota(db, user)
                user.update(
                    used_today=quota["used"],
                    pending=quota["pending"],
                    daily_limit=quota["limit"],
                    remaining=quota["remaining"],
                )
                user["total_runs"] = db.execute(
                    "SELECT COUNT(*) FROM usage WHERE user_id=? AND execution_status='SUCCESS'",
                    (user["user_id"],),
                ).fetchone()[0]
            plans = [dict(row) for row in db.execute("SELECT * FROM plans")]
            return dict(users=users, plans=plans)

    def release_failed_reservation(self, execution_id):
        """CLI-only recovery after the operator has stopped the interrupted worker."""
        with self.transaction() as db:
            row = db.execute(
                "SELECT * FROM usage WHERE execution_id=? AND execution_status='RUNNING'", (execution_id,)
            ).fetchone()
            if row is None:
                raise AccountError("Aucune réservation en cours pour cet identifiant.")
            db.execute(
                "UPDATE usage SET execution_status='FAILED',finished_at=?,error_code='OperatorRecovery' WHERE usage_id=?",
                (self.now().isoformat(), row["usage_id"]),
            )
