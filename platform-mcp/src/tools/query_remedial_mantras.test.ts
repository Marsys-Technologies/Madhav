/**
 * query_remedial_mantras.test.ts — Unit tests for the query_remedial_mantras MCP tool.
 *
 * TR-P4-S1 AC.4: all 3 test files must pass.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryRemedialMantras } from './query_remedial_mantras.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildRemedialEnvelope(chunks: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-remedial-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'remedial-bundle-id',
        tool_name: 'remedial_codex_query',
        tool_version: '1.0.0',
        invocation_params: {},
        results: chunks.map(chunk => ({
          content: JSON.stringify(chunk),
          source_canonical_id: 'REMEDIAL_CODEX_v2_0',
          source_version: '2.0',
          confidence: 1.0,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 6,
        result_hash: 'sha256:remedial-test',
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

async function callQueryRemedialMantras(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      _schema: unknown,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
    },
  } as unknown as McpServer

  registerQueryRemedialMantras(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_remedial_mantras handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_remedial_mantras', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns ≥1 chunk when querying for Saturn', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([
      { content: 'Saturn propitiation: chant Shani Beej mantra 108 times on Saturday...', doc_type: 'l4_remedial', chunk_id: 'rem-saturn-001' },
      { content: 'Saturn gemstone: Blue Sapphire (Neelam) — consult an expert before wearing...', doc_type: 'l4_remedial', chunk_id: 'rem-saturn-002' },
    ]))

    const result = await callQueryRemedialMantras({ planet: 'Saturn' })

    expect(result).toBeDefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    expect(res.content.length).toBeGreaterThan(0)
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    // The result has ≥1 chunk in the results array
    expect(parsed.result.results.length).toBeGreaterThanOrEqual(1)
  })

  it('passes planet param to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ planet: 'Saturn' })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('remedial_codex_query')
    expect((params as Record<string, unknown>)['planet']).toBe('Saturn')
  })

  it('composes keyword from house when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ house: 7 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['keyword']).toBe('house 7')
  })

  it('composes keyword from condition when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ condition: 'debilitated Mars' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['keyword']).toBe('debilitated Mars')
  })

  it('composes keyword from both house and condition', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ house: 7, condition: 'Rahu affliction' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['keyword']).toBe('house 7 Rahu affliction')
  })

  it('omits keyword from params when neither house nor condition is provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ planet: 'Mars' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['keyword']).toBeUndefined()
  })

  it('passes default limit of 8', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ planet: 'Moon' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(8)
  })

  it('passes custom limit when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildRemedialEnvelope([]))

    await callQueryRemedialMantras({ planet: 'Jupiter', limit: 15 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(15)
  })

  it('returns error result when primitive call fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-003',
        error: { class: 'internal', message: 'DB error' },
      },
    })

    const result = await callQueryRemedialMantras({ planet: 'Saturn' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })
})
