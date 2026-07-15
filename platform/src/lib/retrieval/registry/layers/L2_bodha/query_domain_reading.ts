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
import { grahaAffinity, bhavaAffinity, DOMAIN_BHAVA_AFFINITY } from '../../../ranking/priors_config'

/** Max signal_ids hydrated with text in one bounded lookup (payload + query safety). */
const HYDRATION_ID_CAP = 2000

/** Candidate pool fetched by raw salience before the domain-composite re-rank (mirrors query_signals). */
const DISCRIMINATION_CANDIDATE_SIZE = 400
/** How many domain-discriminated signals to surface on the reading. */
const DISCRIMINATED_TOP_K = 20

/**
 * External reading-domain → the value present in bodha_msr_signals.domains_affected_array
 * that scopes the candidate pool. `null` = no array pre-filter (the domain is not a stored
 * tag — e.g. moksha/education); the pool is the whole chart and the composite domain overlay
 * (graha×domain + bhāva×domain + varga) does ALL the discrimination. Disclosed in provenance.
 */
const DOMAIN_TO_SIGNAL_FILTER: Record<string, string | null> = {
  career:       'career',
  wealth:       'wealth',
  relationship: 'relationship',
  health:       'health',
  character:    'character',
  spirituality: 'spirituality',
  education:    null,   // not a stored domain tag — rank whole-chart by the vidyā overlay (2/4/5/9 + Me/Ju/Ke)
  moksha:       null,   // not a stored domain tag — rank whole-chart by the mokṣa-trikoṇa overlay (4-8-12 + Ketu)
  other:        null,
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
        'Life domain to query.',
        'One of: career, wealth, relationship, health, character, spirituality, education, moksha, other.',
        'education = vidyā (bhāva 4/5/2/9 + Mercury/Jupiter/Ketu); moksha = the 4-8-12 mokṣa-trikoṇa',
        '+ Ketu axis (NOT a 9th-house/dharma alias — that is spirituality).',
        'Each domain re-ranks its signals by a domain-specific graha×bhāva×varga overlay, so the',
        'ranked_signals surface genuinely differs across domains (see ranked_signals[].rationale).',
        'If omitted or unrecognized, returns the list of available domains for this chart.',
      ].join(' '),
      enum: ['career', 'wealth', 'relationship', 'health', 'character', 'spirituality', 'education', 'moksha', 'other'],
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

    const VALID_DOMAINS = ['career', 'wealth', 'relationship', 'health', 'character', 'spirituality', 'education', 'moksha', 'other']

    try {
      // Domain discovery is sourced from bodha_cdlm_cells (domain_row/domain_col).
      // bodha_question_lenses has no domain column; lenses are filtered via DOMAIN_TO_QUESTION_TYPES.
      if (!domain || !VALID_DOMAINS.includes(domain)) {
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
      const RANKED_HYDRATE_PER_LENS = 25
      const lensRankedIds: string[] = []
      for (const lens of lensRes.rows as Array<Record<string, unknown>>) {
        const arj = lens['all_relevant_ranked_jsonb']
        const ranked = arj && typeof arj === 'object' && !Array.isArray(arj)
          ? (arj as Record<string, unknown>)['ranked_signals']
          : arj
        if (Array.isArray(ranked)) {
          for (const rs of ranked.slice(0, RANKED_HYDRATE_PER_LENS)) {
            const sid = (rs as Record<string, unknown>)?.['signal_id']
            if (typeof sid === 'string' && sid) lensRankedIds.push(sid)
          }
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
      const hydratedLenses = (lensRes.rows as Array<Record<string, unknown>>).map(lens => {
        const arj = lens['all_relevant_ranked_jsonb']
        if (arj && typeof arj === 'object' && !Array.isArray(arj)) {
          const arjObj = arj as Record<string, unknown>
          const ranked = arjObj['ranked_signals']
          if (Array.isArray(ranked)) {
            const enriched = ranked.map(rs => {
              const r = rs as Record<string, unknown>
              const t = typeof r['signal_id'] === 'string' ? textById.get(r['signal_id'] as string) : undefined
              return t ? { ...r, headline: t.headline, summary: t.summary, signature_tier: t.signature_tier } : r
            })
            return { ...lens, all_relevant_ranked_jsonb: { ...arjObj, ranked_signals: enriched } }
          }
        }
        return lens
      })

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
