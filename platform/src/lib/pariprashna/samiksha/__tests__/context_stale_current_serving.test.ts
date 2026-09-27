/**
 * Samīkṣā ledger — chart-context staleness (Jātaka Phase-A3, item 2).
 *
 * "Old-context ledger rows cannot seed a current reading" / "cannot count as
 * current availability" / "lifecycle sweeps must not mutate them as though
 * they were current." Every current-serving surface of this ledger excludes a
 * row a correction has marked chart_context_stale_at (migration 1123) by
 * default. "Samīkṣā history remains readable": a single-row fetch by id
 * (outcome recording, confirm/dismiss) and the total census count are
 * unaffected — recording a historical outcome, and knowing the ledger's whole
 * size, are both explicitly permitted regardless of staleness.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'

function fakeExec(rows: unknown[] = []) {
  const calls: Array<{ sql: string; params?: unknown[] }> = []
  const exec = vi.fn(async (sql: string, params?: unknown[]) => {
    calls.push({ sql, params })
    return { rows: rows as never[], rowCount: rows.length }
  })
  return { exec, calls }
}

describe('countBadge — current actionable count excludes stale rows', () => {
  it('scopes the count to chart_context_stale_at IS NULL', async () => {
    const { countBadge } = await import('../badge')
    const { exec, calls } = fakeExec([{ count: '0' }])
    await countBadge('c1', exec)
    expect(calls[0]!.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})

describe('listLedgerRowsForChart — current-actionable lists exclude stale rows by default', () => {
  it('excludes stale rows unless includeStale is passed', async () => {
    const { listLedgerRowsForChart } = await import('../reader')
    const { exec, calls } = fakeExec()
    await listLedgerRowsForChart('c1', { status: 'detected' }, exec)
    expect(calls[0]!.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })

  it('includeStale drops the exclusion and the row carries explicit historical-context metadata', async () => {
    const { listLedgerRowsForChart } = await import('../reader')
    const { exec, calls } = fakeExec([
      { id: 'r1', chart_context_stale_at: '2026-09-27T00:00:00Z', chart_context_stale_reason: 'chart_details_changed', chart_context_superseded_by_run_id: 'run-1' },
    ])
    const rows = await listLedgerRowsForChart('c1', { includeStale: true }, exec)
    expect(calls[0]!.sql).not.toMatch(/chart_context_stale_at\s+IS\s+NULL/)
    expect(rows[0]).toMatchObject({ chart_context_stale_at: '2026-09-27T00:00:00Z', chart_context_stale_reason: 'chart_details_changed' })
  })

  it('getLedgerRow (single-row fetch by id) is never filtered by staleness — Samīkṣā history remains readable', async () => {
    const { getLedgerRow } = await import('../reader')
    const { exec, calls } = fakeExec([{ id: 'r1' }])
    await getLedgerRow('r1', exec)
    // It still SELECTs the column (so the caller can see the metadata); it
    // must never WHERE-filter by it.
    expect(calls[0]!.sql).toMatch(/chart_context_stale_at/)
    expect(calls[0]!.sql).not.toMatch(/WHERE[\s\S]*chart_context_stale_at\s+IS\s+NULL/)
  })
})

describe('countLedgerRows — the census total is unaffected (audit total, not current-actionable)', () => {
  it('never filters by staleness', async () => {
    const { countLedgerRows } = await import('../writer')
    const { exec, calls } = fakeExec([{ count: '0' }])
    await countLedgerRows('c1', exec)
    expect(calls[0]!.sql).not.toMatch(/chart_context_stale_at/)
  })
})

describe('getCoverageStats — the current-pipeline panel excludes stale rows', () => {
  it('scopes the grouped lifecycle count to chart_context_stale_at IS NULL', async () => {
    const { getCoverageStats } = await import('../review')
    const { exec, calls } = fakeExec([])
    await getCoverageStats('c1', exec)
    expect(calls[0]!.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})

describe('daily_job — the sweep never mutates a stale row as though it were current', () => {
  beforeEach(() => vi.resetModules())

  it('selectCloseableIds (drives the open→window_closed transition) excludes stale rows', async () => {
    const { runDailyJob } = await import('../daily_job')
    const { exec, calls } = fakeExec([])
    await runDailyJob({ asOf: '2026-09-27', chartId: 'c1', exec, closingSoonDays: 7 })
    const closeableCall = calls.find((c) => /lifecycle_status = 'open'/.test(c.sql) && /upper\("window"\) < \$1/.test(c.sql))
    expect(closeableCall, 'expected the closeable-window select').toBeDefined()
    expect(closeableCall!.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })

  it('selectClosingSoon (surfaces a "closing soon" notice) excludes stale rows', async () => {
    const { runDailyJob } = await import('../daily_job')
    const { exec, calls } = fakeExec([])
    await runDailyJob({ asOf: '2026-09-27', chartId: 'c1', exec, closingSoonDays: 7 })
    const soonCall = calls.find((c) => /lifecycle_status = 'open'/.test(c.sql) && /upper\("window"\) >= \$1/.test(c.sql))
    expect(soonCall, 'expected the closing-soon select').toBeDefined()
    expect(soonCall!.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})
