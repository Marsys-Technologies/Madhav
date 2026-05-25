/**
 * msr_sql.test.ts — Unit tests for the msr_sql MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - Input params are forwarded correctly to callPlatformPrimitive
 *   - Zod validation rejects invalid inputs (confidence_floor out of range,
 *     invalid chart_id UUID, limit out of range)
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
import { registerMsrSql } from './msr_sql.js'

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
      trace_id: 'trace-msr-sql-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'msr-sql-bundle-id',
        tool_name: 'msr_sql',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'MSR',
          source_version: '3.0',
          confidence: 0.85,
          significance: 0.8,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:msr-sql-test',
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
      trace_id: 'trace-msr-sql-err',
      error: { class: 'internal', message: 'DB error in msr_sql' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callMsrSql(
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

  registerMsrSql(stubServer, () => principal)

  if (!capturedHandler) throw new Error('msr_sql handler was not registered')

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

describe('msr_sql — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerMsrSql(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('msr_sql')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { signal_id: 'SIG.MSR.001', domain: 'career', claim_text: 'Strong career yoga' },
    ]))

    const result = await callMsrSql({ domain: 'career' })

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callMsrSql({ domain: 'career' })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: domain is forwarded to callPlatformPrimitive
  it('AC.4 — domain is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ domain: 'health' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('msr_sql')
    expect((params as Record<string, unknown>)['domain']).toBe('health')
  })

  // AC.5: domains[] is forwarded when provided
  it('AC.5 — domains array is forwarded when provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ domains: ['career', 'wealth'] })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['domains']).toEqual(['career', 'wealth'])
  })

  // AC.6: confidence_floor is forwarded
  it('AC.6 — confidence_floor is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ domain: 'spiritual', confidence_floor: 0.8 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['confidence_floor']).toBe(0.8)
  })

  // AC.7: forward_looking is forwarded
  it('AC.7 — forward_looking is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ forward_looking: true })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['forward_looking']).toBe(true)
  })

  // AC.8: signal_type is forwarded as an array
  it('AC.8 — signal_type is forwarded as an array', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ signal_type: 'yoga' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['signal_type']).toEqual(['yoga'])
  })

  // AC.9: limit defaults to 50 when not provided
  it('AC.9 — limit defaults to 50 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ domain: 'career' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(50)
  })

  // AC.10: explicit limit is forwarded
  it('AC.10 — explicit limit is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callMsrSql({ limit: 100 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(100)
  })

  // AC.11: chart_id UUID is forwarded
  it('AC.11 — chart_id UUID is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const chartId = '123e4567-e89b-12d3-a456-426614174000'
    await callMsrSql({ chart_id: chartId })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(chartId)
  })

  // AC.12: Zod rejects invalid chart_id (not a UUID)
  it('AC.12 — Zod rejects non-UUID chart_id', async () => {
    const result = await callMsrSql({ chart_id: 'not-a-uuid' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.13: Zod rejects confidence_floor > 1
  it('AC.13 — Zod rejects confidence_floor > 1', async () => {
    const result = await callMsrSql({ confidence_floor: 1.5 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.14: Zod rejects limit > 500
  it('AC.14 — Zod rejects limit > 500', async () => {
    const result = await callMsrSql({ limit: 501 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.15: response envelope content is parseable JSON
  it('AC.15 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callMsrSql({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })
})
