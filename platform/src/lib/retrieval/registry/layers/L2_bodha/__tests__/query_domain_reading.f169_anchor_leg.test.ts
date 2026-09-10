/**
 * query_domain_reading.f169_anchor_leg.test.ts — PARIŚEṢA F-169 regression.
 * ============================================================================
 * F-169, as filed: `lensRankBasisNote` (query_domain_reading.ts, served as
 * `ranked_signals_per_lens_rank_note`) asserted the anchor-slice UNION ran and that "the
 * domain's significators are guaranteed CONSIDERED" — but that assertion was only ever
 * gated on `rerankedLensCount > 0` (whether the MAIN rerank leg produced a composite basis
 * for at least one lens), entirely independent of whether the ANCHOR leg (a second, separate
 * DB round-trip) actually ran and found anything. A bare `catch {}` around the anchor query
 * meant three distinct failure modes could each silently void the guarantee while the note
 * kept claiming it held:
 *   1. the anchor query THROWS,
 *   2. the domain declares no anchor actors (graha_aliases/houses both empty) so the leg
 *      never runs at all, and
 *   3. the query succeeds but matches none of these lenses' families.
 *
 * The fix threads an observable `anchor_leg: 'applied' | 'no_anchors' | 'no_family_hits' |
 * 'failed'` receipt out of `computeLensRerank`, serves it as
 * `ranked_signals_per_lens_anchor_leg`, and branches the note's candidate-set clause on it —
 * so the "guaranteed CONSIDERED" sentence is served ONLY when the anchor leg actually applied.
 * The bare `catch {}` is replaced with a logged `console.warn` + the served 'failed' receipt,
 * mirroring the in-file precedent at the second (main-rerank) catch, which already reported
 * failure honestly via the rank-basis mechanism.
 *
 * No live DB: `query` is mocked and dispatched on SQL shape (same harness as
 * query_domain_reading.f114_lens_rank.test.ts).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryDomainReadingCapability } from '../query_domain_reading'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LENS_ID  = '11111111-1111-4111-8111-111111111111'

const VENUS_7TH_ID = '33333333-3333-4333-8333-333333333333'
const VENUS_7TH_HEADLINE = 'VEN: kalatra karaka in bhava 7 [ga_structural]'
const SAT_ID = (i: number) => `22222222-2222-4222-8222-${String(i).padStart(12, '0')}`
const TIED_SALIENCE = 2.16108

/** A small stored family: a few salience-tied rows plus one buried-below-window row. */
function storedRankedSignals() {
  const sat = Array.from({ length: 5 }, (_, i) => ({
    signal_id: SAT_ID(i),
    salience: TIED_SALIENCE,
    signal_type_class: 'composite_state',
    source_l1_asset: 'ga_sensitive',
    in_template: true,
    non_template_significant: false,
  }))
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
  const sat = Array.from({ length: 5 }, (_, i) => ({
    signal_id: SAT_ID(i),
    signal_type_id: 'sensitive_point_position',
    signal_type_class: 'composite_state',
    signal_tradition: 'parashari',
    signal_summary_text: `SAT: filler row ${i} [ga_sensitive]`,
    signal_headline_text: `SAT: filler row ${i} [ga_sensitive]`,
    computed_salience: TIED_SALIENCE,
    domains_affected_array: ['character', 'relationship', 'spirituality'],
    source_subsystem: 'sensitive',
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
    configuration_jsonb: { graha: 'VEN', house: 7 },
    graph_node_strength_contribution_jsonb: null,
  }
  return [...sat, venus]
}

/**
 * Installs the mocked `query` dispatcher. `anchorBehavior` controls the domain-ANCHOR slice
 * query specifically (the only query projecting `signal_id::text AS signal_id`):
 *   - 'throw'  → the anchor query rejects (models the original bare-catch failure mode)
 *   - 'hits'   → the anchor query returns rows (array of signal_ids to hand back)
 *   - 'empty'  → the anchor query succeeds but returns zero rows
 */
function installMock(opts: {
  anchorBehavior?: 'throw' | 'hits' | 'empty'
  anchorHitIds?: string[]
  storedFamily?: unknown[]
  rerankRowsOverride?: unknown[]
} = {}) {
  const family = opts.storedFamily ?? storedRankedSignals()
  const rr = opts.rerankRowsOverride ?? rerankRows()
  mockQuery.mockImplementation(async (sql: string) => {
    if (/FROM bodha_question_lenses/.test(sql)) {
      if (/COUNT\(\*\)/.test(sql)) return { rows: [{ n: 1 }] }
      return {
        rows: [{
          lens_id: LENS_ID,
          question_type: 'marriage',
          template_element_ids_jsonb: { signal_count: family.length },
          all_relevant_ranked_jsonb: { ranked_signals: family, total_count: family.length },
          lens_template_version: 'classical_v1.0',
          points_only_assertion: true,
          verification_pass_status: 'documented_approximation',
          computed_at: '2026-08-20T00:00:00Z',
        }],
      }
    }
    // The domain-ANCHOR slice.
    if (/signal_id::text AS signal_id/.test(sql)) {
      if (opts.anchorBehavior === 'throw') {
        throw new Error('simulated anchor-slice connection reset')
      }
      if (opts.anchorBehavior === 'hits') {
        return { rows: (opts.anchorHitIds ?? [VENUS_7TH_ID]).map(id => ({ signal_id: id })) }
      }
      // 'empty' or unset — matches nothing.
      return { rows: [] }
    }
    // computeLensRerank's ranker-input fetch.
    if (/FROM bodha_msr_signals/.test(sql)
        && /graph_node_strength_contribution_jsonb/.test(sql)
        && /uuid\[\]/.test(sql)) {
      return { rows: rr }
    }
    // cdlm cells, discriminated pool, hydration, chart_facts, dashas — empty path.
    return { rows: [] }
  })
}

function servedNote(content: Record<string, unknown>) {
  return String(content['ranked_signals_per_lens_rank_note'])
}

describe('F-169 — anchor_leg receipt keeps lensRankBasisNote honest about the anchor-slice guarantee', () => {
  beforeEach(() => { mockQuery.mockReset() })
  afterEach(() => { vi.restoreAllMocks() })

  it('MUST FAIL ON TODAY\'S CODE (pre-fix): anchor query throws → note must not claim the UNION, anchor_leg="failed" served', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    installMock({ anchorBehavior: 'throw' })

    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 10 }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>

    // The receipt: the anchor leg must be reported as failed, not silently absorbed.
    expect(content['ranked_signals_per_lens_anchor_leg']).toBe('failed')

    // The note must NOT assert the anchor-slice UNION ran / the significator guarantee held —
    // this is the load-bearing assertion. On the pre-fix code the note unconditionally claims
    // "guaranteed CONSIDERED" whenever rerankedLensCount > 0, regardless of the anchor leg.
    const note = servedNote(content)
    expect(note).not.toMatch(/guaranteed CONSIDERED/)
    expect(note).not.toMatch(/UNION a bounded/)
    expect(note).toMatch(/NOT guaranteed considered/)

    // And the failure was logged (non-fatal — no thrown error, no is_error response).
    expect(warnSpy).toHaveBeenCalled()
    const loggedText = warnSpy.mock.calls.map(c => c.join(' ')).join('\n')
    expect(loggedText).toMatch(/F-169/)
  })

  it('domain with no anchors configured → anchor_leg="no_anchors", note says so, guarantee not claimed', async () => {
    installMock()
    // 'transition' is a valid domain (DOMAIN_READING_VALID_DOMAINS) whose GRAHA_DOMAIN_AFFINITY
    // / DOMAIN_BHAVA_AFFINITY rows are both absent (priors_config's `Domain` type excludes it),
    // so domainAnchorActors('transition') returns { grahas: [], houses: [] } — the anchor leg's
    // guard condition is false and the leg never runs. Unlike 'other'/'general' this does NOT
    // hit computeLensRerank's early bypass, so the main rerank leg still runs and the composite
    // branch of the note is genuinely exercised.
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'transition', max_signals_per_lens: 10 }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>

    // Sanity: the main rerank leg did produce a composite basis (otherwise this test would
    // trivially pass via the honest-stored-order branch instead of exercising anchor_leg).
    expect(content['ranked_signals_per_lens_rank_basis']).toBe('composite_4d_domain_overlay')

    expect(content['ranked_signals_per_lens_anchor_leg']).toBe('no_anchors')
    const note = servedNote(content)
    expect(note).not.toMatch(/guaranteed CONSIDERED/)
    expect(note).toMatch(/declares no anchor/)
    expect(note).toMatch(/NOT guaranteed considered/)
  })

  it('anchor query succeeds but matches no lens family → anchor_leg="no_family_hits", guarantee not claimed', async () => {
    installMock({ anchorBehavior: 'empty' })
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 10 }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>

    expect(content['ranked_signals_per_lens_anchor_leg']).toBe('no_family_hits')
    const note = servedNote(content)
    expect(note).not.toMatch(/guaranteed CONSIDERED/)
    expect(note).toMatch(/matched none of/)
    expect(note).toMatch(/NOT guaranteed considered/)
  })

  it('happy path: anchor leg applies → anchor_leg="applied", note is the unchanged golden string', async () => {
    installMock({ anchorBehavior: 'hits', anchorHitIds: [VENUS_7TH_ID] })
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'relationship', max_signals_per_lens: 10 }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>

    expect(content['ranked_signals_per_lens_anchor_leg']).toBe('applied')

    const expectedNote =
      `Each lens's ranked_signals head is re-ranked by the 'relationship' composite overlay ` +
      `(graha×domain affinity × bhāva×domain congruence × varga grain × class prior × L1 śaḍbala/dignity × daśā activation), ` +
      `the SAME ranker the top-level ranked_signals and query_signals use. ` +
      `The stored bo_drishti order is build-time and domain-AGNOSTIC (raw computed_salience, no tie-break) — ` +
      `on charts where its top of distribution is a tie-block, reading the stored head as "the top N for this domain" is unsound (F-114). ` +
      `Candidate set = top 400 of each family by stored salience ` +
      `UNION a bounded 300-row anchor slice naming the domain's own ` +
      `kāraka grahas / primary bhāvas (moon/jupiter/venus · ` +
      `bhāva 4/7/8/12), because on real families the ` +
      `first kāraka-bearing row can sit far below any affordable salience window. Both legs are ` +
      `bounded: the domain's significators are guaranteed CONSIDERED, not that every family member is. ` +
      `Rows outside the candidate set keep their stored relative order and are never dropped. ` +
      `Drill query_signals for the whole family.`

    expect(servedNote(content)).toBe(expectedNote)
  })
})
