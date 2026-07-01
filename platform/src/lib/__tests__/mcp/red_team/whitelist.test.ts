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
// D7 Step 4: primitives_registry retired — imports moved to tool_name_bridge
import {
  isAllowedSurgicalTool,
  MCP_TO_RETRIEVAL_TOOL,
  SURGICAL_TOOLS,
} from '@/lib/retrieval/registry/tool_name_bridge'

// ── RT-04: Whitelist enforcement ─────────────────────────────────────────────

describe('RT-04 — Primitive whitelist enforcement', () => {
  it('RT-04a: whitelisted tool pattern_register is accepted (UDA Campaign addition)', () => {
    // pattern_register was added as a UDA surgical primitive
    expect(isAllowedSurgicalTool('pattern_register')).toBe(true)
  })

  it('RT-04b: whitelisted tool resonance_register is accepted (UDA Campaign addition)', () => {
    expect(isAllowedSurgicalTool('resonance_register')).toBe(true)
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
    // timeline_query and contradiction_register are now whitelisted UDA Campaign additions
    expect(isAllowedSurgicalTool('timeline_query')).toBe(true)
    expect(isAllowedSurgicalTool('contradiction_register')).toBe(true)
    // These remain unwhitelisted
    expect(isAllowedSurgicalTool('nonexistent_tool')).toBe(false)
    expect(isAllowedSurgicalTool('ask_madhav')).toBe(false)
  })

  it('RT-04g: all original + TR Wave + UDA whitelisted names are accepted', () => {
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
      // UDA Campaign additions (14 portal-native tools)
      'msr_sql',
      'temporal',
      'kp_query',
      'query_kp_ruling_planets',
      'pattern_register',
      'resonance_register',
      'cluster_atlas',
      'contradiction_register',
      'query_ucn_walk',
      'query_cdlm_lookup',
      'query_rm_walk',
      'query_jaimini_drishti',
      'timeline_query',
      'query_signal_state',
    ]
    for (const name of expected) {
      expect(isAllowedSurgicalTool(name)).toBe(true)
    }
  })

  it('RT-04h: whitelist maps 46 entries (11 original + 4 MCP TR + 4 retrieval aliases + 4 stubs + 14 UDA + 2 entity + 7 remedy)', () => {
    expect(Object.keys(MCP_TO_RETRIEVAL_TOOL)).toHaveLength(46)
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
