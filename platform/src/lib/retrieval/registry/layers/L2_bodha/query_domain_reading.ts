/**
 * query_domain_reading — Domain Reading (L2 Bodha)
 * =================================================
 * Drill into a life domain via two sources:
 *   - bodha_question_lenses (bo_drishti): question lenses keyed by question_type
 *     filtered at query-time via DOMAIN_TO_QUESTION_TYPES (inverted from
 *     bo_drishti.py::QUESTION_TYPE_CONFIG). No domain column in the table — mapping is pure query logic.
 *   - bodha_cdlm_cells (bo_sangati): CDLM cross-domain matrix cells (domain_row/col)
 *
 * Returns a reconciled multi-vantage domain view. Signal references are emitted
 * from CDLM cells; bodha_question_lenses carries no signal_id_refs column.
 *
 * Payload bounding (F-021R-b / F-023):
 *   - shared_signal_ids_array stripped from served cells by default (shared_signal_count
 *     is the useful scalar; raw IDs available via query_signals drill).
 *   - signal_id_refs capped to max_signal_refs (default 200) — sufficient for
 *     downstream temporal-activation filtering (query_temporal_activation top_k=20).
 *   - response_format=full restores the arrays (capped at higher limits).
 *
 * E-2 freshness contract on DEFECT-001 (R5.1 C2 item 1): constituent_facts_array on
 * referenced signals historically carried a 91.5% orphan rate (L1 hash rebuild mismatch).
 * That figure is now stale and is re-derived LIVE per call rather than restated — see
 * `provenance.defect_001` in the response. The drill link to query_signals handles
 * unresolved joins with graceful-empty regardless of the current rate.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { deriveDefect001Note } from '../../../provenance/freshness_notes'
import { demoteSignatureTier } from '../../../ranking/salience_demotion'
import {
  applyCompositeRanking, extractPrimaryBhava, extractPrimaryGraha,
} from '../../../ranking/composite_ranker'
import { fetchL1Context } from '../../../ranking/l1_context_fetcher'
import {
  grahaAffinity, bhavaAffinity, DOMAIN_BHAVA_AFFINITY, domainAnchorActors,
} from '../../../ranking/priors_config'
import { CANONICAL_DOMAINS } from '@/lib/domain_vocabulary'

// ADHIṢṬHĀNA Lane A7: this file's own comment already cited
// "brahmagyan.domain_vocabulary.CANONICAL_DOMAINS" by name (SHABDA-SHUDDHI Lane L5 Fix 4) but
// hardcoded the 13 values as a separate literal instead of importing the SSoT — textbook
// adoption debt. `VALID_DOMAINS` and the `domain` input_schema `enum` below now spread the
// real import; the two non-canonical backward-compat extras ('moksha', 'other') are retained
// verbatim (same reasoning as before: 'moksha' has its own DOMAIN_TO_SIGNAL_FILTER overlay
// distinct from 'spirituality'; 'other' means "return all lenses" via DOMAIN_TO_QUESTION_TYPES).
const DOMAIN_READING_VALID_DOMAINS: readonly string[] = [...CANONICAL_DOMAINS, 'moksha', 'other']

/** Max signal_ids hydrated with text in one bounded lookup (payload + query safety). */
const HYDRATION_ID_CAP = 2000

/** Candidate pool fetched by raw salience before the domain-composite re-rank (mirrors query_signals). */
const DISCRIMINATION_CANDIDATE_SIZE = 400
/** How many domain-discriminated signals to surface on the reading. */
const DISCRIMINATED_TOP_K = 20

/**
 * F-114 (PARIŚEṢA / CL-10) — per-lens re-rank candidate window.
 *
 * The stored `all_relevant_ranked_jsonb.ranked_signals` family is ordered by the
 * BUILD-time, domain-agnostic `computed_salience` alone (bo_drishti.py sorts on a single
 * float key with no tie-break). On the canonical chart the relationship family's top of
 * distribution is a 13-way EXACT tie at salience 2.16108 — thirteen `ga_sensitive` SATURN
 * rows (upagraha / saham / midpoint / bhṛgu-nāḍī / aprakāśa …). Slicing the head of that
 * array to serve the "top 10 marriage signals" therefore returned ten indistinguishable
 * rows, not one of which named the 7th lord, Venus, or a marriage yoga.
 *
 * `domain_salience_jsonb` does NOT rescue this: it is exactly
 * `computed_salience / cardinality(domains_affected_array)` (verified 3698/3698 rows on the
 * canonical chart), i.e. a uniform split carrying zero domain-specific information.
 *
 * The real domain-relevance machinery already exists in this repo and is already used two
 * functions above (`computeDiscriminatedSignals`): `applyCompositeRanking` with the domain
 * overlay — graha×domain affinity (VEN×relationship 1.50 vs SAT×relationship 0.90),
 * bhāva×domain congruence (DOMAIN_BHAVA_AFFINITY.relationship = {7:2.2, 12:1.6, 8:1.5,
 * 4:1.2}), varga grain, class prior, real L1 śaḍbala/dignity, dasha activation — plus a
 * three-layer tie-break that guarantees no two served rows share a `final_rank_score`.
 * F-114 is that ranker not being wired into the per-lens surface; this constant bounds the
 * candidate window it re-ranks (mirrors DISCRIMINATION_CANDIDATE_SIZE).
 *
 * A ranker can only re-rank what it is given, and a salience-head window alone is NOT enough:
 * measured on the canonical chart's marriage family (3,698 rows), the FIRST Venus-bearing row
 * sits at stored rank 902 and the FIRST 7th-house row at 1,041 — so a head window of any
 * affordable size would have re-ranked a candidate set that never contained the domain's own
 * kāraka or kalatra-bhāva, and F-114's actual complaint ("not one names the 7th lord, Venus,
 * or a marriage yoga") would have survived the fix. The candidate set is therefore
 *   salience-head window  ∪  domain-ANCHOR slice
 * where the anchor slice is a second bounded, salience-ordered query for rows naming a graha
 * or bhāva the domain's OWN affinity tables rate above neutral (`domainAnchorActors`, a pure
 * projection of GRAHA_DOMAIN_AFFINITY + DOMAIN_BHAVA_AFFINITY — no second list to drift).
 *
 * HONEST LIMITATION (disclosed on the response, never papered over): both legs are bounded,
 * so this guarantees the domain's significators are CONSIDERED, not that every family member
 * is. The whole family stays reachable via `query_signals`. See
 * `00_ARCHITECTURE/briefs/parisesa/F114_RANKING_DESIGN_CONTRACT_v1_0.md`.
 */
const LENS_RERANK_CANDIDATE_SIZE = 400
/** Bounded second leg: rows naming a domain kāraka graha or a primary domain bhāva. */
const LENS_ANCHOR_SLICE_SIZE = 300

/** Ranking-basis receipt values for a lens's served ranked_signals head. */
const LENS_RANK_BASIS_COMPOSITE = 'composite_4d_domain_overlay'
const LENS_RANK_BASIS_STORED    = 'stored_salience_build_time'

/**
 * D-1.5b Lane B-7 (Gate B B7_budgets) — per-lens cap on the served
 * `all_relevant_ranked_jsonb.ranked_signals` array. Each stored question lens carries its
 * FULL relevance family (measured 1,637 rows for wealth/property, up to 9,693 for progeny);
 * emitting it unbounded is what blew `bodha_domain_reading_get(domain=wealth)` to 909,221
 * bytes — ~785KB of it two lenses' ranked_signals alone. The Lane B-6 lens_limit fix bounded
 * the lens FAMILY (how many lenses) but not the rows INSIDE each lens; this bounds the latter.
 *
 * The default (25) intentionally equals RANKED_HYDRATE_PER_LENS — beyond it the rows were not
 * even text-hydrated (WP-1.2e), so serving them added ID-heavy bytes with no headline/summary.
 * The true family size stays visible per lens (`ranked_signals_total`) and the whole family
 * remains reachable via response_format=full (up to 200/lens) or the query_signals drill.
 */
const RANKED_SIGNALS_PER_LENS_DEFAULT = 25
const RANKED_SIGNALS_PER_LENS_MAX = 100
const RANKED_SIGNALS_PER_LENS_FULL = 200

/**
 * External reading-domain → the value present in bodha_msr_signals.domains_affected_array
 * that scopes the candidate pool. `null` = no array pre-filter (the domain is not a stored
 * tag — e.g. moksha/education); the pool is the whole chart and the composite domain overlay
 * (graha×domain + bhāva×domain + varga) does ALL the discrimination. Disclosed in provenance.
 */
// SHABDA-SHUDDHI Lane L5 (Fix 4): extended to cover all 13 canonical domains.
// Domains not stored as bodha_msr_signals domain tags use null (whole-chart ranked
// by the domain-specific graha×bhāva×varga overlay).
const DOMAIN_TO_SIGNAL_FILTER: Record<string, string | null> = {
  career:       'career',
  wealth:       'wealth',
  relationship: 'relationship',
  health:       'health',
  character:    'character',
  spirituality: 'spirituality',
  education:    null,   // not a stored domain tag — rank whole-chart by the vidyā overlay (2/4/5/9 + Me/Ju/Ke)
  progeny:      null,   // not a stored domain tag — rank whole-chart by the 5th-house/putra overlay
  family:       null,   // not a stored domain tag — rank whole-chart by the 4th-house/sukha overlay
  residence:    null,   // not a stored domain tag — rank whole-chart by the 4th-house/bhoomi overlay
  travel:       null,   // not a stored domain tag — rank whole-chart by the 3rd/12th/yatra overlay
  transition:   null,   // not a stored domain tag — rank whole-chart by the 8th-house/sandhi overlay
  general:      null,   // no overlay — return highest salience signals chart-wide
  moksha:       null,   // not a stored domain tag — rank whole-chart by the mokṣa-trikoṇa overlay (4-8-12 + Ketu)
  other:        null,   // no filter applied; all lenses returned
}

interface DiscriminatedSignal {
  signal_id: string
  headline: string | null
  summary: string | null
  computed_salience: number | null
  signal_type_class: string | null
  signature_tier: string | null
  signature_tier_demoted_from?: string
  bhava: number | null
  graha: string | null
  final_rank_score: number
  /** Inline, human-readable reason THIS signal ranks where it does for THIS domain (ND-W1.2). */
  rationale: string
}

/**
 * WP-1.2β (LCA-14 / R-44) — the domain-DISCRIMINATED ranked surface. The stored lens
 * ranked_signals sort by a domain-agnostic global `computed_salience`, so wealth/relationship/
 * career top-K were ~95% identical (Lane-6 shard-6-b0). This re-ranks a domain candidate pool
 * through the SAME composite pipeline query_signals uses, WITH the domain overlay (graha×domain
 * + bhāva×domain + varga), and returns the top-K with an inline classical rationale per row.
 */
async function computeDiscriminatedSignals(
  chart_id: string,
  ayanamsha_id: string,
  domain: string,
): Promise<{ signals: DiscriminatedSignal[]; pool_size: number; filtered_by: string | null }> {
  const filterVal = DOMAIN_TO_SIGNAL_FILTER[domain] ?? null
  const filters = ['chart_id = $1', 'ayanamsha_id = $2', '(lel_origin IS NULL OR lel_origin = false)']
  const params: unknown[] = [chart_id, ayanamsha_id]
  if (filterVal) {
    filters.push(`$${params.length + 1} = ANY(domains_affected_array)`)
    params.push(filterVal)
  }
  params.push(DISCRIMINATION_CANDIDATE_SIZE)
  const sql = `
    SELECT signal_id, signal_type_id, signal_type_class, signal_tradition,
           signal_summary_text, signal_headline_text, computed_salience,
           top_k_salience_rank, domains_affected_array, constituent_facts_array,
           source_subsystem, valence, verification_pass_status, citation_human,
           lel_origin, signature_tier, configuration_jsonb
    FROM bodha_msr_signals
    WHERE ${filters.join(' AND ')}
    ORDER BY computed_salience DESC NULLS LAST
    LIMIT $${params.length}`
  const res = await query<Record<string, unknown>>(sql, params)
  if (res.rows.length === 0) return { signals: [], pool_size: 0, filtered_by: filterVal }

  const as_of_date = new Date().toISOString().split('T')[0]
  const ctx = await fetchL1Context(chart_id, ayanamsha_id, as_of_date)
  const scored = applyCompositeRanking(
    res.rows as unknown as Parameters<typeof applyCompositeRanking>[0], ctx, domain,
  )
  const bhavaRow = DOMAIN_BHAVA_AFFINITY[domain]
  const signals: DiscriminatedSignal[] = scored.slice(0, DISCRIMINATED_TOP_K).map(s => {
    const bhava = extractPrimaryBhava(s)
    const grahaRaw = extractPrimaryGraha(s)
    const demoted = demoteSignatureTier(s as unknown as Record<string, unknown>)
    // Inline rationale (ND-W1.2): why this row ranks here for THIS domain.
    const reasons: string[] = []
    if (bhava != null) {
      const bw = bhavaAffinity(bhava, domain)
      const primaries = bhavaRow
        ? Object.entries(bhavaRow).filter(([, w]) => w >= 2.0).map(([h]) => h).join('/')
        : ''
      reasons.push(
        `bhāva ${bhava} × ${domain} congruence ${bw.toFixed(2)}` +
        (bw >= 2.0 ? ` (a primary ${domain} house)` : bw < 1.0 ? ` (outside the ${domain} house-set${primaries ? `; primaries ${primaries}` : ''})` : ''),
      )
    }
    if (grahaRaw) {
      const ga = grahaAffinity(grahaRaw, domain)
      reasons.push(`graha ${grahaRaw} × ${domain} affinity ${ga.toFixed(2)}`)
    }
    if (reasons.length === 0) reasons.push(`no bhāva/graha resolved — ranked on class-prior × strength × salience only`)
    return {
      signal_id:         String(s.signal_id),
      headline:          (s.signal_headline_text as string | null) ?? null,
      summary:           (s.signal_summary_text as string | null) ?? null,
      computed_salience: (s.computed_salience as number | null) ?? null,
      signal_type_class: (s.signal_type_class as string | null) ?? null,
      signature_tier:    (demoted['signature_tier'] as string | null) ?? null,
      ...(demoted['signature_tier_demoted_from']
        ? { signature_tier_demoted_from: demoted['signature_tier_demoted_from'] as string } : {}),
      bhava,
      graha:             grahaRaw,
      final_rank_score:  s.final_rank_score,
      rationale:         reasons.join('; '),
    }
  })
  return { signals, pool_size: res.rows.length, filtered_by: filterVal }
}

// ── F-114: per-lens domain-aware re-rank ─────────────────────────────────────────────

/**
 * Read a lens's ranked-signal array out of either schema shape
 * (object `{ranked_signals: [...]}` or the flat schema-v1 array). Returns null when neither.
 */
function readLensRankedSignals(arj: unknown): unknown[] | null {
  if (Array.isArray(arj)) return arj
  if (arj && typeof arj === 'object') {
    const rs = (arj as Record<string, unknown>)['ranked_signals']
    if (Array.isArray(rs)) return rs
  }
  return null
}

interface LensRerank {
  /** signal_id → 0-based composite rank within this lens (lower = better). */
  rankById: Map<string, number>
  /** signal_id → the ranker's own unique final_rank_score. */
  scoreById: Map<string, number>
  /** How many of the lens family actually entered the re-rank. */
  candidate_window: number
}

/**
 * F-114 — re-rank each lens's stored ranked_signals family through the SAME domain-aware
 * composite ranker `computeDiscriminatedSignals` (and query_signals, and assess_*) already
 * use, so the per-lens head served to a caller is domain-DISCRIMINATED instead of being the
 * head of a build-time, domain-agnostic, tie-degenerate salience order.
 *
 * Deterministic; no LLM; touches NO stored salience column (the ranker's standing invariant —
 * composite_ranker.ts header). One bounded DB round-trip for the union of all lenses'
 * candidate ids. Returns an EMPTY map on any failure, so the caller falls back honestly to
 * the stored order and says so via the rank-basis receipt (§N.8: a signal without a real
 * detector behind it is null, not green — here, a re-rank that did not run is reported as
 * not-run, never as though it had).
 */
async function computeLensRerank(
  chart_id: string,
  ayanamsha_id: string,
  domain: string,
  lensRows: Array<Record<string, unknown>>,
): Promise<Map<string, LensRerank>> {
  const out = new Map<string, LensRerank>()
  // 'other'/'general' request no domain overlay at all — re-ranking would add no
  // discrimination, so leave the stored order (and say so) rather than churn it.
  if (domain === 'other' || domain === 'general') return out

  // Leg 1 — salience-head window per lens, plus each lens's FULL membership set (already in
  // memory from the jsonb) so the anchor slice below can be intersected against it exactly.
  const perLens: Array<{ key: string; ids: string[]; family: Set<string> }> = []
  const allIds = new Set<string>()
  for (const lens of lensRows) {
    const key = String(lens['lens_id'] ?? '')
    if (!key) continue
    const ranked = readLensRankedSignals(lens['all_relevant_ranked_jsonb'])
    if (!ranked || ranked.length === 0) continue
    const family = new Set<string>()
    for (const rs of ranked) {
      const sid = (rs as Record<string, unknown> | null)?.['signal_id']
      if (typeof sid === 'string' && sid) family.add(sid)
    }
    const ids: string[] = []
    for (const rs of ranked.slice(0, LENS_RERANK_CANDIDATE_SIZE)) {
      const sid = (rs as Record<string, unknown> | null)?.['signal_id']
      if (typeof sid === 'string' && sid) { ids.push(sid); allIds.add(sid) }
    }
    if (ids.length > 0) perLens.push({ key, ids, family })
  }
  if (allIds.size === 0) return out

  // Leg 2 — domain-ANCHOR slice: rows naming a graha or bhāva the domain's own affinity tables
  // rate above neutral. Without this the ranker never sees Venus or the 7th house on a real
  // marriage family (measured stored ranks 902 / 1041 — far outside any affordable head window).
  const anchorIdsByLens = new Map<string, string[]>()
  const anchors = domainAnchorActors(domain)
  if (anchors.graha_aliases.length > 0 || anchors.houses.length > 0) {
    try {
      const filters = ['chart_id = $1', 'ayanamsha_id = $2', '(lel_origin IS NULL OR lel_origin = false)']
      const params: unknown[] = [chart_id, ayanamsha_id]
      const tag = DOMAIN_TO_SIGNAL_FILTER[domain] ?? null
      if (tag) { filters.push(`$${params.length + 1} = ANY(domains_affected_array)`); params.push(tag) }
      const anchorPreds: string[] = []
      if (anchors.graha_aliases.length > 0) {
        params.push(anchors.graha_aliases)
        anchorPreds.push(`lower(configuration_jsonb->>'graha') = ANY($${params.length}::text[])`)
      }
      if (anchors.houses.length > 0) {
        const houseStrings = anchors.houses.map(String)
        params.push(houseStrings)
        // Mirrors extractPrimaryBhava's read order (composite_ranker.ts) — same keys, same precedence.
        anchorPreds.push(
          `COALESCE(configuration_jsonb->>'target_house', configuration_jsonb->>'house',` +
          ` configuration_jsonb->>'bhava', configuration_jsonb->>'bhava_num',` +
          ` configuration_jsonb->>'source_house') = ANY($${params.length}::text[])`,
        )
        params.push(`house_(${anchors.houses.join('|')})(?![0-9])`)
        anchorPreds.push(`signal_type_id ~ $${params.length}`)
      }
      filters.push(`(${anchorPreds.join(' OR ')})`)
      params.push(LENS_ANCHOR_SLICE_SIZE)
      const anchorRes = await query<Record<string, unknown>>(
        `SELECT signal_id::text AS signal_id FROM bodha_msr_signals
         WHERE ${filters.join(' AND ')}
         ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
         LIMIT $${params.length}`,
        params,
      )
      for (const { key, family } of perLens) {
        const hits: string[] = []
        for (const r of anchorRes.rows) {
          const sid = String(r['signal_id'] ?? '')
          // Only promote a row that genuinely belongs to THIS lens's family — the anchor
          // query is domain-scoped, not lens-scoped, and a lens must never be handed a row
          // it does not actually carry.
          if (sid && family.has(sid)) hits.push(sid)
        }
        if (hits.length > 0) {
          anchorIdsByLens.set(key, hits)
          for (const sid of hits) allIds.add(sid)
        }
      }
    } catch {
      // Non-fatal: the re-rank still runs on the salience-head window alone.
    }
  }

  try {
    // ONE bounded fetch of exactly the columns applyCompositeRanking reads. Fetching the
    // ranker's inputs (rather than trusting the lens jsonb's 6-field projection) is the
    // §N.5 discipline: the ranker reads the L2 row, it never re-derives it from a copy.
    const res = await query<Record<string, unknown>>(
      `SELECT signal_id, signal_type_id, signal_type_class, signal_tradition,
              signal_summary_text, signal_headline_text, computed_salience,
              top_k_salience_rank, domains_affected_array, constituent_facts_array,
              source_subsystem, valence, verification_pass_status, citation_human,
              lel_origin, signature_tier, configuration_jsonb,
              graph_node_strength_contribution_jsonb
       FROM bodha_msr_signals
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND signal_id = ANY($3::uuid[])`,
      [chart_id, ayanamsha_id, [...allIds]],
    )
    if (res.rows.length === 0) return out
    const rowById = new Map<string, Record<string, unknown>>()
    for (const r of res.rows) rowById.set(String(r['signal_id']), r)

    const as_of_date = new Date().toISOString().split('T')[0]
    const ctx = await fetchL1Context(chart_id, ayanamsha_id, as_of_date)

    for (const { key, ids } of perLens) {
      const candidateIds = [...new Set([...ids, ...(anchorIdsByLens.get(key) ?? [])])]
      const rows = candidateIds
        .map(id => rowById.get(id))
        .filter((r): r is Record<string, unknown> => r !== undefined)
      if (rows.length === 0) continue
      const scored = applyCompositeRanking(
        rows as unknown as Parameters<typeof applyCompositeRanking>[0], ctx, domain,
      )
      const rankById  = new Map<string, number>()
      const scoreById = new Map<string, number>()
      scored.forEach((s, i) => {
        const sid = String(s.signal_id)
        rankById.set(sid, i)
        scoreById.set(sid, s.final_rank_score)
      })
      out.set(key, { rankById, scoreById, candidate_window: rows.length })
    }
  } catch {
    // Non-fatal: caller keeps the stored order and reports rank_basis honestly.
    return new Map()
  }
  return out
}

/**
 * F-114 — apply a lens's re-rank to its stored ranked_signals array.
 * Rows inside the re-ranked candidate window sort by composite rank; rows outside it keep
 * their stored relative order and stay strictly BELOW the window (never silently dropped —
 * B.10). Returns the reordered array plus the basis receipt.
 */
function applyLensRerank(
  ranked: unknown[],
  rr: LensRerank | undefined,
): { ordered: unknown[]; basis: string; candidate_window: number | null } {
  if (!rr || rr.rankById.size === 0) {
    return { ordered: ranked, basis: LENS_RANK_BASIS_STORED, candidate_window: null }
  }
  const OUTSIDE = Number.MAX_SAFE_INTEGER
  const decorated = ranked.map((rs, storedIdx) => {
    const sid = (rs as Record<string, unknown> | null)?.['signal_id']
    const key = typeof sid === 'string' ? sid : ''
    const r = rr.rankById.get(key)
    const score = rr.scoreById.get(key)
    return {
      rs: (r !== undefined && rs && typeof rs === 'object' && !Array.isArray(rs))
        ? { ...(rs as Record<string, unknown>), composite_rank: r, final_rank_score: score ?? null }
        : rs,
      order: r ?? OUTSIDE,
      storedIdx,
    }
  })
  decorated.sort((a, b) => (a.order - b.order) || (a.storedIdx - b.storedIdx))
  return {
    ordered: decorated.map(d => d.rs),
    basis: LENS_RANK_BASIS_COMPOSITE,
    candidate_window: rr.candidate_window,
  }
}

interface HydratedSignalText {
  signal_id: string
  headline: string | null
  summary: string | null
  signature_tier: string | null
  signature_tier_demoted_from?: string
}

/**
 * WP-1.2(e) (LCA-18c): hydrate bare signal_ids with headline/summary text so
 * get_domain_reading rows carry human-readable text, not IDs-without-text. One bounded
 * chart-scoped `signal_id = ANY(...)` lookup over the DISTINCT ids the response will
 * actually serve. Also demotes the hydrated signature_tier (WP-1.2d) so descriptive/
 * per-varga rows don't surface as major/chart_defining here either.
 */
async function hydrateSignalText(
  chart_id: string,
  ayanamsha_id: string,
  signalIds: string[],
): Promise<Map<string, HydratedSignalText>> {
  const map = new Map<string, HydratedSignalText>()
  const distinct = Array.from(new Set(signalIds.filter(Boolean))).slice(0, HYDRATION_ID_CAP)
  if (distinct.length === 0) return map
  const res = await query<Record<string, unknown>>(
    `SELECT signal_id, signal_headline_text, signal_summary_text, signature_tier,
            signal_type_id, configuration_jsonb
     FROM bodha_msr_signals
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND signal_id::text = ANY($3::text[])`,
    [chart_id, ayanamsha_id, distinct],
  )
  for (const row of res.rows) {
    const demoted = demoteSignatureTier(row)
    const sid = String(row['signal_id'] ?? '')
    if (!sid) continue
    map.set(sid, {
      signal_id: sid,
      headline: (row['signal_headline_text'] as string | null) ?? null,
      summary: (row['signal_summary_text'] as string | null) ?? null,
      signature_tier: (demoted['signature_tier'] as string | null) ?? null,
      ...(demoted['signature_tier_demoted_from']
        ? { signature_tier_demoted_from: demoted['signature_tier_demoted_from'] as string }
        : {}),
    })
  }
  return map
}

/**
 * Maps each valid life-domain to the question_types that cover it.
 * Inverted from bo_drishti.py::QUESTION_TYPE_CONFIG (source of truth).
 * Domain 'other' returns an empty array — no filter applied (all lenses returned).
 */
const DOMAIN_TO_QUESTION_TYPES: Record<string, string[]> = {
  career:       ['career', 'progeny'],
  wealth:       ['wealth', 'property'],
  relationship: ['marriage', 'progeny'],
  health:       ['health', 'longevity'],
  // WP-1.2β: un-collapse the over-mapped domains. character = self+manas (1/3), no longer
  // borrowing 'education'; education becomes its OWN vidyā domain (4-vidyā-sthāna + 2-vāk);
  // spirituality stays dharma-centred (9); moksha is DISTINCT (12-8-4 trikoṇa, not a 9-alias).
  character:    ['character', 'siblings'],
  education:    ['education', 'wealth'],
  spirituality: ['spirituality', 'education'],
  moksha:       ['spirituality', 'foreign_travel', 'longevity'],
  other:        [],
  // SHABDA-SHUDDHI Lane L5 (Fix 4): canonical domains newly accessible.
  // These map to question_types using the best available overlapping lens type;
  // where no specific lens type covers them, an empty array returns all lenses.
  progeny:      ['progeny'],
  family:       ['health'],       // closest lens covering 4th-house sukha themes
  residence:    ['property'],
  travel:       ['foreign_travel'],
  transition:   ['longevity'],    // closest lens covering 8th-house transformation
  general:      [],               // no filter — all lenses returned (same as 'other')
}

export const queryDomainReadingCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_domain_reading',
  type:  'tool',
  layer: 'L2',
  name:  'query_domain_reading',

  description: [
    'Drill into a specific life domain for a chart using the Bodha synthesis layer.',
    'Returns question lenses from bodha_question_lenses filtered by question_type via the',
    'DOMAIN_TO_QUESTION_TYPES mapping (inverted from bo_drishti.py::QUESTION_TYPE_CONFIG),',
    'and the domain-scoped CDLM cross-domain matrix cells from bodha_cdlm_cells.',
    'CDLM cells include shared_signal_count; shared_signal_ids_array is omitted by default (token-safe).',
    'signal_id_refs emits a capped set of signal IDs (default 200) for downstream hydration.',
    'Use response_format=full to include shared_signal_ids_array per cell and up to 2000 signal refs.',
    'If no lens exists for the requested domain, returns the list of available domains.',
    'Multi-vantage: lens covers house + karaka + varga vantages; CDLM covers cross-domain spillover.',
    'Follows query_ucd in the reading hierarchy; drill further with query_signals.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: ['marsys://tool/L2/query_signals'],

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    domain: {
      type: 'string',
      description: [
        'Life domain to query. 13 canonical domains:',
        'career, wealth, relationship, health, character, spirituality, education,',
        'progeny, family, residence, travel, transition, general.',
        'Plus backward-compat extras: moksha (spirituality alias via 4-8-12 overlay), other (all lenses).',
        'education = vidyā (bhāva 4/5/2/9 + Me/Ju/Ke); moksha = the 4-8-12 mokṣa-trikoṇa + Ketu',
        '(NOT a spirituality alias — has its own overlay). Each domain re-ranks signals by a',
        'domain-specific graha×bhāva×varga overlay (see ranked_signals[].rationale).',
        'If omitted or unrecognized, returns the list of available domains for this chart.',
      ].join(' '),
      enum: [...DOMAIN_READING_VALID_DOMAINS],
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to filter by (default: 'lahiri_chitrapaksha').",
    },
    max_signal_refs: {
      type: 'number',
      description: [
        'Max signal IDs to include in signal_id_refs (default 200).',
        'Capped at 2000. Sufficient for downstream temporal-activation filtering.',
        'Use response_format=full to get up to 2000 automatically.',
      ].join(' '),
    },
    response_format: {
      type: 'string',
      description: [
        "Controls payload verbosity. 'default' (or omitted): token-safe —",
        'shared_signal_ids_array omitted from cells, signal_id_refs capped to 200.',
        "'full': shared_signal_ids_array included (capped per cell), signal_id_refs capped to 2000.",
      ].join(' '),
      enum: ['default', 'full'],
    },
    lens_limit: {
      type: 'number',
      description: 'D-1.5b response budget: max bodha_question_lenses rows to return (default 60, ' +
        'max 200). See `lens_pagination.total` in the response for the true family size.',
    },
    lens_offset: {
      type: 'number',
      description: 'D-1.5b response budget: pagination offset into the question-lens family ' +
        '(default 0). Use with lens_limit to page beyond the default 60.',
    },
    max_signals_per_lens: {
      type: 'number',
      description: 'D-1.5b B-7 response budget: max ranked_signals to serve INSIDE each ' +
        'question lens (default 25, max 100). The stored lens holds its full relevance family ' +
        '(hundreds–thousands of rows); serving it unbounded blew this response past 900KB. ' +
        'Each lens still reports `ranked_signals_total` (the true family size) and ' +
        '`ranked_signals_capped`. Use response_format=full to raise the per-lens cap to 200, ' +
        'or drill via query_signals for the whole family.',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 5,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id     = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const domain          = args['domain'] as string | undefined
    const ayanamsha_id    = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const response_format = (args['response_format'] as string | undefined) ?? 'default'
    const is_full         = response_format === 'full'
    // Default cap: 200 (enough for temporal-activation filter top_k=20 with headroom).
    // Full mode cap: 2000. Hard ceiling either way.
    const max_signal_refs = is_full
      ? 2000
      : Math.min(
          typeof args['max_signal_refs'] === 'number' ? (args['max_signal_refs'] as number) : 200,
          2000,
        )
    // D-1.5b (item 2, response budget): the lens family was previously a hardcoded LIMIT 60
    // with no offset and no total count — a chart with more than 60 matching lenses had the
    // remainder permanently unreachable. Bounded, honest pagination now applies.
    const lens_limit  = Math.min(Math.max(typeof args['lens_limit'] === 'number' ? (args['lens_limit'] as number) : 60, 1), 200)
    const lens_offset = Math.max(typeof args['lens_offset'] === 'number' ? (args['lens_offset'] as number) : 0, 0)
    // D-1.5b B-7 (Gate B B7_budgets): per-lens ranked_signals cap — the unbounded section
    // that kept this response at ~909KB even after B-6's lens-family pagination. Full mode
    // raises the cap to 200/lens (still bounded); default/explicit mode is 25 (max 100).
    const max_signals_per_lens = is_full
      ? RANKED_SIGNALS_PER_LENS_FULL
      : Math.min(
          Math.max(typeof args['max_signals_per_lens'] === 'number' ? (args['max_signals_per_lens'] as number) : RANKED_SIGNALS_PER_LENS_DEFAULT, 1),
          RANKED_SIGNALS_PER_LENS_MAX,
        )

    // SHABDA-SHUDDHI Lane L5 (Fix 4): gate was inverted — blocked canonical domains
    // (progeny/family/residence/travel/transition/general) and passed non-canonical
    // 'moksha' (a spirituality alias) through. Extended to cover all 13 canonical domains.
    // 'other' retained for "return all lenses" fallback (DOMAIN_TO_QUESTION_TYPES maps it
    // to []). 'moksha' retained for backward compat (handled by DOMAIN_TO_SIGNAL_FILTER
    // as null-filter = whole-chart ranking with moksha overlay). ADHIṢṬHĀNA Lane A7: the
    // literal below is now DOMAIN_READING_VALID_DOMAINS (module-level, sourced from the
    // CANONICAL_DOMAINS SSoT import) instead of a second inline copy of the same 15 values.

    try {
      // Domain discovery is sourced from bodha_cdlm_cells (domain_row/domain_col).
      // bodha_question_lenses has no domain column; lenses are filtered via DOMAIN_TO_QUESTION_TYPES.
      if (!domain || !DOMAIN_READING_VALID_DOMAINS.includes(domain)) {
        const availSql = `
          SELECT DISTINCT d AS domain
          FROM bodha_cdlm_cells,
               LATERAL (VALUES (domain_row), (domain_col)) AS v(d)
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND d IS NOT NULL
          ORDER BY d
        `
        const availRes = await query<Record<string, unknown>>(availSql, [chart_id, ayanamsha_id])
        return {
          content: {
            chart_id,
            ayanamsha_id,
            available_domains: availRes.rows,
            requested_domain:  domain ?? null,
            note: domain ? `Domain '${domain}' not found. Available domains listed.` : 'No domain requested.',
          },
          is_error: false,
        }
      }

      // Question lenses from bodha_question_lenses.
      // bodha_question_lenses has no domain column; lenses are keyed by question_type.
      // We resolve domain -> question_types via DOMAIN_TO_QUESTION_TYPES and apply
      // a WHERE question_type = ANY($3) filter when the domain has a non-empty mapping.
      // Domain 'other' (or empty mapping) skips the filter and returns all lenses.
      const relevantQuestionTypes = DOMAIN_TO_QUESTION_TYPES[domain] ?? []
      const filterByQuestionType = relevantQuestionTypes.length > 0

      const lensSql = filterByQuestionType
        ? `
        SELECT
          lens_id,
          question_type,
          template_element_ids_jsonb,
          all_relevant_ranked_jsonb,
          lens_template_version,
          points_only_assertion,
          verification_pass_status,
          computed_at
        FROM bodha_question_lenses
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND question_type = ANY($3)
        ORDER BY question_type
        LIMIT $4 OFFSET $5
      `
        : `
        SELECT
          lens_id,
          question_type,
          template_element_ids_jsonb,
          all_relevant_ranked_jsonb,
          lens_template_version,
          points_only_assertion,
          verification_pass_status,
          computed_at
        FROM bodha_question_lenses
        WHERE chart_id = $1 AND ayanamsha_id = $2
        ORDER BY question_type
        LIMIT $3 OFFSET $4
      `

      // D-1.5b: genuine COUNT(*) of the SAME filter the page above is drawn from, so
      // `lens_pagination.total` is a real family size, not the page length mislabeled as total.
      const lensCountSql = filterByQuestionType
        ? `SELECT COUNT(*)::int AS n FROM bodha_question_lenses WHERE chart_id = $1 AND ayanamsha_id = $2 AND question_type = ANY($3)`
        : `SELECT COUNT(*)::int AS n FROM bodha_question_lenses WHERE chart_id = $1 AND ayanamsha_id = $2`

      // CDLM cross-domain cell from bodha_cdlm_cells (real columns)
      const cdlmSql = `
        SELECT
          cell_id,
          domain_row,
          domain_col,
          domain_relationship_class,
          shared_signal_count,
          net_linkage_strength,
          computed_linkage_strength,
          shared_signal_ids_array,
          dominant_linkage_rank_in_chart,
          cell_remedy_priority_rank,
          computed_at
        FROM bodha_cdlm_cells
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND (domain_row = $3 OR domain_col = $3)
        ORDER BY net_linkage_strength DESC NULLS LAST
        LIMIT 10
      `

      const [lensRes, lensCountRes, cdlmRes, discriminated] = await Promise.all([
        filterByQuestionType
          ? query<Record<string, unknown>>(lensSql, [chart_id, ayanamsha_id, relevantQuestionTypes, lens_limit, lens_offset])
          : query<Record<string, unknown>>(lensSql, [chart_id, ayanamsha_id, lens_limit, lens_offset]),
        filterByQuestionType
          ? query<{ n: number }>(lensCountSql, [chart_id, ayanamsha_id, relevantQuestionTypes])
          : query<{ n: number }>(lensCountSql, [chart_id, ayanamsha_id]),
        query<Record<string, unknown>>(cdlmSql, [chart_id, ayanamsha_id, domain]),
        // WP-1.2β: domain-discriminated composite ranked surface ('other' has no overlay).
        domain === 'other'
          ? Promise.resolve({ signals: [], pool_size: 0, filtered_by: null })
          : computeDiscriminatedSignals(chart_id, ayanamsha_id, domain),
      ])
      const lensTotal = lensCountRes.rows[0]?.n ?? lensRes.rows.length

      // F-114 (CL-10): domain-aware re-rank of each lens's ranked_signals family, BEFORE the
      // per-lens head is sliced or hydrated — otherwise the head is the build-time salience
      // order, whose top of distribution is a 13-way exact tie on the canonical chart.
      const lensRerank = await computeLensRerank(
        chart_id, ayanamsha_id, domain, lensRes.rows as Array<Record<string, unknown>>,
      )
      const lensRankBases = new Map<string, { basis: string; candidate_window: number | null }>()

      // Collect signal refs from CDLM cells and apply bounding.
      // shared_signal_ids_array is stripped from served cells in default mode
      // (shared_signal_count already present; raw IDs available via query_signals).
      const MAX_IDS_PER_CELL_FULL = 50
      const allSignalRefs = new Set<string>()

      const cdlmCells = (cdlmRes.rows as Array<Record<string, unknown>>).map(cell => {
        const ids = Array.isArray(cell['shared_signal_ids_array'])
          ? (cell['shared_signal_ids_array'] as string[])
          : []

        // Accumulate into the global ref set (capped later)
        for (const id of ids) allSignalRefs.add(id)

        if (is_full) {
          // Full mode: include the array but cap per cell to avoid runaway payloads
          return ids.length > MAX_IDS_PER_CELL_FULL
            ? { ...cell, shared_signal_ids_array: ids.slice(0, MAX_IDS_PER_CELL_FULL), shared_signal_ids_truncated: true }
            : cell
        }
        // Default: strip shared_signal_ids_array — shared_signal_count is the useful signal
        const { shared_signal_ids_array: _dropped, ...rest } = cell
        return rest
      })

      const signalRefsTotal = allSignalRefs.size
      const signalRefsArray = Array.from(allSignalRefs).slice(0, max_signal_refs)

      // WP-1.2(e) (LCA-18c): gather the signal_ids this response will actually surface —
      // the CDLM-derived refs PLUS the top ranked_signals inside each question lens — and
      // hydrate them all with headline/summary text in one bounded lookup, so no served row
      // is a bare ID-without-text.
      // D-1.5b B-7: hydrate exactly the rows we will SERVE per lens (max_signals_per_lens),
      // so no served ranked_signal is a bare ID-without-text (WP-1.2e) and no un-served row
      // pays a hydration lookup.
      // F-114: hydrate the rows the RE-RANKED head will actually serve, not the stored-salience
      // head — otherwise the composite-ranked rows come back as bare IDs-without-text.
      const lensRankedIds: string[] = []
      for (const lens of lensRes.rows as Array<Record<string, unknown>>) {
        const ranked = readLensRankedSignals(lens['all_relevant_ranked_jsonb'])
        if (!ranked) continue
        const { ordered } = applyLensRerank(ranked, lensRerank.get(String(lens['lens_id'] ?? '')))
        for (const rs of ordered.slice(0, max_signals_per_lens)) {
          const sid = (rs as Record<string, unknown> | null)?.['signal_id']
          if (typeof sid === 'string' && sid) lensRankedIds.push(sid)
        }
      }
      const textById = await hydrateSignalText(
        chart_id, ayanamsha_id, [...signalRefsArray, ...lensRankedIds],
      )

      // Hydrated ref rows (replaces the bare id list; signal_id_refs kept for back-compat).
      const signalRefs = signalRefsArray.map(sid => textById.get(sid) ?? {
        signal_id: sid, headline: null, summary: null, signature_tier: null,
      })

      // Enrich each lens's ranked_signals objects in place with headline/summary/tier.
      // D-1.5b B-7 (Gate B B7_budgets): SLICE ranked_signals to max_signals_per_lens BEFORE
      // enriching — the stored family is up to ~9.7k rows/lens and emitting it whole is what
      // kept this response ~909KB. The true family size is disclosed per lens
      // (ranked_signals_total / ranked_signals_capped) and the whole family stays reachable
      // via response_format=full (200/lens) or the query_signals drill.
      let anyLensCapped = false
      let anyTemplateIdsCapped = false
      const hydratedLenses = (lensRes.rows as Array<Record<string, unknown>>).map(lensRaw => {
        // D-1.5b B-7 (Gate B B7_budgets, 2nd pass): the ranked_signals cap above killed the
        // #1 offender, but each lens ALSO carries `template_element_ids_jsonb.signal_ids` — the
        // SAME relevance family as a raw UUID list (measured ~63KB/lens, ~126KB for 2 lenses,
        // which kept the served response at ~155KB > the 100KB gate even after ranked_signals
        // was bounded). Cap that ID list to the same per-lens budget; the true count is already
        // disclosed by the sibling `signal_count` field, so nothing is lost — the full family is
        // reachable via response_format=full or the query_signals drill, same as ranked_signals.
        const lens = { ...lensRaw }
        const teij = lens['template_element_ids_jsonb']
        if (teij && typeof teij === 'object' && !Array.isArray(teij)) {
          const teijObj = teij as Record<string, unknown>
          const ids = teijObj['signal_ids']
          if (Array.isArray(ids) && ids.length > max_signals_per_lens) {
            anyTemplateIdsCapped = true
            lens['template_element_ids_jsonb'] = {
              ...teijObj,
              signal_ids: (ids as unknown[]).slice(0, max_signals_per_lens),
              signal_ids_total: ids.length,
              signal_ids_capped: true,
            }
          }
        }
        const arj = lens['all_relevant_ranked_jsonb']
        // F-114 (CL-10): re-order the family by the domain-aware composite ranker BEFORE the
        // head is sliced. Without this, the served "top N for this domain" is the head of the
        // build-time domain-agnostic salience order — on the canonical chart, ten SATURN
        // ga_sensitive rows all tied at salience 2.16108, none naming the 7th lord or Venus.
        const rr = lensRerank.get(String(lens['lens_id'] ?? ''))
        if (arj && typeof arj === 'object' && !Array.isArray(arj)) {
          const arjObj = arj as Record<string, unknown>
          const ranked = arjObj['ranked_signals']
          if (Array.isArray(ranked)) {
            const total = ranked.length
            const capped = total > max_signals_per_lens
            if (capped) anyLensCapped = true
            const { ordered, basis, candidate_window } = applyLensRerank(ranked, rr)
            lensRankBases.set(String(lens['lens_id'] ?? ''), { basis, candidate_window })
            const enriched = ordered.slice(0, max_signals_per_lens).map(rs => {
              const r = rs as Record<string, unknown>
              const t = typeof r['signal_id'] === 'string' ? textById.get(r['signal_id'] as string) : undefined
              return t ? { ...r, headline: t.headline, summary: t.summary, signature_tier: t.signature_tier } : r
            })
            return {
              ...lens,
              all_relevant_ranked_jsonb: { ...arjObj, ranked_signals: enriched, total_count: total },
              ranked_signals_total:  total,
              ranked_signals_capped: capped,
              ranked_signals_rank_basis: basis,
              ...(candidate_window !== null ? { ranked_signals_rerank_window: candidate_window } : {}),
            }
          }
        }
        // Flat-array schema-v1 fallback: bound it too.
        if (Array.isArray(arj)) {
          const total = arj.length
          const capped = total > max_signals_per_lens
          if (capped) anyLensCapped = true
          const { ordered, basis, candidate_window } = applyLensRerank(arj as unknown[], rr)
          lensRankBases.set(String(lens['lens_id'] ?? ''), { basis, candidate_window })
          return {
            ...lens,
            all_relevant_ranked_jsonb: ordered.slice(0, max_signals_per_lens),
            ranked_signals_total:  total,
            ranked_signals_capped: capped,
            ranked_signals_rank_basis: basis,
            ...(candidate_window !== null ? { ranked_signals_rerank_window: candidate_window } : {}),
          }
        }
        return lens
      })

      // F-114: honest roll-up receipt for the per-lens rank basis (§N.8 — a signal must be
      // computed by a detector that measures the claim it asserts; here the claim is
      // "these rows are domain-ranked", and the receipt reports it per lens, truthfully,
      // including when the re-rank did NOT run).
      const rerankedLensCount = [...lensRankBases.values()]
        .filter(v => v.basis === LENS_RANK_BASIS_COMPOSITE).length
      const lensRankBasisNote = rerankedLensCount > 0
        ? `Each lens's ranked_signals head is re-ranked by the '${domain}' composite overlay ` +
          `(graha×domain affinity × bhāva×domain congruence × varga grain × class prior × L1 śaḍbala/dignity × daśā activation), ` +
          `the SAME ranker the top-level ranked_signals and query_signals use. ` +
          `The stored bo_drishti order is build-time and domain-AGNOSTIC (raw computed_salience, no tie-break) — ` +
          `on charts where its top of distribution is a tie-block, reading the stored head as "the top N for this domain" is unsound (F-114). ` +
          `Candidate set = top ${LENS_RERANK_CANDIDATE_SIZE} of each family by stored salience ` +
          `UNION a bounded ${LENS_ANCHOR_SLICE_SIZE}-row anchor slice naming the domain's own ` +
          `kāraka grahas / primary bhāvas (${domainAnchorActors(domain).grahas.join('/') || '—'} · ` +
          `bhāva ${domainAnchorActors(domain).houses.join('/') || '—'}), because on real families the ` +
          `first kāraka-bearing row can sit far below any affordable salience window. Both legs are ` +
          `bounded: the domain's significators are guaranteed CONSIDERED, not that every family member is. ` +
          `Rows outside the candidate set keep their stored relative order and are never dropped. ` +
          `Drill query_signals for the whole family.`
        : `ranked_signals are served in their STORED bo_drishti order (build-time raw computed_salience, domain-agnostic, no tie-break). ` +
          `No domain composite re-rank was applied for this call — read the head as a salience listing, NOT as "the top N for ${domain}" (F-114).`

      // E-2 freshness contract: re-derive DEFECT-001 live for this chart rather than
      // restating the historical "91.5% orphan" literal.
      const defect001 = await deriveDefect001Note(chart_id)

      return {
        content: {
          chart_id,
          ayanamsha_id,
          domain,
          // WP-1.2β (LCA-14 / R-44): THE domain-discriminated ranked surface. Unlike the stored
          // lens ranked_signals (sorted by domain-agnostic global salience → ~95% identical
          // across domains), these are re-ranked by the domain's graha×bhāva×varga overlay, so
          // wealth/relationship/moksha/etc. surface genuinely different signals. Each row carries
          // an inline `rationale` (ND-W1.2). This is the surface to read for a domain-SPECIFIC view.
          ranked_signals:         discriminated.signals,
          ranked_signals_note:    discriminated.filtered_by
            ? `Composite-ranked over ${discriminated.pool_size} '${discriminated.filtered_by}'-tagged candidates with the ${domain} overlay (graha×bhāva×varga). See each row's rationale.`
            : `'${domain}' is not a stored signal domain-tag; ranked whole-chart (${discriminated.pool_size} candidates) purely by the ${domain} classical overlay (graha×bhāva×varga). See each row's rationale.`,
          question_lenses:        hydratedLenses,
          // F-114 (CL-10): rank-basis receipt for the per-lens ranked_signals heads.
          ranked_signals_per_lens_rank_basis: rerankedLensCount > 0
            ? LENS_RANK_BASIS_COMPOSITE : LENS_RANK_BASIS_STORED,
          ranked_signals_per_lens_reranked_lenses: rerankedLensCount,
          ranked_signals_per_lens_rank_note: lensRankBasisNote,
          // D-1.5b B-7 (Gate B B7_budgets): honest receipt for the per-lens ranked_signals
          // cap — the section whose unbounded emission (up to ~9.7k rows/lens) kept this
          // response at ~909KB. Per-lens ranked_signals_total/ranked_signals_capped carry the
          // per-lens detail; this is the roll-up + recovery pointer.
          ranked_signals_per_lens_cap: max_signals_per_lens,
          ranked_signals_per_lens_note: anyLensCapped
            ? `Each question lens serves at most ${max_signals_per_lens} ranked_signals (see per-lens ranked_signals_total for the true family size). ` +
              (is_full ? 'response_format=full is already applied (cap 200/lens). ' : 'Use response_format=full (cap 200/lens), max_signals_per_lens (≤100), or drill query_signals for the whole family.')
            : `All lenses returned their full ranked_signals family (each ≤ ${max_signals_per_lens}).`,
          // D-1.5b B-7 (2nd pass): honest receipt for the per-lens template_element_ids_jsonb.signal_ids
          // cap — the raw-UUID relevance-family list that dominated the response (~63KB/lens) once
          // ranked_signals was bounded. Same cap, same recovery path; per-lens signal_ids_total
          // discloses the true count.
          template_element_ids_per_lens_note: anyTemplateIdsCapped
            ? `Each lens's template_element_ids_jsonb.signal_ids is capped at ${max_signals_per_lens} (see per-lens signal_ids_total / the sibling signal_count for the true family size). Use response_format=full or drill query_signals for the whole family.`
            : `All lenses returned their full template_element_ids_jsonb.signal_ids family (each ≤ ${max_signals_per_lens}).`,
          cdlm_cells:             cdlmCells,
          signal_refs:            signalRefs,
          signal_id_refs:         signalRefsArray,
          signal_id_refs_total:   signalRefsTotal,
          signal_id_refs_capped:  signalRefsArray.length < signalRefsTotal,
          lens_count:             lensRes.rows.length,
          // D-1.5b response budget: honest pagination receipt for the question-lens family —
          // previously a hardcoded LIMIT 60 with no offset/total, so any chart with more than
          // 60 matching lenses had the remainder permanently unreachable.
          lens_pagination: {
            offset: lens_offset,
            limit: lens_limit,
            total: lensTotal,
            returned_count: lensRes.rows.length,
            more_available: lens_offset + lensRes.rows.length < lensTotal,
          },
          cdlm_cell_count:        cdlmRes.rows.length,
          drill_next:             'marsys://tool/L2/query_signals',
          response_format,
          provenance: {
            tables: ['bodha_question_lenses', 'bodha_cdlm_cells'],
            model_mismatch_note: [
              'bodha_question_lenses has no domain column; lenses are filtered at query-time',
              'via DOMAIN_TO_QUESTION_TYPES (source: bo_drishti.py::QUESTION_TYPE_CONFIG).',
              'Domain \'other\' or unmapped domains return all lenses (no filter).',
              'Signal references derive from CDLM cells only.',
            ].join(' '),
            // Structured, live-derived (E-2 freshness contract) — read this, not any
            // historical figure.
            defect_001: defect001,
            // Legacy string field retained (additive) — sourced from the same live derivation.
            defect_001_note: defect001.note,
            hydration_note: `WP-1.2(e): signal_refs and lens ranked_signals carry headline/summary ` +
              `text (hydrated from bodha_msr_signals); ${textById.size} id(s) resolved to text. ` +
              `signature_tier on hydrated rows reflects the WP-1.2(d) serving cap.`,
            bounding_note: is_full
              ? `response_format=full: shared_signal_ids_array included (capped ${MAX_IDS_PER_CELL_FULL}/cell), signal_id_refs capped at ${max_signal_refs}.`
              : `response_format=default: shared_signal_ids_array omitted from cells (use shared_signal_count); signal_id_refs capped at ${max_signal_refs} of ${signalRefsTotal} total.`,
          },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id, domain },
        is_error: true,
      }
    }
  },
}
