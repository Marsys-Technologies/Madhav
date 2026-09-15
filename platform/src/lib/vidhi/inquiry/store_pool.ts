import 'server-only'

import { Connector } from '@google-cloud/cloud-sql-connector'
import { Pool, type PoolClient } from 'pg'

import { assertChartContextValue, CHART_CONTEXT_GUC, PRINCIPAL_ID_GUC } from '@/lib/db/roles'

const g = globalThis as typeof globalThis & {
  __pgInquiryStorePool?: Pool
  __pgInquiryStoreConnector?: Connector
}

export class InquiryStoreRoleNotConfiguredError extends Error {
  constructor() {
    super(
      'INQUIRY_STORE_ROLE_NOT_CONFIGURED: configure INQUIRY_STORE_DATABASE_URL or ' +
      'DB_INQUIRY_USER and DB_INQUIRY_PASSWORD; refusing to use the broad application pool',
    )
    this.name = 'InquiryStoreRoleNotConfiguredError'
  }
}

/**
 * Dedicated least-privilege pool for Pūrṇa lifecycle and managed-job state.
 * It never falls back to DB_USER/DB_PASSWORD: doing so would silently bypass
 * the role_web_serve grant and RLS boundary these stores are designed around.
 */
export async function getInquiryStorePool(): Promise<Pool> {
  if (g.__pgInquiryStorePool) return g.__pgInquiryStorePool

  const keepalive = {
    keepAlive: true,
    keepAliveInitialDelayMillis: 10_000,
    idleTimeoutMillis: 15_000,
    connectionTimeoutMillis: 5_000,
    options: '-c statement_timeout=25000',
    max: 10,
  }
  if (process.env.INQUIRY_STORE_DATABASE_URL) {
    g.__pgInquiryStorePool = new Pool({
      connectionString: process.env.INQUIRY_STORE_DATABASE_URL,
      ...keepalive,
    })
  } else if (process.env.DB_INQUIRY_USER && process.env.DB_INQUIRY_PASSWORD) {
    const instanceConnectionName = process.env.INSTANCE_CONNECTION_NAME
    const database = process.env.DB_NAME
    if (!instanceConnectionName || !database) throw new InquiryStoreRoleNotConfiguredError()
    const connector = new Connector()
    const clientOpts = await connector.getOptions({ instanceConnectionName })
    g.__pgInquiryStoreConnector = connector
    g.__pgInquiryStorePool = new Pool({
      ...clientOpts,
      user: process.env.DB_INQUIRY_USER,
      password: process.env.DB_INQUIRY_PASSWORD,
      database,
      ...keepalive,
    })
  } else {
    throw new InquiryStoreRoleNotConfiguredError()
  }

  g.__pgInquiryStorePool.on('error', (error) => {
    console.error('[pg inquiry store] idle client error (evicted)', error)
  })
  return g.__pgInquiryStorePool
}

/** Pin tenant context for every query made through the dedicated RLS role. */
export async function withInquiryStoreContext<T>(
  principalUid: string,
  chartId: string | null,
  action: (client: PoolClient) => Promise<T>,
): Promise<T> {
  const pinnedChart = chartId === null ? null : assertChartContextValue(chartId)
  const pool = await getInquiryStorePool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query('SELECT set_config($1, $2, true)', [PRINCIPAL_ID_GUC, principalUid])
    if (pinnedChart !== null) {
      await client.query('SELECT set_config($1, $2, true)', [CHART_CONTEXT_GUC, pinnedChart])
    }
    const result = await action(client)
    await client.query('COMMIT')
    return result
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
  }
}

export async function __resetInquiryStorePoolForTests(): Promise<void> {
  if (g.__pgInquiryStorePool) await g.__pgInquiryStorePool.end()
  if (g.__pgInquiryStoreConnector) await g.__pgInquiryStoreConnector.close()
  delete g.__pgInquiryStorePool
  delete g.__pgInquiryStoreConnector
}
