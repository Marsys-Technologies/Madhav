/**
 * f131_priority_ranking_glossary.test.ts — F-131 serving-seam regression suite.
 *
 * PROVES, at the `callPriorityRankingCapability.handler` boundary:
 *   1. an internal computation-abstention row ("floored: no_canonical_per_varga_method") is
 *      NOT served as a ranked priority signal;
 *   2. it is disclosed as excluded — with the matched pattern and the rank it would have
 *      occupied — rather than silently dropped (B.10);
 *   3. real signals come back with an acharya-grade `signal_headline_label` beside the
 *      unchanged raw `signal_headline_text`;
 *   4. an unmapped category is passed through verbatim and counted, never relabelled by guess;
 *   5. the SQL itself asks the DB for the marker classification and a total ORDER BY.
 *
 * FIXTURE PROVENANCE: every `signal_headline_text` below was read live from
 * bodha_msr_signals for chart 482012f1-710e-4a25-994a-93821f5871aa on 2026-08-21 — including
 * the abstention row, which really did rank #5 in the original 6-month-window reproducer.
 * The DB is mocked (this suite runs without a live Postgres); the STRINGS are real.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

// Imported after the mock is registered.
const { callPriorityRankingCapability } = await import('../call_service_wrappers')

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

/** Rows shaped exactly as the handler's CTE returns them (post-window-function). */
const LIVE_ROWS = [
  {
    signal_id: 'df5c4452-6e42-4bae-a6a2-15f3616a3703',
    signal_headline_text: 'SAT: arudha pada: sign = Aquarius [ga_sensitive]',
    computed_salience: 1.890945,
    domains_affected_array: ['career', 'wealth'],
    signal_type_class: 'karaka_alignment',
    activation_strength: 1,
    window_start: '2024-12-08',
    window_end: '2027-08-18',
    trigger_type: 'DISPOSITOR_RELATIONAL',
    neutral_dignity_downranked: false,
    abstention_marker_pattern: null,
    catalog_only_marker_pattern: null,
    priority_score: 1.890945,
    pre_exclusion_rank: '1',
    partition_rank: '1',
  },
  {
    signal_id: 'e1e8fcd1-837e-4e45-8526-4fb958517549',
    signal_headline_text: 'kp planet significations: star lord = Mercury [ga_sensitive]',
    computed_salience: 1.2075,
    domains_affected_array: ['character'],
    signal_type_class: 'tradition_specific',
    activation_strength: 1,
    window_start: '2010-08-18',
    window_end: '2027-08-18',
    trigger_type: 'DIGNITY',
    neutral_dignity_downranked: false,
    abstention_marker_pattern: null,
    catalog_only_marker_pattern: null,
    priority_score: 1.2075,
    pre_exclusion_rank: '2',
    partition_rank: '2',
  },
  {
    // THE F-131 ROW. Ranked #3 here (it ranked #5 in the live 20-row reproducer).
    signal_id: '05312dc7-4166-47fc-86c4-2c43cc7c5975',
    signal_headline_text:
      'graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method [ga_structural]',
    computed_salience: 1.296648,
    domains_affected_array: ['character', 'family'],
    signal_type_class: 'composite_state',
    activation_strength: 1,
    window_start: '2024-12-08',
    window_end: '2027-08-18',
    trigger_type: 'SUBSYSTEM',
    neutral_dignity_downranked: false,
    abstention_marker_pattern: 'floored: no_canonical_per_varga_method',
    catalog_only_marker_pattern: null,
    priority_score: 1.296648,
    pre_exclusion_rank: '3',
    partition_rank: '1',
  },
]

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: LIVE_ROWS })
})
afterEach(() => vi.clearAllMocks())

async function run(args: Record<string, unknown> = {}) {
  const res = await callPriorityRankingCapability.handler(
    { chart_id: CHART, date_from: '2026-08-21', date_to: '2027-02-21', top_k: 20, ...args },
    undefined,
  )
  expect(res.is_error).toBe(false)
  return res.content as Record<string, unknown>
}

describe('F-131 — abstention marker is not served as a priority signal', () => {
  it('excludes the floored: no_canonical_per_varga_method row from ranked_signals', async () => {
    const c = await run()
    const ranked = c.ranked_signals as Array<Record<string, unknown>>

    expect(ranked).toHaveLength(2)
    expect(ranked.map(r => r.signal_id)).not.toContain('05312dc7-4166-47fc-86c4-2c43cc7c5975')
    // The abstention string must be categorically absent from the served signal set.
    expect(JSON.stringify(ranked)).not.toContain('no_canonical_per_varga_method')
    expect(JSON.stringify(ranked)).not.toContain('floored:')
    // ...and it must not leak into the grounding refs either.
    expect(c.signal_id_refs).not.toContain('05312dc7-4166-47fc-86c4-2c43cc7c5975')
    expect(c.signal_count).toBe(2)
  })

  it('discloses the exclusion rather than dropping it silently (B.10)', async () => {
    const c = await run()
    expect(c.excluded_internal_marker_count).toBe(1)

    const excluded = c.excluded_internal_markers as Array<Record<string, unknown>>
    expect(excluded).toHaveLength(1)
    expect(excluded[0]).toMatchObject({
      signal_id: '05312dc7-4166-47fc-86c4-2c43cc7c5975',
      signal_headline_text:
        'graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method [ga_structural]',
      matched_pattern: 'floored: no_canonical_per_varga_method',
      exclusion_reason: 'internal_computation_abstention_marker',
      pre_exclusion_rank: 3,   // the rank it WOULD have occupied — what makes this meaningful
    })
    expect(String(c.excluded_internal_marker_note)).toContain('EXCLUDED')
    expect(String(c.excluded_internal_marker_note)).toContain('§B.10')
  })

  it('excludes the SECOND live abstention family, caught only by the bare "floored:" pattern', async () => {
    // Live-DB finding (2026-08-21, canonical chart): F-131's write-up named ONE abstention
    // reason, `no_canonical_per_varga_method`. There are in fact TWO families among the 66
    // floored rows on this chart — the other is
    //   'graha drik bala per varga: D5 = floored: drik_requires_varga_aspect_geometry'
    // whose reason string appears NOWHERE in INTERNAL_MARKER_PATTERNS. It is caught solely by
    // the generic bare "floored:" entry. That makes the bare pattern load-bearing rather than
    // redundant belt-and-braces: tightening the list to only the named F-131 strings would
    // silently re-open the defect for ~30 rows. This test exists to fail if anyone does that.
    const drikRow = {
      ...LIVE_ROWS[2],
      signal_id: 'drik-abstention-row',
      signal_headline_text:
        'graha drik bala per varga: D5 = floored: drik_requires_varga_aspect_geometry [ga_structural]',
      abstention_marker_pattern: 'floored:',
    }
    queryMock.mockResolvedValue({ rows: [LIVE_ROWS[0], drikRow] })
    const c = await run()

    expect(c.signal_count).toBe(1)
    expect(JSON.stringify(c.ranked_signals)).not.toContain('drik_requires_varga_aspect_geometry')
    expect(c.excluded_internal_marker_count).toBe(1)
    expect((c.excluded_internal_markers as Array<Record<string, unknown>>)[0].matched_pattern)
      .toBe('floored:')

    // And the bare pattern really is still in the set the DB is asked to match on.
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    const bound = params.find(p => Array.isArray(p) && (p as string[]).includes('floored:'))
    expect(bound).toBeDefined()
  })

  it('reports zero-exclusions explicitly, so "none" differs from "never checked" (§N.8)', async () => {
    queryMock.mockResolvedValue({ rows: LIVE_ROWS.filter(r => !r.abstention_marker_pattern) })
    const c = await run()
    expect(c.excluded_internal_marker_count).toBe(0)
    expect(c.excluded_internal_markers).toEqual([])
    expect(c).not.toHaveProperty('excluded_internal_marker_note')
  })

  it('asks the DB for the classification — the exclusion is not a client-side afterthought', async () => {
    await run()
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toContain('abstention_marker_pattern')
    expect(sql).toContain('catalog_only_marker_pattern')
    expect(sql).toContain('WITH ORDINALITY')
    // The abstention patterns really are bound as a parameter (not inlined/forgotten).
    const bound = params.find(p => Array.isArray(p) && (p as string[]).includes('floored:'))
    expect(bound).toBeDefined()
    // §N.7 item 2: a selection that reduces to a ranked page carries a TOTAL order.
    expect(sql).toMatch(/ORDER BY priority_score DESC NULLS LAST, signal_id\s*$/)
  })

  it('serves top_k REAL signals — exclusion does not silently shrink the page', async () => {
    await run({ top_k: 20 })
    const [sql] = queryMock.mock.calls[0] as [string]
    // Servable rows are limited by their own partition rank, not by a post-LIMIT filter.
    expect(sql).toContain('PARTITION BY (s.abstention_marker_pattern IS NULL)')
    expect(sql).toMatch(/abstention_marker_pattern IS NULL\s+AND partition_rank\s+<= \$\d+/)
  })
})

describe('F-131 — raw template strings are labelled, unmapped ones passed through', () => {
  it('adds an acharya-grade label beside the unchanged raw headline', async () => {
    const c = await run()
    const row = (c.ranked_signals as Array<Record<string, unknown>>)[0]

    expect(row.signal_headline_label).toBe('SAT: Arudha Pāda: sign = Aquarius [ga_sensitive]')
    expect(row.headline_label_mapped).toBe(true)
    expect(row.headline_fact_category).toBe('arudha_pada')
    // The raw L1-referencing template is still there — labelled, not replaced (§N.5 / B.10).
    expect(row.signal_headline_text).toBe('SAT: arudha pada: sign = Aquarius [ga_sensitive]')
  })

  it('passes an unmapped category through verbatim, flags it, and counts it', async () => {
    const c = await run()
    const row = (c.ranked_signals as Array<Record<string, unknown>>)[1]

    expect(row.headline_label_mapped).toBe(false)
    expect(row.headline_fact_category).toBeNull()
    expect(row.signal_headline_label).toBe(row.signal_headline_text)
    expect(c.unmapped_headline_count).toBe(1)
    expect(String(c.unmapped_headline_note)).toContain('No label was invented')
  })

  it('strips the internal window-function helper columns from served rows', async () => {
    const c = await run()
    for (const row of c.ranked_signals as Array<Record<string, unknown>>) {
      expect(row).not.toHaveProperty('partition_rank')
      expect(row).not.toHaveProperty('pre_exclusion_rank')
      expect(row).not.toHaveProperty('abstention_marker_pattern')
    }
  })

  it('serves a catalog-only row (flagged) instead of excluding it (§N.6)', async () => {
    queryMock.mockResolvedValue({
      rows: [{
        ...LIVE_ROWS[0],
        signal_id: 'catalog-only-row',
        signal_headline_text: 'yoga label: fire reason = requires_pass [ga_structural]',
        abstention_marker_pattern: null,
        catalog_only_marker_pattern: 'requires_pass',
      }],
    })
    const c = await run()
    const ranked = c.ranked_signals as Array<Record<string, unknown>>

    expect(ranked).toHaveLength(1)                    // served, not dropped
    expect(ranked[0].catalog_only_unverified).toBe(true)
    expect(c.catalog_only_rows_in_page).toBe(1)
    expect(c.excluded_internal_marker_count).toBe(0)
    expect(String(c.catalog_only_note)).toContain('ganita_yoga_firings_get')
  })

  it('still rejects a missing chart_id', async () => {
    const res = await callPriorityRankingCapability.handler({}, undefined)
    expect(res.is_error).toBe(true)
  })
})
