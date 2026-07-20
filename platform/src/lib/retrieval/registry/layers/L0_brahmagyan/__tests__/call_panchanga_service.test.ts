/**
 * call_panchanga_service — W2b Batch 3 dark-set wiring (chart_panchanga_cache concept,
 * TABLE_CONCEPT_DISPOSITIONS_v2_0.md §6/§8)
 * ============================================================================
 * Proves the handler forwards to the real `panchang.py` compute-service endpoints
 * (/api/compute/panchanga, /api/compute/panchanga/range) — the same mocked-fetch
 * wiring-seam pattern as `L3_kala/__tests__/w2_dark_set_wiring.test.ts` (this file's
 * own header cites that as the pattern being followed). A live, unmocked compute
 * proof against the real Swiss-Ephemeris-backed panchang engine is out of this
 * platform-side suite's scope (python-sidecar owns that) — this suite's job is
 * narrower: the TS handler's request shape, URL, mode dispatch, and error handling.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { callPanchangaServiceCapability } from '../call_panchanga_service'

const ORIGINAL_ENV = { ...process.env }

afterEach(() => {
  vi.unstubAllGlobals()
  process.env = { ...ORIGINAL_ENV }
})

describe('call_panchanga_service — mode=single', () => {
  it('forwards to POST {sidecar}/api/compute/panchanga with default Bhubaneswar/IST coordinates', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
    process.env.PYTHON_SIDECAR_API_KEY = 'test-key'

    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(url).toBe('http://sidecar.test/api/compute/panchanga')
      expect(init.method).toBe('POST')
      expect(JSON.parse(init.body as string)).toEqual({
        date: '2026-07-20',
        lat: 20.27,
        lon: 85.84,
        tz_offset_minutes: 330,
        chart_id: undefined,
      })
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          panchang: { tithi: 'Shukla Saptami', vara: 'Somavara', nakshatra: 'Hasta', yoga: 'Shiva', karana: 'Garaja' },
          native_context: null,
          cache_hit: false,
        }),
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await callPanchangaServiceCapability.handler({ date: '2026-07-20' }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['panchang']).toMatchObject({ tithi: 'Shukla Saptami' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('passes through an optional chart_id to hydrate native_context', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'

    const fetchMock = vi.fn(async (_url: string, init: RequestInit) => {
      expect(JSON.parse(init.body as string)).toMatchObject({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' })
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, panchang: {}, native_context: { birth_nakshatra: 'Purva Bhadrapada' }, cache_hit: false }),
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await callPanchangaServiceCapability.handler(
      { date: '2026-07-20', chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
      undefined
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['native_context']).toMatchObject({ birth_nakshatra: 'Purva Bhadrapada' })
  })

  it('requires date for mode=single', async () => {
    const result = await callPanchangaServiceCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })
})

describe('call_panchanga_service — mode=range', () => {
  it('forwards to POST {sidecar}/api/compute/panchanga/range', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'

    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(url).toBe('http://sidecar.test/api/compute/panchanga/range')
      expect(JSON.parse(init.body as string)).toMatchObject({ date_from: '2026-07-20', date_to: '2026-07-25' })
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, panchangs: [{ date: '2026-07-20' }, { date: '2026-07-21' }], count: 2 }),
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await callPanchangaServiceCapability.handler(
      { mode: 'range', date_from: '2026-07-20', date_to: '2026-07-25' },
      undefined
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(2)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('requires date_from and date_to for mode=range', async () => {
    const result = await callPanchangaServiceCapability.handler({ mode: 'range', date_from: '2026-07-20' }, undefined)
    expect(result.is_error).toBe(true)
  })
})

describe('call_panchanga_service — error handling', () => {
  it('reports a config error when PYTHON_SIDECAR_URL is unset', async () => {
    delete process.env.PYTHON_SIDECAR_URL
    const result = await callPanchangaServiceCapability.handler({ date: '2026-07-20' }, undefined)
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>)['error'])).toContain('PYTHON_SIDECAR_URL not configured')
  })

  it('surfaces a sidecar non-OK response as an error, not a silent success', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 500, json: async () => ({ detail: 'engine error' }) })))

    const result = await callPanchangaServiceCapability.handler({ date: '2026-07-20' }, undefined)
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>)['error'])).toContain('500')
  })

  it('rejects an unknown mode', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
    const result = await callPanchangaServiceCapability.handler({ mode: 'bogus', date: '2026-07-20' }, undefined)
    expect(result.is_error).toBe(true)
  })
})

describe('call_panchanga_service — descriptor shape', () => {
  it('is a global-scope tool, distinct from the natal-only chart_panchanga concept', () => {
    expect(callPanchangaServiceCapability.scope).toBe('global')
    expect(callPanchangaServiceCapability.uri).toBe('marsys://tool/L0/call_panchanga_service')
  })
})
