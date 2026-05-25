/**
 * temporal.test.ts — Unit tests for the temporal MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - Input params are forwarded correctly to callPlatformPrimitive
 *   - Zod validation rejects invalid inputs (bad date format, invalid chart_id UUID)
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
import { registerTemporal } from './temporal.js'

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
      trace_id: 'trace-temporal-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'temporal-bundle-id',
        tool_name: 'temporal',
        tool_version: '1.1',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'TEMPORAL_DATA',
          source_version: '1.0',
          confidence: 1.0,
          significance: 0.8,
        })),
        served_from_cache: false,
        latency_ms: 15,
        result_hash: 'sha256:temporal-test',
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
      trace_id: 'trace-temporal-err',
      error: { class: 'internal', message: 'Sidecar unavailable' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callTemporal(
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

  registerTemporal(stubServer, () => principal)

  if (!capturedHandler) throw new Error('temporal handler was not registered')

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

describe('temporal — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerTemporal(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('temporal')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { planet: 'Saturn', sign: 'Pisces', house: 12, degree: 14.5 },
    ]))

    const result = await callTemporal({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callTemporal({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: date_from is forwarded to callPlatformPrimitive
  it('AC.4 — date_from is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({ date_from: '2026-06-01' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('temporal')
    expect((params as Record<string, unknown>)['date_from']).toBe('2026-06-01')
  })

  // AC.5: date_to is forwarded to callPlatformPrimitive
  it('AC.5 — date_to is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({ date_to: '2026-06-30' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['date_to']).toBe('2026-06-30')
  })

  // AC.6: include_transits is forwarded
  it('AC.6 — include_transits is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({ include_transits: false })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['include_transits']).toBe(false)
  })

  // AC.7: include_ephemeris is forwarded
  it('AC.7 — include_ephemeris is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({ include_ephemeris: true })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['include_ephemeris']).toBe(true)
  })

  // AC.8: include_dashas is forwarded
  it('AC.8 — include_dashas is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({ include_dashas: true })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['include_dashas']).toBe(true)
  })

  // AC.9: chart_id UUID is forwarded
  it('AC.9 — chart_id UUID is forwarded', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const chartId = '123e4567-e89b-12d3-a456-426614174000'
    await callTemporal({ chart_id: chartId })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(chartId)
  })

  // AC.10: include_transits defaults to true when not provided
  it('AC.10 — include_transits defaults to true when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['include_transits']).toBe(true)
  })

  // AC.11: include_ephemeris defaults to false when not provided
  it('AC.11 — include_ephemeris defaults to false when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['include_ephemeris']).toBe(false)
  })

  // AC.12: include_dashas defaults to false when not provided
  it('AC.12 — include_dashas defaults to false when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callTemporal({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['include_dashas']).toBe(false)
  })

  // AC.13: Zod rejects non-UUID chart_id
  it('AC.13 — Zod rejects non-UUID chart_id', async () => {
    const result = await callTemporal({ chart_id: 'not-a-uuid' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.14: Zod rejects invalid date_from format
  it('AC.14 — Zod rejects invalid date_from format', async () => {
    const result = await callTemporal({ date_from: '01-06-2026' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.15: response envelope content is parseable JSON with ok: true
  it('AC.15 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callTemporal({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })
})
