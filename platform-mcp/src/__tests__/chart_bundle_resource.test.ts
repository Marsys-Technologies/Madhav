/**
 * INF11-S1: chart_bundle_resource + multi_ayanamsha_resource tests
 * [BUILD-ORCH-J-03]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { registerChartBundleResource } from '../resources/chart_bundle_resource.js'
import { registerMultiAyanamshaResource } from '../resources/multi_ayanamsha_resource.js'

function makeMockServer() {
  const handlers: Map<string, (...args: unknown[]) => unknown> = new Map()
  return {
    resource: vi.fn((_name: string, _template: unknown, handler: unknown) => {
      handlers.set(_name as string, handler as (...args: unknown[]) => unknown)
    }),
    getHandler: (name: string) => handlers.get(name),
  }
}

const CHART_ID = 'cccccccc-0000-0000-0000-000000000001'

const MOCK_BUNDLE = {
  chart_id: CHART_ID,
  ayanamshas_requested: ['lahiri', 'true_chitra'],
  ayanamshas_found: ['lahiri', 'true_chitra'],
  birth_panchanga: { tithi: 'Shukla Tritiya', vara: 'Ravivara', moon_nakshatra: 'Rohini' },
  active_yogas: [{ yoga_name: 'Gajakesari', strength: 0.9 }],
  ayanamsha_slices: [{
    ayanamsha_id: 'lahiri',
    planets: [{ planet: 'Sun', sign: 'Capricorn', house: 12, nakshatra: 'Uttara Ashadha' }],
    houses: [{ house: 1, sign: 'Aquarius' }],
    dasha_chain: [{ level: 'maha', lord: 'Mercury', start_date: '2023-01-01', end_date: '2040-01-01' }],
  }],
  cross_ayanamsha: [{ ayanamsha_1: 'lahiri', ayanamsha_2: 'raman', divergence_score: 0.15 }],
  token_estimate: 1200,
}

describe('registerChartBundleResource', () => {
  let server: ReturnType<typeof makeMockServer>

  beforeEach(() => {
    server = makeMockServer()
    vi.clearAllMocks()
  })

  it('registers resource named chart-bundle', () => {
    registerChartBundleResource(server as never)
    expect(server.resource).toHaveBeenCalledWith('chart-bundle', expect.anything(), expect.any(Function))
  })

  it('returns markdown with panchanga data when bundle available', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_BUNDLE,
    })

    registerChartBundleResource(server as never)
    const handler = server.getHandler('chart-bundle') as Function
    const uri = { href: `marsys://chart-bundle/${CHART_ID}`, pathname: `/${CHART_ID}` }
    const result = await handler(uri, {})

    const text = result.contents[0].text as string
    expect(text).toContain('Shukla Tritiya')
    expect(text).toContain('Ravivara')
    expect(text).toContain('Gajakesari')
    expect(text).toContain('Mercury')
  })

  it('returns fallback message when API fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network error'))

    registerChartBundleResource(server as never)
    const handler = server.getHandler('chart-bundle') as Function
    const uri = { href: `marsys://chart-bundle/${CHART_ID}`, pathname: `/${CHART_ID}` }
    const result = await handler(uri, {})

    const text = result.contents[0].text as string
    expect(text).toContain('Bundle data not yet loaded')
  })

  it('returns fallback when API returns non-ok status', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 })

    registerChartBundleResource(server as never)
    const handler = server.getHandler('chart-bundle') as Function
    const uri = { href: `marsys://chart-bundle/${CHART_ID}`, pathname: `/${CHART_ID}` }
    const result = await handler(uri, {})

    const text = result.contents[0].text as string
    expect(text).toContain('Bundle data not yet loaded')
  })
})

const MOCK_STATUS = {
  ayanamsha_status: [
    { ayanamsha_id: 'lahiri', latest_build_id: 'b1', status: 'complete', finished_at: '2026-05-30T04:00:00Z', engine_version: 'v1', is_latest_engine: true, steps_complete: 14, steps_total: 14 },
    { ayanamsha_id: 'raman', latest_build_id: null, status: 'not_built', finished_at: null, engine_version: null, is_latest_engine: false, steps_complete: 0, steps_total: 0 },
  ],
}

describe('registerMultiAyanamshaResource', () => {
  let server: ReturnType<typeof makeMockServer>

  beforeEach(() => {
    server = makeMockServer()
    vi.clearAllMocks()
  })

  it('registers resource named multi-ayanamsha', () => {
    registerMultiAyanamshaResource(server as never)
    expect(server.resource).toHaveBeenCalledWith('multi-ayanamsha', expect.anything(), expect.any(Function))
  })

  it('returns markdown table with build status', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_STATUS,
    })

    registerMultiAyanamshaResource(server as never)
    const handler = server.getHandler('multi-ayanamsha') as Function
    const uri = { href: `marsys://multi-ayanamsha/${CHART_ID}`, pathname: `/${CHART_ID}` }
    const result = await handler(uri, {})

    const text = result.contents[0].text as string
    expect(text).toContain('lahiri')
    expect(text).toContain('complete')
    expect(text).toContain('not_built')
  })

  it('returns fallback when status fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('timeout'))

    registerMultiAyanamshaResource(server as never)
    const handler = server.getHandler('multi-ayanamsha') as Function
    const uri = { href: `marsys://multi-ayanamsha/${CHART_ID}`, pathname: `/${CHART_ID}` }
    const result = await handler(uri, {})

    const text = result.contents[0].text as string
    expect(text).toContain('Trigger a build first')
  })
})
