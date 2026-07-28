/**
 * query_ucd — Chart Digest Query (L2 Bodha) — a.k.a. `synthesis_query` (design §5 #7)
 * ======================================================================================
 * Reads vw_chart_digest + bodha_msr_signals top signals for a chart.
 * Returns a compact, LLM-ready Bodha synthesis digest:
 *   - Entity profiles: hierarchically-aggregated composite-ranked signal groups (E-6)
 *   - Top MSR signals by composite rank (atomic, backward-compat, top K)
 *   - Domain convergence leaders (top 5 domains)
 *   - Contradiction count
 *   - Weakest graha + priority class
 *   - Trap1 audit count
 *
 * R5 W1 (design §E-6, "THE ORIENT SURFACE IS RANKING-GOVERNED, ALWAYS"): P2 found the
 * digest reading a raw `ORDER BY computed_salience` (coarse) while the drill surface
 * (query_signals.ts) already applies the 4-dimensional composite ranker — map and
 * territory used different rankings. Fix: this handler now fetches the SAME candidate
 * pool shape query_signals.ts uses, runs it through the SAME applyCompositeRanking
 * pipeline (composite_ranker.ts), and then applies HIERARCHICAL AGGREGATION
 * (buildHierarchicalProfiles) — "one composite Saturn-AV profile row, never twenty
 * atoms" — before shipping entity_profiles as the primary orient surface. The atomic
 * `top_signals` list is retained for backward compatibility, now composite-ranked too.
 *
 * R5.1 C2 item 2 (E-6 completion): entity_profiles aggregates on the GRAHA axis, but
 * the atomic `top_signals` band was still un-aggregated — same-family atoms (same
 * graha × signal_type_id, e.g. `graha_dignity_per_varga:dignity_state` repeated once
 * per varga) could still tie/cluster and flood the top band with near-duplicate rows
 * for one graha, crowding out other distinct findings (the "dignity-row tie-block" a
 * closing probe observed). Fix: `collapseSignalFamilies` (composite_ranker.ts) groups
 * the SAME composite-ranked pool by family and keeps exactly one representative row
 * per family in the top band — the highest-scoring member, score untouched (B.10) —
 * with the rest demoted to `family_member_pointers` (signal_ids), still reachable via
 * query_signals, never deleted from bodha_msr_signals.
 *
 * Used by the consumption layer (Bodha chat) as the primary chart-level
 * context loader for the L2 synthesis surface.
 */

import type { CapabilityDescriptor } from '../../index'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { cacheKey, cacheGet, cacheSet } from '../../../cache'
import { applyCompositeRanking, buildRankingBasis, buildHierarchicalProfiles, collapseSignalFamilies } from '../../../ranking/composite_ranker'
import { fetchL1Context } from '../../../ranking/l1_context_fetcher'
import { PRIORS_VERSION } from '../../../ranking/priors_config'
import { demoteSignatureTiers } from '../../../ranking/salience_demotion'
import { GRAHA_CODE_TO_NAME } from '../../../address_resolver'

/** Max resolvable fact_ids surfaced in the envelope-level grounding block (payload safety). */
const GROUNDING_FACT_IDS_CAP = 200

/**
 * CR-55 fix (Lane 5, §N.6 density retrofit — serving-side): `vw_chart_digest.weakest_graha`
 * is populated by `bo_upaya.py`'s `resonance_score_v1` (an RM/relationship-mechanism ranking,
 * NOT a strength measure) — genuinely the wrong site for "which graha is weakest", and outside
 * this lane's file scope to fix at the writer (bo_upaya.py/bo_samvada.py are Lane-4's/RM's
 * files, not this lane's). Rather than keep serving that mislabeled value under a name that
 * promises strength, this re-derives the honest answer LIVE from the already-computed L1
 * Shadbala total (fact_category='graha_shadbala_total', the classical six-fold strength
 * measure BPHS Ch.27 actually names for exactly this question) — zero new computation, a
 * straight MIN() over an existing per-chart fact set (B.10). Never fails the caller: on any
 * error this falls back to the view's original (mislabeled) value rather than breaking the
 * response.
 */
export async function deriveShadbalaWeakestGraha(
  chart_id: string,
  ayanamsha_id: string,
): Promise<{ graha: string | null; shadbala_rupa: number | null } | null> {
  try {
    const res = await query<{ fact_subject: string; fact_value_num: string | number | null }>(
      `SELECT fact_subject, fact_value_num
       FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_shadbala_total'
         AND fact_value_num IS NOT NULL
         AND fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN')
       ORDER BY fact_value_num ASC
       LIMIT 1`,
      [chart_id, ayanamsha_id],
    )
    const row = res.rows[0]
    if (!row) return null
    const code = String(row.fact_subject ?? '')
    return {
      graha: GRAHA_CODE_TO_NAME[code] ?? code,
      shadbala_rupa: row.fact_value_num != null ? Number(row.fact_value_num) : null,
    }
  } catch {
    return null // honest null — never fabricated; caller keeps the view's original value
  }
}

/**
 * WP-1.2(a) (LCA-14, §N.5) — resolve which of a signal pool's constituent fact_ids
 * actually exist in chart_facts, returning a fact_id → fact_subject map. Bounded: a
 * single chart-scoped `fact_id = ANY(...)` lookup over the DISTINCT constituent ids of
 * the already-fetched candidate pool (never an open scan). The map is BOTH the §N.5
 * resolvability proof (an id is in the map iff it resolves) AND the entity-attribution
 * source (fact_subject carries the graha token, e.g. `D108_SAT`).
 */
async function resolveConstituentFactSubjects(
  chart_id: string,
  rows: Array<{ constituent_facts_array?: string[] | null }>,
): Promise<Map<string, string>> {
  const distinct = Array.from(new Set(
    rows.flatMap(r => r.constituent_facts_array ?? []).filter((v): v is string => typeof v === 'string' && v.length > 0),
  ))
  const map = new Map<string, string>()
  if (distinct.length === 0) return map
  const res = await query<{ fact_id: string; fact_subject: string | null }>(
    `SELECT fact_id, fact_subject FROM chart_facts WHERE chart_id = $1 AND fact_id = ANY($2::text[])`,
    [chart_id, distinct],
  )
  for (const r of res.rows) {
    if (typeof r.fact_id === 'string') map.set(r.fact_id, r.fact_subject ?? '')
  }
  return map
}

// Candidate pool fetched by raw computed_salience before composite re-ranking —
// mirrors query_signals.ts's CANDIDATE_FETCH_SIZE pattern (same ranking pipeline,
// E-6). Smaller than query_signals' 500 because the orient surface aggregates
// down to entity profiles, not a full atomic page.
const CANDIDATE_FETCH_SIZE = 300

/**
 * WP-0.1 / LCA-17 defense-in-depth (F-0893/0902/0905/0908).
 *
 * Extract the chart identity a query_ucd payload stamps into `content.chart_id`.
 * The orientation digest ALWAYS echoes the chart_id it was computed for; a payload
 * whose echoed chart_id does not match the requested chart_id is a cross-chart
 * substitution and must never be served — regardless of how it arose (a cache-key
 * collision, a future caching bug, etc.). Returns undefined when no chart identity
 * can be read (treated as a match-failure by callers, i.e. do not trust it).
 */
export function orientationChartIdOf(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') return undefined
  const content = (payload as Record<string, unknown>).content
  if (!content || typeof content !== 'object') return undefined
  const cid = (content as Record<string, unknown>).chart_id
  return typeof cid === 'string' ? cid : undefined
}

/** True iff the payload's echoed chart identity matches the requested chart_id. */
export function orientationEchoMatches(payload: unknown, chart_id: string): boolean {
  return orientationChartIdOf(payload) === chart_id
}

export const queryUcdCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_ucd',
  type:  'tool',
  layer: 'L2',
  name:  'query_ucd',

  description: [
    'Returns a structured Bodha synthesis digest for a chart (synthesis_query, design §5 #7).',
    'Includes: entity_profiles (hierarchically-aggregated composite-ranked signal groups —',
    'design §E-6, one row per graha rather than N atomic signals), top MSR signals',
    '(atomic, composite-ranked, backward-compat, ALSO family-collapsed — same graha ×',
    'signal_type_id repeats, e.g. per-varga dignity signals, collapse to one composite row',
    'with family_member_pointers to the rest — see provenance.family_aggregation_note),',
    'domain convergence scores, contradiction count, weakest graha priority class,',
    'and quality audit trap1 count.',
    'response_format governs verbosity: digest (counts + entity_profiles only, no atomic',
    'signals), summary (default; entity_profiles + capped atomic top_signals),',
    'full (entity_profiles + uncapped atomic top_signals up to top_k_signals).',
    'Primary context-loader for L2 chart queries.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (canonical_id from asset_registry)',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to filter by (default: 'lahiri_chitrapaksha')",
      required: false,
    },
    top_k_signals: {
      type: 'number',
      description: 'How many top MSR signals to return (default: 20, max: 100)',
      required: false,
    },
    top_k_entities: {
      type: 'number',
      description: 'How many hierarchically-aggregated entity profiles to return (default: 10, max: 30).',
      required: false,
    },
    signal_class: {
      type: 'string',
      description: "Filter signals by class: 'yoga'|'dosha'|'karaka_alignment'|'composite_state'|'sade_sati'|'panchanga'",
      required: false,
    },
    min_salience: {
      type: 'number',
      description: 'Minimum computed_salience threshold (0..1, default: 0)',
      required: false,
    },
    response_format: {
      type: 'string',
      description: "Verbosity: 'digest' (counts + entity_profiles only) | 'summary' (default; + capped top_signals) | 'full' (+ uncapped top_signals).",
      enum: ['digest', 'summary', 'full'],
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  drill_children: [
    'marsys://tool/L2/query_domain_reading',
    'marsys://tool/L2/query_signals',
    'marsys://tool/L2/traverse_chart_graph',
  ],
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: true,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  // Band phase 4 ("Reading the whole chart") — B.11 whole-chart-read (UCN/UCD digest).
  register: { reader_label: 'Reading the whole chart' },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 1,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    // L-6: chart_id null guard
    if (!args.chart_id) {
      return { content: { error: 'chart_id is required for query_ucd' }, is_error: true }
    }
    const chart_id       = String(args.chart_id)
    const ayanamsha_id   = String(args.ayanamsha_id  ?? DEFAULT_AYANAMSHA)

    const response_format = (['digest', 'summary', 'full'].includes(String(args.response_format))
      ? String(args.response_format) : 'summary') as 'digest' | 'summary' | 'full'

    // H-11: cache check
    const _cacheKey = cacheKey('query_ucd', { chart_id, ayanamsha_id,
      top_k_signals: args.top_k_signals, top_k_entities: args.top_k_entities,
      signal_class: args.signal_class, min_salience: args.min_salience,
      response_format, priors_version: PRIORS_VERSION })
    const _cached = cacheGet(_cacheKey)
    // WP-0.1 / LCA-17 defense-in-depth: only serve a cached payload whose echoed
    // chart identity matches the requested chart_id. A mismatch is a cross-chart
    // substitution — never serve it; fall through to a fresh compute. This holds
    // even if a future key-collision reintroduces the substitution the SHA-256
    // cache-key fix already prevents. Isolation strictly stronger, never looser.
    if (_cached !== undefined) {
      if (orientationEchoMatches(_cached, chart_id)) {
        return _cached as ReturnType<typeof this.handler>
      }
      console.error(
        `[query_ucd] LCA-17 GUARD: discarded cached payload for chart ${chart_id} — ` +
        `echoed chart_id was ${String(orientationChartIdOf(_cached))}. Recomputing.`,
      )
    }
    const top_k           = Math.min(Number(args.top_k_signals ?? 20), 100)
    const top_k_entities  = Math.min(Number(args.top_k_entities ?? 10), 30)
    const signal_class    = args.signal_class ? String(args.signal_class) : null
    const min_salience    = Number(args.min_salience ?? 0)

    // ── Digest from vw_chart_digest ─────────────────────────────────────────
    // WP-1.5 type hygiene (F-0963 class): msr_signal_count/yoga_count/dosha_count/
    // contradiction_count are bigint — node-postgres serializes bigint as a JS STRING
    // ("573"), so the digest shipped string counts a consumer cannot arithmetic on. Cast
    // ::int (these are small chart-scoped tallies, never near the int ceiling) so the
    // served counts are real JSON numbers, matching trap1_count (already integer).
    const digestSql = `
      SELECT msr_signal_count::int AS msr_signal_count,
             yoga_count::int AS yoga_count,
             dosha_count::int AS dosha_count,
             avg_salience, max_salience,
             contradiction_count::int AS contradiction_count,
             weakest_graha, top_priority_class,
             top_convergence_domains, trap1_count, digest_at
      FROM vw_chart_digest
      WHERE chart_id = $1 AND ayanamsha_id = $2
    `

    // ── Candidate signal pool from bodha_msr_signals ─────────────────────────
    // R5 W1 (design §E-6): fetch a wide candidate pool by raw computed_salience
    // (coarse), then apply the SAME composite ranking pipeline query_signals.ts
    // uses (applyCompositeRanking) — the orient surface must never rank
    // differently from its own drill surface. Column set matches query_signals.ts's
    // SIGNAL_COLUMNS so the composite ranker's sub-scorers (classPrior needs
    // source_subsystem; topicRelevance/intrinsicStrength/temporalActivation need
    // configuration_jsonb) have what they need.
    const classFilter    = signal_class ? `AND signal_type_class = $5` : ''
    const salienceFilter = min_salience > 0 ? `AND computed_salience >= $6` : ''
    const signalSql = `
      SELECT signal_id, signal_type_id, signal_type_class, signal_tradition,
             signal_summary_text, signal_headline_text,
             computed_salience, top_k_salience_rank, domains_affected_array,
             constituent_facts_array, source_subsystem, valence,
             verification_pass_status, configuration_jsonb, citation_human,
             lel_origin, signature_tier
      FROM bodha_msr_signals
      WHERE chart_id = $1 AND ayanamsha_id = $2
        ${classFilter}
        ${salienceFilter}
      ORDER BY computed_salience DESC NULLS LAST
      LIMIT $3 OFFSET $4
    `

    // ── Top convergence domains ──────────────────────────────────────────────
    const convSql = `
      SELECT domain, convergence_count, convergence_score, cross_tradition_count,
             salience_weighted_sum, contradiction_count
      FROM bodha_convergence
      WHERE chart_id = $1 AND ayanamsha_id = $2 AND snapshot_type = 'static_natal'
      ORDER BY convergence_score DESC NULLS LAST
      LIMIT 7
    `

    try {
      void _ctx

      const signalParams: unknown[] = [chart_id, ayanamsha_id, CANDIDATE_FETCH_SIZE, 0]
      if (signal_class)  signalParams.push(signal_class)
      if (min_salience > 0) signalParams.push(min_salience)

      const as_of_date = new Date().toISOString().split('T')[0]
      const [digestResult, signalResult, convResult, l1Context, shadbalaWeakest] = await Promise.all([
        query(digestSql, [chart_id, ayanamsha_id]),
        query(signalSql, signalParams),
        query(convSql,   [chart_id, ayanamsha_id]),
        fetchL1Context(chart_id, ayanamsha_id, as_of_date),
        deriveShadbalaWeakestGraha(chart_id, ayanamsha_id),
      ])

      const digest = (digestResult.rows[0] ?? {}) as Record<string, unknown>
      // CR-55 (Lane 5): prefer the live Shadbala-derived weakest graha over the view's
      // resonance_score_v1-sourced value. `weakest_graha_source` discloses which computation
      // won so a caller comparing against the RM/resonance framing isn't misled (never a
      // silent swap — B.10/CR-42 discipline).
      const viewWeakestGraha = digest.weakest_graha as string | null | undefined
      const weakest_graha = shadbalaWeakest?.graha ?? viewWeakestGraha ?? null
      const weakest_graha_source = shadbalaWeakest?.graha
        ? 'shadbala_total_min (BPHS Ch.27 six-fold strength; CR-55 fix)'
        : (viewWeakestGraha ? 'vw_chart_digest.weakest_graha (resonance_score_v1 — RM ranking, not a strength measure; shadbala derivation unavailable for this call)' : null)

      // E-6: composite-rank the candidate pool (domain=null — orientation is
      // domain-agnostic; topicRelevance/vargaWeight fall back to their D1/neutral
      // baselines) then hierarchically aggregate into entity profiles.
      const rawRows = signalResult.rows as unknown as Parameters<typeof applyCompositeRanking>[0]
      const scoredAll = applyCompositeRanking(rawRows, l1Context, null)

      // WP-1.2(a) (LCA-14, §N.5): resolve the candidate pool's constituent fact_ids to
      // chart_facts (fact_id → fact_subject). This both proves resolvability (only ids in
      // the map are surfaced as grounding) and supplies fact_subject-based entity
      // attribution so the per-varga dignity flood is attributed to its real graha rather
      // than a giant UNATTRIBUTED bucket.
      const factSubjectByFactId = await resolveConstituentFactSubjects(chart_id, signalResult.rows as Array<{ constituent_facts_array?: string[] | null }>)

      // WP-1.2β: exclude the residual UNATTRIBUTED bucket from the served profiles (0%
      // UNATTRIBUTED, ND-W1.2) — the residual is disclosed below in `attribution`.
      const entity_profiles = buildHierarchicalProfiles(scoredAll, top_k_entities, 3, { factSubjectByFactId, excludeUnattributed: true })
      const ranking_basis = buildRankingBasis(scoredAll, null)

      // WP-1.2β (LCA-14): attribution honesty (E-2). Across the FULL scored candidate pool,
      // count how many signals still land in the residual UNATTRIBUTED bucket after the
      // graha + sade_sati + bhāva attribution chain, and confirm 0 UNATTRIBUTED entities are
      // SERVED in the top-K entity_profiles. Disclosed, never silently dropped (B.10).
      const servedUnattributed = entity_profiles.filter(p => p.entity_type === 'unattributed').length
      const { deriveSignalEntity } = await import('../../../ranking/composite_ranker')
      let poolUnattributed = 0
      for (const s of scoredAll) {
        if (deriveSignalEntity(s, factSubjectByFactId) === 'UNATTRIBUTED') poolUnattributed++
      }
      const attribution = {
        served_unattributed_entities: servedUnattributed,
        served_unattributed_share: entity_profiles.length > 0 ? servedUnattributed / entity_profiles.length : 0,
        candidate_pool_size: scoredAll.length,
        candidate_pool_unattributed: poolUnattributed,
        note: servedUnattributed === 0
          ? 'WP-1.2β: 0% UNATTRIBUTED on the served ranked surface — every served entity_profile ' +
            'resolves to a graha or a bhāva (chart address). candidate_pool_unattributed genuinely ' +
            'un-attributable signals (typically panchāṅga/muhūrta birth-moment descriptors carrying ' +
            'neither a graha nor a bhāva) are EXCLUDED from the served profiles and disclosed here ' +
            '(not silently dropped — B.10); drill them via query_signals if needed.'
          : `WP-1.2β: ${servedUnattributed} UNATTRIBUTED entity(ies) surfaced — attribution gap to disclose, not hide.`,
      }

      // response_format bounding (E-5 — this facet is now actually load-bearing;
      // previously declared by callers but unimplemented server-side):
      //   digest  → entity_profiles + counts only, no atomic signal rows
      //   summary → entity_profiles + capped atomic top_signals (top_k, max 100)
      //   full    → entity_profiles + full atomic top_signals (top_k, max 100)
      // (both summary/full share the same top_k cap today — 'full' exists as the
      // explicit non-default choice that keeps the door open for a higher ceiling
      // without a breaking change later.)
      //
      // R5.1 C2 item 2 (E-6 completion): collapse same-family atomic signals
      // (same graha × signal_type_id — e.g. graha_dignity_per_varga repeated once
      // per varga) into ONE composite row BEFORE slicing to top_k. This is what
      // fixes the dignity-row tie-blocks that used to flood the top band with
      // near-duplicate atoms for a single graha — family members are demoted to
      // `family_member_pointers` (still resolvable via query_signals), never
      // deleted from bodha_msr_signals.
      const familyCollapsed = collapseSignalFamilies(scoredAll)
      // WP-1.2(d): serve-time salience demotion — descriptive/per-varga rows may not carry
      // major/chart_defining tiers on the wire (LCA-9b-2 serving cap).
      const atomicSignals = response_format === 'digest'
        ? []
        : demoteSignatureTiers(familyCollapsed.slice(0, top_k).map(s => {
            const { _subscores, ...rest } = s
            void _subscores
            return rest as Record<string, unknown>
          }))
      const familiesCollapsedCount = familyCollapsed.filter(s => s.is_family_composite).length

      // WP-1.2(a) (LCA-14, §N.5): envelope-level grounding — the union of RESOLVABLE
      // constituent fact_ids across the entity profiles (each already filtered to ids that
      // provably exist in chart_facts). Every id here resolves; UNATTRIBUTED is no longer
      // the top entity_profile because attribution now drains it (see buildHierarchicalProfiles).
      const groundingFactIds: string[] = []
      const seenFactId = new Set<string>()
      for (const p of entity_profiles) {
        for (const fid of p.fact_ids) {
          if (seenFactId.has(fid)) continue
          seenFactId.add(fid)
          groundingFactIds.push(fid)
          if (groundingFactIds.length >= GROUNDING_FACT_IDS_CAP) break
        }
        if (groundingFactIds.length >= GROUNDING_FACT_IDS_CAP) break
      }
      const grounding = {
        fact_ids: groundingFactIds,
        resolvable: true as const,
        resolved_fact_count: factSubjectByFactId.size,
        note: 'WP-1.2(a): fact_ids are the resolvable L1 chart_facts.fact_id set backing the ' +
          'ranked entity_profiles (each id verified present in chart_facts, §N.5). Per-entity ' +
          'fact_ids live on entity_profiles[].fact_ids; per-signal on top_signals[].constituent_facts_array.',
      }

      const result = {
        content: {
          chart_id,
          ayanamsha_id,
          response_format,
          digest: {
            msr_signal_count:     digest.msr_signal_count,
            yoga_count:           digest.yoga_count,
            dosha_count:          digest.dosha_count,
            avg_salience:         digest.avg_salience,
            max_salience:         digest.max_salience,
            contradiction_count:  digest.contradiction_count,
            weakest_graha,
            weakest_graha_source,
            top_priority_class:   digest.top_priority_class,
            trap1_count:          digest.trap1_count,
          },
          entity_profiles,
          top_signals:           atomicSignals,
          convergence_domains:   convResult.rows,
          grounding,
          attribution,
          ranking_basis,
          filters: { top_k, top_k_entities, signal_class, min_salience },
          provenance: {
            tables: ['vw_chart_digest', 'bodha_msr_signals', 'bodha_convergence'],
            ranking_note: `E-6: entity_profiles + top_signals both composite-ranked ` +
              `(priors_version=${PRIORS_VERSION}) — same pipeline as query_signals.ts, not a ` +
              `separate stored-band or raw-salience order.`,
            aggregation_note: `Hierarchical aggregation: ${scoredAll.length} atomic candidate ` +
              `signals → ${entity_profiles.length} entity profile(s) (design §E-6).`,
            family_aggregation_note: `E-6 completion (R5.1 C2 item 2): ${scoredAll.length} atomic ` +
              `candidates → ${familyCollapsed.length} family-collapsed row(s) before the top_k=${top_k} ` +
              `cut; ${familiesCollapsedCount} of those are composite rows representing >1 same-family ` +
              `atom (same graha × signal_type_id, e.g. a per-varga dignity construct). Collapsed atoms ` +
              `are demoted to family_member_pointers on the representative row, not deleted — drill via ` +
              `query_signals with the same signal_type_id/graha to reach them.`,
          },
        },
        is_error: false as const,
      }
      // WP-0.1 / LCA-17 defense-in-depth: never cache or serve a freshly-computed
      // payload whose echoed chart identity does not match the requested chart_id.
      // (By construction it does — content.chart_id is set to chart_id above — this
      // is a hard invariant guard, not an expected branch.)
      if (!orientationEchoMatches(result, chart_id)) {
        return {
          content: { error: 'LCA-17 chart-identity invariant violated in query_ucd', chart_id, ayanamsha_id },
          is_error: true as const,
        }
      }
      cacheSet(_cacheKey, result)
      return result
    } catch (err) {
      return {
        content: { error: String(err), chart_id, ayanamsha_id },
        is_error: true,
      }
    }
  },
}
