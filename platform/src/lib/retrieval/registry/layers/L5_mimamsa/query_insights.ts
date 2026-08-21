/**
 * query_insights — Insight Surface Query (L5 Mīmāṃsā)
 * =====================================================
 * Reads mimamsa_insight_units + overlays for a chart.
 * Returns ranked, retrievable insight units with provenance chains:
 *   - Calibrated-outlook insights (prediction → event match scores)
 *   - Manifestation-grammar insights (channel propensity learnings)
 *   - Emergent-law discoveries (pattern candidates from mining)
 *   - Load-bearing conclusion map
 *   - Negative-knowledge statements
 *
 * Primary context-loader for L5 calibrated reading surface.
 */

import type { CapabilityDescriptor } from '../../index'
import { query } from '@/lib/db/client'

export const EMPIRICALLY_CALIBRATED = 'empirical'

// GA-5 review finding on #1386 (rounds 2-3): mi_darshana.py embeds a suppressed numeric
// value in `statement` across (at least) FIVE distinct templates, not just one --
// verdict_object: "(grade N.N/10)"; load_bearing: "(sensitivity=N.NN)"; calibrated_outlook:
// "observed outcome rate is N.N%"; manifestation_grammar's non-empirical branch:
// "(prior-based estimate: N%)" (line 179 -- found round 3, LATENT on the canonical chart
// today since its 7 rows are all currently evidence_grade=empirical, but the branch is
// reachable and will fire on other charts). Redacting by SHAPE (not by re-deriving the
// row's own value, which risks drifting from how mi_darshana actually formats it) catches
// every known citation shape regardless of which template produced it. `g` flag added --
// a statement could in principle carry more than one citation.
//
// STRUCTURAL RESIDUAL, NOT fully closed by this list (disclosed, not fixed -- round 3
// finding): emergent_law statements are free text copied from mimamsa_discoveries, an
// unbounded shape no fixed regex list can be proven exhaustive against. Closing that
// durably needs either a write-path fix (mi_darshana.py never embeds a numeric confidence
// citation in free-text discoveries) or a serve-time numeric-residue assertion (fail loud
// if ANY bare confidence-shaped number survives a suppressed row's statement) -- both
// larger changes than this fix's own scope. Tracked, not chased into a round 4.
//
// F-143 UPDATE: that residual stopped being latent. Before F-143, discovery rows with
// n_support >= 5 were graded 'empirical' and so never reached this suppressor at all; the
// fix demotes them (20 rows on the canonical chart) to 'assignment_only', which routes
// their statements through here for the first time. The two shapes mi_pariksha's discovery
// substep actually emits are now covered explicitly -- the current "mean credit=N.NN" form
// and the pre-v2.1 "(mean=N.NN, n=N)" form, which stays in prod rows until mi_pariksha
// re-runs. The unbounded-free-text residual above is unchanged in principle.
const EMBEDDED_NUMERIC_EVIDENCE_PATTERNS: Array<{ pattern: RegExp; replacement: string }> = [
  { pattern: /\(grade\s+[\d.]+\/10\)/gi, replacement: '(grade suppressed — see tier_suppression_note)' },
  { pattern: /\(sensitivity=[\d.]+\)/gi, replacement: '(sensitivity suppressed — see tier_suppression_note)' },
  { pattern: /observed outcome rate is [\d.]+%/gi, replacement: 'observed outcome rate is [suppressed — see tier_suppression_note]' },
  { pattern: /\(prior-based estimate: [\d.]+%\)/gi, replacement: '(prior-based estimate suppressed — see tier_suppression_note)' },
  { pattern: /mean credit=[\d.]+/gi, replacement: 'mean credit=[suppressed — see tier_suppression_note]' },
  { pattern: /\(mean=[\d.]+,\s*n=\d+\)/gi, replacement: '(mean credit suppressed — see tier_suppression_note)' },
]

// F-143: evidence_grade is a TIERED vocabulary, not a boolean. Served verbatim per row and
// counted in evidence_grade_counts; this legend keeps a caller from collapsing the tiers
// into "empirical vs. not" and reading an assignment count as scored evidence.
export const EVIDENCE_GRADE_LEGEND: Record<string, string> = {
  empirical:
    'backed by >= 5 outcome-adjudicated prediction/event matches (CONFIRMED|PARTIAL|REFUTED). ' +
    'The only tier whose numeric fields are served unsuppressed.',
  assignment_only:
    'enough ASSIGNMENTS (attribution rows / channel opportunities) to look well-supported, but ' +
    'fewer than 5 of them were outcome-adjudicated. Not evidence of accuracy. Numerics suppressed.',
  prior_only:
    'below every evidence threshold, or no scored count is recorded at all — the number shown ' +
    'would come from a prior, not from this chart. Numerics suppressed.',
  structural:
    'deterministically derived from chart structure or from an unadjudicated probe ' +
    '(e.g. retrodiction rows: an anchor match is not a scored hit). Numerics suppressed.',
}

export function redactEmbeddedNumericEvidence(statement: string): string {
  let out = statement
  for (const { pattern, replacement } of EMBEDDED_NUMERIC_EVIDENCE_PATTERNS) {
    out = out.replace(pattern, replacement)
  }
  return out
}

export function suppressIfNotCalibrated(row: Record<string, unknown>): Record<string, unknown> {
  if (row['evidence_grade'] === EMPIRICALLY_CALIBRATED) return row
  // P3-b tier-suppression (F-69): evidence_grade is anything other than 'empirical' (structural,
  // prior_only, missing) → no empirically-calibrated score exists for this insight. Mirrors
  // ka_kshetra/stage8_spec.py:136. The stored mimamsa_insight_units row is never mutated.
  const pc = row['provenance_chain'] as Record<string, unknown> | null
  const rawStatement = row['statement']
  const statement = typeof rawStatement === 'string'
    ? redactEmbeddedNumericEvidence(rawStatement)
    : rawStatement
  // GA-5 review finding on #1386 round 3 (2nd finding, same round): mi_darshana.py writes
  // the SAME suppressed float into more than one provenance_chain key depending on
  // insight_type -- manifestation_grammar duplicates it as both provenance_chain.grade AND
  // provenance_chain.propensity (mi_darshana.py's json.dumps({'channel':.., 'domain':.., 
  // 'propensity': prop})). Nulling only .grade left .propensity serving the exact number
  // .grade was just nulled for -- confirmed live: all 10 manifestation_grammar rows on the
  // canonical chart currently carry this key (latent today, all currently empirical). Null
  // BOTH known duplicate keys explicitly -- not a blanket "null every number in
  // provenance_chain", which would incorrectly strip unrelated numeric fields other insight
  // types legitimately carry (e.g. verdict_object's ranked_evidence[].salience, an evidence-
  // weighting score, not a suppressed confidence value).
  const suppressedProvenanceChain = pc == null ? pc : { ...pc, grade: null, propensity: null }
  return {
    ...row,
    statement,
    rank_consequence: null,
    confidence_band: null,
    provenance_chain: suppressedProvenanceChain,
    tier_suppression_note: `rank_consequence/confidence_band/provenance_chain.grade+propensity/statement's embedded numeric evidence (grade/sensitivity/outcome-rate/prior-estimate citations) suppressed at serve time: evidence_grade=${JSON.stringify(row['evidence_grade'])} — no empirically-calibrated score exists for this insight yet (P3-b tier-suppression; see services/ka_kshetra/stage8_spec.py for the precedent this mirrors). The stored value is unaffected.`,
  }
}

export const queryInsightsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_insights',
  type:  'tool',
  layer: 'L5',
  name:  'query_insights',

  description: [
    'Returns ranked L5 Mīmāṃsā insight units for a chart.',
    'Includes calibrated outlooks, manifestation-grammar learnings,',
    'emergent-law discoveries, load-bearing conclusions, and negative knowledge.',
    'All units carry provenance chains back to L1 chart_facts.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID',
      required: true,
    },
    insight_type: {
      type: 'string',
      description: "Filter by type: 'calibrated_outlook'|'manifestation_grammar'|'emergent_law'|'retrodiction'|'load_bearing'|'negative_knowledge'|'verdict_object'. ('retrodiction' and 'verdict_object' rows are written by mi_darshana and were previously undocumented here — insight_type mirrors mimamsa_discoveries.discovery_class for discovery-sourced rows.)",
      required: false,
    },
    domain: {
      type: 'string',
      description: 'Filter by life domain (career, health, relationship, etc.)',
      required: false,
    },
    min_rank: {
      type: 'number',
      description: 'Minimum rank_consequence threshold (0..1, default: 0)',
      required: false,
    },
    top_k: {
      type: 'number',
      description: 'Max insight units to return (default: 30, max: 200)',
      required: false,
    },
    include_negative_knowledge: {
      type: 'boolean',
      description: 'Include is_negative_knowledge=true rows (default: true)',
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: true,

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 2,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id    = String(args.chart_id)
    const insight_type = args.insight_type ? String(args.insight_type) : null
    const domain      = args.domain ? String(args.domain) : null
    const min_rank    = Number(args.min_rank ?? 0)
    const top_k       = Math.min(Number(args.top_k ?? 30), 200)
    const include_neg = args.include_negative_knowledge !== false

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2

    if (insight_type) { filters.push(`insight_type = $${p++}`); params.push(insight_type) }
    if (domain)        { filters.push(`domain = $${p++}`);       params.push(domain) }
    if (min_rank > 0)  { filters.push(`rank_consequence >= $${p++}`); params.push(min_rank) }
    if (!include_neg)  { filters.push(`is_negative_knowledge = false`) }

    params.push(top_k)

    const sql = `
      SELECT insight_id, insight_type, domain, horizon, question_lens,
             statement, rank_consequence, confidence_band, n_support,
             leakage_status, evidence_grade, freshness_lel_version,
             last_calibrated_at, provenance_chain, is_negative_knowledge,
             surface_formula_version, updated_at
      FROM mimamsa_insight_units
      WHERE ${filters.join(' AND ')}
      ORDER BY rank_consequence DESC NULLS LAST
      LIMIT $${p}
    `

    // Calibration summary
    const calSql = `
      SELECT
        COUNT(*)::int                                              AS total_matches,
        COUNT(*) FILTER (WHERE composite_verdict = 'CONFIRMED')   AS confirmed,
        COUNT(*) FILTER (WHERE composite_verdict = 'PARTIAL')     AS partial,
        COUNT(*) FILTER (WHERE composite_verdict = 'REFUTED')     AS refuted,
        COUNT(*) FILTER (WHERE composite_verdict = 'UNRESOLVED')  AS unresolved,
        AVG(composite_score)::numeric(4,3)                        AS mean_composite_score
      FROM mimamsa_calibration
      WHERE chart_id = $1
    `

    try {
      const [insightResult, calResult] = await Promise.all([
        query(sql, params),
        query(calSql, [chart_id]),
      ])

      const calibration_summary = (calResult.rows[0] ?? {}) as Record<string, unknown>

      const evidence_grade_counts: Record<string, number> = {}
      for (const row of insightResult.rows as Array<Record<string, unknown>>) {
        const g = String(row.evidence_grade ?? 'unknown')
        evidence_grade_counts[g] = (evidence_grade_counts[g] ?? 0) + 1
      }

      // F-143: only legend entries for grades actually present, so the legend can never
      // imply a tier this response does not contain.
      const evidence_grade_legend: Record<string, string> = {}
      for (const g of Object.keys(evidence_grade_counts)) {
        evidence_grade_legend[g] = EVIDENCE_GRADE_LEGEND[g] ?? 'unrecognized tier — treated as not-calibrated (fail-closed: numerics suppressed).'
      }

      return {
        content: {
          chart_id,
          insight_units:       insightResult.rows.map(suppressIfNotCalibrated),
          calibration_summary,
          evidence_grade_counts,
          evidence_grade_legend,
          filters:             { insight_type, domain, min_rank, top_k, include_neg },
          total_returned:      insightResult.rows.length,
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}
