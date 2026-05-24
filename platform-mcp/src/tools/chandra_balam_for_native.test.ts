/**
 * chandra_balam_for_native.test.ts — Unit tests for the chandra_balam_for_native MCP tool.
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
import { registerChandraBalamForNative } from './chandra_balam_for_native.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildChandraBalamEnvelope(resultData: unknown) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-chandra-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'chandra-bundle-id',
        tool_name: 'query_chandra_balam',
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
        result_hash: 'sha256:chandra-test',
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

const SAMPLE_CHANDRA_RESULT = {
  date: '2026-05-25',
  chandra_bala_score: 0.90,
  interpretation: 'Auspicious — Moon in 6th from birth Moon sign (Sadhaka; achievement).',
  moon_nakshatra: 'Purva Phalguni',
  moon_sign: 'Leo',
  moon_sign_id: 5,
  birth_moon_sign: 'Pisces',
  birth_moon_sign_id: 12,
  position_from_birth_moon: 6,
}

async function callChandraBalamForNative(
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

  registerChandraBalamForNative(stubServer, () => principal)

  if (!capturedHandler) throw new Error('chandra_balam_for_native handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('chandra_balam_for_native', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('forwards date param to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildChandraBalamEnvelope(SAMPLE_CHANDRA_RESULT))

    await callChandraBalamForNative({ date: '2026-05-25' })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('query_chandra_balam')
    expect((params as Record<string, unknown>)['date']).toBe('2026-05-25')
  })

  it('calls query_chandra_balam (not another tool name)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildChandraBalamEnvelope(SAMPLE_CHANDRA_RESULT))

    await callChandraBalamForNative({ date: '2026-05-25' })

    const [toolName] = mockCall.mock.calls[0]
    expect(toolName).toBe('query_chandra_balam')
  })

  it('query_chandra_balam is distinct from query_tara_balam (different tool name)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildChandraBalamEnvelope(SAMPLE_CHANDRA_RESULT))

    await callChandraBalamForNative({ date: '2026-05-25' })

    const [toolName] = mockCall.mock.calls[0]
    expect(toolName).not.toBe('query_tara_balam')
    expect(toolName).not.toBe('query_panchanga')
    expect(toolName).not.toBe('query_muhurat')
  })

  it('returns ok result when primitive call succeeds', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildChandraBalamEnvelope(SAMPLE_CHANDRA_RESULT))

    const result = await callChandraBalamForNative({ date: '2026-05-25' })

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
        trace_id: 'fail-chandra-001',
        error: { class: 'internal', message: 'Engine error computing chandra_bala' },
      },
    })

    const result = await callChandraBalamForNative({ date: '2026-05-25' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('returns error result when primitive call returns ok:false with 422', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 422,
      envelope: {
        ok: false,
        trace_id: 'fail-chandra-002',
        error: { class: 'validation', message: 'Invalid date format' },
      },
    })

    const result = await callChandraBalamForNative({ date: 'bad-date' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('works for native birth date (Moon in same sign as birth — position 1)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildChandraBalamEnvelope({
      ...SAMPLE_CHANDRA_RESULT,
      date: '1984-02-05',
      chandra_bala_score: 0.80,
      moon_sign: 'Pisces',
      moon_sign_id: 12,
      position_from_birth_moon: 1,
      interpretation: 'Neutral — Moon in same sign as birth Moon (Janma position).',
    }))

    const result = await callChandraBalamForNative({ date: '1984-02-05' })
    expect((result as { isError?: boolean }).isError).toBeUndefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  it('works for acharya tier', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildChandraBalamEnvelope(SAMPLE_CHANDRA_RESULT))

    const result = await callChandraBalamForNative(
      { date: '2026-05-25' },
      { user_uid: 'acharya', audience_tier: 'acharya', key_id: 'acharya-key' }
    )
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })
})
