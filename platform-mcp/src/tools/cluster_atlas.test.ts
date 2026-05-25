/**
 * cluster_atlas.test.ts — Unit tests for the cluster_atlas MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - Input params (domain, sub_domain, min_size, limit) are forwarded correctly
 *   - Zod validation enforces min_size >= 1 and limit range (1–100)
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
import { registerClusterAtlas } from './cluster_atlas.js'

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
      trace_id: 'trace-cluster-atlas-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'cluster-atlas-bundle-id',
        tool_name: 'cluster_atlas',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'CLUSTER_ATLAS',
          source_version: '1.0',
          confidence: 0.85,
          significance: 0.80,
        })),
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:cluster-atlas-test',
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
      trace_id: 'trace-cluster-atlas-err',
      error: { class: 'internal', message: 'Cluster atlas unavailable' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callClusterAtlas(
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

  registerClusterAtlas(stubServer, () => principal)

  if (!capturedHandler) throw new Error('cluster_atlas handler was not registered')

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

describe('cluster_atlas — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerClusterAtlas(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('cluster_atlas')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { cluster_id: 'CL.001', cluster_label: 'Career Elevation Cluster', dominant_domain: 'career', cluster_size_n: 7 },
    ]))

    const result = await callClusterAtlas({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callClusterAtlas({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: domain param is forwarded to callPlatformPrimitive
  it('AC.4 — domain is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({ domain: 'career' })

    expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('cluster_atlas')
    expect((params as Record<string, unknown>)['domain']).toBe('career')
  })

  // AC.5: sub_domain param is forwarded to callPlatformPrimitive
  it('AC.5 — sub_domain is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({ sub_domain: 'wealth' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['sub_domain']).toBe('wealth')
  })

  // AC.6: min_size param is forwarded to callPlatformPrimitive
  it('AC.6 — min_size is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({ min_size: 3 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['min_size']).toBe(3)
  })

  // AC.7: limit defaults to 20 when not provided
  it('AC.7 — limit defaults to 20 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(20)
  })

  // AC.8: custom limit is forwarded correctly
  it('AC.8 — custom limit is forwarded correctly', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({ limit: 50 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(50)
  })

  // AC.9: Zod rejects min_size < 1
  it('AC.9 — Zod rejects min_size < 1', async () => {
    const result = await callClusterAtlas({ min_size: 0 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.10: Zod rejects limit > 100
  it('AC.10 — Zod rejects limit > 100', async () => {
    const result = await callClusterAtlas({ limit: 101 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.11: Zod rejects limit < 1
  it('AC.11 — Zod rejects limit < 1', async () => {
    const result = await callClusterAtlas({ limit: 0 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.12: response envelope content is parseable JSON with ok: true
  it('AC.12 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callClusterAtlas({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.13: domain not included in params when not provided
  it('AC.13 — domain not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('domain' in params).toBe(false)
  })

  // AC.14: sub_domain not included in params when not provided
  it('AC.14 — sub_domain not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('sub_domain' in params).toBe(false)
  })

  // AC.15: min_size not included in params when not provided
  it('AC.15 — min_size not included in params when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('min_size' in params).toBe(false)
  })

  // AC.16: all optional params forwarded together correctly
  it('AC.16 — all params forwarded together correctly', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callClusterAtlas({ domain: 'career', sub_domain: 'finance', min_size: 5, limit: 10 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['domain']).toBe('career')
    expect(params['sub_domain']).toBe('finance')
    expect(params['min_size']).toBe(5)
    expect(params['limit']).toBe(10)
  })
})
