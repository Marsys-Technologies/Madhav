/** Fail-closed release evidence gate for the one-shot DP-SD-018 cutover. */
import { execFileSync } from 'node:child_process'
import { Pool } from 'pg'

function requireValue(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required by the protected data-plane cutover environment.`)
  return value
}

export async function assertDataPlaneCutoverPreflight(): Promise<void> {
  const databaseUrl = requireValue('PROD_DATABASE_URL')
  const backupId = requireValue('DATA_PLANE_BACKUP_RESTORE_ID')
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
    throw new Error('Named Cloud SQL backup/restore evidence is absent or unsuccessful.')
  }
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    await client.query('BEGIN READ ONLY')
    const lock = await client.query<{ locked: boolean }>(
      `SELECT pg_try_advisory_xact_lock(hashtextextended('DP-SD-018-PROTECTED-CUTOVER',0)) AS locked`,
    )
    if (!lock.rows[0]?.locked) throw new Error('Exclusive DP-SD-018 cutover lease is already held.')
    const active = await client.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM public.build_runs
      WHERE state IN ('running','queued','dispatching')
    `)
    if (active.rows[0]?.count !== '0') throw new Error('Data-plane cutover requires build-run quiescence.')
    await client.query('ROLLBACK')
  } finally { client.release(); await pool.end() }
}

if (require.main === module) assertDataPlaneCutoverPreflight().catch((error) => {
  console.error(error); process.exitCode = 1
})
