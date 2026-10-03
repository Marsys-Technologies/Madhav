-- Disposable PostgreSQL 15 bootstrap mirroring production role attributes (read from pg_roles via the reader, 2026-10-03).
-- Run ONCE as the container superuser.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
    ('amjis_app', true, false), ('amjis_inquiry_serve', true, true), ('data_plane_builder', true, false),
    ('data_plane_l1_owner', false, false), ('data_plane_l2_owner', false, false), ('data_plane_migrator', true, false),
    ('data_plane_schema_owner', false, false), ('data_plane_verifier', true, false), ('nirmana_campaign_control_writer', true, false),
    ('nirmana_evidence_ingress_writer', true, false), ('nirmana_evidence_owner', false, false), ('nirmana_migrator', true, false),
    ('purna_inquiry_owner', false, false), ('retrieval_census_ro', true, true), ('role_jobs', false, true), ('role_ledger_write', false, true),
    ('role_orchestrator', false, true), ('role_sidecar', false, true), ('role_web_serve', false, true), ('suvarna_reader', true, false),
    ('utkarsha_builder', false, true)) AS t(name, login, inherit) LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=r.name) THEN EXECUTE format('CREATE ROLE %I %s %s NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS',
                   r.name, CASE WHEN r.login THEN 'LOGIN PASSWORD ''pw''' ELSE 'NOLOGIN' END, CASE WHEN r.inherit THEN 'INHERIT' ELSE 'NOINHERIT' END); END IF;
  END LOOP;
END $$;
DO $$ BEGIN IF NOT pg_has_role('amjis_inquiry_serve','role_web_serve','MEMBER') THEN GRANT role_web_serve TO amjis_inquiry_serve; END IF; END $$;
-- pre-cutover production state: amjis_app owns schema public and the database objects it creates
ALTER SCHEMA public OWNER TO amjis_app;
GRANT CREATE ON DATABASE dp_role_test TO amjis_app;
GRANT CONNECT ON DATABASE dp_role_test TO data_plane_builder, data_plane_migrator, data_plane_verifier, suvarna_reader;
-- stubs for Cloud SQL administrative roles that appear in production ACLs / ownership (NOLOGIN, no privileges)
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cloudsqlsuperuser') THEN CREATE ROLE cloudsqlsuperuser NOLOGIN; END IF; IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cloudsqladmin') THEN CREATE ROLE cloudsqladmin NOLOGIN; END IF; END $$;
