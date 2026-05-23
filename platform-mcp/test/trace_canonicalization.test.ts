/**
 * trace_canonicalization.test.ts — Unit tests for trace name canonicalization.
 *
 * Verifies that list_recent_queries returns MCP-facing tool names
 * (e.g. query_chart_facts) instead of retrieval-side names
 * (e.g. chart_facts_query) when the mcp_tool column (migration 116) is present.
 *
 * Tests the name-resolution logic from platform/src/app/api/mcp/recent/route.ts
 * by directly exercising the three-tier fallback:
 *   1. mcp_tool column (canonical, migration 116)
 *   2. data_summary.mcp_tool (written by primitives route since MCPT v3.2)
 *   3. step_name (retrieval-side fallback for pre-MCPT-v3.2 rows)
 */

import { describe, it, expect } from 'vitest'

// ── Types mirroring platform/src/app/api/mcp/recent/route.ts ──────────────────

interface DbTraceRow {
  query_id: string
  created_at: string
  step_name: string
  mcp_tool: string | null
  data_summary: Record<string, unknown> | null
  payload: { items?: Array<{ text?: string }> } | null
}

interface RecentQueryRow {
  trace_id: string
  created_at: string
  tool: string
  source: string
  query_summary: string
}

// ── Name resolution logic (mirrors recent/route.ts) ───────────────────────────

/**
 * Pure function that mirrors the tool-name resolution in recent/route.ts.
 * Keeps the test independent of the platform Next.js env.
 */
function resolveToolName(row: DbTraceRow): string {
  const dataSummary = row.data_summary as Record<string, unknown> | null
  return (
    row.mcp_tool ??
    (dataSummary?.mcp_tool as string | undefined) ??
    row.step_name ??
    'unknown'
  )
}

function buildRecentQueryRow(row: DbTraceRow): RecentQueryRow {
  const dataSummary = row.data_summary as Record<string, unknown> | null
  const mcpTool = resolveToolName(row)
  const source = (dataSummary?.source as string | undefined) ?? 'mcp'

  let querySummary = ''
  if (dataSummary && typeof dataSummary.query_summary === 'string' && dataSummary.query_summary) {
    querySummary = dataSummary.query_summary as string
  }
  if (!querySummary) {
    const items = (row.payload as { items?: Array<{ text?: string }> } | null)?.items ?? []
    for (const item of items) {
      if (item.text && item.text.includes('"key_id"')) {
        try {
          JSON.parse(item.text)
          // Not a query text — skip
        } catch {
          if (item.text.length > 0 && !item.text.startsWith('{')) {
            querySummary = item.text.slice(0, 80)
            break
          }
        }
      }
    }
  }
  if (!querySummary) {
    querySummary = `${mcpTool} call`
  }

  return {
    trace_id: row.query_id,
    created_at: row.created_at,
    tool: mcpTool,
    source,
    query_summary: querySummary,
  }
}

// ── Fixtures ──────────────────────────────────────────────────────────────────

const TRACE_ID = 'a4f3e2b1-0c1d-4e5f-a6b7-c8d9e0f1a2b3'
const CREATED_AT = '2026-05-23T10:00:00.000Z'

/** Row as written by the primitives route after migration 116 is applied. */
const rowWithMcpToolColumn: DbTraceRow = {
  query_id: TRACE_ID,
  created_at: CREATED_AT,
  step_name: 'chart_facts_query',         // retrieval-side name
  mcp_tool: 'query_chart_facts',          // MCP-facing name (migration 116 column)
  data_summary: {
    tool_name: 'chart_facts_query',
    mcp_tool: 'query_chart_facts',
    result: 'mcp_primitive:query_chart_facts',
    query_summary: 'chart facts for house 7',
    source: 'mcp_primitive',
  },
  payload: {
    items: [
      {
        id: TRACE_ID,
        source: 'mcp_primitive',
        layer: 'system',
        token_estimate: 0,
        text: JSON.stringify({ surgical: true, mcp_tool: 'query_chart_facts', key_id: 'key-abc' }),
        score: 1,
      },
    ],
  },
}

/** Row written by MCPT v3.2 primitives route (mcp_tool in data_summary) but
 * before migration 116 column exists (mcp_tool column is NULL). */
const rowWithDataSummaryMcpToolOnly: DbTraceRow = {
  query_id: TRACE_ID,
  created_at: CREATED_AT,
  step_name: 'chart_facts_query',
  mcp_tool: null,                         // column absent (pre-migration)
  data_summary: {
    tool_name: 'chart_facts_query',
    mcp_tool: 'query_chart_facts',
    result: 'mcp_primitive:query_chart_facts',
    source: 'mcp_primitive',
  },
  payload: {
    items: [
      {
        id: TRACE_ID,
        source: 'mcp_primitive',
        layer: 'system',
        token_estimate: 0,
        text: JSON.stringify({ surgical: true, mcp_tool: 'query_chart_facts', key_id: 'key-abc' }),
        score: 1,
      },
    ],
  },
}

/** Row written before MCPT v3.2 — no mcp_tool anywhere, only step_name. */
const rowWithStepNameOnly: DbTraceRow = {
  query_id: TRACE_ID,
  created_at: CREATED_AT,
  step_name: 'chart_facts_query',
  mcp_tool: null,
  data_summary: {
    tool_name: 'chart_facts_query',
    result: 'mcp_primitive:query_chart_facts',
    source: 'mcp_primitive',
  },
  payload: {
    items: [
      {
        id: TRACE_ID,
        source: 'mcp_primitive',
        layer: 'system',
        token_estimate: 0,
        text: JSON.stringify({ surgical: true, key_id: 'key-abc' }),
        score: 1,
      },
    ],
  },
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('trace name canonicalization — resolveToolName', () => {
  it('returns mcp_tool column when present (migration 116)', () => {
    const tool = resolveToolName(rowWithMcpToolColumn)
    expect(tool).toBe('query_chart_facts')
    expect(tool).not.toBe('chart_facts_query')
  })

  it('returns data_summary.mcp_tool when mcp_tool column is null', () => {
    const tool = resolveToolName(rowWithDataSummaryMcpToolOnly)
    expect(tool).toBe('query_chart_facts')
    expect(tool).not.toBe('chart_facts_query')
  })

  it('falls back to step_name when mcp_tool is absent everywhere', () => {
    const tool = resolveToolName(rowWithStepNameOnly)
    expect(tool).toBe('chart_facts_query')
  })

  it('returns unknown when all three sources are null/undefined', () => {
    // The ?? operator only falls through on null/undefined, not empty string.
    // A row with step_name = null and no mcp_tool returns 'unknown'.
    const emptyRow: DbTraceRow = {
      query_id: TRACE_ID,
      created_at: CREATED_AT,
      // Cast null to satisfy the non-null type — simulates a DB row with no step_name
      step_name: null as unknown as string,
      mcp_tool: null,
      data_summary: null,
      payload: null,
    }
    const tool = resolveToolName(emptyRow)
    expect(tool).toBe('unknown')
  })

  it('mcp_tool column takes priority over data_summary.mcp_tool', () => {
    const rowWithBoth: DbTraceRow = {
      ...rowWithMcpToolColumn,
      mcp_tool: 'query_chart_facts',
      data_summary: {
        ...rowWithMcpToolColumn.data_summary,
        mcp_tool: 'some_other_value',  // should be ignored
      },
    }
    expect(resolveToolName(rowWithBoth)).toBe('query_chart_facts')
  })
})

describe('list_recent_queries returns MCP-facing names', () => {
  it('returns tool: "query_chart_facts" not "chart_facts_query" when mcp_tool column present', () => {
    const result = buildRecentQueryRow(rowWithMcpToolColumn)
    expect(result.tool).toBe('query_chart_facts')
    expect(result.tool).not.toBe('chart_facts_query')
  })

  it('returns tool: "query_chart_facts" via data_summary fallback when column absent', () => {
    const result = buildRecentQueryRow(rowWithDataSummaryMcpToolOnly)
    expect(result.tool).toBe('query_chart_facts')
    expect(result.tool).not.toBe('chart_facts_query')
  })

  it('falls back to step_name for pre-MCPT-v3.2 rows', () => {
    const result = buildRecentQueryRow(rowWithStepNameOnly)
    expect(result.tool).toBe('chart_facts_query')
  })

  it('populates trace_id from query_id', () => {
    const result = buildRecentQueryRow(rowWithMcpToolColumn)
    expect(result.trace_id).toBe(TRACE_ID)
  })

  it('uses data_summary.query_summary when present', () => {
    const result = buildRecentQueryRow(rowWithMcpToolColumn)
    expect(result.query_summary).toBe('chart facts for house 7')
  })

  it('falls back to "<tool> call" summary when query_summary absent', () => {
    const result = buildRecentQueryRow(rowWithDataSummaryMcpToolOnly)
    expect(result.query_summary).toBe('query_chart_facts call')
  })

  it('detects mcp_primitive source from data_summary', () => {
    const result = buildRecentQueryRow(rowWithMcpToolColumn)
    expect(result.source).toBe('mcp_primitive')
  })
})

describe('other MCP tool name mappings', () => {
  const toolMappings = [
    { step_name: 'msr_sql', mcp_tool: 'query_signals' },
    { step_name: 'vector_search', mcp_tool: 'vector_search' },
    { step_name: 'cgm_graph_walk', mcp_tool: 'get_cgm_subgraph' },
    { step_name: 'temporal', mcp_tool: 'query_dasha_periods' },
    { step_name: 'lel_query', mcp_tool: 'lel_query' },
  ]

  for (const { step_name, mcp_tool } of toolMappings) {
    it(`resolves ${step_name} → ${mcp_tool} via mcp_tool column`, () => {
      const row: DbTraceRow = {
        query_id: TRACE_ID,
        created_at: CREATED_AT,
        step_name,
        mcp_tool,
        data_summary: { tool_name: step_name, mcp_tool, source: 'mcp_primitive' },
        payload: null,
      }
      expect(resolveToolName(row)).toBe(mcp_tool)
    })
  }
})
