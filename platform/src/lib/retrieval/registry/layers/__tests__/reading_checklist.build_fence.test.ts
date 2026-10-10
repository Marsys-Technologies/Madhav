import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { chartServedGenerationFromRows } from '../../generation/served_generation'
import {
  fetchKpCuspChain,
  fetchWealthAshtakavarga,
  fetchWealthSpecialLagnas,
  fetchWealthYogiAvayogi,
  fetchTajakaSourceFence,
  fetchWealthTajaka,
  fetchSensitiveDegreeFirings,
  fetchWealthCorroboratingVargas,
  fetchWealthReadingSourceFence,
  WEALTH_CORROBORATING_VARGAS,
  WEALTH_READING_REQUIRED_ASSETS,
} from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const BUILD_ID = '11111111-1111-4111-8111-111111111111'

beforeEach(() => queryMock.mockReset())

/** A served generation in which every named asset resolves unless listed as unresolved. */
function servedGeneration(assetIds: readonly string[], unresolved: Record<string, string> = {}) {
  return chartServedGenerationFromRows(CHART_ID, [...assetIds], assetIds.map(asset_id => ({
    asset_id, partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: BUILD_ID, rows_build_id: unresolved[asset_id] === 'skip_chain_writer_missing' ? null : BUILD_ID,
    receipt_state: 'proven', freshness_state: unresolved[asset_id] === 'receipt_not_fresh' ? 'stale' : 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64), spec_active: true, receipt_run_state: 'completed',
    receipt_asset_present: true, receipt_disposition: unresolved[asset_id] === 'skip_chain_writer_missing' ? 'skip_no_delta' : 'build',
    observed_at: '2026-09-07T00:00:00Z',
  })))
}

describe('reading-checklist selected-build fence', () => {
  it('fences sensitive-degree facts to the judgment build', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{
      fact_id: 'active-sensitive', fact_subject: 'MAR', fact_key: 'pushkara',
      fact_value_text: 'pushkara', fact_value_jsonb: { fired: true },
    }] })

    const result = await fetchSensitiveDegreeFirings(CHART_ID, AYANAMSHA, BUILD_ID)

    expect(result.fact_ids).toEqual(['active-sensitive'])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = ANY($4::uuid[])')
    expect(String(sql)).not.toContain('build_id = $4::text')
    expect(params).toEqual([
      CHART_ID, AYANAMSHA, ['pushkara', 'gandanta', 'mrityu_bhaga', 'kartari'], [BUILD_ID],
    ])
  })

  it('threads build_id through the KP child and never accepts another generation', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })

    const result = await fetchKpCuspChain(CHART_ID, AYANAMSHA, [2, 11], BUILD_ID)

    expect(result.cusps).toEqual([])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = ANY($4::uuid[])')
    expect(String(sql)).not.toContain('build_id = $4::text')
    expect(params).toEqual([
      CHART_ID,
      // SS N-356: the KP chain is read at Krishnamurti whatever (Lahiri) id the caller passes.
      'krishnamurti',
      ['cusp_kp_lords', 'kp_cuspal_significators', 'bhava_cusps', 'kp_ruling_planets_natal'],
      [BUILD_ID],
    ])
  })

  it('requires every wealth producer to resolve to its own served generation, not one shared build', async () => {
    queryMock.mockResolvedValueOnce({ rows: WEALTH_READING_REQUIRED_ASSETS.map(asset_id => ({
      asset_id,
      receipt_matches_selected_build: true,
      replacement_in_progress: false,
    })) })

    const result = await fetchWealthReadingSourceFence(CHART_ID, servedGeneration(WEALTH_READING_REQUIRED_ASSETS))

    expect(result.ok).toBe(true)
    expect(result.ready).toBe(true)
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('asset_provenance_receipts receipt')
    expect(String(sql)).toContain('asset_freshness freshness')
    expect(String(sql)).toContain('asset_output_digest_specs digest_spec')
    // RC-1: no receipt is required to share one chart-wide build id.
    expect(String(sql)).not.toContain('receipt.build_id = $3')
    expect(String(sql)).toContain("fenced_run.state IN ('planned', 'running', 'paused')")
    expect(String(sql)).toContain('proven_receipt.build_id = fenced_run.id')
    expect(params).toEqual([[...WEALTH_READING_REQUIRED_ASSETS], CHART_ID])
  })

  it('fails closed if a selected-build receipt is missing or a replacement is active', async () => {
    queryMock.mockResolvedValueOnce({ rows: WEALTH_READING_REQUIRED_ASSETS.map(asset_id => ({
      asset_id,
      receipt_matches_selected_build: asset_id !== 'ga_strength',
      replacement_in_progress: asset_id === 'ga_vichara',
    })) })

    const result = await fetchWealthReadingSourceFence(CHART_ID, servedGeneration(WEALTH_READING_REQUIRED_ASSETS))

    expect(result.ok).toBe(true)
    expect(result.ready).toBe(false)
    expect(result.assets.find(asset => asset.asset_id === 'ga_strength')?.receipt_matches_selected_build).toBe(false)
    expect(result.assets.find(asset => asset.asset_id === 'ga_vichara')?.replacement_in_progress).toBe(true)
  })

  it('refuses a producer whose receipt exists but does not resolve to a served generation, and names why', async () => {
    queryMock.mockResolvedValueOnce({ rows: WEALTH_READING_REQUIRED_ASSETS.map(asset_id => ({
      asset_id, receipt_matches_selected_build: true, replacement_in_progress: false,
    })) })

    const result = await fetchWealthReadingSourceFence(CHART_ID, servedGeneration(
      WEALTH_READING_REQUIRED_ASSETS, { ga_structural: 'skip_chain_writer_missing', ga_vichara: 'receipt_not_fresh' },
    ))

    expect(result.ready).toBe(false)
    expect(result.assets.find(asset => asset.asset_id === 'ga_structural')).toMatchObject({
      receipt_matches_selected_build: false, served_generation_reason: 'skip_chain_writer_missing',
    })
    expect(result.assets.find(asset => asset.asset_id === 'ga_vichara')).toMatchObject({
      receipt_matches_selected_build: false, served_generation_reason: 'receipt_not_fresh',
    })
    expect(result.assets.find(asset => asset.asset_id === 'ga_strength')).toMatchObject({
      receipt_matches_selected_build: true, served_generation_reason: null,
    })
  })

  it('reads the exact D9/D11 wealth pivots from the selected build and preserves their facts', async () => {
    queryMock.mockResolvedValueOnce({ rows: [
      { id: '101', subject: 'VEN', constituent_fact_ids: ['fact-v'], value_jsonb: { per_varga: { D9: { relation: 'agree' }, D11: { relation: 'oppose' } } } },
      { id: '102', subject: 'JUP', constituent_fact_ids: ['fact-j'], value_jsonb: { per_varga: { D9: { relation: 'abstain' }, D11: { relation: 'agree' } } } },
    ] })

    const result = await fetchWealthCorroboratingVargas(CHART_ID, AYANAMSHA, [
      { role: 'bhavesha', code: 'VEN' }, { role: 'karaka', code: 'JUP' },
    ], BUILD_ID)

    expect(result.state).toBe('served')
    expect(result.rows).toHaveLength(4)
    expect(result.rows.map(row => row.varga)).toEqual([...WEALTH_CORROBORATING_VARGAS, ...WEALTH_CORROBORATING_VARGAS])
    expect(result.fact_ids).toEqual(['fact-j', 'fact-v'])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain("build_id = ANY($3::uuid[])")
    expect(String(sql)).toContain("domain = 'wealth'")
    expect(params).toEqual([CHART_ID, AYANAMSHA, [BUILD_ID], ['VEN', 'JUP']])
  })

  it('fails closed rather than treating missing or duplicate fixed pivots as an empty finding', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{
      id: '101', subject: 'VEN', constituent_fact_ids: [], value_jsonb: { per_varga: { D9: { relation: 'agree' }, D11: { relation: 'agree' } } },
    }] })
    const result = await fetchWealthCorroboratingVargas(CHART_ID, AYANAMSHA, [
      { role: 'bhavesha', code: 'VEN' }, { role: 'karaka', code: 'JUP' },
    ], BUILD_ID)
    expect(result).toEqual({ state: 'source_incomplete', rows: [], fact_ids: [] })
  })

  it('requires every fixed wealth Ashtakavarga natural key from the selected build', async () => {
    const rows = [
      ...['D2', 'D9', 'D11'].flatMap(varga => [2, 11].map(house => ({ fact_id: `b-${varga}-${house}`, fact_category: 'ashtakavarga_bindu_per_varga', fact_subject: `SARVA-HOUSE_${house}`, fact_key: varga, fact_value_num: 28 }))),
      ...['D2', 'D9', 'D11'].flatMap(varga => ['VEN', 'JUP'].map(actor => ({ fact_id: `p-${varga}-${actor}`, fact_category: 'ashtakavarga_pinda_sarva_per_varga', fact_subject: actor, fact_key: varga, fact_value_num: 48 }))),
    ]
    queryMock.mockResolvedValueOnce({ rows })
    const result = await fetchWealthAshtakavarga(CHART_ID, AYANAMSHA, ['VEN', 'JUP'], BUILD_ID)
    expect(result.state).toBe('served')
    expect(result.rows).toHaveLength(12)
    expect(String(queryMock.mock.calls[0]![0])).toContain('build_id = ANY($3::uuid[])')
  })

  it('requires the full selected-build Indu/Sree/Hora atomic lagna receipt', async () => {
    const numericKeys = new Set(['longitude_sidereal', 'pada', 'house_d1'])
    const rows = ['INDU_LAGNA', 'SREE_LAGNA', 'HORA_LAGNA'].flatMap(subject => [
      'longitude_sidereal', 'sign', 'sign_lord', 'nakshatra', 'nakshatra_lord', 'pada', 'house_d1',
    ].map(fact_key => ({
      fact_id: `${subject}-${fact_key}`,
      fact_subject: subject,
      fact_key,
      fact_value_num: numericKeys.has(fact_key) ? 12 : null,
      fact_value_text: numericKeys.has(fact_key) ? null : 'Aries',
      verification_pass_status: 'two_pass_verified',
    })))
    queryMock.mockResolvedValueOnce({ rows })

    const result = await fetchWealthSpecialLagnas(CHART_ID, AYANAMSHA, BUILD_ID)

    expect(result.state).toBe('served')
    expect(result.rows).toHaveLength(21)
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = ANY($3::uuid[])')
    expect(String(sql)).toContain("fact_category = 'special_lagna'")
    expect(params).toEqual([
      CHART_ID, AYANAMSHA, [BUILD_ID],
      ['INDU_LAGNA', 'SREE_LAGNA', 'HORA_LAGNA'],
      ['longitude_sidereal', 'sign', 'sign_lord', 'nakshatra', 'nakshatra_lord', 'pada', 'house_d1'],
    ])
  })

  it('requires every selected-build Yogi-system natural key', async () => {
    const required: Record<string, string[]> = {
      YOGI: ['point_longitude', 'sign', 'nakshatra', 'assigned_graha'],
      AVAYOGI: ['point_longitude', 'sign', 'nakshatra', 'assigned_graha'],
      DUPLICATE_YOGI: ['sign', 'assigned_graha'],
      SAHAYOGI: ['sign', 'assigned_graha'],
    }
    const rows = Object.entries(required).flatMap(([fact_subject, keys]) => keys.map(fact_key => ({
      fact_id: `${fact_subject}-${fact_key}`,
      fact_subject,
      fact_key,
      fact_value_num: fact_key === 'point_longitude' ? 123.45 : null,
      fact_value_text: fact_key === 'point_longitude' ? null : 'Mercury',
      verification_pass_status: 'two_pass_verified',
    })))
    queryMock.mockResolvedValueOnce({ rows })

    const result = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)

    expect(result.state).toBe('served')
    expect(result.rows).toHaveLength(12)
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain("fact_category = 'sensitive_point_yogi'")
    expect(String(sql)).toContain('build_id = ANY($3::uuid[])')
    expect(params).toEqual([
      CHART_ID, AYANAMSHA, [BUILD_ID],
      ['YOGI', 'AVAYOGI', 'DUPLICATE_YOGI', 'SAHAYOGI'],
      ['point_longitude', 'sign', 'nakshatra', 'assigned_graha'],
    ])
  })

  it('fences Tajaka independently and selects exactly one as-of annual record', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [{
        asset_id: 'ga_tajaka', receipt_matches_selected_build: true, replacement_in_progress: false,
      }] })
      .mockResolvedValueOnce({ rows: [{
        varsha_id: 'annual-1', varsha_year: 42,
        varsha_start_iso: '2026-01-01T00:00:00.000Z', varsha_end_iso: '2027-01-01T00:00:00.000Z',
        year_lord_method: 'tajik_classical', year_lord: 'Jupiter',
        candidate_lord_jsonb: { Jupiter: 5 }, muntha_position_jsonb: { sign: 'Aries' },
        applicable_tajik_yogas_array: [], verification_pass_status: 'two_pass_verified',
        citation_ref: 'tajaka-ref', citation_human: 'Tajaka citation.',
      }] })

    const fence = await fetchTajakaSourceFence(CHART_ID, servedGeneration(['ga_tajaka']))
    const result = await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')

    expect(fence.ready).toBe(true)
    expect(fence.assets).toEqual([{
      asset_id: 'ga_tajaka', receipt_matches_selected_build: true, served_generation_reason: null, replacement_in_progress: false,
    }])
    expect(result.state).toBe('served')
    expect(result.row?.varsha_year).toBe(42)
    const [fenceSql, fenceParams] = queryMock.mock.calls[0]!
    expect(String(fenceSql)).toContain('asset_provenance_receipts receipt')
    expect(fenceParams).toEqual([['ga_tajaka'], CHART_ID])
    const [tajakaSql, tajakaParams] = queryMock.mock.calls[1]!
    expect(String(tajakaSql)).toContain('l1_tajik_varsha_year_lords')
    expect(String(tajakaSql)).toContain('build_id = ANY($3::uuid[])')
    expect(String(tajakaSql)).toContain('varsha_start_iso <= $4::date')
    expect(tajakaParams).toEqual([CHART_ID, AYANAMSHA, [BUILD_ID], '2026-09-19'])
  })
})
