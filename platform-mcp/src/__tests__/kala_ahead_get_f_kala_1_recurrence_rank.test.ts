/**
 * kala_ahead_get_f_kala_1_recurrence_rank.test.ts — F-KALA-1
 * (L3_W1_ANALYSIS_BATCH_E.md, ka_kalasutra finding 1), third call site.
 *
 * THE DEFECT: `computeRecurrenceLadder`'s per-signal collapse (ahead.ts) kept the row with
 * `(existing.max_orb_strength ?? -Infinity) >= (orb ?? -Infinity)`. `orb_strength` is 99.6%
 * NULL (measured) — `ka_sangam` only produces windows for ≤260 of ~50,104 activation
 * predicates — so once both sides default to `-Infinity`, the comparison is ALWAYS true and
 * the loop's "first row wins" became the undocumented actual rule for 99.6% of signals.
 *
 * THE FIX: rank by `dasha_activation_proximity_score` (0% NULL measured, higher = stronger)
 * first, `orb_strength` as a secondary tiebreak, `id` as the final total-order tiebreak —
 * same semantics as the sibling fixes to `register_d9_judgment.ts` and
 * `query_temporal_activation.ts` earlier this session.
 *
 * A separate file from `kala_ahead_get_recurrence_ladder_w1.test.ts` (not an edit to it) —
 * lower merge-conflict risk, matching that file's own stated convention for this shared area
 * of ahead.ts.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const DAY_MS = 86400000
const today = new Date()
const iso = (deltaDays: number) => new Date(today.getTime() + deltaDays * DAY_MS).toISOString().slice(0, 10)

const LADDER = [
  { date: iso(90), graha: 'Saturn', trigger: 'unclassified', strength: 0.6, point_kind: 'period_start' },
]

function activationRow(overrides: Record<string, unknown>) {
  return {
    id: 'act-1',
    signal_id: 'sig-saturn-ad',
    ayanamsha_id: 'lahiri_chitrapaksha',
    signature_class: 'CLASSIFY_RESIDUAL',
    orb_strength: null,
    dasha_activation_proximity_score: null,
    domains_affected_array: ['career'],
    source_citation: 'default',
    activation_predicted_dates_jsonb: LADDER,
    ...overrides,
  }
}

function mockRegistryFetch(activations: Array<Record<string, unknown>>) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [], activations }
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

describe('F-KALA-1 — kala_ahead_get recurrence_ladder ranks by dasha_activation_proximity_score first', () => {
  it('the 99.6%-NULL scenario: orb_strength ties at NULL, proximity score decides the winner', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch([
        activationRow({ source_citation: 'low', dasha_activation_proximity_score: 0.2 }),
        activationRow({ source_citation: 'high', dasha_activation_proximity_score: 0.9 }),
        activationRow({ source_citation: 'mid', dasha_activation_proximity_score: 0.5 }),
      ]),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder).toHaveLength(1)
    // Before the fix, whichever row was processed FIRST ('low') would have silently won —
    // the array order above is deliberately NOT sorted by proximity, to prove the ranking
    // logic itself decides this, not row order.
    expect(result.recurrence_ladder[0]!.source_citation).toBe('high')
  })

  it('falls back to orb_strength as a secondary tiebreak when proximity scores tie', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch([
        activationRow({ source_citation: 'weak-orb', dasha_activation_proximity_score: 0.5, orb_strength: 0.2 }),
        activationRow({ source_citation: 'strong-orb', dasha_activation_proximity_score: 0.5, orb_strength: 0.9 }),
      ]),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder[0]!.source_citation).toBe('strong-orb')
    expect(result.recurrence_ladder[0]!.max_orb_strength).toBe(0.9)
  })

  it('a real proximity score always outranks a NULL one, even against a high orb_strength on the NULL side', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch([
        activationRow({ source_citation: 'null-proximity-high-orb', dasha_activation_proximity_score: null, orb_strength: 0.99 }),
        activationRow({ source_citation: 'low-proximity', dasha_activation_proximity_score: 0.01, orb_strength: null }),
      ]),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.recurrence_ladder[0]!.source_citation).toBe('low-proximity')
  })
})
