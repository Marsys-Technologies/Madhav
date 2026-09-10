/** Read-only deployment gate for the one-shot Nirmana ownership handoff. */
import { Pool } from 'pg'

const MARKER = '633_nirmana_evidence_writer_ownership.sql'
const DATABASE_URL = 'DATABASE_URL'

export type NirmanaEvidenceOwnershipStatus = 'marked' | 'unmarked'

/** A first handoff needs the direct legacy owner; a durable marker does not. */
export function requiresNirmanaEvidenceLegacyOwner(status: NirmanaEvidenceOwnershipStatus): boolean {
  return status === 'unmarked'
}

/**
 * Uses the ordinary migration principal only to read the migration ledger.
 * A connection or SELECT failure is intentionally propagated: callers must
 * never reinterpret an unavailable ledger as an unmarked first deployment.
 */
export async function readNirmanaEvidenceOwnershipStatus(databaseUrl = process.env[DATABASE_URL]): Promise<NirmanaEvidenceOwnershipStatus> {
  if (!databaseUrl) throw new Error(`${DATABASE_URL} is required to read the Nirmana ownership handoff marker.`)
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  try {
    const result = await pool.query<{ marked: boolean }>(
      'SELECT EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename = $1) AS marked',
      [MARKER],
    )
    return result.rows[0]?.marked === true ? 'marked' : 'unmarked'
  } finally { await pool.end() }
}

if (require.main === module) {
  readNirmanaEvidenceOwnershipStatus().then((status) => {
    process.stdout.write(`${status}\n`)
  }).catch((error) => {
    console.error(error)
    process.exitCode = 1
  })
}
