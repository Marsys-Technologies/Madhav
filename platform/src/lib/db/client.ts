import 'server-only'
import { Pool, QueryResult, QueryResultRow, types } from 'pg'

// Return date/timestamp columns as strings to match TypeScript types
types.setTypeParser(types.builtins.DATE, (v) => v)
types.setTypeParser(types.builtins.TIMESTAMP, (v) => v)
types.setTypeParser(types.builtins.TIMESTAMPTZ, (v) => v)
// Return NUMERIC/DECIMAL columns as numbers (pg returns them as strings by default)
types.setTypeParser(1700, parseFloat)

let _pool: Pool | null = null

// Recycle idle sockets before Cloud SQL Auth Proxy drops them (~10 min)
// to avoid ECONNRESET on pooled-but-dead connections.
const POOL_KEEPALIVE = {
  keepAlive: true,
  idleTimeoutMillis: 30_000,
}

function attachErrorHandler(pool: Pool): Pool {
  pool.on('error', (err) => {
    console.error('[pg pool] idle client error (evicted)', err)
  })
  return pool
}

async function initPool(): Promise<Pool> {
  if (process.env.DATABASE_URL) {
    // Local dev: Cloud SQL Auth Proxy via DATABASE_URL from .env.rag
    return attachErrorHandler(
      new Pool({ connectionString: process.env.DATABASE_URL, ...POOL_KEEPALIVE })
    )
  }
  // Production (Cloud Run): cloud-sql-connector authenticates via ADC
  const { Connector } = await import('@google-cloud/cloud-sql-connector')
  const connector = new Connector()
  const clientOpts = await connector.getOptions({
    instanceConnectionName: process.env.INSTANCE_CONNECTION_NAME!,
  })
  return attachErrorHandler(
    new Pool({
      ...clientOpts,
      user: process.env.DB_USER!,
      password: process.env.DB_PASSWORD!,
      database: process.env.DB_NAME!,
      ...POOL_KEEPALIVE,
    })
  )
}

export async function getPool(): Promise<Pool> {
  if (!_pool) _pool = await initPool()
  return _pool
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  sql: string,
  params?: unknown[]
): Promise<QueryResult<T>> {
  const pool = await getPool()
  return pool.query<T>(sql, params)
}
