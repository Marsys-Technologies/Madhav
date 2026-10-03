/**
 * Test helper for DELETE /api/charts/[id].
 *
 * A fake two-connection pool that models the two PostgreSQL behaviours that
 * matter to the chart-delete transaction (CHART_DELETION_COMPLETENESS_DESIGN
 * section 2.1, finding R2):
 *
 *   - transaction state belongs to a CONNECTION, not to the pool;
 *   - `pool.query()` checks out whichever connection is next (so a BEGIN and a
 *     later DELETE issued through it can land on different connections, and an
 *     unrelated request in between makes that the norm), whereas
 *     `pool.connect()` pins one connection until `release()`.
 *
 * Three chart-owned rows exist (one each in conversations, asset_throughput
 * and chart_grants), the "3 of 3" of the design-report fixture.
 */

export interface StatementLog {
  conn: number
  sql: string
}

export interface FakeClient {
  query: (sql: string, params?: unknown[]) => Promise<{ rows: unknown[]; rowCount: number }>
  release: (err?: unknown) => void
}

export interface FakeDeletePoolOptions {
  role?: string
  owner?: string
  /** Statement (prefix match) that throws on its first execution. */
  failOn?: string
  /** Statement (prefix match) that waits for `gate.release()` before running. */
  gateOn?: string
  /** Make the ROLLBACK statement itself throw (broken connection). */
  failRollback?: boolean
}

export function makeFakeDeletePool(opts: FakeDeletePoolOptions = {}) {
  const log: StatementLog[] = []
  const committed = new Set(['conversations', 'asset_throughput', 'chart_grants'])
  const conns = [0, 1].map((id) => ({ id, inTx: false, staged: [] as string[], busy: false }))
  let next = 0
  let gateResolve: (() => void) | null = null
  const gatePromise = opts.gateOn ? new Promise<void>((r) => (gateResolve = r)) : null
  let gateHit: (() => void) | null = null
  const gateReached = new Promise<void>((r) => (gateHit = r))
  const releases: Array<{ conn: number; err: unknown }> = []
  let failed = false

  async function exec(conn: (typeof conns)[number], sql: string): Promise<{ rows: unknown[]; rowCount: number }> {
    log.push({ conn: conn.id, sql })
    if (/^SELECT role FROM profiles/.test(sql)) return { rows: [{ role: opts.role ?? 'guest' }], rowCount: 1 }
    if (/^SELECT owner_id, client_id FROM charts/.test(sql)) {
      return { rows: [{ owner_id: opts.owner ?? 'owner-uid', client_id: 'client-x' }], rowCount: 1 }
    }
    if (opts.gateOn && sql.startsWith(opts.gateOn) && gatePromise) {
      gateHit?.()
      await gatePromise
    }
    if (opts.failOn && sql.startsWith(opts.failOn) && !failed) {
      failed = true
      throw new Error('injected failure')
    }
    if (sql === 'BEGIN') {
      conn.inTx = true
      return { rows: [], rowCount: 0 }
    }
    if (sql === 'COMMIT') {
      if (conn.inTx) for (const t of conn.staged) committed.delete(t)
      conn.staged = []
      conn.inTx = false
      return { rows: [], rowCount: 0 }
    }
    if (sql === 'ROLLBACK') {
      if (opts.failRollback) throw new Error('connection terminated')
      conn.staged = []
      conn.inTx = false
      return { rows: [], rowCount: 0 }
    }
    const del = /^DELETE FROM (\w+)/.exec(sql)
    if (del) {
      if (conn.inTx) conn.staged.push(del[1])
      else committed.delete(del[1]) // autocommit: durable immediately
      return { rows: [], rowCount: 1 }
    }
    return { rows: [], rowCount: 0 }
  }

  function pick() {
    for (let i = 0; i < conns.length; i++) {
      const c = conns[(next + i) % conns.length]
      if (!c.busy) {
        next = (c.id + 1) % conns.length
        return c
      }
    }
    throw new Error('fake pool exhausted')
  }

  const pool = {
    /** pool-level query: one statement on whichever connection is next. */
    async query(sql: string, params?: unknown[]) {
      void params
      const c = pick()
      c.busy = true
      try {
        return await exec(c, sql)
      } finally {
        c.busy = false
      }
    },
    /** dedicated checkout: pinned until release(). */
    async connect(): Promise<FakeClient> {
      const c = pick()
      c.busy = true
      return {
        query: (sql: string, params?: unknown[]) => {
          void params
          return exec(c, sql)
        },
        release: (err?: unknown) => {
          releases.push({ conn: c.id, err })
          c.busy = false
        },
      }
    },
  }

  return {
    pool,
    log,
    releases,
    /** rows still durable after everything the test ran */
    rowsLeft: () => committed.size,
    gateReached,
    gate: { release: () => gateResolve?.() },
    /** statements of the delete transaction (BEGIN..COMMIT/ROLLBACK) in order */
    txStatements: () => {
      const start = log.findIndex((l) => l.sql === 'BEGIN')
      return start < 0 ? [] : log.slice(start)
    },
    connections: conns,
  }
}
