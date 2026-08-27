-- Migration 633: attest the completed direct-legacy-owner campaign handoff.
-- Ownership changes happen only in the preceding direct-owner preflight; this
-- marker runs as the separate deployment-only nirmana_migrator login.
DO $$
DECLARE
  protected_role text;
BEGIN
  IF session_user <> 'nirmana_migrator' OR current_user <> 'nirmana_migrator' THEN
    RAISE EXCEPTION 'migration 633 must run as nirmana_migrator';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner'
    AND NOT rolcanlogin AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
    AND NOT rolreplication AND NOT rolbypassrls) THEN
    RAISE EXCEPTION 'migration 633 requires a normalized NOLOGIN evidence owner';
  END IF;
  FOREACH protected_role IN ARRAY ARRAY[
    'nirmana_evidence_owner',
    'nirmana_evidence_ingress_writer',
    'nirmana_campaign_control_writer',
    'nirmana_migrator'
  ] LOOP
    IF EXISTS (
      SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member
      WHERE role.rolname = protected_role
    ) THEN
      RAISE EXCEPTION 'migration 633 refuses protected writer role memberships for %', protected_role;
    END IF;
  END LOOP;
  IF EXISTS (SELECT 1 FROM pg_namespace namespace JOIN pg_roles owner ON owner.oid = namespace.nspowner
    WHERE namespace.nspname = current_schema() AND owner.rolname <> 'nirmana_evidence_owner') THEN
    RAISE EXCEPTION 'migration 633 requires evidence owner schema ownership';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
    JOIN pg_roles owner ON owner.oid = relation.relowner
    WHERE namespace.nspname = current_schema()
      AND relation.relname IN ('nirmana_elevation_campaign_definitions','nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
      AND owner.rolname <> 'nirmana_evidence_owner') THEN
    RAISE EXCEPTION 'migration 633 requires evidence owner campaign relations';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_proc procedure
      JOIN pg_namespace namespace ON namespace.oid = procedure.pronamespace
      JOIN pg_roles owner ON owner.oid = procedure.proowner
     WHERE namespace.nspname = current_schema()
       AND procedure.proname = ANY (ARRAY[
         'nirmana_elevation_prevent_event_mutation',
         'nirmana_elevation_guard_definition_mutation',
         'nirmana_elevation_prevent_label_mutation',
         'nirmana_elevation_guard_server_reconstructed_insert',
         'nirmana_elevation_guard_control_writer',
         'nirmana_elevation_prevent_campaign_truncate'
       ])
       AND owner.rolname <> 'nirmana_evidence_owner'
  ) THEN
    RAISE EXCEPTION 'migration 633 requires evidence owner campaign guards';
  END IF;
  IF (SELECT count(*) FROM pg_trigger trigger
      JOIN pg_class relation ON relation.oid = trigger.tgrelid
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
      WHERE namespace.nspname = current_schema()
        AND trigger.tgname = ANY (ARRAY[
          'nirmana_elevation_events_append_only',
          'nirmana_elevation_definitions_versioned',
          'nirmana_elevation_asset_labels_append_only',
          'nirmana_elevation_events_server_writer',
          'nirmana_elevation_definitions_control_writer',
          'nirmana_elevation_labels_control_writer',
          'nirmana_elevation_definitions_no_truncate',
          'nirmana_elevation_events_no_truncate'
        ])
        AND trigger.tgenabled = 'O') <> 8 THEN
    RAISE EXCEPTION 'migration 633 requires all campaign evidence guards enabled';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app'
    AND (rolcreatedb OR rolcreaterole OR rolsuper OR rolbypassrls))
    OR has_schema_privilege('amjis_app', current_schema(), 'CREATE') THEN
    RAISE EXCEPTION 'migration 633 refuses generic application administration';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_database database
    JOIN pg_roles owner ON owner.oid = database.datdba
    WHERE database.datname = current_database() AND owner.rolname = 'amjis_app'
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses generic application database ownership';
  END IF;
  IF NOT has_schema_privilege('nirmana_migrator', current_schema(), 'USAGE, CREATE') THEN
    RAISE EXCEPTION 'migration 633 requires the deployment-only migrator schema contract';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_class relation
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = current_schema()
       AND relation.relname IN ('nirmana_elevation_campaign_definitions','nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
       AND (
         has_table_privilege('amjis_app', relation.oid, 'INSERT, UPDATE, DELETE, TRUNCATE')
         OR NOT has_table_privilege('amjis_app', relation.oid, 'SELECT')
       )
  ) THEN
    RAISE EXCEPTION 'migration 633 requires generic application SELECT-only campaign access';
  END IF;
END;
$$;
