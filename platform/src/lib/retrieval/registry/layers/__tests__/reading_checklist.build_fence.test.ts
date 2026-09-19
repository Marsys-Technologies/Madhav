import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import {
  fetchKpCuspChain,
  fetchSensitiveDegreeFirings,
  fetchWealthReadingSourceFence,
  WEALTH_READING_REQUIRED_ASSETS,
} from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const BUILD_ID = '11111111-1111-4111-8111-111111111111'

beforeEach(() => queryMock.mockReset())

describe('reading-checklist selected-build fence', () => {
  it('fences sensitive-degree facts to the judgment build', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{
      fact_id: 'active-sensitive', fact_subject: 'MAR', fact_key: 'pushkara',
      fact_value_text: 'pushkara', fact_value_jsonb: { fired: true },
    }] })

    const result = await fetchSensitiveDegreeFirings(CHART_ID, AYANAMSHA, BUILD_ID)

    expect(result.fact_ids).toEqual(['active-sensitive'])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = $4::uuid')
    expect(String(sql)).not.toContain('build_id = $4::text')
    expect(params).toEqual([
      CHART_ID, AYANAMSHA, ['pushkara', 'gandanta', 'mrityu_bhaga', 'kartari'], BUILD_ID,
    ])
  })

  it('threads build_id through the KP child and never accepts another generation', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })

    const result = await fetchKpCuspChain(CHART_ID, AYANAMSHA, [2, 11], BUILD_ID)

    expect(result.cusps).toEqual([])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = $4::uuid')
    expect(String(sql)).not.toContain('build_id = $4::text')
    expect(params).toEqual([
      CHART_ID,
      AYANAMSHA,
      ['cusp_kp_lords', 'kp_cuspal_significators', 'bhava_cusps', 'kp_ruling_planets_natal'],
      BUILD_ID,
    ])
  })

  it('requires all wealth producers to have a current-spec fresh/proven receipt for the selected build', async () => {
    queryMock.mockResolvedValueOnce({ rows: WEALTH_READING_REQUIRED_ASSETS.map(asset_id => ({
      asset_id,
      receipt_matches_selected_build: true,
      replacement_in_progress: false,
    })) })

    const result = await fetchWealthReadingSourceFence(CHART_ID, BUILD_ID)

    expect(result.ok).toBe(true)
    expect(result.ready).toBe(true)
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('asset_provenance_receipts receipt')
    expect(String(sql)).toContain('asset_freshness freshness')
    expect(String(sql)).toContain('asset_output_digest_specs digest_spec')
    expect(String(sql)).toContain('receipt.build_id = $3::uuid')
    expect(String(sql)).toContain("fenced_run.state IN ('planned', 'running', 'paused')")
    expect(String(sql)).toContain('proven_receipt.build_id = fenced_run.id')
    expect(params).toEqual([[...WEALTH_READING_REQUIRED_ASSETS], CHART_ID, BUILD_ID])
  })

  it('fails closed if a selected-build receipt is missing or a replacement is active', async () => {
    queryMock.mockResolvedValueOnce({ rows: WEALTH_READING_REQUIRED_ASSETS.map(asset_id => ({
      asset_id,
      receipt_matches_selected_build: asset_id !== 'ga_strength',
      replacement_in_progress: asset_id === 'ga_vichara',
    })) })

    const result = await fetchWealthReadingSourceFence(CHART_ID, BUILD_ID)

    expect(result.ok).toBe(true)
    expect(result.ready).toBe(false)
    expect(result.assets.find(asset => asset.asset_id === 'ga_strength')?.receipt_matches_selected_build).toBe(false)
    expect(result.assets.find(asset => asset.asset_id === 'ga_vichara')?.replacement_in_progress).toBe(true)
  })
})
