/**
 * pattern_register.test.ts — Unit tests for the pattern_register MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - Input params (domain, keyword, min_confidence, limit) are forwarded correctly
 *   - Zod validation enforces min_confidence range (0.0–1.0) and limit range (1–200)
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
import { registerPatternRegister } from './pattern_register.js'

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
      trace_id: 'trace-pattern-register-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'pattern-register-bundle-id',
        tool_name: 'pattern_register',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'PATTERN_REGISTER',
          source_version: '1.0',
          confidence: 0.85,
          significance: 0.75,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:pattern-register-test',
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
      trace_id: 'trace-pattern-register-err',
      error: { class: 'internal', message: 'Pattern register unavailable' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callPatternRegister(
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

  registerPatternRegister(stubServer, () => principal)

  if (!capturedHandler) throw new Error('pattern_register handler was not registered')

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

describe('pattern_register — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerPatternRegister(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('pattern_register')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { pattern_id: 'PAT.001', claim_text: 'Career elevation pattern', domain: 'career' },
    ]))

    const result = await callPatternRegister({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callPatternRegister({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: domain param is forwarded to callPlatformPrimitive
  it('AC.4 — domain is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({ domain: 'career' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('pattern_register')
    expect((params as Record<string, unknown>)['domain']).toBe('career')
  })

  // AC.5: keyword param is forwarded to callPlatformPrimitive
  it('AC.5 — keyword is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({ keyword: 'Saturn' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['keyword']).toBe('Saturn')
  })

  // AC.6: min_confidence is forwarded to callPlatformPrimitive
  it('AC.6 — min_confidence is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({ min_confidence: 0.7 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['min_confidence']).toBe(0.7)
  })

  // AC.7: limit defaults to 50 when not provided
  it('AC.7 — limit defaults to 50 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(50)
  })

  // AC.8: custom limit is forwarded correctly
  it('AC.8 — custom limit is forwarded correctly', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({ limit: 100 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(100)
  })

  // AC.9: Zod rejects min_confidence < 0
  it('AC.9 — Zod rejects min_confidence < 0', async () => {
    const result = await callPatternRegister({ min_confidence: -0.1 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.10: Zod rejects min_confidence > 1
  it('AC.10 — Zod rejects min_confidence > 1', async () => {
    const result = await callPatternRegister({ min_confidence: 1.5 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.11: Zod rejects limit > 200
  it('AC.11 — Zod rejects limit > 200', async () => {
    const result = await callPatternRegister({ limit: 201 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.12: Zod rejects limit < 1
  it('AC.12 — Zod rejects limit < 1', async () => {
    const result = await callPatternRegister({ limit: 0 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.13: response envelope content is parseable JSON with ok: true
  it('AC.13 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callPatternRegister({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.14: domain not included in params when not provided
  it('AC.14 — domain not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('domain' in params).toBe(false)
  })

  // AC.15: keyword not included in params when not provided
  it('AC.15 — keyword not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('keyword' in params).toBe(false)
  })

  // AC.16: min_confidence not included in params when not provided
  it('AC.16 — min_confidence not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callPatternRegister({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('min_confidence' in params).toBe(false)
  })
})
