/**
 * cross_school_lookup.test.ts — Regression tests for the cross_school_lookup MCP tool.
 *
 * Tests the C3 bug fix (TR-P2-S2): the wrapper now correctly forwards the `claim`
 * param as `topic` to callPlatformPrimitive, rather than allowing the platform to
 * fall back to the static string "surgical_primitive:cross_school_lookup".
 *
 * Also verifies:
 *   - The response always includes `unrepresented_schools: ["nadi","bnn","yogini"]`
 *   - No top-level `error` key when the primitive returns no matches (returns
 *     empty results instead of an error envelope)
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
import { registerCrossSchoolLookup } from './cross_school_lookup.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildSuccessEnvelope(schoolResults: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-cross-school-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'cross-school-bundle-id',
        tool_name: 'multi_school_signal_lookup',
        tool_version: '1.0.0',
        invocation_params: {},
        results: schoolResults.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'school_signal_coverage',
          source_version: '1.0',
          confidence: 0.85,
          significance: 0.8,
        })),
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:cross-school-test',
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

function buildEmptyEnvelope() {
  return buildSuccessEnvelope([])
}

function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-cross-school-err',
      error: { class: 'internal', message: 'DB error in cross_school_lookup' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callCrossSchoolLookup(
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

  registerCrossSchoolLookup(stubServer, () => principal)

  if (!capturedHandler) throw new Error('cross_school_lookup handler was not registered')

  // Simulate Zod validation as the MCP SDK would perform
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// Helper: parse the text content from an MCP result
function parseResultContent(result: unknown): unknown {
  const r = result as { content?: Array<{ type: string; text: string }>; isError?: boolean }
  if (!r.content?.[0]?.text) return null
  return JSON.parse(r.content[0].text)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('cross_school_lookup — C3 claim forwarding fix + Nadi/BNN/Yogini note', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1 + AC.3: claim is forwarded as `topic` in toolParams (not as a static string)
  it('AC.1/AC.3 — claim is forwarded as topic in toolParams (not static string)', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([
      { school: 'parashara', coverage_type: 'primary', confidence: 0.95, matching_signals: ['SIG.MSR.001'] },
    ]))

    await callCrossSchoolLookup({ claim: 'Jupiter lord of 9H' })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('cross_school_lookup')

    // The topic param must equal the user's claim — not the static fallback string
    const typedParams = params as Record<string, unknown>
    expect(typedParams['topic']).toBe('Jupiter lord of 9H')
    expect(typedParams['topic']).not.toBe('surgical_primitive:cross_school_lookup')
  })

  // AC.1: claim is also preserved as `claim` in toolParams
  it('AC.1 — claim is preserved as claim in toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([]))

    await callCrossSchoolLookup({ claim: 'Saturn in 10th house delays career until 36' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['claim']).toBe('Saturn in 10th house delays career until 36')
  })

  // AC.2: response always includes unrepresented_schools: ["nadi","bnn","yogini"]
  it('AC.2 — response includes unrepresented_schools: ["nadi","bnn","yogini"]', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([
      { school: 'kp', coverage_type: 'secondary', confidence: 0.75, matching_signals: [] },
    ]))

    const result = await callCrossSchoolLookup({ claim: 'Moon-Ketu conjunction in 4th house' })

    const parsed = parseResultContent(result) as {
      result?: { unrepresented_schools?: string[] }
    }
    expect(parsed?.result?.unrepresented_schools).toEqual(['nadi', 'bnn', 'yogini'])
  })

  // AC.2: unrepresented_schools note is also present
  it('AC.2 — response includes unrepresented_schools_note explaining the gap', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callCrossSchoolLookup({ claim: 'Venus in 7H indicates early marriage' })

    const parsed = parseResultContent(result) as {
      result?: { unrepresented_schools_note?: string }
    }
    expect(parsed?.result?.unrepresented_schools_note).toContain('not in the corpus')
  })

  // No top-level error key when primitive returns empty matches
  it('AC.2 — no top-level error key when primitive returns no school results (empty result)', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEmptyEnvelope())

    const result = await callCrossSchoolLookup({ claim: 'some obscure claim with no matching signals' })

    // Must not be an error result
    expect((result as { isError?: boolean }).isError).toBeUndefined()

    // Must not have a top-level `error` key in the parsed content
    const parsed = parseResultContent(result) as Record<string, unknown>
    expect(parsed?.['error']).toBeUndefined()
  })

  // Optional schools filter is forwarded when provided
  it('schools filter is forwarded to toolParams when provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([]))

    await callCrossSchoolLookup({
      claim: 'Rahu in 1H increases ambition',
      schools: ['parashara', 'jaimini'],
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['schools']).toEqual(['parashara', 'jaimini'])
  })

  // Schools filter is absent from toolParams when not provided
  it('schools key is absent from toolParams when no schools filter given', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([]))

    await callCrossSchoolLookup({ claim: 'any claim' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(Object.hasOwn(params, 'schools')).toBe(false)
  })

  // Zod rejects invalid school values
  it('Zod rejects invalid school enum value', async () => {
    const result = await callCrossSchoolLookup({ claim: 'valid claim', schools: ['not_a_school'] })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // Error path: when primitive returns 500, errorResult is returned
  it('returns errorResult when primitive call fails (status >= 400)', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildErrorEnvelope())

    const result = await callCrossSchoolLookup({ claim: 'Jupiter lord of 9H' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.5: each school entry in results has school_count as a number
  it('AC.5 — each school entry in results has school_count as a number', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSuccessEnvelope([
      { school: 'parashara', coverage_type: 'primary', confidence: 0.95, matching_signals: ['SIG.MSR.001'] },
      { school: 'jaimini', coverage_type: 'secondary', confidence: 0.80, matching_signals: [] },
    ]))

    const result = await callCrossSchoolLookup({ claim: 'Saturn in 10th house delays career' })
    const parsed = parseResultContent(result) as {
      result?: { results?: Array<Record<string, unknown>> }
    }
    const entries = parsed?.result?.results ?? []
    expect(entries.length).toBeGreaterThan(0)
    for (const entry of entries) {
      expect(typeof entry['school_count']).toBe('number')
    }
  })

  // Different claims produce different topic values (not the same static string)
  it('different claims produce different topic values in toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildEmptyEnvelope())

    await callCrossSchoolLookup({ claim: 'claim alpha' })
    await callCrossSchoolLookup({ claim: 'claim beta' })

    const topicA = (mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>)['topic']
    const topicB = (mockCallPlatformPrimitive.mock.calls[1][1] as Record<string, unknown>)['topic']
    expect(topicA).toBe('claim alpha')
    expect(topicB).toBe('claim beta')
    expect(topicA).not.toBe(topicB)
  })
})
