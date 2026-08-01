/**
 * query_parihara_graph — L0 Brahmagyan parihāra graph + activity rules + factor census
 * =============================================================================
 * ṢAḌ-DARŚANA campaign items 36/41 (SHAD_DARSHANA_BRIEF_v2_0.md §1 rows 36 + 41 ·
 * §3 W3). The substrate — tables `bg_parihara_rules`, `bg_muhurta_activity_rules`,
 * `bg_muhurta_factor_census`, writer `bg_parihara_rules.py`, migration 485 —
 * landed with PR #930 (Night 2). This capability is the read path over all three;
 * it computes nothing of its own and re-authors no corpus content.
 *
 * THE THREE PAYLOADS (one asset, three physical tables — mirrors the asset's own
 * `count_sql`):
 *   1. `parihara_rules`  — the doṣa-cancellation graph. Every row already carries a
 *      REAL non-placeholder classical citation: the writer's own SQL filter excludes
 *      brahma_dosha_catalog rows whose only citation is the `classical_tradition`
 *      placeholder. That exclusion is a density fact a caller MUST see, so this
 *      handler counts the excluded placeholder-only doṣas LIVE (never a hardcoded
 *      literal) and returns it as `placeholder_only_dosha_count` beside
 *      `real_cited_dosha_count` — §N.6 part 1: a caller can never read the served
 *      row count as "every doṣa in the corpus".
 *   2. `activity_rules`  — per-activity (vivah/griha_pravesh/vyapara/yatra/
 *      property_purchase/mantra_initiation/upaya_ritual/sadhana_initiation) tithi/
 *      nakṣatra/vāra quality rules, materialized verbatim from panchang_engine's
 *      already-cited EVENT_TABLES.
 *   3. `factor_census`    — item 41's completeness register: one row per named
 *      classical timing-factor family, disposed `computed` / `not_computed` /
 *      `not_in_corpus` with a citation or an honest gap reason.
 *
 * THE SCOPE DISCLOSURE THAT MATTERS (carried through verbatim from the substrate,
 * never softened): at PR #930, every parihāra row was `scope='natal'` — the ingested
 * corpus held NO muhūrta-specific doṣa-cancellation content at chapter/verse grain.
 * ADJUDICATION-10 Part 1 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md, migration 524)
 * later found and seeded the ONE genuine exception the corpus actually holds — the
 * Abhijit sarva-doṣaghna gloss at bphs_jaimini PG213 — as a single `scope='muhurta'`
 * row keyed to `dosha_canonical_id='rahu_kalam'` (the schema has no wildcard/all-doṣa
 * convention, so this one row narrows to one doṣa key by construction, disclosed via
 * `extraction_context='translator_gloss_in_narrative'`, not invented as a mūla-sūtra).
 * Every OTHER muhūrta-scope cancellation remains genuinely absent and is registered
 * in the factor census; this handler surfaces the LIVE count as `muhurta_scope_rule_count`
 * (never a hardcoded assumption) so the downstream adjudication engine reports the
 * corpus's actual, current state rather than a stale snapshot (B.10 / data-honesty rail).
 *
 * Global chart-independent reference — no chart_id, by construction.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const SECTIONS = ['parihara_rules', 'activity_rules', 'factor_census'] as const
type Section = (typeof SECTIONS)[number]

const ACTIVITY_CLASSES = [
  'vivah', 'griha_pravesh', 'vyapara', 'yatra',
  'property_purchase', 'mantra_initiation', 'upaya_ritual', 'sadhana_initiation',
] as const

export const queryPariharaGraphCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_parihara_graph',
  type:  'tool',
  layer: 'L0',
  name:  'query_parihara_graph',

  description: [
    'Read the parihāra (doṣa-cancellation) graph, the per-activity muhūrta factor-quality rule',
    'tables, and the Muhūrta Factor Census / corpus-gap register (bg_parihara_rules,',
    'bg_muhurta_activity_rules, bg_muhurta_factor_census). Request one section or all three.',
    'Parihāra rows are citation-filtered: only doṣas carrying a real, non-placeholder classical',
    'citation are represented, and the count of doṣas excluded for carrying only a',
    "'classical_tradition' placeholder is returned alongside — never read the served row count as",
    'the whole corpus. Rows also carry extraction_context (translator_gloss_in_narrative vs',
    'mula_sutra_citation, nullable) so a translator gloss is never read with a mūla-sūtra’s',
    'evidentiary weight. Nearly every row is scope=natal; the one named muhūrta-scope exception is',
    'reported via the live muhurta_scope_rule_count, never assumed absent or assumed present.',
    'The census disposes each named timing-factor family as',
    'computed, not_computed or not_in_corpus with a citation or an honest gap reason and an',
    'ingestion pointer. Global classical reference — no chart_id needed; returns RULES, not any',
    "chart's verdict.",
  ].join(' '),

  input_schema: {
    section: { type: 'string', description: `Which payload: ${SECTIONS.join(', ')}, or omit for all three.` },
    activity_class: { type: 'string', description: `Filter activity_rules to one of: ${ACTIVITY_CLASSES.join(', ')}.` },
    dosha_canonical_id: { type: 'string', description: 'Filter parihara_rules to one doṣa canonical id.' },
    disposition: { type: 'string', description: 'Filter factor_census by disposition: computed, not_computed, not_in_corpus.' },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const sectionArg = args['section'] != null ? String(args['section']) : null
    if (sectionArg && !(SECTIONS as readonly string[]).includes(sectionArg)) {
      return { content: { error: `section must be one of: ${SECTIONS.join(', ')}` }, is_error: true }
    }
    const wants = (s: Section) => sectionArg === null || sectionArg === s

    const activityClass = args['activity_class'] != null ? String(args['activity_class']) : null
    if (activityClass && !(ACTIVITY_CLASSES as readonly string[]).includes(activityClass)) {
      return { content: { error: `activity_class must be one of: ${ACTIVITY_CLASSES.join(', ')}` }, is_error: true }
    }
    const doshaId = args['dosha_canonical_id'] != null ? String(args['dosha_canonical_id']) : null
    const disposition = args['disposition'] != null ? String(args['disposition']) : null

    const content: Record<string, unknown> = {
      sections_returned: SECTIONS.filter(wants),
      filters: { section: sectionArg, activity_class: activityClass, dosha_canonical_id: doshaId, disposition },
      disclaimer:
        'Classical RULE tables and a corpus-gap register only — not a computed election verdict ' +
        'for any chart or moment. Adjudication over these rules is the caller\'s engine.',
      provenance: {
        tables: ['bg_parihara_rules', 'bg_muhurta_activity_rules', 'bg_muhurta_factor_census'],
        asset_id: 'bg_parihara_rules',
      },
    }

    try {
      if (wants('parihara_rules')) {
        const filters: string[] = ['1=1']
        const params: unknown[] = []
        let p = 1
        if (doshaId) { filters.push(`dosha_canonical_id = $${p++}`); params.push(doshaId) }
        const rulesResult = await query<Record<string, unknown>>(
          `SELECT dosha_canonical_id, dosha_name_en, dosha_category, cancellation_index,
                  cancellation_condition_text, net_standing, scope,
                  source_text_id, source_chapter, source_citation, extraction_context
             FROM bg_parihara_rules
            WHERE ${filters.join(' AND ')}
            ORDER BY dosha_canonical_id, cancellation_index`,
          params,
        )
        const rules = rulesResult.rows
        const muhurtaScoped = rules.filter((r) => r['scope'] === 'muhurta')

        // Live density counts — the placeholder/real split is queried, never asserted from
        // a remembered literal (the substrate's own PR body number would go stale silently).
        const splitResult = await query<Record<string, unknown>>(
          `SELECT
             COUNT(*) FILTER (
               WHERE cancellation_conditions IS NOT NULL
                 AND classical_citations IS NOT NULL
                 AND jsonb_typeof(classical_citations) = 'array'
                 AND EXISTS (
                   SELECT 1 FROM jsonb_array_elements(classical_citations) elem
                   WHERE elem->>'text_id' IS NOT NULL AND elem->>'text_id' <> 'classical_tradition')
             ) AS real_cited,
             COUNT(*) FILTER (
               WHERE cancellation_conditions IS NOT NULL
                 AND NOT (
                   classical_citations IS NOT NULL
                   AND jsonb_typeof(classical_citations) = 'array'
                   AND EXISTS (
                     SELECT 1 FROM jsonb_array_elements(classical_citations) elem
                     WHERE elem->>'text_id' IS NOT NULL AND elem->>'text_id' <> 'classical_tradition'))
             ) AS placeholder_only
           FROM brahma_dosha_catalog`,
          [],
        )
        const split = splitResult.rows[0] ?? {}

        content['parihara_rules'] = {
          rows: rules,
          count: rules.length,
          // §N.6 part 1 — confirmed vs excluded, counted separately and pointed at.
          real_cited_dosha_count: Number(split['real_cited'] ?? 0),
          placeholder_only_dosha_count: Number(split['placeholder_only'] ?? 0),
          placeholder_note:
            'Doṣas whose only classical_citations entry is the placeholder text_id ' +
            "'classical_tradition' are EXCLUDED from this graph by the substrate writer. They " +
            'exist in brahma_dosha_catalog and are reachable via query_dosha_catalog, but they ' +
            'are not citation-backed cancellation rules and must not be counted as such.',
          muhurta_scope_rule_count: muhurtaScoped.length,
          scope_note:
            muhurtaScoped.length === 0
              ? 'ZERO muhūrta-scope cancellation rules exist. Every row here is scope=natal ' +
                '(Manglik/Kāla-Sarpa/Kemadruma-class bhaṅga). The corpus holds no muhūrta-specific ' +
                'doṣa-cancellation content at chapter/verse grain — registered as a gap in the ' +
                'factor census. An adjudication engine must therefore report residual doṣas ' +
                'uncancelled rather than apply a natal bhaṅga rule to a moment.'
              : `${muhurtaScoped.length} muhūrta-scope cancellation rule(s) present.`,
          ...(rules.length === 0
            ? { empty_reason: `No parihāra rows${doshaId ? ` for dosha_canonical_id=${doshaId}` : ''} — the bg_parihara_rules asset may not be built in this environment.` }
            : {}),
        }
      }

      if (wants('activity_rules')) {
        const filters: string[] = ['1=1']
        const params: unknown[] = []
        let p = 1
        if (activityClass) { filters.push(`activity_class = $${p++}`); params.push(activityClass) }
        const result = await query<Record<string, unknown>>(
          `SELECT activity_class, factor_type, factor_id, quality_score, source_citation
             FROM bg_muhurta_activity_rules
            WHERE ${filters.join(' AND ')}
            ORDER BY activity_class, factor_type, factor_id`,
          params,
        )
        content['activity_rules'] = {
          rows: result.rows,
          count: result.rows.length,
          ...(result.rows.length === 0
            ? { empty_reason: `No activity rules${activityClass ? ` for activity_class=${activityClass}` : ''} — the bg_parihara_rules asset may not be built in this environment.` }
            : {}),
        }
      }

      if (wants('factor_census')) {
        const filters: string[] = ['1=1']
        const params: unknown[] = []
        let p = 1
        if (disposition) { filters.push(`disposition = $${p++}`); params.push(disposition) }
        const result = await query<Record<string, unknown>>(
          `SELECT factor_family, factor_name, disposition, citation_or_gap_note,
                  evidence_pointer, school_tag
             FROM bg_muhurta_factor_census
            WHERE ${filters.join(' AND ')}
            ORDER BY factor_family, factor_name`,
          params,
        )
        const byDisposition: Record<string, number> = {}
        for (const r of result.rows) {
          const d = String(r['disposition'])
          byDisposition[d] = (byDisposition[d] ?? 0) + 1
        }
        content['factor_census'] = {
          rows: result.rows,
          count: result.rows.length,
          disposition_counts: byDisposition,
          census_note:
            'The completeness register for muhūrta factors. not_computed / not_in_corpus rows ' +
            'are named ingestion work items, never silently improvised elsewhere.',
          ...(result.rows.length === 0
            ? { empty_reason: `No census rows${disposition ? ` with disposition=${disposition}` : ''} — the bg_parihara_rules asset may not be built in this environment.` }
            : {}),
        }
      }

      return { content, is_error: false }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
