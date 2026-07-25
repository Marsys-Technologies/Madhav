/**
 * prediction_lifecycle_sweep — unit tests (EL-58, Elevation Campaign v2.1 Lane γ.J)
 * ====================================================================================
 * DB is mocked — no live connection required. matchOpenPredictionsForLelEvent
 * (owned by platform/src/lib/lel/prospective_ledger.ts, out of this lane's
 * manifest) is mocked too — this suite verifies the SWEEP's own logic (candidate
 * detection, dry_run gating, lapsed_unobserved reporting), not that imported
 * function's internals (covered by its own suite).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/lel/prospective_ledger', () => ({
  matchOpenPredictionsForLelEvent: vi.fn(async () => []),
  toleranceDaysFor: (c: string) => (c === 'month_known' ? 75 : 45),
}))

import { query as mockQuery } from '@/lib/db/client'
import { matchOpenPredictionsForLelEvent as mockMatchFn } from '@/lib/lel/prospective_ledger'
import { predictionLifecycleSweepCapability, LAPSED_UNOBSERVED_MIGRATION_SQL } from '../prediction_lifecycle_sweep'

describe('prediction_lifecycle_sweep — descriptor shape', () => {
  it('is per_chart, requires chart_id, lel_capable, NOT calibration_context_only', () => {
    expect(predictionLifecycleSweepCapability.scope).toBe('per_chart')
    expect(predictionLifecycleSweepCapability.required_inputs).toContain('chart_id')
    expect(predictionLifecycleSweepCapability.lel_capable).toBe(true)
    // F-R7's calibration_context_only is for outcome/LEL-READ context-supply tools; this tool
    // performs a lifecycle SWEEP/mutation, not a context read, so it deliberately does not carry it.
    expect(predictionLifecycleSweepCapability.calibration_context_only).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(predictionLifecycleSweepCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })

  it('exports a ready, additive-only migration text naming the new enum value', () => {
    expect(LAPSED_UNOBSERVED_MIGRATION_SQL).toContain('lapsed_unobserved')
    expect(LAPSED_UNOBSERVED_MIGRATION_SQL).toContain('ALTER TABLE')
    expect(LAPSED_UNOBSERVED_MIGRATION_SQL).not.toMatch(/DROP TABLE|TRUNCATE/i)
  })
})

beforeEach(() => {
  vi.mocked(mockMatchFn).mockClear()
})

function mockDb(handlers: Array<{ match: RegExp; rows: unknown[] }>) {
  vi.mocked(mockQuery).mockReset()
  vi.mocked(mockQuery).mockImplementation((async (sql: string) => {
    for (const h of handlers) {
      if (h.match.test(sql)) return { rows: h.rows }
    }
    return { rows: [] }
  }) as never)
}

describe('prediction_lifecycle_sweep — mimamsa_predictions half', () => {
  it('errors when chart_id is absent', async () => {
    const result = await predictionLifecycleSweepCapability.handler({}, {})
    expect(result.is_error).toBe(true)
  })

  it('dry_run default: reports would_write_expired for a lapsed row with no LEL candidate, writes nothing', async () => {
    mockDb([
      { match: /FROM mimamsa_predictions/, rows: [{ prediction_id: 'p1', domain: 'spirituality', eval_date: '2024-01-01', observation_window: '[2022-01-01,2024-01-01)', outcome_claim: 'x' }] },
      { match: /FROM brahma_event_ontology WHERE domain/, rows: [{ domain: 'spirituality', lel_category: 'spiritual' }] },
      { match: /FROM life_events/, rows: [] },
    ])
    const result = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'mimamsa_predictions' }, {})
    expect(result.is_error).toBe(false)
    const content = result.content as { mimamsa_predictions: { dry_run: boolean; expired_written: number; rows: Array<{ disposition: string }> } }
    expect(content.mimamsa_predictions.dry_run).toBe(true)
    expect(content.mimamsa_predictions.expired_written).toBe(0)
    expect(content.mimamsa_predictions.rows[0]!.disposition).toBe('would_write_expired')
    const calls = vi.mocked(mockQuery).mock.calls
    expect(calls.every(c => !/UPDATE/i.test(String(c[0])))).toBe(true)
  })

  it('apply mode writes expired for lapsed rows with no LEL candidate', async () => {
    mockDb([
      { match: /FROM mimamsa_predictions/, rows: [{ prediction_id: 'p1', domain: 'spirituality', eval_date: '2024-01-01', observation_window: '[2022-01-01,2024-01-01)', outcome_claim: 'x' }] },
      { match: /FROM brahma_event_ontology WHERE domain/, rows: [{ domain: 'spirituality', lel_category: 'spiritual' }] },
      { match: /FROM life_events/, rows: [] },
      { match: /UPDATE mimamsa_predictions/, rows: [] },
    ])
    const result = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'mimamsa_predictions', dry_run: false }, {})
    const content = result.content as { mimamsa_predictions: { expired_written: number } }
    expect(content.mimamsa_predictions.expired_written).toBe(1)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(calls.some(c => /UPDATE mimamsa_predictions/i.test(String(c[0])))).toBe(true)
  })

  it('never auto-writes confirmed/denied when a candidate LEL match exists — reports only', async () => {
    mockDb([
      { match: /FROM mimamsa_predictions/, rows: [{ prediction_id: 'p1', domain: 'spirituality', eval_date: '2024-01-01', observation_window: '[2022-01-01,2024-01-01)', outcome_claim: 'x' }] },
      { match: /FROM brahma_event_ontology WHERE domain/, rows: [{ domain: 'spirituality', lel_category: 'spiritual' }] },
      { match: /FROM life_events/, rows: [{ event_id: 'ev1', event_date: '2023-01-01', domain: 'spiritual/foo', shape: 'point', date_confidence: 'exact', interval_start: null, interval_end: null, milestone_label: null }] },
    ])
    const result = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'mimamsa_predictions', dry_run: false }, {})
    const content = result.content as { mimamsa_predictions: { rows: Array<{ disposition: string }>, expired_written: number } }
    expect(content.mimamsa_predictions.rows[0]!.disposition).toBe('candidate_match_found_no_auto_write')
    expect(content.mimamsa_predictions.expired_written).toBe(0)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(calls.every(c => !/UPDATE mimamsa_predictions.*confirmed|denied/i.test(String(c[0])))).toBe(true)
  })
})

describe('prediction_lifecycle_sweep — brahma_prospective_ledger half', () => {
  it('reports lapsed_unobserved_candidate + blocked_pending_migration for a lapsed open row with no LEL candidate (the 2011-class case)', async () => {
    mockDb([
      { match: /FROM brahma_prospective_ledger/, rows: [{ prediction_id: 'pred-2011', event_class: 'major_gain', claim: '2011 window', claim_shape: 'interval', observation_window: `[2011-02-15,2011-03-11)`, milestone_set: null }] },
      { match: /FROM brahma_event_ontology WHERE event_class_id/, rows: [{ event_class_id: 'major_gain', lel_category: 'finance' }] },
      { match: /FROM life_events/, rows: [] },
    ])
    const result = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'brahma_prospective_ledger' }, {})
    expect(result.is_error).toBe(false)
    const content = result.content as { brahma_prospective_ledger: { lapsed_open_count: number; rows: Array<{ disposition: string; blocked_pending_migration?: boolean }> } }
    expect(content.brahma_prospective_ledger.lapsed_open_count).toBe(1)
    const row = content.brahma_prospective_ledger.rows[0]!
    expect(row.disposition).toBe('lapsed_unobserved_candidate')
    expect(row.blocked_pending_migration).toBe(true)
    expect(mockMatchFn).not.toHaveBeenCalled()
  })

  it('does not treat a still-open future-window row (e.g. B-2 Sat-Jupiter Apr-Aug 2027) as lapsed', async () => {
    mockDb([
      { match: /FROM brahma_prospective_ledger/, rows: [{ prediction_id: 'pred-b2', event_class: 'major_gain', claim: 'Sat-Jupiter convergence', claim_shape: 'interval', observation_window: `[2027-04-09,2027-08-19)`, milestone_set: null }] },
    ])
    const result = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'brahma_prospective_ledger' }, {})
    const content = result.content as { brahma_prospective_ledger: { lapsed_open_count: number } }
    expect(content.brahma_prospective_ledger.lapsed_open_count).toBe(0)
  })

  it('apply mode calls the existing matchOpenPredictionsForLelEvent hook (never re-implements the write) when a candidate overlaps', async () => {
    mockDb([
      { match: /FROM brahma_prospective_ledger/, rows: [{ prediction_id: 'pred-x', event_class: 'major_gain', claim: 'x', claim_shape: 'interval', observation_window: `[2011-02-15,2011-03-11)`, milestone_set: null }] },
      { match: /FROM brahma_event_ontology WHERE event_class_id/, rows: [{ event_class_id: 'major_gain', lel_category: 'finance' }] },
      { match: /FROM life_events/, rows: [{ event_id: 'ev-2011', event_date: '2011-02-20', domain: 'finance/windfall', shape: 'point', date_confidence: 'exact', interval_start: null, interval_end: null, milestone_label: null }] },
    ])
    const result = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'brahma_prospective_ledger', dry_run: false }, {})
    const content = result.content as { brahma_prospective_ledger: { matched_applied: number; rows: Array<{ disposition: string }> } }
    expect(mockMatchFn).toHaveBeenCalledTimes(1)
    expect(content.brahma_prospective_ledger.rows[0]!.disposition).toBe('matched_via_existing_hook')
    expect(content.brahma_prospective_ledger.matched_applied).toBe(1)
  })

  it('dry_run default never calls matchOpenPredictionsForLelEvent even with a candidate overlap', async () => {
    mockDb([
      { match: /FROM brahma_prospective_ledger/, rows: [{ prediction_id: 'pred-x', event_class: 'major_gain', claim: 'x', claim_shape: 'interval', observation_window: `[2011-02-15,2011-03-11)`, milestone_set: null }] },
      { match: /FROM brahma_event_ontology WHERE event_class_id/, rows: [{ event_class_id: 'major_gain', lel_category: 'finance' }] },
      { match: /FROM life_events/, rows: [{ event_id: 'ev-2011', event_date: '2011-02-20', domain: 'finance/windfall', shape: 'point', date_confidence: 'exact', interval_start: null, interval_end: null, milestone_label: null }] },
    ])
    await predictionLifecycleSweepCapability.handler({ chart_id: CHART_A, table: 'brahma_prospective_ledger' }, {})
    expect(mockMatchFn).not.toHaveBeenCalled()
  })
})
