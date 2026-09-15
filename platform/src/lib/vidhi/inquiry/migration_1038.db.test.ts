import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

const databaseUrl = process.env.PURNA_ANVESANA_W7_DATABASE_URL
const describeDisposable = databaseUrl ? describe.sequential : describe.skip
const migrationSql = readFileSync(
  resolve(__dirname, '../../../../supabase/migrations/1038_planner_managed_prashna_jobs.sql'),
  'utf8',
)
const principalA = 'purna-w7-job-principal-a'
const principalB = 'purna-w7-job-principal-b'
const principalToDelete = 'purna-w7-job-principal-delete'
const keyA = 'key-a'
const keyB = 'key-b'
const keyToRevoke = 'key-to-revoke'
const keyForDeletedPrincipal = 'key-profile-delete'
const oauthHash = 'a'.repeat(64)
const oauthKey = `oauth_sha256:${oauthHash}`
const chartA = '00000000-0000-4000-8000-000000000701'
const chartToDelete = '00000000-0000-4000-8000-000000000702'
const jobA = '00000000-0000-4000-8000-000000000711'
const jobB = '00000000-0000-4000-8000-000000000712'

function assertDisposableUrl(value: string): void {
  const parsed = new URL(value)
  if (!['127.0.0.1', 'localhost', '::1'].includes(parsed.hostname)
    || !parsed.pathname.slice(1).startsWith('purna_w7_')) {
    throw new Error('PURNA_ANVESANA_W7_DATABASE_URL must target a localhost purna_w7_* database')
  }
}

async function inPrincipal<T>(
  pool: Pool,
  principal: string,
  action: (client: PoolClient) => Promise<T>,
  chartId?: string,
): Promise<T> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query('SET LOCAL ROLE role_web_serve')
    await client.query('SELECT set_config($1,$2,true), set_config($3,$4,true)', [
      'app.principal_id', principal, 'app.chart_context', chartId ?? '',
    ])
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

function createJob(
  pool: Pool,
  jobId: string,
  principal = principalA,
  key = keyA,
  authKind: 'api_key' | 'oauth' = 'api_key',
  chart = chartA,
) {
  return inPrincipal(pool, principal, (client) => client.query(
    `SELECT * FROM create_planner_managed_prashna_job($1,$2,$3,$4,$5,$6::jsonb)`,
    [jobId, principal, key, authKind, chart,
      JSON.stringify({ question: 'durable job proof', response_format: 'standard' })],
  ), chart)
}

function claimJob(pool: Pool, jobId: string, worker: string, principal = principalA, key = keyA) {
  return inPrincipal(pool, principal, (client) => client.query<{
    status: string; lease_owner: string | null; attempt_count: number; error_text: string | null
  }>(
    `SELECT status, lease_owner, attempt_count, error_text
       FROM claim_planner_managed_prashna_job($1,$2,$3,$4,30)`,
    [jobId, principal, key, worker],
  ))
}

function documentedDownSql(sql: string): string {
  const section = sql.split('-- DOWN (manual, destructive; retain/export terminal job evidence before use):')[1]
  const statements = section?.split('\n').flatMap((line) => {
    const match = line.match(/^-- ((?:DROP|ALTER) .+;)$/)
    return match ? [match[1]] : []
  }) ?? []
  if (statements.length !== 9) throw new Error('migration 1038 documented DOWN block is incomplete')
  return statements.join('\n')
}

describeDisposable('migration 1038 durable managed jobs acceptance', () => {
  let adminPool: Pool
  let instanceA: Pool
  let instanceB: Pool
  let downApplied = false

  beforeAll(async () => {
    assertDisposableUrl(databaseUrl!)
    adminPool = new Pool({ connectionString: databaseUrl, max: 6 })
    await adminPool.query(`
      DO $$ BEGIN CREATE ROLE role_web_serve NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
      DO $$ BEGIN CREATE ROLE purna_w7_web LOGIN PASSWORD 'purna_w7_web_test_only'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
      ALTER ROLE purna_w7_web PASSWORD 'purna_w7_web_test_only';
      GRANT role_web_serve TO purna_w7_web;
      CREATE TABLE IF NOT EXISTS profiles (id text PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS charts (id uuid PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS mcp_api_keys (
        key_id text PRIMARY KEY,
        key_hash text NOT NULL,
        user_uid text NOT NULL,
        revoked_at timestamptz
      );
      CREATE TABLE IF NOT EXISTS mcp_oauth_tokens (
        access_token_hash text PRIMARY KEY,
        uid text NOT NULL,
        expires_at timestamptz NOT NULL
      );
      CREATE OR REPLACE FUNCTION app_chart_context() RETURNS uuid LANGUAGE sql STABLE AS $$
        SELECT NULLIF(current_setting('app.chart_context', true), '')::uuid
      $$;
      INSERT INTO profiles(id) VALUES ('${principalA}'),('${principalB}'),('${principalToDelete}') ON CONFLICT DO NOTHING;
      INSERT INTO charts(id) VALUES ('${chartA}'),('${chartToDelete}') ON CONFLICT DO NOTHING;
      INSERT INTO mcp_api_keys(key_id,key_hash,user_uid)
      VALUES ('${keyA}','test-only-hash-a','${principalA}'),
             ('${keyB}','test-only-hash-b','${principalB}'),
             ('${keyToRevoke}','test-only-revoked-hash','${principalA}'),
             ('${keyForDeletedPrincipal}','test-only-profile-delete-hash','${principalToDelete}')
      ON CONFLICT (key_id) DO UPDATE SET key_hash=excluded.key_hash,user_uid=excluded.user_uid;
      INSERT INTO mcp_oauth_tokens(access_token_hash,uid,expires_at)
      VALUES ('${oauthHash}','${principalB}',now() + interval '1 hour')
      ON CONFLICT (access_token_hash) DO UPDATE SET uid=excluded.uid,expires_at=excluded.expires_at;
    `)
    const serveUrl = new URL(databaseUrl!)
    serveUrl.username = 'purna_w7_web'
    serveUrl.password = 'purna_w7_web_test_only'
    instanceA = new Pool({ connectionString: serveUrl.toString(), max: 2 })
    instanceB = new Pool({ connectionString: serveUrl.toString(), max: 2 })
  })

  afterAll(async () => {
    if (instanceA) await instanceA.end()
    if (instanceB) await instanceB.end()
    if (adminPool) {
      if (!downApplied) await adminPool.query(documentedDownSql(migrationSql)).catch(() => undefined)
      await adminPool.end()
    }
  })

  it('applies and replays with RLS, no direct table access, and only bounded function grants', async () => {
    await adminPool.query(migrationSql)
    await adminPool.query(migrationSql)
    const table = await adminPool.query(`
      SELECT relrowsecurity FROM pg_class WHERE relname='planner_managed_prashna_jobs'
    `)
    expect(table.rows).toEqual([{ relrowsecurity: true }])
    const tableGrants = await adminPool.query(`
      SELECT privilege_type FROM information_schema.role_table_grants
       WHERE grantee='role_web_serve' AND table_name='planner_managed_prashna_jobs'
    `)
    expect(tableGrants.rows).toEqual([])
    const functionGrants = await adminPool.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM information_schema.role_routine_grants
       WHERE grantee='role_web_serve' AND routine_name LIKE '%planner_managed_prashna_job%'
    `)
    expect(Number(functionGrants.rows[0].count)).toBeGreaterThanOrEqual(6)
    await expect(inPrincipal(instanceA, principalA, (client) =>
      client.query('SELECT * FROM planner_managed_prashna_jobs'), chartA,
    )).rejects.toMatchObject({ code: '42501' })
  })

  it('binds create and lookup to principal UID, API-key id, and chart context', async () => {
    await createJob(instanceA, jobA)
    const idempotent = await createJob(instanceB, jobA)
    expect(idempotent.rows).toHaveLength(1)
    expect(await adminPool.query(
      'SELECT count(*)::int AS count FROM planner_managed_prashna_jobs WHERE job_id=$1', [jobA],
    )).toMatchObject({ rows: [{ count: 1 }] })
    await expect(inPrincipal(instanceB, principalA, (client) => client.query(
      'SELECT * FROM create_planner_managed_prashna_job($1,$2,$3,$4,$5,$6::jsonb)',
      [jobA, principalA, keyA, 'api_key', chartA, JSON.stringify({ question: 'conflicting retry' })],
    ), chartA)).rejects.toMatchObject({ code: '23505' })
    const own = await inPrincipal(instanceB, principalA, (client) => client.query(
      'SELECT job_id, chart_id, request_jsonb FROM get_planner_managed_prashna_job($1,$2,$3)',
      [jobA, principalA, keyA],
    ))
    expect(own.rows).toMatchObject([{ job_id: jobA, chart_id: chartA, request_jsonb: { question: 'durable job proof' } }])
    const wrongKey = await inPrincipal(instanceB, principalA, (client) => client.query(
      'SELECT job_id FROM get_planner_managed_prashna_job($1,$2,$3)', [jobA, principalA, 'key-b'],
    ))
    expect(wrongKey.rowCount).toBe(0)
    const wrongPrincipal = await inPrincipal(instanceB, principalB, (client) => client.query(
      'SELECT job_id FROM get_planner_managed_prashna_job($1,$2,$3)', [jobA, principalB, keyA],
    ))
    expect(wrongPrincipal.rowCount).toBe(0)
    await expect(inPrincipal(instanceA, principalB, (client) => client.query(
      'SELECT * FROM create_planner_managed_prashna_job($1,$2,$3,$4,$5,$6::jsonb)',
      [jobB, principalA, keyA, 'api_key', chartA, '{}'],
    ), chartA)).rejects.toMatchObject({ code: '42501' })
    await expect(inPrincipal(instanceA, principalA, (client) => client.query(
      'SELECT * FROM create_planner_managed_prashna_job($1,$2,$3,$4,$5,$6::jsonb)',
      ['00000000-0000-4000-8000-000000000713', principalA, keyB, 'api_key', chartA, '{}'],
    ), chartA)).rejects.toMatchObject({ code: '42501' })
  })

  it('binds OAuth jobs to the full active token hash and cascades token revocation', async () => {
    const oauthJob = '00000000-0000-4000-8000-000000000714'
    const created = await createJob(instanceA, oauthJob, principalB, oauthKey, 'oauth')
    expect(created.rows[0]).toMatchObject({
      principal_uid: principalB,
      principal_key_id: oauthKey,
      principal_auth_kind: 'oauth',
      api_key_id: null,
      oauth_token_hash: oauthHash,
    })
    await adminPool.query(
      `UPDATE mcp_oauth_tokens SET expires_at=now() - interval '1 second' WHERE access_token_hash=$1`,
      [oauthHash],
    )
    const expired = await inPrincipal(instanceA, principalB, (client) => client.query(
      'SELECT job_id FROM get_planner_managed_prashna_job($1,$2,$3)',
      [oauthJob, principalB, oauthKey],
    ))
    expect(expired.rowCount).toBe(0)
    await expect(createJob(instanceA, oauthJob, principalB, oauthKey, 'oauth'))
      .rejects.toMatchObject({ code: '42501' })
    await adminPool.query('DELETE FROM mcp_oauth_tokens WHERE access_token_hash=$1', [oauthHash])
    expect(await adminPool.query(
      'SELECT count(*)::int AS count FROM planner_managed_prashna_jobs WHERE job_id=$1', [oauthJob],
    )).toMatchObject({ rows: [{ count: 0 }] })
  })

  it('makes API-key jobs inaccessible immediately after soft revocation and cascades hard deletion', async () => {
    const revokedJob = '00000000-0000-4000-8000-000000000715'
    await createJob(instanceA, revokedJob, principalA, keyToRevoke, 'api_key')
    await adminPool.query('UPDATE mcp_api_keys SET revoked_at=now() WHERE key_id=$1', [keyToRevoke])
    const inaccessible = await inPrincipal(instanceA, principalA, (client) => client.query(
      'SELECT job_id FROM get_planner_managed_prashna_job($1,$2,$3)',
      [revokedJob, principalA, keyToRevoke],
    ))
    expect(inaccessible.rowCount).toBe(0)
    await expect(createJob(instanceA, revokedJob, principalA, keyToRevoke, 'api_key'))
      .rejects.toMatchObject({ code: '42501' })
    await expect(createJob(
      instanceA,
      '00000000-0000-4000-8000-000000000716',
      principalA,
      keyToRevoke,
      'api_key',
    )).rejects.toMatchObject({ code: '42501' })
    await adminPool.query('DELETE FROM mcp_api_keys WHERE key_id=$1', [keyToRevoke])
    expect(await adminPool.query(
      'SELECT count(*)::int AS count FROM planner_managed_prashna_jobs WHERE job_id=$1', [revokedJob],
    )).toMatchObject({ rows: [{ count: 0 }] })
  })

  it('allows exactly one cross-instance lease winner and recovers only after expiry', async () => {
    const [a, b] = await Promise.all([
      claimJob(instanceA, jobA, 'worker-a'),
      claimJob(instanceB, jobA, 'worker-b'),
    ])
    const acquired = [a.rows[0], b.rows[0]].filter((row) => row.lease_owner === 'worker-a' || row.lease_owner === 'worker-b')
    expect(new Set(acquired.map((row) => row.lease_owner)).size).toBe(1)
    const winner = acquired[0].lease_owner!
    const loser = winner === 'worker-a' ? 'worker-b' : 'worker-a'
    expect([a.rows[0], b.rows[0]].find((row) => row.lease_owner === winner)?.attempt_count).toBe(1)

    await adminPool.query(
      `UPDATE planner_managed_prashna_jobs SET lease_expires_at=now() - interval '1 second' WHERE job_id=$1`,
      [jobA],
    )
    const recovered = await claimJob(instanceB, jobA, loser)
    expect(recovered.rows[0]).toMatchObject({ status: 'running', lease_owner: loser, attempt_count: 2 })
  })

  it('rejects a stale worker and durably returns the full terminal result across instances', async () => {
    const current = await adminPool.query<{ lease_owner: string }>(
      'SELECT lease_owner FROM planner_managed_prashna_jobs WHERE job_id=$1', [jobA],
    )
    const worker = current.rows[0].lease_owner
    const stale = await inPrincipal(instanceA, principalA, (client) => client.query(
      `SELECT * FROM complete_planner_managed_prashna_job($1,$2,$3,$4,$5::jsonb)`,
      [jobA, principalA, keyA, 'stale-worker', '{"ok":true}'],
    ))
    expect(stale.rowCount).toBe(0)
    const completed = await inPrincipal(instanceB, principalA, (client) => client.query(
      `SELECT status, result_jsonb, lease_owner FROM complete_planner_managed_prashna_job($1,$2,$3,$4,$5::jsonb)`,
      [jobA, principalA, keyA, worker, JSON.stringify({ ok: true, outcome: 'plan', completeness: { status: 'complete' } })],
    ))
    expect(completed.rows).toEqual([{
      status: 'complete', result_jsonb: { ok: true, outcome: 'plan', completeness: { status: 'complete' } }, lease_owner: null,
    }])
    const replayed = await inPrincipal(instanceA, principalA, (client) => client.query(
      `SELECT status, result_jsonb FROM complete_planner_managed_prashna_job($1,$2,$3,$4,$5::jsonb)`,
      [jobA, principalA, keyA, worker, JSON.stringify({ ok: true, outcome: 'plan', completeness: { status: 'complete' } })],
    ))
    expect(replayed.rows).toEqual([{
      status: 'complete', result_jsonb: { ok: true, outcome: 'plan', completeness: { status: 'complete' } },
    }])
    const conflictingReplay = await inPrincipal(instanceA, principalA, (client) => client.query(
      `SELECT * FROM complete_planner_managed_prashna_job($1,$2,$3,$4,$5::jsonb)`,
      [jobA, principalA, keyA, worker, JSON.stringify({ ok: true, outcome: 'different' })],
    ))
    expect(conflictingReplay.rowCount).toBe(0)
    const fetched = await inPrincipal(instanceA, principalA, (client) => client.query(
      `SELECT status, result_jsonb FROM get_planner_managed_prashna_job($1,$2,$3)`,
      [jobA, principalA, keyA],
    ))
    expect(fetched.rows).toEqual([{
      status: 'complete', result_jsonb: { ok: true, outcome: 'plan', completeness: { status: 'complete' } },
    }])
  })

  it('fails closed after three expired attempts instead of retrying forever', async () => {
    await createJob(instanceA, jobB)
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      const claimed = await claimJob(instanceA, jobB, `worker-${attempt}`)
      expect(claimed.rows[0]).toMatchObject({ status: 'running', attempt_count: attempt })
      await adminPool.query(
        `UPDATE planner_managed_prashna_jobs SET lease_expires_at=now() - interval '1 second' WHERE job_id=$1`,
        [jobB],
      )
    }
    const exhausted = await claimJob(instanceB, jobB, 'worker-4')
    expect(exhausted.rows[0]).toMatchObject({
      status: 'failed', lease_owner: null, attempt_count: 3, error_text: 'MANAGED_JOB_RETRY_EXHAUSTED',
    })
  })

  it('reconciles an identical failed terminal write but rejects a conflicting replay', async () => {
    const failedJob = '00000000-0000-4000-8000-000000000719'
    const worker = 'failure-worker'
    await createJob(instanceA, failedJob)
    await claimJob(instanceA, failedJob, worker)
    const fail = () => inPrincipal(instanceA, principalA, (client) => client.query(
      `SELECT status, error_text FROM fail_planner_managed_prashna_job($1,$2,$3,$4,$5)`,
      [failedJob, principalA, keyA, worker, 'engine rejected request'],
    ))
    expect((await fail()).rows).toEqual([{ status: 'failed', error_text: 'engine rejected request' }])
    expect((await fail()).rows).toEqual([{ status: 'failed', error_text: 'engine rejected request' }])
    const conflicting = await inPrincipal(instanceA, principalA, (client) => client.query(
      `SELECT * FROM fail_planner_managed_prashna_job($1,$2,$3,$4,$5)`,
      [failedJob, principalA, keyA, worker, 'different error'],
    ))
    expect(conflicting.rowCount).toBe(0)
  })


  it('does not obstruct governed chart or profile deletion and purges their jobs', async () => {
    const chartJob = '00000000-0000-4000-8000-000000000717'
    const profileJob = '00000000-0000-4000-8000-000000000718'
    await createJob(instanceA, chartJob, principalA, keyA, 'api_key', chartToDelete)
    await createJob(instanceA, profileJob, principalToDelete, keyForDeletedPrincipal, 'api_key')
    await adminPool.query('DELETE FROM charts WHERE id=$1', [chartToDelete])
    await adminPool.query('DELETE FROM profiles WHERE id=$1', [principalToDelete])
    expect(await adminPool.query(
      'SELECT count(*)::int AS count FROM planner_managed_prashna_jobs WHERE job_id=ANY($1::uuid[])',
      [[chartJob, profileJob]],
    )).toMatchObject({ rows: [{ count: 0 }] })
  })

  it('applies the documented destructive down only in the disposable database', async () => {
    await adminPool.query(documentedDownSql(migrationSql))
    downApplied = true
    const objects = await adminPool.query(`
      SELECT to_regclass('public.planner_managed_prashna_jobs') AS table_name,
             to_regprocedure('public.create_planner_managed_prashna_job(uuid,text,text,text,uuid,jsonb)') AS create_function
    `)
    expect(objects.rows).toEqual([{ table_name: null, create_function: null }])
  })
})
