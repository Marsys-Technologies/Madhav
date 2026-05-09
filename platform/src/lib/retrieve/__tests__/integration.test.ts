import { describe, it, expect, vi } from 'vitest'

// Mock storage and telemetry so imports of the tool modules don't fail
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))

import { RETRIEVAL_TOOLS, getTool } from '../index'

describe('RETRIEVAL_TOOLS registry integration', () => {
  it('has exactly 21 tools', () => {
    // 10 original + kp_query + saham_query + divisional_query (W4-R2) + chart_facts_query (W4-R3)
    // + domain_report_query + remedial_codex_query + timeline_query (W5-R2 M2-D234-BUNDLE)
    // + query_signal_state + query_kp_ruling_planets + query_varshaphala (D-series)
    // + cross_varga_dignity_query (VARGA-ETL-FULL-S1-CPA D8, 2026-05-10)
    expect(RETRIEVAL_TOOLS).toHaveLength(21)
  })

  it('getTool("msr_sql") returns the MSR SQL tool', () => {
    const t = getTool('msr_sql')
    expect(t).toBeDefined()
    expect(t?.name).toBe('msr_sql')
  })

  it('getTool("pattern_register") returns the pattern register tool', () => {
    const t = getTool('pattern_register')
    expect(t).toBeDefined()
    expect(t?.name).toBe('pattern_register')
  })

  it('getTool("resonance_register") returns the resonance register tool', () => {
    const t = getTool('resonance_register')
    expect(t).toBeDefined()
    expect(t?.name).toBe('resonance_register')
  })

  it('getTool("cluster_atlas") returns the cluster atlas tool', () => {
    const t = getTool('cluster_atlas')
    expect(t).toBeDefined()
    expect(t?.name).toBe('cluster_atlas')
  })

  it('getTool("contradiction_register") returns the contradiction register tool', () => {
    const t = getTool('contradiction_register')
    expect(t).toBeDefined()
    expect(t?.name).toBe('contradiction_register')
  })

  it('getTool("temporal") returns the temporal tool', () => {
    const t = getTool('temporal')
    expect(t).toBeDefined()
    expect(t?.name).toBe('temporal')
  })

  it('getTool("query_msr_aggregate") returns the aggregate tool', () => {
    const t = getTool('query_msr_aggregate')
    expect(t).toBeDefined()
    expect(t?.name).toBe('query_msr_aggregate')
  })

  it('getTool("cgm_graph_walk") returns the CGM graph walk tool', () => {
    const t = getTool('cgm_graph_walk')
    expect(t).toBeDefined()
    expect(t?.name).toBe('cgm_graph_walk')
  })

  it('getTool("manifest_query") returns the manifest query tool', () => {
    const t = getTool('manifest_query')
    expect(t).toBeDefined()
    expect(t?.name).toBe('manifest_query')
  })

  it('getTool("vector_search") returns the vector search tool', () => {
    const t = getTool('vector_search')
    expect(t).toBeDefined()
    expect(t?.name).toBe('vector_search')
  })

  it('vector_search tool is marked secondary', () => {
    const t = getTool('vector_search')
    expect(t?.secondary).toBe(true)
  })

  it('getTool("nonexistent") returns undefined', () => {
    expect(getTool('nonexistent')).toBeUndefined()
  })

  it('all tools have a name, version, and retrieve function', () => {
    for (const t of RETRIEVAL_TOOLS) {
      expect(typeof t.name).toBe('string')
      expect(t.name.length).toBeGreaterThan(0)
      expect(typeof t.version).toBe('string')
      expect(typeof t.retrieve).toBe('function')
    }
  })

  it('all tool names in registry are unique', () => {
    const names = RETRIEVAL_TOOLS.map(t => t.name)
    const unique = new Set(names)
    expect(unique.size).toBe(names.length)
  })
})
