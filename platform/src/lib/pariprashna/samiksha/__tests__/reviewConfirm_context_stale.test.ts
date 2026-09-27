/**
 * confirmDetectedCandidate — chart-context staleness defense-in-depth
 * (Jātaka Phase-A3, independent-review finding). The confidence-band UPDATE
 * that runs while the row is still `detected` is scoped to
 * chart_context_stale_at IS NULL, consistent with transitionLifecycle's own
 * guard on the confirmed/open steps this function goes on to call.
 */
import { describe, expect, it, vi } from 'vitest'
import { confirmDetectedCandidate } from '../reviewConfirm'

const STAMP = { build_id: 'b', priors_version: 'p', formula_versions: {}, ranking_config: {}, now_context_date: '2026-01-01' }

function fakeExec(responses: unknown[][]) {
  let i = 0
  const calls: Array<{ sql: string; params?: unknown[] }> = []
  const exec = vi.fn(async (sql: string, params?: unknown[]) => {
    calls.push({ sql, params })
    const rows = responses[i] ?? []
    i++
    return { rows: rows as never[], rowCount: rows.length }
  })
  return { exec, calls }
}

describe('confirmDetectedCandidate — the confidence-band UPDATE excludes context-stale rows', () => {
  it('the band UPDATE (while still detected) is scoped to chart_context_stale_at IS NULL', async () => {
    const { exec, calls } = fakeExec([
      [{ id: 'r1' }], // band UPDATE
      [{ lifecycle_status: 'detected' }], // currentStatus (confirmDetectedRow)
      [{ id: 'r1' }], // detected -> confirmed UPDATE
      [{ lifecycle_status: 'confirmed' }], // currentStatus (confirmed -> open)
      [{ id: 'r1' }], // confirmed -> open UPDATE
    ])
    await confirmDetectedCandidate({ rowId: 'r1', probability: 0.6, stamp: STAMP }, exec)
    const bandUpdate = calls.find((c) => /SET confidence/i.test(c.sql))!
    expect(bandUpdate.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})
