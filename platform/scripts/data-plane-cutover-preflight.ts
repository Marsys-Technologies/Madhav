/** Fail-closed release evidence gate for the one-shot DP-SD-018 cutover. */
import { execFileSync } from 'node:child_process'
import { Pool } from 'pg'

function requireValue(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required by the protected data-plane cutover environment.`)
  return value
}

export function parseBackupRestoreReceipt(value: string): { backupId: string; restoreOperationId: string } {
  const parts = value.split(':')
  if (parts.length !== 2 || parts.some((part) => !/^[A-Za-z0-9_-]+$/.test(part))) {
    throw new Error('DATA_PLANE_BACKUP_RESTORE_ID must pin exact backup-id:restore-operation-id evidence.')
  }
  return { backupId: parts[0], restoreOperationId: parts[1] }
}

export async function withDataPlaneCutoverLease<T>(action: () => Promise<T>): Promise<T> {
  const databaseUrl = requireValue('PROD_DATABASE_URL')
  const { backupId, restoreOperationId } = parseBackupRestoreReceipt(requireValue('DATA_PLANE_BACKUP_RESTORE_ID'))
  const lease = requireValue('DATA_PLANE_CUTOVER_LEASE')
  const approver = requireValue('DATA_PLANE_INDEPENDENT_APPROVER')
  const actor = requireValue('GITHUB_ACTOR')
  if (approver === actor) throw new Error('DP-SD-018 independent approver must differ from the deploying actor.')
  if (!/^[0-9a-f-]{36}$/i.test(lease)) throw new Error('DATA_PLANE_CUTOVER_LEASE must be an exact UUID lease receipt.')
  const backup = JSON.parse(execFileSync('gcloud', [
    'sql', 'backups', 'describe', backupId, '--instance', 'amjis-postgres',
    '--project', process.env.GCP_PROJECT ?? 'madhav-astrology', '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as { status?: string; id?: string | number }
  if (backup.status !== 'SUCCESSFUL' || String(backup.id) !== backupId) {
    throw new Error('Named Cloud SQL backup evidence is absent or unsuccessful.')
  }
  const restore = JSON.parse(execFileSync('gcloud', [
    'sql', 'operations', 'describe', restoreOperationId,
    '--project', process.env.GCP_PROJECT ?? 'madhav-astrology', '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as {
    name?: string; status?: string; operationType?: string; targetId?: string
    backupContext?: { backupId?: string | number }
  }
  if (restore.name !== restoreOperationId || restore.status !== 'DONE'
      || restore.targetId !== 'amjis-postgres'
      || !/^RESTORE(?:_|$)/.test(restore.operationType ?? '')
      || String(restore.backupContext?.backupId ?? '') !== backupId) {
    throw new Error('Named Cloud SQL restore operation does not prove the pinned backup was restored successfully.')
  }
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const lock = await client.query<{ locked: boolean }>(
      `SELECT pg_try_advisory_xact_lock(hashtextextended('DP-SD-018-PROTECTED-CUTOVER',0)) AS locked`,
    )
    if (!lock.rows[0]?.locked) throw new Error('Exclusive DP-SD-018 cutover lease is already held.')
    await client.query(`LOCK TABLE public.build_runs, public.build_run_assets
      IN SHARE ROW EXCLUSIVE MODE NOWAIT`)
    const active = await client.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM public.build_runs
      WHERE state IN ('running','queued','dispatching')
    `)
    if (active.rows[0]?.count !== '0') throw new Error('Data-plane cutover requires build-run quiescence.')
    return await action()
  } finally {
    await client.query('ROLLBACK').catch(() => undefined)
    client.release()
    await pool.end()
  }
}

export async function assertDataPlaneCutoverPreflight(): Promise<void> {
  await withDataPlaneCutoverLease(async () => undefined)
}

if (require.main === module) assertDataPlaneCutoverPreflight().catch((error) => {
  console.error(error); process.exitCode = 1
})
