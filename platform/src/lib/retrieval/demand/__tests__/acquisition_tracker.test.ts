/**
 * acquisition_tracker.test.ts — WP-1.6 (P-12) demand-side tracker schema proof.
 *
 * Proves the record round-trips (serialize → parse → serialize is identity),
 * the pure reducers keep the summary in sync, and validateTracker catches the
 * dishonest states (received without evidence, exhausted without a reason).
 */
import { describe, it, expect } from 'vitest'
import {
  createTracker,
  markReceived,
  markExhausted,
  recomputeSummary,
  validateTracker,
  type EvidenceItem,
  type AcquisitionTracker,
} from '../acquisition_tracker'

function sampleItems(): EvidenceItem[] {
  return [
    { item_id: 'e1-bhava-condition', family_key: 'house_sign', label: '7th bhava condition', status: 'needed', candidate_routes: ['marsys://tool/L2/query_signals'] },
    { item_id: 'e2-bhavesha-dignity', family_key: 'dignity_state', label: '7th lord dignity', status: 'needed', candidate_routes: ['marsys://tool/L1/get_dignity'] },
    { item_id: 'e3-karaka', family_key: 'karaka', label: 'Venus (kāraka) condition', status: 'needed', candidate_routes: ['marsys://tool/L1/get_karakas'] },
    { item_id: 'e4-varga', family_key: 'navamsha_sign', label: 'D9 confirmation', status: 'needed', candidate_routes: ['marsys://tool/L1/get_divisionals'] },
  ]
}

describe('WP-1.6 acquisition tracker — round-trip', () => {
  it('serialize → parse → serialize is identity', () => {
    let t = createTracker({ question: 'How is the marriage?', chart_id: '482012f1-710e-4a25-994a-93821f5871aa', domains: ['marriage'], map_version: '1.0.0', items: sampleItems(), planned_at: '2026-07-13T00:00:00.000Z' })
    t = markReceived(t, 'e1-bhava-condition', { via_route: 'marsys://tool/L2/query_signals', provenance: 'planned', arrived_count: 3, reference_ids: ['sig_abc', 'sig_def'] })
    t = markReceived(t, 'e2-bhavesha-dignity', { via_route: 'marsys://tool/L1/get_dignity', provenance: 'volunteered' })
    t = markExhausted(t, 'e4-varga', { reason: 'route_empty', detail: 'no D9 rows for chart', routes_tried: ['marsys://tool/L1/get_divisionals'] })

    const json = JSON.stringify(t)
    const parsed = JSON.parse(json) as AcquisitionTracker
    expect(JSON.stringify(parsed)).toBe(json)
    expect(validateTracker(parsed)).toEqual([])
  })

  it('summary tracks received / needed / exhausted / volunteered / coverage', () => {
    let t = createTracker({ question: 'q', items: sampleItems() })
    expect(t.summary).toMatchObject({ total: 4, needed: 4, received: 0, exhausted: 0, coverage: 0, chase_complete: false })

    t = markReceived(t, 'e1-bhava-condition', { via_route: 'r', provenance: 'planned' })
    t = markReceived(t, 'e3-karaka', { via_route: 'r', provenance: 'volunteered' })
    t = markExhausted(t, 'e4-varga', { reason: 'no_route' })
    expect(t.summary).toMatchObject({ total: 4, needed: 1, received: 2, exhausted: 1, volunteered: 1, coverage: 0.5, chase_complete: false })

    t = markExhausted(t, 'e2-bhavesha-dignity', { reason: 'budget_exhausted' })
    expect(t.summary.chase_complete).toBe(true) // no item still 'needed'
    expect(t.summary.needed).toBe(0)
  })

  it('immutable updates: reducers return a new tracker, original untouched', () => {
    const t0 = createTracker({ question: 'q', items: sampleItems() })
    const t1 = markReceived(t0, 'e1-bhava-condition', { via_route: 'r', provenance: 'planned' })
    expect(t0.summary.received).toBe(0)
    expect(t1.summary.received).toBe(1)
    expect(t1).not.toBe(t0)
  })
})

describe('WP-1.6 acquisition tracker — honesty guards', () => {
  it('flags received status without evidence block', () => {
    const t = createTracker({ question: 'q', items: [{ item_id: 'x', family_key: null, label: 'l', status: 'received', candidate_routes: [] }] })
    expect(validateTracker(t)).toContain('x: received status without received block')
  })

  it('flags exhausted status without a reason', () => {
    const items: EvidenceItem[] = [{ item_id: 'y', family_key: null, label: 'l', status: 'exhausted', candidate_routes: [] }]
    const t: AcquisitionTracker = { schema_version: '1.0', question: 'q', planned_at: 'now', items, summary: recomputeSummary(items) }
    expect(validateTracker(t)).toContain('y: exhausted status without reason')
  })

  it('flags a summary that drifts from the items', () => {
    const items = sampleItems()
    const t: AcquisitionTracker = { schema_version: '1.0', question: 'q', planned_at: 'now', items, summary: { total: 4, needed: 0, received: 4, exhausted: 0, volunteered: 0, coverage: 1, chase_complete: true } }
    expect(validateTracker(t)).toContain('summary out of sync with items')
  })
})
