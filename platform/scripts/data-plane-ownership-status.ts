/** Read-only, semantic deployment gate for the DP-SD-018 protected boundary. */
import { Pool } from 'pg'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from './data-plane-ownership-preflight'

export type DataPlaneOwnershipStatus = 'marked' | 'unmarked'
const FILES = [
  '1035_data_plane_l1_producer_history.sql',
  '1036_data_plane_l2_producer_generations.sql',
] as const

const LIFECYCLE_FUNCTIONS = [
  'open_l1_data_plane_generation', 'l1_data_plane_capture_row',
  'capture_l1_data_plane_dasha_partition', 'complete_l1_data_plane_partition',
  'select_l1_data_plane_generation', 'rollback_l1_data_plane_generation',
  'assert_l2_msr_delete_safe', 'bind_l2_exact_inputs',
  'open_l2_data_plane_generation', 'l2_data_plane_capture_row',
  'complete_l2_data_plane_partition', 'select_l2_data_plane_generation',
  'rollback_l2_data_plane_generation',
] as const

export async function readDataPlaneOwnershipStatus(databaseUrl = process.env.DATABASE_URL): Promise<DataPlaneOwnershipStatus> {
  if (!databaseUrl) throw new Error('DATABASE_URL is required to read the data-plane ownership state.')
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  try {
    const marker = await pool.query<{ count: string }>(
      'SELECT count(*)::text AS count FROM public._migrations_applied WHERE filename = ANY($1::text[])',
      [[...FILES]],
    )
    const applied = Number(marker.rows[0]?.count ?? 0)
    const history = await pool.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relname IN ('l1_data_plane_generations','data_plane_l2_producer_generations')
    `)
    if (applied === 0 && Number(history.rows[0]?.count ?? 0) === 0) return 'unmarked'
    if (applied !== FILES.length) throw new Error('Partial DP-SD-018 migration marker state; refusing deployment.')

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
