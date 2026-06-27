/**
 * D3 Grounding Spine — DB Proxy Interface
 * =========================================
 * Thin abstraction over the Postgres client so the grounding spine can be
 * tested with an in-memory stub without needing a live DB connection.
 *
 * Design rule: the grounding spine imports DbProxy, NOT the real pg client
 * directly. Integration tests wire the real client; unit tests wire a stub.
 * This is how the grounding spine satisfies "testable without the DB" while
 * still proving correctness against the real schema in integration mode.
 */

// ── DbProxy interface ─────────────────────────────────────────────────────────

/**
 * Minimal query interface the grounding spine needs.
 * The real implementation delegates to @/lib/db/client#query.
 * Test stubs implement this with in-memory data.
 */
export interface DbProxy {
  /**
   * Execute a parameterized SQL query and return rows.
   * Read-only: grounding spine never mutates the DB.
   *
   * @param sql   Parameterized SQL ($1, $2, ...)
   * @param params Query parameter values
   * @returns     Array of result rows (typed as T)
   */
  query<T extends Record<string, unknown>>(
    sql: string,
    params: unknown[]
  ): Promise<T[]>
}

// ── Live DB proxy (production) ────────────────────────────────────────────────

/**
 * Production DbProxy that delegates to the shared pg pool.
 * Import and use this in production handlers.
 *
 * Note: lazy-imported to avoid pulling 'server-only' into test environments.
 */
export function makeLiveDbProxy(): DbProxy {
  return {
    async query<T extends Record<string, unknown>>(
      sql: string,
      params: unknown[]
    ): Promise<T[]> {
      // Dynamic import avoids top-level 'server-only' in test bundling
      const { query } = await import('@/lib/db/client')
      const result = await query<T>(sql, params)
      return result.rows
    },
  }
}

// ── In-memory stub proxy (tests) ──────────────────────────────────────────────

/**
 * Row maps for in-memory stub: keyed by table name.
 * Each entry is an array of row objects.
 */
export type StubData = {
  bodha_msr_signals?: Record<string, unknown>[]
  chart_facts?: Record<string, unknown>[]
}

/**
 * Build an in-memory DbProxy stub for unit tests.
 * Queries against 'bodha_msr_signals' and 'chart_facts' are served from
 * the stub data; any other table returns empty rows (not an error).
 *
 * The stub performs parameter substitution (only $1..$N positional params)
 * and simple WHERE clause matching on signal_id/chart_id/fact_id.
 */
export function makeStubDbProxy(data: StubData): DbProxy {
  return {
    async query<T extends Record<string, unknown>>(
      sql: string,
      params: unknown[]
    ): Promise<T[]> {
      const sqlLower = sql.toLowerCase()

      if (sqlLower.includes('bodha_msr_signals')) {
        const rows = (data.bodha_msr_signals ?? []) as T[]
        return filterRows(rows, sql, params)
      }

      if (sqlLower.includes('chart_facts')) {
        const rows = (data.chart_facts ?? []) as T[]
        return filterRows(rows, sql, params)
      }

      return []
    },
  }
}

/**
 * Very simple row filter for stub queries.
 * Supports:
 *   - WHERE chart_id = $N  → filter by chart_id
 *   - WHERE signal_id = ANY($N) → filter signal_id in array
 *   - WHERE fact_id = ANY($N)   → filter fact_id in array
 *   - AND chart_id = $N  (same as above)
 *
 * This is intentionally minimal — real SQL semantics are tested in integration.
 */
function filterRows<T extends Record<string, unknown>>(
  rows: T[],
  sql: string,
  params: unknown[]
): T[] {
  let result = [...rows]

  // Extract chart_id param ($N where column = 'chart_id')
  const chartIdMatch = sql.match(/chart_id\s*=\s*\$(\d+)/i)
  if (chartIdMatch) {
    const idx = parseInt(chartIdMatch[1], 10) - 1
    const chartId = params[idx] as string
    result = result.filter((r) => r['chart_id'] === chartId)
  }

  // Extract signal_id = ANY($N)
  const signalAnyMatch = sql.match(/signal_id\s*=\s*ANY\(\$(\d+)\)/i)
  if (signalAnyMatch) {
    const idx = parseInt(signalAnyMatch[1], 10) - 1
    const ids = params[idx] as string[]
    result = result.filter((r) => ids.includes(r['signal_id'] as string))
  }

  // Extract fact_id = ANY($N)
  const factAnyMatch = sql.match(/fact_id\s*=\s*ANY\(\$(\d+)\)/i)
  if (factAnyMatch) {
    const idx = parseInt(factAnyMatch[1], 10) - 1
    const ids = params[idx] as string[]
    result = result.filter((r) => ids.includes(r['fact_id'] as string))
  }

  return result
}
