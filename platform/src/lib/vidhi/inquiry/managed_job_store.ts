import type { PoolClient } from 'pg'
import { getServeReadPool, withChartContext } from '@/lib/db/roles'

export type ManagedPrashnaJobStatus = 'pending' | 'running' | 'complete' | 'failed'
export type ManagedPrashnaResponseFormat = 'digest' | 'summary' | 'standard' | 'narrative' | 'full'

export interface ManagedPrashnaJobRequest {
  readonly question: string
  readonly response_format: ManagedPrashnaResponseFormat
  readonly scope_tuple?: unknown
}

export interface ManagedPrashnaJobProgress {
  readonly message: string
  readonly pct: number
}

export interface ManagedPrashnaJobRow<TResult = unknown> {
  readonly job_id: string
  readonly principal_uid: string
  readonly principal_key_id: string
  readonly principal_auth_kind: 'api_key' | 'oauth'
  readonly api_key_id: string | null
  readonly oauth_token_hash: string | null
  readonly chart_id: string
  readonly request_jsonb: ManagedPrashnaJobRequest
  readonly status: ManagedPrashnaJobStatus
  readonly progress_jsonb: ManagedPrashnaJobProgress | null
  readonly result_jsonb: TResult | null
  readonly error_text: string | null
  readonly lease_owner: string | null
  readonly lease_expires_at: string | null
  readonly terminal_worker_id: string | null
  readonly attempt_count: number
  readonly created_at: string
  readonly updated_at: string
  readonly retention_expires_at: string
}

async function withPrincipalContext<T>(
  principalUid: string,
  action: (client: PoolClient) => Promise<T>,
): Promise<T> {
  const pool = await getServeReadPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query('SELECT set_config($1, $2, true)', ['app.principal_id', principalUid])
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

export async function createManagedPrashnaJob(args: {
  job_id: string
  principal_uid: string
  principal_key_id: string
  principal_auth_kind: 'api_key' | 'oauth'
  chart_id: string
  request: ManagedPrashnaJobRequest
}): Promise<ManagedPrashnaJobRow> {
  return withChartContext(args.chart_id, async (client) => {
    await client.query('SELECT set_config($1, $2, true), set_config($3, $4, true)', [
      'app.principal_id', args.principal_uid, 'app.chart_context', args.chart_id,
    ])
    const result = await client.query<ManagedPrashnaJobRow>(
      `SELECT * FROM create_planner_managed_prashna_job($1,$2,$3,$4,$5,$6::jsonb)`,
      [args.job_id, args.principal_uid, args.principal_key_id, args.principal_auth_kind,
        args.chart_id, JSON.stringify(args.request)],
    )
    if (!result.rows[0]) throw new Error('MANAGED_JOB_CREATION_FAILED')
    return result.rows[0]
  }, { principalId: args.principal_uid })
}

export async function getManagedPrashnaJob(args: {
  job_id: string
  principal_uid: string
  principal_key_id: string
}): Promise<ManagedPrashnaJobRow | null> {
  return withPrincipalContext(args.principal_uid, async (client) => {
    const result = await client.query<ManagedPrashnaJobRow>(
      'SELECT * FROM get_planner_managed_prashna_job($1,$2,$3)',
      [args.job_id, args.principal_uid, args.principal_key_id],
    )
    return result.rows[0] ?? null
  })
}

export async function claimManagedPrashnaJob(args: {
  job_id: string
  principal_uid: string
  principal_key_id: string
  lease_owner: string
  lease_seconds?: number
}): Promise<ManagedPrashnaJobRow | null> {
  return withPrincipalContext(args.principal_uid, async (client) => {
    const result = await client.query<ManagedPrashnaJobRow>(
      'SELECT * FROM claim_planner_managed_prashna_job($1,$2,$3,$4,$5)',
      [args.job_id, args.principal_uid, args.principal_key_id, args.lease_owner, args.lease_seconds ?? 450],
    )
    return result.rows[0] ?? null
  })
}

export async function updateManagedPrashnaJobProgress(args: {
  job_id: string
  principal_uid: string
  principal_key_id: string
  lease_owner: string
  progress: ManagedPrashnaJobProgress
  lease_seconds?: number
}): Promise<ManagedPrashnaJobRow> {
  return withPrincipalContext(args.principal_uid, async (client) => {
    const result = await client.query<ManagedPrashnaJobRow>(
      'SELECT * FROM update_planner_managed_prashna_job_progress($1,$2,$3,$4,$5::jsonb,$6)',
      [args.job_id, args.principal_uid, args.principal_key_id, args.lease_owner,
        JSON.stringify(args.progress), args.lease_seconds ?? 450],
    )
    if (!result.rows[0]) throw new Error('MANAGED_JOB_LEASE_LOST')
    return result.rows[0]
  })
}

export async function completeManagedPrashnaJob<TResult>(args: {
  job_id: string
  principal_uid: string
  principal_key_id: string
  lease_owner: string
  result: TResult
}): Promise<ManagedPrashnaJobRow<TResult>> {
  return withPrincipalContext(args.principal_uid, async (client) => {
    const result = await client.query<ManagedPrashnaJobRow<TResult>>(
      'SELECT * FROM complete_planner_managed_prashna_job($1,$2,$3,$4,$5::jsonb)',
      [args.job_id, args.principal_uid, args.principal_key_id, args.lease_owner, JSON.stringify(args.result)],
    )
    if (!result.rows[0]) throw new Error('MANAGED_JOB_LEASE_LOST')
    return result.rows[0]
  })
}

export async function failManagedPrashnaJob(args: {
  job_id: string
  principal_uid: string
  principal_key_id: string
  lease_owner: string
  error: string
}): Promise<ManagedPrashnaJobRow> {
  return withPrincipalContext(args.principal_uid, async (client) => {
    const result = await client.query<ManagedPrashnaJobRow>(
      'SELECT * FROM fail_planner_managed_prashna_job($1,$2,$3,$4,$5)',
      [args.job_id, args.principal_uid, args.principal_key_id, args.lease_owner, args.error],
    )
    if (!result.rows[0]) throw new Error('MANAGED_JOB_LEASE_LOST')
    return result.rows[0]
  })
}
