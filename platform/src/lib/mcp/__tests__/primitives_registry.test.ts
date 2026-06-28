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
      'cross_school_lookup',
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

  // FIX-1 regression: 14 UDA tools now pass whitelist
  describe('14 UDA tools now pass whitelist (FIX-1 regression)', () => {
    const udaMcpTools = [
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
    it.each(udaMcpTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(true)
    })
  })

  // TR Wave Class B/C stubs also pass (so they get 500 retrieval-not-found, not 400 whitelist-block)
  describe('TR Wave stub tools admitted through whitelist', () => {
    const stubTools = [
      'query_tara_balam',
      'query_chandra_balam',
      'jaimini_chara_dasha',
      'jaimini_chara_dasha_full',
    ]
    it.each(stubTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
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
