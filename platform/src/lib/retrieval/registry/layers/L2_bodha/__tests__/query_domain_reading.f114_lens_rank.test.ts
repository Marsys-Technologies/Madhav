/**
 * query_domain_reading.f114_lens_rank.test.ts — PARIŚEṢA F-114 (CL-10) regression.
 * ================================================================================
 * F-114, as filed: `assess_marriage`'s 'marriage' lens reported signal_count 3698 and served
 * as its top-10 ranked signals ten `ga_sensitive` SATURN rows at IDENTICAL salience 2.16108
 * ('SAT: graha nakshatra join', 'SAT: bhrigu nadi point', 'SAT: esoteric point shiva',
 * 'SAT: upagraha position', 'SAT: midpoint', 'SAT: saham position', 'SAT: aprakasha position',
 * …). Not one named the 7th lord, Venus, or a marriage yoga.
 *
 * Root cause (verified live against the canonical chart's production rows): the stored
 * `bodha_question_lenses.all_relevant_ranked_jsonb.ranked_signals` array is ordered at BUILD
 * time by raw `computed_salience` alone (bo_drishti.py), which is
 *   (a) domain-AGNOSTIC — every row in the family already matches the domain tag, so salience
 *       does no within-domain discrimination whatsoever; and
 *   (b) not a total order — the relationship family's top of distribution is a 13-way EXACT
 *       tie at 2.16108 (and a 61-way tie at 0.82800).
 * Serving the head of that array as "the top N signals for this domain" is therefore unsound.
 * `domain_salience_jsonb` does not rescue it: it is exactly computed_salience / |domains|
 * (3698/3698 rows on the canonical chart), a uniform split with zero domain information.
 *
 * The fix wires the repo's EXISTING domain-aware composite ranker (composite_ranker.ts, already
 * used by the top-level ranked_signals surface in this very file, by query_signals, and by
 * assess_*) into the per-lens head. No new ranking algorithm was invented.
 *
 * No live DB: `query` is mocked and dispatched on SQL shape.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryDomainReadingCapability } from '../query_domain_reading'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LENS_ID  = '11111111-1111-4111-8111-111111111111'

/** The degenerate cluster, verbatim in shape: 13 ga_sensitive SATURN rows, salience 2.16108. */
const SAT_HEADLINES = [
  'SAT: sun derived upagraha: sign = Capricorn [ga_sensitive]',
  'SAT: upagraha position: sign = Aquarius [ga_sensitive]',
  'SAT: midpoint: sign = Capricorn [ga_sensitive]',
  'SAT: saham position: sign = Capricorn [ga_sensitive]',
  'SAT: upagraha position: sign = Capricorn [ga_sensitive]',
  'SAT: bhrigu nadi point: sign = Aquarius [ga_sensitive]',
  'SAT: graha pada join: pada number ref = 1 [ga_sensitive]',
  'SAT: graha nakshatra join: nakshatra id ref = 16 [ga_sensitive]',
  'SAT: midpoint: sign = Aquarius [ga_sensitive]',
  'SAT: saham position: sign = Aquarius [ga_sensitive]',
  'SAT: esoteric point shiva: sign = Aquarius [ga_sensitive]',
  'SAT: bhrigu nadi point: sign = Capricorn [ga_sensitive]',
  'SAT: aprakasha position: sign = Capricorn [ga_sensitive]',
]
const TIED_SALIENCE = 2.16108

const satId = (i: number) => `22222222-2222-4222-8222-${String(i).padStart(12, '0')}`
/** The row a marriage lens is supposed to surface: Venus (kalatra-kāraka) in the 7th. */
const VENUS_7TH_ID = '33333333-3333-4333-8333-333333333333'
const VENUS_7TH_HEADLINE = 'VEN: kalatra karaka in bhava 7 [ga_structural]'

/** The stored family, in the exact order bo_drishti persists it (salience DESC). */
function storedRankedSignals() {
  const sat = SAT_HEADLINES.map((_, i) => ({
    signal_id: satId(i),
    salience: TIED_SALIENCE,
    signal_type_class: 'composite_state',
    source_l1_asset: 'ga_sensitive',
    in_template: true,
    non_template_significant: false,
  }))
  // Buried BELOW the whole tie-block by raw salience — i.e. invisible to a head-slice of 10.
  const venus = {
    signal_id: VENUS_7TH_ID,
    salience: 0.9,
    signal_type_class: 'composite_state',
    source_l1_asset: 'ga_structural',
    in_template: true,
    non_template_significant: false,
  }
  return [...sat, venus]
}

/** Ranker-input rows for the same family (what computeLensRerank fetches from the DB). */
function rerankRows() {
  const sat = SAT_HEADLINES.map((h, i) => ({
    signal_id: satId(i),
    signal_type_id: 'sensitive_point_position',
    signal_type_class: 'composite_state',
    signal_tradition: 'parashari',
    signal_summary_text: h,
    signal_headline_text: h,
    computed_salience: TIED_SALIENCE,
    domains_affected_array: ['character', 'relationship', 'spirituality'],
    source_subsystem: 'sensitive',
    // No house resolves → bhāva×domain congruence is neutral (1.0); graha SAT×relationship = 0.90.
    configuration_jsonb: { graha: 'SAT', fact_key: 'sign', fact_value_text: 'Capricorn' },
    graph_node_strength_contribution_jsonb: null,
  }))
  const venus = {
    signal_id: VENUS_7TH_ID,
    signal_type_id: 'karaka_bhava_placement',
    signal_type_class: 'composite_state',
    signal_tradition: 'parashari',
    signal_summary_text: VENUS_7TH_HEADLINE,
    signal_headline_text: VENUS_7TH_HEADLINE,
    computed_salience: 0.9,
    domains_affected_array: ['relationship'],
    source_subsystem: 'structural',
    // graha VEN×relationship = 1.50, bhāva 7×relationship = 2.20 (kalatra-bhāva).
    configuration_jsonb: { graha: 'VEN', house: 7 },
    graph_node_strength_contribution_jsonb: null,
  }
  return [...sat, venus]
}

function installMock(opts: {
  rerankRows?: unknown[]
  storedFamily?: unknown[]
  anchorIds?: string[]
} = {}) {
  const rr = opts.rerankRows ?? rerankRows()
  const family = opts.storedFamily ?? storedRankedSignals()
  mockQuery.mockImplementation(async (sql: string) => {
    if (/FROM bodha_question_lenses/.test(sql)) {
      if (/COUNT\(\*\)/.test(sql)) return { rows: [{ n: 2 }] }
      return {
        rows: [{
          lens_id: LENS_ID,
          question_type: 'marriage',
          template_element_ids_jsonb: { signal_count: 3698 },
          all_relevant_ranked_jsonb: { ranked_signals: family, total_count: 3698 },
          lens_template_version: 'classical_v1.0',
          points_only_assertion: true,
          verification_pass_status: 'documented_approximation',
          computed_at: '2026-08-20T00:00:00Z',
        }],
      }
    }
    // The domain-ANCHOR slice — the only query projecting `signal_id::text AS signal_id`.
    if (/signal_id::text AS signal_id/.test(sql)) {
      return { rows: (opts.anchorIds ?? []).map(id => ({ signal_id: id })) }
    }
    // computeLensRerank's ranker-input fetch — the only one selecting the CGM centrality
    // column by uuid[].
    if (/FROM bodha_msr_signals/.test(sql)
        && /graph_node_strength_contribution_jsonb/.test(sql)
        && /uuid\[\]/.test(sql)) {
      return { rows: rr }
    }
    // Everything else (cdlm cells, the discriminated pool, hydration, chart_facts, dashas)
    // degrades to its empty path — this test is scoped to the per-lens rank basis.
    return { rows: [] }
  })
}

function servedHead(content: Record<string, unknown>) {
  const lenses = content['question_lenses'] as Array<Record<string, unknown>>
  const lens = lenses[0]!
  const arj = lens['all_relevant_ranked_jsonb'] as Record<string, unknown>
  return { lens, rows: arj['ranked_signals'] as Array<Record<string, unknown>> }
}

describe('F-114 — marriage lens ranked_signals must not be a degenerate identical-salience block', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('reproduces the defect shape: the STORED order really is 13 identical-salience SAT rows first', () => {
    const stored = storedRankedSignals()
    const head = stored.slice(0, 10)
    expect(head).toHaveLength(10)
    expect(new Set(head.map(r => r.salience)).size).toBe(1)
    expect(head.every(r => r.source_l1_asset === 'ga_sensitive')).toBe(true)
    // The row a marriage lens actually owes the caller is nowhere in that head.
    expect(head.some(r => r.signal_id === VENUS_7TH_ID)).toBe(false)
  })

  it('serves a domain-ranked head, not the identical-salience block', async () => {
    installMock()
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 10 }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const { lens, rows } = servedHead(content)

    expect(rows).toHaveLength(10)

    // (1) THE regression assertion: the served top-10 is no longer one undifferentiated
    // salience block. Before the fix every row carried salience 2.16108.
    const salienceValues = new Set(rows.map(r => r['salience']))
    expect(salienceValues.size).toBeGreaterThan(1)

    // (2) …and it is no longer ten non-domain-specific ga_sensitive rows.
    const sourceAssets = new Set(rows.map(r => r['source_l1_asset']))
    expect(sourceAssets.size).toBeGreaterThan(1)

    // (3) The kalatra-kāraka-in-the-7th row — buried below the whole tie-block by raw
    // salience — is lifted to the top by the domain overlay (VEN×relationship 1.50 ×
    // bhāva 7×relationship 2.20 vs SAT×relationship 0.90 × neutral 1.00).
    expect(rows[0]!['signal_id']).toBe(VENUS_7TH_ID)

    // (4) Every served row carries a distinct rank score — the ranker's three-layer
    // tie-break guarantees no two positions share one (composite_ranker.ts). A tie among
    // served rows is the exact F-114 failure mode.
    const scores = rows.map(r => r['final_rank_score'] as number)
    expect(scores.every(s => typeof s === 'number' && Number.isFinite(s))).toBe(true)
    expect(new Set(scores).size).toBe(scores.length)
    // Monotonically non-increasing — the head really is sorted by that score.
    for (let i = 1; i < scores.length; i++) expect(scores[i]!).toBeLessThan(scores[i - 1]!)

    // (5) The response says, machine-readably, what basis the head was ranked on.
    expect(lens['ranked_signals_rank_basis']).toBe('composite_4d_domain_overlay')
    expect(lens['ranked_signals_total']).toBe(14)
    expect(content['ranked_signals_per_lens_rank_basis']).toBe('composite_4d_domain_overlay')
    expect(content['ranked_signals_per_lens_reranked_lenses']).toBe(1)
    expect(String(content['ranked_signals_per_lens_rank_note'])).toMatch(/composite overlay/)
  })

  it('never drops a family member: rows outside the re-rank window keep their stored order below it', async () => {
    installMock()
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 100 }, undefined,
    )
    const { rows } = servedHead(result.content as Record<string, unknown>)
    // All 14 family members are still served — the re-rank REORDERS, it does not filter (B.10).
    expect(rows).toHaveLength(14)
    const ids = new Set(rows.map(r => r['signal_id']))
    expect(ids.size).toBe(14)
    expect(ids.has(VENUS_7TH_ID)).toBe(true)
    for (let i = 0; i < SAT_HEADLINES.length; i++) expect(ids.has(satId(i))).toBe(true)
  })

  it('promotes a domain kāraka / kalatra-bhāva row that sits OUTSIDE the salience-head window', async () => {
    // Measured on the canonical chart: the marriage family's first Venus-bearing row is at
    // stored rank 902 and its first 7th-house row at 1041 — both far outside any affordable
    // salience-head window. Without the anchor slice the ranker would faithfully re-rank a
    // candidate set that never contained the domain's own significators, and F-114's actual
    // complaint would survive the fix. This models exactly that geometry.
    const WINDOW = 400
    const filler = Array.from({ length: WINDOW + 20 }, (_, i) => ({
      signal_id: satId(i),
      salience: TIED_SALIENCE,
      signal_type_class: 'composite_state',
      source_l1_asset: 'ga_sensitive',
      in_template: true,
      non_template_significant: false,
    }))
    const venusStored = {
      signal_id: VENUS_7TH_ID,
      salience: 0.41,
      signal_type_class: 'composite_state',
      source_l1_asset: 'ga_structural',
      in_template: true,
      non_template_significant: false,
    }
    // Buried at index 415 — beyond the 400-row salience-head window.
    const storedFamily = [...filler.slice(0, 415), venusStored, ...filler.slice(415)]
    expect(storedFamily.slice(0, WINDOW).some(r => r.signal_id === VENUS_7TH_ID)).toBe(false)

    const ranker = [
      ...filler.slice(0, WINDOW).map((r, i) => ({
        signal_id: r.signal_id,
        signal_type_id: 'sensitive_point_position',
        signal_type_class: 'composite_state',
        signal_tradition: 'parashari',
        signal_summary_text: SAT_HEADLINES[i % SAT_HEADLINES.length],
        signal_headline_text: SAT_HEADLINES[i % SAT_HEADLINES.length],
        computed_salience: TIED_SALIENCE,
        domains_affected_array: ['character', 'relationship', 'spirituality'],
        source_subsystem: 'sensitive',
        configuration_jsonb: { graha: 'SAT', fact_key: 'sign', fact_value_text: 'Capricorn' },
        graph_node_strength_contribution_jsonb: null,
      })),
      { ...rerankRows().at(-1)!, computed_salience: 0.41 },
    ]

    installMock({ storedFamily, rerankRows: ranker, anchorIds: [VENUS_7TH_ID] })
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 10 }, undefined,
    )
    const content = result.content as Record<string, unknown>
    const { lens, rows } = servedHead(content)

    // The anchor leg pulled the kalatra-kāraka-in-the-7th row into the candidate set, and the
    // domain overlay then ranked it first — despite the LOWEST raw salience in the family.
    expect(rows[0]!['signal_id']).toBe(VENUS_7TH_ID)
    expect(rows[0]!['salience']).toBe(0.41)
    expect(lens['ranked_signals_rank_basis']).toBe('composite_4d_domain_overlay')
    expect(String(content['ranked_signals_per_lens_rank_note'])).toMatch(/anchor slice/)
    // Nothing was dropped: the family is still the full stored size.
    expect(lens['ranked_signals_total']).toBe(storedFamily.length)
  })

  it('reports the basis HONESTLY as stored-salience when the re-rank could not run (§N.8)', async () => {
    // The ranker-input fetch comes back empty → no re-rank is possible. The response must say
    // so rather than claim a domain ranking it did not perform.
    installMock({ rerankRows: [] })
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 10 }, undefined,
    )
    const content = result.content as Record<string, unknown>
    const { lens, rows } = servedHead(content)
    expect(lens['ranked_signals_rank_basis']).toBe('stored_salience_build_time')
    expect(content['ranked_signals_per_lens_rank_basis']).toBe('stored_salience_build_time')
    expect(content['ranked_signals_per_lens_reranked_lenses']).toBe(0)
    expect(String(content['ranked_signals_per_lens_rank_note'])).toMatch(/NOT as "the top N/)
    // …and the stored order is served unchanged, not silently reshuffled.
    expect(rows[0]!['signal_id']).toBe(satId(0))
  })
})
