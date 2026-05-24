/**
 * tara_balam_for_native.test.ts — Unit tests for the tara_balam_for_native MCP tool.
 *
 * TR-P4-S2 AC: all 3 test files must pass.
 * Mocks callPlatformPrimitive to verify params, error handling, and response shape.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerTaraBalamForNative } from './tara_balam_for_native.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildTaraBalamEnvelope(resultData: unknown) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-tara-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'tara-bundle-id',
        tool_name: 'query_tara_balam',
        tool_version: '1.0.0',
        invocation_params: {},
        results: [{
          content: JSON.stringify(resultData),
          source_canonical_id: 'PANCHANGA_DAILY',
          source_version: '1.0',
          confidence: 1.0,
          significance: 0.85,
        }],
        served_from_cache: false,
        latency_ms: 8,
        result_hash: 'sha256:tara-test',
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

const SAMPLE_TARA_RESULT = {
  date: '2026-05-25',
  tara_count: 6,
  tara_name: 'Sadhaka',
  score: 0.95,
  interpretation: 'Auspicious — achievement tara; favourable for purposeful action and accomplishment.',
  moon_nakshatra: 'Purva Phalguni',
  birth_nakshatra: 'Purva Bhadrapada',
  birth_nakshatra_id: 25,
  cycle: 1,
  quality: 'auspicious',
}

async function callTaraBalamForNative(
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

  registerTaraBalamForNative(stubServer, () => principal)

  if (!capturedHandler) throw new Error('tara_balam_for_native handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('tara_balam_for_native', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('forwards date param to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildTaraBalamEnvelope(SAMPLE_TARA_RESULT))

    await callTaraBalamForNative({ date: '2026-05-25' })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('query_tara_balam')
    expect((params as Record<string, unknown>)['date']).toBe('2026-05-25')
  })

  it('calls query_tara_balam (not another tool name)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildTaraBalamEnvelope(SAMPLE_TARA_RESULT))

    await callTaraBalamForNative({ date: '1984-02-05' })

    const [toolName] = mockCall.mock.calls[0]
    expect(toolName).toBe('query_tara_balam')
  })

  it('forwards native birth date correctly', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildTaraBalamEnvelope({
      ...SAMPLE_TARA_RESULT,
      date: '1984-02-05',
      tara_count: 1,
      tara_name: 'Janma',
      score: 0.50,
    }))

    const result = await callTaraBalamForNative({ date: '1984-02-05' })
    expect((result as { isError?: boolean }).isError).toBeUndefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  it('returns ok result when primitive call succeeds', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildTaraBalamEnvelope(SAMPLE_TARA_RESULT))

    const result = await callTaraBalamForNative({ date: '2026-05-25' })

    expect((result as { isError?: boolean }).isError).toBeUndefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    expect(res.content.length).toBeGreaterThan(0)
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  it('returns error result when primitive call returns 500', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-tara-001',
        error: { class: 'internal', message: 'Engine error computing tara_bala' },
      },
    })

    const result = await callTaraBalamForNative({ date: '2026-05-25' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('returns error result when primitive call returns ok:false', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 422,
      envelope: {
        ok: false,
        trace_id: 'fail-tara-002',
        error: { class: 'validation', message: 'Invalid date format' },
      },
    })

    const result = await callTaraBalamForNative({ date: 'not-a-date' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('works for super_admin tier', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildTaraBalamEnvelope(SAMPLE_TARA_RESULT))

    const result = await callTaraBalamForNative(
      { date: '2026-05-25' },
      { user_uid: 'admin', audience_tier: 'super_admin', key_id: 'admin-key' }
    )
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  it('works for acharya tier', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildTaraBalamEnvelope(SAMPLE_TARA_RESULT))

    const result = await callTaraBalamForNative(
      { date: '2026-05-25' },
      { user_uid: 'acharya', audience_tier: 'acharya', key_id: 'acharya-key' }
    )
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })
})
