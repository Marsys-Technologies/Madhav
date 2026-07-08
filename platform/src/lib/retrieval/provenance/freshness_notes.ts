/**
 * E-2 freshness contract — provenance notes as DATA, not stale literals
 * ======================================================================
 * R5.1 C2 item 1 (see CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md §C2.1;
 * R5_AUTHORITY_DOSSIER_v1_0.md §6: "stale provenance notes mislead worse than
 * none (E-2)").
 *
 * Prior to this module, several handlers carried hardcoded string literals
 * asserting DEFECT-001's orphan rate as "91.5% (OPEN)" and signature_tier as
 * "FULLY DEGENERATE — 100% background". Both claims were true at the time they
 * were written but are FALSE today — post-R4 rebuild changed the underlying
 * counts (verified live against prod: constituent_facts_array orphan rate is
 * now ~1.08% across both canonical charts; signature_tier carries a real
 * 4-value distribution, not a single degenerate value). Restating the old
 * literal is worse than saying nothing (E-2) — it makes a caller distrust
 * good data or trust a since-fixed defect's absence incorrectly.
 *
 * This module re-derives both claims LIVE against current DB state on every
 * call and returns them as structured data carrying `as_of` (when this
 * particular derivation ran) and `expires_on` (the TTL after which a caller
 * holding a cached copy of this note should treat it as stale and re-fetch,
 * not because the derivation itself expires — every call re-derives from
 * scratch — but so no client silently trusts an old response forever).
 *
 * Canonical-or-floor: if the live derivation cannot resolve (query error, or
 * genuinely zero rows to check), the note is floored as `status: 'UNKNOWN'`
 * or `'NO_DATA'` with a `metrics` object of `null`s — never a fabricated or
 * remembered number.
 */

import { query } from '@/lib/db/client'

export type FreshnessStatus =
  | 'RESOLVED'          // 0% orphan / fully non-degenerate
  | 'MOSTLY_RESOLVED'    // small residual orphan rate
  | 'OPEN'               // materially unresolved — matches historical defect shape
  | 'DEGENERATE'         // signature_tier: one value dominates (>=99%)
  | 'POPULATED'          // signature_tier: real distribution present
  | 'NO_DATA'            // no rows to check — claim genuinely not assessable
  | 'UNKNOWN'            // live derivation failed — floored, not guessed

export interface FreshnessNote {
  claim_id: 'DEFECT-001' | 'SIGNATURE_TIER'
  status: FreshnessStatus
  note: string
  /** ISO timestamp: when this response's derivation ran. */
  as_of: string
  /** ISO timestamp: TTL after which a cached copy should be treated as stale and re-fetched. */
  expires_on: string
  metrics: Record<string, number | string | null>
}

// Informational TTL only — every call re-derives from live state regardless.
const NOTE_TTL_MS = 24 * 60 * 60 * 1000

function freshnessWindow(): { as_of: string; expires_on: string } {
  const now = new Date()
  return {
    as_of: now.toISOString(),
    expires_on: new Date(now.getTime() + NOTE_TTL_MS).toISOString(),
  }
}

/**
 * DEFECT-001 freshness contract.
 *
 * If `factIdSample` is supplied, derives the orphan rate over exactly those
 * referenced fact_ids (response-scoped — precise to what was actually served).
 * If omitted, derives the orphan rate over ALL constituent_facts_array
 * references for the chart's bodha_msr_signals rows (whole-chart — answers
 * "what is DEFECT-001's status right now for this chart").
 */
export async function deriveDefect001Note(
  chartId: string,
  factIdSample?: string[],
): Promise<FreshnessNote> {
  const { as_of, expires_on } = freshnessWindow()
  try {
    let totalRefs: number
    let orphanRefs: number

    if (factIdSample && factIdSample.length > 0) {
      const uniqueIds = Array.from(new Set(factIdSample)).filter(Boolean)
      const resolved = await query<{ fact_id: string }>(
        `SELECT fact_id FROM chart_facts WHERE chart_id = $1 AND fact_id = ANY($2::text[])`,
        [chartId, uniqueIds],
      )
      totalRefs = uniqueIds.length
      orphanRefs = totalRefs - resolved.rows.length
    } else {
      const res = await query<{ total_refs: string; orphan_refs: string }>(
        `WITH refs AS (
           SELECT unnest(m.constituent_facts_array) AS fact_id
           FROM bodha_msr_signals m
           WHERE m.chart_id = $1 AND m.constituent_facts_array IS NOT NULL
             AND array_length(m.constituent_facts_array, 1) > 0
         )
         SELECT count(*)::text AS total_refs,
                count(*) FILTER (WHERE cf.fact_id IS NULL)::text AS orphan_refs
         FROM refs LEFT JOIN chart_facts cf ON cf.chart_id = $1 AND cf.fact_id = refs.fact_id`,
        [chartId],
      )
      totalRefs = Number(res.rows[0]?.total_refs ?? 0)
      orphanRefs = Number(res.rows[0]?.orphan_refs ?? 0)
    }

    if (totalRefs === 0) {
      return {
        claim_id: 'DEFECT-001',
        status: 'NO_DATA',
        note: 'No constituent_facts_array references found to check for this chart — ' +
          'cannot derive an orphan rate; not asserting one.',
        as_of, expires_on,
        metrics: { total_refs: 0, orphan_refs: null, orphan_pct: null },
      }
    }

    const orphanPct = Math.round((orphanRefs / totalRefs) * 1000) / 10
    const status: FreshnessStatus =
      orphanPct === 0 ? 'RESOLVED' : orphanPct < 5 ? 'MOSTLY_RESOLVED' : 'OPEN'

    const note =
      `constituent_facts_array resolution against chart_facts, derived live for chart ${chartId}: ` +
      `${orphanRefs}/${totalRefs} references orphaned (${orphanPct}%). ` +
      (status === 'RESOLVED'
        ? 'All references resolve — DEFECT-001 no longer reproduces on this chart.'
        : status === 'MOSTLY_RESOLVED'
        ? 'DEFECT-001 is substantially resolved on this chart (historical baseline pre-R4 rebuild ' +
          'was ~91.5% orphan) — a small residual remains. Treat unresolved refs as reference-only, not an error.'
        : 'Unresolved refs are reference-only, not an error — do not fail joins on them.')

    return {
      claim_id: 'DEFECT-001',
      status,
      note,
      as_of, expires_on,
      metrics: { total_refs: totalRefs, orphan_refs: orphanRefs, orphan_pct: orphanPct },
    }
  } catch (e) {
    return {
      claim_id: 'DEFECT-001',
      status: 'UNKNOWN',
      note: `Live orphan-rate derivation failed (${String(e)}) — floored as UNKNOWN rather than ` +
        'restating a historical figure.',
      as_of, expires_on,
      metrics: { total_refs: null, orphan_refs: null, orphan_pct: null },
    }
  }
}

/**
 * signature_tier freshness contract.
 *
 * Historically reported as "fully degenerate (100% background)". Re-derived
 * live per chart/ayanamsha — post-R4 the column carries a real distribution.
 */
export async function deriveSignatureTierNote(
  chartId: string,
  ayanamshaId: string,
): Promise<FreshnessNote> {
  const { as_of, expires_on } = freshnessWindow()
  try {
    const res = await query<{ signature_tier: string | null; n: string }>(
      `SELECT signature_tier, count(*)::text AS n
       FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2
       GROUP BY signature_tier`,
      [chartId, ayanamshaId],
    )
    const total = res.rows.reduce((sum, r) => sum + Number(r.n), 0)

    if (total === 0) {
      return {
        claim_id: 'SIGNATURE_TIER',
        status: 'NO_DATA',
        note: 'No bodha_msr_signals rows found for this chart/ayanamsha — cannot derive a ' +
          'signature_tier distribution.',
        as_of, expires_on,
        metrics: { total: 0 },
      }
    }

    const dist: Record<string, number> = {}
    for (const r of res.rows) {
      const tier = r.signature_tier ?? 'unknown'
      dist[tier] = Math.round((Number(r.n) / total) * 1000) / 10
    }
    const dominantPct = Math.max(...Object.values(dist))
    const degenerate = dominantPct >= 99
    const distText = Object.entries(dist)
      .sort((a, b) => b[1] - a[1])
      .map(([t, p]) => `${t}=${p}%`)
      .join(', ')

    return {
      claim_id: 'SIGNATURE_TIER',
      status: degenerate ? 'DEGENERATE' : 'POPULATED',
      note: `signature_tier distribution, derived live for chart ${chartId}: ${distText}. ` +
        (degenerate
          ? 'Column is effectively degenerate — do not rank or filter by it; use computed_salience.'
          : 'Column carries a real distribution (not degenerate, unlike the pre-R4 state) — ranking ' +
            'still uses computed_salience as primary, but signature_tier is now a usable secondary signal.'),
      as_of, expires_on,
      metrics: { total, ...dist },
    }
  } catch (e) {
    return {
      claim_id: 'SIGNATURE_TIER',
      status: 'UNKNOWN',
      note: `Live signature_tier derivation failed (${String(e)}) — floored as UNKNOWN rather than ` +
        'restating a historical figure.',
      as_of, expires_on,
      metrics: {},
    }
  }
}
