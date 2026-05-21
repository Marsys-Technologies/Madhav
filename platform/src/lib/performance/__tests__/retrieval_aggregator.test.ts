import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getRetrievalStats, ALL_TOOL_NAMES } from '../retrieval_aggregator'

beforeEach(() => mockQuery.mockReset())

function dbRows(rows: Array<{ plan_tools_selected: string | null; created_at: string }>) {
  return Promise.resolve({ rows })
}

describe('getRetrievalStats', () => {
  it('empty DB → all 33 tools with call_count 0, orphaned_tools has all 33, pct_coverage = 0', async () => {
    mockQuery.mockReturnValue(dbRows([]))

    const stats = await getRetrievalStats(168)

    expect(stats.tools).toHaveLength(ALL_TOOL_NAMES.length)
    expect(ALL_TOOL_NAMES.length).toBe(33)

    for (const t of stats.tools) {
      expect(t.call_count).toBe(0)
      expect(t.is_orphaned).toBe(true)
      expect(t.last_called_at).toBeNull()
    }

    expect(stats.orphaned_tools).toHaveLength(33)
    expect(stats.coverage_scoreboard.tools_called_at_least_once).toBe(0)
    expect(stats.coverage_scoreboard.pct_coverage).toBe(0)
    expect(stats.coverage_scoreboard.total_tools).toBe(33)
    expect(stats.total_queries).toBe(0)
    expect(stats.top_combinations).toHaveLength(0)
  })

  it('2 queries with msr_sql + lel_query → both get call_count 2, others 0', async () => {
    const ts = '2026-05-20T10:00:00Z'
    mockQuery.mockReturnValue(dbRows([
      { plan_tools_selected: JSON.stringify(['msr_sql', 'lel_query']), created_at: ts },
      { plan_tools_selected: JSON.stringify(['msr_sql', 'lel_query']), created_at: ts },
    ]))

    const stats = await getRetrievalStats(168)

    const msrTool = stats.tools.find(t => t.tool_name === 'msr_sql')
    const lelTool = stats.tools.find(t => t.tool_name === 'lel_query')
    const otherTool = stats.tools.find(t => t.tool_name === 'temporal')

    expect(msrTool?.call_count).toBe(2)
    expect(msrTool?.is_orphaned).toBe(false)
    expect(msrTool?.last_called_at).toBe(ts)

    expect(lelTool?.call_count).toBe(2)
    expect(lelTool?.is_orphaned).toBe(false)

    expect(otherTool?.call_count).toBe(0)
    expect(otherTool?.is_orphaned).toBe(true)

    expect(stats.orphaned_tools).not.toContain('msr_sql')
    expect(stats.orphaned_tools).not.toContain('lel_query')
    expect(stats.coverage_scoreboard.tools_called_at_least_once).toBe(2)
    expect(stats.total_queries).toBe(2)
  })

  it('top_combinations computed correctly from 3 queries with different tool sets', async () => {
    mockQuery.mockReturnValue(dbRows([
      // combo A appears twice
      { plan_tools_selected: JSON.stringify(['msr_sql', 'temporal']), created_at: '2026-05-20T10:00:00Z' },
      { plan_tools_selected: JSON.stringify(['msr_sql', 'temporal']), created_at: '2026-05-20T09:00:00Z' },
      // combo B appears once
      { plan_tools_selected: JSON.stringify(['lel_query']), created_at: '2026-05-20T08:00:00Z' },
    ]))

    const stats = await getRetrievalStats(168)

    expect(stats.top_combinations.length).toBeGreaterThanOrEqual(2)
    // combo A should be first (higher count)
    const comboA = stats.top_combinations[0]
    expect(comboA.count).toBe(2)
    expect(comboA.tools).toEqual(['msr_sql', 'temporal'])

    const comboB = stats.top_combinations[1]
    expect(comboB.count).toBe(1)
    expect(comboB.tools).toEqual(['lel_query'])
  })

  it('is_orphaned is false for called tools and true for zero-call tools', async () => {
    mockQuery.mockReturnValue(dbRows([
      { plan_tools_selected: JSON.stringify(['cgm_graph_walk']), created_at: '2026-05-20T10:00:00Z' },
    ]))

    const stats = await getRetrievalStats(168)

    const calledTool = stats.tools.find(t => t.tool_name === 'cgm_graph_walk')
    const uncalledTool = stats.tools.find(t => t.tool_name === 'query_muhurat')

    expect(calledTool?.is_orphaned).toBe(false)
    expect(uncalledTool?.is_orphaned).toBe(true)
  })

  it('tools are sorted by call_count desc then name asc', async () => {
    mockQuery.mockReturnValue(dbRows([
      { plan_tools_selected: JSON.stringify(['msr_sql', 'temporal', 'lel_query']), created_at: '2026-05-20T10:00:00Z' },
      { plan_tools_selected: JSON.stringify(['msr_sql', 'temporal']), created_at: '2026-05-20T09:00:00Z' },
    ]))

    const stats = await getRetrievalStats(168)

    // msr_sql and temporal both have 2 calls; they should come first (sorted by name among equals)
    const top = stats.tools.slice(0, 3)
    const topCounts = top.map(t => t.call_count)
    expect(topCounts[0]).toBeGreaterThanOrEqual(topCounts[1])
    expect(topCounts[1]).toBeGreaterThanOrEqual(topCounts[2])

    // Verify alphabetical tie-breaking: among tools with count 2, msr_sql < temporal alphabetically
    const twoCallTools = stats.tools.filter(t => t.call_count === 2)
    expect(twoCallTools.map(t => t.tool_name)).toEqual(
      [...twoCallTools.map(t => t.tool_name)].sort()
    )
  })

  it('handles null or malformed plan_tools_selected gracefully', async () => {
    mockQuery.mockReturnValue(dbRows([
      { plan_tools_selected: null, created_at: '2026-05-20T10:00:00Z' },
      { plan_tools_selected: 'not-valid-json{{{', created_at: '2026-05-20T09:00:00Z' },
      { plan_tools_selected: JSON.stringify(['msr_sql']), created_at: '2026-05-20T08:00:00Z' },
    ]))

    const stats = await getRetrievalStats(168)

    // Only msr_sql should be counted; nulls and bad JSON skipped
    const msrTool = stats.tools.find(t => t.tool_name === 'msr_sql')
    expect(msrTool?.call_count).toBe(1)
    expect(stats.total_queries).toBe(3)
  })
})
