/**
 * timeline_query.test.ts — Unit tests for the timeline_query MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - dasha_name param is forwarded correctly to callPlatformPrimitive
 *   - keyword param is forwarded correctly to callPlatformPrimitive
 *   - limit param is forwarded correctly (default 8 when omitted)
 *   - Response content is parseable JSON with ok: true
 *   - isError: true when envelope.ok is false (even with status 200)
 *   - Tool name forwarded to callPlatformPrimitive is exactly 'timeline_query'
 *   - principal is forwarded to callPlatformPrimitive
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
import { registerTimelineQuery } from './timeline_query.js'

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
      trace_id: 'trace-timeline-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'timeline-bundle-id',
        tool_name: 'timeline_query',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'LIFETIME_TIMELINE_v1_0',
          source_version: '1.0',
          confidence: 1.0,
        })),
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:timeline-test',
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
      trace_id: 'trace-timeline-err',
      error: { class: 'internal', message: 'timeline_query DB error' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callTimelineQuery(
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

  registerTimelineQuery(stubServer, () => principal)

  if (!capturedHandler) throw new Error('timeline_query handler was not registered')

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

describe('timeline_query — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerTimelineQuery(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('timeline_query')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { content: 'Mercury MD 2014-08-21 → 2027-08-21 ...', doc_type: 'l5_timeline', chunk_id: 'chunk-001' },
    ]))

    const result = await callTimelineQuery({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callTimelineQuery({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: dasha_name is forwarded to callPlatformPrimitive
  it('AC.4 — dasha_name is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTimelineQuery({ dasha_name: 'Mercury MD' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('timeline_query')
    expect((params as Record<string, unknown>)['dasha_name']).toBe('Mercury MD')
  })

  // AC.5: keyword is forwarded to callPlatformPrimitive
  it('AC.5 — keyword is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTimelineQuery({ keyword: 'inflection' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['keyword']).toBe('inflection')
  })

  // AC.6: limit is forwarded; defaults to 8 when omitted
  it('AC.6 — limit defaults to 8 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTimelineQuery({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(8)
  })

  it('AC.6b — explicit limit is forwarded correctly', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTimelineQuery({ limit: 15 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(15)
  })

  // AC.7: response content is parseable JSON with ok: true
  it('AC.7 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callTimelineQuery({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.8: isError: true when envelope.ok is false (even with status 200)
  it('AC.8 — isError: true when envelope.ok is false regardless of status', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue({
      status: 200,
      envelope: { ok: false, trace_id: 'trace-x', error: { class: 'zero_rows', message: 'no l5_timeline chunks matched' } },
    })

    const result = await callTimelineQuery({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.9: tool name forwarded to callPlatformPrimitive is exactly 'timeline_query'
  it('AC.9 — callPlatformPrimitive is called with tool name timeline_query', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTimelineQuery({ dasha_name: 'Ketu MD' })

    expect(vi.mocked(callPlatformPrimitive).mock.calls[0][0]).toBe('timeline_query')
  })

  // AC.10: principal is passed through to callPlatformPrimitive
  it('AC.10 — principal is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const customPrincipal: Principal = {
      user_uid: 'acharya-user',
      audience_tier: 'acharya',
      key_id: 'acharya-key',
    }

    await callTimelineQuery({}, customPrincipal)

    const passedPrincipal = vi.mocked(callPlatformPrimitive).mock.calls[0][2] as Principal
    expect(passedPrincipal.user_uid).toBe('acharya-user')
    expect(passedPrincipal.audience_tier).toBe('acharya')
  })

  // AC.11: dasha_name omitted when not provided (not undefined forwarded)
  it('AC.11 — dasha_name omitted from params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTimelineQuery({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('dasha_name' in params).toBe(false)
  })

  // AC.12: limit out of range (>50) is caught by Zod schema
  it('AC.12 — limit > 50 is rejected by Zod schema', async () => {
    const result = await callTimelineQuery({ limit: 51 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })
})
