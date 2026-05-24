/**
 * query_shashtiamsha.test.ts — Unit tests for the query_shashtiamsha MCP tool.
 *
 * TR-P7-S4 acceptance criteria:
 *   AC.1 — Returns planets array with ≥ 1 entry.
 *   AC.2 — Each planet has d60_pada_name (non-empty string).
 *   AC.3 — Pada calculation: planet at 7.5° in sign → pada = ceil(7.5/0.5) = 15
 *           → cycles to position ((15-1) % 12) + 1 = 3 → "Deva".
 *   AC.4 — Pada cycle: padas 1–12 have distinct names; pada 13 = pada 1 (Ghora).
 *   AC.5 — Planet at 0° → pada = 1 (Ghora).
 *   AC.6 — Error propagation: when divisional_query fails, returns isError: true.
 *   AC.7 — callPlatformPrimitive called with varga=D60.
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
  registerQueryShashtiamsha,
  calculatePada,
  resolvePadaEntry,
  parseD60Positions,
  assembleShashtiamshaResult,
  D60_PADA_NAMES,
} from './query_shashtiamsha.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a divisional_query envelope with D60 planet rows.
 * Each row: { planet, sign, house, longitude_in_sign }
 */
function buildD60Envelope(
  rows: Array<{ planet: string; sign: string; house: number; longitude_in_sign?: number }>,
) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-d60-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'medium', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'shashtiamsha-bundle-id',
        tool_name: 'divisional_query',
        tool_version: '1.0',
        invocation_params: { varga: 'D60' },
        results: rows.map((row, i) => ({
          content: JSON.stringify({
            fact_id: `D60_${row.planet}_${i}`,
            category: 'planet',
            varga: 'D60',
            value_text: `${row.planet} in ${row.sign}`,
            planet: row.planet,
            sign: row.sign,
            house: row.house,
            longitude_in_sign: row.longitude_in_sign ?? 0,
          }),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:shashtiamsha-test',
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
      trace_id: 'trace-fail-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

async function callQueryShashtiamsha(
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

  registerQueryShashtiamsha(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_shashtiamsha handler was not registered')
  return capturedHandler(args)
}

function parseToolResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_shashtiamsha (TR-P7-S4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC.1: Returns planets array with ≥ 1 entry ────────────────────────────

  it('AC.1 — returns planets array with ≥ 1 entry', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD60Envelope([
      { planet: 'Jupiter', sign: 'Leo', house: 5, longitude_in_sign: 14.5 },
    ]))

    const result = await callQueryShashtiamsha({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>

    expect(Array.isArray(res['planets'])).toBe(true)
    expect((res['planets'] as unknown[]).length).toBeGreaterThanOrEqual(1)
  })

  // ── AC.2: Each planet has d60_pada_name (non-empty string) ───────────────

  it('AC.2 — each planet has d60_pada_name as non-empty string', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD60Envelope([
      { planet: 'Sun', sign: 'Aries', house: 1, longitude_in_sign: 10.0 },
      { planet: 'Moon', sign: 'Cancer', house: 4, longitude_in_sign: 5.5 },
      { planet: 'Saturn', sign: 'Capricorn', house: 10, longitude_in_sign: 0.25 },
    ]))

    const result = await callQueryShashtiamsha({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const planets = res['planets'] as Array<Record<string, unknown>>

    for (const planet of planets) {
      expect(typeof planet['d60_pada_name']).toBe('string')
      expect((planet['d60_pada_name'] as string).length).toBeGreaterThan(0)
    }
  })

  // ── AC.3: Pada calculation — 7.5° → pada 15 → "Deva" ────────────────────

  it('AC.3 — planet at 7.5° in sign → pada 15 → "Deva"', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD60Envelope([
      { planet: 'Jupiter', sign: 'Leo', house: 5, longitude_in_sign: 7.5 },
    ]))

    const result = await callQueryShashtiamsha({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const planets = res['planets'] as Array<Record<string, unknown>>

    expect(planets[0]['d60_pada_number']).toBe(15)
    expect(planets[0]['d60_pada_name']).toBe('Deva')
  })

  it('AC.3 — calculatePada(7.5) returns 15', () => {
    expect(calculatePada(7.5)).toBe(15)
  })

  it('AC.3 — resolvePadaEntry(15) returns Deva', () => {
    const entry = resolvePadaEntry(15)
    expect(entry.name).toBe('Deva')
    // (15-1) % 12 + 1 = 14 % 12 + 1 = 2 + 1 = 3 → D60_PADA_NAMES[3] = Deva
  })

  // ── AC.4: Pada cycle — pada 13 = pada 1 (Ghora) ──────────────────────────

  it('AC.4 — pada 13 cycles to pada 1 name (Ghora)', () => {
    const entry13 = resolvePadaEntry(13)
    const entry1 = resolvePadaEntry(1)
    expect(entry13.name).toBe('Ghora')
    expect(entry13.name).toBe(entry1.name)
  })

  it('AC.4 — pada 24 cycles to pada 12 (Purishaka)', () => {
    const entry24 = resolvePadaEntry(24)
    const entry12 = resolvePadaEntry(12)
    expect(entry24.name).toBe('Purishaka')
    expect(entry24.name).toBe(entry12.name)
  })

  it('AC.4 — padas 1–12 all have distinct names', () => {
    const names = Object.values(D60_PADA_NAMES).map(e => e.name)
    const uniqueNames = new Set(names)
    expect(uniqueNames.size).toBe(12)
  })

  it('AC.4 — pada 60 cycles to pada 12 (Purishaka)', () => {
    const entry60 = resolvePadaEntry(60)
    // (60-1) % 12 + 1 = 59 % 12 + 1 = 11 + 1 = 12 → Purishaka
    expect(entry60.name).toBe('Purishaka')
  })

  it('AC.4 — pada 25 cycles to pada 1 (Ghora)', () => {
    // (25-1) % 12 + 1 = 24 % 12 + 1 = 0 + 1 = 1 → Ghora
    const entry25 = resolvePadaEntry(25)
    expect(entry25.name).toBe('Ghora')
  })

  // ── AC.5: Planet at 0° → pada 1 ──────────────────────────────────────────

  it('AC.5 — planet at 0° in sign → pada 1 (Ghora)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD60Envelope([
      { planet: 'Mars', sign: 'Aries', house: 1, longitude_in_sign: 0 },
    ]))

    const result = await callQueryShashtiamsha({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const planets = res['planets'] as Array<Record<string, unknown>>

    expect(planets[0]['d60_pada_number']).toBe(1)
    expect(planets[0]['d60_pada_name']).toBe('Ghora')
  })

  it('AC.5 — calculatePada(0) returns 1', () => {
    expect(calculatePada(0)).toBe(1)
  })

  it('AC.5 — calculatePada(-0.1) returns 1 (clamped)', () => {
    expect(calculatePada(-0.1)).toBe(1)
  })

  // ── AC.6: Error propagation ────────────────────────────────────────────────

  it('AC.6 — returns isError: true when divisional_query fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryShashtiamsha({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── AC.7: callPlatformPrimitive called with varga=D60 ─────────────────────

  it('AC.7 — passes varga=D60 and default chart_id to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
    mockCall.mockResolvedValue(buildD60Envelope([
      { planet: 'Sun', sign: 'Leo', house: 1, longitude_in_sign: 5.0 },
    ]))

    await callQueryShashtiamsha({})

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('divisional_query')
    expect((params as Record<string, unknown>)['varga']).toBe('D60')
    expect((params as Record<string, unknown>)['chart_id']).toBe(NATIVE_CHART_ID)
  })

  it('passes custom chart_id when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD60Envelope([
      { planet: 'Sun', sign: 'Leo', house: 1, longitude_in_sign: 5.0 },
    ]))

    const CUSTOM_CHART_ID = 'custom-chart-uuid-5678'
    await callQueryShashtiamsha({ chart_id: CUSTOM_CHART_ID })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(CUSTOM_CHART_ID)
  })

  // ── Unit tests for exported helpers ───────────────────────────────────────

  describe('calculatePada', () => {
    it('0.5° → pada 1', () => { expect(calculatePada(0.5)).toBe(1) })
    it('0.51° → pada 2', () => { expect(calculatePada(0.51)).toBe(2) })
    it('1.0° → pada 2', () => { expect(calculatePada(1.0)).toBe(2) })
    it('29.5° → pada 59', () => { expect(calculatePada(29.5)).toBe(59) })
    it('30.0° → pada 60', () => { expect(calculatePada(30.0)).toBe(60) })
    it('15.0° → pada 30', () => { expect(calculatePada(15.0)).toBe(30) })
  })

  describe('resolvePadaEntry', () => {
    it('pada 1 → Ghora', () => { expect(resolvePadaEntry(1).name).toBe('Ghora') })
    it('pada 9 → Garuda', () => { expect(resolvePadaEntry(9).name).toBe('Garuda') })
    it('pada 12 → Purishaka', () => { expect(resolvePadaEntry(12).name).toBe('Purishaka') })
    it('pada 13 → Ghora (cycle restart)', () => { expect(resolvePadaEntry(13).name).toBe('Ghora') })
    it('pada 21 → Garuda (2nd cycle)', () => { expect(resolvePadaEntry(21).name).toBe('Garuda') })
    it('pada 33 → Garuda (3rd cycle)', () => { expect(resolvePadaEntry(33).name).toBe('Garuda') })
    it('all entries have non-empty name and interpretation', () => {
      for (let i = 1; i <= 60; i++) {
        const entry = resolvePadaEntry(i)
        expect(entry.name.length).toBeGreaterThan(0)
        expect(entry.interpretation.length).toBeGreaterThan(0)
      }
    })
  })

  describe('parseD60Positions', () => {
    it('extracts planet rows from ToolBundle results[].content', () => {
      const envelope = buildD60Envelope([
        { planet: 'Venus', sign: 'Taurus', house: 2, longitude_in_sign: 12.5 },
      ]).envelope as Record<string, unknown>

      const positions = parseD60Positions(envelope)
      expect(positions).toHaveLength(1)
      expect(positions[0].planet).toBe('Venus')
      expect(positions[0].sign).toBe('Taurus')
      expect(positions[0].house).toBe(2)
      expect(positions[0].longitude_in_sign).toBe(12.5)
    })

    it('returns empty array for empty result', () => {
      const positions = parseD60Positions({ result: {} })
      expect(positions).toHaveLength(0)
    })

    it('returns empty array for no-result envelope', () => {
      const positions = parseD60Positions({})
      expect(positions).toHaveLength(0)
    })
  })

  describe('assembleShashtiamshaResult', () => {
    it('assembles correct d60_pada_name from longitude_in_sign', () => {
      const positions = [
        { planet: 'Jupiter', sign: 'Leo', house: 5, longitude_in_sign: 7.5 },
      ]
      const res = assembleShashtiamshaResult(positions)
      expect(res.planets[0].d60_pada_name).toBe('Deva')
      expect(res.planets[0].d60_pada_number).toBe(15)
    })

    it('includes all required fields in each planet record', () => {
      const positions = [
        { planet: 'Mars', sign: 'Aries', house: 1, longitude_in_sign: 3.0 },
      ]
      const res = assembleShashtiamshaResult(positions)
      const p = res.planets[0]
      expect(p.planet).toBe('Mars')
      expect(p.d60_sign).toBe('Aries')
      expect(p.d60_house).toBe(1)
      expect(p.d60_longitude_in_sign).toBe(3.0)
      expect(typeof p.d60_pada_number).toBe('number')
      expect(typeof p.d60_pada_name).toBe('string')
      expect(typeof p.d60_interpretation).toBe('string')
    })

    it('handles empty positions array', () => {
      const res = assembleShashtiamshaResult([])
      expect(res.planets).toHaveLength(0)
    })
  })

  // ── D60_PADA_NAMES completeness ────────────────────────────────────────────

  it('D60_PADA_NAMES has exactly 12 entries', () => {
    expect(Object.keys(D60_PADA_NAMES)).toHaveLength(12)
  })

  it('D60_PADA_NAMES keys are 1–12', () => {
    for (let i = 1; i <= 12; i++) {
      expect(D60_PADA_NAMES[i]).toBeDefined()
    }
  })

  it('D60_PADA_NAMES[3] is Deva (referenced in AC.3)', () => {
    expect(D60_PADA_NAMES[3]!.name).toBe('Deva')
  })
})
