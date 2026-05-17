/**
 * retrieval_capability_spec.test.ts
 *
 * Regression test added 2026-05-17 after audit finding F.PIPE.1 / F.SYNTH.1:
 * four tools (lel_query, query_signal_state, query_kp_ruling_planets,
 * query_varshaphala) lived in RETRIEVAL_TOOLS but were never propagated into
 * RETRIEVAL_CAPABILITY_SPEC — the LLM-first planner could not select them.
 *
 * This test guarantees every runtime-registered tool has a matching planner
 * catalog entry, and every catalog entry refers to a real registered tool.
 * Without this gate, a future PR that adds a new tool to RETRIEVAL_TOOLS but
 * forgets the spec entry will fail CI.
 */

import { describe, it, expect } from 'vitest'
import { RETRIEVAL_TOOLS } from '@/lib/retrieve'
import {
  RETRIEVAL_CAPABILITY_SPEC,
  getCapability,
  renderRetrievalCapabilitySpec,
} from '../retrieval_capability_spec'

describe('RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage', () => {
  it('every runtime tool has a planner spec entry', () => {
    const missing: string[] = []
    for (const tool of RETRIEVAL_TOOLS) {
      if (!getCapability(tool.name)) missing.push(tool.name)
    }
    expect(
      missing,
      `Tools in RETRIEVAL_TOOLS but missing from RETRIEVAL_CAPABILITY_SPEC — ` +
        `planner cannot select them: ${missing.join(', ')}`
    ).toEqual([])
  })

  it('every planner spec entry refers to a real registered tool', () => {
    const registered = new Set(RETRIEVAL_TOOLS.map((t) => t.name))
    const orphans = RETRIEVAL_CAPABILITY_SPEC.filter((e) => !registered.has(e.tool_name)).map(
      (e) => e.tool_name
    )
    expect(
      orphans,
      `Spec entries with no corresponding RETRIEVAL_TOOLS registration — ` +
        `planner will hallucinate calls to nonexistent tools: ${orphans.join(', ')}`
    ).toEqual([])
  })

  it('spec entry count matches runtime tool count exactly', () => {
    expect(RETRIEVAL_CAPABILITY_SPEC.length).toBe(RETRIEVAL_TOOLS.length)
  })

  it('the four previously planner-blind tools are now in the spec', () => {
    const previouslyBlind = [
      'lel_query',
      'query_signal_state',
      'query_kp_ruling_planets',
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
