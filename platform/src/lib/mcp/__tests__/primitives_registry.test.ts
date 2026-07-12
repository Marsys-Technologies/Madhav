import { describe, it, expect } from 'vitest'
// D7 Step 4: primitives_registry retired — imports moved to tool_name_bridge
import { isAllowedSurgicalTool, MCP_TO_RETRIEVAL_TOOL, SURGICAL_TOOLS } from '@/lib/retrieval/registry/tool_name_bridge'

describe('primitives_registry', () => {
  // FIX-1 regression: original MCP-facing tool names pass whitelist
  describe('original MCP tool names pass whitelist', () => {
    const originalMcpTools = [
      'query_chart_facts',
      'query_signals',
      'query_dasha_periods',
      'query_panchanga',
      'query_ephemeris',
      'query_transit_event',
      'lel_query',
      'vector_search',
      'get_cgm_subgraph',
      // WP-1.7 (LCA-1/13): cross_school_lookup removed — see rejected block below
      'read_classical_text',
      // TR Wave additions
      'query_varshphal',
      'query_divisional_chart',
      'query_remedial_mantras',
      'muhurta_finder',
    ]
    it.each(originalMcpTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(true)
    })
  })

  // WP-1.7 (LCA-1/13): only the UDA/portal tools that resolve to a REAL registered
  // capability are retained on the whitelist (msr_sql, temporal, contradiction_register).
  describe('retained UDA tools pass whitelist AND resolve to a real capability', () => {
    const retainedUdaTools = [
      'msr_sql',
      'temporal',
      'contradiction_register',
    ]
    it.each(retainedUdaTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(true)
    })
  })

  // WP-1.7 (LCA-1/13): the 12 vestigial UDA/legacy names had NO backing capability
  // (getToolByName undefined → local 500). They were REMOVED from the whitelist so the
  // primitives route now returns a clean 400 {class:"validation"} instead of a 500.
  describe('removed dead tools are now REJECTED (WP-1.7 — no backing capability)', () => {
    const removedDeadTools = [
      'cross_school_lookup',
      'kp_query',
      'query_kp_ruling_planets',
      'pattern_register',
      'resonance_register',
      'cluster_atlas',
      'query_ucn_walk',
      'query_cdlm_lookup',
      'query_rm_walk',
      'query_jaimini_drishti',
      'timeline_query',
      'query_signal_state',
      'jaimini_chara_dasha',
      'jaimini_chara_dasha_full',
    ]
    it.each(removedDeadTools)('isAllowedSurgicalTool("%s") === false', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(false)
    })
  })

  // WP-1.7 (LCA-1/13): tara/chandra bala now resolve (get_tara_chandra_bala) and stay whitelisted.
  describe('tara/chandra bala admitted through whitelist (now resolve)', () => {
    const balaTools = [
      'query_tara_balam',
      'query_chandra_balam',
    ]
    it.each(balaTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(true)
    })
  })

  describe('rejects unknown tools (FIX-1: prototype-pollution guard)', () => {
    const invalidTools = ['nonexistent', 'fake_tool', '', 'QUERY_SIGNALS', 'msr-sql', '__proto__', 'constructor', 'toString']
    it.each(invalidTools)('isAllowedSurgicalTool("%s") === false', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(false)
    })
  })

  it('all MCP_TO_RETRIEVAL_TOOL values are non-empty strings (SurgicalToolName)', () => {
    for (const [k, v] of Object.entries(MCP_TO_RETRIEVAL_TOOL)) {
      expect(typeof v, `key ${k} value should be string`).toBe('string')
      expect(v.length, `key ${k} value should be non-empty`).toBeGreaterThan(0)
    }
  })

  it('SURGICAL_TOOLS array contains only non-empty strings', () => {
    for (const tool of SURGICAL_TOOLS) {
      expect(typeof tool).toBe('string')
      expect(tool.length).toBeGreaterThan(0)
    }
  })

  it('MCP_TO_RETRIEVAL_TOOL has at least 25 entries (original 11 + TR Wave + UDA 14)', () => {
    expect(Object.keys(MCP_TO_RETRIEVAL_TOOL).length).toBeGreaterThanOrEqual(25)
  })

  it('every MCP_TO_RETRIEVAL_TOOL value is contained in SURGICAL_TOOLS', () => {
    const surgicalSet = new Set(SURGICAL_TOOLS)
    for (const [k, v] of Object.entries(MCP_TO_RETRIEVAL_TOOL)) {
      expect(surgicalSet.has(v as (typeof SURGICAL_TOOLS)[number]), `value "${v}" for key "${k}" not in SURGICAL_TOOLS`).toBe(true)
    }
  })

  it('FIX-1 prototype-pollution guard: uses Object.hasOwn not "in" operator', () => {
    // __proto__ is a prototype property on plain objects; "in" would return true, Object.hasOwn returns false
    expect(isAllowedSurgicalTool('__proto__')).toBe(false)
    expect(isAllowedSurgicalTool('constructor')).toBe(false)
    expect(isAllowedSurgicalTool('hasOwnProperty')).toBe(false)
  })
})
