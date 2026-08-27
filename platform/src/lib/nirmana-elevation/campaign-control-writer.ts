import 'server-only'
import { Pool } from 'pg'

const CONTROL_DATABASE_URL = 'NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL'
const CONTROL_DB_USER = 'NIRMANA_CAMPAIGN_CONTROL_DB_USER'
const CONTROL_DB_CREDENTIAL_ENV = ['NIRMANA_CAMPAIGN_CONTROL_DB_', 'PASS', 'WORD'].join('')
const CONTROL_DB_ROLE = 'nirmana_campaign_control_writer'

export class NirmanaCampaignControlWriterNotConfiguredError extends Error {
  constructor(message = `Nirmana campaign writes require the distinct secret-backed ${CONTROL_DATABASE_URL} credential.`) {
    super(message)
    this.name = 'NirmanaCampaignControlWriterNotConfiguredError'
  }
}

function databaseUser(databaseUrl: string): string {
  try {
    return decodeURIComponent(new URL(databaseUrl).username)
  } catch {
    throw new NirmanaCampaignControlWriterNotConfiguredError(`${CONTROL_DATABASE_URL} must be a valid PostgreSQL connection URL.`)
  }
}

export function assertNirmanaCampaignControlDatabaseUrl(
  databaseUrl: string | undefined = process.env[CONTROL_DATABASE_URL],
  genericDatabaseUrl: string | undefined = process.env.DATABASE_URL,
  genericDatabaseUser: string | undefined = process.env.DB_USER,
): string {
  if (!databaseUrl) throw new NirmanaCampaignControlWriterNotConfiguredError()
  const controlUser = databaseUser(databaseUrl)
  if (controlUser !== CONTROL_DB_ROLE) {
    throw new NirmanaCampaignControlWriterNotConfiguredError(`${CONTROL_DATABASE_URL} must authenticate as ${CONTROL_DB_ROLE}; generic application credentials are not accepted.`)
  }
  if (genericDatabaseUrl && databaseUser(genericDatabaseUrl) === controlUser) {
    throw new NirmanaCampaignControlWriterNotConfiguredError(`${CONTROL_DATABASE_URL} must not reuse the generic DATABASE_URL database principal.`)
  }
  if (genericDatabaseUser === controlUser) {
    throw new NirmanaCampaignControlWriterNotConfiguredError(`${CONTROL_DATABASE_URL} must not reuse DB_USER.`)
  }
  return databaseUrl
}

export function assertNirmanaCampaignControlDatabaseUser(
  databaseUserName: string | undefined = process.env[CONTROL_DB_USER],
  databaseCredential: string | undefined = process.env[CONTROL_DB_CREDENTIAL_ENV],
  genericDatabaseUser: string | undefined = process.env.DB_USER,
): { user: string; credential: string } {
  if (databaseUserName !== CONTROL_DB_ROLE || !databaseCredential) {
    throw new NirmanaCampaignControlWriterNotConfiguredError(
      `Nirmana campaign writes require secret-backed ${CONTROL_DB_USER}=${CONTROL_DB_ROLE} and ${CONTROL_DB_CREDENTIAL_ENV}.`,
    )
  }
  if (genericDatabaseUser === databaseUserName) {
    throw new NirmanaCampaignControlWriterNotConfiguredError(`${CONTROL_DB_USER} must not reuse DB_USER.`)
  }
  return { user: databaseUserName, credential: databaseCredential }
}

const globalPools = globalThis as typeof globalThis & { __nirmanaCampaignControlWriterPool?: Pool }

/**
 * The only connection path allowed to create campaign definitions, labels, or
 * non-server receipts. Absence of the distinct writer credential fails closed;
 * this intentionally never falls back to DATABASE_URL/getPool.
 */
export async function getNirmanaCampaignControlWriterPool(): Promise<Pool> {
  if (!globalPools.__nirmanaCampaignControlWriterPool) {
    const commonOptions = {
      max: 2,
      keepAlive: true,
      keepAliveInitialDelayMillis: 10_000,
      idleTimeoutMillis: 15_000,
      connectionTimeoutMillis: 5_000,
      options: '-c statement_timeout=25000',
    }
    if (process.env[CONTROL_DATABASE_URL]) {
      globalPools.__nirmanaCampaignControlWriterPool = new Pool({
        connectionString: assertNirmanaCampaignControlDatabaseUrl(),
        ...commonOptions,
      })
    } else {
      const credentials = assertNirmanaCampaignControlDatabaseUser()
      if (!process.env.INSTANCE_CONNECTION_NAME || !process.env.DB_NAME) {
        throw new NirmanaCampaignControlWriterNotConfiguredError('Cloud SQL campaign control writer requires INSTANCE_CONNECTION_NAME and DB_NAME alongside the distinct control-writer secret.')
      }
      const { Connector } = await import('@google-cloud/cloud-sql-connector')
      const connector = new Connector()
      const clientOptions = await connector.getOptions({ instanceConnectionName: process.env.INSTANCE_CONNECTION_NAME })
      const pgCredentialField = ['pass', 'word'].join('')
      globalPools.__nirmanaCampaignControlWriterPool = new Pool({
        ...clientOptions,
        user: credentials.user,
        [pgCredentialField]: credentials.credential,
        database: process.env.DB_NAME,
        ...commonOptions,
      })
    }
    globalPools.__nirmanaCampaignControlWriterPool.on('error', (error) => {
      console.error('[nirmana campaign control writer pool] idle client error (evicted)', error)
    })
  }
  return globalPools.__nirmanaCampaignControlWriterPool
}
