/**
 * kp_query.test.ts — Unit tests for the kp_query MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - Input params (cusp, planet, query_type) are forwarded correctly
 *   - Zod validation enforces cusp range (1–12) and query_type enum
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
import { registerKpQuery } from './kp_query.js'

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
      trace_id: 'trace-kp-query-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'kp-query-bundle-id',
        tool_name: 'kp_query',
        tool_version: '1.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:kp-query-test',
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
      trace_id: 'trace-kp-query-err',
      error: { class: 'internal', message: 'Database unavailable' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callKpQuery(
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

  registerKpQuery(stubServer, () => principal)

  if (!capturedHandler) throw new Error('kp_query handler was not registered')

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

describe('kp_query — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerKpQuery(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('kp_query')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { fact_id: 'KP.CUSP.10', category: 'kp_cusp', kp_data: { star_lord: 'Saturn' } },
    ]))

    const result = await callKpQuery({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callKpQuery({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: cusp param is forwarded to callPlatformPrimitive
  it('AC.4 — cusp is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callKpQuery({ cusp: 10 })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('kp_query')
    expect((params as Record<string, unknown>)['cusp']).toBe(10)
  })

  // AC.5: planet param is forwarded to callPlatformPrimitive
  it('AC.5 — planet is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callKpQuery({ planet: 'Saturn' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['planet']).toBe('Saturn')
  })

  // AC.6: query_type is forwarded to callPlatformPrimitive
  it('AC.6 — query_type is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callKpQuery({ query_type: 'significators' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['query_type']).toBe('significators')
  })

  // AC.7: query_type defaults to 'all' when not provided
  it('AC.7 — query_type defaults to all when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callKpQuery({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['query_type']).toBe('all')
  })

  // AC.8: Zod rejects cusp < 1
  it('AC.8 — Zod rejects cusp < 1', async () => {
    const result = await callKpQuery({ cusp: 0 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.9: Zod rejects cusp > 12
  it('AC.9 — Zod rejects cusp > 12', async () => {
    const result = await callKpQuery({ cusp: 13 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.10: Zod rejects invalid query_type enum value
  it('AC.10 — Zod rejects invalid query_type enum value', async () => {
    const result = await callKpQuery({ query_type: 'invalid_type' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.11: response envelope content is parseable JSON with ok: true
  it('AC.11 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callKpQuery({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.12: cusp not included in params when not provided
  it('AC.12 — cusp not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callKpQuery({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('cusp' in params).toBe(false)
  })

  // AC.13: planet not included in params when not provided
  it('AC.13 — planet not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callKpQuery({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('planet' in params).toBe(false)
  })
})
