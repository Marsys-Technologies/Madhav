/**
 * ephemeris_sidecar_api_key.test.ts — ṢAḌ-DARŚANA Gate W1 verify-reopen, ROOT CAUSE A.
 * ============================================================================
 * `main.py` mounts the ENTIRE `/brahmagyan/ephemeris` router behind
 * `dependencies=[Depends(verify_api_key)]`, and `PYTHON_SIDECAR_API_KEY` is wired from Secret
 * Manager onto every deployed service (`.github/workflows/deploy.yml`). A capability handler
 * that omits the `x-api-key` header therefore 401s on EVERY production call.
 *
 * `query_planet_transit.ts` omitted it. Its `!res.ok` branch returned `{ ok: false, error,
 * count: 0, rows: [] }`, which reached `kala_now_get` / `kala_ahead_get` over HTTP 200 and was
 * read as a genuine empty — so all 9 grahas' transit fields were null on both canonical charts
 * while `coverage` asserted `state: "computed"`. The sibling `query_planet_position.ts` had this
 * exact defect found and fixed under WP-1.7 (LCA-1, LCA-12); the fix was never propagated to the
 * four siblings. This suite is the propagation guard.
 *
 * These capabilities read their env at MODULE SCOPE, so each case sets env and then
 * `vi.resetModules()` + dynamic-imports — otherwise the assertions would test whatever env
 * happened to be present when the module first loaded (a false-positive test, which is the very
 * defect class this file exists to prevent — CLAUDE.md §N.8).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const ORIGINAL_ENV = { ...process.env }

/** Every L0 capability that calls the API-key-protected /brahmagyan/ephemeris router. */
const EPHEMERIS_CAPABILITIES = [
  { module: '../query_planet_transit', exportName: 'queryPlanetTransitCapability', args: { planet: 'Jupiter', start_date: '2026-07-30', end_date: '2026-07-30' } },
  { module: '../query_planet_position', exportName: 'queryPlanetPositionCapability', args: { date: '2026-07-30', planet: 'Jupiter' } },
  { module: '../query_aspects_at_time', exportName: 'queryAspectsAtTimeCapability', args: { date: '2026-07-30' } },
  { module: '../query_retrograde_periods', exportName: 'queryRetrogradePeriodsCapability', args: { planet: 'Mercury', start_date: '2026-01-01', end_date: '2026-12-31' } },
] as const

beforeEach(() => {
  process.env.PYTHON_SIDECAR_URL = 'http://sidecar.test'
  process.env.PYTHON_SIDECAR_API_KEY = 'secret-key-123'
  vi.resetModules()
})

afterEach(() => {
  vi.unstubAllGlobals()
  process.env = { ...ORIGINAL_ENV }
})

describe('ROOT CAUSE A — every /brahmagyan/ephemeris capability forwards x-api-key', () => {
  for (const cap of EPHEMERIS_CAPABILITIES) {
    it(`${cap.exportName} sends x-api-key when PYTHON_SIDECAR_API_KEY is set`, async () => {
      const seen: Array<Record<string, string>> = []
      vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
        seen.push((init?.headers ?? {}) as Record<string, string>)
        return { ok: true, json: async () => ({ ok: true, rows: [], count: 0 }), text: async () => '' } as Response
      }))

      const mod = await import(cap.module) as Record<string, { handler: (a: Record<string, unknown>) => Promise<unknown> }>
      await mod[cap.exportName]!.handler({ ...cap.args })

      expect(seen.length, `${cap.exportName} made no fetch call`).toBeGreaterThan(0)
      for (const headers of seen) {
        expect(headers['x-api-key'], `${cap.exportName} omitted x-api-key — every production call would 401`).toBe('secret-key-123')
      }
    })

    it(`${cap.exportName} omits the header entirely when no key is configured (local bench)`, async () => {
      delete process.env.PYTHON_SIDECAR_API_KEY
      vi.resetModules()
      const seen: Array<Record<string, string>> = []
      vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
        seen.push((init?.headers ?? {}) as Record<string, string>)
        return { ok: true, json: async () => ({ ok: true, rows: [], count: 0 }), text: async () => '' } as Response
      }))

      const mod = await import(cap.module) as Record<string, { handler: (a: Record<string, unknown>) => Promise<unknown> }>
      await mod[cap.exportName]!.handler({ ...cap.args })

      expect(seen.length).toBeGreaterThan(0)
      expect(seen[0]!['x-api-key']).toBeUndefined()
    })
  }
})

describe('ROOT CAUSE A — a 401 is reported as a FAILURE, never as a high-confidence empty', () => {
  it('query_planet_transit surfaces an error + confidence:none on a 401, so a consumer can tell it apart from "no rows"', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: false, status: 401,
      text: async () => '{"detail":"Invalid API key"}',
      json: async () => ({ detail: 'Invalid API key' }),
    }) as unknown as Response))

    const { queryPlanetTransitCapability } = await import('../query_planet_transit')
    const result = await queryPlanetTransitCapability.handler(
      { planet: 'Jupiter', start_date: '2026-07-30', end_date: '2026-07-30' },
    ) as Record<string, unknown>

    // `rows: []` alone is ambiguous — these three fields are what make it unambiguous, and are
    // exactly what the serving facades now key their coverage claim off (CLAUDE.md §N.8).
    expect(result['ok']).toBe(false)
    expect(String(result['error'])).toContain('401')
    expect(result['confidence']).toBe('none')
    expect(result['rows']).toEqual([])
  })

  it('a sidecar that is unreachable (fetch throws) is also a failure, not an empty', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('ECONNREFUSED') }))

    const { queryPlanetTransitCapability } = await import('../query_planet_transit')
    const result = await queryPlanetTransitCapability.handler(
      { planet: 'Jupiter', start_date: '2026-07-30', end_date: '2026-07-30' },
    ) as Record<string, unknown>

    expect(result['ok']).toBe(false)
    expect(String(result['error'])).toContain('unreachable')
    expect(result['confidence']).toBe('none')
  })

  it('a healthy call passes the sidecar payload through verbatim (no re-shaping)', async () => {
    const payload = {
      ok: true, planet: 'Jupiter', count: 1,
      rows: [{ date: '2026-07-30', sign_number: 4, degree_in_sign: 12.401, nakshatra_number: 9, is_retrograde: false }],
    }
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => payload, text: async () => '' }) as Response))

    const { queryPlanetTransitCapability } = await import('../query_planet_transit')
    const result = await queryPlanetTransitCapability.handler(
      { planet: 'Jupiter', start_date: '2026-07-30', end_date: '2026-07-30' },
    )
    expect(result).toEqual(payload)
  })
})

describe('ROOT CAUSE A — the sidecar URL default matches the real local bench port', () => {
  it('defaults to :8000 (the port main.py binds), not the stale :8001', async () => {
    delete process.env.PYTHON_SIDECAR_URL
    vi.resetModules()
    let seenUrl = ''
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      seenUrl = String(url)
      return { ok: true, json: async () => ({ ok: true, rows: [], count: 0 }), text: async () => '' } as Response
    }))

    const { queryPlanetTransitCapability } = await import('../query_planet_transit')
    await queryPlanetTransitCapability.handler(
      { planet: 'Jupiter', start_date: '2026-07-30', end_date: '2026-07-30' },
    )
    // WP-1.7's own note: "the prior 8001 default silently missed the bench and contributed to
    // ephemeris 'returns nothing' symptoms locally."
    expect(seenUrl).toContain('localhost:8000')
    expect(seenUrl).not.toContain('8001')
  })
})
