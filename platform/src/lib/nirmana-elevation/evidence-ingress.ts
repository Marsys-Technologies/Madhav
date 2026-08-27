import 'server-only'
import { Pool } from 'pg'

const INGRESS_DATABASE_URL = 'NIRMANA_EVIDENCE_INGRESS_DATABASE_URL'
const INGRESS_DB_ROLE = 'nirmana_evidence_ingress_writer'

export class NirmanaEvidenceIngressNotConfiguredError extends Error {
  constructor(message = `Server-reconstructed evidence requires the distinct secret-backed ${INGRESS_DATABASE_URL} credential.`) {
    super(message)
    this.name = 'NirmanaEvidenceIngressNotConfiguredError'
  }
}
function databaseUser(databaseUrl: string): string {
  try {
    return decodeURIComponent(new URL(databaseUrl).username)
  } catch {
    throw new NirmanaEvidenceIngressNotConfiguredError(`${INGRESS_DATABASE_URL} must be a valid PostgreSQL connection URL.`)
  }
}

/**
 * Refuse generic application credentials even when a caller gives them under a
 * different variable. The migration grants the ingress role only the evidence
 * reads and INSERT privilege it needs; credential provisioning is deployment
 * controlled and deliberately not invented by this application code.
 */
export function assertNirmanaEvidenceIngressDatabaseUrl(
  databaseUrl: string | undefined = process.env[INGRESS_DATABASE_URL],
  genericDatabaseUrl: string | undefined = process.env.DATABASE_URL,
  genericDatabaseUser: string | undefined = process.env.DB_USER,
): string {
  if (!databaseUrl) throw new NirmanaEvidenceIngressNotConfiguredError()
  const ingressUser = databaseUser(databaseUrl)
  if (ingressUser !== INGRESS_DB_ROLE) {
    throw new NirmanaEvidenceIngressNotConfiguredError(`${INGRESS_DATABASE_URL} must authenticate as ${INGRESS_DB_ROLE}; generic application credentials are not accepted.`)
  }
  if (genericDatabaseUrl && databaseUser(genericDatabaseUrl) === ingressUser) {
    throw new NirmanaEvidenceIngressNotConfiguredError(`${INGRESS_DATABASE_URL} must not reuse the generic DATABASE_URL database principal.`)
  }
  if (genericDatabaseUser === ingressUser) {
    throw new NirmanaEvidenceIngressNotConfiguredError(`${INGRESS_DATABASE_URL} must not reuse DB_USER.`)
  }
  return databaseUrl
}

const globalPools = globalThis as typeof globalThis & { __nirmanaEvidenceIngressPool?: Pool }

/**
 * The only connection path allowed to append server-reconstructed receipts.
 * It never falls back to getPool/DATABASE_URL: lacking the separately
 * provisioned secret means the evidence action fails closed.
 */
export async function getNirmanaEvidenceIngressPool(): Promise<Pool> {
  const connectionString = assertNirmanaEvidenceIngressDatabaseUrl()
  if (!globalPools.__nirmanaEvidenceIngressPool) {
    globalPools.__nirmanaEvidenceIngressPool = new Pool({
      connectionString,
      max: 2,
      keepAlive: true,
      keepAliveInitialDelayMillis: 10_000,
      idleTimeoutMillis: 15_000,
      connectionTimeoutMillis: 5_000,
      options: '-c statement_timeout=25000',
    })
    globalPools.__nirmanaEvidenceIngressPool.on('error', (error) => {
      console.error('[nirmana evidence ingress pool] idle client error (evicted)', error)
    })
  }
  return globalPools.__nirmanaEvidenceIngressPool
}
