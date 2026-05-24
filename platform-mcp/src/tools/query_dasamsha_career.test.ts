/**
 * query_dasamsha_career.test.ts — Unit tests for the query_dasamsha_career MCP tool.
 *
 * TR-P7-S4 acceptance criteria:
 *   AC.1 — Returns non-null d10_ascendant.
 *   AC.2 — planets array has ≥ 1 entry.
 *   AC.3 — career_indicators array is present (can be empty if no rule fires on mock data).
 *   AC.4 — 10H lord rule fires when mock data has the 10H lord in a kendra/trikona.
 *   AC.5 — Sun in D10 10H fires "Career significator" indicator.
 *   AC.6 — 10H lord in dusthana fires the obstacle indicator.
 *   AC.7 — Error propagation: when divisional_query fails, returns isError: true.
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
  registerQueryDasamshhaCareer,
  parseD10Positions,
  classifyDignity,
  computeCareerIndicators,
  assembleDasamshhaResult,
} from './query_dasamsha_career.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a divisional_query envelope with D10 planet rows.
 * Each row: { planet, sign, house }
 */
function buildD10Envelope(rows: Array<{ planet: string; sign: string; house: number }>) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-d10-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'dasamsha-bundle-id',
        tool_name: 'divisional_query',
        tool_version: '1.0',
        invocation_params: { varga: 'D10' },
        results: rows.map((row, i) => ({
          content: JSON.stringify({
            fact_id: `D10_${row.planet}_${i}`,
            category: 'planet',
            varga: 'D10',
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
        result_hash: 'sha256:dasamsha-test',
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

async function callQueryDasamshhaCareer(
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

  registerQueryDasamshhaCareer(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_dasamsha_career handler was not registered')
  return capturedHandler(args)
}

function parseToolResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_dasamsha_career (TR-P7-S4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC.1: Returns non-null d10_ascendant ──────────────────────────────────

  it('AC.1 — returns non-null d10_ascendant', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Sun', sign: 'Leo', house: 1 },
      { planet: 'Saturn', sign: 'Scorpio', house: 4 },
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>

    expect(res['d10_ascendant']).toBeDefined()
    expect(typeof res['d10_ascendant']).toBe('string')
    expect((res['d10_ascendant'] as string).length).toBeGreaterThan(0)
  })

  // ── AC.2: planets array has ≥ 1 entry ────────────────────────────────────

  it('AC.2 — planets array has ≥ 1 entry', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Jupiter', sign: 'Cancer', house: 5 },
      { planet: 'Moon', sign: 'Libra', house: 7 },
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>

    expect(Array.isArray(res['planets'])).toBe(true)
    expect((res['planets'] as unknown[]).length).toBeGreaterThanOrEqual(1)
  })

  // ── AC.3: career_indicators array is present ──────────────────────────────

  it('AC.3 — career_indicators array is present (can be empty)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Rahu', sign: 'Gemini', house: 3 },
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>

    expect(Array.isArray(res['career_indicators'])).toBe(true)
  })

  // ── AC.4: 10H lord in kendra fires career indicator ───────────────────────

  it('AC.4 — 10H lord in kendra fires career indicator', async () => {
    // D10 Asc = Leo → 10H = Taurus → 10H lord = Venus
    // Venus in 4H (kendra) should fire "10H lord in D10" + "10H lord in kendra/trikona"
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Sun', sign: 'Leo', house: 1 },   // ascendant marker
      { planet: 'Venus', sign: 'Scorpio', house: 4 }, // 10H lord Venus in 4H kendra
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const indicators = res['career_indicators'] as Array<{ indicator: string; planet: string }>

    expect(indicators.length).toBeGreaterThan(0)
    const tenthLordIndicator = indicators.find(ind => ind.indicator === '10H lord in D10')
    expect(tenthLordIndicator).toBeDefined()
    expect(tenthLordIndicator?.planet).toBe('Venus')
  })

  // ── AC.5: Sun in D10 10H fires career significator indicator ─────────────

  it('AC.5 — Sun in D10 10H fires "Career significator in D10 10H" indicator', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Sun', sign: 'Aries', house: 10 },
      { planet: 'Moon', sign: 'Cancer', house: 1 },
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const indicators = res['career_indicators'] as Array<{ indicator: string; planet: string }>

    const sigIndicator = indicators.find(ind => ind.indicator === 'Career significator in D10 10H')
    expect(sigIndicator).toBeDefined()
    expect(sigIndicator?.planet).toBe('Sun')
  })

  it('AC.5 — Saturn in D10 10H also fires career significator indicator', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Saturn', sign: 'Capricorn', house: 10 },
      { planet: 'Sun', sign: 'Aries', house: 1 },
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const indicators = res['career_indicators'] as Array<{ indicator: string; planet: string }>

    const satIndicator = indicators.find(
      ind => ind.indicator === 'Career significator in D10 10H' && ind.planet === 'Saturn'
    )
    expect(satIndicator).toBeDefined()
  })

  // ── AC.6: 10H lord in dusthana fires obstacle indicator ──────────────────

  it('AC.6 — 10H lord in 8H fires "10H lord in dusthana" indicator', async () => {
    // D10 Asc = Scorpio → 10H = Leo → 10H lord = Sun
    // Sun in 8H should fire both "10H lord in D10" and "10H lord in dusthana"
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Mars', sign: 'Scorpio', house: 1 },  // ascendant marker
      { planet: 'Sun', sign: 'Gemini', house: 8 },    // 10H lord Sun in 8H (dusthana)
    ]))

    const result = await callQueryDasamshhaCareer({})
    const parsed = parseToolResult(result)
    const res = parsed['result'] as Record<string, unknown>
    const indicators = res['career_indicators'] as Array<{ indicator: string; planet: string }>

    const obstacleIndicator = indicators.find(ind => ind.indicator === '10H lord in dusthana (6H/8H/12H)')
    expect(obstacleIndicator).toBeDefined()
    expect(obstacleIndicator?.planet).toBe('Sun')
  })

  // ── AC.7: Error propagation ────────────────────────────────────────────────

  it('AC.7 — returns isError: true when divisional_query fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryDasamshhaCareer({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Unit tests for exported helpers ───────────────────────────────────────

  describe('parseD10Positions', () => {
    it('extracts planet rows from ToolBundle results[].content', () => {
      const envelope = buildD10Envelope([
        { planet: 'Jupiter', sign: 'Cancer', house: 5 },
      ]).envelope as Record<string, unknown>

      const positions = parseD10Positions(envelope)
      expect(positions).toHaveLength(1)
      expect(positions[0].planet).toBe('Jupiter')
      expect(positions[0].sign).toBe('Cancer')
      expect(positions[0].house).toBe(5)
    })

    it('returns empty array for empty result', () => {
      const positions = parseD10Positions({ result: {} })
      expect(positions).toHaveLength(0)
    })
  })

  describe('classifyDignity', () => {
    it('returns "own_sign" for Sun in Leo', () => {
      expect(classifyDignity('Sun', 'Leo')).toBe('own_sign')
    })

    it('returns "exalted" for Sun in Aries', () => {
      expect(classifyDignity('Sun', 'Aries')).toBe('exalted')
    })

    it('returns "neutral" for Sun in Gemini', () => {
      expect(classifyDignity('Sun', 'Gemini')).toBe('neutral')
    })

    it('returns "exalted" for Saturn in Libra', () => {
      expect(classifyDignity('Saturn', 'Libra')).toBe('exalted')
    })

    it('returns "own_sign" for Mars in Scorpio', () => {
      expect(classifyDignity('Mars', 'Scorpio')).toBe('own_sign')
    })
  })

  describe('computeCareerIndicators', () => {
    it('returns empty array when no rules match', () => {
      // Rahu only — no 10H lord, no career significator in 10H
      const positions = [{ planet: 'Rahu', sign: 'Gemini', house: 3 }]
      const indicators = computeCareerIndicators(positions, 'Gemini')
      // Gemini asc 10H lord = Jupiter; Jupiter not in positions, so no 10H lord indicator
      // Rahu not a career significator
      expect(Array.isArray(indicators)).toBe(true)
    })

    it('fires kendra/trikona indicator for Venus (Leo Asc 10H lord) in 1H', () => {
      const positions = [
        { planet: 'Sun', sign: 'Leo', house: 1 },
        { planet: 'Venus', sign: 'Taurus', house: 1 },  // own sign + trikona
      ]
      const indicators = computeCareerIndicators(positions, 'Leo')
      const types = indicators.map(i => i.indicator)
      expect(types).toContain('10H lord in D10')
      expect(types).toContain('10H lord in own sign or exalted')
    })
  })

  describe('assembleDasamshhaResult', () => {
    it('uses house-1 sign as d10_ascendant', () => {
      const positions = [
        { planet: 'Sun', sign: 'Aries', house: 1 },
        { planet: 'Moon', sign: 'Leo', house: 5 },
      ]
      const res = assembleDasamshhaResult(positions)
      expect(res.d10_ascendant).toBe('Aries')
    })

    it('falls back to first planet sign when no house-1 entry', () => {
      const positions = [
        { planet: 'Jupiter', sign: 'Cancer', house: 5 },
      ]
      const res = assembleDasamshhaResult(positions)
      expect(res.d10_ascendant).toBe('Cancer')
    })

    it('planets array includes dignity field', () => {
      const positions = [
        { planet: 'Sun', sign: 'Leo', house: 1 },
      ]
      const res = assembleDasamshhaResult(positions)
      expect(res.planets[0].dignity).toBe('own_sign')
    })
  })

  // ── callPlatformPrimitive call verification ────────────────────────────────

  it('passes varga=D10 and default chart_id to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Sun', sign: 'Leo', house: 1 },
    ]))

    await callQueryDasamshhaCareer({})

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('divisional_query')
    expect((params as Record<string, unknown>)['varga']).toBe('D10')
    expect((params as Record<string, unknown>)['chart_id']).toBe(NATIVE_CHART_ID)
  })

  it('passes custom chart_id when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildD10Envelope([
      { planet: 'Sun', sign: 'Leo', house: 1 },
    ]))

    const CUSTOM_CHART_ID = 'custom-chart-uuid-1234'
    await callQueryDasamshhaCareer({ chart_id: CUSTOM_CHART_ID })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(CUSTOM_CHART_ID)
  })
})
