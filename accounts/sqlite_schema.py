"""Legacy local/test schema, retained for compatibility."""

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
