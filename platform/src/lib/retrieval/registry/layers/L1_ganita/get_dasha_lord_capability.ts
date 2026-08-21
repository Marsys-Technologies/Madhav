/**
 * get_dasha_lord_capability — B8 derived view: per Mahādaśā-lord serving capability
 * =====================================================================================
 * Doctrine Campaign D-1.5b, Lane B-7 ("Governance + derived view").
 *
 * For every Vimśottarī Mahādaśā (MD) lord on a chart, joins already-computed rows across
 * THREE existing L1/L1-sibling assets — never re-deriving any of them (§N.5: L1 is the
 * authority; this file only aggregates):
 *   - chart_dashas   (ga_dashas)   — which grahas actually carry an MD period on this chart
 *   - chart_facts    (ga_strength) — graha_shadbala_total.rupa, for a percentile rank
 *   - chart_vichara  (ga_vichara)  — house_class (valence_pass.value_jsonb.actor_primary_class,
 *     reusing classify_actor()'s classification — see ga_vichara_writer.py:287),
 *     functional_lordship (value_jsonb.stored_functional_class_bphs, the stored
 *     graha_functional_class_per_ascendant fact ga_vichara cross-checks against), and
 *     ratification_factor (varga_ratification rows — ga_vichara_writer.py's design §11
 *     term, averaged across every domain this lord is karaka for; NULL, honestly, for a
 *     lord that is not a stored karaka for any domain — B.10, never fabricated).
 *
 * IMPLEMENTATION CHOICE (brief's stated alternative, no migration): this is a COMPUTED
 * SERVING-LAYER AGGREGATION, not a SQL VIEW/materialized view. The established MV pattern
 * in this codebase (`mv_chart_bhava_bala_summary`, `platform/migrations/_archive/138_mvs.sql`
 * — a per-chart pivot of chart_facts via MAX(CASE WHEN...) GROUP BY) is mirrored here at the
 * application layer instead of a new DB object, because (a) authoring a migration is
 * explicitly conductor-owned for this wave (CONDUCTOR_PROTOCOL.md §1 Migration guard;
 * BRIEF_D1_5B.md Lane B-7 may_touch note) and (b) the join is cheap and fully expressible as
 * three bounded, indexed queries + an in-process merge — no aggregate needs to survive a
 * chart rebuild independent of a request. If per-chart query volume later justifies caching
 * this as a real materialized view, that is a follow-up migration request, not introduced here.
 *
 * warning_tier (NEW, this lane — not previously stored anywhere): a DETERMINISTIC,
 * zero-new-computation composite of the three joined signals above, in the same spirit as
 * judgment_query's composite_score (register_d9_judgment.ts) — never an LLM judgment, never
 * a probability (L4/L5's domain). See WARNING_TIER_WEIGHTS below for the exact formula.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import type { JudgmentFlagEntry } from '../../../envelope'
import { judgmentFlag } from '../../../envelope'
import { grahaCodeOf } from '@/lib/retrieval/address_resolver'

// ── graha display-name <-> chart_facts/chart_vichara subject-code map ──────────────────
// Values sourced from the graha SSoT (address_resolver.grahaCodeOf) rather than
// hardcoded literals — ADHIṢṬHĀNA Lane A2. Kept as a local Record (not a bare
// grahaCodeOf() call at the read site below) because grahaCodeOf() THROWS on an
// unrecognized name (B.10 — no silent fallback) while this call site's existing
// contract is a graceful skip-with-judgment-flag for an unmapped lord_graha; the
// 9 literal keys here are well-formed graha names so grahaCodeOf() never throws
// building this table.
const GRAHA_TO_SUBJECT: Record<string, string> = Object.fromEntries(
  ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    .map(name => [name, grahaCodeOf(name)]),
)

interface DashaLordRow {
  lord: string
  lord_subject: string
  house_class: string | null
  functional_lordship: string | null
  shadbala_rupa: number | null
  shadbala_percentile: number | null
  ratification_factor: number | null
  ratification_domains: string[]
  warning_tier: 'none' | 'watch' | 'elevated' | 'high'
  warning_score: number
  warning_reasons: string[]
  fact_ids: string[]
}

// House classes ga_vichara_writer.py's classify_actor() can return (DUSTHANA_HOUSES/
// MARAKA_HOUSES membership) that this view treats as warning-worthy. Kept as a named
// constant (not a magic string list) so the formula's provenance is auditable the same
// way judgment_query's DIGNITY_WEIGHT / YOGA_MATCH_WEIGHT are.
const WARNING_HOUSE_CLASSES = new Set(['dusthana_lord', 'maraka'])
const WARNING_TIER_WEIGHTS = {
  house_class: 1,        // house_class in WARNING_HOUSE_CLASSES
  low_shadbala: 1,        // shadbala_percentile < LOW_SHADBALA_PERCENTILE
  low_ratification: 1,    // ratification_factor present and < 1.0 (design §11 clamp midpoint)
  functional_malefic: 1,  // functional_lordship contains 'malefic' (BPHS temporal/natural malefic)
}
// Exported (F-113): significator_condition.ts reuses this EXACT threshold + the
// PERCENT_RANK-over-9-grahas percentile below it, so the assess_* significator surface and
// this B8 view can never disagree about which graha counts as strength-extreme on a chart.
export const LOW_SHADBALA_PERCENTILE = 0.34

function computeWarningTier(row: {
  house_class: string | null
  functional_lordship: string | null
  shadbala_percentile: number | null
  ratification_factor: number | null
}): { tier: DashaLordRow['warning_tier']; score: number; reasons: string[] } {
  let score = 0
  const reasons: string[] = []

  if (row.house_class && WARNING_HOUSE_CLASSES.has(row.house_class)) {
    score += WARNING_TIER_WEIGHTS.house_class
    reasons.push(`house_class=${row.house_class}`)
  }
  if (row.shadbala_percentile !== null && row.shadbala_percentile < LOW_SHADBALA_PERCENTILE) {
    score += WARNING_TIER_WEIGHTS.low_shadbala
    reasons.push(`shadbala_percentile=${row.shadbala_percentile.toFixed(2)} (< ${LOW_SHADBALA_PERCENTILE})`)
  }
  if (row.ratification_factor !== null && row.ratification_factor < 1.0) {
    score += WARNING_TIER_WEIGHTS.low_ratification
    reasons.push(`ratification_factor=${row.ratification_factor} (< 1.0)`)
  }
  if (row.functional_lordship && /malefic/i.test(row.functional_lordship)) {
    score += WARNING_TIER_WEIGHTS.functional_malefic
    reasons.push(`functional_lordship=${row.functional_lordship}`)
  }

  const tier: DashaLordRow['warning_tier'] =
    score >= 3 ? 'high' : score === 2 ? 'elevated' : score === 1 ? 'watch' : 'none'
  return { tier, score, reasons }
}

export const getDashaLordCapabilityCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_dasha_lord_capability',
  type: 'tool',
  layer: 'L1',
  name: 'get_dasha_lord_capability',

  description: [
    'B8 derived view: per Vimśottarī Mahādaśā (MD) lord on this chart, serves',
    '{lord, house_class (kendra/trikona/dusthana/maraka/upachaya — reusing ga_vichara\'s',
    'classify_actor classification), shadbala_percentile (rank among the 9 grahas by',
    'graha_shadbala_total.rupa), functional_lordship (stored graha_functional_class_per_ascendant),',
    'ratification_factor (ga_vichara varga_ratification, averaged across every domain this lord',
    'is a stored karaka for — null, honestly, when the lord is karaka for no domain), and',
    'warning_tier (none/watch/elevated/high — a deterministic, zero-new-computation composite',
    'of the above four signals; see get_dasha_lord_capability.ts WARNING_TIER_WEIGHTS for the',
    'exact formula and citations). Computed serving-layer aggregation over chart_dashas +',
    'chart_facts + chart_vichara — no new astronomical computation (B.10); every value traces',
    'to an existing L1/L1-sibling fact via fact_id_refs.',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'lahiri_chitrapaksha')." },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Daśā structure' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  // CLAUDE.md §N.6 (Serving Density Principle): every row here is a CONFIRMED, already-
  // computed value (never a catalog/requires_pass label) — there is no catalog-vs-confirmed
  // split on this surface, so density_contract declares paginated:false (at most 9 MD lords)
  // and empty_reason:true (an honestly-empty chart_dashas/chart_vichara join is flagged, not
  // silently returned as `[]`).
  density_contract: {
    paginated: false,
    facets: ['ayanamsha_id'],
    empty_reason: true,
  },

  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      if (!chartId) return { content: { error: 'chart_id is required' }, is_error: true }
      const ayanamshaId = (args.ayanamsha_id as string | undefined) ?? 'lahiri_chitrapaksha'

      const [dashaLordsRes, shadbalaRes, vicharaRes, ratificationRes] = await Promise.all([
        // ── chart_dashas (ga_dashas): every graha that carries a Vimśottarī MD on this chart ──
        query<{ lord_graha: string }>(
          `SELECT DISTINCT lord_graha FROM chart_dashas
           WHERE chart_id = $1 AND ayanamsha_id = $2 AND system_id = 'vimshottari' AND level_n = 1`,
          [chartId, ayanamshaId],
        ),
        // ── chart_facts (ga_strength): graha_shadbala_total.rupa + percentile among the 9 grahas ──
        query<{ fact_id: string; fact_subject: string; rupa: number; percentile: number }>(
          `SELECT fact_id, fact_subject, fact_value_num AS rupa,
                  PERCENT_RANK() OVER (ORDER BY fact_value_num) AS percentile
           FROM chart_facts
           WHERE chart_id = $1 AND ayanamsha_id = $2
             AND fact_category = 'graha_shadbala_total' AND fact_key = 'rupa'`,
          [chartId, ayanamshaId],
        ),
        // ── chart_vichara (ga_vichara): house_class + functional_lordship, D1 valence_pass rows ──
        query<{ subject: string; house_class: string | null; functional_lordship: string | null; fact_ids: string[] }>(
          `SELECT subject,
                  (array_agg(value_jsonb->>'actor_primary_class') FILTER (WHERE value_jsonb->>'actor_primary_class' IS NOT NULL))[1] AS house_class,
                  (array_agg(value_jsonb->>'stored_functional_class_bphs') FILTER (WHERE value_jsonb->>'stored_functional_class_bphs' IS NOT NULL))[1] AS functional_lordship,
                  (array_agg(DISTINCT cf) FILTER (WHERE cf IS NOT NULL)) AS fact_ids
           FROM chart_vichara, LATERAL unnest(constituent_fact_ids) AS cf
           WHERE chart_id = $1 AND ayanamsha_id = $2 AND varga = 'D1' AND vichara_family = 'valence_pass'
           GROUP BY subject`,
          [chartId, ayanamshaId],
        ),
        // ── chart_vichara (ga_vichara): ratification_factor, averaged across every domain ──
        query<{ subject: string; avg_ratification: number; domains: string[] }>(
          `SELECT subject, AVG(ratification_factor) AS avg_ratification, array_agg(DISTINCT domain) AS domains
           FROM chart_vichara
           WHERE chart_id = $1 AND ayanamsha_id = $2 AND vichara_family = 'varga_ratification'
             AND ratification_factor IS NOT NULL
           GROUP BY subject`,
          [chartId, ayanamshaId],
        ),
      ])

      const shadbalaBySubject = new Map(shadbalaRes.rows.map(r => [r.fact_subject, r]))
      const vicharaBySubject = new Map(vicharaRes.rows.map(r => [r.subject, r]))
      const ratificationBySubject = new Map(ratificationRes.rows.map(r => [r.subject, r]))

      const rows: DashaLordRow[] = []
      const judgment_flags: JudgmentFlagEntry[] = []

      for (const { lord_graha } of dashaLordsRes.rows) {
        const subject = GRAHA_TO_SUBJECT[lord_graha]
        if (!subject) {
          judgment_flags.push(judgmentFlag('unmapped_lord_graha', `'${lord_graha}' has no known subject-code mapping — row skipped, not fabricated.`))
          continue
        }
        const sb = shadbalaBySubject.get(subject)
        const vc = vicharaBySubject.get(subject)
        const rf = ratificationBySubject.get(subject)

        const house_class = vc?.house_class ?? null
        const functional_lordship = vc?.functional_lordship ?? null
        const shadbala_rupa = sb ? Number(sb.rupa) : null
        const shadbala_percentile = sb ? Number(sb.percentile) : null
        const ratification_factor = rf ? Number(rf.avg_ratification) : null
        const ratification_domains = rf?.domains?.filter((d): d is string => d !== null) ?? []

        const { tier, score, reasons } = computeWarningTier({
          house_class, functional_lordship, shadbala_percentile, ratification_factor,
        })

        const fact_ids = [
          ...(vc?.fact_ids ?? []),
          ...(sb ? [sb.fact_id] : []),
        ]

        rows.push({
          lord: lord_graha,
          lord_subject: subject,
          house_class,
          functional_lordship,
          shadbala_rupa,
          shadbala_percentile,
          ratification_factor,
          ratification_domains,
          warning_tier: tier,
          warning_score: score,
          warning_reasons: reasons,
          fact_ids: Array.from(new Set(fact_ids)),
        })

        if (house_class === null) {
          judgment_flags.push(judgmentFlag('house_class_unresolved', `no chart_vichara valence_pass row found for ${lord_graha} (${subject}) — honest gap, not fabricated.`))
        }
        if (ratification_factor === null) {
          judgment_flags.push(judgmentFlag('ratification_unavailable', `${lord_graha} (${subject}) is not a stored karaka for any domain in chart_vichara.varga_ratification — honest absence, not fabricated.`))
        }
      }

      if (rows.length === 0) {
        judgment_flags.push(judgmentFlag('zero_rows_returned', 'no Vimśottarī level-1 MD lords found for this chart/ayanamsha — honest empty, not a query failure being hidden.'))
      }

      return {
        content: {
          chart_id: chartId,
          ayanamsha_id: ayanamshaId,
          rows,
          total: rows.length,
          judgment_flags,
          formula_note:
            'warning_tier is a DETERMINISTIC composite (never an LLM judgment, never a calibrated ' +
            'probability): +1 house_class in {dusthana_lord, maraka} (ga_vichara classify_actor); ' +
            `+1 shadbala_percentile < ${LOW_SHADBALA_PERCENTILE} (rank among this chart's 9 grahas ` +
            'by graha_shadbala_total.rupa); +1 ratification_factor < 1.0 (ga_vichara varga_ratification, ' +
            'averaged across every domain this lord is karaka for); +1 functional_lordship containing ' +
            "'malefic' (stored graha_functional_class_per_ascendant). Score 0=none, 1=watch, 2=elevated, " +
            '3+=high.',
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
