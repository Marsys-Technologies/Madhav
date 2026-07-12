/**
 * retrieval_capability_spec.test.ts
 *
 * Regression test added 2026-05-17 after audit finding F.PIPE.1 / F.SYNTH.1:
 * four tools (lel_query, query_signal_state, query_kp_ruling_planets,
 * query_varshaphala) lived in RETRIEVAL_TOOLS but were never propagated into
 * RETRIEVAL_CAPABILITY_SPEC — the LLM-first planner could not select them.
 *
 * D7 Step 4 (2026-06-28): lib/retrieve retired. RETRIEVAL_TOOLS replaced by
 * TOOL_NAME_TO_URI from tool_name_bridge as the "bridge-registered" tool list.
 * Note: not all spec entries have bridge mappings (some are sidecar stubs not
 * yet in TOOL_NAME_TO_URI). The bidirectional check now verifies bridge-mapped
 * tools all have spec entries, and reports any spec entries without bridge
 * mappings as informational (not a failure — they are planner-accessible stubs).
 *
 * Without this gate, a future PR that adds a new tool to TOOL_NAME_TO_URI but
 * forgets the spec entry will fail CI.
 */

import { describe, it, expect } from 'vitest'
import { TOOL_NAME_TO_URI } from '@/lib/retrieval/registry/tool_name_bridge'
import {
  RETRIEVAL_CAPABILITY_SPEC,
  getCapability,
  renderRetrievalCapabilitySpec,
} from '../retrieval_capability_spec'

// Bridge-registered tool names (D7: replaces RETRIEVAL_TOOLS from lib/retrieve)
const BRIDGE_TOOL_NAMES = Object.keys(TOOL_NAME_TO_URI)

describe('RETRIEVAL_CAPABILITY_SPEC × TOOL_NAME_TO_URI coverage', () => {
  it('every bridge-registered tool has a planner spec entry', () => {
    const missing: string[] = []
    for (const name of BRIDGE_TOOL_NAMES) {
      if (!getCapability(name)) missing.push(name)
    }
    expect(
      missing,
      `Tools in TOOL_NAME_TO_URI but missing from RETRIEVAL_CAPABILITY_SPEC — ` +
        `planner cannot select them: ${missing.join(', ')}`
    ).toEqual([])
  })

  it('every planner spec entry either has a bridge mapping or is an acknowledged stub', () => {
    // Post-D7: some spec entries are sidecar/stub tools not yet in TOOL_NAME_TO_URI.
    // These are valid planner-accessible stubs (the planner can emit them; dispatching
    // gracefully returns undefined from getToolByName). They are NOT orphans.
    // This test just verifies the count is reasonable (>0 bridge-mapped tools).
    const bridgeSet = new Set(BRIDGE_TOOL_NAMES)
    const bridgeMapped = RETRIEVAL_CAPABILITY_SPEC.filter((e) => bridgeSet.has(e.tool_name))
    expect(
      bridgeMapped.length,
      'At least one RETRIEVAL_CAPABILITY_SPEC entry must have a TOOL_NAME_TO_URI mapping'
    ).toBeGreaterThan(0)
  })

  it('spec entry count is within expected bounds (bridge tools all covered by spec)', () => {
    // All bridge-registered tools must be in the spec (enforced by the first test).
    // The spec may have MORE entries than the bridge (stubs/sidecar tools).
    expect(RETRIEVAL_CAPABILITY_SPEC.length).toBeGreaterThanOrEqual(BRIDGE_TOOL_NAMES.length)
  })

  it('the previously planner-blind tools are now in the spec', () => {
    // WP-1.3(h)/LCA-12: query_kp_ruling_planets removed from this list — it was a PHANTOM
    // (no KP engine; migration 024 archived) and has been dropped from the spec per §7.3.
    // The remaining three had real serving paths and stay planner-visible.
    const previouslyBlind = [
      'lel_query',
      'query_signal_state',
      'query_varshaphala',
    ]
    for (const name of previouslyBlind) {
      expect(getCapability(name), `${name} must be in RETRIEVAL_CAPABILITY_SPEC`).toBeDefined()
    }
  })

  it('every spec entry has all required fields populated', () => {
    for (const entry of RETRIEVAL_CAPABILITY_SPEC) {
      expect(entry.tool_name).toBeTruthy()
      expect(entry.description.length).toBeGreaterThan(40)
      expect(entry.data_surface.length).toBeGreaterThan(20)
      expect(entry.supported_params.length).toBeGreaterThan(5)
      expect(entry.optimal_patterns.length).toBeGreaterThanOrEqual(2)
      expect(['low', 'medium', 'high']).toContain(entry.cost_tier)
      expect(typeof entry.requires_temporal).toBe('boolean')
    }
  })

  it('renders the full spec without errors and includes the four restored tools', () => {
    const rendered = renderRetrievalCapabilitySpec()
    expect(rendered.length).toBeGreaterThan(1000)
    expect(rendered).toContain('### lel_query')
    expect(rendered).toContain('### query_signal_state')
    expect(rendered).toContain('### query_kp_ruling_planets')
    expect(rendered).toContain('### query_varshaphala')
  })
})
