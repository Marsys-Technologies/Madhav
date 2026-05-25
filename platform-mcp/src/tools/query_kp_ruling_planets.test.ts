/**
 * query_kp_ruling_planets.test.ts — Unit tests for the query_kp_ruling_planets MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - chart_id UUID param is forwarded correctly
 *   - Zod validation rejects non-UUID chart_id
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
import { registerQueryKpRulingPlanets } from './query_kp_ruling_planets.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildSuccessEnvelope(results: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-kp-ruling-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'kp-ruling-bundle-id',
        tool_name: 'query_kp_ruling_planets',
        tool_version: '1.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'KP_SUBLORDS_RAW',
          source_version: '1.0',
          confidence: 0.95,
          significance: 0.8,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:kp-ruling-test',
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
      trace_id: 'trace-kp-ruling-err',
      error: { class: 'internal', message: 'Database unavailable' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQueryKpRulingPlanets(
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

  registerQueryKpRulingPlanets(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_kp_ruling_planets handler was not registered')

  // Simulate Zod validation as the MCP SDK would perform
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// Helper: parse text content from MCP result
function parseResultContent(result: unknown): unknown {
  const r = result as { content?: Array<{ type: string; text: string }>; isError?: boolean }
  if (!r.content?.[0]?.text) return null
  return JSON.parse(r.content[0].text)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_kp_ruling_planets — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerQueryKpRulingPlanets(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('query_kp_ruling_planets')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { planet: 'Saturn', star_lord: 'Venus', sub_lord: 'Sun', sub_sub_lord: 'Moon' },
    ]))

    const result = await callQueryKpRulingPlanets({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryKpRulingPlanets({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: chart_id UUID is forwarded to callPlatformPrimitive
  it('AC.4 — chart_id UUID is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const chartId = '123e4567-e89b-12d3-a456-426614174000'
    await callQueryKpRulingPlanets({ chart_id: chartId })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('query_kp_ruling_planets')
    expect((params as Record<string, unknown>)['chart_id']).toBe(chartId)
  })

  // AC.5: chart_id not included in params when not provided
  it('AC.5 — chart_id not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryKpRulingPlanets({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('chart_id' in params).toBe(false)
  })

  // AC.6: Zod rejects non-UUID chart_id
  it('AC.6 — Zod rejects non-UUID chart_id', async () => {
    const result = await callQueryKpRulingPlanets({ chart_id: 'not-a-uuid' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.7: Zod rejects empty string chart_id
  it('AC.7 — Zod rejects empty string chart_id', async () => {
    const result = await callQueryKpRulingPlanets({ chart_id: '' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.8: response envelope content is parseable JSON with ok: true
  it('AC.8 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callQueryKpRulingPlanets({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.9: tool works with no args (empty object)
  it('AC.9 — tool works with no args (defaults to native chart)', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { planet: 'Sun', star_lord: 'Mercury', sub_lord: 'Saturn', sub_sub_lord: 'Jupiter' },
      { planet: 'Moon', star_lord: 'Venus', sub_lord: 'Mars', sub_sub_lord: 'Rahu' },
    ]))

    const result = await callQueryKpRulingPlanets({})

    const r = result as { content?: Array<{ type: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
  })
})
