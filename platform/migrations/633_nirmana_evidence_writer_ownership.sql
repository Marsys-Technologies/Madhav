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
    AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
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
  IF NOT EXISTS (SELECT 1 FROM pg_namespace namespace JOIN pg_roles owner ON owner.oid = namespace.nspowner
    WHERE namespace.nspname = 'nirmana_evidence' AND owner.rolname = 'nirmana_evidence_owner') THEN
    RAISE EXCEPTION 'migration 633 requires evidence owner schema ownership';
  END IF;
  IF (SELECT count(*) FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
    JOIN pg_roles owner ON owner.oid = relation.relowner
    WHERE namespace.nspname = 'nirmana_evidence'
      AND relation.relname IN ('nirmana_elevation_campaign_definitions','nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
      AND relation.relkind IN ('r', 'p')
      AND owner.rolname = 'nirmana_evidence_owner') <> 3 THEN
    RAISE EXCEPTION 'migration 633 requires evidence owner campaign relations';
  END IF;
  IF (
    SELECT count(*)
  FROM (
    SELECT 1
      FROM pg_proc procedure
      JOIN pg_namespace namespace ON namespace.oid = procedure.pronamespace
      JOIN pg_roles owner ON owner.oid = procedure.proowner
     WHERE namespace.nspname = 'nirmana_evidence'
       AND procedure.proname = ANY (ARRAY[
         'nirmana_elevation_prevent_event_mutation',
         'nirmana_elevation_guard_definition_mutation',
         'nirmana_elevation_prevent_label_mutation',
         'nirmana_elevation_guard_server_reconstructed_insert',
         'nirmana_elevation_guard_control_writer',
         'nirmana_elevation_prevent_campaign_truncate'
       ])
       AND owner.rolname = 'nirmana_evidence_owner'
  ) AS owned_guards) <> 6 THEN
    RAISE EXCEPTION 'migration 633 requires evidence owner campaign guards';
  END IF;
  IF (SELECT count(*) FROM pg_trigger trigger
      JOIN pg_class relation ON relation.oid = trigger.tgrelid
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
      WHERE namespace.nspname = 'nirmana_evidence'
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
    AND (NOT rolcanlogin OR rolinherit OR rolcreatedb OR rolcreaterole OR rolsuper OR rolreplication OR rolbypassrls))
    OR has_schema_privilege('amjis_app', 'nirmana_evidence', 'CREATE') THEN
    RAISE EXCEPTION 'migration 633 refuses generic application administration';
  END IF;
  -- NOINHERIT does not prevent SET ROLE.  The marker is a final-state
  -- attestation: generic application identity must have no membership edge
  -- in either direction, including the legacy Cloud SQL database-owner edge.
  IF EXISTS (
    SELECT 1
      FROM pg_auth_members membership
      JOIN pg_roles parent ON parent.oid = membership.roleid
      JOIN pg_roles member ON member.oid = membership.member
     WHERE parent.rolname = 'amjis_app' OR member.rolname = 'amjis_app'
  ) OR EXISTS (
    SELECT 1 FROM pg_database database
     WHERE database.datname = current_database()
       AND (database.datdba = 'amjis_app'::regrole
         OR pg_has_role('amjis_app', database.datdba, 'MEMBER'))
  ) OR has_database_privilege('amjis_app', current_database(), 'CREATE') THEN
    RAISE EXCEPTION 'migration 633 requires generic application role membership and database administration cleanup';
  END IF;
  -- Mirror the preflight's bounded provider-root classification. A bare
  -- postgres role is not exempt: it must be the non-super direct child of the
  -- current database owner. The three additional names are exact observed
  -- Cloud SQL system users, not a cloudsql* wildcard; no other descendant is
  -- accepted.
  IF EXISTS (
    WITH RECURSIVE provider_roots(oid, depth) AS (
      SELECT datdba, 0 FROM pg_database WHERE datname = current_database()
      UNION ALL
      SELECT membership.member, parent.depth + 1
        FROM pg_auth_members membership
        JOIN provider_roots parent ON parent.oid = membership.roleid
    )
    SELECT 1
      FROM provider_roots root
      JOIN pg_roles role ON role.oid = root.oid
      JOIN pg_database database ON database.datname = current_database()
     WHERE NOT (
       root.oid = database.datdba
       OR (root.depth = 1 AND role.rolname = 'postgres' AND NOT role.rolsuper AND NOT role.rolreplication AND NOT role.rolbypassrls)
       OR (root.depth = 1 AND role.rolname IN ('cloudsqlagent', 'cloudsqlimportexport', 'cloudsqllogical'))
     )
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses unbounded provider database-owner membership topology';
  END IF;
  IF NOT has_schema_privilege('amjis_app', 'nirmana_evidence', 'USAGE') THEN
    RAISE EXCEPTION 'migration 633 requires generic application read schema usage';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer'
    AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
    AND NOT rolreplication AND NOT rolbypassrls) THEN
    RAISE EXCEPTION 'migration 633 requires a normalized ingress writer';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer'
    AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
    AND NOT rolreplication AND NOT rolbypassrls) THEN
    RAISE EXCEPTION 'migration 633 requires a normalized control writer';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_migrator'
    AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
    AND NOT rolreplication AND NOT rolbypassrls) THEN
    RAISE EXCEPTION 'migration 633 requires a normalized deployment-only migrator';
  END IF;
  IF NOT has_schema_privilege('nirmana_evidence_ingress_writer', 'nirmana_evidence', 'USAGE')
    OR NOT has_schema_privilege('nirmana_campaign_control_writer', 'nirmana_evidence', 'USAGE')
    OR has_schema_privilege('nirmana_evidence_ingress_writer', 'nirmana_evidence', 'CREATE')
    OR has_schema_privilege('nirmana_campaign_control_writer', 'nirmana_evidence', 'CREATE')
    OR has_schema_privilege('nirmana_migrator', 'nirmana_evidence', 'USAGE') THEN
    RAISE EXCEPTION 'migration 633 requires the exact evidence schema access envelope';
  END IF;
  IF has_schema_privilege('nirmana_evidence_owner', 'public', 'CREATE')
    OR has_schema_privilege('nirmana_evidence_ingress_writer', 'public', 'CREATE')
    OR has_schema_privilege('nirmana_campaign_control_writer', 'public', 'CREATE')
    OR has_schema_privilege('nirmana_migrator', 'public', 'CREATE')
    OR NOT has_schema_privilege('nirmana_evidence_ingress_writer', 'public', 'USAGE')
    OR NOT has_schema_privilege('nirmana_campaign_control_writer', 'public', 'USAGE')
    OR NOT has_schema_privilege('nirmana_migrator', 'public', 'USAGE') THEN
    RAISE EXCEPTION 'migration 633 requires exact shared-schema writer access';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_class relation
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname IN ('nirmana_elevation_campaign_definitions','nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
       AND (
         has_table_privilege('amjis_app', relation.oid, 'INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
         OR NOT has_table_privilege('amjis_app', relation.oid, 'SELECT')
       )
  ) THEN
    RAISE EXCEPTION 'migration 633 requires generic application SELECT-only campaign access';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_class relation
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relkind = 'S'
  ) THEN
    RAISE EXCEPTION 'migration 633 requires no campaign-owned sequences with unreviewed ACLs';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_class relation
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname = 'nirmana_elevation_campaign_definitions'
       AND (NOT has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'SELECT, INSERT, UPDATE')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'DELETE, TRUNCATE, REFERENCES, TRIGGER'))
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname IN ('nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
       AND (NOT has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'SELECT, INSERT')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER'))
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname = 'nirmana_elevation_campaign_definitions'
       AND (NOT has_table_privilege('nirmana_evidence_ingress_writer', relation.oid, 'SELECT')
         OR has_table_privilege('nirmana_evidence_ingress_writer', relation.oid, 'INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER'))
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname = 'nirmana_elevation_campaign_events'
       AND (NOT has_table_privilege('nirmana_evidence_ingress_writer', relation.oid, 'SELECT, INSERT')
         OR has_table_privilege('nirmana_evidence_ingress_writer', relation.oid, 'UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER'))
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname = 'nirmana_elevation_asset_labels'
       AND has_table_privilege('nirmana_evidence_ingress_writer', relation.oid, 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname IN ('nirmana_elevation_campaign_definitions','nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
       AND has_table_privilege('nirmana_migrator', relation.oid, 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
  ) THEN
    RAISE EXCEPTION 'migration 633 requires exact campaign table writer ACLs';
  END IF;
  IF EXISTS (
    SELECT 1
      FROM pg_attribute attribute
      JOIN pg_class relation ON relation.oid = attribute.attrelid
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
      CROSS JOIN LATERAL aclexplode(attribute.attacl) AS column_acl
      LEFT JOIN pg_roles grantee ON grantee.oid = column_acl.grantee
     WHERE namespace.nspname = 'nirmana_evidence'
       AND relation.relname IN ('nirmana_elevation_campaign_definitions','nirmana_elevation_campaign_events','nirmana_elevation_asset_labels')
       AND (column_acl.grantee = 0 OR grantee.rolname IN ('amjis_app','nirmana_evidence_ingress_writer','nirmana_campaign_control_writer','nirmana_migrator'))
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses residual campaign column ACLs';
  END IF;
  -- No non-owner writer may retain an unreviewed effective surface outside
  -- nirmana_evidence.  Control has a narrow public read allowlist; the
  -- deployment-only marker may only maintain the public migration ledger.
  IF EXISTS (
    SELECT 1 FROM pg_namespace namespace
     WHERE namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
       AND namespace.nspname NOT IN ('public', 'nirmana_evidence')
       AND (
         has_schema_privilege('nirmana_campaign_control_writer', namespace.oid, 'USAGE, CREATE')
         OR has_schema_privilege('nirmana_migrator', namespace.oid, 'USAGE, CREATE')
       )
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname <> 'nirmana_evidence'
       AND namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
       AND (
         (has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'SELECT')
           AND (namespace.nspname <> 'public' OR relation.relname <> ALL (ARRAY['asset_registry','nirmana_elevation_monitor_observations','build_runs','build_run_assets','asset_provenance_receipts','_migrations_applied'])))
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'INSERT')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'UPDATE')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'DELETE')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'TRUNCATE')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'REFERENCES')
         OR has_table_privilege('nirmana_campaign_control_writer', relation.oid, 'TRIGGER')
         OR (has_table_privilege('nirmana_migrator', relation.oid, 'SELECT')
           AND (namespace.nspname <> 'public' OR relation.relname <> '_migrations_applied'))
         OR (has_table_privilege('nirmana_migrator', relation.oid, 'INSERT')
           AND (namespace.nspname <> 'public' OR relation.relname <> '_migrations_applied'))
         OR has_table_privilege('nirmana_migrator', relation.oid, 'UPDATE')
         OR has_table_privilege('nirmana_migrator', relation.oid, 'DELETE')
         OR has_table_privilege('nirmana_migrator', relation.oid, 'TRUNCATE')
         OR has_table_privilege('nirmana_migrator', relation.oid, 'REFERENCES')
         OR has_table_privilege('nirmana_migrator', relation.oid, 'TRIGGER')
       )
  ) OR EXISTS (
    SELECT 1 FROM pg_class relation JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname <> 'nirmana_evidence'
       AND namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
       AND relation.relkind = 'S'
       AND (has_sequence_privilege('nirmana_campaign_control_writer', relation.oid, 'USAGE, SELECT, UPDATE')
         OR has_sequence_privilege('nirmana_migrator', relation.oid, 'USAGE, SELECT, UPDATE'))
  ) OR EXISTS (
    SELECT 1 FROM pg_attribute attribute
      JOIN pg_class relation ON relation.oid = attribute.attrelid
      JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
      CROSS JOIN LATERAL aclexplode(attribute.attacl) AS column_acl
      LEFT JOIN pg_roles grantee ON grantee.oid = column_acl.grantee
     WHERE namespace.nspname <> 'nirmana_evidence'
       AND namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
       AND (column_acl.grantee = 0 OR grantee.rolname IN ('nirmana_campaign_control_writer','nirmana_migrator'))
  ) OR has_database_privilege('nirmana_campaign_control_writer', current_database(), 'CREATE')
    OR has_database_privilege('nirmana_migrator', current_database(), 'CREATE') THEN
    RAISE EXCEPTION 'migration 633 refuses non-owner writer ACLs outside the explicit envelope';
  END IF;
  -- Default privileges are a future-object ACL path, so the marker must
  -- attest them as carefully as current relation ACLs.  PUBLIC grants count:
  -- they are effective for every protected writer.  Only defaults whose
  -- grantor can create in a schema a protected role can use (or can create a
  -- schema) are relevant; unrelated isolated schemas do not block the marker.
  IF EXISTS (
    WITH protected_roles(name) AS (
      SELECT unnest(ARRAY['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'])
    ), provider_roots(oid) AS (
      WITH RECURSIVE closure(oid) AS (
        SELECT datdba FROM pg_database WHERE datname = current_database()
        UNION
        SELECT membership.member FROM pg_auth_members membership JOIN closure parent ON parent.oid = membership.roleid
      ) SELECT oid FROM closure
    )
    SELECT 1
      FROM pg_default_acl defaults
      JOIN pg_roles grantor ON grantor.oid = defaults.defaclrole
      CROSS JOIN LATERAL aclexplode(defaults.defaclacl) AS default_grant
      LEFT JOIN pg_roles grantee ON grantee.oid = default_grant.grantee
     WHERE grantor.oid NOT IN (SELECT oid FROM provider_roots)
       AND default_grant.grantee <> defaults.defaclrole
       AND (default_grant.grantee = 0 OR grantee.rolname IN (SELECT name FROM protected_roles))
       AND (
         (defaults.defaclobjtype = 'n' AND has_database_privilege(grantor.rolname, current_database(), 'CREATE'))
         OR (defaults.defaclobjtype <> 'n' AND EXISTS (
           SELECT 1 FROM pg_namespace namespace
            WHERE (defaults.defaclnamespace = 0 OR defaults.defaclnamespace = namespace.oid)
              AND namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
              AND has_schema_privilege(grantor.rolname, namespace.oid, 'CREATE')
              AND EXISTS (SELECT 1 FROM protected_roles protected WHERE has_schema_privilege(protected.name, namespace.oid, 'USAGE'))
         ))
       )
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses relevant protected-writer default ACLs';
  END IF;
  -- A missing pg_default_acl row is not a deny: PostgreSQL grants PUBLIC
  -- EXECUTE on newly created functions and PUBLIC USAGE on new types.  Each
  -- role that can create where a protected role has USAGE must explicitly
  -- override both hard-wired defaults before this marker can attest it.
  IF EXISTS (
    WITH protected_roles(name) AS (
      SELECT unnest(ARRAY['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'])
    ), provider_roots(oid) AS (
      WITH RECURSIVE closure(oid) AS (
        SELECT datdba FROM pg_database WHERE datname = current_database()
        UNION
        SELECT membership.member FROM pg_auth_members membership JOIN closure parent ON parent.oid = membership.roleid
      ) SELECT oid FROM closure
    )
    SELECT 1
      FROM pg_roles grantor
     WHERE NOT grantor.rolsuper
       AND grantor.oid NOT IN (SELECT oid FROM provider_roots)
       AND EXISTS (
       SELECT 1 FROM pg_namespace namespace
        WHERE namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
          AND has_schema_privilege(grantor.rolname, namespace.oid, 'CREATE')
          AND EXISTS (SELECT 1 FROM protected_roles protected WHERE has_schema_privilege(protected.name, namespace.oid, 'USAGE'))
     )
       AND (
         NOT EXISTS (
           SELECT 1 FROM pg_default_acl defaults
            WHERE defaults.defaclrole = grantor.oid AND defaults.defaclnamespace = 0 AND defaults.defaclobjtype = 'f'
              AND NOT EXISTS (
                SELECT 1 FROM aclexplode(defaults.defaclacl) AS default_grant
                 WHERE default_grant.grantee = 0 AND default_grant.privilege_type = 'EXECUTE'
              )
         )
         OR NOT EXISTS (
           SELECT 1 FROM pg_default_acl defaults
            WHERE defaults.defaclrole = grantor.oid AND defaults.defaclnamespace = 0 AND defaults.defaclobjtype = 'T'
              AND NOT EXISTS (
                SELECT 1 FROM aclexplode(defaults.defaclacl) AS default_grant
                 WHERE default_grant.grantee = 0 AND default_grant.privilege_type = 'USAGE'
              )
         )
       )
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses hard-wired PUBLIC function/type defaults for a protected-writer grantor';
  END IF;
END;
$$;
