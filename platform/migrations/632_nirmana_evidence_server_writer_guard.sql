-- Migration 632: bind server-reconstructed Nirmana evidence to its own
-- dedicated database login. Migration 592 remains immutable.
BEGIN;

-- This role deliberately has no password here: the deploy owner must provision
-- a distinct secret-backed credential in a separate controlled action before
-- any server-reconstructed receipt can be recorded. Until then the application
-- fails closed rather than falling back to DATABASE_URL/DB_USER.
DO $$
DECLARE
  relation_name text;
  column_name text;
  inherited_role text;
  core_read_relations constant text[] := ARRAY[
    'nirmana_elevation_campaign_definitions',
    'nirmana_elevation_campaign_events',
    'asset_registry',
    'build_runs',
    'build_run_assets',
    'asset_provenance_receipts',
    'nirmana_elevation_monitor_observations',
    '_migrations_applied'
  ];
  detector_read_relations constant text[] := ARRAY[
    'asset_output_digest_specs',
    'bg_avastha_schemes', 'bg_combustion_orbs', 'bg_dignity_reference',
    'bg_gochara_arcs', 'bg_gochara_citation_resolution',
    'bg_graha_naisargika_friendship', 'bg_kota_chakra_rings',
    'bg_kp_sublord_division', 'bg_medical_mappings',
    'bg_motion_state_thresholds', 'bg_muhurta_lattice', 'bg_nakshatra_medical',
    'bg_parihara_rules', 'bg_muhurta_activity_rules', 'bg_muhurta_factor_census',
    'bg_phaladeepika_latta', 'bg_prashna_fructification_rules',
    'bg_prashna_lagna_methods', 'bg_prashna_significators',
    'bg_prashna_special_techniques', 'bg_prashna_tajik_yogas',
    'bg_sarvatobhadra_grid', 'bg_sign_medical', 'bg_sky_calendar',
    'bg_synthetic_cohort', 'bg_synthetic_cohort_md', 'bg_transit_engine',
    'bg_transit_moorti', 'bg_transit_rules', 'bg_vastu_direction_remedials',
    'bg_vastu_directions', 'bg_vedha_malefic_scale',
    'brahma_activity_ontology', 'brahma_class_priors',
    'brahma_compendium_index', 'brahma_dasha_systems', 'brahma_dosha_catalog',
    'brahma_event_ontology', 'brahma_formula_constants', 'brahma_ontology',
    'brahma_remedy_corpus', 'brahma_yoga_catalog', 'brahma_yoga_source_chunks',
    'classical_attributions', 'classical_text_chunks', 'classical_texts',
    'ephemeris_daily', 'nirmana_bg_texts_integrity_baselines',
    'reference_aspects', 'reference_constants', 'reference_dasha_systems',
    'reference_doshas', 'reference_glossary', 'reference_houses',
    'reference_karakas', 'reference_nakshatra', 'reference_nakshatra_matrix',
    'reference_nakshatra_pada', 'reference_planets', 'reference_signs',
    'reference_strength_systems', 'reference_topic_tags', 'reference_upagrahas',
    'reference_vargas', 'reference_yogas', 'sutravali_rules',
    'vidhi_floor_items', 'vidhi_intent_floors', 'vidhi_primitives'
  ];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    CREATE ROLE nirmana_evidence_ingress_writer LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;

  -- Replaying this migration must reduce a pre-existing role to the same least
  -- privilege boundary as a newly-created one. In particular, NOINHERIT alone
  -- is insufficient: an inherited membership can still be assumed with SET ROLE.
  ALTER ROLE nirmana_evidence_ingress_writer
    LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  FOR inherited_role IN
    SELECT parent.rolname
      FROM pg_auth_members AS membership
      JOIN pg_roles AS parent ON parent.oid = membership.roleid
      JOIN pg_roles AS member ON member.oid = membership.member
     WHERE member.rolname = 'nirmana_evidence_ingress_writer'
  LOOP
    EXECUTE format('REVOKE %I FROM nirmana_evidence_ingress_writer', inherited_role);
  END LOOP;

  EXECUTE format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM nirmana_evidence_ingress_writer', current_database());
  EXECUTE format('REVOKE ALL PRIVILEGES ON SCHEMA %I FROM nirmana_evidence_ingress_writer', current_schema());
  EXECUTE format('REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I FROM nirmana_evidence_ingress_writer', current_schema());
  EXECUTE format('REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I FROM nirmana_evidence_ingress_writer', current_schema());
  FOR relation_name, column_name IN
    SELECT relation.relname, attribute.attname
      FROM pg_class AS relation
      JOIN pg_attribute AS attribute ON attribute.attrelid = relation.oid
      JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = current_schema()
       AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
       AND attribute.attnum > 0
       AND NOT attribute.attisdropped
  LOOP
    EXECUTE format(
      'REVOKE ALL PRIVILEGES (%I) ON TABLE %I.%I FROM nirmana_evidence_ingress_writer',
      column_name, current_schema(), relation_name
    );
  END LOOP;

  EXECUTE format('GRANT CONNECT ON DATABASE %I TO nirmana_evidence_ingress_writer', current_database());
  EXECUTE format('GRANT USAGE ON SCHEMA %I TO nirmana_evidence_ingress_writer', current_schema());
  FOREACH relation_name IN ARRAY core_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
    END IF;
  END LOOP;
  IF to_regclass(format('%I.%I', current_schema(), 'nirmana_elevation_campaign_events')) IS NOT NULL THEN
    EXECUTE format('GRANT INSERT ON TABLE %I.nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer', current_schema());
  END IF;

  -- Authoritative frozen-integrity detector read contract. This is deliberately
  -- explicit rather than inferred from target_table or raw SQL: any future
  -- detector relation needs a reviewed migration addition before an ingress
  -- receipt can be earned. Missing grants fail the detector closed.
  FOREACH relation_name IN ARRAY detector_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
    END IF;
  END LOOP;

  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname = 'nirmana_evidence_ingress_writer'
       AND rolcanlogin AND NOT rolinherit AND NOT rolsuper
       AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'migration 632 could not normalize nirmana_evidence_ingress_writer role attributes';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_auth_members AS membership
      JOIN pg_roles AS member ON member.oid = membership.member
     WHERE member.rolname = 'nirmana_evidence_ingress_writer'
  ) THEN
    RAISE EXCEPTION 'migration 632 refuses a nirmana_evidence_ingress_writer role with inherited memberships';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_class AS relation
      JOIN pg_roles AS owner ON owner.oid = relation.relowner
     WHERE owner.rolname = 'nirmana_evidence_ingress_writer'
       AND relation.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
  ) THEN
    RAISE EXCEPTION 'migration 632 refuses an ingress login that owns database relations';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND NOT (
         privilege_type = 'SELECT'
         AND table_name = ANY(core_read_relations || detector_read_relations)
       )
       AND NOT (
         privilege_type = 'INSERT'
         AND table_name = 'nirmana_elevation_campaign_events'
       )
  ) THEN
    RAISE EXCEPTION 'migration 632 could not revoke stale ingress table privileges';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_attribute AS attribute
      JOIN pg_class AS relation ON relation.oid = attribute.attrelid
      JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
      CROSS JOIN LATERAL aclexplode(attribute.attacl) AS column_acl
      JOIN pg_roles AS grantee ON grantee.oid = column_acl.grantee
     WHERE namespace.nspname = current_schema()
       AND grantee.rolname = 'nirmana_evidence_ingress_writer'
  ) THEN
    RAISE EXCEPTION 'migration 632 could not revoke stale ingress column privileges';
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION nirmana_elevation_guard_server_reconstructed_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.source_kind = 'server_reconstructed'
     AND (session_user <> 'nirmana_evidence_ingress_writer'
          OR current_user <> 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'server-reconstructed Nirmana evidence may only be inserted by the dedicated evidence ingress login';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_events_server_writer
  ON nirmana_elevation_campaign_events;
CREATE TRIGGER nirmana_elevation_events_server_writer
  BEFORE INSERT ON nirmana_elevation_campaign_events
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_server_reconstructed_insert();

COMMENT ON FUNCTION nirmana_elevation_guard_server_reconstructed_insert() IS
  'Rejects server_reconstructed receipt insertion unless session_user and current_user are the dedicated Nirmana evidence ingress login.';

COMMIT;
