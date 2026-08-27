import 'server-only'
import { Pool } from 'pg'

const INGRESS_DATABASE_URL = 'NIRMANA_EVIDENCE_INGRESS_DATABASE_URL'
const INGRESS_DB_USER = 'NIRMANA_EVIDENCE_INGRESS_DB_USER'
const INGRESS_DB_PASSWORD = 'NIRMANA_EVIDENCE_INGRESS_DB_PASSWORD'
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

export function assertNirmanaEvidenceIngressDatabaseUser(
  databaseUserName: string | undefined = process.env[INGRESS_DB_USER],
  password: string | undefined = process.env[INGRESS_DB_PASSWORD],
  genericDatabaseUser: string | undefined = process.env.DB_USER,
): { user: string; password: string } {
  if (databaseUserName !== INGRESS_DB_ROLE || !password) {
    throw new NirmanaEvidenceIngressNotConfiguredError(
      `Server-reconstructed evidence requires secret-backed ${INGRESS_DB_USER}=${INGRESS_DB_ROLE} and ${INGRESS_DB_PASSWORD}.`,
    )
  }
  if (genericDatabaseUser === databaseUserName) {
    throw new NirmanaEvidenceIngressNotConfiguredError(`${INGRESS_DB_USER} must not reuse DB_USER.`)
  }
  return { user: databaseUserName, password }
}

const globalPools = globalThis as typeof globalThis & { __nirmanaEvidenceIngressPool?: Pool }

/**
 * The only connection path allowed to append server-reconstructed receipts.
 * It never falls back to getPool/DATABASE_URL: lacking the separately
 * provisioned secret means the evidence action fails closed.
 */
export async function getNirmanaEvidenceIngressPool(): Promise<Pool> {
  if (!globalPools.__nirmanaEvidenceIngressPool) {
    const commonOptions = {
      max: 2,
      keepAlive: true,
      keepAliveInitialDelayMillis: 10_000,
      idleTimeoutMillis: 15_000,
      connectionTimeoutMillis: 5_000,
      options: '-c statement_timeout=25000',
    }
    if (process.env[INGRESS_DATABASE_URL]) {
      // Explicit local/test DSNs remain supported. Cloud Run's normal path is
      // below: a distinct credential through the Cloud SQL connector, never a
      // raw socket URL assumed to be reachable from the serving container.
      globalPools.__nirmanaEvidenceIngressPool = new Pool({
        connectionString: assertNirmanaEvidenceIngressDatabaseUrl(),
        ...commonOptions,
      })
    } else {
      const credentials = assertNirmanaEvidenceIngressDatabaseUser()
      if (!process.env.INSTANCE_CONNECTION_NAME || !process.env.DB_NAME) {
        throw new NirmanaEvidenceIngressNotConfiguredError('Cloud SQL ingress requires INSTANCE_CONNECTION_NAME and DB_NAME alongside the distinct ingress secret.')
      }
      const { Connector } = await import('@google-cloud/cloud-sql-connector')
      const connector = new Connector()
      const clientOptions = await connector.getOptions({ instanceConnectionName: process.env.INSTANCE_CONNECTION_NAME })
      globalPools.__nirmanaEvidenceIngressPool = new Pool({
        ...clientOptions,
        user: credentials.user,
        password: credentials.password,
        database: process.env.DB_NAME,
        ...commonOptions,
      })
    }
    globalPools.__nirmanaEvidenceIngressPool.on('error', (error) => {
      console.error('[nirmana evidence ingress pool] idle client error (evicted)', error)
    })
  }
  return globalPools.__nirmanaEvidenceIngressPool
}
