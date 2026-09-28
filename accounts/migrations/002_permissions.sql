SET LOCAL search_path TO dataflow, pg_catalog;

-- Deliberately no password and NOLOGIN until an operator configures credentials.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dataflow_app') THEN
        CREATE ROLE dataflow_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
            NOREPLICATION NOBYPASSRLS;
    ELSIF EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname='dataflow_app'
        AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
    ) OR EXISTS (
        SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname='dataflow_app')
    ) THEN
        RAISE EXCEPTION 'Existing application role is not least-privilege; operator review required';
    END IF;
END $$;

REVOKE ALL ON SCHEMA dataflow FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA dataflow FROM PUBLIC;
GRANT USAGE ON SCHEMA dataflow TO dataflow_app;
GRANT SELECT ON dataflow.schema_version TO dataflow_app;
GRANT SELECT, UPDATE ON dataflow.plans TO dataflow_app;
GRANT SELECT, INSERT, UPDATE ON dataflow.users, dataflow.usage TO dataflow_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON dataflow.sessions,
    dataflow.password_resets, dataflow.rate_limits TO dataflow_app;
GRANT SELECT, INSERT ON dataflow.audit_log TO dataflow_app;

-- Supabase API roles, if present, must not see this private schema.
DO $$ DECLARE api_role TEXT; BEGIN
    FOREACH api_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = api_role) THEN
            EXECUTE format('REVOKE ALL ON SCHEMA dataflow FROM %I', api_role);
            EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA dataflow FROM %I', api_role);
        END IF;
    END LOOP;
END $$;
INSERT INTO schema_version VALUES(2) ON CONFLICT DO NOTHING;
