/**
 * query_jaimini_drishti.test.ts — Unit tests for the query_jaimini_drishti MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success (stub may return not_implemented)
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - params object is forwarded correctly to callPlatformPrimitive
 *   - No-params call omits params key from forwarded args
 *   - Response content is parseable JSON with ok: true
 *   - isError: true when envelope.ok is false (even with status 200)
 *   - Tool name forwarded is exactly 'query_jaimini_drishti'
 *   - Principal is passed through to callPlatformPrimitive
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
import { registerQueryJaiminiDrishti } from './query_jaimini_drishti.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildSuccessEnvelope(result: unknown = {}) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-jaimini-drishti-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'medium', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'jaimini-drishti-bundle-id',
        tool_name: 'query_jaimini_drishti',
        tool_version: '1.0.0',
        invocation_params: {},
        results: [{
          content: JSON.stringify(result),
          source_canonical_id: 'FORENSIC',
          source_version: '1.0',
          confidence: 0.5,
          significance: 0.7,
        }],
        served_from_cache: false,
        latency_ms: 15,
        result_hash: 'sha256:jaimini-drishti-test',
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
    status: 503,
    envelope: {
      ok: false,
      trace_id: 'trace-jaimini-drishti-err',
      error: { class: 'not_implemented', message: 'Jaimini engine M6+ scope' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQueryJaiminiDrishti(
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

  registerQueryJaiminiDrishti(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_jaimini_drishti handler was not registered')

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

describe('query_jaimini_drishti — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerQueryJaiminiDrishti(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('query_jaimini_drishti')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(
      buildSuccessEnvelope({ aspects: [], status: 'stub' })
    )

    const result = await callQueryJaiminiDrishti({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryJaiminiDrishti({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: params object is forwarded to callPlatformPrimitive
  it('AC.4 — params object is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    await callQueryJaiminiDrishti({ params: { lagna: 'Scorpio', include_upapada: true } })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, passedArgs] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('query_jaimini_drishti')
    const args = passedArgs as Record<string, unknown>
    expect(args['params']).toEqual({ lagna: 'Scorpio', include_upapada: true })
  })

  // AC.5: no-params call omits params key from forwarded args
  it('AC.5 — no-params call omits params key from forwarded args', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    await callQueryJaiminiDrishti({})

    const passedArgs = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(passedArgs['params']).toBeUndefined()
  })

  // AC.6: empty params object is forwarded (not treated as absent)
  it('AC.6 — empty params object {} is forwarded as params key', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    await callQueryJaiminiDrishti({ params: {} })

    const passedArgs = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(passedArgs['params']).toEqual({})
  })

  // AC.7: response content is parseable JSON with ok: true
  it('AC.7 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    const result = await callQueryJaiminiDrishti({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.8: isError: true when envelope.ok is false (even with status 200)
  it('AC.8 — isError: true when envelope.ok is false regardless of status', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue({
      status: 200,
      envelope: {
        ok: false,
        trace_id: 'trace-x',
        error: { class: 'not_implemented', message: 'stub endpoint' },
      },
    })

    const result = await callQueryJaiminiDrishti({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.9: tool name forwarded is exactly 'query_jaimini_drishti'
  it('AC.9 — callPlatformPrimitive is called with tool name query_jaimini_drishti', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    await callQueryJaiminiDrishti({})

    expect(vi.mocked(callPlatformPrimitive).mock.calls[0][0]).toBe('query_jaimini_drishti')
  })

  // AC.10: principal is passed through to callPlatformPrimitive
  it('AC.10 — principal is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    const customPrincipal: Principal = {
      user_uid: 'acharya-user',
      audience_tier: 'acharya',
      key_id: 'acharya-key',
    }

    await callQueryJaiminiDrishti({}, customPrincipal)

    const passedPrincipal = vi.mocked(callPlatformPrimitive).mock.calls[0][2] as Principal
    expect(passedPrincipal.user_uid).toBe('acharya-user')
    expect(passedPrincipal.audience_tier).toBe('acharya')
  })

  // AC.11: Zod accepts arbitrary key-value params (record schema)
  it('AC.11 — Zod accepts arbitrary params with string, number, boolean values', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope({}))

    // Should not throw or return a zodError
    const result = await callQueryJaiminiDrishti({
      params: { sign: 'Aries', house: 1, include_aspects: true, mode: null },
    })
    expect((result as { isZodError?: boolean }).isZodError).toBeUndefined()
  })
})
