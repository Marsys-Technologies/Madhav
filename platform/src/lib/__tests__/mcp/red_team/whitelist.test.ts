/**
 * whitelist.test.ts — Red-team: RT-04
 *
 * RT-04: Primitive whitelist enforcement — non-whitelisted tool name returns
 * {ok: false, error: {class: "validation"}} with HTTP 400.
 *
 * Also verifies RT-06 (prototype pollution) via isAllowedSurgicalTool("__proto__").
 *
 * MCP-4-S2 red-team session.
 */

import { describe, it, expect } from 'vitest'
import {
  isAllowedSurgicalTool,
  MCP_TO_RETRIEVAL_TOOL,
  SURGICAL_TOOLS,
} from '@/lib/mcp/primitives_registry'

// ── RT-04: Whitelist enforcement ─────────────────────────────────────────────

describe('RT-04 — Primitive whitelist enforcement', () => {
  it('RT-04a: non-whitelisted tool pattern_register is rejected', () => {
    // pattern_register is in-process only (not a surgical primitive)
    expect(isAllowedSurgicalTool('pattern_register')).toBe(false)
  })

  it('RT-04b: non-whitelisted tool resonance_register is rejected', () => {
    expect(isAllowedSurgicalTool('resonance_register')).toBe(false)
  })

  it('RT-04c: non-whitelisted tool ask_madhav is rejected (end-to-end tool, not surgical)', () => {
    expect(isAllowedSurgicalTool('ask_madhav')).toBe(false)
  })

  it('RT-04d: non-whitelisted tool execute_plan is rejected', () => {
    expect(isAllowedSurgicalTool('execute_plan')).toBe(false)
  })

  it('RT-04e: empty string is rejected', () => {
    expect(isAllowedSurgicalTool('')).toBe(false)
  })

  it('RT-04f: arbitrary string is rejected', () => {
    expect(isAllowedSurgicalTool('drop_table_msr_signals')).toBe(false)
    expect(isAllowedSurgicalTool('timeline_query')).toBe(false)
    expect(isAllowedSurgicalTool('contradiction_register')).toBe(false)
  })

  it('RT-04g: all original + TR Wave whitelisted names are accepted', () => {
    const expected = [
      // Original 11
      'query_chart_facts',
      'query_signals',
      'query_dasha_periods',
      'query_panchanga',
      'query_ephemeris',
      'query_transit_event',
      'lel_query',
      'vector_search',
      'get_cgm_subgraph',
      'cross_school_lookup',
      'read_classical_text',
      // TR Wave MCP-facing names
      'query_varshphal',
      'query_divisional_chart',
      'query_remedial_mantras',
      'muhurta_finder',
      // TR Wave retrieval-name aliases
      'query_varshaphala',
      'divisional_query',
      'remedial_codex_query',
      'query_muhurat',
    ]
    for (const name of expected) {
      expect(isAllowedSurgicalTool(name)).toBe(true)
    }
  })

  it('RT-04h: whitelist maps 23 entries (11 original + 4 MCP TR + 4 retrieval aliases + 4 stubs)', () => {
    expect(Object.keys(MCP_TO_RETRIEVAL_TOOL)).toHaveLength(23)
  })

  it('RT-04i: all retrieval tool targets are in SURGICAL_TOOLS', () => {
    for (const [, retrievalName] of Object.entries(MCP_TO_RETRIEVAL_TOOL)) {
      expect(SURGICAL_TOOLS).toContain(retrievalName)
    }
  })
})

// ── Prototype pollution guard (RT-06 supporting evidence) ────────────────────

describe('RT-06 — Prototype pollution guard: isAllowedSurgicalTool uses Object.hasOwn', () => {
  it('RT-06a: __proto__ is rejected (not in whitelist)', () => {
    // If the function used `in` instead of Object.hasOwn(), "__proto__" would
    // return true because all plain objects have __proto__ on their prototype chain.
    expect(isAllowedSurgicalTool('__proto__')).toBe(false)
  })

  it('RT-06b: constructor is rejected', () => {
    expect(isAllowedSurgicalTool('constructor')).toBe(false)
  })

  it('RT-06c: toString is rejected', () => {
    expect(isAllowedSurgicalTool('toString')).toBe(false)
  })

  it('RT-06d: valueOf is rejected', () => {
    expect(isAllowedSurgicalTool('valueOf')).toBe(false)
  })

  it('RT-06e: hasOwnProperty is rejected', () => {
    // 'hasOwnProperty' is on Object.prototype — `in` check would yield true
    expect(isAllowedSurgicalTool('hasOwnProperty')).toBe(false)
  })
})

// ── Mapping correctness ───────────────────────────────────────────────────────

describe('Mapping correctness — MCP-facing names map to correct retrieval tool names', () => {
  it('query_chart_facts → chart_facts_query', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['query_chart_facts']).toBe('chart_facts_query')
  })

  it('query_signals → msr_sql', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['query_signals']).toBe('msr_sql')
  })

  it('get_cgm_subgraph → cgm_graph_walk', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['get_cgm_subgraph']).toBe('cgm_graph_walk')
  })

  it('cross_school_lookup → multi_school_signal_lookup', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['cross_school_lookup']).toBe('multi_school_signal_lookup')
  })

  it('lel_query → lel_query (direct mapping)', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['lel_query']).toBe('lel_query')
  })
})
