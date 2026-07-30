/**
 * kala_ahead_get_digest_90d_w1.test.ts — ṢAḌ-DARŚANA W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1,
 * "E6-lite: proactive 90-day digest preset on AHEAD (D4)").
 *
 * Tests the new kala_ahead_get field added on top of tools/kala_views/ahead.ts's existing
 * thin facade: digest_90d. A separate file from kala_ahead_get.test.ts / the other
 * kala_ahead_get_*_w1_joins.test.ts files (not an edit to any of them) — new file, lower
 * merge-conflict risk, per this lane's established convention.
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §2.3 ("Horizon presets: 90d / 1y / 5y /
 * daśā-span, family-collapsed, never 25 photocopies"). The digest is a pure SELECTION over
 * fields kala_ahead_get already computes (windows, projections, gulika_kalam_ahead,
 * recurrence_ladder, mudda_dasha_varsha), bounded to [today, today+90d] — no new computation,
 * no new registry call.
 *
 * Contract gates:
 *   ✓ items bounded to the fixed 90-day forward window (an item entirely outside it is
 *     excluded, never silently included).
 *   ✓ the daily gulika-kālam surface collapses to ONE summary item, not one per day.
 *   ✓ ritual_opportunities_note is present and explicitly explains the W1 ritual-free state
 *     (Gate W1: "ritual rows are NOT expected here — Mode 1 arrives at W4").
 *   ✓ coverage: computed when item_count > 0; honest_empty (never silently absent) when
 *     every underlying surface is empty/unreachable.
 *   ✓ item_count always equals items.length.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const DAY_MS = 86400000
const today = new Date()
const iso = (deltaDays: number) => new Date(today.getTime() + deltaDays * DAY_MS).toISOString().slice(0, 10)

const WINDOW_FAMILY_IN_90D = {
  window_start: iso(10),
  window_end: iso(20),
  window_peak: iso(15),
  member_count: 2,
  member_signal_ids: ['sig-a', 'sig-b'],
  signature_classes: ['dasha_ingress'],
  domains: ['career'],
  max_orb_strength: 0.7,
}

const WINDOW_FAMILY_BEYOND_90D = {
  window_start: iso(200),
  window_end: iso(220),
  window_peak: iso(210),
  member_count: 1,
  member_signal_ids: ['sig-far'],
  signature_classes: ['dasha_ingress'],
  domains: ['health'],
  max_orb_strength: 0.4,
}

const PROJECTION_IN_90D = {
  window_start: iso(30),
  window_end: iso(60),
  domain: 'wealth',
  member_count: 3,
  member_ids: ['proj-1'],
  member_signal_ids: ['sig-c'],
  probability_tier: 'tier_1_high' as const,
}

const PROJECTION_BEYOND_90D = {
  window_start: iso(400),
  window_end: iso(430),
  domain: 'relationship',
  member_count: 1,
  member_ids: ['proj-far'],
  member_signal_ids: [],
  probability_tier: 'tier_2_moderate' as const,
}

const GULIKA_DAYS = [
  { date: iso(1), inauspicious: [{ label: 'gulika_kalam', start_utc: `${iso(1)}T06:00:00Z`, end_utc: `${iso(1)}T07:30:00Z` }] },
  { date: iso(2), inauspicious: [{ label: 'gulika_kalam', start_utc: `${iso(2)}T06:00:00Z`, end_utc: `${iso(2)}T07:30:00Z` }] },
]

const RECURRENCE_LADDER_IN_90D_ROW = {
  id: 'act-1',
  signal_id: 'sig-recur-near',
  signature_class: 'CLASSIFY_RESIDUAL',
  orb_strength: 1,
  domains_affected_array: ['career'],
  source_citation: 'ka_kalasutra:v1.0:signal=sig-recur-near',
  activation_predicted_dates_jsonb: [{ date: iso(45), strength: 0.8, trigger: 'unclassified', point_kind: 'period_peak', graha: 'Saturn' }],
}

const RECURRENCE_LADDER_BEYOND_90D_ROW = {
  id: 'act-2',
  signal_id: 'sig-recur-far',
  signature_class: 'CLASSIFY_RESIDUAL',
  orb_strength: 1,
  domains_affected_array: ['health'],
  source_citation: 'ka_kalasutra:v1.0:signal=sig-recur-far',
  activation_predicted_dates_jsonb: [{ date: iso(500), strength: 0.8, trigger: 'unclassified', point_kind: 'period_peak', graha: 'Jupiter' }],
}

const VARSHA_ROW = {
  varsha_year: 42,
  varsha_start_iso: iso(-100),
  varsha_end_iso: iso(265),
  year_lord: 'Saturn',
  // ṢAḌ-DARŚANA W1 verify-reopen (item 30, Root Cause C): the Muntha is stored as the JSONB
  // column `muntha_position_jsonb`, NOT as flat `muntha_sign` / `muntha_house` columns. This
  // mock previously asserted the flat shape — a shape no writer has ever emitted — which is
  // exactly why the all-null-muntha defect passed CI while failing on every real chart. Shape
  // below copied verbatim from a live `ganita_tajaka_get` response
  // (l1_tajik_varsha_year_lords.muntha_position_jsonb), not invented.
  muntha_position_jsonb: {
    lord: 'Jupiter',
    sign: 'Aquarius',
    degree: 12.4311,
    house_from_natal_lagna: 11,
    house_from_varsha_lagna: 3,
  },
}

const MUDDA_CHAIN = [{ level_n: 1, level_name: 'Mahadasha', lord_graha: 'Saturn', lord_sign: 'Aquarius', start_date: iso(-10), end_date: iso(300) }]

function mockRegistryFetch(opts: {
  reachable: boolean
  windowFamilies?: Array<Record<string, unknown>>
  projectionFamilies?: Array<Record<string, unknown>>
  gulikaDays?: typeof GULIKA_DAYS
  activations?: Array<Record<string, unknown>>
  varshaRows?: Array<Record<string, unknown>>
  muddaChain?: typeof MUDDA_CHAIN
}) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = {
        window_families: opts.windowFamilies ?? [],
        forward_windows: [],
        activations: opts.activations ?? [],
      }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projection_families: opts.projectionFamilies ?? [] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      inner = { systems: [{ system_id: 'mudda', active_chain: opts.muddaChain ?? [] }] }
    } else if (body.uri === 'marsys://tool/L0/query_planet_transit') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L1/get_tajik') {
      inner = { varsha_year_lords: { rows: opts.varshaRows ?? [] } }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      inner = { panchangs: opts.gulikaDays ?? [] }
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

describe('kala_ahead_get E6-lite — digest_90d', () => {
  it('includes items overlapping the next 90 days and excludes items entirely beyond it', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch({
        reachable: true,
        windowFamilies: [WINDOW_FAMILY_IN_90D, WINDOW_FAMILY_BEYOND_90D],
        projectionFamilies: [PROJECTION_IN_90D, PROJECTION_BEYOND_90D],
      }),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const kinds = result.digest_90d.items.map((i) => `${i.kind}:${i.window_or_date}`)
    expect(kinds).toContain(`temporal_window:${WINDOW_FAMILY_IN_90D.window_start}..${WINDOW_FAMILY_IN_90D.window_end}`)
    expect(kinds).toContain(`probabilistic_projection:${PROJECTION_IN_90D.window_start}..${PROJECTION_IN_90D.window_end}`)
    expect(kinds.some((k) => k.includes(WINDOW_FAMILY_BEYOND_90D.window_start))).toBe(false)
    expect(kinds.some((k) => k.includes(PROJECTION_BEYOND_90D.window_start))).toBe(false)
  })

  it('collapses the daily gulika-kālam surface to ONE summary item, not one per day', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, gulikaDays: GULIKA_DAYS }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const gulikaItems = result.digest_90d.items.filter((i) => i.kind === 'gulika_kalam')
    expect(gulikaItems).toHaveLength(1)
    expect(gulikaItems[0]!.detail).toContain(String(GULIKA_DAYS.length))
  })

  it('includes a recurrence-ladder item only when its next occurrence falls within 90 days', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch({
        reachable: true,
        activations: [RECURRENCE_LADDER_IN_90D_ROW, RECURRENCE_LADDER_BEYOND_90D_ROW],
      }),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const recurItems = result.digest_90d.items.filter((i) => i.kind === 'recurrence_ladder_point')
    expect(recurItems).toHaveLength(1)
    expect(recurItems[0]!.fact_ids).toEqual(['sig-recur-near'])
    // the far-future recurrence is still visible on the full (non-digest) field, never dropped
    expect(result.recurrence_ladder.map((e) => e.signal_id).sort()).toEqual(['sig-recur-far', 'sig-recur-near'])
  })

  it('includes ONE mudda_dasha_varsha item when the join resolves', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, varshaRows: [VARSHA_ROW], muddaChain: MUDDA_CHAIN }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const muddaItems = result.digest_90d.items.filter((i) => i.kind === 'mudda_dasha_varsha')
    expect(muddaItems).toHaveLength(1)
    expect(muddaItems[0]!.detail).toContain('Saturn')
  })

  it('ritual_opportunities_note explicitly names the W1 ritual-free state (Gate W1 requirement)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.digest_90d.ritual_opportunities_note).toContain('W4')
    expect(result.digest_90d.ritual_opportunities_note.toLowerCase()).toContain('ritual')
  })

  it('as_of_date / digest_to_date bound a 90-day span and horizon_days is 90', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.digest_90d.horizon_days).toBe(90)
    const spanDays = Math.round(
      (new Date(result.digest_90d.digest_to_date).getTime() - new Date(result.digest_90d.as_of_date).getTime()) / DAY_MS,
    )
    expect(spanDays).toBe(90)
  })

  it('item_count always equals items.length', async () => {
    vi.stubGlobal(
      'fetch',
      mockRegistryFetch({
        reachable: true,
        windowFamilies: [WINDOW_FAMILY_IN_90D],
        projectionFamilies: [PROJECTION_IN_90D],
        gulikaDays: GULIKA_DAYS,
        activations: [RECURRENCE_LADDER_IN_90D_ROW],
        varshaRows: [VARSHA_ROW],
        muddaChain: MUDDA_CHAIN,
      }),
    )
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.digest_90d.item_count).toBe(result.digest_90d.items.length)
    expect(result.digest_90d.item_count).toBeGreaterThan(0)
  })

  it('coverage marks ahead_digest_90d computed when at least one item is present', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, gulikaDays: GULIKA_DAYS }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['ahead_digest_90d']?.state).toBe('computed')
  })

  it('honest_empty (never fabricated) when nothing computed falls inside the 90-day window', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.digest_90d.items).toEqual([])
    expect(result.digest_90d.item_count).toBe(0)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['ahead_digest_90d']?.state).toBe('honest_empty')
    expect(byConcept['ahead_digest_90d']?.reason?.length).toBeGreaterThan(0)
  })
})
