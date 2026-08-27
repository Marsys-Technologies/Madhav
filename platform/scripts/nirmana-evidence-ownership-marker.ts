/**
 * Applies only the post-preflight migration-633 attestation as the dedicated
 * migrator login.  The ordinary migration runner remains on its established
 * generic executor for every other repository migration.
 */
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool } from 'pg'

const MIGRATOR_URL = 'NIRMANA_MIGRATOR_DATABASE_URL'
const FILENAME = '633_nirmana_evidence_writer_ownership.sql'

export async function applyNirmanaEvidenceOwnershipMarker(databaseUrl = process.env[MIGRATOR_URL]): Promise<void> {
  if (!databaseUrl) throw new Error(`${MIGRATOR_URL} is required to attest the Nirmana ownership handoff.`)
  const sql = readFileSync(resolve(__dirname, '../migrations', FILENAME), 'utf8')
  const sha256 = createHash('sha256').update(sql).digest('hex')
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string }>('SELECT session_user, current_user')
    if (actor.rows[0]?.session_user !== 'nirmana_migrator' || actor.rows[0]?.current_user !== 'nirmana_migrator') {
      throw new Error('Nirmana ownership marker must authenticate directly as nirmana_migrator.')
    }
    const existing = await client.query<{ sha256: string }>('SELECT sha256 FROM public._migrations_applied WHERE filename = $1', [FILENAME])
    if (existing.rows[0]) {
      if (existing.rows[0].sha256 !== sha256) throw new Error('Migration 633 is already recorded with a different digest.')
      return
    }
    const prerequisite = await client.query('SELECT 1 FROM public._migrations_applied WHERE filename = $1', ['632_nirmana_evidence_server_writer_guard.sql'])
    if (prerequisite.rowCount !== 1) throw new Error('Migration 632 must be recorded before the Nirmana ownership marker.')
    await client.query('BEGIN')
    try {
      await client.query(sql)
      // sql_identity is deliberately left NULL here. The normal generic runner
      // owns tracker maintenance and will backfill it only after proving this
      // exact SHA matches the file it sees.
      await client.query('INSERT INTO public._migrations_applied (filename, sha256) VALUES ($1, $2)', [FILENAME, sha256])
      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    }
  } finally {
    client.release()
    await pool.end()
  }
}

if (require.main === module) {
  applyNirmanaEvidenceOwnershipMarker().catch((error) => {
    console.error(error)
    process.exitCode = 1
  })
}
