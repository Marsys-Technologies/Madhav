import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getKpCuspsCapability } from '../get_kp_cusps'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// Minimal fact-row fixtures for house 1 across the four KP categories (krishnamurti),
// mirroring the real native-chart values so the assembly is exercised end-to-end.
const ROWS = [
  { fact_id: 'a1', fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_01', fact_key: 'star_lord', fact_value_text: 'Ketu', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'a2', fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_01', fact_key: 'sub_lord', fact_value_text: 'Mercury', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'a3', fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_01', fact_key: 'sub_sub_lord', fact_value_text: 'Rahu', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'a4', fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_01', fact_key: 'prana_lord', fact_value_text: 'Rahu', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'b1', fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_1', fact_key: 'sign_lord', fact_value_text: 'Mars', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'b2', fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_1', fact_key: 'star_lord', fact_value_text: 'Ketu', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'b3', fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_1', fact_key: 'sub_lord', fact_value_text: 'Mercury', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'b4', fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_1', fact_key: 'cusp_longitude_sidereal', fact_value_text: null, fact_value_num: 12.528, fact_value_jsonb: null },
  { fact_id: 'b5', fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti', fact_subject: 'CUSP_1', fact_key: 'significators_json', fact_value_text: null, fact_value_num: null, fact_value_jsonb: ['Mars', 'Ketu'] },
  { fact_id: 'c1', fact_category: 'bhava_cusps', ayanamsha_id: 'krishnamurti', fact_subject: 'BHAVA_01', fact_key: 'placidus_madhya', fact_value_text: null, fact_value_num: 27.5226, fact_value_jsonb: null },
  { fact_id: 'd1', fact_category: 'kp_ruling_planets_natal', ayanamsha_id: 'krishnamurti', fact_subject: 'RP_ASC_LORD', fact_key: 'ruling_planet', fact_value_text: 'Mars', fact_value_num: null, fact_value_jsonb: null },
  { fact_id: 'd2', fact_category: 'kp_ruling_planets_natal', ayanamsha_id: 'krishnamurti', fact_subject: 'RP_ASC_LORD', fact_key: 'longitude_sidereal', fact_value_text: null, fact_value_num: 12.528, fact_value_jsonb: null },
]

describe('getKpCuspsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('requires chart_id', async () => {
    const result = await getKpCuspsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('defaults to the KP-canonical krishnamurti ayanamsha, param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: ROWS })
    await getKpCuspsCapability.handler({ chart_id: CHART_ID }, undefined)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params[0]).toBe(CHART_ID)
    expect(params[1]).toBe('krishnamurti')
    // categories array does NOT include graha_kp_lords unless opted in
    expect(params[2]).not.toContain('graha_kp_lords')
  })

  it('fences KP facts to the requested build and returns that provenance', async () => {
    const buildId = '815ec8dd-d994-490f-b99c-f1fc4776f39d'
    mockQuery.mockResolvedValueOnce({ rows: ROWS })

    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, build_id: buildId }, undefined)

    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(sql).toContain('AND build_id = ANY($4::uuid[])')
    expect(sql).not.toContain('AND build_id = $4::text')
    expect(params).toEqual([CHART_ID, 'krishnamurti', expect.any(Array), [buildId]])
    expect((result.content as Record<string, unknown>)['build_id']).toBe(buildId)
  })

  it('assembles a per-cusp view with the full KP chain + sign derived from stored longitude', async () => {
    mockQuery.mockResolvedValueOnce({ rows: ROWS })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const cusps = content['cusps'] as Array<Record<string, unknown>>
    expect(cusps).toHaveLength(1)
    const c1 = cusps[0]
    expect(c1['house']).toBe(1)
    expect(c1['sign_lord']).toBe('Mars')
    expect(c1['star_lord']).toBe('Ketu')
    expect(c1['sub_lord']).toBe('Mercury')
    expect(c1['sub_sub_lord']).toBe('Rahu')
    expect(c1['prana_lord']).toBe('Rahu')
    // 12.528° sidereal → Aries (0–30°)
    expect(c1['sign']).toBe('Aries')
    expect(c1['cusp_degrees']).toMatchObject({ placidus_madhya: 27.5226 })
    expect(c1['chain_divergence']).toBeNull()
    expect((c1['fact_ids'] as string[]).length).toBeGreaterThan(0)
    const rp = content['ruling_planets'] as Array<Record<string, unknown>>
    expect(rp[0]).toMatchObject({ role: 'RP_ASC_LORD', ruling_planet: 'Mars' })
  })

  it('flags a star/sub divergence between the two KP source categories instead of silently choosing', async () => {
    const diverged = ROWS.map(r =>
      r.fact_id === 'b2' ? { ...r, fact_value_text: 'Sun' } : r,  // kp_cuspal_significators star_lord ≠ cusp_kp_lords
    )
    mockQuery.mockResolvedValueOnce({ rows: diverged })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID }, undefined)
    const cusps = (result.content as Record<string, unknown>)['cusps'] as Array<Record<string, unknown>>
    expect(cusps[0]['chain_divergence']).not.toBeNull()
    expect(String((cusps[0]['chain_divergence'] as string[])[0])).toContain('star_lord')
  })

  it('include_graha_kp_lords adds the category and returns the per-graha chain', async () => {
    const withGraha = [
      ...ROWS,
      { fact_id: 'g1', fact_category: 'graha_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: 'JUP', fact_key: 'star_lord', fact_value_text: 'Ketu', fact_value_num: null, fact_value_jsonb: null },
      { fact_id: 'g2', fact_category: 'graha_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: 'JUP', fact_key: 'sub_lord', fact_value_text: 'Saturn', fact_value_num: null, fact_value_jsonb: null },
    ]
    mockQuery.mockResolvedValueOnce({ rows: withGraha })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, include_graha_kp_lords: true }, undefined)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params[2]).toContain('graha_kp_lords')
    const graha = (result.content as Record<string, unknown>)['graha_kp_lords'] as Array<Record<string, unknown>>
    expect(graha[0]).toMatchObject({ graha: 'JUP', star_lord: 'Ketu', sub_lord: 'Saturn' })
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'nope' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    // SS N-362 (b): the id 'nope' is ignored (KP has one frame); the empty reason names the frame actually read
    // and the note names the ignored request.
    expect(String(content['empty_reason'])).toContain('ayanamsha_id=krishnamurti')
    expect(String(content['ayanamsha_note'])).toContain("'nope'")
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: per_chart scope requires chart_id, grounds to l1 fact_ids', () => {
    expect(getKpCuspsCapability.scope).toBe('per_chart')
    expect(getKpCuspsCapability.required_inputs).toContain('chart_id')
    expect(getKpCuspsCapability.grounds_to).toMatchObject({ l1_fact_ids: true })
  })

  it('refuses (never reads unfenced, never matches zero rows) on an explicit-empty build fence', async () => {
    mockQuery.mockReset()
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, build_id: [] }, undefined)
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)['code']).toBe('explicit_empty_build_fence')
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

// SS N-362 (b): NO asymmetry. get_kp_cusps follows the same rule as every other KP read: it IGNORES a
// non-KP id (reads krishnamurti always, also for "all", scope "all" and an unrecognised id), says so
// in `ayanamsha_note` when something other than krishnamurti was asked for, and keeps the KP label.
describe('getKpCuspsCapability: one KP frame whatever ayanamsha is passed (SS N-362 b)', () => {
  beforeEach(() => { mockQuery.mockReset() })

  const NON_KP = ['lahiri_chitrapaksha', 'true_chitra', 'raman', 'surya_siddhanta_classical']
  /** [label, extra args, value the note must name (null = no note)] */
  const requests: Array<[string, Record<string, unknown>, string | null]> = [
    ['no id', {}, null],
    ['krishnamurti itself', { ayanamsha_id: 'krishnamurti' }, null],
    ['the alias kp', { ayanamsha_id: 'kp' }, null],
    ['the Lahiri primary id (what a caller or the bridge passes)', { ayanamsha_id: 'lahiri_chitrapaksha' }, 'lahiri_chitrapaksha'],
    ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }, 'LAHIRI'],
    ['raman', { ayanamsha_id: 'raman' }, 'raman'],
    ['true_chitra', { ayanamsha_id: 'true_chitra' }, 'true_chitra'],
    ['"all"', { ayanamsha_id: 'all' }, 'all'],
    ['ayanamsha_scope "all"', { ayanamsha_scope: 'all' }, 'all'],
    ['a nonsense id', { ayanamsha_id: 'not_an_ayanamsha_xyz' }, 'not_an_ayanamsha_xyz'],
  ]

  it.each(requests)('%s: SQL param is krishnamurti, labelled, note only when asked otherwise', async (_label, extra, requested) => {
    mockQuery.mockResolvedValueOnce({ rows: ROWS })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, ...extra }, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery).toHaveBeenCalledTimes(1)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params[1]).toBe('krishnamurti')
    for (const other of NON_KP) expect(params).not.toContain(other)
    const c = result.content as Record<string, unknown>
    expect(c['ayanamsha_id']).toBe('krishnamurti')
    expect(c['ayanamsha_scope']).toBeUndefined()
    expect(c['kp_frame_ayanamsha_id']).toBe('krishnamurti')
    expect(c['kp_frame_label']).toBe(KP_FRAME_LABEL)
    if (requested === null) {
      expect(c['ayanamsha_note']).toBeUndefined()
    } else {
      expect(String(c['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
      expect(String(c['ayanamsha_note'])).toContain(`'${requested}'`)
    }
  })

  it.each(requests)('%s: the empty-result payload reads krishnamurti, keeps the label and the note', async (_label, extra, requested) => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, ...extra }, undefined)
    expect(result.is_error).toBe(false)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params[1]).toBe('krishnamurti')
    const c = result.content as Record<string, unknown>
    expect(c['count']).toBe(0)
    expect(c['ayanamsha_id']).toBe('krishnamurti')
    expect(c['kp_frame_label']).toBe(KP_FRAME_LABEL)
    expect(String(c['empty_reason'])).toContain('ayanamsha_id=krishnamurti')
    if (requested === null) expect(c['ayanamsha_note']).toBeUndefined()
    else expect(String(c['ayanamsha_note'])).toContain(`'${requested}'`)
  })

  it('a non-KP id never turns into an invalid-ayanamsha error (KP ignores the passed id)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: ROWS })
    const result = await getKpCuspsCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'bogus' }, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('the build fence still composes with the pinned frame (param order unchanged)', async () => {
    const buildId = '815ec8dd-d994-490f-b99c-f1fc4776f39d'
    mockQuery.mockResolvedValueOnce({ rows: ROWS })
    await getKpCuspsCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'raman', build_id: buildId }, undefined)
    expect(mockQuery.mock.calls[0][1]).toEqual([CHART_ID, 'krishnamurti', expect.any(Array), [buildId]])
  })
})
