-- the administrator the executor connects as: a NON-superuser with CREATEROLE and no table privilege and no USAGE on schema
-- public (Cloud SQL's `postgres`, as read live). Valid on PostgreSQL <= 15 (CREATEROLE may grant any non-superuser role);
-- on >= 16 the tests run the executor as the cluster superuser instead (conftest: DPFA2_TEST_ADMIN).
CREATE ROLE adm LOGIN CREATEROLE;
-- a stand-in for suvarna_reader (read-only; may read the attestation tables, not the snapshot tables)
CREATE ROLE rehearsal_reader LOGIN;
GRANT USAGE ON SCHEMA public TO rehearsal_reader;
GRANT SELECT ON public.l1_data_plane_function_attestations, public.l1_data_plane_trigger_attestations,
  public.l2_data_plane_function_attestations, public.l2_data_plane_trigger_attestations,
  public.chart_divisionals, public.build_runs, public.l1_data_plane_generations TO rehearsal_reader;
INSERT INTO public.charts(id,chart_id,client_id,owner_id,birth_date,birth_time,birth_lat,birth_lng,timezone_id,house_system)
VALUES ('aaaaaaaa-1111-4222-8333-000000000001','aaaaaaaa-1111-4222-8333-000000000001','syn-client','syn-owner','1991-07-19','06:20:00',18.52,73.86,'Asia/Kolkata','whole_sign')
ON CONFLICT DO NOTHING;
