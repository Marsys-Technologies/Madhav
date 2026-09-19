/** DP-SD-018 one-shot administrator bootstrap for the L1/L2 protected boundary. */
import { Pool, PoolClient, type PoolConfig } from 'pg'

// This is intentionally distinct from DATA_PLANE_ADMIN_DATABASE_URL.  The
// latter is constrained to the isolated validation proxy; ownership transfer
// must authenticate directly as postgres and must never borrow that route.
export const ADMIN_URL = 'DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL'

export const L1_ACTIVE_TABLES = [
  'chart_facts', 'chart_dashas', 'chart_divisionals', 'ga_condition_composite',
  'ga_yoga_firings', 'chart_vichara', 'ga_transit_anchors',
  'l1_tajik_varsha_year_lords', 'ga_medical',
  'ga_vastu_planet_direction_map', 'ga_prashna_lagna', 'ga_prashna_judgment',
] as const

export const L2_ACTIVE_TABLES = [
  'bodha_msr_signals', 'bodha_cgm_nodes', 'bodha_cgm_edges',
  'bodha_contradictions', 'bodha_cgm_paths', 'bodha_cgm_motifs',
  'bodha_cgm_sub_graphs', 'bodha_cgm_chart_topology_summary', 'bodha_mechanisms',
  'bodha_cdlm_cells', 'bodha_convergence', 'bodha_triangulation',
  'bodha_cdlm_chart_summary', 'bodha_cdlm_domain_rollups',
  'bodha_cdlm_pattern_clusters', 'bodha_pratijna', 'bodha_rm_resonances',
  'bodha_rm_remedy_prescriptions', 'bodha_rm_dasha_windowed_prescriptions',
  'bodha_rm_chart_summary', 'bodha_rm_dosha_remedy_bundles',
  'bodha_rm_pattern_remedies', 'bodha_signal_embeddings', 'bodha_discoveries',
  'bodha_anomalies', 'bodha_question_lenses', 'bodha_chart_gestalt',
  'synthesis_quality_scorecard', 'bodha_grounding_matches',
] as const

// Current-plan runtime writes outside the newly protected producer tables.
// These names are explicit so an asset_registry edit cannot widen the role.
export const CONTROL_AND_L0_L3_TABLES = [
  'build_runs', 'build_run_assets', 'asset_throughput', 'build_substep_progress',
  'build_checkpoints', 'build_events', 'orchestrator_event_register',
  'performance_queries', 'performance_judge_verdict',
  'brahma_class_priors', 'brahma_compendium_index', 'brahma_dasha_systems',
  'brahma_dosha_catalog', 'brahma_event_ontology', 'brahma_formula_constants',
  'brahma_ontology', 'brahma_remedy_corpus', 'brahma_yoga_catalog',
  'bg_dignity_reference', 'bg_gochara_arcs', 'bg_gochara_citation_resolution',
  'bg_kota_chakra_rings', 'bg_kp_sublord_division', 'bg_medical_mappings',
  'bg_muhurta_lattice', 'bg_nakshatra_medical', 'bg_parihara_rules',
  'bg_phaladeepika_latta', 'bg_sarvatobhadra_grid', 'bg_sign_medical',
  'bg_sky_calendar', 'bg_transit_engine', 'bg_transit_rules',
  'bg_vastu_directions', 'bg_vedha_malefic_scale', 'classical_attributions',
  'classical_text_chunks', 'ephemeris_daily', 'reference_planets',
  'reference_nakshatras', 'reference_signs', 'reference_aspects',
  'reference_vargas', 'reference_houses', 'reference_strength_systems',
  'reference_karakas', 'reference_upagrahas', 'reference_constants',
  'reference_topic_tags', 'reference_glossary', 'reference_yogas',
  'reference_doshas', 'reference_dasha_systems', 'sutravali_rules',
  'vidhi_floor_items', 'vidhi_primitives', 'gochara_resonance_map',
  'gochara_v3_calibration', 'ka_kshetra_tier_basis', 'kala_activation',
  'kala_activation_predicates', 'kala_avadhi', 'kala_bhavishya',
  'kala_convergence', 'kala_convergence_staging', 'kala_darshana',
  'kala_field', 'kala_field_boundaries', 'kala_field_clocks', 'kala_field_gof',
  'kala_field_kinematics', 'kala_field_null', 'kala_field_primitives',
  'kala_field_promise_edges', 'kala_field_promise_nodes',
  'kala_field_provenance', 'kala_field_routes', 'kala_field_salience',
  'kala_field_skill', 'kala_field_snapshots', 'kala_field_weight_versions',
  'kala_field_weights', 'kala_field_windows', 'kala_gochara_authority',
  'kala_gochara_v2_build_state', 'kala_gochara_windows',
  'kala_gochara_windows_v2', 'kala_insights', 'kala_jivana_parva',
  'kala_kota_chakra', 'kala_moorti_nirnaya', 'kala_obstruction',
  'kala_paddhati_profile', 'kala_sudarshana_varsha', 'kala_taranga',
  'kala_timeline_spec', 'kala_tithi_pravesha', 'kala_vedha_gochara',
] as const

const qi = (value: string): string => `"${value.replaceAll('"', '""')}"`

async function revokeAllRelationGrantees(
  client: PoolClient,
  objectKind: 'TABLE' | 'SEQUENCE',
  relation: string,
  owner: string,
): Promise<void> {
  const grantees = await client.query<{ grantee: string }>(`
    SELECT DISTINCT COALESCE(grantee.rolname, 'PUBLIC') AS grantee
    FROM pg_class object
    JOIN pg_namespace ns ON ns.oid=object.relnamespace
    CROSS JOIN LATERAL aclexplode(COALESCE(
      object.relacl,
      acldefault(CASE WHEN object.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END, object.relowner)
    )) acl
    LEFT JOIN pg_roles grantee ON grantee.oid=acl.grantee
    JOIN pg_roles object_owner ON object_owner.oid=object.relowner
    WHERE ns.nspname='public' AND object.relname=$1
      AND COALESCE(grantee.rolname, 'PUBLIC')<>object_owner.rolname
  `, [relation])
  for (const { grantee } of grantees.rows) {
    const principal = grantee === 'PUBLIC' ? 'PUBLIC' : qi(grantee)
    await client.query(`REVOKE ALL ON ${objectKind} public.${qi(relation)} FROM ${principal}`)
  }
  // A NULL ACL still implies PUBLIC defaults for functions, but not for tables
  // and sequences. Keep this explicit so future PostgreSQL default changes or
  // fixture drift cannot silently widen the protected relation surface.
  await client.query(`REVOKE ALL ON ${objectKind} public.${qi(relation)} FROM PUBLIC`)
}

async function revokeAllPublicSchemaGrantees(client: PoolClient): Promise<void> {
  const grantees = await client.query<{ grantee: string }>(`
    SELECT DISTINCT COALESCE(grantee.rolname, 'PUBLIC') AS grantee
    FROM pg_namespace ns
    CROSS JOIN LATERAL aclexplode(COALESCE(ns.nspacl, acldefault('n',ns.nspowner))) acl
    LEFT JOIN pg_roles grantee ON grantee.oid=acl.grantee
    JOIN pg_roles object_owner ON object_owner.oid=ns.nspowner
    WHERE ns.nspname='public'
      AND COALESCE(grantee.rolname, 'PUBLIC')<>object_owner.rolname
  `)
  for (const { grantee } of grantees.rows) {
    const principal = grantee === 'PUBLIC' ? 'PUBLIC' : qi(grantee)
    await client.query(`REVOKE ALL ON SCHEMA public FROM ${principal}`)
  }
  await client.query('REVOKE ALL ON SCHEMA public FROM PUBLIC')
}

async function revokeAllDefaultPrivilegeGrantees(client: PoolClient, owner: string): Promise<void> {
  const grants = await client.query<{
    namespace_name: string | null
    object_kind: 'TABLES' | 'SEQUENCES' | 'FUNCTIONS' | 'TYPES' | 'SCHEMAS'
    grantee: string
    privilege_type: string
  }>(`
    SELECT ns.nspname namespace_name,
      CASE d.defaclobjtype
        WHEN 'r' THEN 'TABLES' WHEN 'S' THEN 'SEQUENCES'
        WHEN 'f' THEN 'FUNCTIONS' WHEN 'T' THEN 'TYPES' WHEN 'n' THEN 'SCHEMAS'
      END object_kind,
      COALESCE(grantee.rolname,'PUBLIC') grantee,acl.privilege_type
    FROM pg_default_acl d JOIN pg_roles default_owner ON default_owner.oid=d.defaclrole
    LEFT JOIN pg_namespace ns ON ns.oid=d.defaclnamespace
    CROSS JOIN LATERAL aclexplode(d.defaclacl) acl
    LEFT JOIN pg_roles grantee ON grantee.oid=acl.grantee
    WHERE default_owner.rolname=$1
      AND COALESCE(grantee.rolname,'PUBLIC')<>default_owner.rolname
  `, [owner])
  for (const grant of grants.rows) {
    if (!grant.object_kind) throw new Error(`Unsupported default privilege object kind for ${owner}.`)
    const namespace = grant.namespace_name ? ` IN SCHEMA ${qi(grant.namespace_name)}` : ''
    const principal = grant.grantee === 'PUBLIC' ? 'PUBLIC' : qi(grant.grantee)
    await client.query(
      `ALTER DEFAULT PRIVILEGES${namespace} REVOKE ${grant.privilege_type} ON ${grant.object_kind} FROM ${principal}`,
    )
  }
}

async function normalizeDataPlaneMemberships(client: PoolClient): Promise<void> {
  const controlled = [
    'data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner',
    'data_plane_migrator','data_plane_builder','data_plane_verifier',
  ]
  const unexpected = await client.query<{ parent_role: string; member_role: string }>(`
    SELECT parent.rolname parent_role,member.rolname member_role
    FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid
    JOIN pg_roles member ON member.oid=m.member
    WHERE (parent.rolname=ANY($1::text[]) OR member.rolname=ANY($1::text[]))
      AND NOT (parent.rolname=ANY($2::text[]) AND member.rolname='data_plane_migrator')
  `, [controlled, ['data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner']])
  for (const edge of unexpected.rows) {
    await client.query(`REVOKE ${qi(edge.parent_role)} FROM ${qi(edge.member_role)}`)
  }
}

async function assertRoles(client: PoolClient): Promise<void> {
  const actor = await client.query<{ current_user: string; can_manage: boolean }>(`
    SELECT current_user,
           rolsuper OR rolcreaterole AS can_manage
    FROM pg_roles WHERE rolname = current_user
  `)
  if (actor.rows[0]?.current_user !== 'postgres' || actor.rows[0]?.can_manage !== true) {
    throw new Error('Data-plane ownership preflight requires direct postgres administrative authentication.')
  }
  await client.query(`DO $$
    DECLARE r text;
    BEGIN
      FOREACH r IN ARRAY ARRAY['data_plane_migrator','data_plane_builder','data_plane_verifier'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=r) THEN
          RAISE EXCEPTION 'required preprovisioned login role % is absent', r;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname=r AND
          (NOT rolcanlogin OR rolinherit OR rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls)) THEN
          RAISE EXCEPTION 'login role % is not normalized', r;
        END IF;
      END LOOP;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname LIKE 'data\\_plane\\_%' ESCAPE '\\'
        AND rolname <> ALL(ARRAY[
          'data_plane_migrator','data_plane_builder','data_plane_verifier',
          'data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner'
        ])) THEN
        RAISE EXCEPTION 'unknown data-plane principal collision';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_schema_owner') THEN
        CREATE ROLE data_plane_schema_owner NOLOGIN NOINHERIT;
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_l1_owner') THEN CREATE ROLE data_plane_l1_owner NOLOGIN NOINHERIT; END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_l2_owner') THEN CREATE ROLE data_plane_l2_owner NOLOGIN NOINHERIT; END IF;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner')
        AND (rolcanlogin OR rolinherit OR rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls)) THEN
        RAISE EXCEPTION 'protected owner role is not normalized';
      END IF;
    END $$`)
}

async function transferTables(client: PoolClient, owner: string, tables: readonly string[]): Promise<void> {
  for (const table of tables) {
    const exists = await client.query<{ present: boolean }>(
      `SELECT to_regclass($1) IS NOT NULL AS present`, [`public.${table}`],
    )
    if (exists.rows[0]?.present !== true) throw new Error(`Required producer table public.${table} is absent.`)
    const currentOwner = await client.query<{ owner: string }>(
      `SELECT pg_get_userbyid(relowner) AS owner FROM pg_class WHERE oid=to_regclass($1)`,
      [`public.${table}`],
    )
    if (currentOwner.rows[0]?.owner === 'amjis_app') {
      await client.query(`SET LOCAL ROLE amjis_app`)
      await client.query(`ALTER TABLE public.${qi(table)} OWNER TO ${qi(owner)}`)
    } else if (currentOwner.rows[0]?.owner !== owner) {
      throw new Error(`Unexpected owner ${currentOwner.rows[0]?.owner} for public.${table}.`)
    }
    const sequences = await client.query<{ sequence_name: string }>(`
      SELECT DISTINCT seq.relname AS sequence_name
      FROM pg_class tab
      JOIN pg_namespace ns ON ns.oid = tab.relnamespace
      JOIN pg_attribute col ON col.attrelid = tab.oid AND col.attnum > 0
      JOIN pg_depend dep ON dep.refclassid = 'pg_class'::regclass
        AND dep.refobjid = tab.oid AND dep.refobjsubid = col.attnum
        AND dep.classid = 'pg_class'::regclass AND dep.deptype IN ('a', 'i')
      JOIN pg_class seq ON seq.oid = dep.objid AND seq.relkind = 'S'
      WHERE ns.nspname = 'public' AND tab.relname = $1
    `, [table])
    await client.query(`SET LOCAL ROLE ${qi(owner)}`)
    await revokeAllRelationGrantees(client, 'TABLE', table, owner)
    // Commit the ownership stage deny-by-default. Builder DML is published only
    // by the guarded layer migration, after its admission triggers exist.
    await client.query(`GRANT SELECT ON TABLE public.${qi(table)} TO data_plane_builder, amjis_app, data_plane_verifier, data_plane_migrator${owner === 'data_plane_l1_owner' ? ', data_plane_l2_owner' : ''}`)
    for (const { sequence_name: sequence } of sequences.rows) {
      await revokeAllRelationGrantees(client, 'SEQUENCE', sequence, owner)
      await client.query(`GRANT SELECT ON SEQUENCE public.${qi(sequence)} TO data_plane_builder, data_plane_verifier, data_plane_migrator, amjis_app`)
    }
    await client.query('SET LOCAL ROLE amjis_app')
  }
}

export async function runDataPlaneOwnershipPreflight(
  databaseUrl: string | PoolConfig | undefined = process.env[ADMIN_URL],
): Promise<void> {
  if (!databaseUrl) throw new Error(`${ADMIN_URL} is required for the one-shot data-plane ownership preflight.`)
  const pool = new Pool(typeof databaseUrl === 'string'
    ? { connectionString: databaseUrl, max: 1 }
    : { ...databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await assertRoles(client)
    // The protected migrations use gen_random_uuid().  Provision this standard
    // PostgreSQL extension within the same transaction as the ownership stage:
    // a later preflight failure rolls back both the extension and all role or
    // ownership work, while an already-provisioned database remains unchanged.
    await client.query('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    const pgcrypto = await client.query(`SELECT 1 FROM pg_extension WHERE extname='pgcrypto'`)
    if (pgcrypto.rowCount !== 1) throw new Error('DBA prerequisite pgcrypto is absent; install it before protected-owner cutover.')
    const legacyOwners = await client.query<{ owner: string }>(`
      SELECT DISTINCT owner.rolname AS owner
      FROM pg_class object
      JOIN pg_namespace ns ON ns.oid = object.relnamespace
      JOIN pg_roles owner ON owner.oid = object.relowner
      WHERE ns.nspname = 'public' AND object.relname = ANY($1::text[])
    `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (legacyOwners.rows.some(({ owner }) => !['amjis_app', 'data_plane_l1_owner', 'data_plane_l2_owner'].includes(owner))) {
      throw new Error(`Unexpected protected producer owner topology: ${legacyOwners.rows.map((row) => row.owner).join(', ')}`)
    }
    const schemaOwner = await client.query<{ owner: string }>(
      `SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='public'`,
    )
    if (!['amjis_app', 'data_plane_schema_owner'].includes(schemaOwner.rows[0]?.owner ?? '')) {
      throw new Error(`Unexpected public schema owner ${schemaOwner.rows[0]?.owner}.`)
    }
    await client.query(`
      GRANT amjis_app TO postgres;
      GRANT data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner TO amjis_app WITH ADMIN OPTION;
      DO $$ BEGIN EXECUTE format('GRANT CREATE ON DATABASE %I TO amjis_app, data_plane_schema_owner', current_database()); END $$;
    `)
    await client.query(`SET LOCAL ROLE amjis_app;
      UPDATE public.asset_registry SET target_floor=0, count_sql='SELECT 0 AS count' WHERE asset_id='bo_samvada';
      UPDATE public.asset_output_digest_specs SET retired_at=COALESCE(retired_at,clock_timestamp()) WHERE asset_id='bo_samvada' AND retired_at IS NULL;
      GRANT SELECT ON public.charts, public.chart_grants, public.asset_registry, public.build_runs, public.build_run_assets TO data_plane_l1_owner, data_plane_l2_owner;
      GRANT SELECT ON public.fact_category_ownership TO data_plane_l1_owner;
      GRANT SELECT ON public.asset_output_digest_specs TO data_plane_l2_owner;
      RESET ROLE`)
    if (schemaOwner.rows[0]?.owner === 'amjis_app') {
      await client.query('SET LOCAL ROLE amjis_app; ALTER SCHEMA public OWNER TO data_plane_schema_owner; RESET ROLE')
    }
    await client.query('SET LOCAL ROLE data_plane_schema_owner')
    await revokeAllPublicSchemaGrantees(client)
    await client.query('RESET ROLE')
    await client.query('SET LOCAL ROLE data_plane_l1_owner')
    await revokeAllDefaultPrivilegeGrantees(client, 'data_plane_l1_owner')
    await client.query('RESET ROLE')
    await client.query('SET LOCAL ROLE data_plane_l2_owner')
    await revokeAllDefaultPrivilegeGrantees(client, 'data_plane_l2_owner')
    await client.query('RESET ROLE')
    await client.query(`
      DO $$ BEGIN EXECUTE format('REVOKE CREATE ON DATABASE %I FROM amjis_app, data_plane_schema_owner', current_database()); END $$;
      SET LOCAL ROLE data_plane_schema_owner;
      GRANT USAGE ON SCHEMA public TO data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner, data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve;
      DO $$ BEGIN
        IF to_regrole('purna_inquiry_owner') IS NOT NULL THEN
          GRANT USAGE ON SCHEMA public TO purna_inquiry_owner;
        END IF;
      END $$;
      GRANT CREATE ON SCHEMA public TO data_plane_l1_owner, data_plane_l2_owner;
      RESET ROLE;
      SET LOCAL ROLE data_plane_l1_owner;
      ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
      ALTER DEFAULT PRIVILEGES REVOKE USAGE ON TYPES FROM PUBLIC;
      RESET ROLE;
      SET LOCAL ROLE data_plane_l2_owner;
      ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
      ALTER DEFAULT PRIVILEGES REVOKE USAGE ON TYPES FROM PUBLIC;
      RESET ROLE;
    `)
    await client.query('SET LOCAL ROLE amjis_app')
    await transferTables(client, 'data_plane_l1_owner', L1_ACTIVE_TABLES)
    await transferTables(client, 'data_plane_l2_owner', L2_ACTIVE_TABLES)
    await client.query('RESET ROLE')
    await client.query('SET LOCAL ROLE amjis_app')
    for (const table of CONTROL_AND_L0_L3_TABLES) {
      const exists = await client.query<{ present: boolean }>(
        `SELECT to_regclass($1) IS NOT NULL AS present`, [`public.${table}`],
      )
      // This explicit superset spans installations of different ages. Absence
      // never widens the role; only a listed relation that actually exists is granted.
      if (exists.rows[0]?.present !== true) continue
      await client.query(`REVOKE ALL ON TABLE public.${qi(table)} FROM data_plane_builder`)
      await client.query(`GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.${qi(table)} TO data_plane_builder`)
      const sequences = await client.query<{ sequence_name: string }>(`
        SELECT DISTINCT seq.relname AS sequence_name FROM pg_class tab
        JOIN pg_namespace ns ON ns.oid=tab.relnamespace
        JOIN pg_depend dep ON dep.refobjid=tab.oid AND dep.refclassid='pg_class'::regclass
          AND dep.classid='pg_class'::regclass AND dep.deptype IN ('a','i')
        JOIN pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
        WHERE ns.nspname='public' AND tab.relname=$1
      `, [table])
      for (const { sequence_name: sequence } of sequences.rows) {
        await client.query(`REVOKE ALL ON SEQUENCE public.${qi(sequence)} FROM data_plane_builder`)
        await client.query(`GRANT USAGE, SELECT ON SEQUENCE public.${qi(sequence)} TO data_plane_builder`)
      }
    }
    await client.query(`
      REVOKE ALL ON TABLE public._migrations_applied FROM data_plane_migrator, data_plane_verifier;
      GRANT SELECT, INSERT ON TABLE public._migrations_applied TO data_plane_migrator;
      GRANT SELECT ON TABLE public._migrations_applied TO data_plane_verifier;
      REVOKE ALL ON SEQUENCE public._migrations_applied_id_seq FROM data_plane_migrator;
      GRANT USAGE ON SEQUENCE public._migrations_applied_id_seq TO data_plane_migrator;
    `)
    await client.query('RESET ROLE')
    await client.query(`
      REVOKE data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner FROM data_plane_builder, data_plane_verifier, amjis_app, role_orchestrator;
      REVOKE amjis_app FROM postgres;
      GRANT data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner TO data_plane_migrator;
    `)
    await normalizeDataPlaneMemberships(client)
    await client.query(`DO $$ BEGIN
      EXECUTE format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM data_plane_migrator, data_plane_builder, data_plane_verifier', current_database());
      EXECUTE format('GRANT CONNECT, TEMPORARY ON DATABASE %I TO data_plane_builder', current_database());
      EXECUTE format('GRANT CONNECT ON DATABASE %I TO data_plane_migrator, data_plane_verifier', current_database());
    END $$`)
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  } finally {
    client.release()
    await pool.end()
  }
}

if (require.main === module) {
  runDataPlaneOwnershipPreflight().catch((error) => {
    console.error(error)
    process.exitCode = 1
  })
}
