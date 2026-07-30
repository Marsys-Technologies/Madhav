/**
 * kala_now_get_w1_joins.test.ts — ṢAḌ-DARŚANA W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1,
 * items 32 + 29).
 *
 * Tests the four new kala_now_get join fields added on top of tools/kala_views/now.ts's
 * existing thin facade: disha_shula, gulika_kalam_now, chandrashtama, hora_now,
 * janma_resonance. A separate file from kala_now_get.test.ts (not an edit to it) — this
 * lane shares now.ts with several already-merged/in-flight sibling lanes, and a new file
 * carries far lower merge-conflict risk than editing the existing suite.
 *
 * Mirrors kala_now_get.test.ts's mock-fetch pattern: the double-wrapped
 * `{ ok, content: { content, is_error } }` contract dispatched by URI.
 *
 * Contract gates:
 *   ✓ Gate W1 objectivity (SHAD_DARSHANA_BRIEF_v2_0.md §3): every new field is a raw
 *     fact/flag — no favorable/unfavorable grading anywhere in these assertions.
 *   ✓ Gate W1 acceptance: new fields present-and-non-empty when the join sources resolve,
 *     honest-empty (via `coverage`) when they don't — never fabricated.
 *   ✓ §N.5: janma_resonance birth_id/birth_fact_id trace verbatim to the L1 chart_facts
 *     rows the mock returns — never re-derived.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaNow } from '../tools/kala_views/now.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const NOW = Date.now()
const ISO = (ms: number) => new Date(ms).toISOString()

// A wide-margin "now" window (±2h) so is_active_now/hora_now resolve deterministically
// regardless of how long the test takes to run.
const GULIKA_ACTIVE = { label: 'gulika_kalam', start_utc: ISO(NOW - 2 * 3600_000), end_utc: ISO(NOW + 2 * 3600_000) }
const GULIKA_PAST = { label: 'gulika_kalam', start_utc: ISO(NOW - 4 * 3600_000), end_utc: ISO(NOW - 2 * 3600_000) }

const HORA_LIST = [
  { label: 'hora_saturn', start_utc: ISO(NOW - 4 * 3600_000), end_utc: ISO(NOW - 2 * 3600_000) },
  { label: 'hora_mars', start_utc: ISO(NOW - 2 * 3600_000), end_utc: ISO(NOW + 2 * 3600_000) },
  { label: 'hora_sun', start_utc: ISO(NOW + 2 * 3600_000), end_utc: ISO(NOW + 4 * 3600_000) },
]

function panchangPayload(opts: { gulika?: typeof GULIKA_ACTIVE | null; varaId?: number; moonSignId?: number; nativeMoonSignId?: number }) {
  const varaId = opts.varaId ?? 1
  return {
    tithi: { id: 5, name: 'Krishna Panchami', end_utc: null },
    nakshatra: { id: 25, name: 'Purva Bhadrapada', end_utc: null },
    vara: { id: varaId, name: varaId === 1 ? 'Ravivara' : 'Somavara', end_utc: null },
    inauspicious: opts.gulika === null ? [] : [opts.gulika ?? GULIKA_ACTIVE],
    hora: HORA_LIST,
    planets: { moon: { name: 'Moon', sign_id: opts.moonSignId ?? 8, sign_name: 'Scorpio', nakshatra_id: 25, nakshatra_name: 'Purva Bhadrapada' } },
  }
}

const NATIVE_CONTEXT = { chart_id: TEST_CHART_ID, moon_sign_id: 1, moon_sign_name: 'Aries', birth_nakshatra_id: 25, birth_nakshatra_name: 'Purva Bhadrapada' }

const NATAL_ROWS = [
  { fact_id: 'fact-vara-1', fact_category: 'panchanga_vara', ayanamsha_id: 'INVARIANT', fact_key: 'number', fact_value_num: 1, fact_value_text: null },
  { fact_id: 'fact-vara-name', fact_category: 'panchanga_vara', ayanamsha_id: 'INVARIANT', fact_key: 'name', fact_value_num: null, fact_value_text: 'Ravivara' },
  { fact_id: 'fact-tithi-1', fact_category: 'panchanga_tithi', ayanamsha_id: 'INVARIANT', fact_key: 'number_in_lunar_month', fact_value_num: 3, fact_value_text: null },
  { fact_id: 'fact-tithi-name', fact_category: 'panchanga_tithi', ayanamsha_id: 'INVARIANT', fact_key: 'name', fact_value_num: null, fact_value_text: 'Shukla Tritiya' },
  { fact_id: 'fact-nak-1', fact_category: 'panchanga_nakshatra_moon', ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'number', fact_value_num: 25, fact_value_text: null },
  { fact_id: 'fact-nak-name', fact_category: 'panchanga_nakshatra_moon', ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'name', fact_value_num: null, fact_value_text: 'Purva Bhadrapada' },
]

function mockRegistryFetch(opts: {
  reachable: boolean
  panchangaReachable?: boolean
  natalReachable?: boolean
  panchang?: ReturnType<typeof panchangPayload>
  nativeContext?: typeof NATIVE_CONTEXT | null
  natalRows?: typeof NATAL_ROWS
}) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_temporal_view') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      if (opts.panchangaReachable === false) throw new Error('panchanga service unreachable in test')
      inner = { panchang: opts.panchang ?? panchangPayload({}), native_context: opts.nativeContext === undefined ? NATIVE_CONTEXT : opts.nativeContext }
    } else if (body.uri === 'marsys://tool/L1/get_panchanga') {
      if (opts.natalReachable === false) throw new Error('L1 get_panchanga unreachable in test')
      inner = { rows: opts.natalRows ?? NATAL_ROWS }
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

describe('kala_now_get W1 join — disha_shula (item 32)', () => {
  it('resolves the diśā-śūla direction from today\'s vara_id via the classical table', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ varaId: 1 }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.disha_shula).toEqual({
      vara_id: 1,
      vara_name: 'Ravivara',
      avoid_direction: 'West',
      source_citation: expect.stringContaining('Diśā-śūla'),
    })
  })

  it('different vara_id resolves a different direction (2 → East, per DISHA_SHUL_TABLE)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ varaId: 2 }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.disha_shula?.avoid_direction).toBe('East')
  })
})

describe('kala_now_get W1 join — gulika_kalam_now (item 32)', () => {
  it('is_active_now=true when the current moment falls inside the window', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ gulika: GULIKA_ACTIVE }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.gulika_kalam_now?.is_active_now).toBe(true)
    expect(result.gulika_kalam_now?.window_start_utc).toBe(GULIKA_ACTIVE.start_utc)
  })

  it('is_active_now=false when the window has already passed', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ gulika: GULIKA_PAST }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.gulika_kalam_now?.is_active_now).toBe(false)
  })

  it('is_active_now=null with a stated reason when as_of is not the real current date', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ gulika: GULIKA_ACTIVE }) }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2020-01-01' }, TEST_PRINCIPAL)
    expect(result.gulika_kalam_now?.is_active_now).toBeNull()
    expect(result.gulika_kalam_now?.not_meaningful_reason?.length).toBeGreaterThan(0)
  })
})

describe('kala_now_get W1 join — hora_now (item 29)', () => {
  it('resolves the current planetary-hour lord from the hora label', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.hora_now?.hora_lord).toBe('Mars')
    expect(result.hora_now?.window_start_utc).toBe(HORA_LIST[1]?.start_utc)
  })
})

describe('kala_now_get W1 join — chandrashtama (item 29)', () => {
  it('is_chandrashtama=true when transit Moon is house 8 from natal Moon', async () => {
    // native Moon sign_id=1 (Aries), transit Moon sign_id=8 (Scorpio) → house 8
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ moonSignId: 8 }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    // ṢAḌ-DARŚANA W1 verify-reopen (§N.5): chandrāṣṭama now takes the natal Moon rāśi from
    // L1 `chart_facts` when available, and DISCLOSES which authority it used. This mock does
    // not stub `get_dignity`, so the L1 fact is absent and the documented fallback to the
    // panchāṅga service's own re-derivation applies — asserted explicitly here rather than
    // left implicit, because "which authority produced this number" is exactly the question
    // §N.5 exists to make answerable.
    expect(result.chandrashtama).toEqual({
      is_chandrashtama: true,
      house_from_natal_moon: 8,
      natal_moon_sign_id: 1,
      transit_moon_sign_id: 8,
      natal_moon_sign_source: 'panchanga_native_context',
      natal_moon_sign_fact_id: null,
      native_context_agrees_with_l1: null,
    })
  })

  it('is_chandrashtama=false when transit Moon is in the natal Moon sign (house 1)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ moonSignId: 1 }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.chandrashtama?.is_chandrashtama).toBe(false)
    expect(result.chandrashtama?.house_from_natal_moon).toBe(1)
  })

  it('honest_empty when native_context could not be resolved', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, nativeContext: null }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.chandrashtama).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['chandrashtama']?.state).toBe('honest_empty')
  })
})

describe('kala_now_get W1 join — janma_resonance (item 29c; definition found in corpus, not invented)', () => {
  it('flags vara/nakshatra resonance true and tithi resonance false, tracing to L1 fact_ids', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchang: panchangPayload({ varaId: 1 }) }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.janma_resonance?.vara).toEqual({
      today_id: 1, today_name: 'Ravivara', birth_id: 1, birth_name: 'Ravivara',
      birth_fact_id: 'fact-vara-1', resonance: true,
    })
    expect(result.janma_resonance?.nakshatra.resonance).toBe(true)
    expect(result.janma_resonance?.nakshatra.birth_fact_id).toBe('fact-nak-1')
    // panchangPayload's tithi.id is 5; NATAL_ROWS birth tithi is 3 → no resonance
    expect(result.janma_resonance?.tithi.resonance).toBe(false)
    expect(result.janma_resonance?.tithi.today_id).toBe(5)
    expect(result.janma_resonance?.tithi.birth_id).toBe(3)
  })

  it('honest_empty when L1 natal panchanga facts are unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, natalReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.janma_resonance).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['janma_resonance']?.state).toBe('honest_empty')
    expect(byConcept['janma_resonance']?.reason?.length).toBeGreaterThan(0)
  })
})

describe('kala_now_get W1 joins — honest-empty on unreachable panchāṅga service (Gate W1 coverage)', () => {
  it('all five new fields are null and coverage marks each honest_empty, never fabricated', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchangaReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.disha_shula).toBeNull()
    expect(result.gulika_kalam_now).toBeNull()
    expect(result.chandrashtama).toBeNull()
    expect(result.hora_now).toBeNull()
    expect(result.janma_resonance).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    for (const key of ['disha_shula', 'gulika_kalam_now', 'chandrashtama', 'hora_now', 'janma_resonance']) {
      expect(byConcept[key]?.state).toBe('honest_empty')
      expect(byConcept[key]?.reason?.length).toBeGreaterThan(0)
    }
  })
})
