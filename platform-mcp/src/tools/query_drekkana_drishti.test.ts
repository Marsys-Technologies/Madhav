/**
 * query_drekkana_drishti.test.ts — Unit tests for the query_drekkana_drishti MCP tool.
 *
 * Session: TR-P7-S1
 *
 * Acceptance criteria:
 *   TC.1 — query_drekkana_drishti({}) returns a non-empty planets array.
 *   TC.2 — Each planet in the response has drekkana_sign, drekkana_house, drishti_targets.
 *   TC.3 — Moveable sign aspects: all signs except 2nd and 12th from itself.
 *   TC.4 — Fixed sign aspects: exactly the other 3 fixed signs.
 *   TC.5 — Dual sign aspects: exactly the other 3 dual signs.
 *   TC.6 — Mutual drishti pairs are correctly identified.
 *   TC.7 — planet_in_sign is set when a planet occupies the aspected sign, null otherwise.
 *   TC.8 — Error propagation: when divisional_query fails, returns isError: true.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import {
  registerQueryDrekkanaDisthi,
  computeDrekkanaAspects,
  computeDrekkanaResults,
  signIndex,
  signFromIndex,
  SIGN_TYPE_MAP,
  SIGNS,
} from './query_drekkana_drishti.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a divisional_query envelope with the given D3 planet rows.
 * Each row: { planet, sign, house }
 */
function buildD3Envelope(rows: Array<{ planet: string; sign: string; house: number }>) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-d3-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'drekkana-bundle-id',
        tool_name: 'divisional_query',
        tool_version: '1.0',
        invocation_params: { varga: 'D3' },
        results: rows.map((row, i) => ({
          content: JSON.stringify({
            fact_id: `D3_${row.planet}_${i}`,
            category: 'planet',
            varga: 'D3',
            value_text: `${row.planet} in ${row.sign}`,
            planet: row.planet,
            sign: row.sign,
            house: row.house,
          }),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:drekkana-test',
        schema_version: '1.0',
      },
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-error-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/** Sample D3 positions covering all three sign types. */
const SAMPLE_D3_POSITIONS = [
  { planet: 'Jupiter', sign: 'Aries',  house: 1 },  // moveable
  { planet: 'Sun',     sign: 'Leo',    house: 5 },  // fixed
  { planet: 'Mercury', sign: 'Gemini', house: 3 },  // dual
  { planet: 'Moon',    sign: 'Cancer', house: 4 },  // moveable
  { planet: 'Saturn',  sign: 'Aquarius', house: 11 }, // fixed
]

/** Call the MCP handler via a stub server. */
async function callQueryDrekkana(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      _schema: unknown,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
    },
  } as unknown as McpServer

  registerQueryDrekkanaDisthi(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_drekkana_drishti handler was not registered')
  return capturedHandler(args)
}

/** Parse the content text from a handler result. */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Pure computation tests ────────────────────────────────────────────────────

describe('Drekkana Drishti pure computation', () => {
  describe('signIndex and signFromIndex', () => {
    it('Aries has index 1', () => {
      expect(signIndex('Aries')).toBe(1)
    })

    it('Pisces has index 12', () => {
      expect(signIndex('Pisces')).toBe(12)
    })

    it('unknown sign returns 0', () => {
      expect(signIndex('UnknownSign')).toBe(0)
    })

    it('signFromIndex(1) returns Aries', () => {
      expect(signFromIndex(1)).toBe('Aries')
    })

    it('signFromIndex wraps around correctly', () => {
      // 12 + 1 = 13 → 1 → Aries
      expect(signFromIndex(13)).toBe('Aries')
    })
  })

  describe('SIGN_TYPE_MAP', () => {
    it('Aries, Cancer, Libra, Capricorn are moveable', () => {
      expect(SIGN_TYPE_MAP['Aries']).toBe('moveable')
      expect(SIGN_TYPE_MAP['Cancer']).toBe('moveable')
      expect(SIGN_TYPE_MAP['Libra']).toBe('moveable')
      expect(SIGN_TYPE_MAP['Capricorn']).toBe('moveable')
    })

    it('Taurus, Leo, Scorpio, Aquarius are fixed', () => {
      expect(SIGN_TYPE_MAP['Taurus']).toBe('fixed')
      expect(SIGN_TYPE_MAP['Leo']).toBe('fixed')
      expect(SIGN_TYPE_MAP['Scorpio']).toBe('fixed')
      expect(SIGN_TYPE_MAP['Aquarius']).toBe('fixed')
    })

    it('Gemini, Virgo, Sagittarius, Pisces are dual', () => {
      expect(SIGN_TYPE_MAP['Gemini']).toBe('dual')
      expect(SIGN_TYPE_MAP['Virgo']).toBe('dual')
      expect(SIGN_TYPE_MAP['Sagittarius']).toBe('dual')
      expect(SIGN_TYPE_MAP['Pisces']).toBe('dual')
    })
  })

  describe('computeDrekkanaAspects', () => {
    // TC.3 — Moveable sign
    it('TC.3 — Aries (moveable) aspects 9 signs (all except 2nd=Taurus, 12th=Pisces, itself)', () => {
      const aspects = computeDrekkanaAspects('Aries')
      // 12 signs - 3 (itself + 2nd + 12th) = 9
      expect(aspects).toHaveLength(9)
      expect(aspects).not.toContain('Aries')   // itself
      expect(aspects).not.toContain('Taurus')  // 2nd from Aries
      expect(aspects).not.toContain('Pisces')  // 12th from Aries
    })

    it('TC.3 — Cancer (moveable) aspects all except Leo (2nd) and Gemini (12th)', () => {
      const aspects = computeDrekkanaAspects('Cancer')
      expect(aspects).not.toContain('Cancer')
      expect(aspects).not.toContain('Leo')     // 2nd from Cancer
      expect(aspects).not.toContain('Gemini')  // 12th from Cancer
      expect(aspects).toHaveLength(9)
    })

    it('TC.3 — Libra (moveable) excludes Scorpio (2nd) and Virgo (12th)', () => {
      const aspects = computeDrekkanaAspects('Libra')
      expect(aspects).not.toContain('Libra')
      expect(aspects).not.toContain('Scorpio')
      expect(aspects).not.toContain('Virgo')
      expect(aspects).toHaveLength(9)
    })

    it('TC.3 — Capricorn (moveable) excludes Aquarius (2nd) and Sagittarius (12th)', () => {
      const aspects = computeDrekkanaAspects('Capricorn')
      expect(aspects).not.toContain('Capricorn')
      expect(aspects).not.toContain('Aquarius')
      expect(aspects).not.toContain('Sagittarius')
      expect(aspects).toHaveLength(9)
    })

    // TC.4 — Fixed sign
    it('TC.4 — Taurus (fixed) aspects exactly Leo, Scorpio, Aquarius', () => {
      const aspects = computeDrekkanaAspects('Taurus')
      expect(aspects).toHaveLength(3)
      expect(aspects).toContain('Leo')
      expect(aspects).toContain('Scorpio')
      expect(aspects).toContain('Aquarius')
      expect(aspects).not.toContain('Taurus')
    })

    it('TC.4 — Leo (fixed) aspects Taurus, Scorpio, Aquarius', () => {
      const aspects = computeDrekkanaAspects('Leo')
      expect(aspects).toHaveLength(3)
      expect(aspects).toContain('Taurus')
      expect(aspects).toContain('Scorpio')
      expect(aspects).toContain('Aquarius')
    })

    it('TC.4 — Scorpio (fixed) aspects Taurus, Leo, Aquarius', () => {
      const aspects = computeDrekkanaAspects('Scorpio')
      expect(aspects).toHaveLength(3)
      expect(aspects).toContain('Taurus')
      expect(aspects).toContain('Leo')
      expect(aspects).toContain('Aquarius')
    })

    // TC.5 — Dual sign
    it('TC.5 — Gemini (dual) aspects exactly Virgo, Sagittarius, Pisces', () => {
      const aspects = computeDrekkanaAspects('Gemini')
      expect(aspects).toHaveLength(3)
      expect(aspects).toContain('Virgo')
      expect(aspects).toContain('Sagittarius')
      expect(aspects).toContain('Pisces')
      expect(aspects).not.toContain('Gemini')
    })

    it('TC.5 — Pisces (dual) aspects Gemini, Virgo, Sagittarius', () => {
      const aspects = computeDrekkanaAspects('Pisces')
      expect(aspects).toHaveLength(3)
      expect(aspects).toContain('Gemini')
      expect(aspects).toContain('Virgo')
      expect(aspects).toContain('Sagittarius')
    })

    it('returns empty array for unknown sign', () => {
      const aspects = computeDrekkanaAspects('UnknownSign')
      expect(aspects).toHaveLength(0)
    })
  })

  describe('computeDrekkanaResults', () => {
    // TC.6 — Mutual drishti
    it('TC.6 — detects mutual drishti between two moveable signs that aspect each other', () => {
      // Aries (moveable) aspects Cancer (it aspects 9 signs excl Taurus+Pisces, includes Cancer)
      // Cancer (moveable) aspects Aries (it aspects 9 signs excl Leo+Gemini, includes Aries)
      const positions = [
        { planet: 'Jupiter', sign: 'Aries', house: 1 },
        { planet: 'Moon',    sign: 'Cancer', house: 4 },
      ]
      const result = computeDrekkanaResults(positions)
      expect(result.mutual_drekkana_drishti).toHaveLength(1)
      const mutual = result.mutual_drekkana_drishti[0]
      expect([mutual.planet_a, mutual.planet_b]).toContain('Jupiter')
      expect([mutual.planet_a, mutual.planet_b]).toContain('Moon')
    })

    it('TC.6 — two fixed signs always have mutual drishti', () => {
      // Taurus aspects Leo; Leo aspects Taurus → mutual
      const positions = [
        { planet: 'Venus', sign: 'Taurus', house: 2 },
        { planet: 'Sun',   sign: 'Leo',    house: 5 },
      ]
      const result = computeDrekkanaResults(positions)
      const mutual = result.mutual_drekkana_drishti
      expect(mutual.length).toBeGreaterThan(0)
    })

    it('TC.6 — two dual signs always have mutual drishti', () => {
      const positions = [
        { planet: 'Mercury',   sign: 'Gemini',      house: 3 },
        { planet: 'Jupiter', sign: 'Sagittarius', house: 9 },
      ]
      const result = computeDrekkanaResults(positions)
      const mutual = result.mutual_drekkana_drishti
      expect(mutual.length).toBeGreaterThan(0)
    })

    // TC.7 — planet_in_sign
    it('TC.7 — planet_in_sign is set when a planet occupies the aspected sign', () => {
      // Aries (moveable) aspects Libra (not excluded)
      // Place Venus in Libra → Jupiter in Aries should see Venus at Libra target
      const positions = [
        { planet: 'Jupiter', sign: 'Aries', house: 1 },
        { planet: 'Venus',   sign: 'Libra', house: 7 },
      ]
      const result = computeDrekkanaResults(positions)
      const jupiter = result.planets.find(p => p.planet === 'Jupiter')
      expect(jupiter).toBeDefined()
      const libraTarget = jupiter!.drishti_targets.find(t => t.sign === 'Libra')
      expect(libraTarget).toBeDefined()
      expect(libraTarget!.planet_in_sign).toBe('Venus')
    })

    it('TC.7 — planet_in_sign is null when no planet in aspected sign', () => {
      // Jupiter in Aries; empty Libra
      const positions = [
        { planet: 'Jupiter', sign: 'Aries', house: 1 },
      ]
      const result = computeDrekkanaResults(positions)
      const jupiter = result.planets.find(p => p.planet === 'Jupiter')
      const libraTarget = jupiter!.drishti_targets.find(t => t.sign === 'Libra')
      // Libra is aspected by Aries (moveable, not 2nd or 12th)
      expect(libraTarget).toBeDefined()
      expect(libraTarget!.planet_in_sign).toBeNull()
    })

    it('aspect_strength is 1.0 for all in-sign drishti targets', () => {
      const positions = [{ planet: 'Sun', sign: 'Leo', house: 5 }]
      const result = computeDrekkanaResults(positions)
      const sun = result.planets.find(p => p.planet === 'Sun')
      sun!.drishti_targets.forEach(t => {
        expect(t.aspect_strength).toBe(1.0)
      })
    })

    it('returns correct sign_type for each planet', () => {
      const positions = [
        { planet: 'Jupiter', sign: 'Aries', house: 1 },  // moveable
        { planet: 'Sun',     sign: 'Leo',   house: 5 },  // fixed
        { planet: 'Mercury', sign: 'Gemini', house: 3 }, // dual
      ]
      const result = computeDrekkanaResults(positions)
      expect(result.planets.find(p => p.planet === 'Jupiter')!.sign_type).toBe('moveable')
      expect(result.planets.find(p => p.planet === 'Sun')!.sign_type).toBe('fixed')
      expect(result.planets.find(p => p.planet === 'Mercury')!.sign_type).toBe('dual')
    })
  })
})

// ── MCP handler tests ─────────────────────────────────────────────────────────

describe('query_drekkana_drishti MCP tool (TR-P7-S1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // TC.1 — non-empty planets array
  it('TC.1 — returns a non-empty planets array', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    const res = envelope['result'] as Record<string, unknown>
    const planets = res['planets'] as unknown[]
    expect(Array.isArray(planets)).toBe(true)
    expect(planets.length).toBeGreaterThan(0)
  })

  // TC.2 — each planet has drekkana_sign, drekkana_house, drishti_targets
  it('TC.2 — each planet in response has drekkana_sign, drekkana_house, drishti_targets', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>
    const planets = res['planets'] as Array<Record<string, unknown>>

    for (const planet of planets) {
      expect(planet['planet']).toBeDefined()
      expect(planet['drekkana_sign']).toBeDefined()
      expect(typeof planet['drekkana_house']).toBe('number')
      expect(Array.isArray(planet['drishti_targets'])).toBe(true)
    }
  })

  // TC.2 — sign_type is present
  it('TC.2 — each planet has sign_type (moveable/fixed/dual)', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>
    const planets = res['planets'] as Array<Record<string, unknown>>

    for (const planet of planets) {
      expect(['moveable', 'fixed', 'dual']).toContain(planet['sign_type'])
    }
  })

  // TC.2 — drishti_targets each have sign, planet_in_sign, aspect_strength
  it('TC.2 — drishti_targets have sign, planet_in_sign, aspect_strength fields', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>
    const planets = res['planets'] as Array<Record<string, unknown>>

    for (const planet of planets) {
      const targets = planet['drishti_targets'] as Array<Record<string, unknown>>
      for (const target of targets) {
        expect(SIGNS).toContain(target['sign'])
        // planet_in_sign can be null or a string
        expect(typeof target['planet_in_sign'] === 'string' || target['planet_in_sign'] === null).toBe(true)
        expect(target['aspect_strength']).toBe(1.0)
      }
    }
  })

  // TC.8 — error propagation
  it('TC.8 — returns isError:true when divisional_query fails', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryDrekkana({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // Additional: divisional_query is called with varga=D3
  it('calls divisional_query with varga="D3"', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    await callQueryDrekkana({})

    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('divisional_query')
    expect((params as Record<string, unknown>)['varga']).toBe('D3')
  })

  // Additional: defaults chart_id to native's chart
  it('defaults chart_id to native chart UUID', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    await callQueryDrekkana({})

    const [, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect((params as Record<string, unknown>)['chart_id']).toBe(
      '362f9f17-95a5-490b-a5a7-027d3e0efda0'
    )
  })

  // Additional: mutual_drekkana_drishti is present in result
  it('mutual_drekkana_drishti is present in result', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>

    expect(Array.isArray(res['mutual_drekkana_drishti'])).toBe(true)
  })

  // Additional: meta fields present
  it('response contains meta with planets_found count', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope(SAMPLE_D3_POSITIONS))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)
    const meta = envelope['meta'] as Record<string, unknown>

    expect(meta).toBeDefined()
    expect(meta['division']).toBe('D3')
    expect(meta['planets_found']).toBe(SAMPLE_D3_POSITIONS.length)
  })

  // Additional: empty D3 (no positions) → planets: []
  it('handles empty D3 response gracefully', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildD3Envelope([]))

    const result = await callQueryDrekkana({})
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    const res = envelope['result'] as Record<string, unknown>
    expect((res['planets'] as unknown[]).length).toBe(0)
  })
})
