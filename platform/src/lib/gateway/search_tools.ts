/**
 * search_tools — discoverability over the unified contract.
 *
 * Returns a slim catalog of registered tools optionally filtered by family,
 * role, or a free-text query (case-insensitive match against canonical_name
 * + description). MASTER_PLAN §5 calls for a resident core of ~12 tools and
 * the rest discoverable through this surface.
 */

import { TOOL_CONTRACTS } from '@/lib/contract'
import type { ToolSearchQuery, ToolSearchResult } from './types'

const DEFAULT_LIMIT = 32

export function searchTools(q: ToolSearchQuery = {}): ToolSearchResult[] {
  const limit = q.limit ?? DEFAULT_LIMIT
  const needle = q.query ? q.query.trim().toLowerCase() : null

  let out: ToolSearchResult[] = []
  for (const c of TOOL_CONTRACTS) {
    if (q.family && c.family !== q.family) continue
    if (q.role && c.role !== q.role) continue
    if (needle) {
      const hay = `${c.canonical_name}\n${c.description}`.toLowerCase()
      if (!hay.includes(needle)) continue
    }
    out.push({
      canonical_name: c.canonical_name,
      description: c.description,
      family: c.family,
      role: c.role,
      per_chart: c.per_chart,
      ayanamsha_role: c.ayanamsha_role,
    })
    if (out.length >= limit) break
  }
  return out
}
