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
 * Used by the consumption layer (Bodha chat) as the primary chart-level
 * context loader for the L2 synthesis surface.
 */

import type { CapabilityDescriptor } from '../../index'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { cacheKey, cacheGet, cacheSet } from '../../../cache'
import { applyCompositeRanking, buildRankingBasis, buildHierarchicalProfiles } from '../../../ranking/composite_ranker'
import { fetchL1Context } from '../../../ranking/l1_context_fetcher'
import { PRIORS_VERSION } from '../../../ranking/priors_config'

// Candidate pool fetched by raw computed_salience before composite re-ranking —
// mirrors query_signals.ts's CANDIDATE_FETCH_SIZE pattern (same ranking pipeline,
// E-6). Smaller than query_signals' 500 because the orient surface aggregates
// down to entity profiles, not a full atomic page.
const CANDIDATE_FETCH_SIZE = 300

export const queryUcdCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_ucd',
  type:  'tool',
  layer: 'L2',
  name:  'query_ucd',

  description: [
    'Returns a structured Bodha synthesis digest for a chart (synthesis_query, design §5 #7).',
    'Includes: entity_profiles (hierarchically-aggregated composite-ranked signal groups —',
    'design §E-6, one row per graha rather than N atomic signals), top MSR signals',
    '(atomic, composite-ranked, backward-compat), domain convergence scores,',
    'contradiction count, weakest graha priority class, and quality audit trap1 count.',
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
    if (_cached !== undefined) return _cached as ReturnType<typeof this.handler>
    const top_k           = Math.min(Number(args.top_k_signals ?? 20), 100)
    const top_k_entities  = Math.min(Number(args.top_k_entities ?? 10), 30)
    const signal_class    = args.signal_class ? String(args.signal_class) : null
    const min_salience    = Number(args.min_salience ?? 0)

    // ── Digest from vw_chart_digest ─────────────────────────────────────────
    const digestSql = `
      SELECT msr_signal_count, yoga_count, dosha_count,
             avg_salience, max_salience, contradiction_count,
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
      const [digestResult, signalResult, convResult, l1Context] = await Promise.all([
        query(digestSql, [chart_id, ayanamsha_id]),
        query(signalSql, signalParams),
        query(convSql,   [chart_id, ayanamsha_id]),
        fetchL1Context(chart_id, ayanamsha_id, as_of_date),
      ])

      const digest = (digestResult.rows[0] ?? {}) as Record<string, unknown>

      // E-6: composite-rank the candidate pool (domain=null — orientation is
      // domain-agnostic; topicRelevance/vargaWeight fall back to their D1/neutral
      // baselines) then hierarchically aggregate into entity profiles.
      const rawRows = signalResult.rows as unknown as Parameters<typeof applyCompositeRanking>[0]
      const scoredAll = applyCompositeRanking(rawRows, l1Context, null)
      const entity_profiles = buildHierarchicalProfiles(scoredAll, top_k_entities, 3)
      const ranking_basis = buildRankingBasis(scoredAll, null)

      // response_format bounding (E-5 — this facet is now actually load-bearing;
      // previously declared by callers but unimplemented server-side):
      //   digest  → entity_profiles + counts only, no atomic signal rows
      //   summary → entity_profiles + capped atomic top_signals (top_k, max 100)
      //   full    → entity_profiles + full atomic top_signals (top_k, max 100)
      // (both summary/full share the same top_k cap today — 'full' exists as the
      // explicit non-default choice that keeps the door open for a higher ceiling
      // without a breaking change later.)
      const atomicSignals = response_format === 'digest'
        ? []
        : scoredAll.slice(0, top_k).map(s => {
            const { _subscores, ...rest } = s
            void _subscores
            return rest as Record<string, unknown>
          })

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
            weakest_graha:        digest.weakest_graha,
            top_priority_class:   digest.top_priority_class,
            trap1_count:          digest.trap1_count,
          },
          entity_profiles,
          top_signals:           atomicSignals,
          convergence_domains:   convResult.rows,
          ranking_basis,
          filters: { top_k, top_k_entities, signal_class, min_salience },
          provenance: {
            tables: ['vw_chart_digest', 'bodha_msr_signals', 'bodha_convergence'],
            ranking_note: `E-6: entity_profiles + top_signals both composite-ranked ` +
              `(priors_version=${PRIORS_VERSION}) — same pipeline as query_signals.ts, not a ` +
              `separate stored-band or raw-salience order.`,
            aggregation_note: `Hierarchical aggregation: ${scoredAll.length} atomic candidate ` +
              `signals → ${entity_profiles.length} entity profile(s) (design §E-6).`,
          },
        },
        is_error: false as const,
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
