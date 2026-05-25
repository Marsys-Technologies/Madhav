/**
 * query_rm_walk.test.ts — Unit tests for the query_rm_walk MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - seed_signal_id param is forwarded correctly to callPlatformPrimitive
 *   - Full-dump mode (no params) omits seed_signal_id from forwarded params
 *   - Response content is parseable JSON with ok: true
 *   - isError: true when envelope.ok is false (even with status 200)
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
import { registerQueryRmWalk } from './query_rm_walk.js'

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
      trace_id: 'trace-rm-walk-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'rm-walk-bundle-id',
        tool_name: 'query_rm_walk',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'RM',
          source_version: '2.2',
          confidence: 0.9,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:rm-walk-test',
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
      trace_id: 'trace-rm-walk-err',
      error: { class: 'internal', message: 'RM file not found' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQueryRmWalk(
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

  registerQueryRmWalk(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_rm_walk handler was not registered')

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

describe('query_rm_walk — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerQueryRmWalk(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('query_rm_walk')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { rm_id: 'RM.01', signal_id: 'RM.01', resonance_type: 'Mercury 10H Capricorn', strength: 'STRONGLY_AMPLIFIED' },
    ]))

    const result = await callQueryRmWalk({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryRmWalk({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: seed_signal_id is forwarded to callPlatformPrimitive
  it('AC.4 — seed_signal_id is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryRmWalk({ seed_signal_id: 'MSR.045' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('query_rm_walk')
    expect((params as Record<string, unknown>)['seed_signal_id']).toBe('MSR.045')
  })

  // AC.5: full-dump mode (no seed_signal_id) omits seed_signal_id from params
  it('AC.5 — full-dump mode omits seed_signal_id from forwarded params', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryRmWalk({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['seed_signal_id']).toBeUndefined()
  })

  // AC.6: RM.NN element IDs are also forwarded (not just MSR.NNN IDs)
  it('AC.6 — RM element ID (e.g. "RM.01") is forwarded as seed_signal_id', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryRmWalk({ seed_signal_id: 'RM.01' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['seed_signal_id']).toBe('RM.01')
  })

  // AC.7: response content is parseable JSON with ok: true
  it('AC.7 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callQueryRmWalk({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.8: isError: true when envelope.ok is false (even with status 200)
  it('AC.8 — isError: true when envelope.ok is false regardless of status', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue({
      status: 200,
      envelope: { ok: false, trace_id: 'trace-x', error: { class: 'zero_rows', message: 'no RM entries matched' } },
    })

    const result = await callQueryRmWalk({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.9: tool name forwarded to callPlatformPrimitive is exactly 'query_rm_walk'
  it('AC.9 — callPlatformPrimitive is called with tool name query_rm_walk', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryRmWalk({ seed_signal_id: 'MSR.413' })

    expect(vi.mocked(callPlatformPrimitive).mock.calls[0][0]).toBe('query_rm_walk')
  })

  // AC.10: principal is passed through to callPlatformPrimitive
  it('AC.10 — principal is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const customPrincipal: Principal = {
      user_uid: 'acharya-user',
      audience_tier: 'acharya',
      key_id: 'acharya-key',
    }

    await callQueryRmWalk({}, customPrincipal)

    const passedPrincipal = vi.mocked(callPlatformPrimitive).mock.calls[0][2] as Principal
    expect(passedPrincipal.user_uid).toBe('acharya-user')
    expect(passedPrincipal.audience_tier).toBe('acharya')
  })
})
