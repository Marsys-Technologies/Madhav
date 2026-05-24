/**
 * chart_summary.test.ts — Regression tests for the chart_summary MCP tool.
 *
 * Tests the ToolBundle envelope unwrap fix (C1 bug):
 *   The wrapper must read results[0].content (a JSON string) from the ToolBundle
 *   rather than reading rows_by_category directly off envelope.result.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerChartSummaryTool } from './chart_summary.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Builds a realistic ToolBundle envelope as returned by callPlatformPrimitive
 * when the platform route calls chart_facts_query with batched=true.
 *
 * The platform route does: result: toolResult (the raw ToolBundle).
 * For batched queries, ToolBundle.results[0].content is a JSON string containing
 * { rows_by_category: { [category]: row[] } }.
 */
function buildToolBundleEnvelope(rowsByCategory: Record<string, unknown[]>) {
  const toolBundle = {
    tool_bundle_id: 'test-bundle-id',
    tool_name: 'chart_facts_query',
    tool_version: '1.0.0',
    invocation_params: { category: ['birth_metadata', 'yoga'], batched: true, limit: 200 },
    results: [
      {
        content: JSON.stringify({ rows_by_category: rowsByCategory }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 1.0,
        significance: 0.9,
      },
    ],
    served_from_cache: false,
    latency_ms: 42,
    result_hash: 'sha256:abc123',
    schema_version: '1.0',
  }

  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-test-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: toolBundle,         // <-- this is what the fix must unwrap correctly
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

/**
 * Minimal tool call capture: registers the chart_summary tool on a stub MCP
 * server and invokes the handler directly.
 */
async function callChartSummary(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null

  // Stub MCP server that captures the registered handler
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

  registerChartSummaryTool(stubServer, () => principal)

  if (!capturedHandler) throw new Error('chart_summary handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('chart_summary — ToolBundle envelope unwrap (C1 fix)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns non-empty rows_by_category when primitive returns ToolBundle with results[0].content', async () => {
    const sampleRowsByCategory = {
      birth_metadata: [
        { fact_id: 'BM.001', category: 'birth_metadata', value_text: '1984-02-05', divisional_chart: 'D1' },
      ],
      yoga: [
        { fact_id: 'YG.001', category: 'yoga', value_text: 'Hamsa Yoga', divisional_chart: 'D1' },
        { fact_id: 'YG.002', category: 'yoga', value_text: 'Bhadra Yoga', divisional_chart: 'D1' },
      ],
    }

    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    // Both bulk and divisional calls return realistic ToolBundle envelopes
    mockCallPlatformPrimitive.mockResolvedValue(buildToolBundleEnvelope(sampleRowsByCategory))

    const result = await callChartSummary({ chart_id: NATIVE_CHART_ID, tier: 'super_admin' })

    // Parse the MCP content text
    const content = (result as { content: Array<{ text: string }> }).content[0].text
    const parsed = JSON.parse(content)

    // AC.2: rows_by_category must be an object with at least one key
    expect(parsed.rows_by_category).toBeDefined()
    expect(typeof parsed.rows_by_category).toBe('object')
    expect(Object.keys(parsed.rows_by_category).length).toBeGreaterThan(0)

    // Must have birth_metadata key
    expect(parsed.rows_by_category.birth_metadata).toBeDefined()
    expect(Array.isArray(parsed.rows_by_category.birth_metadata)).toBe(true)
    expect(parsed.rows_by_category.birth_metadata.length).toBeGreaterThan(0)
  })

  it('does not have a top-level error key in the response', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(
      buildToolBundleEnvelope({ birth_metadata: [{ fact_id: 'BM.001', category: 'birth_metadata' }] })
    )

    const result = await callChartSummary({ chart_id: NATIVE_CHART_ID })
    const content = (result as { content: Array<{ text: string }>; isError?: boolean }).content[0].text
    const parsed = JSON.parse(content)

    // AC.2: no top-level error key
    expect(parsed.error).toBeUndefined()
    expect((result as { isError?: boolean }).isError).toBeFalsy()
  })

  it('regression: before fix, direct envelope.result.rows_by_category read returns empty (demonstrates the bug)', () => {
    // This test documents the old buggy read path — reading rows_by_category directly
    // off the ToolBundle (envelope.result) returns undefined.
    const toolBundle = {
      results: [{ content: JSON.stringify({ rows_by_category: { birth_metadata: [{ fact_id: 'BM.001' }] } }) }],
    }
    // OLD (wrong): toolBundle['rows_by_category'] → undefined
    expect((toolBundle as Record<string, unknown>)['rows_by_category']).toBeUndefined()
    // NEW (correct): parse results[0].content
    const content = (toolBundle.results[0] as { content: string }).content
    const parsed = JSON.parse(content)
    expect(parsed.rows_by_category).toBeDefined()
    expect(Object.keys(parsed.rows_by_category).length).toBeGreaterThan(0)
  })

  it('handles empty rows_by_category gracefully (zero results from DB)', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildToolBundleEnvelope({}))

    const result = await callChartSummary({ chart_id: NATIVE_CHART_ID })
    const content = (result as { content: Array<{ text: string }> }).content[0].text
    const parsed = JSON.parse(content)

    // Should return ok:true with empty rows_by_category (not crash)
    expect(parsed).toBeDefined()
    expect(parsed.total_rows).toBe(0)
    expect(parsed.rows_by_category).toEqual({})
  })

  it('passes chart_id to the primitive call', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(
      buildToolBundleEnvelope({ birth_metadata: [] })
    )

    await callChartSummary({ chart_id: NATIVE_CHART_ID })

    // chart_id should appear in at least one of the primitive calls
    const calls = mockCallPlatformPrimitive.mock.calls
    expect(calls.length).toBeGreaterThan(0)
    const firstCall = calls[0]
    const params = firstCall[1] as Record<string, unknown>
    expect(params['chart_id']).toBe(NATIVE_CHART_ID)
  })

  it('returns error result when the primitive call fails', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'trace-fail-001',
        error: { class: 'internal', message: 'DB connection lost', remediation: 'retry' },
      },
    })

    const result = await callChartSummary({ chart_id: NATIVE_CHART_ID })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })
})
