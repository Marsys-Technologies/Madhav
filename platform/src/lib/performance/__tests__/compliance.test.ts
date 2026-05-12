import { describe, it, expect } from 'vitest'

import {
  detectB10Violation,
  detectB11Violation,
  parseCitations,
  type CitationLite,
} from '../compliance'

// ─────────────────────────────────────────────────────────────────────────────
// B.10 — chart-value fabrication
// ─────────────────────────────────────────────────────────────────────────────

describe('detectB10Violation', () => {
  it('returns false when [EXTERNAL_COMPUTATION_REQUIRED] marker is present with numerics', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Jupiter sits at 12°34′ in Sagittarius [EXTERNAL_COMPUTATION_REQUIRED]',
        citationObjects: [],
      })
    ).toBe(false)
  })

  it('returns true when numerics are present, no marker, and no L1 citation', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Jupiter at 12°34′ indicates a strong placement.',
        citationObjects: [],
      })
    ).toBe(true)
  })

  it('returns false when numerics are present but an L1 citation grounds the value', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Jupiter at 12°34′ per (→ FORENSIC: Jupiter natal longitude).',
        citationObjects: [{ source_layer: 'L1', citation_id: 'cite_0_FORENSIC' }],
      })
    ).toBe(false)
  })

  it('returns false on prose-only output (no numerics)', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Jupiter is a benefic that supports career growth.',
        citationObjects: [],
      })
    ).toBe(false)
  })

  it('does NOT flag bare year tokens like 1984 as chart values', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Born in 1984, the native experienced a Saturn return in 2014.',
        citationObjects: [],
      })
    ).toBe(false)
  })

  it('flags the degree-minute pattern 12°34′ as a chart value', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Saturn 12°34′ casts a 3rd aspect.',
        citationObjects: [],
      })
    ).toBe(true)
  })

  it('flags "25 degrees" as a chart value', () => {
    expect(
      detectB10Violation({
        synthesisText: 'Mars sits at 25 degrees in Aries.',
        citationObjects: [],
      })
    ).toBe(true)
  })

  it('does NOT trigger when L2.5 citation (not L1) is the only citation and numerics are bare', () => {
    // L2.5 citation does not ground a chart-value claim; only L1 does.
    const citations: CitationLite[] = [{ source_layer: 'L2_5', citation_id: 'cite_0_MSR' }]
    expect(
      detectB10Violation({
        synthesisText: 'Sun at 15°22′ activates pattern P-001.',
        citationObjects: citations,
      })
    ).toBe(true)
  })

  it('handles undefined inputs without crashing', () => {
    expect(
      detectB10Violation({
        synthesisText: undefined as unknown as string,
        citationObjects: undefined as unknown as CitationLite[],
      })
    ).toBe(false)
  })

  it('returns false for output with only short prose and no degree symbol', () => {
    expect(
      detectB10Violation({
        synthesisText: 'The chart shows strong career indications.',
        citationObjects: [],
      })
    ).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// B.11 — Holistic Synthesis routing
// ─────────────────────────────────────────────────────────────────────────────

describe('detectB11Violation', () => {
  it('returns false when an L2.5 tool fired (e.g. msr_sql)', () => {
    expect(
      detectB11Violation({ toolResults: [{ tool_name: 'msr_sql' }, { tool_name: 'vector_search' }] })
    ).toBe(false)
  })

  it('returns true when only L1-layer tools fired', () => {
    expect(
      detectB11Violation({ toolResults: [{ tool_name: 'vector_search' }, { tool_name: 'kp_query' }] })
    ).toBe(true)
  })

  it('returns true (fail-closed) when toolResults is empty', () => {
    expect(detectB11Violation({ toolResults: [] })).toBe(true)
  })

  it('returns true (fail-closed) when toolResults is undefined', () => {
    expect(detectB11Violation({ toolResults: undefined })).toBe(true)
  })

  it('returns false when cgm_graph_walk fired', () => {
    expect(detectB11Violation({ toolResults: [{ tool_name: 'cgm_graph_walk' }] })).toBe(false)
  })

  it('returns false when pattern_register fired alongside others', () => {
    expect(
      detectB11Violation({
        toolResults: [{ tool_name: 'pattern_register' }, { tool_name: 'kp_query' }],
      })
    ).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// parseCitations
// ─────────────────────────────────────────────────────────────────────────────

describe('parseCitations', () => {
  it('returns empty array on no citations', () => {
    expect(parseCitations('Plain prose without markers.')).toEqual([])
  })

  it('parses an L1 citation', () => {
    const out = parseCitations('Sun at 10° (→ FORENSIC: Sun natal longitude).')
    expect(out).toHaveLength(1)
    expect(out[0].source_layer).toBe('L1')
  })

  it('parses an L2.5 citation', () => {
    const out = parseCitations('Pattern fires (→ MSR/signal/P-001).')
    expect(out).toHaveLength(1)
    expect(out[0].source_layer).toBe('L2_5')
  })

  it('parses multiple mixed citations', () => {
    const out = parseCitations('A (→ FORENSIC: x) and B (→ MSR/y) and C (→ 03_DOMAIN_REPORTS/z).')
    expect(out).toHaveLength(3)
    expect(out.map((c) => c.source_layer)).toEqual(['L1', 'L2_5', 'L3'])
  })
})
