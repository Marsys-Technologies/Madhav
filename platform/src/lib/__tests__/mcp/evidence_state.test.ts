/**
 * evidence_state.test.ts — F-126 zero-result detector.
 *
 * The defect: `mimamsa_lel_query` (→ platform primitive `lel_query`) served
 * `epistemics.confidence_band: 'high'` on a query that matched ZERO life events.
 * The band was hardcoded in the primitives route, so no result could ever have
 * produced a different value — a grade with no detector behind it (§N.8).
 *
 * These tests pin the detector itself. The route-level regression (the exact
 * live-reproduced envelope) lives in primitives.test.ts.
 */

import { describe, it, expect } from 'vitest'
import { detectEvidenceState, surgicalConfidenceBand } from '@/lib/mcp/evidence_state'

/**
 * The EXACT payload production returned for the F-126 reproducer
 * (chart 482012f1…, query "marriage relationship spouse partner wedding"),
 * wrapped in the ToolBundle shape tool_name_bridge.ts builds.
 */
const F126_EMPTY_LEL_BUNDLE = {
  tool_bundle_id: '76b91eb2-46c3-4f4d-a878-51e090e8b629',
  tool_name: 'lel_query',
  tool_version: '1.0',
  invocation_params: {
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    query: 'marriage relationship spouse partner wedding',
  },
  results: [
    {
      content: JSON.stringify({
        chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
        events: [],
        count: 0,
        total_matching: 0,
        has_more: false,
        filters: {
          category: null, domain: null, significance: null,
          start_date: null, end_date: null,
          query: 'marriage relationship spouse partner wedding',
          limit: 50, offset: 0,
        },
        provenance: {
          tables: ['life_events'],
          no_leakage_note:
            'life_events is a calibration corpus only — must not feed prediction generation.',
          source: 'LIFE_EVENT_LOG (user-authored); served chart-scoped.',
        },
      }),
    },
  ],
  served_from_cache: false,
  latency_ms: 36,
  result_hash: 'sha256:718b835d81d16e99fbdce27d3e4c062e12fa2a0c0b2746bb1282acdce057a73c',
  schema_version: '1.0',
}

describe('detectEvidenceState — F-126 reproducer', () => {
  it('grades the exact live zero-result LEL bundle as empty', () => {
    expect(detectEvidenceState(F126_EMPTY_LEL_BUNDLE)).toBe('empty')
  })

  it('grades the same bundle as present once one event matches', () => {
    const populated = {
      ...F126_EMPTY_LEL_BUNDLE,
      results: [
        {
          content: JSON.stringify({
            chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
            events: [{ event_id: 'e1', event_date: '2011-02-13', description: 'marriage' }],
            count: 1,
            total_matching: 1,
            has_more: false,
          }),
        },
      ],
    }
    expect(detectEvidenceState(populated)).toBe('present')
  })

  it('grades the live PAGED production payload (count 2 of 11) as present', () => {
    // Captured live alongside the reproducer: mimamsa_lel_query {query:"career", limit:2}
    // on the canonical chart. Guards the other direction — a real, populated,
    // mid-pagination result must never be graded empty by this fix.
    const paged = {
      tool_bundle_id: 'ba35ff3e-bd46-4e5c-9f86-cb0f1bb12836',
      tool_name: 'lel_query',
      results: [
        {
          content: JSON.stringify({
            chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
            events: [
              { event_id: 'fd04fecc-21f7-5dfd-b68b-f1a6f1cd6bfa', event_date: '2007-06-10', category: 'career' },
              { event_id: 'aed78f94-87ca-5347-a1d0-7f277a99b6c4', event_date: '2008-06-09', category: 'career' },
            ],
            count: 2,
            total_matching: 11,
            has_more: true,
          }),
        },
      ],
      schema_version: '1.0',
    }
    expect(detectEvidenceState(paged)).toBe('present')
  })
})

describe('detectEvidenceState — bare payloads', () => {
  it('zero count + zero total_matching → empty', () => {
    expect(detectEvidenceState({ events: [], count: 0, total_matching: 0 })).toBe('empty')
  })

  it('non-zero total_matching → present', () => {
    expect(detectEvidenceState({ events: [], count: 0, total_matching: 12 })).toBe('present')
  })

  it('a populated collection outranks a zero counter (never grades served rows empty)', () => {
    // Defensive: a stale/secondary counter must not be able to call served rows empty.
    expect(detectEvidenceState({ rows: [{ a: 1 }], count: 0 })).toBe('present')
  })

  it('empty array payload → empty', () => {
    expect(detectEvidenceState([])).toBe('empty')
  })

  it('non-empty array payload → present', () => {
    expect(detectEvidenceState([{ a: 1 }])).toBe('present')
  })

  it('payload with no readable count → indeterminate (never a guessed downgrade)', () => {
    expect(detectEvidenceState({ signals: [] })).toBe('indeterminate')
    expect(detectEvidenceState({ nodes: [], edges: [] })).toBe('indeterminate')
    expect(detectEvidenceState({ verdict: { grade: 'strong' }, warnings: [] })).toBe('indeterminate')
  })

  it('a ToolBundle with zero result entries → empty', () => {
    expect(detectEvidenceState({ tool_bundle_id: 'x', tool_name: 't', results: [] })).toBe('empty')
  })

  it('unparseable content string → indeterminate, empty string → empty', () => {
    expect(
      detectEvidenceState({ tool_bundle_id: 'x', tool_name: 't', results: [{ content: 'not json' }] }),
    ).toBe('indeterminate')
    expect(
      detectEvidenceState({ tool_bundle_id: 'x', tool_name: 't', results: [{ content: '' }] }),
    ).toBe('empty')
  })

  it('a plain object with a results array but no bundle marker is graded as a payload', () => {
    // `{results: []}` from e.g. vector_search is a payload, not a ToolBundle —
    // no count key, so it is honestly indeterminate rather than assumed empty.
    expect(detectEvidenceState({ results: [] })).toBe('indeterminate')
  })
})

describe('surgicalConfidenceBand', () => {
  it("empty → 'none' (no finding for a band to grade)", () => {
    expect(surgicalConfidenceBand('empty')).toBe('none')
  })

  it("present → 'high' (pre-existing surgical-lookup behaviour, unchanged)", () => {
    expect(surgicalConfidenceBand('present')).toBe('high')
  })

  it("indeterminate → 'high' (no measurement ⇒ no invented downgrade)", () => {
    expect(surgicalConfidenceBand('indeterminate')).toBe('high')
  })
})
