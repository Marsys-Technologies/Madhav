import 'server-only'

import { query } from '@/lib/db/client'

/**
 * PERF-S3 — Retrieval Utilization & Planner Routing aggregation.
 *
 * Reads plan_tools_selected from performance_queries to compute per-tool
 * call counts over a rolling time window and detect orphaned tools.
 */

// Hardcoded to avoid circular import from @/lib/retrieve (server-only singleton)
export const ALL_TOOL_NAMES: readonly string[] = [
  'msr_sql',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'temporal',
  'query_msr_aggregate',
  'cgm_graph_walk',
  'manifest_query',
  'vector_search',
  'kp_query',
  'saham_query',
  'divisional_query',
  'chart_facts_query',
  'cross_varga_dignity_query',
  'domain_report_query',
  'remedial_codex_query',
  'timeline_query',
  'query_signal_state',
  'query_kp_ruling_planets',
  'query_varshaphala',
  'lel_query',
  'classical_text_search',
  'classical_attribution_lookup',
  'multi_school_signal_lookup',
  'convergence_score_lookup',
  'query_ephemeris',
  'query_panchanga',
  'query_transit_event',
  'query_dasha_periods',
  'query_muhurat',
  'query_jaimini_drishti',
  'query_v7_additions',
] as const

export interface ToolStats {
  tool_name: string
  call_count: number
  last_called_at: string | null
  is_orphaned: boolean
}

export interface RetrievalStats {
  window_hours: number
  generated_at: string
  tools: ToolStats[]
  orphaned_tools: string[]
  total_queries: number
  coverage_scoreboard: {
    total_tools: number
    tools_called_at_least_once: number
    pct_coverage: number
  }
  top_combinations: Array<{ tools: string[]; count: number }>
}

interface RawRow {
  plan_tools_selected: string | null
  created_at: string
}

export async function getRetrievalStats(windowHours: number = 168): Promise<RetrievalStats> {
  const generated_at = new Date().toISOString()

  // Fetch rows in window — limit 1000 for combination aggregation
  const sql = `
    SELECT plan_tools_selected, created_at
    FROM performance_queries
    WHERE created_at > NOW() - INTERVAL '${Math.floor(windowHours)} hours'
    ORDER BY created_at DESC
    LIMIT 1000
  `

  let rawRows: RawRow[] = []
  try {
    const result = await query<RawRow>(sql)
    rawRows = result.rows
  } catch (err) {
    console.error('[retrieval_aggregator] DB query failed', err)
    // Return graceful empty response
  }

  // Build per-tool tallies
  const countMap = new Map<string, number>()
  const lastCalledMap = new Map<string, string>()

  // Seed all known tools with 0
  for (const name of ALL_TOOL_NAMES) {
    countMap.set(name, 0)
  }

  // Aggregate combinations (sorted tool-set string → count)
  const combinationMap = new Map<string, { tools: string[]; count: number }>()

  for (const row of rawRows) {
    if (!row.plan_tools_selected) continue

    let toolList: string[]
    try {
      toolList = typeof row.plan_tools_selected === 'string'
        ? (JSON.parse(row.plan_tools_selected) as string[])
        : (row.plan_tools_selected as unknown as string[])
    } catch {
      continue
    }

    if (!Array.isArray(toolList)) continue

    for (const toolName of toolList) {
      if (typeof toolName !== 'string') continue
      countMap.set(toolName, (countMap.get(toolName) ?? 0) + 1)
      // Keep only the first (most-recent due to DESC sort) occurrence
      if (!lastCalledMap.has(toolName)) {
        lastCalledMap.set(toolName, row.created_at)
      }
    }

    // Top combinations
    const sortedTools = [...toolList].sort()
    const key = JSON.stringify(sortedTools)
    const existing = combinationMap.get(key)
    if (existing) {
      existing.count += 1
    } else {
      combinationMap.set(key, { tools: sortedTools, count: 1 })
    }
  }

  // Build ToolStats array
  const tools: ToolStats[] = Array.from(countMap.entries())
    .map(([tool_name, call_count]) => ({
      tool_name,
      call_count,
      last_called_at: lastCalledMap.get(tool_name) ?? null,
      is_orphaned: call_count === 0,
    }))
    .sort((a, b) => {
      if (b.call_count !== a.call_count) return b.call_count - a.call_count
      return a.tool_name.localeCompare(b.tool_name)
    })

  const orphaned_tools = tools.filter(t => t.is_orphaned).map(t => t.tool_name)
  const tools_called_at_least_once = tools.filter(t => !t.is_orphaned).length
  const total_tools = ALL_TOOL_NAMES.length
  const pct_coverage = total_tools > 0
    ? Math.round((tools_called_at_least_once / total_tools) * 100)
    : 0

  // Top 5 combinations
  const top_combinations = Array.from(combinationMap.values())
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)

  return {
    window_hours: windowHours,
    generated_at,
    tools,
    orphaned_tools,
    total_queries: rawRows.length,
    coverage_scoreboard: {
      total_tools,
      tools_called_at_least_once,
      pct_coverage,
    },
    top_combinations,
  }
}
