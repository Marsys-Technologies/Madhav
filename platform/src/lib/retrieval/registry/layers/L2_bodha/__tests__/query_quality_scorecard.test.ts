/**
 * query_quality_scorecard — unit tests
 * ======================================
 * SAMĀPANA Track C item 2 (GA.1 class): the stored `synthesis_quality_scorecard` row's
 * `unresolved_constituent_facts_count` is a writer-time snapshot that goes stale the moment
 * an L1 rebuild runs after the Bodha writer last scored it. The handler already re-derives a
 * correct, live count via `deriveDefect001Note` and served it separately as `defect_001` — but
 * used to ALSO serve the stale raw DB value verbatim inside `scorecard`, so a caller reading
 * `scorecard.unresolved_constituent_facts_count` could see a different number than
 * `defect_001.metrics.orphan_refs` for the exact same chart in the exact same response. This
 * suite locks in the fix: the served `scorecard.unresolved_constituent_facts_count` must always
 * equal the live-derived `defect_001.metrics.orphan_refs`, never the raw stored value.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryQualityScorecardCapability } from '../query_quality_scorecard'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_quality_scorecard — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryQualityScorecardCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('never disagrees: served scorecard.unresolved_constituent_facts_count always equals ' +
    'the live-derived defect_001.metrics.orphan_refs, overwriting a stale stored value', async () => {
    vi.mocked(mockQuery)
      // 1st call: the scorecard row itself, with a STALE stored count (99999) that must NOT
      // survive into the response.
      .mockResolvedValueOnce({
        rows: [{
          scorecard_id: 'sc-1',
          chart_id: CHART_A,
          build_id: 'build-1',
          msr_signal_count: 500,
          cdlm_cell_count: 10,
          cgm_node_count: 20,
          cgm_edge_count: 30,
          two_pass_verified_pct: 81,
          documented_approximation_pct: 5,
          msr_citation_ref_coverage_pct: 100,
          trap1_authority_inversion_count: 0,
          trap2_narration_leak_count: 0,
          unresolved_constituent_facts_count: 99999,
          scored_at: '2026-01-01T00:00:00.000Z',
        }],
      } as never)
      // 2nd call: deriveDefect001Note's own live re-derivation query (total_refs/orphan_refs).
      .mockResolvedValueOnce({
        rows: [{ total_refs: '1000', orphan_refs: '3' }],
      } as never)

    const result = await queryQualityScorecardCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)

    const content = result.content as Record<string, unknown>
    const scorecard = content['scorecard'] as Record<string, unknown>
    const defect001 = content['defect_001'] as { metrics: Record<string, unknown> }

    // The live-derived orphan count, not the stale 99999 the DB row carried.
    expect(defect001.metrics['orphan_refs']).toBe(3)
    expect(scorecard['unresolved_constituent_facts_count']).toBe(3)
    // The two numbers must always agree — that is the whole point of the fix.
    expect(scorecard['unresolved_constituent_facts_count']).toBe(defect001.metrics['orphan_refs'])
  })

  it('no scorecard row (no_data:true) does not throw when overwriting the field', async () => {
    vi.mocked(mockQuery)
      .mockResolvedValueOnce({ rows: [] } as never) // no scorecard row
      .mockResolvedValueOnce({ rows: [{ total_refs: '0', orphan_refs: '0' }] } as never) // NO_DATA path

    const result = await queryQualityScorecardCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['scorecard']).toBeNull()
    expect(content['no_data']).toBe(true)
  })
})
