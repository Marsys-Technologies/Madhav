/**
 * query_transits_over_natal.test.ts — Unit tests for the query_transits_over_natal MCP tool.
 *
 * TR-P6-S1: 8 acceptance criteria tests.
 *
 *   T1 — conjunction event detected (Jupiter at 245.5/245.3 within 1° of natal Moon 245.7)
 *   T2 — natal_longitude is 245.7 in the response
 *   T3 — total_events equals transit_events.length
 *   T4 — transit_planets filter: only Jupiter appears when Saturn is out of orb
 *   T5 — Zod rejects orb_degrees: 0 (below 0.1 minimum)
 *   T6 — Zod rejects orb_degrees: 11 (above 10 maximum)
 *   T7 — empty natal_positions rows → tool returns an error (not a crash)
 *   T8 — empty ephemeris positions → transit_events is [] and total_events is 0
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
import { registerQueryTransitsOverNatal } from './query_transits_over_natal.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a ToolBundle-style envelope for chart_facts (natal_positions).
 * The content JSON is what unwrapToolBundle will parse.
 */
function buildChartFactsEnvelope(rows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-cf-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        tool_bundle_id: 'cf-bundle-id',
        tool_name: 'query_chart_facts',
        results: [
          {
            content: JSON.stringify({ rows }),
            source_canonical_id: 'CHART_FACTS',
            confidence: 1.0,
          },
        ],
        served_from_cache: false,
        latency_ms: 5,
      },
      citations: [],
      plan: null,
      predictions_logged: [],
    },
  }
}

/**
 * Build a ToolBundle-style envelope for query_ephemeris.
 * positions is the flat array of {date, planet, longitude} objects.
 */
function buildEphemerisEnvelope(positions: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-eph-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        tool_bundle_id: 'eph-bundle-id',
        tool_name: 'query_ephemeris',
        results: [
          {
            content: JSON.stringify({ positions }),
            source_canonical_id: 'EPHEMERIS_DAILY',
            confidence: 1.0,
          },
        ],
        served_from_cache: false,
        latency_ms: 10,
      },
      citations: [],
      plan: null,
      predictions_logged: [],
    },
  }
}

/** Build an error envelope from the platform. */
function buildErrorEnvelope(message = 'DB error') {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-err-001',
      error: { class: 'internal', message },
    },
  }
}

/**
 * Register the tool on a stub MCP server and invoke the handler with Zod validation.
 */
async function callQueryTransitsOverNatal(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
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

  registerQueryTransitsOverNatal(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_transits_over_natal handler was not registered')

  // Simulate Zod validation as the MCP SDK would
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

/** Parse MCP content text from an okResult or errorResult. */
function parseContent(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Common mock data ──────────────────────────────────────────────────────────

// natal Moon at 245.7°
const natalMoonRows = [
  { planet: 'Moon', longitude: 245.7 },
]

// Jupiter in-orb on two consecutive days (245.5 and 245.3 — both within 1° of 245.7)
const jupiterInOrbPositions = [
  { date: '2026-07-15', planet: 'Jupiter', longitude: 245.5 },
  { date: '2026-07-16', planet: 'Jupiter', longitude: 245.3 },
]

// Default base args
const baseArgs = {
  date_range: { from: '2026-07-01', to: '2026-07-31' },
  target_natal_point: 'natal_moon',
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_transits_over_natal (TR-P6-S1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── T1: Jupiter conjunction detected ────────────────────────────────────────

  it('T1 — detects Jupiter conjunction event when Jupiter is within 1° orb of natal Moon', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    // call 1: chart_facts (natal_positions)
    mock.mockResolvedValueOnce(buildChartFactsEnvelope(natalMoonRows))
    // call 2: query_ephemeris
    mock.mockResolvedValueOnce(buildEphemerisEnvelope(jupiterInOrbPositions))

    const result = await callQueryTransitsOverNatal(baseArgs)

    expect((result as { isError?: boolean }).isError).toBeFalsy()
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(true)

    const events = parsed['transit_events'] as Array<Record<string, unknown>>
    expect(events.length).toBeGreaterThan(0)

    const jupiterConjunction = events.find(
      e => e['transit_planet'] === 'Jupiter' && e['aspect_type'] === 'conjunction',
    )
    expect(jupiterConjunction).toBeDefined()
    expect(jupiterConjunction!['date_entered_orb']).toBe('2026-07-15')
  })

  // ── T2: natal_longitude is 245.7 ────────────────────────────────────────────

  it('T2 — natal_longitude in response matches the fetched natal position (245.7)', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildChartFactsEnvelope(natalMoonRows))
    mock.mockResolvedValueOnce(buildEphemerisEnvelope(jupiterInOrbPositions))

    const result = await callQueryTransitsOverNatal(baseArgs)
    const parsed = parseContent(result)

    expect(parsed['natal_longitude']).toBe(245.7)
  })

  // ── T3: total_events equals transit_events.length ───────────────────────────

  it('T3 — total_events equals transit_events.length', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildChartFactsEnvelope(natalMoonRows))
    mock.mockResolvedValueOnce(buildEphemerisEnvelope(jupiterInOrbPositions))

    const result = await callQueryTransitsOverNatal(baseArgs)
    const parsed = parseContent(result)

    const events = parsed['transit_events'] as unknown[]
    expect(parsed['total_events']).toBe(events.length)
  })

  // ── T4: transit_planets filter ───────────────────────────────────────────────

  it('T4 — transit_planets: ["Jupiter"] filter excludes out-of-orb Saturn', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildChartFactsEnvelope(natalMoonRows))

    // Ephemeris has both Jupiter (in orb) and Saturn (far from natal Moon)
    const positions = [
      { date: '2026-07-15', planet: 'Jupiter', longitude: 245.5 },
      { date: '2026-07-15', planet: 'Saturn', longitude: 100.0 },  // far from 245.7
    ]
    mock.mockResolvedValueOnce(buildEphemerisEnvelope(positions))

    const result = await callQueryTransitsOverNatal({
      ...baseArgs,
      transit_planets: ['Jupiter'],
    })

    const parsed = parseContent(result)
    const events = parsed['transit_events'] as Array<Record<string, unknown>>

    // Only Jupiter should appear — Saturn is both filtered out AND out of orb
    expect(events.every(e => e['transit_planet'] === 'Jupiter')).toBe(true)
    expect(events.some(e => e['transit_planet'] === 'Saturn')).toBe(false)
  })

  // ── T5: Zod rejects orb_degrees: 0 ─────────────────────────────────────────

  it('T5 — Zod rejects orb_degrees: 0 (below 0.1 minimum)', async () => {
    const result = await callQueryTransitsOverNatal({
      ...baseArgs,
      orb_degrees: 0,
    })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  // ── T6: Zod rejects orb_degrees: 11 ─────────────────────────────────────────

  it('T6 — Zod rejects orb_degrees: 11 (above 10 maximum)', async () => {
    const result = await callQueryTransitsOverNatal({
      ...baseArgs,
      orb_degrees: 11,
    })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  // ── T7: empty natal rows → error ────────────────────────────────────────────

  it('T7 — returns error when natal_positions and fallback both return empty rows (no crash)', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    // Primary natal_positions call returns empty rows
    mock.mockResolvedValueOnce(buildChartFactsEnvelope([]))
    // Fallback planet_positions/lagna call also returns empty rows
    mock.mockResolvedValueOnce(buildChartFactsEnvelope([]))

    const result = await callQueryTransitsOverNatal(baseArgs)

    expect((result as { isError: boolean }).isError).toBe(true)
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(false)
    expect(parsed['error']).toBe('natal_longitude_not_found')
  })

  // ── T8: empty ephemeris → transit_events [] and total_events 0 ──────────────

  it('T8 — empty ephemeris positions → transit_events is [] and total_events is 0', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildChartFactsEnvelope(natalMoonRows))
    mock.mockResolvedValueOnce(buildEphemerisEnvelope([]))  // no positions

    const result = await callQueryTransitsOverNatal(baseArgs)

    expect((result as { isError?: boolean }).isError).toBeFalsy()
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(true)
    expect(parsed['transit_events']).toEqual([])
    expect(parsed['total_events']).toBe(0)
  })
})
