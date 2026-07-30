/**
 * kala_ahead_get_recurrence_ladder_w1.test.ts — ṢAḌ-DARŚANA W1 (SHAD_DARSHANA_BRIEF_v2_0.md
 * §3 W1, item 2: "Recurrence-ladder serving (`activation_predicted_dates_jsonb`)").
 *
 * Tests the new kala_ahead_get join field added on top of tools/kala_views/ahead.ts's
 * existing thin facade: recurrence_ladder. A separate file from kala_ahead_get.test.ts /
 * the other kala_ahead_get_*_w1_joins.test.ts files (not an edit to any of them) — this lane
 * shares ahead.ts with several already-merged sibling lanes, and a new file carries far lower
 * merge-conflict risk than editing an existing suite.
 *
 * Production-state note (verified via direct postgres query before writing this join, not
 * assumed): `bodha_msr_signals.activation_predicted_dates_jsonb` — the L2 hook this
 * registry item is literally named after — is genuinely 100% NULL on both canonical charts
 * (0 of 49,608 rows on 482012f1; 0 of 49,980 on 1c826d5a). The populated substrate this join
 * actually reads is `kala_activation.activation_predicted_dates_jsonb` (the L3 `ka_kalasutra`
 * table's OWN same-named column — 323,571 of 332,723 rows non-empty on 482012f1), surfaced
 * via the RAW `activations` array the SAME `query_temporal_activation` capability call
 * already returns (no new registry call, no new migration, no new computation — §N.5/B.10).
 *
 * Contract gates:
 *   ✓ recurrence_ladder collapses per signal_id (duplicate predicate rows sharing a
 *     byte-identical ladder for the same signal keep only the highest-orb_strength row).
 *   ✓ future_points excludes points before today (AHEAD is forward-looking) — never
 *     fabricates a forward point when the whole ladder is historical.
 *   ✓ total_points_in_ladder discloses the full ladder size even when only the future half
 *     is served in future_points (honest partial disclosure, not a silent truncation).
 *   ✓ coverage: computed when at least one signal has a future point; honest_empty
 *     (distinguishing "ladder exists but fully past" from "no ladder anywhere") otherwise.
 *   ✓ unreachable L3 registry → honest_empty, never fabricated.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const DAY_MS = 86400000
const today = new Date()
const iso = (deltaDays: number) => new Date(today.getTime() + deltaDays * DAY_MS).toISOString().slice(0, 10)

// A ladder spanning past + future recurrences, matching the design doc's own example shape
// (KALA_SIX_VIEWS_DESIGN_v1_0.md §2.2: "Saturn-AD re-fires 2032-33, 2047-50...").
const SATURN_LADDER = [
  { date: iso(-3650), graha: 'Saturn', level: 2, source: 'dasha_timeline', trigger: 'unclassified', strength: 0.6, point_kind: 'period_start' },
  { date: iso(-3600), graha: 'Saturn', level: 2, source: 'dasha_timeline', trigger: 'unclassified', strength: 1, point_kind: 'period_peak' },
  { date: iso(90), graha: 'Saturn', level: 2, source: 'dasha_timeline', trigger: 'unclassified', strength: 0.6, point_kind: 'period_start' },
  { date: iso(120), graha: 'Saturn', level: 2, source: 'dasha_timeline', trigger: 'unclassified', strength: 1, point_kind: 'period_peak' },
  { date: iso(4000), graha: 'Saturn', level: 2, source: 'dasha_timeline', trigger: 'unclassified', strength: 0.6, point_kind: 'period_start' },
]

// A convergence-path ladder (the OTHER writer shape — {date, strength, trigger} only,
// no graha/point_kind) — entirely historical, so it must yield zero future_points.
const HISTORICAL_ONLY_LADDER = [
  { date: iso(-10), strength: 1, trigger: 'transit_conjunction' },
  { date: iso(-3), strength: 0.4, trigger: 'transit_conjunction' },
]

function activationRow(overrides: Record<string, unknown>) {
  return {
    id: 'act-1',
    signal_id: 'sig-saturn-ad',
    ayanamsha_id: 'lahiri_chitrapaksha',
    signature_class: 'CLASSIFY_RESIDUAL',
    orb_strength: 1,
    domains_affected_array: ['career'],
    source_citation: 'ka_kalasutra:v1.0:signal=sig-saturn-ad:src=dasha_timeline:period=2',
    activation_predicted_dates_jsonb: SATURN_LADDER,
    ...overrides,
  }
}

function mockRegistryFetch(opts: { reachable: boolean; activations?: Array<Record<string, unknown>> }) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = {
        window_families: [],
        forward_windows: [],
        activations: opts.activations ?? [activationRow({})],
      }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projection_families: [] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      inner = { systems: [] }
    } else if (body.uri === 'marsys://tool/L0/query_planet_transit') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L1/get_tajik') {
      inner = { varsha_year_lords: { rows: [] } }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      inner = { panchangs: [] }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('kala_ahead_get W1 join — recurrence_ladder (item 2)', () => {
  it('serves only the FUTURE points of the ladder, sorted ascending', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder).toHaveLength(1)
    const entry = result.recurrence_ladder[0]!
    expect(entry.signal_id).toBe('sig-saturn-ad')
    expect(entry.future_points.map((p) => p.date)).toEqual([iso(90), iso(120), iso(4000)])
    expect(entry.future_points[0]!.point_kind).toBe('period_start')
    expect(entry.future_points[0]!.strength).toBe(0.6)
  })

  it('discloses total_points_in_ladder including the past points not surfaced in future_points', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const entry = result.recurrence_ladder[0]!
    expect(entry.total_points_in_ladder).toBe(SATURN_LADDER.length)
    expect(entry.future_points.length).toBeLessThan(entry.total_points_in_ladder)
  })

  it('domains_affected and signature_class trace verbatim to the raw activation row', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const entry = result.recurrence_ladder[0]!
    expect(entry.domains_affected).toEqual(['career'])
    expect(entry.signature_class).toBe('CLASSIFY_RESIDUAL')
    expect(entry.source_citation).toBe('ka_kalasutra:v1.0:signal=sig-saturn-ad:src=dasha_timeline:period=2')
  })

  it('collapses duplicate predicate rows for the SAME signal, keeping the highest orb_strength', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch({
        reachable: true,
        activations: [
          activationRow({ source_citation: 'period=0', orb_strength: 0.3 }),
          activationRow({ source_citation: 'period=2', orb_strength: 1 }),
          activationRow({ source_citation: 'period=1', orb_strength: 0.6 }),
        ],
      }),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder).toHaveLength(1)
    expect(result.recurrence_ladder[0]!.source_citation).toBe('period=2')
    expect(result.recurrence_ladder[0]!.max_orb_strength).toBe(1)
  })

  it('coverage marks recurrence_ladder computed when a future point exists', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['recurrence_ladder']?.state).toBe('computed')
  })

  it('honest_empty (never fabricated) when the ladder exists but is entirely historical', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch({
        reachable: true,
        activations: [activationRow({ signal_id: 'sig-historical', activation_predicted_dates_jsonb: HISTORICAL_ONLY_LADDER })],
      }),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder).toEqual([])
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['recurrence_ladder']?.state).toBe('honest_empty')
    expect(byConcept['recurrence_ladder']?.reason).toContain('past')
  })

  it('honest_empty when no activation row carries a populated ladder at all', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, activations: [activationRow({ activation_predicted_dates_jsonb: null })] }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder).toEqual([])
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['recurrence_ladder']?.state).toBe('honest_empty')
    expect(byConcept['recurrence_ladder']?.reason).toContain('bodha_msr_signals')
  })

  it('honest_empty when the L3 registry is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder).toEqual([])
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['recurrence_ladder']?.state).toBe('honest_empty')
    expect(byConcept['recurrence_ladder']?.reason?.length).toBeGreaterThan(0)
  })

  it('provenance_envelope.recurrence_ladder_reachable mirrors windows_reachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.provenance_envelope.recurrence_ladder_reachable).toBe(true)
    expect(result.provenance_envelope.recurrence_ladder_reachable).toBe(result.provenance_envelope.windows_reachable)
  })
})
