import { query } from '@/lib/db/client'
import {
  ABSTENTION_MARKER_PATTERNS,
  CATALOG_ONLY_MARKER_PATTERNS,
} from '@/lib/retrieval/signal_glossary'

export interface PriorityRankingRow {
  signal_id?: string
  signal_headline_text?: string | null
  neutral_dignity_downranked?: boolean
  abstention_marker_pattern?: string | null
  catalog_only_marker_pattern?: string | null
  priority_score?: number | null
  pre_exclusion_rank?: number | string | null
  partition_rank?: number | string | null
  [k: string]: unknown
}

export interface PriorityRankingQuery {
  chart_id: string
  ayanamsha_id: string
  date_from: string
  date_to: string
  domain_filter: readonly string[] | null
  top_k: number
}

/** Read the existing independently capped served and excluded ranking partitions. */
export async function readPriorityRankingRows({
  chart_id,
  ayanamsha_id,
  date_from,
  date_to,
  domain_filter,
  top_k,
}: PriorityRankingQuery): Promise<PriorityRankingRow[]> {
  // Join activation with signals to compute combined priority.
  // WP-1.5: prior SQL referenced columns that do not exist on kala_activation
  // (activation_strength/window_start/window_end/trigger_type) → every call errored.
  // Real columns: orb_strength (activation strength proxy), activation_start/_end (DATE),
  // signature_class. F-DATE-TZ: activation_start/_end emitted via to_char as 'YYYY-MM-DD'.
  // MC-024 fix: a "graha dignity per varga: dignity state = neutral" descriptor row is
  // rarely a genuine priority signal (a neutral dignity is a non-finding, not a strength
  // or weakness worth surfacing near the top) — down-ranked via a priority_score penalty
  // multiplier rather than dropped (B.10: never silently drop data), and flagged per-row
  // (neutral_dignity_downranked) plus summarized in the envelope so a caller can tell a
  // downranked row apart from one that genuinely scored low.
  // F-131 (PARIŚEṢA-V4): two defects on this surface, both fixed here at serve time.
  //
  //  (1) INTERNAL COMPUTATION-ABSTENTION MARKERS WERE RANKED AS PRIORITY SIGNALS.
  //      "graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method
  //      [ga_structural]" is not an astrological finding — it is the writer's honest
  //      §B.10 record that no verifiable classical per-varga ceṣṭā-bala formula exists,
  //      and it ranked #5 by priority_score on the native's own chart. Such rows are now
  //      excluded from `ranked_signals` and DISCLOSED in `excluded_internal_markers`
  //      with the pattern that matched and the rank they would have occupied — excluded
  //      with a trace, never silently dropped (B.10, and the same disclosure discipline
  //      as `neutral_dignity_downranked` below). `requires_pass` catalog-only rows are
  //      deliberately NOT excluded — see signal_glossary.ts's disposition note (§N.6).
  //
  //  (2) RAW TEMPLATE STRINGS WERE SERVED AS PROSE. `signal_headline_text` is a
  //      deterministic template whose category segment is a bare snake_case schema key.
  //      Each served row now also carries `signal_headline_label`, the acharya-grade
  //      form from the glossary — and `headline_label_mapped: false` plus the unchanged
  //      raw string when no mapping exists (nothing is invented, §N.7 item 6).
  //      `signal_headline_text` is still returned raw on every row (§N.5 / B.10).
  //
  // Excluding after the LIMIT would silently shrink the page below top_k, so the ranking
  // is done in one query with two window functions: `partition_rank` ranks the servable
  // (non-abstention) rows so exactly top_k of them come back, and `pre_exclusion_rank`
  // records where an abstention row WOULD have landed, which is what makes the
  // disclosure meaningful ("this was going to be your #5").
  const params: unknown[] = [chart_id, ayanamsha_id, date_from, date_to]
  let domainClause = ''
  if (domain_filter && domain_filter.length > 0) {
    params.push(domain_filter)
    domainClause = ` AND m.domains_affected_array && $${params.length}::text[]`
  }
  params.push(ABSTENTION_MARKER_PATTERNS)
  const abstentionParam = params.length
  params.push(CATALOG_ONLY_MARKER_PATTERNS)
  const catalogParam = params.length
  params.push(top_k)
  const topKParam = params.length

  // strpos() over lowercased text rather than ILIKE: the glossary patterns contain `[`
  // and `_`, both LIKE metacharacters, and a plain substring test is what the Python
  // side's own semantics are. WITH ORDINALITY preserves glossary order so the most
  // specific pattern is the one reported when several match.
  const markerExpr = (paramIdx: number) => `
            (SELECT t.p FROM unnest($${paramIdx}::text[]) WITH ORDINALITY AS t(p, ord)
              WHERE strpos(lower(m.signal_headline_text), lower(t.p)) > 0
              ORDER BY t.ord LIMIT 1)`

  const sql = `
        WITH scored AS (
          SELECT
            m.signal_id,
            m.signal_headline_text,
            m.computed_salience,
            m.domains_affected_array,
            m.signal_type_class,
            a.orb_strength AS activation_strength,
            to_char(a.activation_start, 'YYYY-MM-DD') AS window_start,
            to_char(a.activation_end, 'YYYY-MM-DD')   AS window_end,
            a.signature_class AS trigger_type,
            (m.signal_headline_text ILIKE '%dignity%neutral%') AS neutral_dignity_downranked,
            ${markerExpr(abstentionParam)} AS abstention_marker_pattern,
            ${markerExpr(catalogParam)} AS catalog_only_marker_pattern,
            -- NIRMĀṆA L3-W3 (§N.7 item 6). This was COALESCE(a.orb_strength, 0.5).
            --
            -- kala_activation.orb_strength is NULL on 669,964 of 672,551 rows (99.6%), so that
            -- default fired on almost every row of a RANKING score. And 0.5 is not neutral:
            -- where orb_strength is actually present it ranges 0.700-1.000 with a mean of 0.986,
            -- so the substituted value sits BELOW the entire observed range. The effect was a
            -- systematic penalty for the absence of data — the 0.4% of rows that happen to carry
            -- an orb outranked the rest largely because they carry one at all.
            --
            -- The factor is now DROPPED when unavailable rather than invented, which is this
            -- codebase's established convention for an absent term (cf. kala_ritual_resonance:
            -- "DROPPED from the product and the product renormalised over the factors actually
            -- present — never zero-filled"). orb_strength_available is emitted alongside so a
            -- caller can tell a score computed WITH the orb term from one computed without it;
            -- the two are not strictly comparable, and the flag is what makes that visible
            -- instead of silent (§N.6 — density signalling is data, not narration).
            (a.orb_strength IS NOT NULL) AS orb_strength_available,
            (m.computed_salience * COALESCE(a.orb_strength, 1.0) *
              (CASE WHEN m.signal_headline_text ILIKE '%dignity%neutral%' THEN 0.3 ELSE 1.0 END)
            ) AS priority_score
          FROM bodha_msr_signals m
          JOIN kala_activation a ON m.signal_id = a.signal_id
            AND a.chart_id = m.chart_id
            AND a.ayanamsha_id = m.ayanamsha_id
          WHERE m.chart_id = $1
            AND m.ayanamsha_id = $2
            AND a.activation_end >= $3::date
            AND a.activation_start <= $4::date${domainClause}
        ),
        ranked AS (
          SELECT s.*,
            ROW_NUMBER() OVER (
              ORDER BY s.priority_score DESC NULLS LAST, s.signal_id
            ) AS pre_exclusion_rank,
            ROW_NUMBER() OVER (
              PARTITION BY (s.abstention_marker_pattern IS NULL)
              ORDER BY s.priority_score DESC NULLS LAST, s.signal_id
            ) AS partition_rank
          FROM scored s
        )
        SELECT * FROM ranked
        WHERE (abstention_marker_pattern IS NULL     AND partition_rank     <= $${topKParam})
           OR (abstention_marker_pattern IS NOT NULL AND pre_exclusion_rank <= $${topKParam})
        ORDER BY priority_score DESC NULLS LAST, signal_id
      `



  const result = await query<PriorityRankingRow>(sql, params)
  return result.rows
}
