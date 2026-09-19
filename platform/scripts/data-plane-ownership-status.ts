/** Read-only, semantic deployment gate for the DP-SD-018 protected boundary. */
import { Pool, type PoolConfig } from 'pg'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from './data-plane-ownership-preflight'
import { sqlIdentityOf } from './migrate'

export type DataPlaneOwnershipStatus = 'marked' | 'unmarked'
const FILES = [
  '1035_data_plane_l1_producer_history.sql',
  '1036_data_plane_l2_producer_generations.sql',
] as const
const L1_HISTORY = [
  'l1_data_plane_generations','l1_data_plane_generation_partitions','l1_data_plane_partition_contexts',
  'l1_data_plane_row_snapshots','l1_data_plane_fact_snapshots','l1_data_plane_dasha_snapshots',
  'l1_data_plane_configuration_snapshots','l1_data_plane_function_attestations','l1_data_plane_policy_attestations',
  'l1_data_plane_view_attestations','l1_data_plane_trigger_attestations',
  'l1_data_plane_sequence_attestations',
  'l1_data_plane_generation_heads','l1_data_plane_current_rows','l1_data_plane_current_dashas',
  'l1_data_plane_current_facts','l1_data_plane_current_configurations',
] as const
const L2_HISTORY = [
  'data_plane_l2_producer_generations','l2_data_plane_generation_partitions','l2_data_plane_generation_runs',
  'l2_data_plane_run_rows','l2_data_plane_partition_contexts','l2_data_plane_run_intents',
  'l2_data_plane_input_bind_receipts','l2_data_plane_row_snapshots','l2_data_plane_generation_heads',
  'l2_data_plane_asset_outputs','l2_data_plane_function_attestations','l2_data_plane_policy_attestations',
  'l2_data_plane_view_attestations','l2_data_plane_trigger_attestations',
  'l2_data_plane_sequence_attestations','l2_data_plane_manifest_attestations',
  'l2_data_plane_current_rows',
] as const

const LIFECYCLE_FUNCTIONS = [
  'open_l1_data_plane_generation', 'l1_data_plane_capture_row',
  'capture_l1_data_plane_dasha_partition', 'authorize_l1_chart_facts_delete', 'complete_l1_data_plane_partition',
  'select_l1_data_plane_generation', 'rollback_l1_data_plane_generation',
  'assert_l2_msr_delete_safe', 'bind_l2_exact_inputs',
  'open_l2_data_plane_generation', 'l2_data_plane_capture_row',
  'complete_l2_data_plane_partition', 'select_l2_data_plane_generation',
  'rollback_l2_data_plane_generation',
] as const

export async function readDataPlaneOwnershipStatus(
  database: string | Readonly<PoolConfig> | undefined = process.env.DATABASE_URL,
): Promise<DataPlaneOwnershipStatus> {
  if (!database) throw new Error('DATABASE_URL is required to read the data-plane ownership state.')
  const pool = new Pool(typeof database === 'string'
    ? { connectionString: database, max: 1 }
    : { ...database, max: 1 })
  try {
    const marker = await pool.query<{ count: string }>(
      'SELECT count(DISTINCT filename)::text AS count FROM public._migrations_applied WHERE filename = ANY($1::text[])',
      [[...FILES]],
    )
    const applied = Number(marker.rows[0]?.count ?? 0)
    const history = await pool.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relname IN ('l1_data_plane_generations','data_plane_l2_producer_generations')
    `)
    if (applied === 0 && Number(history.rows[0]?.count ?? 0) === 0) return 'unmarked'
    if (applied !== FILES.length) throw new Error('Partial DP-SD-018 migration marker state; refusing deployment.')

    const recorded = await pool.query<{ filename: string; sha256: string | null; sql_identity: string | null; copies: string }>(`
      SELECT filename, min(sha256) AS sha256, min(sql_identity) AS sql_identity, count(*)::text AS copies
      FROM public._migrations_applied WHERE filename=ANY($1::text[]) GROUP BY filename
    `, [[...FILES]])
    for (const filename of FILES) {
      const sql = readFileSync(resolve(__dirname, '../supabase/migrations', filename), 'utf8')
      const expectedHash = createHash('sha256').update(sql).digest('hex')
      const expectedIdentity = sqlIdentityOf(sql)
      const row = recorded.rows.find((candidate) => candidate.filename === filename)
      if (!row || row.copies !== '1' || !row.sha256 || !row.sql_identity
          || row.sha256 !== expectedHash || row.sql_identity !== expectedIdentity) {
        throw new Error(`${filename} has a missing, duplicate, or mismatched protected identity.`)
      }
    }

    const roles = await pool.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM pg_roles
      WHERE (rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner')
             AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole
             AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls)
         OR (rolname IN ('data_plane_migrator','data_plane_builder','data_plane_verifier')
             AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole
             AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls)
    `)
    if (Number(roles.rows[0]?.count ?? 0) !== 6) throw new Error('DP-SD-018 role normalization drift detected.')
    const unknownRoles = await pool.query<{ unsafe: boolean }>(`
      SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname LIKE 'data\\_plane\\_%' ESCAPE '\\'
        AND rolname<>ALL($1::text[])) AS unsafe
    `, [[
      'data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner',
      'data_plane_migrator','data_plane_builder','data_plane_verifier',
    ]])
    if (unknownRoles.rows[0]?.unsafe) throw new Error('Unknown data-plane principal detected.')

    const topology = await pool.query<{ schema_owner: string; bad_memberships: string; migrator_memberships: string }>(`
      SELECT
        pg_get_userbyid((SELECT nspowner FROM pg_namespace WHERE nspname='public')) AS schema_owner,
        (SELECT count(*)::text FROM pg_auth_members m JOIN pg_roles p ON p.oid=m.roleid JOIN pg_roles c ON c.oid=m.member
          WHERE p.rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner')
            AND c.rolname IN ('amjis_app','role_orchestrator','data_plane_builder','data_plane_verifier')) AS bad_memberships,
        (SELECT count(*)::text FROM pg_auth_members m JOIN pg_roles p ON p.oid=m.roleid JOIN pg_roles c ON c.oid=m.member
          WHERE p.rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner')
            AND c.rolname='data_plane_migrator') AS migrator_memberships
    `)
    const t = topology.rows[0]
    if (t?.schema_owner !== 'data_plane_schema_owner' || Number(t.bad_memberships) !== 0 || Number(t.migrator_memberships) !== 3) {
      throw new Error('DP-SD-018 protected role membership or schema-owner drift detected.')
    }
    const exactMemberships = await pool.query<{ unsafe: boolean }>(`
      WITH controlled(role_name) AS (SELECT unnest($1::text[])),
      actual AS (
        SELECT parent.rolname parent_role,member.rolname member_role
        FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid
        JOIN pg_roles member ON member.oid=m.member
        WHERE parent.rolname IN (SELECT role_name FROM controlled)
           OR member.rolname IN (SELECT role_name FROM controlled)
      ), expected(parent_role,member_role) AS (VALUES
        ('data_plane_schema_owner','data_plane_migrator'),
        ('data_plane_l1_owner','data_plane_migrator'),
        ('data_plane_l2_owner','data_plane_migrator')
      )
      SELECT EXISTS (SELECT 1 FROM actual a FULL JOIN expected e USING(parent_role,member_role)
        WHERE a.parent_role IS NULL OR e.parent_role IS NULL) AS unsafe
    `, [[
      'data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner',
      'data_plane_migrator','data_plane_builder','data_plane_verifier',
    ]])
    if (exactMemberships.rows[0]?.unsafe) throw new Error('Exact bidirectional data-plane role membership drift detected.')
    const recursiveMembership = await pool.query<{ unsafe: boolean }>(`
      WITH RECURSIVE reach(roleid, member) AS (
        SELECT roleid, member FROM pg_auth_members
        UNION
        SELECT r.roleid, m.member FROM reach r JOIN pg_auth_members m ON m.roleid=r.member
      )
      SELECT EXISTS (
        SELECT 1 FROM reach x JOIN pg_roles owner ON owner.oid=x.roleid
        JOIN pg_roles member ON member.oid=x.member
        WHERE owner.rolname=ANY($1::text[]) AND member.rolname<>'data_plane_migrator'
      ) AS unsafe
    `, [['data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner']])
    if (recursiveMembership.rows[0]?.unsafe) throw new Error('Recursive protected-owner membership drift detected.')

    for (const [owner, tables] of [['data_plane_l1_owner', L1_ACTIVE_TABLES], ['data_plane_l2_owner', L2_ACTIVE_TABLES]] as const) {
      const objects = await pool.query<{ count: string }>(`
        SELECT count(*)::text AS count FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public' AND c.relname=ANY($1::text[]) AND r.rolname=$2
      `, [[...tables], owner])
      if (Number(objects.rows[0]?.count ?? 0) !== tables.length) throw new Error(`${owner} protected table ownership drift detected.`)
      const sequences = await pool.query<{ bad: boolean }>(`
        SELECT EXISTS (
          SELECT 1 FROM pg_class tab JOIN pg_namespace ns ON ns.oid=tab.relnamespace
          JOIN pg_depend dep ON dep.refobjid=tab.oid AND dep.refclassid='pg_class'::regclass
            AND dep.classid='pg_class'::regclass AND dep.deptype IN ('a','i')
          JOIN pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
          JOIN pg_roles r ON r.oid=seq.relowner
          WHERE ns.nspname='public' AND tab.relname=ANY($1::text[]) AND r.rolname<>$2
        ) AS bad
      `, [[...tables], owner])
      if (sequences.rows[0]?.bad) throw new Error(`${owner} protected sequence ownership drift detected.`)
    }

    const exactRelations = await pool.query<{ unsafe: boolean }>(`
      WITH expected AS (
        SELECT name,'r'::"char" relation_kind,'data_plane_l1_owner' owner_name
        FROM unnest($1::text[]) name
        UNION ALL
        SELECT name,CASE WHEN name=ANY($2::text[]) THEN 'v'::"char" ELSE 'r'::"char" END,
               'data_plane_l1_owner' FROM unnest($3::text[]) name
        UNION ALL
        SELECT name,'r'::"char",'data_plane_l2_owner' FROM unnest($4::text[]) name
        UNION ALL
        SELECT name,CASE WHEN name=ANY($5::text[]) THEN 'v'::"char" ELSE 'r'::"char" END,
               'data_plane_l2_owner' FROM unnest($6::text[]) name
      ), actual AS (
        SELECT c.relname name,c.relkind relation_kind,pg_get_userbyid(c.relowner) owner_name
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m') AND (
          c.relname=ANY($7::text[]) OR starts_with(c.relname,'l1_data_plane_')
          OR starts_with(c.relname,'l2_data_plane_') OR c.relname='data_plane_l2_producer_generations'
        )
      )
      SELECT EXISTS (SELECT 1 FROM actual a FULL JOIN expected e
        USING(name,relation_kind,owner_name)
        WHERE a.name IS NULL OR e.name IS NULL) AS unsafe
    `, [
      [...L1_ACTIVE_TABLES],
      ['l1_data_plane_current_rows','l1_data_plane_current_dashas','l1_data_plane_current_facts','l1_data_plane_current_configurations'],
      [...L1_HISTORY],
      [...L2_ACTIVE_TABLES],
      ['l2_data_plane_current_rows'],
      [...L2_HISTORY],
      [...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES],
    ])
    if (exactRelations.rows[0]?.unsafe) throw new Error('Protected relation count, kind, or owner drift detected.')

    const exactSequences = await pool.query<{ unsafe: boolean }>(`
      WITH expected AS (
        SELECT * FROM public.l1_data_plane_sequence_attestations
        UNION ALL SELECT * FROM public.l2_data_plane_sequence_attestations
      ), actual AS (
        SELECT seq.relname sequence_name,tab.relname table_name,col.attname column_name,
               dep.deptype dependency_type,pg_get_userbyid(seq.relowner) owner_name
        FROM pg_class tab JOIN pg_namespace ns ON ns.oid=tab.relnamespace
        JOIN pg_attribute col ON col.attrelid=tab.oid AND col.attnum>0
        JOIN pg_depend dep ON dep.refobjid=tab.oid AND dep.refobjsubid=col.attnum
          AND dep.refclassid='pg_class'::regclass AND dep.classid='pg_class'::regclass
          AND dep.deptype IN ('a','i')
        JOIN pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
        WHERE ns.nspname='public' AND tab.relname=ANY($1::text[])
      )
      SELECT EXISTS (SELECT 1 FROM actual a FULL JOIN expected e
        USING(sequence_name,table_name,column_name,dependency_type,owner_name)
        WHERE a.sequence_name IS NULL OR e.sequence_name IS NULL) AS unsafe
    `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (exactSequences.rows[0]?.unsafe) throw new Error('Protected sequence count, kind, owner, or dependency drift detected.')

    const manifest = await pool.query<{ unsafe: boolean }>(`
      SELECT count(*)<>1 OR bool_or(manifest_name<>'l2_data_plane_asset_outputs')
        OR bool_or(definition_digest<>encode(digest(COALESCE((
          SELECT string_agg(asset_id||chr(31)||source_table,chr(30) ORDER BY asset_id,source_table)
          FROM public.l2_data_plane_asset_outputs
        ),''),'sha256'),'hex')) AS unsafe
      FROM public.l2_data_plane_manifest_attestations
    `)
    if (manifest.rows[0]?.unsafe) throw new Error('L2 asset-output manifest digest drift detected.')

    const sequenceAcl = await pool.query<{ unsafe: boolean }>(`
      WITH protected AS (
        SELECT DISTINCT seq.oid,seq.relowner
        FROM pg_class tab JOIN pg_namespace ns ON ns.oid=tab.relnamespace
        JOIN pg_depend dep ON dep.refobjid=tab.oid AND dep.refclassid='pg_class'::regclass
          AND dep.classid='pg_class'::regclass AND dep.deptype IN ('a','i')
        JOIN pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
        WHERE ns.nspname='public' AND tab.relname=ANY($1::text[])
      ), actual AS (
        SELECT p.oid,COALESCE(r.rolname,'PUBLIC') grantee,owner.rolname owner_name,a.privilege_type
        FROM protected p JOIN pg_class c ON c.oid=p.oid
        CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl,acldefault('S',c.relowner))) a
        LEFT JOIN pg_roles r ON r.oid=a.grantee
        JOIN pg_roles owner ON owner.oid=c.relowner
      ), expected(grantee,privilege_type) AS (VALUES
        ('data_plane_builder','SELECT'),('data_plane_builder','USAGE'),
        ('amjis_app','SELECT'),('data_plane_verifier','SELECT'),('data_plane_migrator','SELECT')
      )
      SELECT EXISTS (SELECT 1 FROM actual a WHERE
        a.grantee<>a.owner_name
        AND NOT EXISTS (SELECT 1 FROM expected e WHERE e.grantee=a.grantee AND e.privilege_type=a.privilege_type))
      OR EXISTS (SELECT 1 FROM protected p CROSS JOIN expected e
        WHERE NOT EXISTS (SELECT 1 FROM actual a WHERE a.oid=p.oid AND a.grantee=e.grantee AND a.privilege_type=e.privilege_type))
      AS unsafe
    `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (sequenceAcl.rows[0]?.unsafe) throw new Error('Protected sequence ACL allowlist drift detected.')

    const functions = await pool.query<{ count: string }>(`
      SELECT count(DISTINCT p.proname)::text AS count
      FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles r ON r.oid=p.proowner
      WHERE n.nspname='public' AND p.proname=ANY($1::text[]) AND p.prosecdef
        AND r.rolname IN ('data_plane_l1_owner','data_plane_l2_owner') AND NOT has_function_privilege('public',p.oid,'EXECUTE')
        AND 'search_path=pg_catalog, public, pg_temp'=ANY(COALESCE(p.proconfig, ARRAY[]::text[]))
    `, [[...LIFECYCLE_FUNCTIONS]])
    if (Number(functions.rows[0]?.count ?? 0) !== LIFECYCLE_FUNCTIONS.length) throw new Error('DP-SD-018 lifecycle function hardening drift detected.')

    const triggers = await pool.query<{ l1: string; l2: string }>(`
      SELECT
        count(*) FILTER (WHERE t.tgname='l1_data_plane_capture')::text AS l1,
        count(*) FILTER (WHERE t.tgname='l2_data_plane_capture')::text AS l2
      FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE NOT t.tgisinternal AND t.tgenabled IN ('O','A') AND n.nspname='public'
        AND ((t.tgname='l1_data_plane_capture' AND c.relname=ANY($1::text[]))
          OR (t.tgname='l2_data_plane_capture' AND c.relname=ANY($2::text[])))
    `, [L1_ACTIVE_TABLES.filter((table) => table !== 'chart_dashas'), [...L2_ACTIVE_TABLES]])
    if (Number(triggers.rows[0]?.l1) !== L1_ACTIVE_TABLES.length - 1 || Number(triggers.rows[0]?.l2) !== L2_ACTIVE_TABLES.length) {
      throw new Error('DP-SD-018 protected capture trigger drift detected.')
    }

    const triggerShape = await pool.query<{ unsafe: boolean }>(`
      SELECT EXISTS (
        SELECT 1 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid
        WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY($1::text[])
          AND (
            (t.tgname='l1_data_plane_mutation_guard' AND (t.tgtype<>31 OR p.oid<>'public.l1_data_plane_guard_active_mutation()'::regprocedure))
            OR (t.tgname='l1_data_plane_capture' AND (t.tgtype<>21 OR p.oid<>'public.l1_data_plane_capture_row()'::regprocedure))
            OR (t.tgname='l2_data_plane_mutation_guard' AND (t.tgtype<>31 OR p.oid<>'public.l2_data_plane_guard_active_mutation()'::regprocedure))
            OR (t.tgname='l2_data_plane_capture' AND (t.tgtype<>21 OR p.oid<>'public.l2_data_plane_capture_row()'::regprocedure))
          )
      ) OR (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
             JOIN pg_namespace n ON n.oid=c.relnamespace
             WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY($1::text[])
               AND t.tgname IN ('l1_data_plane_mutation_guard','l2_data_plane_mutation_guard')) <> cardinality($1::text[])
      AS unsafe
    `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (triggerShape.rows[0]?.unsafe) throw new Error('Protected mutation trigger OID/event/timing drift detected.')

    const triggerSurface = await pool.query<{ unsafe: boolean }>(`
      WITH expected AS (
        SELECT * FROM public.l1_data_plane_trigger_attestations
        UNION ALL SELECT * FROM public.l2_data_plane_trigger_attestations
      ), actual AS (
        SELECT c.relname table_name,t.tgname trigger_name,t.tgtype trigger_type,
               t.tgenabled enabled,t.tgfoid function_oid,t.tgfoid::regprocedure::text function_signature,
               encode(digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') definition_digest
        FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY($1::text[])
      )
      SELECT EXISTS (
        SELECT 1 FROM actual a FULL JOIN expected e
          ON a.table_name=e.table_name AND a.trigger_name=e.trigger_name
         AND a.trigger_type=e.trigger_type AND a.enabled=e.enabled
         AND a.function_oid=e.function_oid AND a.function_signature=e.function_signature
         AND a.definition_digest=e.definition_digest
        WHERE a.table_name IS NULL OR e.table_name IS NULL
      ) AS unsafe
    `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (triggerSurface.rows[0]?.unsafe) throw new Error('Protected trigger inventory or definition drift detected.')

    const functionDigests = await pool.query<{ unsafe: boolean }>(`
      SELECT EXISTS (
        SELECT 1 FROM (
          SELECT * FROM public.l1_data_plane_function_attestations
          UNION ALL SELECT * FROM public.l2_data_plane_function_attestations
        ) a
        LEFT JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature)
        WHERE p.oid IS NULL OR a.definition_digest<>encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex')
          OR a.owner_name<>pg_get_userbyid(p.proowner)
          OR a.security_definer<>p.prosecdef
          OR a.config IS DISTINCT FROM p.proconfig
      ) OR EXISTS (
        SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
        JOIN pg_roles owner ON owner.oid=p.proowner
        WHERE n.nspname='public' AND owner.rolname=ANY($1::text[])
          AND (p.proname LIKE 'l1_data_plane_%' OR p.proname LIKE 'l2_data_plane_%'
            OR p.proname=ANY($2::text[]))
          AND NOT EXISTS (
            SELECT 1 FROM (
              SELECT function_signature FROM public.l1_data_plane_function_attestations
              UNION ALL SELECT function_signature FROM public.l2_data_plane_function_attestations
            ) a WHERE p.oid=to_regprocedure('public.'||a.function_signature)
          )
      ) AS unsafe
    `, [
      ['data_plane_l1_owner','data_plane_l2_owner'],
      ['open_l1_data_plane_generation','capture_l1_data_plane_dasha_partition','authorize_l1_chart_facts_delete',
       'complete_l1_data_plane_partition','select_l1_data_plane_generation','rollback_l1_data_plane_generation',
       'assert_l2_msr_delete_safe','bind_l2_exact_inputs','open_l2_data_plane_generation',
       'complete_l2_data_plane_partition','select_l2_data_plane_generation','rollback_l2_data_plane_generation'],
    ])
    if (functionDigests.rows[0]?.unsafe) throw new Error('Protected function definition digest drift detected.')

    const catalogSurface = await pool.query<{ unsafe: boolean }>(`
      WITH expected_policies AS (
        SELECT * FROM public.l1_data_plane_policy_attestations
        UNION ALL SELECT * FROM public.l2_data_plane_policy_attestations
      ), expected_views AS (
        SELECT * FROM public.l1_data_plane_view_attestations
        UNION ALL SELECT * FROM public.l2_data_plane_view_attestations
      ), actual_policies AS (
        SELECT c.relname table_name,p.polname policy_name,p.polcmd command,
               p.polpermissive permissive,p.polroles role_oids,
               pg_get_expr(p.polqual,p.polrelid) using_expression,
               pg_get_expr(p.polwithcheck,p.polrelid) check_expression
        FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname=ANY($1::text[])
      ), actual_views AS (
        SELECT c.relname view_name,c.relkind relation_kind,
               encode(digest(pg_get_viewdef(c.oid,true),'sha256'),'hex') definition_digest,
               pg_get_userbyid(c.relowner) owner_name,c.reloptions options
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relkind IN ('v','m')
          AND (starts_with(c.relname, 'l1_data_plane_current_')
            OR starts_with(c.relname, 'l2_data_plane_current_'))
      )
      SELECT EXISTS (
        SELECT 1 FROM actual_policies a FULL JOIN expected_policies e
          ON a.table_name=e.table_name AND a.policy_name=e.policy_name
         AND a.command=e.command AND a.permissive=e.permissive AND a.role_oids=e.role_oids
         AND a.using_expression IS NOT DISTINCT FROM e.using_expression
         AND a.check_expression IS NOT DISTINCT FROM e.check_expression
        WHERE a.table_name IS NULL OR e.table_name IS NULL
      ) OR EXISTS (
        SELECT 1 FROM actual_views a FULL JOIN expected_views e
          ON a.view_name=e.view_name AND a.relation_kind=e.relation_kind
         AND a.definition_digest=e.definition_digest
         AND a.owner_name=e.owner_name AND a.options IS NOT DISTINCT FROM e.options
        WHERE a.view_name IS NULL OR e.view_name IS NULL
      )
        OR EXISTS (
          WITH actual AS (
            SELECT owner.rolname owner_name,ns.nspname namespace_name,d.defaclobjtype object_type,
                   COALESCE(grantee.rolname,'PUBLIC') grantee,a.privilege_type,a.is_grantable
            FROM pg_default_acl d JOIN pg_roles owner ON owner.oid=d.defaclrole
            LEFT JOIN pg_namespace ns ON ns.oid=d.defaclnamespace
            CROSS JOIN LATERAL aclexplode(d.defaclacl) a
            LEFT JOIN pg_roles grantee ON grantee.oid=a.grantee
            WHERE owner.rolname=ANY($2::text[])
          ), expected(owner_name,namespace_name,object_type,grantee,privilege_type,is_grantable) AS (VALUES
            ('data_plane_l1_owner',NULL::text,'f'::"char",'data_plane_l1_owner','EXECUTE',false),
            ('data_plane_l1_owner',NULL::text,'T'::"char",'data_plane_l1_owner','USAGE',false),
            ('data_plane_l2_owner',NULL::text,'f'::"char",'data_plane_l2_owner','EXECUTE',false),
            ('data_plane_l2_owner',NULL::text,'T'::"char",'data_plane_l2_owner','USAGE',false)
          )
          SELECT 1 FROM actual a FULL JOIN expected e
            ON a.owner_name=e.owner_name AND a.namespace_name IS NOT DISTINCT FROM e.namespace_name
           AND a.object_type=e.object_type AND a.grantee=e.grantee
           AND a.privilege_type=e.privilege_type AND a.is_grantable=e.is_grantable
          WHERE a.owner_name IS NULL OR e.owner_name IS NULL
        )
        AS unsafe
    `, [
      [...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES],
      ['data_plane_l1_owner','data_plane_l2_owner'],
    ])
    if (catalogSurface.rows[0]?.unsafe) throw new Error('Protected policies, views, or default privileges drift detected.')

    const aclSurface = await pool.query<{ unsafe: boolean }>(`
      WITH protected AS (
        SELECT c.oid,c.relname,CASE WHEN c.relname=ANY($1::text[]) THEN 'L1' ELSE 'L2' END layer
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname=ANY($2::text[])
      ), actual AS (
        SELECT p.relname,p.layer,COALESCE(r.rolname,'PUBLIC') grantee,owner.rolname owner_name,a.privilege_type
        FROM protected p JOIN pg_class c ON c.oid=p.oid
        CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl,acldefault('r',c.relowner))) a
        LEFT JOIN pg_roles r ON r.oid=a.grantee
        JOIN pg_roles owner ON owner.oid=c.relowner
      ), allowed(grantee,privilege_type) AS (VALUES
        ('data_plane_builder','SELECT'),('data_plane_builder','INSERT'),
        ('data_plane_builder','UPDATE'),('data_plane_builder','DELETE'),
        ('amjis_app','SELECT'),('data_plane_verifier','SELECT'),('data_plane_migrator','SELECT')
      )
      SELECT EXISTS (
        SELECT 1 FROM actual a WHERE
          NOT EXISTS (SELECT 1 FROM allowed x WHERE x.grantee=a.grantee AND x.privilege_type=a.privilege_type)
          AND NOT (a.layer='L1' AND a.grantee='data_plane_l2_owner' AND a.privilege_type='SELECT')
          AND a.grantee<>a.owner_name
      ) OR EXISTS (
        SELECT 1 FROM protected p CROSS JOIN allowed x
        WHERE NOT EXISTS (SELECT 1 FROM actual a WHERE a.relname=p.relname AND a.grantee=x.grantee AND a.privilege_type=x.privilege_type)
      ) AS unsafe
    `, [[...L1_ACTIVE_TABLES], [...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (aclSurface.rows[0]?.unsafe) throw new Error('Protected table ACL allowlist drift detected.')

    const historyAcl = await pool.query<{ unsafe: boolean }>(`
      WITH protected AS (
        SELECT c.oid,c.relname,CASE WHEN c.relname=ANY($1::text[]) THEN 'L1' ELSE 'L2' END layer,c.relowner,c.relacl
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname=ANY($2::text[])
      ), actual AS (
        SELECT p.relname,p.layer,COALESCE(r.rolname,'PUBLIC') grantee,owner.rolname owner_name,a.privilege_type
        FROM protected p CROSS JOIN LATERAL aclexplode(COALESCE(p.relacl,acldefault('r',p.relowner))) a
        LEFT JOIN pg_roles r ON r.oid=a.grantee
        JOIN pg_roles owner ON owner.oid=p.relowner
      )
      SELECT EXISTS (
        SELECT 1 FROM actual a WHERE
          a.grantee<>a.owner_name
          AND NOT (
            a.privilege_type='SELECT' AND a.grantee IN ('data_plane_builder','data_plane_verifier','data_plane_migrator','amjis_app')
          )
          AND NOT (a.layer='L1' AND a.grantee='data_plane_l2_owner' AND (
            a.privilege_type='SELECT' OR (a.relname='l1_data_plane_generation_heads' AND a.privilege_type='UPDATE')
          ))
      ) OR EXISTS (
        SELECT 1 FROM protected p CROSS JOIN unnest(ARRAY['data_plane_builder','data_plane_verifier','data_plane_migrator','amjis_app']) g
        WHERE NOT EXISTS (SELECT 1 FROM actual a WHERE a.relname=p.relname AND a.grantee=g AND a.privilege_type='SELECT')
      ) OR EXISTS (
        SELECT 1 FROM protected p WHERE p.layer='L1' AND NOT EXISTS (
          SELECT 1 FROM actual a WHERE a.relname=p.relname AND a.grantee='data_plane_l2_owner' AND a.privilege_type='SELECT'
        )
      ) OR NOT EXISTS (
        SELECT 1 FROM actual WHERE relname='l1_data_plane_generation_heads'
          AND grantee='data_plane_l2_owner' AND privilege_type='UPDATE'
      ) AS unsafe
    `, [[...L1_HISTORY], [...L1_HISTORY, ...L2_HISTORY]])
    if (historyAcl.rows[0]?.unsafe) throw new Error('Protected history/view ACL allowlist drift detected.')

    const schemaAcl = await pool.query<{ unsafe: boolean }>(`
      WITH actual AS (
        SELECT COALESCE(r.rolname,'PUBLIC') grantee,a.privilege_type
        FROM pg_namespace n
        CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl,acldefault('n',n.nspowner))) a
        LEFT JOIN pg_roles r ON r.oid=a.grantee WHERE n.nspname='public'
      ), expected(grantee,privilege_type) AS (VALUES
        ('data_plane_schema_owner','USAGE'),('data_plane_schema_owner','CREATE'),
        ('data_plane_l1_owner','USAGE'),('data_plane_l1_owner','CREATE'),
        ('data_plane_l2_owner','USAGE'),('data_plane_l2_owner','CREATE'),
        ('data_plane_migrator','USAGE'),('data_plane_builder','USAGE'),
        ('data_plane_verifier','USAGE'),('amjis_app','USAGE'),
        ('role_web_serve','USAGE')
      )
      SELECT EXISTS (SELECT 1 FROM actual a FULL JOIN expected e USING(grantee,privilege_type)
                     WHERE a.grantee IS NULL OR e.grantee IS NULL) AS unsafe
    `)
    if (schemaAcl.rows[0]?.unsafe) throw new Error('Public schema ACL allowlist drift detected.')

    const functionAcl = await pool.query<{ unsafe: boolean }>(`
      WITH protected AS (
        SELECT p.oid,p.proname,p.proacl,p.proowner
        FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
        WHERE n.nspname='public' AND EXISTS (
          SELECT 1 FROM (
            SELECT function_signature FROM public.l1_data_plane_function_attestations
            UNION ALL SELECT function_signature FROM public.l2_data_plane_function_attestations
          ) a WHERE p.oid=to_regprocedure('public.'||a.function_signature)
        )
      ), actual AS (
        SELECT p.proname,COALESCE(r.rolname,'PUBLIC') grantee,owner.rolname owner_name,a.privilege_type
        FROM protected p CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) a
        LEFT JOIN pg_roles r ON r.oid=a.grantee
        JOIN pg_roles owner ON owner.oid=p.proowner
      ), expected(grantee,proname) AS (VALUES
        ('data_plane_builder','open_l1_data_plane_generation'),('data_plane_builder','authorize_l1_chart_facts_delete'),('data_plane_builder','capture_l1_data_plane_dasha_partition'),
        ('data_plane_builder','complete_l1_data_plane_partition'),('data_plane_builder','select_l1_data_plane_generation'),
        ('data_plane_builder','assert_l2_msr_delete_safe'),('data_plane_builder','bind_l2_exact_inputs'),
        ('data_plane_builder','open_l2_data_plane_generation'),('data_plane_builder','complete_l2_data_plane_partition'),
        ('data_plane_builder','select_l2_data_plane_generation'),
        ('data_plane_verifier','select_l1_data_plane_generation'),('data_plane_verifier','select_l2_data_plane_generation'),
        ('amjis_app','select_l1_data_plane_generation'),('amjis_app','select_l2_data_plane_generation'),
        ('data_plane_migrator','select_l1_data_plane_generation'),('data_plane_migrator','select_l2_data_plane_generation'),
        ('data_plane_migrator','rollback_l1_data_plane_generation'),('data_plane_migrator','rollback_l2_data_plane_generation')
      )
      SELECT EXISTS (
        SELECT 1 FROM actual
        WHERE privilege_type='EXECUTE' AND (
          grantee<>owner_name AND (grantee='PUBLIC'
          OR grantee NOT IN ('data_plane_builder','data_plane_verifier','data_plane_migrator','amjis_app')
          OR (grantee IN ('data_plane_verifier','amjis_app') AND proname NOT IN ('select_l1_data_plane_generation','select_l2_data_plane_generation'))
          OR (grantee='data_plane_migrator' AND proname NOT IN ('select_l1_data_plane_generation','select_l2_data_plane_generation','rollback_l1_data_plane_generation','rollback_l2_data_plane_generation'))
          OR (grantee='data_plane_builder' AND proname NOT IN (
            'open_l1_data_plane_generation','authorize_l1_chart_facts_delete','capture_l1_data_plane_dasha_partition','complete_l1_data_plane_partition','select_l1_data_plane_generation',
            'assert_l2_msr_delete_safe','bind_l2_exact_inputs','open_l2_data_plane_generation','complete_l2_data_plane_partition','select_l2_data_plane_generation'
          )))
        )
      ) OR EXISTS (
        SELECT 1 FROM expected e WHERE NOT EXISTS (
          SELECT 1 FROM actual a WHERE a.grantee=e.grantee AND a.proname=e.proname AND a.privilege_type='EXECUTE'
        )
      ) AS unsafe
    `)
    if (functionAcl.rows[0]?.unsafe) throw new Error('Protected function EXECUTE ACL allowlist drift detected.')

    const privileges = await pool.query<{ unsafe: boolean }>(`
      SELECT has_schema_privilege('amjis_app','public','CREATE')
          OR has_schema_privilege('data_plane_builder','public','CREATE')
          OR EXISTS (SELECT 1 FROM unnest($1::text[]) tab
             WHERE has_table_privilege('data_plane_builder', format('public.%I',tab), 'TRUNCATE,TRIGGER,REFERENCES'))
          OR EXISTS (SELECT 1 FROM unnest($1::text[]) tab
             WHERE has_table_privilege('amjis_app', format('public.%I',tab), 'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER'))
          OR EXISTS (SELECT 1 FROM unnest($1::text[]) tab
             WHERE has_table_privilege('role_orchestrator', format('public.%I',tab), 'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER'))
        AS unsafe
    `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    if (privileges.rows[0]?.unsafe) throw new Error('DP-SD-018 protected write or DDL privilege drift detected.')
    return 'marked'
  } finally { await pool.end() }
}

if (require.main === module) readDataPlaneOwnershipStatus().then((state) => process.stdout.write(`${state}\n`)).catch((error) => {
  console.error(error); process.exitCode = 1
})
