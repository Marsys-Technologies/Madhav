/**
 * retrieval_utilization_aggregator.ts
 *
 * Pure aggregation helpers for the Retrieval Utilization + Planner Routing
 * sections on /performance. No external dependencies.
 */

// ── Retrieval utilization ─────────────────────────────────────────────────────

/**
 * Aggregates `performance_queries` rows into per-tool 24-bucket call counts
 * (bucketed by the hour of `created_at`).
 *
 * @param performanceQueries - Array of performance_queries rows. Expected fields:
 *   - `created_at`: ISO-8601 timestamp string
 *   - `plan_tools_selected`: JSON string (string[]) or null
 * @returns Record<toolName, number[24]>
 */
export function aggregateRetrievalUtilization(
  performanceQueries: Array<Record<string, unknown>>,
): Record<string, number[]> {
  const result: Record<string, number[]> = {}

  for (const row of performanceQueries) {
    // Parse hour bucket from created_at
    const createdAt = row['created_at']
    const hour = createdAt
      ? new Date(createdAt as string).getUTCHours()
      : 0

    // Parse plan_tools_selected
    let tools: string[] = []
    const raw = row['plan_tools_selected']
    if (typeof raw === 'string') {
      try {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) tools = parsed.filter((t): t is string => typeof t === 'string')
      } catch {
        // ignore malformed JSON
      }
    } else if (Array.isArray(raw)) {
      tools = raw.filter((t): t is string => typeof t === 'string')
    }

    for (const tool of tools) {
      if (!result[tool]) {
        result[tool] = new Array<number>(24).fill(0)
      }
      result[tool][hour]++
    }
  }

  return result
}

// ── Coverage stats ────────────────────────────────────────────────────────────

export interface CoverageStats {
  totalAssets: number
  assetsWithTool: number
  toolsWithManifest: number
  plannerVisibleTools: number
}

/**
 * Derives four coverage KPIs from the manifest (compressed form) and the
 * RETRIEVAL_TOOLS list.
 *
 * `manifestCompressed` is the object produced by the manifest_compressor;
 * expected shape: `{ assets?: Array<{ bound_tools?: string[], expose_to_chat?: boolean }> }`.
 * Any missing fields default to 0 to keep the function safe in stub mode.
 */
export function getCoverageStats(
  manifestCompressed: Record<string, unknown> | null | undefined,
  retrievalTools: string[],
): CoverageStats {
  const assets = Array.isArray(manifestCompressed?.['assets'])
    ? (manifestCompressed!['assets'] as Array<Record<string, unknown>>)
    : []

  const totalAssets = assets.length
  const assetsWithTool = assets.filter(a => {
    const bt = a['bound_tools']
    return Array.isArray(bt) && bt.length > 0
  }).length

  // "tools with manifest" = retrieval tools that appear as a bound_tool on ≥1 asset
  const toolsInManifest = new Set<string>()
  for (const a of assets) {
    const bt = a['bound_tools']
    if (Array.isArray(bt)) {
      for (const t of bt) {
        if (typeof t === 'string') toolsInManifest.add(t)
      }
    }
  }
  const toolsWithManifest = retrievalTools.filter(t => toolsInManifest.has(t)).length

  // "planner-visible" = assets where expose_to_chat === true
  const plannerVisibleTools = assets.filter(a => a['expose_to_chat'] === true).length

  return { totalAssets, assetsWithTool, toolsWithManifest, plannerVisibleTools }
}
