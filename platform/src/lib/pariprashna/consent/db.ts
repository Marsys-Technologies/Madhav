/**
 * Paripraśna consent — the production `ConsentDb`.
 *
 * Kept in its own module so every other file in this directory imports only
 * `types.ts` (pure) and can therefore be unit-tested without `server-only`,
 * without a pool, and without a database.
 */

import type { ConsentDb, ConsentQueryable } from './types'

/** Production DB port: the shared pg pool, with a real single-connection transaction. */
export function defaultConsentDb(): ConsentDb {
  return {
    async query(sql, params) {
      const { query } = await import('@/lib/db/client')
      const r = await query(sql as string, params)
      return { rows: r.rows as never[] }
    },
    async withTransaction(fn) {
      const { getPool } = await import('@/lib/db/client')
      const pool = await getPool()
      const client = await pool.connect()
      try {
        await client.query('BEGIN')
        const tx: ConsentQueryable = {
          async query(sql, params) {
            const r = await client.query(sql as string, params as unknown[])
            return { rows: r.rows as never[] }
          },
        }
        const out = await fn(tx)
        await client.query('COMMIT')
        return out
      } catch (err) {
        await client.query('ROLLBACK')
        throw err
      } finally {
        client.release()
      }
    },
  }
}
