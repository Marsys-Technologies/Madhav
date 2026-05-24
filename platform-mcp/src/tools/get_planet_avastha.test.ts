/**
 * get_planet_avastha.test.ts — Unit tests for the get_planet_avastha MCP tool.
 *
 * TR-P6-S3 acceptance criteria:
 *   AC.1 — Mock avastha rows returning Jupiter row with avastha="Garvita".
 *           Verify avastha: "Garvita", source: "chart_facts".
 *   AC.2 — Mock returning 0 avastha rows; verify source is "computed" or
 *           "default_fallback" and avastha is one of the 6 valid values.
 *   AC.3 — avastha_meaning is a non-empty string.
 *   AC.4 — Zod rejects planet="Pluto".
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerGetPlanetAvastha, AVASTHA_MEANINGS } from './get_planet_avastha.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

const VALID_AVASTHAS = Object.keys(AVASTHA_MEANINGS)

/**
 * Build an envelope where chart_facts returns rows_by_category directly on result.
 * This mirrors the simplest platform response shape.
 */
function buildAvasthaEnvelope(avasthaRows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-avastha-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        rows_by_category: {
          avastha: avasthaRows,
        },
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

function buildDignityEnvelope(dignityRows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-dignity-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        rows_by_category: {
          dignity_scores: dignityRows,
        },
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

/**
 * Registers get_planet_avastha on a stub MCP server and invokes the handler
 * directly, with optional Zod validation.
 */
async function callGetPlanetAvastha(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
  applyZodValidation = false,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null
  let capturedSchema: Record<string, unknown> | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      schema: Record<string, unknown>,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
      capturedSchema = schema
    },
  } as unknown as McpServer

  registerGetPlanetAvastha(stubServer, () => principal)

  if (!capturedHandler) throw new Error('get_planet_avastha handler was not registered')

  if (applyZodValidation) {
    const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
    const zodSchema = z.object(schemaShape)
    const parseResult = zodSchema.safeParse(args)
    if (!parseResult.success) {
      return { zodError: parseResult.error, isZodError: true }
    }
    return capturedHandler(parseResult.data as Record<string, unknown>)
  }

  return capturedHandler(args)
}

function parseToolResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('get_planet_avastha (TR-P6-S3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC.1: chart_facts hit → avastha="Garvita", source="chart_facts" ────────

  it('AC.1 — Jupiter row with avastha=Garvita → returns avastha: "Garvita", source: "chart_facts"', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([
      { planet: 'Jupiter', category: 'avastha', value_text: 'Garvita', fact_id: 'AV.001' },
      { planet: 'Saturn', category: 'avastha', value_text: 'Kshudita', fact_id: 'AV.002' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Jupiter', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
    expect(parsed['planet']).toBe('Jupiter')
    expect(parsed['avastha']).toBe('Garvita')
    expect(parsed['source']).toBe('chart_facts')
  })

  it('AC.1 — is_natal is true when use_natal=true', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([
      { planet: 'Jupiter', category: 'avastha', value_text: 'Garvita', fact_id: 'AV.001' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Jupiter', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['is_natal']).toBe(true)
  })

  it('AC.1 — planet match is case-insensitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([
      { planet: 'jupiter', category: 'avastha', value_text: 'Mudita', fact_id: 'AV.003' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Jupiter', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['avastha']).toBe('Mudita')
    expect(parsed['source']).toBe('chart_facts')
  })

  // ── AC.2: 0 avastha rows → fallback path ──────────────────────────────────

  it('AC.2 — 0 avastha rows → source is "computed" or "default_fallback"', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    // First call: avastha rows = 0
    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([]))
    // Second call: dignity_scores with a row for Jupiter
    mockCall.mockResolvedValueOnce(buildDignityEnvelope([
      { planet: 'Jupiter', category: 'dignity_scores', value_text: 'exalted', fact_id: 'DIG.001' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Jupiter', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
    expect(['computed', 'default_fallback']).toContain(parsed['source'])
    expect(VALID_AVASTHAS).toContain(parsed['avastha'])
  })

  it('AC.2 — 0 avastha rows + 0 dignity rows → source is "default_fallback"', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    // First call: avastha rows = 0
    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([]))
    // Second call: dignity_scores = 0
    mockCall.mockResolvedValueOnce(buildDignityEnvelope([]))

    const result = await callGetPlanetAvastha({ planet: 'Mars', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
    expect(parsed['source']).toBe('default_fallback')
    expect(parsed['avastha']).toBe('Mudita')
    expect(VALID_AVASTHAS).toContain(parsed['avastha'])
  })

  it('AC.2 — dignity "debilitated" maps to avastha "Lajjita" (computed)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([]))
    mockCall.mockResolvedValueOnce(buildDignityEnvelope([
      { planet: 'Saturn', category: 'dignity_scores', value_text: 'debilitated', fact_id: 'DIG.002' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Saturn', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['avastha']).toBe('Lajjita')
    expect(parsed['source']).toBe('computed')
  })

  it('AC.2 — dignity "exalted" maps to avastha "Garvita" (computed)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([]))
    mockCall.mockResolvedValueOnce(buildDignityEnvelope([
      { planet: 'Sun', category: 'dignity_scores', value_text: 'exalted', fact_id: 'DIG.003' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Sun', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['avastha']).toBe('Garvita')
    expect(parsed['source']).toBe('computed')
  })

  // ── AC.3: avastha_meaning is a non-empty string ────────────────────────────

  it('AC.3 — avastha_meaning is a non-empty string (chart_facts hit)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([
      { planet: 'Venus', category: 'avastha', value_text: 'Mudita', fact_id: 'AV.004' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Venus', use_natal: true })
    const parsed = parseToolResult(result)

    expect(typeof parsed['avastha_meaning']).toBe('string')
    expect((parsed['avastha_meaning'] as string).length).toBeGreaterThan(0)
  })

  it('AC.3 — avastha_meaning is a non-empty string (default_fallback)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([]))
    mockCall.mockResolvedValueOnce(buildDignityEnvelope([]))

    const result = await callGetPlanetAvastha({ planet: 'Moon', use_natal: true })
    const parsed = parseToolResult(result)

    expect(typeof parsed['avastha_meaning']).toBe('string')
    expect((parsed['avastha_meaning'] as string).length).toBeGreaterThan(0)
  })

  it('AC.3 — all 6 AVASTHA_MEANINGS have non-empty string values', () => {
    for (const [avastha, meaning] of Object.entries(AVASTHA_MEANINGS)) {
      expect(typeof meaning).toBe('string')
      expect(meaning.length).toBeGreaterThan(0)
      expect(avastha.length).toBeGreaterThan(0)
    }
    expect(Object.keys(AVASTHA_MEANINGS)).toHaveLength(6)
  })

  // ── AC.4: Zod rejects planet="Pluto" ──────────────────────────────────────

  it('AC.4 — Zod rejects planet="Pluto"', async () => {
    const result = await callGetPlanetAvastha(
      { planet: 'Pluto', use_natal: true },
      mockPrincipal,
      true  // apply Zod validation
    )
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('AC.4 — Zod rejects planet="Neptune"', async () => {
    const result = await callGetPlanetAvastha(
      { planet: 'Neptune', use_natal: true },
      mockPrincipal,
      true
    )
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('AC.4 — Zod accepts all 9 valid planets', async () => {
    const validPlanets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    const mockCall = vi.mocked(callPlatformPrimitive)

    for (const planet of validPlanets) {
      vi.clearAllMocks()
      mockCall
        .mockResolvedValueOnce(buildAvasthaEnvelope([
          { planet, category: 'avastha', value_text: 'Mudita', fact_id: `AV.${planet}` },
        ]))

      const result = await callGetPlanetAvastha({ planet, use_natal: true }, mockPrincipal, true)
      expect((result as { isZodError?: boolean }).isZodError).toBeUndefined()
    }
  })

  // ── Error handling ─────────────────────────────────────────────────────────

  it('returns error result when first primitive call fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callGetPlanetAvastha({ planet: 'Jupiter', use_natal: true })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Source field integrity ─────────────────────────────────────────────────

  it('source is exactly "chart_facts" when avastha row found', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([
      { planet: 'Mars', category: 'avastha', value_text: 'Kshobhita', fact_id: 'AV.005' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Mars', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['source']).toBe('chart_facts')
  })

  it('source is exactly "computed" when dignity row provides inference', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildAvasthaEnvelope([]))
    mockCall.mockResolvedValueOnce(buildDignityEnvelope([
      { planet: 'Mercury', category: 'dignity_scores', value_text: 'own_sign', fact_id: 'DIG.004' },
    ]))

    const result = await callGetPlanetAvastha({ planet: 'Mercury', use_natal: true })
    const parsed = parseToolResult(result)

    expect(parsed['source']).toBe('computed')
  })
})
