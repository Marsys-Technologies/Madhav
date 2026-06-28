import 'server-only'
import { Pool, QueryResult, QueryResultRow, types } from 'pg'

// Return date/timestamp columns as strings to match TypeScript types
types.setTypeParser(types.builtins.DATE, (v) => v)
types.setTypeParser(types.builtins.TIMESTAMP, (v) => v)
types.setTypeParser(types.builtins.TIMESTAMPTZ, (v) => v)
// Return NUMERIC/DECIMAL columns as numbers (pg returns them as strings by default)
types.setTypeParser(1700, parseFloat)

// Hot-reload guard: reuse the pool across Next.js HMR cycles in dev so we
// don't abandon open connections on every file save.
const g = globalThis as typeof globalThis & { __pgPool?: Pool }

// Recycle idle sockets before Cloud SQL Auth Proxy drops them (~10 min)
// to avoid ECONNRESET on pooled-but-dead connections.
//
// idleTimeoutMillis: 15 s — aggressive eviction so connections cycle out before
// the proxy's idle-drop window. macOS TCP keepalive (keepidle = 7200 s) is
// effectively useless for detecting dead connections on this timescale, so we
// rely on eviction instead. Cost: ~100 ms reconnect after quiet periods, which
// is acceptable in local dev and has no effect in production (cloud-sql-connector
// path manages its own connection lifecycle).
//
// connectionTimeoutMillis: fail fast if the pool queue is saturated (no available
// slot within 5 s) rather than waiting indefinitely.
//
// statement_timeout: 25 s server-side hard cap so runaway queries cannot hold a
// connection slot indefinitely (Cloud SQL default is 0 = unlimited).
const POOL_KEEPALIVE = {
  keepAlive: true,
  keepAliveInitialDelayMillis: 10_000,
  idleTimeoutMillis: 15_000,
  connectionTimeoutMillis: 5_000,
  options: '-c statement_timeout=25000',
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
      new Pool({ connectionString: process.env.DATABASE_URL, max: 15, ...POOL_KEEPALIVE })
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
      max: 15,
      ...POOL_KEEPALIVE,
    })
  )
}

export async function getPool(): Promise<Pool> {
  if (!g.__pgPool) g.__pgPool = await initPool()
  return g.__pgPool
}

function isTransientConnectionError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false
  const e = err as { code?: string; message?: string }
  return (
    e.code === 'ECONNRESET' ||
    e.code === '57P01' ||
    e.message?.includes('timeout exceeded when trying to connect') ||
    e.message?.includes('Connection pool is full') ||
    e.message === 'Connection terminated unexpectedly' ||
    e.message === 'Client has encountered a connection error and is not queryable'
  )
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  sql: string,
  params?: unknown[]
): Promise<QueryResult<T>> {
  const pool = await getPool()
  try {
    return await pool.query<T>(sql, params)
  } catch (err) {
    if (isTransientConnectionError(err)) {
      console.warn('[pg pool] transient connection error, retrying once', err)
      return pool.query<T>(sql, params)
    }
    throw err
  }
}
