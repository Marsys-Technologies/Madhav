/**
 * query_chart_facts.test.ts — Tests for the query_chart_facts MCP tool.
 *
 * Covers:
 *   TR-P3-S2: populated_count field + include_empty_counts flag
 *
 *   AC.1 — include_empty_counts=true returns ALL categories from CHART_FACTS_CATEGORIES
 *           (including those with 0 rows) in rows_by_category
 *   AC.2 — Every category object in a batched response has a populated_count field (number)
 *   AC.3 — categories: ["deity_assignment"] single-batch returns populated_count >= 0
 *   AC.4 — include_empty_counts=false (default) only returns categories with populated_count > 0
 *           (i.e., only categories that had rows in the response)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryChartFacts, CHART_FACTS_CATEGORIES } from './query_chart_facts.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Builds a simple direct envelope (no ToolBundle wrapping) for the batched
 * query_chart_facts response. rows_by_category lives directly on result.
 *
 * This mirrors the simplest platform response shape that query_chart_facts
 * processes (the tool doesn't unwrap ToolBundle content strings — it reads
 * rows_by_category directly off result when batched).
 */
function buildBatchedEnvelope(rowsByCategory: Record<string, unknown[]>) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-qcf-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        rows_by_category: rowsByCategory,
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

/**
 * Builds a simple direct envelope for the single-category query_chart_facts response.
 * rows lives directly on result.
 */
function buildSingleEnvelope(rows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-qcf-002',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        rows,
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
      trace_id: 'trace-fail-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/**
 * Registers query_chart_facts on a stub MCP server and invokes the handler
 * directly, applying Zod validation (same as the MCP SDK would).
 */
async function callQueryChartFacts(
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

  registerQueryChartFacts(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_chart_facts handler was not registered')

  // Simulate Zod validation
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// Helper to parse MCP content text from the result.
// okResult(envelope) serializes the full envelope, so we return it directly.
// Callers access envelope.result.rows_by_category etc.
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// Helper to get the result sub-object from a parsed envelope
function getResultObj(result: unknown): Record<string, unknown> {
  const envelope = parseResult(result)
  return (envelope['result'] ?? {}) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_chart_facts — populated_count + include_empty_counts (TR-P3-S2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC.1: include_empty_counts=true returns ALL known categories ───────────

  it('AC.1 — include_empty_counts=true returns all CHART_FACTS_CATEGORIES including those with 0 rows', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    // First call (pre-query for all categories): return only a subset with data
    const preQueryRows: Record<string, unknown[]> = {
      deity_assignment: [{ fact_id: 'DA.001', category: 'deity_assignment', value_text: 'Shiva' }],
      shadbala: [{ fact_id: 'SB.001', category: 'shadbala', value_num: 7.5 }],
    }
    // Second call (main data query): same subset
    const mainRows: Record<string, unknown[]> = {
      deity_assignment: [{ fact_id: 'DA.001', category: 'deity_assignment', value_text: 'Shiva' }],
      shadbala: [{ fact_id: 'SB.001', category: 'shadbala', value_num: 7.5 }],
    }

    // The handler makes 2 calls when include_empty_counts=true:
    //   call 1 = full-category pre-query (batched, all CHART_FACTS_CATEGORIES)
    //   call 2 = actual args query (categories: [...], batched: true)
    mockCallPlatformPrimitive
      .mockResolvedValueOnce(buildBatchedEnvelope(preQueryRows))
      .mockResolvedValueOnce(buildBatchedEnvelope(mainRows))

    const result = await callQueryChartFacts({
      categories: ['deity_assignment', 'shadbala'],
      include_empty_counts: true,
    })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, unknown> | undefined

    // Must include all CHART_FACTS_CATEGORIES
    expect(rowsByCat).toBeDefined()
    for (const cat of CHART_FACTS_CATEGORIES) {
      expect(rowsByCat).toHaveProperty(cat)
    }
  })

  it('AC.1 — categories with 0 rows have empty rows array when include_empty_counts=true', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    // Pre-query: only 2 categories populated
    mockCallPlatformPrimitive
      .mockResolvedValueOnce(buildBatchedEnvelope({ deity_assignment: [{ fact_id: 'DA.001' }] }))
      .mockResolvedValueOnce(buildBatchedEnvelope({ deity_assignment: [{ fact_id: 'DA.001' }] }))

    const result = await callQueryChartFacts({
      categories: ['deity_assignment'],
      include_empty_counts: true,
    })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, { rows: unknown[]; populated_count: number }> | undefined

    // A category NOT in the pre-query response should exist with empty rows and count=0
    const missingCat = CHART_FACTS_CATEGORIES.find(c => c !== 'deity_assignment')!
    expect(rowsByCat).toHaveProperty(missingCat)
    const missingEntry = rowsByCat![missingCat]
    expect(Array.isArray(missingEntry.rows)).toBe(true)
    expect(missingEntry.rows.length).toBe(0)
    expect(missingEntry.populated_count).toBe(0)
  })

  // ── AC.2: every category has populated_count (number) ─────────────────────

  it('AC.2 — each category in batched response has a populated_count field that is a number', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    const rows: Record<string, unknown[]> = {
      planet: [
        { fact_id: 'PL.001', category: 'planet', value_text: 'Sun in Aries' },
        { fact_id: 'PL.002', category: 'planet', value_text: 'Moon in Taurus' },
      ],
      house: [
        { fact_id: 'HO.001', category: 'house', value_text: 'Ascendant Aquarius' },
      ],
    }

    // include_empty_counts=false (default) — only 1 call (main data)
    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope(rows))

    const result = await callQueryChartFacts({
      categories: ['planet', 'house'],
      // include_empty_counts defaults to false
    })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, { populated_count: number }> | undefined

    expect(rowsByCat).toBeDefined()
    for (const cat of Object.keys(rowsByCat!)) {
      expect(typeof rowsByCat![cat].populated_count).toBe('number')
    }
  })

  it('AC.2 — populated_count equals the number of rows returned for the category', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    const rows: Record<string, unknown[]> = {
      yoga: [
        { fact_id: 'YG.001', category: 'yoga', value_text: 'Hamsa Yoga' },
        { fact_id: 'YG.002', category: 'yoga', value_text: 'Bhadra Yoga' },
        { fact_id: 'YG.003', category: 'yoga', value_text: 'Ruchaka Yoga' },
      ],
      aspect: [
        { fact_id: 'AS.001', category: 'aspect', value_text: 'Saturn aspects Moon' },
      ],
    }

    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope(rows))

    const result = await callQueryChartFacts({ categories: ['yoga', 'aspect'] })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, { rows: unknown[]; populated_count: number }>

    expect(rowsByCat['yoga'].populated_count).toBe(3)
    expect(rowsByCat['aspect'].populated_count).toBe(1)
  })

  // ── AC.3: single category categories: ["deity_assignment"] ────────────────

  it('AC.3 — categories: ["deity_assignment"] returns populated_count >= 0 for deity_assignment', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    const rows: Record<string, unknown[]> = {
      deity_assignment: [
        { fact_id: 'DA.001', category: 'deity_assignment', value_text: 'Shiva', planet: 'Saturn' },
        { fact_id: 'DA.002', category: 'deity_assignment', value_text: 'Vishnu', planet: 'Jupiter' },
      ],
    }

    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope(rows))

    const result = await callQueryChartFacts({ categories: ['deity_assignment'] })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, { populated_count: number }>

    expect(rowsByCat).toHaveProperty('deity_assignment')
    expect(typeof rowsByCat['deity_assignment'].populated_count).toBe('number')
    expect(rowsByCat['deity_assignment'].populated_count).toBeGreaterThanOrEqual(0)
  })

  // ── AC.4: include_empty_counts=false only returns categories with rows ─────

  it('AC.4 — include_empty_counts=false (default) only returns categories that have rows', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    // Only 2 of the 37 known categories are returned
    const rows: Record<string, unknown[]> = {
      shadbala: [{ fact_id: 'SB.001', category: 'shadbala', value_num: 7.5 }],
      planet: [{ fact_id: 'PL.001', category: 'planet', value_text: 'Sun in Aries' }],
    }

    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope(rows))

    const result = await callQueryChartFacts({
      categories: ['shadbala', 'planet'],
      include_empty_counts: false,
    })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, unknown>

    // Should only contain the 2 returned categories
    const keys = Object.keys(rowsByCat)
    expect(keys).toHaveLength(2)
    expect(keys).toContain('shadbala')
    expect(keys).toContain('planet')

    // Should NOT contain categories not in the response
    const absentCat = CHART_FACTS_CATEGORIES.find(c => c !== 'shadbala' && c !== 'planet')!
    expect(keys).not.toContain(absentCat)
  })

  it('AC.4 — include_empty_counts=false categories all have populated_count > 0', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    const rows: Record<string, unknown[]> = {
      bhava_bala: [{ fact_id: 'BB.001', category: 'bhava_bala', value_num: 5.2 }],
      upagraha: [
        { fact_id: 'UG.001', category: 'upagraha', value_text: 'Gulika in 8H' },
        { fact_id: 'UG.002', category: 'upagraha', value_text: 'Mandi in 9H' },
      ],
    }

    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope(rows))

    const result = await callQueryChartFacts({
      categories: ['bhava_bala', 'upagraha'],
    })

    const resultObj = getResultObj(result)
    const rowsByCat = resultObj['rows_by_category'] as Record<string, { populated_count: number }>

    for (const cat of Object.keys(rowsByCat)) {
      expect(rowsByCat[cat].populated_count).toBeGreaterThan(0)
    }
  })

  // ── Single-category mode (category: string) ────────────────────────────────

  it('single category mode — populated_count is set in result', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    const singleRows = [
      { fact_id: 'SB.001', category: 'shadbala', planet: 'Saturn', value_num: 7.5 },
      { fact_id: 'SB.002', category: 'shadbala', planet: 'Jupiter', value_num: 6.2 },
    ]

    mockCallPlatformPrimitive.mockResolvedValueOnce(buildSingleEnvelope(singleRows))

    const result = await callQueryChartFacts({ category: 'shadbala' })

    const resultObj = getResultObj(result)
    expect(typeof resultObj['populated_count']).toBe('number')
    expect(resultObj['populated_count']).toBe(2)
  })

  it('single category mode with include_empty_counts=true exposes all_category_counts', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

    // Pre-query (all categories batched) then main query
    const preQueryData: Record<string, unknown[]> = {
      shadbala: [{ fact_id: 'SB.001' }],
      planet: [{ fact_id: 'PL.001' }, { fact_id: 'PL.002' }],
    }
    mockCallPlatformPrimitive
      .mockResolvedValueOnce(buildBatchedEnvelope(preQueryData))
      .mockResolvedValueOnce(buildSingleEnvelope([{ fact_id: 'SB.001', category: 'shadbala' }]))

    const result = await callQueryChartFacts({
      category: 'shadbala',
      include_empty_counts: true,
    })

    const resultObj = getResultObj(result)
    expect(typeof resultObj['populated_count']).toBe('number')
    // all_category_counts should list every known category
    const allCounts = resultObj['all_category_counts'] as Record<string, number> | undefined
    expect(allCounts).toBeDefined()
    for (const cat of CHART_FACTS_CATEGORIES) {
      expect(allCounts).toHaveProperty(cat)
      expect(typeof allCounts![cat]).toBe('number')
    }
  })

  // ── Error handling ─────────────────────────────────────────────────────────

  it('returns error result when primitive call fails', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    // When include_empty_counts=false (default), only 1 primitive call is made.
    mockCallPlatformPrimitive.mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callQueryChartFacts({ categories: ['planet'] })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Zod schema validation ──────────────────────────────────────────────────

  it('include_empty_counts defaults to false when not provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope({
      planet: [{ fact_id: 'PL.001' }],
    }))

    // Should not throw; only 1 callPlatformPrimitive call (no pre-query)
    await callQueryChartFacts({ categories: ['planet'] })

    // With include_empty_counts=false, only the main data call is made
    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
  })

  it('limit defaults to 50 when not provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValueOnce(buildBatchedEnvelope({}))

    await callQueryChartFacts({ categories: ['yoga'] })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(50)
  })

  it('Zod rejects house < 1', async () => {
    const result = await callQueryChartFacts({ category: 'planet', house: 0 })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('Zod rejects house > 12', async () => {
    const result = await callQueryChartFacts({ category: 'planet', house: 13 })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })
})
