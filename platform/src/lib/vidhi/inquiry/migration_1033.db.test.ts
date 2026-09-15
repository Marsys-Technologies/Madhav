import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { __resetInquiryStorePoolForTests, getInquiryStorePool } from './store_pool'
import {
  commitInquiryObservation,
  createInquiryLifecycle,
  failCloseAmbiguousInquiryAction,
  getInquiryLifecycle,
  markInquiryActionDispatched,
  reserveInquiryAction,
} from './lifecycle_store'
import type { InquiryContract } from './types'

const databaseUrl = process.env.PURNA_ANVESANA_W5_DATABASE_URL
const describeDisposable = databaseUrl ? describe.sequential : describe.skip
const migrationSql = readFileSync(
  resolve(__dirname, '../../../../migrations/1033_planner_inquiry_lifecycle.sql'),
  'utf8',
)
const reservationMigrationSql = readFileSync(
  resolve(__dirname, '../../../../migrations/1037_planner_inquiry_action_reservations.sql'),
  'utf8',
)

const principalA = 'purna-w5-principal-a'
const principalB = 'purna-w5-principal-b'
const quotaPrincipal = 'purna-w5-quota-principal'
const chartA = '00000000-0000-4000-8000-000000000501'
const chartB = '00000000-0000-4000-8000-000000000502'
const inquiryA = '00000000-0000-4000-8000-000000000511'
const inquiryB = '00000000-0000-4000-8000-000000000512'
const inquiryC = '00000000-0000-4000-8000-000000000514'
const inquiryD = '00000000-0000-4000-8000-000000000515'

function assertDisposableUrl(value: string): void {
  const parsed = new URL(value)
  if (!['127.0.0.1', 'localhost', '::1'].includes(parsed.hostname)) {
    throw new Error('PURNA_ANVESANA_W5_DATABASE_URL must target localhost')
  }
  if (!parsed.pathname.slice(1).startsWith('purna_w5_')) {
    throw new Error('PURNA_ANVESANA_W5_DATABASE_URL database must start with purna_w5_')
  }
}

async function inWebContext<T>(
  pool: Pool,
  principal: string,
  chartId: string,
  action: (client: PoolClient) => Promise<T>,
): Promise<T> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query('SET LOCAL ROLE role_web_serve')
    await client.query(
      'SELECT set_config($1, $2, true), set_config($3, $4, true)',
      ['app.principal_id', principal, 'app.chart_context', chartId],
    )
    const result = await action(client)
    await client.query('COMMIT')
    return result
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
  }
}

function lifecycleValues(inquiryId: string, principal: string, chartId: string) {
  return [
    inquiryId,
    principal,
    chartId,
    'sha256:semantic',
    'sha256:execution',
    'sha256:capability',
    'planner-scu-v1',
    'sha256:overlay-v1',
    'build-v1',
    JSON.stringify({ contract_id: `contract:${inquiryId}`, immutable: true }),
    JSON.stringify({ contract_id: `contract:${inquiryId}`, status: 'INCOMPLETE' }),
    'sha256:jti-0',
  ]
}

const insertLifecycle = `
  INSERT INTO planner_inquiry_lifecycles
    (inquiry_id, principal_uid, chart_id, semantic_contract_hash, execution_plan_hash,
     capability_content_hash, capability_compatibility_version, chart_overlay_version,
     chart_build_id, authorization_jsonb, contract_jsonb, current_jti_hash, expires_at)
  VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb,$12,now() + interval '1 hour')
`

function createLifecycle(client: PoolClient, inquiryId: string, principal: string, chartId: string) {
  return client.query(
    `SELECT * FROM create_planner_inquiry_lifecycle(
       $1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb,'INCOMPLETE',$12,now() + interval '1 hour'
     )`,
    lifecycleValues(inquiryId, principal, chartId),
  )
}

function documentedDownSql(sql: string): string {
  const section = sql.split('-- DOWN (manual, destructive; retain/export evidence before use):')[1]
  const statements = section?.split('\n').flatMap((line) => {
    const match = line.match(/^-- (DROP .+;)$/)
    return match ? [match[1]] : []
  }) ?? []
  if (statements.length !== 5) throw new Error('migration 1033 documented DOWN block is incomplete')
  return statements.join('\n')
}

const downSql = documentedDownSql(migrationSql)

function lifecycleContract(): InquiryContract {
  return {
    contract_version: '1.3.0', compiler_version: '2.0.0',
    contract_id: 'sha256:contract-c', semantic_contract_hash: 'sha256:semantic-c',
    execution_plan_hash: 'sha256:execution-c', chart_id: chartA,
    execution_channel: 'mcp_full', question: 'disposable lifecycle proof',
    scope_tuple: {
      intent: 'explain', domains: ['wealth'], width: 'focused', depth: 'standard',
      horizon: 'timeless', intervention: false, entitlement: 'native',
    },
    capability_compatibility_version: 'planner-scu-v2',
    capability_content_hash: 'sha256:capability-c',
    chart_availability_version: 'sha256:overlay-c', chart_build_id: 'build-c',
    obligations: [{
      obligation_id: 'obl-c', label: 'Lifecycle proof', source: 'deterministic_floor',
      materiality: 'required', scu_ids: ['scu.c'], rationale: 'fixture',
      disposition: 'pending', evidence_refs: [], gap_reason: null,
    }],
    plan_items: [{
      item_id: 'item-001', obligation_ids: ['obl-c'], scu_id: 'scu.c',
      binding_id: 'registry:marsys://tool/L1/c', args: {}, authorization_args: {},
      depends_on: [], state: 'ready', blocked_reason: null, observation: null,
    }],
    material_frontier: [], omission_findings: [], ai_hypotheses: [],
    status: 'INCOMPLETE', status_reasons: ['finalization_required'], iteration: 0, max_iterations: 3,
  }
}

describeDisposable('migration 1033 disposable PostgreSQL acceptance', () => {
  let pool: Pool
  let servePool: Pool | undefined
  let downApplied = false

  beforeAll(async () => {
    assertDisposableUrl(databaseUrl!)
    pool = new Pool({ connectionString: databaseUrl, max: 8 })
    await pool.query(`
      DO $$ BEGIN
        CREATE ROLE role_web_serve NOLOGIN;
      EXCEPTION WHEN duplicate_object THEN NULL;
      END $$;
      DO $$ BEGIN
        CREATE ROLE purna_inquiry_owner NOLOGIN NOINHERIT;
      EXCEPTION WHEN duplicate_object THEN NULL;
      END $$;
      DO $$ BEGIN
        CREATE ROLE purna_w5_web LOGIN PASSWORD 'purna_w5_web_test_only';
      EXCEPTION WHEN duplicate_object THEN NULL;
      END $$;
      ALTER ROLE purna_w5_web PASSWORD 'purna_w5_web_test_only';
      GRANT role_web_serve TO purna_w5_web;
      CREATE TABLE IF NOT EXISTS profiles (id text PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS charts (id uuid PRIMARY KEY);
      CREATE OR REPLACE FUNCTION app_chart_context()
      RETURNS uuid LANGUAGE sql STABLE AS $$
        SELECT NULLIF(current_setting('app.chart_context', true), '')::uuid
      $$;
      GRANT USAGE, CREATE ON SCHEMA public TO purna_inquiry_owner;
      GRANT REFERENCES (id) ON TABLE profiles, charts TO purna_inquiry_owner;
      GRANT purna_inquiry_owner TO CURRENT_USER WITH ADMIN OPTION;
      INSERT INTO profiles(id) VALUES ('${principalA}'), ('${principalB}'), ('${quotaPrincipal}') ON CONFLICT DO NOTHING;
      INSERT INTO charts(id) VALUES ('${chartA}'), ('${chartB}') ON CONFLICT DO NOTHING;
    `)
  })

  afterAll(async () => {
    if (!pool) return
    if (servePool) await __resetInquiryStorePoolForTests()
    if (!downApplied) {
      await pool.query('DROP TABLE IF EXISTS planner_inquiry_action_reservations').catch(() => undefined)
      await pool.query('DROP FUNCTION IF EXISTS planner_inquiry_action_reservation_guard()').catch(() => undefined)
      await pool.query(downSql).catch(() => undefined)
    }
    await pool.end()
  })

  it('rolls back every migration object when the transaction fails before commit', async () => {
    const schema = 'purna_w7_migration_rollback'
    const client = await pool.connect()
    try {
      await client.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await client.query(`CREATE SCHEMA ${schema}`)
      await client.query(`SET search_path TO ${schema}, public`)
      const forcedFailureSql = migrationSql.replace(
        '\nCOMMIT;\n',
        "\nSELECT 1 / 0; -- disposable proof: force failure inside the migration transaction\nCOMMIT;\n",
      )
      await expect(client.query(forcedFailureSql)).rejects.toMatchObject({ code: '22012' })
      await client.query('ROLLBACK')
      const objects = await client.query<{ table_count: string; function_count: string }>(`
        SELECT
          (SELECT count(*)::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname=$1 AND c.relname IN ('planner_inquiry_lifecycles','planner_inquiry_evidence_receipts')) AS table_count,
          (SELECT count(*)::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname=$1 AND p.proname IN ('planner_inquiry_immutable_guard','create_planner_inquiry_lifecycle','purge_expired_planner_inquiries_global')) AS function_count
      `, [schema])
      expect(objects.rows[0]).toEqual({ table_count: '0', function_count: '0' })
    } finally {
      await client.query('RESET search_path').catch(() => undefined)
      await client.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`).catch(() => undefined)
      client.release()
    }
  })

  it('applies and replays the up migration without broadening serving-role grants', async () => {
    await pool.query(migrationSql)
    await pool.query(migrationSql)
    await pool.query(reservationMigrationSql)
    await pool.query(reservationMigrationSql)

    const catalog = await pool.query<{ relname: string; relrowsecurity: boolean }>(`
      SELECT relname, relrowsecurity
      FROM pg_class
      WHERE relname IN ('planner_inquiry_lifecycles', 'planner_inquiry_evidence_receipts', 'planner_inquiry_action_reservations')
      ORDER BY relname
    `)
    expect(catalog.rows).toEqual([
      { relname: 'planner_inquiry_action_reservations', relrowsecurity: true },
      { relname: 'planner_inquiry_evidence_receipts', relrowsecurity: true },
      { relname: 'planner_inquiry_lifecycles', relrowsecurity: true },
    ])

    const privileges = await pool.query<{ table_name: string; privilege_type: string }>(`
      SELECT table_name, privilege_type
      FROM information_schema.role_table_grants
      WHERE grantee='role_web_serve'
        AND table_name IN ('planner_inquiry_lifecycles', 'planner_inquiry_evidence_receipts', 'planner_inquiry_action_reservations')
      ORDER BY table_name, privilege_type
    `)
    expect(privileges.rows).toEqual([
      { table_name: 'planner_inquiry_action_reservations', privilege_type: 'INSERT' },
      { table_name: 'planner_inquiry_action_reservations', privilege_type: 'SELECT' },
      { table_name: 'planner_inquiry_evidence_receipts', privilege_type: 'INSERT' },
      { table_name: 'planner_inquiry_evidence_receipts', privilege_type: 'SELECT' },
      { table_name: 'planner_inquiry_lifecycles', privilege_type: 'SELECT' },
    ])
    const updateColumns = await pool.query<{ column_name: string }>(`
      SELECT column_name
      FROM information_schema.role_column_grants
      WHERE grantee='role_web_serve'
        AND table_name='planner_inquiry_lifecycles'
        AND privilege_type='UPDATE'
      ORDER BY column_name
    `)
    expect(updateColumns.rows.map((row) => row.column_name)).toEqual([
      'contract_jsonb',
      'current_jti_hash',
      'revision',
      'status',
      'updated_at',
    ])
    const reservationUpdateColumns = await pool.query<{ column_name: string }>(`
      SELECT column_name
      FROM information_schema.role_column_grants
      WHERE grantee='role_web_serve'
        AND table_name='planner_inquiry_action_reservations'
        AND privilege_type='UPDATE'
      ORDER BY column_name
    `)
    expect(reservationUpdateColumns.rows.map((row) => row.column_name)).toEqual([
      'committed_at',
      'dispatch_started_at',
      'lease_expires_at',
      'reservation_hash',
      'state',
    ])
  })

  it('isolates lifecycle and receipt rows by both authenticated subject and chart', async () => {
    await inWebContext(pool, principalA, chartA, async (client) => {
      await createLifecycle(client, inquiryA, principalA, chartA)
      await client.query(
        `INSERT INTO planner_inquiry_evidence_receipts
          (inquiry_id, revision, obligation_ids, plan_item_id, scu_id, binding_id,
           canonical_args_hash, raw_result_hash, disposition, evidence_jsonb)
         VALUES ($1,1,ARRAY['obligation-a'],'item-001','scu.a','registry:a',
                 'sha256:args','sha256:result','served','{"rows":[1]}'::jsonb)`,
        [inquiryA],
      )
      await client.query(
        `INSERT INTO planner_inquiry_action_reservations
           (inquiry_id, revision, plan_item_id, source_jti_hash, reservation_hash, lease_expires_at)
         VALUES ($1,0,'item-002','sha256:jti-isolation','sha256:reservation-isolation',now() + interval '1 minute')`,
        [inquiryA],
      )
    })
    await inWebContext(pool, principalB, chartB, async (client) => {
      await createLifecycle(client, inquiryB, principalB, chartB)
    })

    for (const [principal, chartId, expected] of [
      [principalA, chartA, 1],
      [principalA, chartB, 0],
      [principalB, chartA, 0],
    ] as const) {
      await inWebContext(pool, principal, chartId, async (client) => {
        const lifecycles = await client.query('SELECT inquiry_id FROM planner_inquiry_lifecycles')
        const receipts = await client.query('SELECT receipt_id FROM planner_inquiry_evidence_receipts')
        const reservations = await client.query('SELECT plan_item_id FROM planner_inquiry_action_reservations')
        expect(lifecycles.rowCount).toBe(expected)
        expect(receipts.rowCount).toBe(principal === principalA && chartId === chartA ? 1 : 0)
        expect(reservations.rowCount).toBe(principal === principalA && chartId === chartA ? 1 : 0)
      })
    }

    await expect(inWebContext(pool, principalB, chartB, (client) =>
      client.query(insertLifecycle, lifecycleValues(
        '00000000-0000-4000-8000-000000000513',
        principalA,
        chartA,
      )),
    )).rejects.toMatchObject({ code: '42501' })
  })

  it('makes quota, creation timestamps and 30-day retention impossible to bypass', async () => {
    await expect(inWebContext(pool, quotaPrincipal, chartA, (client) =>
      client.query(
        `INSERT INTO planner_inquiry_lifecycles
          (inquiry_id, principal_uid, chart_id, semantic_contract_hash, execution_plan_hash,
           capability_content_hash, capability_compatibility_version, chart_overlay_version,
           chart_build_id, authorization_jsonb, contract_jsonb, current_jti_hash, expires_at,
           created_at, retention_expires_at)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb,$12,
                 now() + interval '1 hour', now() - interval '100 years',
                 now() + interval '100 years')`,
        lifecycleValues('00000000-0000-4000-8000-000000000590', quotaPrincipal, chartA),
      ),
    )).rejects.toMatchObject({ code: '42501' })

    await inWebContext(pool, quotaPrincipal, chartA, async (client) => {
      for (let index = 0; index < 8; index += 1) {
        await createLifecycle(
          client,
          `00000000-0000-4000-8000-${String(600 + index).padStart(12, '0')}`,
          quotaPrincipal,
          chartA,
        )
      }
    })
    await expect(inWebContext(pool, quotaPrincipal, chartA, (client) =>
      createLifecycle(client, '00000000-0000-4000-8000-000000000608', quotaPrincipal, chartA),
    )).rejects.toThrow('INQUIRY_ACTIVE_LIMIT_REACHED')

    const bounds = await pool.query<{ count: string; timestamps_pinned: boolean; retention_pinned: boolean }>(`
      SELECT count(*)::text AS count,
             bool_and(created_at > now() - interval '5 minutes') AS timestamps_pinned,
             bool_and(retention_expires_at BETWEEN now() + interval '29 days'
                                           AND now() + interval '31 days') AS retention_pinned
      FROM planner_inquiry_lifecycles
      WHERE principal_uid=$1 AND chart_id=$2
    `, [quotaPrincipal, chartA])
    expect(bounds.rows[0]).toEqual({ count: '8', timestamps_pinned: true, retention_pinned: true })
  })

  it('keeps evidence receipts append-only for the serving role', async () => {
    await expect(inWebContext(pool, principalA, chartA, (client) =>
      client.query(
        'UPDATE planner_inquiry_evidence_receipts SET evidence_jsonb=$1 WHERE inquiry_id=$2',
        [JSON.stringify({ forged: true }), inquiryA],
      ),
    )).rejects.toMatchObject({ code: '42501' })
    await expect(inWebContext(pool, principalA, chartA, (client) =>
      client.query(
        `UPDATE planner_inquiry_action_reservations
            SET state='committed', committed_at=now()
          WHERE inquiry_id=$1 AND plan_item_id='item-002'`,
        [inquiryA],
      ),
    )).rejects.toThrow('invalid planner inquiry action state transition')

    await expect(inWebContext(pool, principalA, chartA, (client) =>
      client.query('DELETE FROM planner_inquiry_evidence_receipts WHERE inquiry_id=$1', [inquiryA]),
    )).rejects.toMatchObject({ code: '42501' })

    const retained = await inWebContext(pool, principalA, chartA, (client) =>
      client.query<{ evidence_jsonb: unknown }>(
        'SELECT evidence_jsonb FROM planner_inquiry_evidence_receipts WHERE inquiry_id=$1',
        [inquiryA],
      ),
    )
    expect(retained.rows).toEqual([{ evidence_jsonb: { rows: [1] } }])

    await expect(inWebContext(pool, principalA, chartA, (client) =>
      client.query('DELETE FROM planner_inquiry_action_reservations WHERE inquiry_id=$1', [inquiryA]),
    )).rejects.toMatchObject({ code: '42501' })
    await expect(inWebContext(pool, principalA, chartA, (client) =>
      client.query(
        'UPDATE planner_inquiry_action_reservations SET source_jti_hash=$1 WHERE inquiry_id=$2',
        ['sha256:forged', inquiryA],
      ),
    )).rejects.toMatchObject({ code: '42501' })
  })

  it('allows exactly one compare-and-swap winner and rejects receipt replay', async () => {
    const compete = (nextHash: string) => inWebContext(pool, principalA, chartA, (client) =>
      client.query(
        `UPDATE planner_inquiry_lifecycles
         SET revision=revision+1, current_jti_hash=$1, updated_at=now()
         WHERE inquiry_id=$2 AND revision=0 AND current_jti_hash='sha256:jti-0'
         RETURNING revision`,
        [nextHash, inquiryA],
      ).then((result) => result.rowCount),
    )
    const winners = await Promise.all([compete('sha256:winner-a'), compete('sha256:winner-b')])
    expect(winners.sort()).toEqual([0, 1])

    await expect(inWebContext(pool, principalA, chartA, (client) =>
      client.query(
        `INSERT INTO planner_inquiry_evidence_receipts
          (inquiry_id, revision, obligation_ids, plan_item_id, scu_id, binding_id,
           canonical_args_hash, raw_result_hash, disposition, evidence_jsonb)
         VALUES ($1,1,ARRAY['obligation-replay'],'item-001','scu.a','registry:a',
                 'sha256:args','sha256:result','served','{}'::jsonb)`,
        [inquiryA],
      ),
    )).rejects.toMatchObject({ code: '23505' })
  })

  it('runs lifecycle-store creation, reservation and observation through the RLS role', async () => {
    const serveUrl = new URL(databaseUrl!)
    serveUrl.username = 'purna_w5_web'
    serveUrl.password = 'purna_w5_web_test_only'
    process.env.INQUIRY_STORE_DATABASE_URL = serveUrl.toString()
    servePool = await getInquiryStorePool()

    const contract = lifecycleContract()
    const created = await createInquiryLifecycle({
      inquiry_id: inquiryC,
      principal_uid: principalA,
      contract,
      jti_hash: 'sha256:jti-c',
      expires_at: '2099-01-01T00:00:00.000Z',
    })
    const stored = await getInquiryLifecycle(inquiryC, principalA, chartA)
    expect(stored).toMatchObject({ inquiry_id: inquiryC, revision: 0, current_jti_hash: 'sha256:jti-c' })

    const attempts = await Promise.allSettled([
      reserveInquiryAction({ row: created, expected_jti_hash: 'sha256:jti-c', reservation_hash: 'sha256:reservation-a', plan_item_id: 'item-001' }),
      reserveInquiryAction({ row: created, expected_jti_hash: 'sha256:jti-c', reservation_hash: 'sha256:reservation-b', plan_item_id: 'item-001' }),
    ])
    expect(attempts.filter((result) => result.status === 'fulfilled')).toHaveLength(1)
    expect(attempts.filter((result) => result.status === 'rejected')).toHaveLength(1)
    const winner = attempts[0].status === 'fulfilled' ? 'sha256:reservation-a' : 'sha256:reservation-b'
    await markInquiryActionDispatched({ row: created, plan_item_id: 'item-001', reservation_hash: winner })

    const observed: InquiryContract = {
      ...contract,
      obligations: contract.obligations.map((obligation) => ({
        ...obligation, disposition: 'served', evidence_refs: ['raw:sha256:result-c'],
      })),
      plan_items: contract.plan_items.map((item) => ({
        ...item, state: 'observed', observation: {
          disposition: 'served', evidence_refs: ['raw:sha256:result-c'], gap_reason: null,
        },
      })),
      iteration: 1,
    }
    const receiptId = await commitInquiryObservation({
      row: created,
      expected_jti_hash: winner,
      next_jti_hash: 'sha256:jti-c-next',
      contract: observed,
      evidence: {
        plan_item_id: 'item-001', obligation_ids: ['obl-c'], scu_id: 'scu.c',
        binding_id: 'registry:marsys://tool/L1/c', canonical_args_hash: 'sha256:args-c',
        raw_result_hash: 'sha256:result-c', disposition: 'served',
        pagination: { semantics: 'none', exhausted: true, next: null },
        payload: { trace_id: 'trace-c', result_bytes: 8 },
      },
    })
    expect(receiptId).toMatch(/^[0-9a-f-]{36}$/)
    expect(await getInquiryLifecycle(inquiryC, principalA, chartA)).toMatchObject({
      revision: 1,
      current_jti_hash: 'sha256:jti-c-next',
    })
    await expect(commitInquiryObservation({
      row: created,
      expected_jti_hash: winner,
      next_jti_hash: 'sha256:forged-replay',
      contract: observed,
      evidence: {
        plan_item_id: 'item-001', obligation_ids: ['obl-c'], scu_id: 'scu.c',
        binding_id: 'registry:marsys://tool/L1/c', canonical_args_hash: 'sha256:args-c',
        raw_result_hash: 'sha256:result-c', disposition: 'served',
        pagination: { semantics: 'none', exhausted: true, next: null }, payload: {},
      },
    })).rejects.toThrow('INQUIRY_TOKEN_REPLAYED_OR_STALE')
  })

  it('recovers only a pre-dispatch expired lease and fails closed after the dispatch boundary', async () => {
    const contract = lifecycleContract()
    const created = await createInquiryLifecycle({
      inquiry_id: inquiryD,
      principal_uid: principalA,
      contract,
      jti_hash: 'sha256:jti-d',
      expires_at: '2099-01-01T00:00:00.000Z',
    })
    const first = await reserveInquiryAction({
      row: created,
      expected_jti_hash: 'sha256:jti-d',
      reservation_hash: 'sha256:reservation-d1',
      plan_item_id: 'item-001',
      lease_seconds: 1,
    })
    expect(first).toEqual({ status: 'acquired', reservation_hash: 'sha256:reservation-d1', recovered: false })

    await new Promise((resolveDelay) => setTimeout(resolveDelay, 1_100))
    const recovered = await reserveInquiryAction({
      row: created,
      expected_jti_hash: 'sha256:jti-d',
      reservation_hash: 'sha256:reservation-d2',
      plan_item_id: 'item-001',
      lease_seconds: 1,
    })
    expect(recovered).toEqual({ status: 'acquired', reservation_hash: 'sha256:reservation-d2', recovered: true })
    await markInquiryActionDispatched({
      row: created,
      plan_item_id: 'item-001',
      reservation_hash: 'sha256:reservation-d2',
      dispatch_timeout_seconds: 1,
    })

    const overlapping = await reserveInquiryAction({
      row: created,
      expected_jti_hash: 'sha256:jti-d',
      reservation_hash: 'sha256:reservation-d3',
      plan_item_id: 'item-001',
    })
    expect(overlapping).toMatchObject({ status: 'in_progress', reservation_hash: 'sha256:reservation-d2' })
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 1_100))
    const retry = await reserveInquiryAction({
      row: created,
      expected_jti_hash: 'sha256:jti-d',
      reservation_hash: 'sha256:reservation-d4',
      plan_item_id: 'item-001',
    })
    expect(retry).toEqual({ status: 'ambiguous', reservation_hash: 'sha256:reservation-d2' })
    const blocked = {
      ...contract,
      status: 'BLOCKED' as const,
      status_reasons: ['dispatch outcome became ambiguous after the at-most-once boundary'],
    }
    await failCloseAmbiguousInquiryAction({
      row: created,
      expected_source_jti_hash: 'sha256:jti-d',
      plan_item_id: 'item-001',
      contract: blocked,
    })
    expect(await getInquiryLifecycle(inquiryD, principalA, chartA)).toMatchObject({
      status: 'BLOCKED',
      revision: 1,
      current_jti_hash: 'terminal',
      contract_jsonb: { status: 'BLOCKED' },
    })
    expect((await pool.query(
      'SELECT state FROM planner_inquiry_action_reservations WHERE inquiry_id=$1',
      [inquiryD],
    )).rows).toEqual([{ state: 'failed_closed' }])
  })

  it('fails closed when immutable authorization or overlay identity is changed', async () => {
    for (const statement of [
      `UPDATE planner_inquiry_lifecycles
       SET authorization_jsonb='{"forged":true}'::jsonb WHERE inquiry_id=$1`,
      `UPDATE planner_inquiry_lifecycles
       SET chart_overlay_version='sha256:overlay-v2' WHERE inquiry_id=$1`,
      `UPDATE planner_inquiry_lifecycles
       SET chart_build_id='build-v2' WHERE inquiry_id=$1`,
    ]) {
      await expect(pool.query(statement, [inquiryA])).rejects.toThrow(
        'planner inquiry immutable authorization cannot change',
      )
    }
  })

  it('applies the documented down migration and removes every Wave 5 object', async () => {
    await pool.query('DROP TABLE IF EXISTS planner_inquiry_action_reservations')
    await pool.query('DROP FUNCTION IF EXISTS planner_inquiry_action_reservation_guard()')
    await pool.query(downSql)
    downApplied = true
    const objects = await pool.query<{ tables: Array<string | null>; functions: Array<string | null> }>(`
      SELECT
        ARRAY[
          to_regclass('public.planner_inquiry_lifecycles')::text,
          to_regclass('public.planner_inquiry_evidence_receipts')::text
        ] AS tables,
        ARRAY[
          to_regprocedure('public.purge_expired_planner_inquiries_global()')::text,
          to_regprocedure('public.create_planner_inquiry_lifecycle(uuid,text,uuid,text,text,text,text,text,text,jsonb,jsonb,text,text,timestamp with time zone)')::text,
          to_regprocedure('public.planner_inquiry_immutable_guard()')::text
        ] AS functions
    `)
    expect(objects.rows[0]).toEqual({ tables: [null, null], functions: [null, null, null] })
  })
})
