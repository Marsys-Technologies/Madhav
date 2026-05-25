/**
 * query_ucn_walk.test.ts — Unit tests for the query_ucn_walk MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - seed_signal_id param is forwarded correctly to callPlatformPrimitive
 *   - depth param is forwarded correctly
 *   - Full-dump mode (no params) omits seed_signal_id from forwarded params
 *   - Zod validation rejects depth out of range
 *   - Response content is parseable JSON with ok: true
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
import { registerQueryUcnWalk } from './query_ucn_walk.js'

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
      trace_id: 'trace-ucn-walk-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'ucn-walk-bundle-id',
        tool_name: 'query_ucn_walk',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'UCN',
          source_version: '4.1',
          confidence: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:ucn-walk-test',
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
      trace_id: 'trace-ucn-walk-err',
      error: { class: 'internal', message: 'UCN file not found' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQueryUcnWalk(
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

  registerQueryUcnWalk(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_ucn_walk handler was not registered')

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

describe('query_ucn_walk — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerQueryUcnWalk(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('query_ucn_walk')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { signal_id: 'MSR.413', confluence_type: 'Career Section', domain: 'D1_Career' },
    ]))

    const result = await callQueryUcnWalk({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryUcnWalk({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: seed_signal_id is forwarded to callPlatformPrimitive
  it('AC.4 — seed_signal_id is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryUcnWalk({ seed_signal_id: 'MSR.234' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('query_ucn_walk')
    expect((params as Record<string, unknown>)['seed_signal_id']).toBe('MSR.234')
  })

  // AC.5: depth is forwarded to callPlatformPrimitive
  it('AC.5 — depth is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryUcnWalk({ depth: 3 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['depth']).toBe(3)
  })

  // AC.6: full-dump mode (no seed_signal_id) omits seed_signal_id from params
  it('AC.6 — full-dump mode omits seed_signal_id from forwarded params', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryUcnWalk({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['seed_signal_id']).toBeUndefined()
  })

  // AC.7: depth defaults to 2 when not provided
  it('AC.7 — depth defaults to 2 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryUcnWalk({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['depth']).toBe(2)
  })

  // AC.8: Zod rejects depth < 1
  it('AC.8 — Zod rejects depth < 1', async () => {
    const result = await callQueryUcnWalk({ depth: 0 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.9: Zod rejects depth > 5
  it('AC.9 — Zod rejects depth > 5', async () => {
    const result = await callQueryUcnWalk({ depth: 6 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.10: response content is parseable JSON with ok: true
  it('AC.10 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callQueryUcnWalk({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.11: seed_signal_id and depth both forwarded together
  it('AC.11 — seed_signal_id and depth both forwarded together', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryUcnWalk({ seed_signal_id: 'MSR.391', depth: 4 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['seed_signal_id']).toBe('MSR.391')
    expect(params['depth']).toBe(4)
  })

  // AC.12: isError: true when envelope.ok is false (even with status 200)
  it('AC.12 — isError: true when envelope.ok is false regardless of status', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue({
      status: 200,
      envelope: { ok: false, trace_id: 'trace-x', error: { class: 'zero_rows', message: 'no results' } },
    })

    const result = await callQueryUcnWalk({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })
})
