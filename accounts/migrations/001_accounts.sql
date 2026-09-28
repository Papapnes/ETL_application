CREATE SCHEMA IF NOT EXISTS dataflow;
REVOKE ALL ON SCHEMA dataflow FROM PUBLIC;
SET LOCAL search_path TO dataflow, pg_catalog;

CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
INSERT INTO schema_version VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS plans(
    plan_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL UNIQUE CHECK(plan_name IN ('FREE','PRO','ADMIN')),
    daily_limit INTEGER CHECK(daily_limit >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    CHECK((plan_name='ADMIN' AND daily_limit IS NULL) OR (plan_name!='ADMIN' AND daily_limit IS NOT NULL))
);
INSERT INTO plans VALUES('free','FREE',5,1) ON CONFLICT DO NOTHING;
INSERT INTO plans VALUES('pro','PRO',50,1) ON CONFLICT DO NOTHING;
INSERT INTO plans VALUES('admin','ADMIN',NULL,1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY, full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE , password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'FREE' REFERENCES plans(plan_name),
    account_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(account_status IN ('ACTIVE','DISABLED')),
    custom_daily_limit INTEGER CHECK(custom_daily_limit >= 0),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions(
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
    created_at DOUBLE PRECISION NOT NULL, expires_at DOUBLE PRECISION NOT NULL, last_seen DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS password_resets(
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
    expires_at DOUBLE PRECISION NOT NULL, used_at DOUBLE PRECISION
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
    bucket TEXT PRIMARY KEY, started_at DOUBLE PRECISION NOT NULL, attempts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log(
    audit_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL REFERENCES users(user_id),
    action TEXT NOT NULL, target_id TEXT, details TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower ON users(lower(email));

REVOKE ALL ON ALL TABLES IN SCHEMA dataflow FROM PUBLIC;
