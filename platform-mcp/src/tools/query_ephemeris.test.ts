/**
 * query_ephemeris.test.ts — Regression tests for the query_ephemeris MCP tool.
 *
 * Tests the C5 bug fix:
 *   1. date_range now uses {from, to} (was {start, end}), mapped to start_date/end_date for primitive.
 *   2. Date range exceeding 1825 days returns an error response.
 *   3. sample_step param is forwarded to primitive.
 *   4. planet accepts a single string or an array; normalized to array before dispatch.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryEphemeris } from './query_ephemeris.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildEphemerisEnvelope(positions: unknown[]) {
  const toolBundle = {
    tool_bundle_id: 'ephemeris-bundle-id',
    tool_name: 'query_ephemeris',
    tool_version: '1.0.0',
    invocation_params: {},
    results: positions.map(p => ({
      content: JSON.stringify(p),
      source_canonical_id: 'EPHEMERIS_DAILY',
      source_version: '1.0',
      confidence: 1.0,
      significance: 0.85,
    })),
    served_from_cache: false,
    latency_ms: 8,
    result_hash: 'sha256:ephemeris-test',
    schema_version: '1.0',
  }

  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-eph-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: toolBundle,
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

/**
 * Register the tool on a stub server, simulate Zod validation, then invoke the handler.
 */
async function callQueryEphemeris(
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

  registerQueryEphemeris(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_ephemeris handler was not registered')

  // Simulate Zod validation as MCP SDK would perform
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_ephemeris — C5 date_range + sample_step fix', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.3: date_range {from, to} is mapped to start_date/end_date for the primitive
  it('AC.3 — date_range.from/to is correctly mapped to start_date/end_date in primitive call', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([
      { date: '2026-06-01', planet: 'jupiter', sign: 'Gemini', degree: 12.3 },
    ]))

    await callQueryEphemeris({
      planet: 'Jupiter',
      date_range: { from: '2026-06-01', to: '2026-06-30' },
    })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('query_ephemeris')

    const p = params as Record<string, unknown>
    expect(p['start_date']).toBe('2026-06-01')
    expect(p['end_date']).toBe('2026-06-30')
    // The raw date_range object must NOT be forwarded to the primitive
    expect(p['date_range']).toBeUndefined()
  })

  // Zod rejects the old {start, end} schema
  it('Zod rejects old date_range shape {start, end} — callers must use {from, to}', async () => {
    const result = await callQueryEphemeris({
      planet: 'Saturn',
      date_range: { start: '2026-01-01', end: '2026-03-31' },
    })
    // Zod should reject because {start, end} fields are not in the schema
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  // AC.3: range > 1825 days returns an error (not a Zod error — it's a handler-level error)
  it('AC.3 — date range exceeding 1825 days returns an error envelope', async () => {
    // 2020-01-01 to 2030-01-01 = ~3653 days
    const result = await callQueryEphemeris({
      planet: 'Saturn',
      date_range: { from: '2020-01-01', to: '2030-01-01' },
    })

    // Should be an MCP error result (isError: true), not a Zod validation error
    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect((result as { isError?: boolean }).isError).toBe(true)

    const content = (result as { content: Array<{ type: string; text: string }> }).content
    expect(content).toBeDefined()
    const text = content[0].text
    const parsed = JSON.parse(text) as Record<string, unknown>
    expect(parsed['ok']).toBe(false)
    expect(parsed['error']).toBe('date_range_too_wide')
    expect((parsed['message'] as string)).toContain('1825 days')
  })

  // AC.3: exactly 1825 days is allowed
  it('AC.3 — date range of exactly 1825 days is allowed', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    // 2021-01-01 + 1825 days = 2025-12-31 (1825 day span)
    const result = await callQueryEphemeris({
      planet: 'Jupiter',
      date_range: { from: '2021-01-01', to: '2025-12-31' },
    })

    // Should reach the primitive, not be rejected
    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect((result as { isError?: boolean }).isError).toBeFalsy()
    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
  })

  // AC.4: sample_step is forwarded to the primitive
  it('AC.4 — sample_step="7d" is included in toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    await callQueryEphemeris({
      planet: 'Mars',
      date_range: { from: '2026-01-01', to: '2026-06-30' },
      sample_step: '7d',
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['sample_step']).toBe('7d')
  })

  it('AC.4 — sample_step="30d" is included in toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    await callQueryEphemeris({
      planet: 'Saturn',
      date_range: { from: '2025-01-01', to: '2026-12-31' },
      sample_step: '30d',
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['sample_step']).toBe('30d')
  })

  it('AC.4 — sample_step defaults to "1d" when not provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    await callQueryEphemeris({
      planet: 'Jupiter',
      date_range: { from: '2026-06-01', to: '2026-06-30' },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['sample_step']).toBe('1d')
  })

  it('AC.4 — return_changes_only=true is forwarded to toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    await callQueryEphemeris({
      planet: 'Venus',
      date_range: { from: '2026-01-01', to: '2026-12-31' },
      return_changes_only: true,
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['return_changes_only']).toBe(true)
  })

  // planet normalization: single string → passed as planet field
  it('planet as single string is forwarded as planet field to primitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    await callQueryEphemeris({
      planet: 'Saturn',
      date_range: { from: '2026-06-01', to: '2026-06-30' },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['planet']).toBe('Saturn')
    // planets array should not be set for single planet
    expect(params['planets']).toBeUndefined()
  })

  // planet as array → forwarded as planets field
  it('planet as array is forwarded as planets[] field to primitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEphemerisEnvelope([]))

    await callQueryEphemeris({
      planet: ['Saturn', 'Jupiter'],
      date_range: { from: '2026-06-01', to: '2026-06-30' },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['planets']).toEqual(['Saturn', 'Jupiter'])
    expect(params['planet']).toBeUndefined()
  })

  it('Zod rejects invalid planet name', async () => {
    const result = await callQueryEphemeris({
      planet: 'Pluto',
      date_range: { from: '2026-01-01', to: '2026-06-30' },
    })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('returns error result when primitive call fails', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-eph-001',
        error: { class: 'internal', message: 'DB connection error' },
      },
    })

    const result = await callQueryEphemeris({
      planet: 'Moon',
      date_range: { from: '2026-01-01', to: '2026-03-31' },
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('reversed date range (from > to) returns date_range_invalid error', async () => {
    const result = await callQueryEphemeris({
      planet: 'Sun',
      date_range: { from: '2026-12-31', to: '2026-01-01' },
    })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect((result as { isError?: boolean }).isError).toBe(true)

    const content = (result as { content: Array<{ type: string; text: string }> }).content
    const parsed = JSON.parse(content[0].text) as Record<string, unknown>
    expect(parsed['error']).toBe('date_range_invalid')
  })
})
