/**
 * The window-opening ask — selector unit tests (lane P4-G).
 *
 * §N.8: "what code path would have to run — and fail — for this signal to correctly read
 * false?" These tests answer that directly, against a MOCK Postgres that faithfully evaluates
 * the exact predicate `select.ts` sends — an in-memory reimplementation of the `WHERE` clause,
 * not a stub that always agrees. Each negative case below is a row shape the mock genuinely
 * excludes, and the fired case proves the same mock genuinely includes the row that should
 * fire. The real-DB round trip (`select_capture_db.integration.test.ts`) re-proves this against
 * an actual Postgres with migration 470 applied — this file is the fast, zero-I/O layer.
 */

import { describe, it, expect } from 'vitest'
import { evaluateWindowAsk, selectAskableWindow, readLifecycleCensus, ASKABLE_LIFECYCLE_STATE } from '../select'
import type { LedgerExecutor } from '../../writer'
import type { LedgerRow, LifecycleState, Outcome } from '../../schema'

// ---------------------------------------------------------------------------
// A faithful in-memory Postgres double for exactly the queries select.ts issues.
// ---------------------------------------------------------------------------

interface FakeRow extends Partial<LedgerRow> {
  id: string
  chart_id: string
  lifecycle_status: LifecycleState
  window: string | null // "[lo,hi)" literal
  outcome: Outcome | null
}

function upperOf(literal: string | null): string | null {
  if (!literal) return null
  const m = /^[[(]([^,]*),([^)\]]*)[)\]]$/.exec(literal.trim())
  return m ? m[2].trim() : null
}

function makeExec(rows: FakeRow[]): LedgerExecutor {
  return (async <T,>(sql: string, params?: unknown[]) => {
    const p = (params ?? []) as unknown[]
    // readLifecycleCensus
    if (sql.includes('GROUP BY lifecycle_status')) {
      const chartId = p[0]
      const counts = new Map<string, number>()
      for (const r of rows) {
        if (r.chart_id !== chartId) continue
        counts.set(r.lifecycle_status, (counts.get(r.lifecycle_status) ?? 0) + 1)
      }
      const out = [...counts.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([lifecycle_status, n]) => ({ lifecycle_status, n: String(n) }))
      return { rows: out as T[], rowCount: out.length }
    }
    // the future-count query
    if (sql.includes('count(*)::text AS n') && sql.includes(`lifecycle_status = '${ASKABLE_LIFECYCLE_STATE}'`)) {
      const [chartId, asOf] = p as [string, string]
      const n = rows.filter(
        (r) =>
          r.chart_id === chartId &&
          r.lifecycle_status === ASKABLE_LIFECYCLE_STATE &&
          r.window !== null &&
          (upperOf(r.window) ?? '') > asOf,
      ).length
      return { rows: [{ n: String(n) }] as T[], rowCount: 1 }
    }
    // selectAskableWindow
    if (sql.includes(`lifecycle_status = '${ASKABLE_LIFECYCLE_STATE}'`) && sql.includes('ORDER BY upper')) {
      const [chartId, asOf] = p as [string, string]
      const candidates = rows
        .filter(
          (r) =>
            r.chart_id === chartId &&
            r.lifecycle_status === ASKABLE_LIFECYCLE_STATE &&
            r.window !== null &&
            (upperOf(r.window) ?? '') <= asOf &&
            r.outcome === null,
        )
        .sort((a, b) => {
          const ua = upperOf(a.window) ?? ''
          const ub = upperOf(b.window) ?? ''
          return ua === ub ? a.id.localeCompare(b.id) : ua.localeCompare(ub)
        })
      const row = candidates[0]
      return { rows: (row ? [row] : []) as T[], rowCount: row ? 1 : 0 }
    }
    throw new Error(`unexpected SQL in select.test.ts fake executor: ${sql}`)
  }) as LedgerExecutor
}

function fakeRow(overrides: Partial<FakeRow> = {}): FakeRow {
  return {
    id: 'row-1',
    chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
    claim_text: 'The native takes a new role.',
    domain: 'career',
    window: '[2026-01-01,2026-07-01)',
    confidence: '[0.55,0.7)',
    direction: 'positive',
    technique_refs: [],
    grounding_fact_ids: [],
    created_from_channel: 'pariprashna',
    lifecycle_status: 'window_closed',
    outcome: null,
    confirmed_at: '2026-01-01T00:00:00.000Z',
    ...overrides,
  } as FakeRow
}

const CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

describe('evaluateWindowAsk — flag_off', () => {
  it('never queries the DB when the flag is off', async () => {
    let queried = false
    const exec: LedgerExecutor = (async () => {
      queried = true
      return { rows: [], rowCount: 0 }
    }) as LedgerExecutor
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: false })
    expect(decision.fired).toBe(false)
    if (!decision.fired) expect(decision.reason).toBe('flag_off')
    expect(queried).toBe(false)
  })
})

describe('evaluateWindowAsk — no_ledger_rows', () => {
  it('reports no_ledger_rows with an empty census when the chart has no rows at all', async () => {
    const exec = makeExec([])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) {
      expect(decision.reason).toBe('no_ledger_rows')
      expect(decision.census).toEqual({})
    }
  })
})

describe('evaluateWindowAsk — no_window_closed_row (THE IMPORTANT NEGATIVE)', () => {
  it('does NOT fire on a row that is still `open` (window running)', async () => {
    const exec = makeExec([fakeRow({ lifecycle_status: 'open' })])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) {
      expect(decision.reason).toBe('no_window_closed_row')
      expect(decision.census.open).toBe(1)
    }
  })

  it('does NOT fire on a row already `outcome_recorded`', async () => {
    const exec = makeExec([fakeRow({ lifecycle_status: 'outcome_recorded', outcome: 'happened' })])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) expect(decision.reason).toBe('no_window_closed_row')
  })

  it('does NOT fire on a `window_closed` row whose outcome is already set (belt-and-braces)', async () => {
    const exec = makeExec([fakeRow({ lifecycle_status: 'window_closed', outcome: 'happened' })])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) expect(decision.reason).toBe('no_window_closed_row')
  })

  it('does NOT fire on a `dismissed` or `lapsed` row', async () => {
    for (const lifecycle_status of ['dismissed', 'lapsed'] as const) {
      const exec = makeExec([fakeRow({ lifecycle_status })])
      const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
      expect(decision.fired).toBe(false)
    }
  })
})

describe('evaluateWindowAsk — window_not_yet_past (defence in depth)', () => {
  it('does NOT fire on a `window_closed` row whose upper bound is still in the future', async () => {
    const exec = makeExec([fakeRow({ lifecycle_status: 'window_closed', window: '[2026-01-01,2027-01-01)' })])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) {
      expect(decision.reason).toBe('window_not_yet_past')
      expect(decision.detail).toMatch(/1 row\(s\)/)
    }
  })
})

describe('evaluateWindowAsk — THE POSITIVE CASE: fires only on a genuinely past, closed, unanswered window', () => {
  it('fires when a real window_closed row has a past upper bound and a null outcome', async () => {
    const exec = makeExec([fakeRow({ lifecycle_status: 'window_closed', window: '[2026-01-01,2026-07-01)' })])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(true)
    if (decision.fired) {
      expect(decision.row.id).toBe('row-1')
      expect(decision.ask.ledgerRowId).toBe('row-1')
      expect(decision.census.window_closed).toBe(1)
    }
  })

  it('selects deterministically — oldest-closing window first, id as tiebreak', async () => {
    const exec = makeExec([
      fakeRow({ id: 'row-B', window: '[2026-01-01,2026-08-01)' }),
      fakeRow({ id: 'row-A', window: '[2026-01-01,2026-07-01)' }),
    ])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(true)
    if (decision.fired) expect(decision.row.id).toBe('row-A')
  })

  it('is chart-scoped: a closed window on a DIFFERENT chart never fires for this chart', async () => {
    const exec = makeExec([fakeRow({ chart_id: '00000000-0000-0000-0000-000000000099' })])
    const decision = await evaluateWindowAsk({ chartId: CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) expect(decision.reason).toBe('no_ledger_rows')
  })
})

describe('evaluateWindowAsk — input validation', () => {
  it('throws on a non-ISO asOf rather than silently misinterpreting it', async () => {
    const exec = makeExec([])
    await expect(
      evaluateWindowAsk({ chartId: CHART, asOf: '08/23/2026', exec, forceEnabled: true }),
    ).rejects.toThrow(/ISO yyyy-mm-dd/)
  })
})

describe('readLifecycleCensus / selectAskableWindow — directly, for the lower-level contract', () => {
  it('census is chart-scoped and sums to the row count', async () => {
    const exec = makeExec([
      fakeRow({ id: 'a', lifecycle_status: 'open' }),
      fakeRow({ id: 'b', lifecycle_status: 'window_closed' }),
      fakeRow({ id: 'c', lifecycle_status: 'window_closed' }),
    ])
    const census = await readLifecycleCensus(CHART, exec)
    expect(census).toEqual({ open: 1, window_closed: 2 })
  })

  it('selectAskableWindow returns null, not throw, when nothing qualifies', async () => {
    const exec = makeExec([fakeRow({ lifecycle_status: 'open' })])
    const row = await selectAskableWindow(CHART, '2026-08-23', exec)
    expect(row).toBeNull()
  })
})
