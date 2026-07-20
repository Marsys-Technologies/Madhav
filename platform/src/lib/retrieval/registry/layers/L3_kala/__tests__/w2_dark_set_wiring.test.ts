/**
 * W2 dark-set wiring — call_ephemeris_at_t (ka_graha_sancara, GT-50) +
 * call_muhurta_score (ka_muhurta_seva, §F gate ruling item 6)
 * ============================================================================
 * Proves both handlers now forward to the real sidecar endpoints
 * (/api/compute/ephemeris_at_t, /api/compute/muhurta_score) instead of the old
 * unconditional-error stub. Mocks `fetch` (this suite runs without a live
 * sidecar process) — the REAL end-to-end compute proof (real swisseph /
 * panchang_engine output, no mocks) lives in the sidecar's own pytest suite:
 *   platform/python-sidecar/tests/l3/test_ephemeris_at_t_sidecar_route.py
 *   platform/python-sidecar/tests/l3/test_muhurta_score_sidecar_route.py
 * This suite's job is narrower and TS-specific: prove the TS handler's request
 * shape, URL, error handling, and success-path passthrough are correct — the
 * exact wiring seam the old stub never exercised.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { callEphemerisAtTCapability, callMuhurtaScoreCapability } from '../call_service_wrappers'

const ORIGINAL_ENV = { ...process.env }

afterEach(() => {
  vi.unstubAllGlobals()
  process.env = { ...ORIGINAL_ENV }
})

describe('call_ephemeris_at_t — no longer the dead stub', () => {
  it('forwards to POST {sidecar}/api/compute/ephemeris_at_t and returns real-shaped positions on success', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
    process.env.PYTHON_SIDECAR_API_KEY = 'test-key'

    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(url).toBe('http://sidecar.test/api/compute/ephemeris_at_t')
      expect(init.method).toBe('POST')
      expect(JSON.parse(init.body as string)).toEqual({
        datetime_utc: '2026-07-20T12:00:00Z',
        ayanamsha_id: 'lahiri_chitrapaksha',
      })
      return {
        ok: true,
        status: 200,
        json: async () => ({
          datetime_utc: '2026-07-20T12:00:00Z',
          ayanamsha_id: 'lahiri_chitrapaksha',
          jd: 2461242.0,
          positions: [
            { planet: 'Sun', longitude: 93.57, sign: 'Cancer', deg_in_sign: 3.57, nakshatra: 'Pushya', pada: 1, retrograde: false, speed: 0.95 },
          ],
        }),
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await callEphemerisAtTCapability.handler({ datetime_utc: '2026-07-20T12:00:00Z' }, undefined)

    expect(result.is_error).toBe(false)
    // The old stub always returned is_error: true with the literal string
    // 'call_ephemeris_at_t is not yet wired to a compute sidecar endpoint' — assert
    // that string is categorically gone from a success-path response.
    expect(JSON.stringify(result.content)).not.toContain('not yet wired')
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(1)
    expect((content['positions'] as unknown[])[0]).toMatchObject({ planet: 'Sun', sign: 'Cancer' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('requires datetime_utc', async () => {
    const result = await callEphemerisAtTCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('reports a config error (not the old stub error) when PYTHON_SIDECAR_URL is unset', async () => {
    delete process.env.PYTHON_SIDECAR_URL
    const result = await callEphemerisAtTCapability.handler({ datetime_utc: '2026-07-20T12:00:00Z' }, undefined)
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>)['error'])).toContain('PYTHON_SIDECAR_URL not configured')
  })

  it('surfaces a sidecar non-OK response as an error, not a silent success', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 422, json: async () => ({ detail: 'bad ayanamsha' }) })))

    const result = await callEphemerisAtTCapability.handler({ datetime_utc: '2026-07-20T12:00:00Z' }, undefined)
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>)['error'])).toContain('422')
  })
})

describe('call_muhurta_score — no longer the dead stub', () => {
  it('forwards to POST {sidecar}/api/compute/muhurta_score and returns real-shaped score on success', async () => {
    process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
    process.env.PYTHON_SIDECAR_API_KEY = 'test-key'

    const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
      expect(url).toBe('http://sidecar.test/api/compute/muhurta_score')
      expect(JSON.parse(init.body as string)).toMatchObject({
        datetime_utc: '2026-07-20T12:00:00Z',
        event_class: 'vivah',
      })
      return {
        ok: true,
        status: 200,
        json: async () => ({
          datetime_utc: '2026-07-20T12:00:00Z',
          local_date: '2026-07-20',
          event_class: 'vivah',
          score: 64.0,
          stars: 3,
          panchang_context: { tithi: 'Shukla Saptami', nakshatra: 'Hasta', vara: 'Somavara', yoga: 'Shiva' },
        }),
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await callMuhurtaScoreCapability.handler({ datetime_utc: '2026-07-20T12:00:00Z', event_class: 'vivah' }, undefined)

    expect(result.is_error).toBe(false)
    expect(JSON.stringify(result.content)).not.toContain('not yet wired')
    const content = result.content as Record<string, unknown>
    expect(content['score']).toBe(64.0)
    expect(content['stars']).toBe(3)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('requires datetime_utc and event_class', async () => {
    const noDatetime = await callMuhurtaScoreCapability.handler({ event_class: 'vivah' }, undefined)
    expect(noDatetime.is_error).toBe(true)

    const noEvent = await callMuhurtaScoreCapability.handler({ datetime_utc: '2026-07-20T12:00:00Z' }, undefined)
    expect(noEvent.is_error).toBe(true)
  })

  it('descriptor event_class enum uses the real EVENTS_MVP vocabulary, not the old dead-stub marketing enum', () => {
    const enumValues = callMuhurtaScoreCapability.input_schema?.['event_class']?.enum
    expect(enumValues).toEqual([
      'vivah', 'griha_pravesh', 'vyapara', 'yatra',
      'property_purchase', 'mantra_initiation', 'upaya_ritual', 'sadhana_initiation',
    ])
    // the old stub-era enum values must be gone — they were never scoreable
    expect(enumValues).not.toContain('marriage')
    expect(enumValues).not.toContain('ceremony')
  })
})
