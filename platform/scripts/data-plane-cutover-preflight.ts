/** Fail-closed release evidence gate for the one-shot DP-SD-018 cutover. */
import { execFileSync } from 'node:child_process'
import { Pool } from 'pg'
import { readDataPlaneOwnershipStatus } from './data-plane-ownership-status'

function requireValue(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required by the protected data-plane cutover environment.`)
  return value
}

export interface BackupRestoreReceipt {
  backupId: string
  restoreOperationId: string
  validationInstance: string
  sourceCommit: string
  leaseId: string
  approvedBy: string
  expiresAt: string
}

export function parseBackupRestoreReceipt(value: string): BackupRestoreReceipt {
  let parsed: unknown
  try { parsed = JSON.parse(value) }
  catch { throw new Error('DATA_PLANE_BACKUP_RESTORE_ID must be an exact JSON receipt.') }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Backup/restore receipt must be an object.')
  const receipt = parsed as Record<string, unknown>
  const expectedKeys = ['approvedBy','backupId','expiresAt','leaseId','restoreOperationId','sourceCommit','validationInstance']
  if (Object.keys(receipt).sort().join(',') !== expectedKeys.join(',')
      || expectedKeys.some((key) => typeof receipt[key] !== 'string' || !(receipt[key] as string).trim())) {
    throw new Error('Backup/restore receipt fields are missing, empty, or unexpected.')
  }
  return receipt as unknown as BackupRestoreReceipt
}

export function assertBackupReceiptBinding(
  receipt: BackupRestoreReceipt,
  binding: { validationInstance: string; sourceCommit: string; leaseId: string; approvedBy: string },
  now = new Date(),
): void {
  if (!/^[A-Za-z0-9_-]+$/.test(receipt.backupId) || !/^[A-Za-z0-9_-]+$/.test(receipt.restoreOperationId)
      || !/^[a-z][a-z0-9-]{4,97}[a-z0-9]$/.test(receipt.validationInstance)
      || !/^[0-9a-f]{40}$/.test(receipt.sourceCommit) || !/^[0-9a-f-]{36}$/i.test(receipt.leaseId)
      || receipt.validationInstance === 'amjis-postgres'
      || receipt.validationInstance !== binding.validationInstance || receipt.sourceCommit !== binding.sourceCommit
      || receipt.leaseId !== binding.leaseId || receipt.approvedBy !== binding.approvedBy) {
    throw new Error('Backup/restore receipt is not bound to this commit, lease, approver, and isolated instance.')
  }
  const expiry = Date.parse(receipt.expiresAt)
  if (!Number.isFinite(expiry) || expiry <= now.getTime() || expiry > now.getTime() + 48 * 60 * 60 * 1000) {
    throw new Error('Backup/restore receipt is expired or has an unsafe expiry horizon.')
  }
}

export async function withDataPlaneCutoverLease<T>(action: () => Promise<T>): Promise<T> {
  const databaseUrl = requireValue('PROD_DATABASE_URL')
  const receipt = parseBackupRestoreReceipt(requireValue('DATA_PLANE_BACKUP_RESTORE_ID'))
  const lease = requireValue('DATA_PLANE_CUTOVER_LEASE')
  const approver = requireValue('DATA_PLANE_INDEPENDENT_APPROVER')
  const actor = requireValue('GITHUB_ACTOR')
  const validationInstance = requireValue('DATA_PLANE_RESTORE_VALIDATION_INSTANCE')
  const validationDatabaseUrl = requireValue('DATA_PLANE_RESTORE_VALIDATION_DATABASE_URL')
  const sourceCommit = requireValue('DEPLOY_SHA')
  if (approver === actor) throw new Error('DP-SD-018 independent approver must differ from the deploying actor.')
  if (!/^[0-9a-f-]{36}$/i.test(lease)) throw new Error('DATA_PLANE_CUTOVER_LEASE must be an exact UUID lease receipt.')
  assertBackupReceiptBinding(receipt, { validationInstance,sourceCommit,leaseId: lease,approvedBy: approver })
  const backup = JSON.parse(execFileSync('gcloud', [
    'sql', 'backups', 'describe', receipt.backupId, '--instance', 'amjis-postgres',
    '--project', process.env.GCP_PROJECT ?? 'madhav-astrology', '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as { status?: string; id?: string | number; endTime?: string }
  const backupCompleted = Date.parse(backup.endTime ?? '')
  if (backup.status !== 'SUCCESSFUL' || String(backup.id) !== receipt.backupId
      || !Number.isFinite(backupCompleted) || backupCompleted > Date.now()
      || Date.now() - backupCompleted > 24 * 60 * 60 * 1000) {
    throw new Error('Named Cloud SQL backup evidence is absent, unsuccessful, or stale.')
  }
  const restore = JSON.parse(execFileSync('gcloud', [
    'sql', 'operations', 'describe', receipt.restoreOperationId,
    '--project', process.env.GCP_PROJECT ?? 'madhav-astrology', '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as {
    name?: string; status?: string; operationType?: string; targetId?: string; endTime?: string
    backupContext?: { backupId?: string | number }
  }
  const restoreCompleted = Date.parse(restore.endTime ?? '')
  if (restore.name !== receipt.restoreOperationId || restore.status !== 'DONE'
      || restore.targetId !== validationInstance || restore.targetId === 'amjis-postgres'
      || !/^RESTORE(?:_|$)/.test(restore.operationType ?? '')
      || String(restore.backupContext?.backupId ?? '') !== receipt.backupId
      || !Number.isFinite(restoreCompleted) || restoreCompleted < backupCompleted
      || restoreCompleted > Date.parse(receipt.expiresAt)) {
    throw new Error('Named restore does not prove the pinned backup on the isolated validation instance.')
  }
  if (await readDataPlaneOwnershipStatus(validationDatabaseUrl) !== 'unmarked') {
    throw new Error('Isolated restore does not attest the expected pre-cutover protected state.')
  }
  const validationPool = new Pool({ connectionString: validationDatabaseUrl, max: 1 })
  try {
    const validation = await validationPool.query<{ version: number; build_runs: string | null }>(`
      SELECT current_setting('server_version_num')::int version,
             to_regclass('public.build_runs')::text build_runs
    `)
    if ((validation.rows[0]?.version ?? 0) < 150000 || (validation.rows[0]?.version ?? 0) >= 160000
        || validation.rows[0]?.build_runs !== 'build_runs') {
      throw new Error('Isolated restore validation database has the wrong engine or schema identity.')
    }
  } finally {
    await validationPool.end()
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
