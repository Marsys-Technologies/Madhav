/** Atomically applies and records the two protected DP-SD-018 migrations. */
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool } from 'pg'
import { sqlIdentityOf } from './migrate'
import { readDataPlaneOwnershipStatus } from './data-plane-ownership-status'

export const PROTECTED_DATA_PLANE_MIGRATIONS = [
  ['1035_data_plane_l1_producer_history.sql', 'data_plane_l1_owner'],
  ['1036_data_plane_l2_producer_generations.sql', 'data_plane_l2_owner'],
] as const

export function stripTransactionWrapper(sql: string): string {
  const begin = sql.search(/(^|\n)BEGIN;\s*\n/i)
  const commit = sql.lastIndexOf('\nCOMMIT;')
  if (begin < 0 || commit <= begin) throw new Error('Protected migration is missing its exact BEGIN/COMMIT wrapper.')
  const beginEnd = sql.indexOf('\n', begin + 1) + 1
  return `${sql.slice(0, begin)}\n${sql.slice(beginEnd, commit)}${sql.slice(commit + '\nCOMMIT;'.length)}`
}

export async function attestDataPlaneMigrations(databaseUrl = process.env.DATA_PLANE_MIGRATOR_DATABASE_URL): Promise<void> {
  if (!databaseUrl) throw new Error('DATA_PLANE_MIGRATOR_DATABASE_URL is required for protected migration attestation.')
  const migrations = PROTECTED_DATA_PLANE_MIGRATIONS.map(([filename, owner]) => {
    const sql = readFileSync(resolve(__dirname, '../supabase/migrations', filename), 'utf8')
    return { filename, owner, sql, sha256: createHash('sha256').update(sql).digest('hex'), identity: sqlIdentityOf(sql) }
  })
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string }>('SELECT session_user, current_user')
    if (actor.rows[0]?.session_user !== 'data_plane_migrator' || actor.rows[0]?.current_user !== 'data_plane_migrator') {
      throw new Error('Protected migrations require direct data_plane_migrator authentication.')
    }
    const rows = await client.query<{ filename: string; sha256: string | null; sql_identity: string | null; copies: string }>(
      `SELECT filename, min(sha256) AS sha256, min(sql_identity) AS sql_identity,
              count(*)::text AS copies
       FROM public._migrations_applied WHERE filename=ANY($1::text[])
       GROUP BY filename`,
      [migrations.map((m) => m.filename)],
    )
    if (rows.rowCount !== 0 && rows.rowCount !== migrations.length) throw new Error('Partial protected migration marker state; manual DBA recovery required.')
    if (rows.rowCount === migrations.length) {
      for (const migration of migrations) {
        const row = rows.rows.find((candidate) => candidate.filename === migration.filename)
        if (!row || row.copies !== '1' || !row.sha256 || !row.sql_identity
            || row.sha256 !== migration.sha256 || row.sql_identity !== migration.identity) {
          throw new Error(`${migration.filename} has a missing, duplicate, or mismatched protected identity.`)
        }
      }
      await readDataPlaneOwnershipStatus(databaseUrl)
      return
    }
    await client.query('BEGIN')
    try {
      for (const migration of migrations) {
        await client.query(`SET LOCAL ROLE ${migration.owner}`)
        await client.query(stripTransactionWrapper(migration.sql))
        await client.query('RESET ROLE')
        await client.query(
          'INSERT INTO public._migrations_applied(filename,sha256,sql_identity) VALUES($1,$2,$3)',
          [migration.filename, migration.sha256, migration.identity],
        )
      }
      await client.query('COMMIT')
    } catch (error) { await client.query('ROLLBACK'); throw error }
    await readDataPlaneOwnershipStatus(databaseUrl)
  } finally { client.release(); await pool.end() }
}

if (require.main === module) attestDataPlaneMigrations().catch((error) => { console.error(error); process.exitCode = 1 })
