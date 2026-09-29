/**
 * reading_checklist.near_miss.test.ts -- the NMB-CAND-v1 near-miss reader (packet v1.1 section 6/7).
 *
 * `fetchNotablyAbsentYogas` is fenced to the served generation of ga_yoga + ga_positions, calls the
 * sidecar route, and turns anything unproven into `source_unproven` (never an empty finding).
 * `interpretYogaBandResponse` is the pure state/wording interpreter.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { chartServedGenerationFromRows } from '../../generation/served_generation'
import {
  NEAR_MISS_CANDIDATE_IDS,
  NEAR_MISS_FORBIDDEN_WORDING,
  NEAR_MISS_REQUIRED_ASSETS,
  fetchNotablyAbsentYogas,
  interpretYogaBandResponse,
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
    pairs: [], l1_firing_ids: [], constituent_fact_ids: [], contradicting_present_siblings: [], ...extra,
  }
}
const NEAR = {
  pairs: [{ houses_ruled: [2, 11], lords: ['venus', 'saturn'], association_mode: 'conjunction', placement_houses: [8], associated: true, gate_failed: true }],
  constituent_fact_ids: ['f2', 'f1'],
}
function response(over: Record<string, unknown> = {}, states: Record<string, string> = {}, ayanamsha = AYA) {
  return {
    band_version: 'NMB-BAND-v1', candidate_set_version: 'NMB-CAND-v1', eligibility_rule_version: 'NMB-ELIG-v1',
    tolerance: 'none', chart_id: CHART, ayanamsha_id: ayanamsha, served_build_ids: [B_POS, B_YOGA],
    candidates: NEAR_MISS_CANDIDATE_IDS.map(id => cand(id, states[id] ?? 'absent', states[id] === 'near_miss' ? NEAR : {})),
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
  vi.stubGlobal('fetch', fetchMock)
  process.env['PYTHON_SIDECAR_URL'] = 'http://sidecar.test/'
  process.env['PYTHON_SIDECAR_API_KEY'] = 'k-1'
})
afterEach(() => {
  vi.unstubAllGlobals()
  delete process.env['PYTHON_SIDECAR_URL']
  delete process.env['PYTHON_SIDECAR_API_KEY']
})

const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body })

describe('interpretYogaBandResponse', () => {
  it('serves near_miss rows only, counts all four states, keeps indeterminate visible', () => {
    const r = interpretYogaBandResponse(response({}, {
      dhana_yoga_house_lords: 'near_miss', dhana_yoga_2_11: 'present', dhana_yoga_5_9: 'indeterminate',
    }), EXPECT)
    expect(r.state).toBe('served')
    expect(r.near_miss.map(x => x.candidate_id)).toEqual(['dhana_yoga_house_lords'])
    expect(r.band_coverage).toEqual({ present: 1, near_miss: 1, absent: 3, indeterminate: 1, total: 6 })
    expect(r.indeterminate.map(x => x.candidate_id)).toEqual(['dhana_yoga_5_9'])
    expect(r.fact_ids).toEqual(['f1', 'f2'])
    expect(r.ayanamsha_sensitive).toBe(false)
  })

  it('near_miss wording follows the fixed template and never trips the forbidden-word rule', () => {
    const [row] = interpretYogaBandResponse(response({}, { dhana_yoga_house_lords: 'near_miss' }), EXPECT).near_miss
    expect(row!.statement).toBe(
      'Not formed: Yoga dhana_yoga_house_lords requires Lords associate (dhana_yoga_house_lords). ' +
      'The chart meets the lord-association leg (the lords of houses 2 and 11, venus and saturn, associate by conjunction); ' +
      'it fails the meeting-house leg (the association falls in house 8, a dusthana of 6/8/12).')
    expect(row!.statement).not.toMatch(NEAR_MISS_FORBIDDEN_WORDING)
    for (const word of ['has', 'gives', 'partial yoga', '50%', 'strength', 'effect', 'prediction']) {
      expect(NEAR_MISS_FORBIDDEN_WORDING.test(`the chart ${word} it`)).toBe(true)
    }
  })

  it('replaces catalogue text that would trip the wording rule, never edits it', () => {
    const bad = response({}, { dhana_yoga_house_lords: 'near_miss' })
    const c = bad.candidates.find(x => x.candidate_id === 'dhana_yoga_house_lords')!
    c.formation_text = 'The chart has a strong effect'
    c.yoga_name = 'Gives wealth yoga'
    const [row] = interpretYogaBandResponse(bad, EXPECT).near_miss
    expect(row!.statement).toContain('requires the shipped formation rule for dhana_yoga_house_lords')
    expect(row!.yoga_name).toBe('dhana_yoga_house_lords')
    expect(row!.statement).not.toMatch(NEAR_MISS_FORBIDDEN_WORDING)
  })

  it('empty_for_this_chart when the band is complete with zero near_miss rows', () => {
    const r = interpretYogaBandResponse(response({}, { dhana_yoga_2_11: 'present' }), EXPECT)
    expect(r.state).toBe('empty_for_this_chart')
    expect(r.near_miss).toEqual([])
    expect(r.band_coverage.total).toBe(6)
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
    expect(r.near_miss).toEqual([])
    expect(r.band_coverage.total).toBe(0)
  })

  it('an unrenderable near_miss row (no gate-failed pair) is unproven, never silently dropped', () => {
    const bad = response({}, { dhana_yoga_house_lords: 'near_miss' })
    bad.candidates.find(x => x.candidate_id === 'dhana_yoga_house_lords')!.pairs = []
    expect(interpretYogaBandResponse(bad, EXPECT).reason).toBe('near_miss_row_unrenderable')
  })

  it('ayanamsha_sensitive is true when another ayanamsha differs, false when all agree, null when unchecked', () => {
    const mine = response({}, { dhana_yoga_house_lords: 'near_miss' })
    const differs = interpretYogaBandResponse(mine, EXPECT, [{ ayanamsha_id: 'raman', raw: response({}, { dhana_yoga_house_lords: 'present' }, 'raman') }])
    expect(differs.ayanamsha_sensitive).toBe(true)
    expect(differs.ayanamsha_sensitive_candidates).toEqual(['dhana_yoga_house_lords'])
    expect(differs.near_miss[0]!.ayanamsha_sensitive).toBe(true)
    const same = interpretYogaBandResponse(mine, EXPECT, [{ ayanamsha_id: 'raman', raw: response({}, { dhana_yoga_house_lords: 'near_miss' }, 'raman') }])
    expect(same.ayanamsha_sensitive).toBe(false)
    const unknown = interpretYogaBandResponse(mine, EXPECT, [{ ayanamsha_id: 'raman', raw: null }])
    expect(unknown.ayanamsha_sensitive).toBeNull()
    expect(unknown.ayanamsha_unchecked).toEqual(['raman'])
    expect(unknown.near_miss[0]!.ayanamsha_sensitive).toBeNull()
    const junk = interpretYogaBandResponse(mine, EXPECT, [{ ayanamsha_id: 'raman', raw: response({ tolerance: 1 }, {}, 'raman') }])
    expect(junk.ayanamsha_unchecked).toEqual(['raman'])
  })
})

describe('fetchNotablyAbsentYogas (served-generation fence + sidecar)', () => {
  it('fences on ga_yoga + ga_positions only (not bo_laksana) and calls the route with the two rows builds', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())              // receipt fence
    queryMock.mockResolvedValueOnce({ rows: [] })             // neighbouring ayanamshas
    fetchMock.mockResolvedValueOnce(ok(response({}, { dhana_yoga_house_lords: 'near_miss' })))

    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())

    expect(r.state).toBe('served')
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
  })

  it('reads neighbouring ayanamshas with a pinned category+key query and reports sensitivity', async () => {
    queryMock.mockResolvedValueOnce(fenceRows())
    queryMock.mockResolvedValueOnce({ rows: [{ ayanamsha_id: 'raman' }, { ayanamsha_id: 'krishnamurti' }] })
    fetchMock.mockImplementation(async (_u: string, init: RequestInit) => {
      const aya = JSON.parse(String(init.body)).ayanamsha_id as string
      if (aya === 'krishnamurti') throw new Error('boom')
      return ok(response({}, aya === 'raman' ? { dhana_yoga_house_lords: 'present' } : { dhana_yoga_house_lords: 'near_miss' }, aya))
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
    fetchMock.mockResolvedValueOnce(ok(response({}, { dhana_yoga_house_lords: 'near_miss' })))
    const r = await fetchNotablyAbsentYogas(CHART, AYA, generation())
    expect(r.state).toBe('served')
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
    expect(r.near_miss).toEqual([])
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
