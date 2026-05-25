/**
 * query_cdlm_lookup.test.ts — Unit tests for the query_cdlm_lookup MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - domain_a, domain_b, signal_id params are forwarded correctly to callPlatformPrimitive
 *   - Full-dump mode (no params) omits all filters from forwarded params
 *   - Response content is parseable JSON with ok: true
 *   - isError: true when envelope.ok is false
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
import { registerQueryCdlmLookup } from './query_cdlm_lookup.js'

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
      trace_id: 'trace-cdlm-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'cdlm-bundle-id',
        tool_name: 'query_cdlm_lookup',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'CDLM',
          source_version: '1.3',
          confidence: 0.88,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:cdlm-test',
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
      trace_id: 'trace-cdlm-err',
      error: { class: 'internal', message: 'CDLM file not found' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQueryCdlmLookup(
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

  registerQueryCdlmLookup(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_cdlm_lookup handler was not registered')

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

describe('query_cdlm_lookup — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerQueryCdlmLookup(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('query_cdlm_lookup')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { domain_pair: 'Career→Wealth', linkage_type: 'feeds', strength: '0.92' },
    ]))

    const result = await callQueryCdlmLookup({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryCdlmLookup({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: domain_a is forwarded to callPlatformPrimitive
  it('AC.4 — domain_a is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryCdlmLookup({ domain_a: 'Career' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('query_cdlm_lookup')
    expect((params as Record<string, unknown>)['domain_a']).toBe('Career')
  })

  // AC.5: domain_b is forwarded to callPlatformPrimitive
  it('AC.5 — domain_b is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryCdlmLookup({ domain_b: 'Wealth' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['domain_b']).toBe('Wealth')
  })

  // AC.6: signal_id is forwarded to callPlatformPrimitive
  it('AC.6 — signal_id is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryCdlmLookup({ signal_id: 'MSR.413' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['signal_id']).toBe('MSR.413')
  })

  // AC.7: full-dump mode (no params) sends empty params object
  it('AC.7 — full-dump mode sends empty params to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryCdlmLookup({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['domain_a']).toBeUndefined()
    expect(params['domain_b']).toBeUndefined()
    expect(params['signal_id']).toBeUndefined()
  })

  // AC.8: all three filters forwarded together
  it('AC.8 — all three filters forwarded together', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryCdlmLookup({ domain_a: 'Career', domain_b: 'Health', signal_id: 'MSR.264' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['domain_a']).toBe('Career')
    expect(params['domain_b']).toBe('Health')
    expect(params['signal_id']).toBe('MSR.264')
  })

  // AC.9: response content is parseable JSON with ok: true
  it('AC.9 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callQueryCdlmLookup({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.10: isError: true when envelope.ok is false (even with status 200)
  it('AC.10 — isError: true when envelope.ok is false regardless of status', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue({
      status: 200,
      envelope: { ok: false, trace_id: 'trace-x', error: { class: 'zero_rows', message: 'no results' } },
    })

    const result = await callQueryCdlmLookup({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.11: domain_a and domain_b together, no signal_id
  it('AC.11 — domain_a + domain_b without signal_id omits signal_id from params', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQueryCdlmLookup({ domain_a: 'Spirit', domain_b: 'Mind' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['domain_a']).toBe('Spirit')
    expect(params['domain_b']).toBe('Mind')
    expect(params['signal_id']).toBeUndefined()
  })
})
