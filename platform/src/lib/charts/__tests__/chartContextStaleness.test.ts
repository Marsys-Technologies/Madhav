/**
 * Chart-context staleness marking (Jātaka Phase-A2, item 2).
 *
 * "Data created from former birth details remains available as historical
 * evidence but cannot be treated as current chart truth." `markChartContextStale`
 * is the pure statement builder the correction transaction runs, inside the
 * SERIALIZABLE transaction, right after the rebuild run is persisted (so
 * `runId` is known). Every statement:
 *   - is scoped to `chart_id = $1`,
 *   - never touches `life_events`,
 *   - never rewrites `lifecycle_status`/`outcome`/`confirmed`/`denied`,
 *   - is idempotent (`WHERE chart_context_stale_at IS NULL`), so a row already
 *     stale from an earlier correction keeps that correction's stamp.
 */
import { describe, expect, it, vi } from 'vitest'
import { markChartContextStale, staleMarkingStatements } from '../chartContextStaleness'

const CHART = '11111111-2222-4333-8444-555555555555'
const RUN = 'run-new'

describe('staleMarkingStatements — pure statement builder', () => {
  const statements = staleMarkingStatements(CHART, RUN)

  it('marks exactly event_chart_state_index and mimamsa_predictions', () => {
    const tables = statements.map((s) => s.sql.match(/UPDATE\s+(\w+)/i)?.[1])
    expect(tables.sort()).toEqual(['event_chart_state_index', 'mimamsa_predictions'])
  })

  it.each(['event_chart_state_index', 'mimamsa_predictions'])('scopes the %s statement to this chart, this run, and only currently-current rows', (table) => {
    const stmt = statements.find((s) => new RegExp(`UPDATE\\s+${table}\\b`, 'i').test(s.sql))!
    expect(stmt.sql).toMatch(/SET\s+chart_context_stale_at\s*=\s*NOW\(\)/i)
    expect(stmt.sql).toMatch(/chart_context_stale_reason\s*=\s*'chart_details_changed'/i)
    expect(stmt.sql).toMatch(/chart_context_superseded_by_run_id\s*=\s*\$2/i)
    expect(stmt.sql).toMatch(/WHERE\s+chart_id\s*=\s*\$1/i)
    expect(stmt.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/i)
    expect(stmt.params).toEqual([CHART, RUN])
  })

  it('never touches lifecycle_status, outcome, confirmed or denied', () => {
    for (const s of statements) {
      expect(s.sql).not.toMatch(/lifecycle_status/i)
      expect(s.sql).not.toMatch(/\boutcome\b/i)
    }
  })

  it('never touches life_events', () => {
    for (const s of statements) expect(s.sql).not.toMatch(/life_events/i)
  })
})

describe('markChartContextStale — executes the statements on the caller\'s transaction client', () => {
  it('runs both UPDATEs on the given db client, in the transaction the caller controls', async () => {
    const calls: Array<{ sql: string; params: unknown[] }> = []
    const db = { query: vi.fn(async (sql: string, params: unknown[] = []) => { calls.push({ sql, params }); return { rows: [], rowCount: 0 } as never }) }
    await markChartContextStale({ db, chartId: CHART, runId: RUN })
    expect(calls).toHaveLength(2)
    expect(calls.every((c) => c.params[0] === CHART && c.params[1] === RUN)).toBe(true)
  })

  it('propagates a query failure (so the caller\'s transaction rolls back)', async () => {
    const db = { query: vi.fn().mockRejectedValue(new Error('db down')) }
    await expect(markChartContextStale({ db, chartId: CHART, runId: RUN })).rejects.toThrow('db down')
  })
})
