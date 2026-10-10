/**
 * reading_checklist.near_miss.test.ts -- the NMB-CAND-v1 formation-band reader (packet v1.2).
 *
 * v1.2 removed `near_miss`: the route serves present / absent / indeterminate only and this reader
 * never emits a formation-gap finding. `fetchNotablyAbsentYogas` is fenced to the served generation
 * of ga_yoga + ga_positions, calls the sidecar route, and turns anything unproven into
 * `source_unproven` (never an empty finding, never `not_computed`). `interpretYogaBandResponse` is
 * the pure interpreter.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { chartServedGenerationFromRows } from '../../generation/served_generation'
import {
  NEAR_MISS_CANDIDATE_IDS,
  NEAR_MISS_CANONICAL_AYANAMSHAS,
  NEAR_MISS_REQUIRED_ASSETS,
  NEAR_MISS_ROUTE_CACHE_MAX_ENTRIES,
  NEAR_MISS_ROUTE_CACHE_TTL_MS,
  checklistExhaustiveness,
  fetchNotablyAbsentYogas,
  interpretYogaBandResponse,
  resetYogaBandRouteStateForTests,
  type ChecklistUnit,
} from '../reading_checklist'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'
const B_POS = '11111111-1111-4111-8111-111111111111'
const B_YOGA = '22222222-2222-4222-8222-222222222222'
const EXPECT = { chart_id: CHART, ayanamsha_id: AYA, served_build_ids: [B_POS, B_YOGA] }

function generation(unresolved: string[] = []) {
  const builds: Record<string, string> = { ga_positions: B_POS, ga_yoga: B_YOGA }
  return chartServedGenerationFromRows(CHART, [...NEAR_MISS_REQUIRED_ASSETS], NEAR_MISS_REQUIRED_ASSETS.map(asset_id => ({
    asset_id, partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: builds[asset_id]!, rows_build_id: builds[asset_id]!,
    receipt_state: 'proven', freshness_state: unresolved.includes(asset_id) ? 'stale' : 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64), spec_active: true, receipt_run_state: 'completed',
    receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
  })))
}

function cand(id: string, state: string, extra: Record<string, unknown> = {}) {
  return {
    candidate_id: id, yoga_name: `Yoga ${id}`, formation_text: `Lords associate (${id}).`, state, reason: null,
    pairs: [], l1_firing_ids: [], constituent_fact_ids: [], contradicting_present_siblings: [], overlaps: [] as string[], ...extra,
  }
}
function response(over: Record<string, unknown> = {}, states: Record<string, string> = {}, ayanamsha = AYA) {
  return {
    band_version: 'NMB-BAND-v1', candidate_set_version: 'NMB-CAND-v1', eligibility_rule_version: 'NMB-ELIG-v1',
    tolerance: 'none', chart_id: CHART, ayanamsha_id: ayanamsha, served_build_ids: [B_POS, B_YOGA],
    candidates: NEAR_MISS_CANDIDATE_IDS.map(id => cand(id, states[id] ?? 'absent', { constituent_fact_ids: [`f-${id}`] })),
    ...over,
  }
}

function fenceRows(ok = true, replacement: string[] = []) {
  return { rows: NEAR_MISS_REQUIRED_ASSETS.map(asset_id => ({
    asset_id, receipt_matches_selected_build: ok, replacement_in_progress: replacement.includes(asset_id),
  })) }
}

const fetchMock = vi.fn()
beforeEach(() => {
  queryMock.mockReset()
  fetchMock.mockReset()
  resetYogaBandRouteStateForTests()
  vi.stubGlobal('fetch', fetchMock)
  process.env['PYTHON_SIDECAR_URL'] = 'http://sidecar.test/'
  process.env['PYTHON_SIDECAR_API_KEY'] = 'k-1'
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
  vi.restoreAllMocks()
  delete process.env['PYTHON_SIDECAR_URL']
  delete process.env['PYTHON_SIDECAR_API_KEY']
})

const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body })

describe('interpretYogaBandResponse (packet v1.2: no near_miss)', () => {
  it('serves an empty notably_absent_yogas array, counts present/absent/indeterminate, near_miss is always 0', () => {
    const r = interpretYogaBandResponse(response({}, { dhana_yoga_2_11: 'present', dhana_yoga_5_9: 'absent' }), EXPECT)
    expect(r.state).toBe('empty_for_this_chart')
    expect(r.notably_absent_yogas).toEqual([])
    expect(r.band_coverage).toEqual({ present: 1, near_miss: 0, absent: 5, indeterminate: 0, total: 6 })
    expect(r.near_miss_capable_candidates).toBe(0)
    expect(r.formation_gap_detection).toBe('not_claimed')
    expect(r.note).toMatch(/formation-gap detection is not claimed/i)
    expect(r.state).not.toBe('not_computed')
    expect(r.fact_ids).toContain('f-dhana_yoga_2_11')
  })

  it('a route row in state near_miss is invalid (the route never emits it): source_unproven', () => {
    const bad = response({}, { dhana_yoga_house_lords: 'near_miss' })
    const r = interpretYogaBandResponse(bad, EXPECT)
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe('band_row_invalid')
    expect(r.notably_absent_yogas).toEqual([])
  })

  it('carries per-candidate statuses with overlaps, the no-summing note and the source honesty block', () => {
    const raw = response({ classical_sources: { directly_in_bphs_ch41_sloka_16: ['dhana_yoga_5_9'], catalog_citation_carries_verse: false } },
      { dhana_yoga_2_11: 'present' })
    raw.candidates.find(c => c.candidate_id === 'dhana_yoga_2_5_9_11')!.overlaps = ['dhana_yoga_2_11']
    const r = interpretYogaBandResponse(raw, EXPECT)
    expect(r.candidate_statuses).toHaveLength(6)
    expect(r.candidate_statuses.find(c => c.candidate_id === 'dhana_yoga_2_11')!.state).toBe('present')
    expect(r.overlap_note).toMatch(/overlapping statuses/)
    expect(r.overlap_note).toMatch(/yoga count/)
    expect(r.overlaps['dhana_yoga_2_5_9_11']).toEqual(['dhana_yoga_2_11'])
    expect(r.classical_sources.directly_in_bphs_ch41_sloka_16).toEqual(['dhana_yoga_5_9'])
    expect(r.classical_sources.catalog_citation_carries_verse).toBe(false)
    expect(r.classical_sources.note).toMatch(/general Parashari sambandha/)
  })

  it.each<[string, unknown, string]>([
    ['not an object', 'nope', 'band_response_malformed'],
    ['five rows', response({ candidates: response().candidates.slice(0, 5) }), 'band_rows_incomplete:5/6'],
    ['seven rows', response({ candidates: [...response().candidates, cand('x', 'absent')] }), 'band_rows_incomplete:7/6'],
    ['duplicate candidate', response({ candidates: [...response().candidates.slice(0, 5), response().candidates[0]] }), 'band_row_invalid'],
    ['foreign candidate id', response({ candidates: [...response().candidates.slice(0, 5), cand('lakshmi_yoga', 'absent')] }), 'band_candidate_set_mismatch'],
    ['unknown state', response({ candidates: [cand('dhana_yoga_house_lords', 'partial'), ...response().candidates.slice(1)] }), 'band_row_invalid'],
    ['wrong candidate version', response({ candidate_set_version: 'NMB-CAND-v2' }), 'band_version_mismatch'],
    ['tolerance not none', response({ tolerance: 0.1 }), 'band_tolerance_not_none'],
    ['other chart', response({ chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a' }), 'band_scope_mismatch'],
    ['other ayanamsha', response({ ayanamsha_id: 'raman' }), 'band_scope_mismatch'],
    ['wrong generation echo', response({ served_build_ids: [B_POS] }), 'band_generation_mismatch'],
  ])('source_unproven: %s', (_n, raw, reason) => {
    const r = interpretYogaBandResponse(raw, EXPECT)
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe(reason)
    expect(r.notably_absent_yogas).toEqual([])
    expect(r.band_coverage.total).toBe(0)
  })
})

describe('B1: an indeterminate candidate means the unit is NOT settled', () => {
  it('interpretYogaBandResponse reports source_unproven / band_indeterminate, keeping the counts visible', () => {
    const r = interpretYogaBandResponse(response({}, { dhana_yoga_5_9: 'indeterminate' }), EXPECT)
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe('band_indeterminate')
    expect(r.band_coverage).toEqual({ present: 0, near_miss: 0, absent: 5, indeterminate: 1, total: 6 })
    expect(r.indeterminate).toEqual([{ candidate_id: 'dhana_yoga_5_9', reason: null }])
    expect(r.notably_absent_yogas).toEqual([])
  })

  it('the checklist does not read exhaustive:true for an indeterminate band, and does for a fully determinate one', () => {
    const unit = (state: string): ChecklistUnit => ({ unit: 'notably_absent_yogas', state } as unknown as ChecklistUnit)
    const bandState = (states: Record<string, string>) => interpretYogaBandResponse(response({}, states), EXPECT).state
    expect(checklistExhaustiveness([unit(bandState({ dhana_yoga_5_9: 'indeterminate' }))]).exhaustive).toBe(false)
    expect(checklistExhaustiveness([unit(bandState({ dhana_yoga_5_9: 'present' }))]).exhaustive).toBe(true)
  })

  it('a neighbour ayanamsha that is indeterminate does not unsettle the primary band', () => {
    const r = interpretYogaBandResponse(response(), EXPECT, [{ ayanamsha_id: 'raman', raw: response({}, { dhana_yoga_5_9: 'indeterminate' }, 'raman') }])
    expect(r.state).toBe('empty_for_this_chart')
    expect(r.ayanamsha_sensitive).toBe(true)
  })
})

describe('B2: ayanamsha_sensitive is false only when every neighbour was compared', () => {
  const mine = () => response({}, { dhana_yoga_2_11: 'present' })
  const same = (aya: string) => ({ ayanamsha_id: aya, raw: response({}, { dhana_yoga_2_11: 'present' }, aya) })
  const differs = (aya: string) => ({ ayanamsha_id: aya, raw: response({}, { dhana_yoga_2_11: 'absent' }, aya) })
  const unchecked = (aya: string) => ({ ayanamsha_id: aya, raw: null })

  it('true when any compared neighbour differs, even with another unchecked', () => {
    const r = interpretYogaBandResponse(mine(), EXPECT, [differs('raman'), unchecked('true_chitra')])
    expect(r.ayanamsha_sensitive).toBe(true)
    expect(r.ayanamsha_sensitive_candidates).toEqual(['dhana_yoga_2_11'])
    expect(r.ayanamsha_sensitive_by_candidate['dhana_yoga_2_11']).toBe(true)
    expect(r.ayanamsha_sensitive_by_candidate['dhana_yoga_5_9']).toBeNull()
  })

  it('false only when all neighbours were compared and agree', () => {
    const r = interpretYogaBandResponse(mine(), EXPECT, [same('raman'), same('krishnamurti')])
    expect(r.ayanamsha_sensitive).toBe(false)
    expect(Object.values(r.ayanamsha_sensitive_by_candidate).every(v => v === false)).toBe(true)
    expect(r.ayanamsha_unchecked).toEqual([])
  })

  it('null (not false) when any neighbour could not be compared, per candidate and overall', () => {
    const r = interpretYogaBandResponse(mine(), EXPECT, [same('raman'), unchecked('krishnamurti')])
    expect(r.ayanamsha_sensitive).toBeNull()
    expect(r.ayanamsha_unchecked).toEqual(['krishnamurti'])
    expect(Object.values(r.ayanamsha_sensitive_by_candidate).every(v => v === null)).toBe(true)
  })

  it('an invalid neighbour response counts as unchecked', () => {
    const junk = { ayanamsha_id: 'raman', raw: response({ tolerance: 1 }, {}, 'raman') }
    const r = interpretYogaBandResponse(mine(), EXPECT, [junk])
    expect(r.ayanamsha_unchecked).toEqual(['raman'])
    expect(r.ayanamsha_sensitive).toBeNull()
  })

  it('zero comparable neighbours is null with a note, never false', () => {
    const none = interpretYogaBandResponse(mine(), EXPECT, [])
    expect(none.ayanamsha_sensitive).toBeNull()
    expect(none.ayanamsha_sensitivity_note).toMatch(/no neighbouring ayanamsha/i)
    expect(Object.values(none.ayanamsha_sensitive_by_candidate).every(v => v === null)).toBe(true)
    const allFailed = interpretYogaBandResponse(mine(), EXPECT, [unchecked('raman'), unchecked('true_chitra')])
    expect(allFailed.ayanamsha_sensitive).toBeNull()
    expect(allFailed.ayanamsha_sensitivity_note).toMatch(/no neighbouring ayanamsha/i)
  })
})

describe('fetchNotablyAbsentYogas (served-generation fence + sidecar)', () => {
  it('fences on ga_yoga + ga_positions only (not bo_laksana) and calls the route with the two rows builds', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())              // receipt fence
    queryMock.mockResolvedValueOnce({ rows: [{ ayanamsha_id: 'raman' }] })  // neighbouring ayanamshas
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) =>
      ok(response({}, { dhana_yoga_2_11: 'present' }, JSON.parse(String(init.body)).ayanamsha_id)))

    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())

    expect(r.state).toBe('empty_for_this_chart')
    expect(NEAR_MISS_REQUIRED_ASSETS).toEqual(['ga_yoga', 'ga_positions'])
    const [, fenceParams] = queryMock.mock.calls[0]!
    expect(fenceParams).toEqual([['ga_yoga', 'ga_positions'], CHART])
    expect(JSON.stringify(fenceParams)).not.toContain('bo_laksana')
    const [url, init] = fetchMock.mock.calls[0]!
    expect(url).toBe('http://sidecar.test/api/compute/yoga_formation_band')
    expect((init as RequestInit).method).toBe('POST')
    expect((init as RequestInit).headers).toMatchObject({ 'x-api-key': 'k-1' })
    expect(JSON.parse(String((init as RequestInit).body))).toEqual({
      chart_id: CHART, ayanamsha_id: AYA, served_build_ids: [B_POS, B_YOGA],
    })
    expect(r.served_build_ids).toEqual([B_POS, B_YOGA])
    expect(r.ayanamsha_sensitive).toBe(false)
  })

  it('zero neighbouring ayanamshas in the served facts leaves sensitivity null, not false', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockResolvedValueOnce({ rows: [] })
    fetchMock.mockResolvedValueOnce(ok(response()))
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    expect(r.ayanamsha_sensitive).toBeNull()
    expect(r.ayanamsha_sensitivity_note).toMatch(/no neighbouring ayanamsha/i)
  })

  it('reads neighbouring ayanamshas with a pinned category+key query and reports sensitivity', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockResolvedValueOnce({ rows: [{ ayanamsha_id: 'raman' }, { ayanamsha_id: 'krishnamurti' }] })
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) => {
      const aya = JSON.parse(String(init.body)).ayanamsha_id as string
      if (aya === 'krishnamurti') throw new Error('boom')
      return ok(response({}, aya === 'raman' ? { dhana_yoga_2_11: 'present' } : {}, aya))
    })

    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())

    const [sql, params] = queryMock.mock.calls[1]!
    expect(String(sql)).toContain("fact_category = 'graha_position'")
    expect(String(sql)).toContain("fact_key = 'sign'")
    expect(String(sql)).toContain('build_id = $2::uuid')
    expect(params).toEqual([CHART, B_POS, AYA])
    expect(r.ayanamsha_sensitive).toBe(true)
    expect(r.ayanamsha_unchecked).toEqual(['krishnamurti'])
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('a failed neighbour lookup leaves sensitivity unknown, not false', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockRejectedValueOnce(new Error('db'))
    fetchMock.mockResolvedValueOnce(ok(response()))
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    expect(r.state).toBe('empty_for_this_chart')
    expect(r.ayanamsha_sensitive).toBeNull()
    expect(r.ayanamsha_unchecked).toEqual(['other_ayanamshas_lookup_failed'])
  })

  it.each([
    ['a receipt does not match the selected build', () => queryMock.mockResolvedValueOnce(fenceRows(false)), generation(), 'source_fence_unproven:ga_positions,ga_yoga'],
    ['a replacement build is in flight', () => queryMock.mockResolvedValueOnce(fenceRows(true, ['ga_yoga'])), generation(), 'source_fence_unproven:ga_yoga'],
    ['the served generation does not resolve ga_positions', () => queryMock.mockResolvedValueOnce(fenceRows()), generation(['ga_positions']), 'source_fence_unproven:ga_positions'],
    ['the receipt fence query fails', () => queryMock.mockRejectedValueOnce(new Error('db')), generation(), 'source_fence_unavailable'],
  ])('source_unproven and no sidecar call when %s', async (_n, arrange, gen, reason) => {
    arrange()
    const r = await fetchNotablyAbsentYogas(CHART, AYA, gen)
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe(reason)
    expect(r.notably_absent_yogas).toEqual([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it.each([
    ['sidecar non-2xx', () => fetchMock.mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) })],
    ['sidecar network failure', () => fetchMock.mockRejectedValueOnce(new Error('ECONNREFUSED'))],
    ['sidecar timeout', () => fetchMock.mockRejectedValueOnce(new DOMException('timed out', 'TimeoutError'))],
  ])('source_unproven (sidecar_unavailable) on %s', async (_n, arrange) => {
    queryMock.mockResolvedValueOnce(fenceRows())
    arrange()
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe('sidecar_unavailable')
  })

  it('source_unproven on a malformed or non-six response from the sidecar', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    fetchMock.mockResolvedValueOnce(ok(response({ candidates: response().candidates.slice(0, 5) })))
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe('band_rows_incomplete:5/6')
  })
})

describe('E: bounded ayanamsha fan-out', () => {
  it('the closed set is the five canonical ayanamshas', () => {
    expect([...NEAR_MISS_CANONICAL_AYANAMSHAS].sort()).toEqual(
      ['krishnamurti', 'lahiri_chitrapaksha', 'raman', 'surya_siddhanta_classical', 'true_chitra'])
  })

  it('ignores unknown / duplicate / own ids from the facts and never exceeds 5 route calls', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockResolvedValueOnce({ rows: [
      { ayanamsha_id: 'raman' }, { ayanamsha_id: 'evil; DROP TABLE x' }, { ayanamsha_id: 'raman' },
      { ayanamsha_id: AYA }, { ayanamsha_id: 'krishnamurti' }, { ayanamsha_id: 'true_chitra' },
      { ayanamsha_id: 'surya_siddhanta_classical' }, { ayanamsha_id: 'made_up_1' }, { ayanamsha_id: 'made_up_2' },
    ] })
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) =>
      ok(response({}, {}, JSON.parse(String(init.body)).ayanamsha_id)))
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    const called = fetchMock.mock.calls.map(([, init]) => JSON.parse(String((init as RequestInit).body)).ayanamsha_id as string)
    expect(called).toHaveLength(5)
    expect(new Set(called)).toEqual(new Set(NEAR_MISS_CANONICAL_AYANAMSHAS))
    expect(r.ayanamsha_sensitive).toBe(false)
  })

  it('PR-3: the neighbours are read in SERVE order (Lahiri-primary), not alphabetical, and the band is labelled a cross-check', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockResolvedValueOnce({ rows: [
      { ayanamsha_id: 'krishnamurti' }, { ayanamsha_id: 'raman' }, { ayanamsha_id: 'surya_siddhanta_classical' }, { ayanamsha_id: 'true_chitra' },
    ] })
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) =>
      ok(response({}, {}, JSON.parse(String(init.body)).ayanamsha_id)))
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    const called = fetchMock.mock.calls.map(([, init]) => JSON.parse(String((init as RequestInit).body)).ayanamsha_id as string)
    // call 0 is the primary; the neighbours follow in serve order
    expect(called.slice(1)).toEqual(['true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical'])
    expect(r.ayanamsha_cross_check_label).toBe('Cross-check, not the reading')
    expect(r.ayanamsha_sensitive).toBe(false) // the booleans are kept
  })

  it('a non-canonical primary ayanamsha is unproven and never reaches the sidecar', async () => {
    const r = await fetchNotablyAbsentYogas(CHART, 'lahiri; DROP', generation())
    expect(r.state).toBe('source_unproven')
    expect(r.reason).toBe('ayanamsha_not_canonical')
    expect(fetchMock).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('E: route-result TTL cache', () => {
  beforeEach(() => {
    // Route by SQL so an early return (failed route call) never leaves a stale queued result.
    queryMock.mockImplementation(async (sql: string) =>
      String(sql).includes('FROM chart_facts') ? { rows: [] } : fenceRows())
  })
  async function callOnce(aya = AYA) {
    return fetchNotablyAbsentYogas(CHART, aya, generation())
  }

  it('constants: 60 s TTL, max 64 entries', () => {
    expect(NEAR_MISS_ROUTE_CACHE_TTL_MS).toBe(60_000)
    expect(NEAR_MISS_ROUTE_CACHE_MAX_ENTRIES).toBe(64)
  })

  it('serves a repeat call for the same (chart, ayanamsha, builds) from cache within the TTL', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    fetchMock.mockImplementation(async () => ok(response()))
    await callOnce()
    await callOnce()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('expires after the TTL and refetches', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    fetchMock.mockImplementation(async () => ok(response()))
    await callOnce()
    vi.setSystemTime(Date.now() + NEAR_MISS_ROUTE_CACHE_TTL_MS + 1)
    await callOnce()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('keys on the sorted build ids and the ayanamsha (a different generation misses)', async () => {
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) => {
      const b = JSON.parse(String(init.body))
      return ok(response({ served_build_ids: b.served_build_ids, ayanamsha_id: b.ayanamsha_id }, {}, b.ayanamsha_id))
    })
    await callOnce()
    const otherGen = chartServedGenerationFromRows(CHART, [...NEAR_MISS_REQUIRED_ASSETS], NEAR_MISS_REQUIRED_ASSETS.map(asset_id => ({
      asset_id, partition_key: '__whole_asset__', receipt_version: 'v1',
      receipt_build_id: asset_id === 'ga_yoga' ? '33333333-3333-4333-8333-333333333333' : B_POS,
      rows_build_id: asset_id === 'ga_yoga' ? '33333333-3333-4333-8333-333333333333' : B_POS,
      receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
      receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    })))
    await fetchNotablyAbsentYogas(CHART, AYA, otherGen)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    await callOnce('raman')
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('never caches a failed call', async () => {
    fetchMock.mockRejectedValueOnce(new Error('ECONNREFUSED'))
    const bad = await callOnce()
    expect(bad.reason).toBe('sidecar_unavailable')
    fetchMock.mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) })
    await callOnce()
    fetchMock.mockImplementation(async () => ok(response()))
    const good = await callOnce()
    expect(good.state).toBe('empty_for_this_chart')
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('is bounded at 64 entries (oldest evicted)', async () => {
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) => {
      const b = JSON.parse(String(init.body))
      return ok(response({ chart_id: b.chart_id, served_build_ids: b.served_build_ids }))
    })
    for (let i = 0; i < NEAR_MISS_ROUTE_CACHE_MAX_ENTRIES + 6; i++) {
      const chart = `00000000-0000-4000-8000-${String(i).padStart(12, '0')}`
      const gen = chartServedGenerationFromRows(chart, [...NEAR_MISS_REQUIRED_ASSETS], NEAR_MISS_REQUIRED_ASSETS.map(asset_id => ({
        asset_id, partition_key: '__whole_asset__', receipt_version: 'v1', receipt_build_id: B_POS, rows_build_id: B_POS,
        receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
        receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
      })))
      await fetchNotablyAbsentYogas(chart, AYA, gen)
    }
    // entry 0 was evicted: asking again refetches (a 71st distinct call is made)
    const before = fetchMock.mock.calls.length
    const chart0 = '00000000-0000-4000-8000-000000000000'
    const gen0 = chartServedGenerationFromRows(chart0, [...NEAR_MISS_REQUIRED_ASSETS], NEAR_MISS_REQUIRED_ASSETS.map(asset_id => ({
      asset_id, partition_key: '__whole_asset__', receipt_version: 'v1', receipt_build_id: B_POS, rows_build_id: B_POS,
      receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
      receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    })))
    await fetchNotablyAbsentYogas(chart0, AYA, gen0)
    expect(fetchMock.mock.calls.length).toBe(before + 1)
  })
})

describe('E: missing sidecar key is logged once', () => {
  it('warns exactly once about PYTHON_SIDECAR_API_KEY across repeated calls and still calls the route', async () => {
    delete process.env['PYTHON_SIDECAR_API_KEY']
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) =>
      ok(response({}, {}, JSON.parse(String(init.body)).ayanamsha_id)))
    for (let i = 0; i < 3; i++) {
      queryMock.mockResolvedValueOnce(fenceRows())
      queryMock.mockResolvedValueOnce({ rows: [] })
      // distinct ayanamsha per call so the cache does not hide the route call
      await fetchNotablyAbsentYogas(CHART, NEAR_MISS_CANONICAL_AYANAMSHAS[i]!, generation())
    }
    const keyWarnings = warn.mock.calls.filter(c => String(c[0]).includes('PYTHON_SIDECAR_API_KEY'))
    expect(keyWarnings).toHaveLength(1)
    const [, init] = fetchMock.mock.calls[0]!
    expect((init as RequestInit).headers).not.toHaveProperty('x-api-key')
  })

  it('does not warn when the key is set', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    fetchMock.mockImplementation(async () => ok(response()))
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockResolvedValueOnce({ rows: [] })
    await fetchNotablyAbsentYogas(CHART, AYA, generation())
    expect(warn.mock.calls.filter(c => String(c[0]).includes('PYTHON_SIDECAR_API_KEY'))).toHaveLength(0)
  })
})
