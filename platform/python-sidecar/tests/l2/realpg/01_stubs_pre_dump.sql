-- Tables the reader cannot dump (permission denied) but that production FKs reference. Stubs carry ONLY what the schema load and the
-- L2 path need; they are NOT claimed to be the production DDL. charts mirrors platform/migrations/001_baseline.sql plus the columns the
-- repo's own DB test inserts (chart_type) and fetch_birth_params reads.
SET ROLE amjis_app;
CREATE TABLE public.charts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), client_id text, name text NOT NULL, birth_date date NOT NULL, birth_time time NOT NULL,
  birth_place text NOT NULL, birth_lat numeric, birth_lng numeric, ayanamsa text DEFAULT 'lahiri', house_system text DEFAULT 'sripathi',
  created_at timestamptz DEFAULT now(), native_id varchar(64) NOT NULL DEFAULT 'abhisek', owner_id text, subject_name text,
  chart_id uuid UNIQUE, role text NOT NULL DEFAULT 'native', created_at_iso timestamptz NOT NULL DEFAULT now(), preferred_name text,
  timezone_id text, chart_type text);
CREATE TABLE public.chart_grants (chart_id uuid, grantee text);
CREATE TABLE public.projects (id uuid PRIMARY KEY);
CREATE TABLE public.message_parts (id uuid PRIMARY KEY);
CREATE TABLE public.eval_runs (id uuid PRIMARY KEY);
CREATE TABLE public.conversations (id uuid PRIMARY KEY);
CREATE TABLE public.audit_log (id uuid PRIMARY KEY);
CREATE TABLE public.ai_turn_routing_snapshots (id uuid PRIMARY KEY);
CREATE TABLE public.ai_provider_connections (id uuid PRIMARY KEY);
CREATE TABLE public.planner_managed_prashna_jobs (id uuid PRIMARY KEY);
CREATE TABLE public.planner_inquiry_lifecycles (id uuid PRIMARY KEY);
RESET ROLE;
