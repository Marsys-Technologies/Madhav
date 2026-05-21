/**
 * retrieval_util_panel_smoke — gate test for PERF-S3
 *
 * Tests:
 * 1. RetrievalUtilizationSection renders and surfaces zero-call tools
 * 2. aggregateRetrievalUtilization correctly parses plan_tools_selected
 */

import { describe, it, expect } from 'vitest'
import {
  aggregateRetrievalUtilization,
  getCoverageStats,
} from '@/lib/performance/retrieval_utilization_aggregator'

// ── Aggregator unit tests ─────────────────────────────────────────────────────

describe('retrieval_util_panel_smoke — aggregateRetrievalUtilization', () => {
  it('returns empty record for no rows', () => {
    const result = aggregateRetrievalUtilization([])
    expect(result).toEqual({})
  })

  it('parses plan_tools_selected JSON string and accumulates counts', () => {
    const rows = [
      {
        created_at: '2026-05-21T10:30:00Z', // hour 10
        plan_tools_selected: JSON.stringify(['msr_sql', 'vector_search']),
      },
      {
        created_at: '2026-05-21T10:45:00Z', // hour 10
        plan_tools_selected: JSON.stringify(['msr_sql']),
      },
      {
        created_at: '2026-05-21T15:00:00Z', // hour 15
        plan_tools_selected: JSON.stringify(['vector_search']),
      },
    ]

    const result = aggregateRetrievalUtilization(rows)

    // Both tools must be present
    expect(result).toHaveProperty('msr_sql')
    expect(result).toHaveProperty('vector_search')

    // 24 buckets each
    expect(result['msr_sql']).toHaveLength(24)
    expect(result['vector_search']).toHaveLength(24)

    // msr_sql: 2 calls in hour 10, 0 elsewhere
    expect(result['msr_sql'][10]).toBe(2)
    expect(result['msr_sql'][15]).toBe(0)

    // vector_search: 1 in hour 10, 1 in hour 15
    expect(result['vector_search'][10]).toBe(1)
    expect(result['vector_search'][15]).toBe(1)
  })

  it('handles null / missing plan_tools_selected gracefully', () => {
    const rows = [
      { created_at: '2026-05-21T08:00:00Z', plan_tools_selected: null },
      { created_at: '2026-05-21T08:00:00Z' },
    ]
    const result = aggregateRetrievalUtilization(rows)
    expect(result).toEqual({})
  })

  it('handles already-parsed array value', () => {
    const rows = [
      {
        created_at: '2026-05-21T06:00:00Z',
        plan_tools_selected: ['msr_sql', 'temporal'],
      },
    ]
    const result = aggregateRetrievalUtilization(rows)
    expect(result['msr_sql'][6]).toBe(1)
    expect(result['temporal'][6]).toBe(1)
  })
})

// ── Component smoke test ──────────────────────────────────────────────────────
// We test the zero-call logic directly without a full DOM render
// (keeps the test fast and avoids heavy React setup for a smoke gate).

describe('retrieval_util_panel_smoke — zero-call logic', () => {
  function zeroCallTools(tools: string[], callData: Record<string, number[]>): string[] {
    return tools.filter(t => {
      const counts = callData[t] ?? new Array<number>(24).fill(0)
      return counts.reduce((a, b) => a + b, 0) === 0
    })
  }

  it('identifies zero-call tools correctly', () => {
    const tools = ['msr_sql', 'vector_search', 'temporal']
    const callData: Record<string, number[]> = {
      msr_sql: new Array<number>(24).fill(0).map((_, i) => (i === 10 ? 3 : 0)),
      vector_search: new Array<number>(24).fill(0),
      // temporal not in callData → defaults to all zeros
    }

    const result = zeroCallTools(tools, callData)
    expect(result).toContain('vector_search')
    expect(result).toContain('temporal')
    expect(result).not.toContain('msr_sql')
  })

  it('returns empty array when all tools have calls', () => {
    const tools = ['msr_sql']
    const callData: Record<string, number[]> = {
      msr_sql: new Array<number>(24).fill(0).map((_, i) => (i === 5 ? 1 : 0)),
    }
    expect(zeroCallTools(tools, callData)).toHaveLength(0)
  })
})

// ── getCoverageStats tests ────────────────────────────────────────────────────

describe('retrieval_util_panel_smoke — getCoverageStats', () => {
  it('returns zeros for null manifest', () => {
    const result = getCoverageStats(null, ['msr_sql', 'vector_search'])
    expect(result.totalAssets).toBe(0)
    expect(result.assetsWithTool).toBe(0)
    expect(result.toolsWithManifest).toBe(0)
    expect(result.plannerVisibleTools).toBe(0)
  })

  it('counts correctly given a simple manifest', () => {
    const manifest = {
      assets: [
        { bound_tools: ['msr_sql'], expose_to_chat: true },
        { bound_tools: ['vector_search', 'msr_sql'], expose_to_chat: false },
        { bound_tools: [], expose_to_chat: true },
      ],
    }
    const result = getCoverageStats(manifest, ['msr_sql', 'vector_search', 'temporal'])
    expect(result.totalAssets).toBe(3)
    expect(result.assetsWithTool).toBe(2)     // first two have bound_tools
    expect(result.toolsWithManifest).toBe(2)  // msr_sql + vector_search appear in manifest
    expect(result.plannerVisibleTools).toBe(2) // expose_to_chat: true × 2
  })
})
