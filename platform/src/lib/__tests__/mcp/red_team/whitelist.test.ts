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
  resolveToolUri,
} from '@/lib/retrieval/registry/tool_name_bridge'

// ── RT-04: Whitelist enforcement ─────────────────────────────────────────────

describe('RT-04 — Primitive whitelist enforcement', () => {
  it('RT-04a: pattern_register is now REJECTED (WP-1.7 removed — no backing capability)', () => {
    // pattern_register was a speculative UDA whitelist entry with no registry capability;
    // isAllowedSurgicalTool admitted it but getToolByName then 500'd. WP-1.7 removed it,
    // so it is now cleanly rejected (400 validation) at the whitelist gate.
    expect(isAllowedSurgicalTool('pattern_register')).toBe(false)
  })

  it('RT-04b: resonance_register is now REJECTED (WP-1.7 removed — no backing capability)', () => {
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
    // WP-1.7: timeline_query REMOVED (no backing cap → now rejected); contradiction_register
    // RETAINED because it resolves to L2/query_contradictions.
    expect(isAllowedSurgicalTool('timeline_query')).toBe(false)
    expect(isAllowedSurgicalTool('contradiction_register')).toBe(true)
    // These remain unwhitelisted
    expect(isAllowedSurgicalTool('nonexistent_tool')).toBe(false)
    expect(isAllowedSurgicalTool('ask_madhav')).toBe(false)
  })

  it('RT-04g: all retained whitelisted names (post WP-1.7) are accepted AND resolve', () => {
    // WP-1.7: only names whose retrieval target resolves via getToolByName are whitelisted.
    const expected = [
      // Original (cross_school_lookup dropped — see removed-tools test)
      'query_chart_facts',
      'query_signals',
      'query_dasha_periods',
      'query_panchanga',
      'query_ephemeris',
      'query_transit_event',
      'lel_query',
      'vector_search',
      'get_cgm_subgraph',
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
      // Tara/Chandra bala (now resolve → get_tara_chandra_bala)
      'query_tara_balam',
      'query_chandra_balam',
      // UDA Campaign — retained portal-native tools that resolve
      'msr_sql',
      'temporal',
      'contradiction_register',
    ]
    for (const name of expected) {
      expect(isAllowedSurgicalTool(name)).toBe(true)
    }
  })

  it('RT-04g2: the 14 WP-1.7-removed dead names are all rejected', () => {
    const removed = [
      'cross_school_lookup', 'kp_query', 'query_kp_ruling_planets',
      'pattern_register', 'resonance_register', 'cluster_atlas',
      'query_ucn_walk', 'query_cdlm_lookup', 'query_rm_walk',
      'query_jaimini_drishti', 'timeline_query', 'query_signal_state',
      'jaimini_chara_dasha', 'jaimini_chara_dasha_full',
    ]
    for (const name of removed) {
      expect(isAllowedSurgicalTool(name)).toBe(false)
    }
  })

  it('RT-04h: whitelist maps 53 entries (34 post-WP-1.7 + 13 WP-1.3a + 5 WP-1.3j + 1 D-4b B-5)', () => {
    expect(Object.keys(MCP_TO_RETRIEVAL_TOOL)).toHaveLength(53)
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

  it('cross_school_lookup removed (WP-1.7 — multi_school_signal_lookup never bridged to registry)', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['cross_school_lookup']).toBeUndefined()
  })

  it('WP-1.7: cgm_graph_walk / temporal / contradiction_register / tara / chandra all resolve', () => {
    for (const retrievalName of ['cgm_graph_walk', 'temporal', 'contradiction_register', 'query_tara_balam', 'query_chandra_balam']) {
      expect(resolveToolUri(retrievalName), `${retrievalName} should have a URI`).toBeDefined()
    }
  })

  it('lel_query → lel_query (direct mapping)', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['lel_query']).toBe('lel_query')
  })
})
