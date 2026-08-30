import 'server-only'
import { Pool } from 'pg'

const DATABASE_URL_ENV = 'NIRMANA_EVIDENCE_VERIFIER_DATABASE_URL'
const ROLE = 'nirmana_evidence_verifier_writer'

export class NirmanaEvidenceVerifierWriterNotConfiguredError extends Error {
  constructor(message = 'Nirmana readiness verification requires its distinct secret-backed verifier database credential.') {
    super(message)
    this.name = 'NirmanaEvidenceVerifierWriterNotConfiguredError'
  }
}

function assertVerifierDatabaseUrl(databaseUrl = process.env[DATABASE_URL_ENV]): string {
  if (!databaseUrl) throw new NirmanaEvidenceVerifierWriterNotConfiguredError()
  let user: string
  try { user = decodeURIComponent(new URL(databaseUrl).username) } catch { throw new NirmanaEvidenceVerifierWriterNotConfiguredError() }
  if (user !== ROLE) throw new NirmanaEvidenceVerifierWriterNotConfiguredError(`${DATABASE_URL_ENV} must authenticate as ${ROLE}.`)
  return databaseUrl
}

const globalPools = globalThis as typeof globalThis & { __nirmanaEvidenceVerifierWriterPool?: Pool }

/** No fallback to the campaign-control or generic application database role. */
export async function getNirmanaEvidenceVerifierWriterPool(): Promise<Pool> {
  if (!globalPools.__nirmanaEvidenceVerifierWriterPool) {
    globalPools.__nirmanaEvidenceVerifierWriterPool = new Pool({
      connectionString: assertVerifierDatabaseUrl(), max: 1, idleTimeoutMillis: 15_000,
      connectionTimeoutMillis: 5_000, options: '-c statement_timeout=25000',
    })
  }
  return globalPools.__nirmanaEvidenceVerifierWriterPool
}
