/**
 * Samīkṣā ledger — chart-context-stale rows cannot re-enter the current
 * lifecycle (Jātaka Phase-A3, item 2; independent-review finding, HIGH→Important).
 *
 * A `detected` claim a correction has marked chart_context_stale_at reflects
 * former birth details. transitionLifecycle refuses to advance it to
 * `confirmed` or `open` — advancing it would put a historical claim back into
 * the current lifecycle and (via confirmDetectedRow) stamp it with the
 * CORRECTED chart's build provenance, misattributing it as current. Recording
 * an eventual historical outcome (window_closed → outcome_recorded /
 * unverisifable) remains permitted — that transition is deliberately
 * unguarded, matching outcome recording elsewhere in this ledger.
 */
import { describe, expect, it, vi } from 'vitest'
import { transitionLifecycle } from '../writer'

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

describe('transitionLifecycle — a chart-context-stale row cannot advance to confirmed or open', () => {
  it('detected → confirmed: the UPDATE is scoped to chart_context_stale_at IS NULL', async () => {
    const { exec, calls } = fakeExec([
      [{ lifecycle_status: 'detected' }], // currentStatus
      [{ id: 'r1' }], // guarded UPDATE succeeds
    ])
    await transitionLifecycle('r1', 'confirmed', { stamp: { build_id: 'b', priors_version: 'p', formula_versions: {}, ranking_config: {}, now_context_date: '2026-01-01' } }, exec)
    const update = calls.find((c) => /^UPDATE/i.test(c.sql))!
    expect(update.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })

  it('confirmed → open: the UPDATE is scoped to chart_context_stale_at IS NULL', async () => {
    const { exec, calls } = fakeExec([
      [{ lifecycle_status: 'confirmed' }],
      [{ id: 'r1' }],
    ])
    await transitionLifecycle('r1', 'open', {}, exec)
    const update = calls.find((c) => /^UPDATE/i.test(c.sql))!
    expect(update.sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })

  it('a stale detected row refused with a named CHART_CONTEXT_STALE error, distinct from an ordinary concurrency race', async () => {
    const { exec } = fakeExec([
      [{ lifecycle_status: 'detected' }], // currentStatus
      [], // guarded UPDATE affects 0 rows (stale)
      [{ chart_context_stale_at: '2026-09-27T00:00:00Z' }], // the disambiguating check
    ])
    await expect(
      transitionLifecycle('r1', 'confirmed', { stamp: { build_id: 'b', priors_version: 'p', formula_versions: {}, ranking_config: {}, now_context_date: '2026-01-01' } }, exec),
    ).rejects.toThrow(/CHART_CONTEXT_STALE/)
  })

  it('an ordinary concurrent change (not stale) still throws the pre-existing concurrency error', async () => {
    const { exec } = fakeExec([
      [{ lifecycle_status: 'detected' }],
      [], // guarded UPDATE affects 0 rows
      [{ chart_context_stale_at: null }], // disambiguating check: not stale — a real race
    ])
    await expect(
      transitionLifecycle('r1', 'confirmed', { stamp: { build_id: 'b', priors_version: 'p', formula_versions: {}, ranking_config: {}, now_context_date: '2026-01-01' } }, exec),
    ).rejects.toThrow(/changed concurrently/)
  })

  it('window_closed → outcome_recorded remains unguarded — recording a historical outcome is permitted', async () => {
    const { exec, calls } = fakeExec([
      [{ lifecycle_status: 'window_closed' }],
      [{ id: 'r1' }],
    ])
    await transitionLifecycle('r1', 'outcome_recorded', { outcome: 'happened', outcome_value: 1 }, exec)
    const update = calls.find((c) => /^UPDATE/i.test(c.sql))!
    expect(update.sql).not.toMatch(/chart_context_stale_at/)
  })
})
