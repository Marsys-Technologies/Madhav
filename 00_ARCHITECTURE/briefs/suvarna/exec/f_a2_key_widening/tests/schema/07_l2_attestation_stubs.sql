-- The deploy gate (data-plane-ownership-status.ts) unions the L1 AND L2 attestation tables. The real L2 layer (migration 1036)
-- needs 29 bodha_* tables this rehearsal does not model, so only the two attestation tables the gate reads are created here,
-- with the same columns and live ownership/ACL (owner data_plane_l2_owner; data_plane_l1_owner has NO SELECT on them, amjis_app has).
-- They hold only the two stub functions' rows: the executor is run with the 12 L1 active tables as the gate table list.
SET ROLE data_plane_l2_owner;
CREATE TABLE public.l2_data_plane_function_attestations (
  function_signature text PRIMARY KEY,
  definition_digest text NOT NULL CHECK (definition_digest ~ '^[0-9a-f]{64}$'),
  owner_name text NOT NULL,
  security_definer boolean NOT NULL,
  config text[]
);
CREATE TABLE public.l2_data_plane_trigger_attestations (
  table_name text NOT NULL,
  trigger_name text NOT NULL,
  trigger_type smallint NOT NULL,
  enabled "char" NOT NULL,
  function_oid oid NOT NULL,
  function_signature text NOT NULL,
  definition_digest text NOT NULL CHECK (definition_digest ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY(table_name, trigger_name)
);
GRANT SELECT ON public.l2_data_plane_function_attestations, public.l2_data_plane_trigger_attestations
  TO data_plane_builder, data_plane_verifier, data_plane_migrator, amjis_app;
-- the two L2 trigger functions the gate's trigger-shape query names by regprocedure literal, attested like the live ones
CREATE FUNCTION public.l2_data_plane_guard_active_mutation() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
  SET search_path = pg_catalog, public, pg_temp AS $f$ BEGIN RETURN NEW; END $f$;
CREATE FUNCTION public.l2_data_plane_capture_row() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
  SET search_path = pg_catalog, public, pg_temp AS $f$ BEGIN RETURN NEW; END $f$;
REVOKE EXECUTE ON FUNCTION public.l2_data_plane_guard_active_mutation(), public.l2_data_plane_capture_row() FROM PUBLIC;
INSERT INTO public.l2_data_plane_function_attestations(function_signature, definition_digest, owner_name, security_definer, config)
SELECT p.oid::regprocedure::text, encode(public.digest(pg_get_functiondef(p.oid), 'sha256'), 'hex'), pg_get_userbyid(p.proowner),
       p.prosecdef, p.proconfig
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname IN ('l2_data_plane_guard_active_mutation', 'l2_data_plane_capture_row');
RESET ROLE;
