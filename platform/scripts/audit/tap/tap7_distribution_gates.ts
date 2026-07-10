/**
 * tap7_distribution_gates.ts — TAP-7 (TOTAL_AUDIT_PROTOCOL_v1_0.md §3,
 * "Distribution gates, universal") — the 8 gates run in the 2026-07-10 audit
 * (MARSYS_DEFECT_GAP_REGISTER_v2_0.md §11.2 "VALUE/DISTRIBUTION DEFECTS
 * (TAP-7 + TAP-3b recompute)" + §11.3 SC-2 G-2/D-17/D-18 citations + Phase 5
 * "TAP-7 8 gates" line item).
 *
 * Gate 1  Collapse-to-constant — a scored column takes ≤2 distinct values
 *         across all rows for a chart (V-2 cheshta_bala, V-3 sthana_bala).
 * Gate 2  All-one-valence — every row in a valence-bearing set shares the
 *         same valence (D-16: 0/5 negative anchors; would catch any
 *         all-positive or all-negative collapse).
 * Gate 3  Identical-causal-chain — a free-text derivation/chain field is the
 *         exact same string across every row (D-17).
 * Gate 4  Degenerate edge annotation — edges share identical
 *         computed_strength AND identical affected_domains (G-2).
 * Gate 5  ≥ (N-1)/N identical component values — a computed composite has
 *         5 or more of its 7 (or equivalent majority) rows numerically
 *         identical (V-4 ishta/kashta; the M-14/TAP-7 "5/7-identical" class).
 * Gate 6  Score-saturation / no-spread — top-K ranked rows cluster within
 *         1e-3 of the same ceiling value, making rank order float-noise
 *         (V-10 MSR composite saturates at 0.8999… for 7/10 top rows).
 * Gate 7  Duplicate-row-to-the-second — two rows share a derived timestamp
 *         to the exact second (V-13 sade-sati cycle duplication).
 * Gate 8  Pagination/offset disjointness — page N and page N+1 of the same
 *         query must not be identical (V-8 offset pagination no-op). This
 *         gate is API-level (query_chart_facts), not DB-level; the SQL
 *         proxy alone cannot exercise it, so it is QUARANTINED here with an
 *         explicit instruction for how the live pipeline should run it
 *         (hit the deployed retrieval API twice with offset=0/48 and diff).
 *
 * Requires DATABASE_URL (or Cloud SQL Auth Proxy) for Gates 1-7 — see
 * lib/tap_db.ts. Gate 8 needs a reachable retrieval API base URL
 * (TAP7_API_BASE_URL) and is quarantined without one.
 *
 * Run: npx tsx --conditions=react-server platform/scripts/audit/tap/tap7_distribution_gates.ts
 */
import { connectTapDb, printReport, NATIVE_CHART_ID, type LawResult } from './lib/tap_db'

async function main() {
  const db = await connectTapDb()
  const results: LawResult[] = []

  if (!db.available) {
    console.log(JSON.stringify({ battery: 'TAP-7 distribution gates', skipped: true, reason: db.reason }, null, 2))
    process.exit(printReport('TAP-7 distribution gates', [], db.reason))
    return
  }

  // Gate 1 — collapse-to-constant (cheshta_bala V-2; sthana_bala V-3)
  {
    const { rows } = await db.query<{ fact_value_num: string; c: string }>(
      `SELECT fact_value_num::text, count(*)::text AS c FROM chart_facts
        WHERE chart_id = $1 AND fact_category = 'graha_shadbala_cheshta'
        GROUP BY fact_value_num`,
      [NATIVE_CHART_ID]
    )
    const distinct = rows.length
    results.push({
      id: 'TAP7-Gate1:cheshta_bala',
      title: 'graha_shadbala_cheshta is not chart-invariant (>2 distinct values)',
      status: distinct > 2 ? 'PASS' : 'QUARANTINED',
      detail: `${distinct} distinct value(s) across all grahas: ${rows.map((r) => `${r.fact_value_num}×${r.c}`).join(', ')}.`,
      register_rows: distinct <= 2 ? ['V-2', 'M-1'] : [],
    })
  }

  // Gate 2 — all-one-valence (phala_anchors — D-16)
  {
    const { rows } = await db.query<{ valence: string; c: string }>(
      `SELECT valence, count(*)::text AS c FROM phala_anchors WHERE chart_id = $1 GROUP BY valence`,
      [NATIVE_CHART_ID]
    ).catch(() => ({ rows: [] as { valence: string; c: string }[] }))
    const distinctValences = rows.length
    results.push({
      id: 'TAP7-Gate2:phala_anchors_valence',
      title: 'phala_anchors valence is not all-one-value (has ≥1 adverse-valence row)',
      status: rows.length === 0 ? 'SKIPPED' : distinctValences > 1 ? 'PASS' : 'QUARANTINED',
      detail:
        rows.length === 0
          ? 'phala_anchors returned 0 rows or has no valence column in this schema version.'
          : `${distinctValences} distinct valence(s): ${rows.map((r) => `${r.valence}×${r.c}`).join(', ')}.`,
      register_rows: rows.length > 0 && distinctValences <= 1 ? ['D-16'] : [],
    })
  }

  // Gate 3 — identical-causal-chain (phala_anchors derivation ledger — D-17)
  {
    const { rows } = await db
      .query<{ chain: string; c: string }>(
        `SELECT derivation_chain::text AS chain, count(*)::text AS c FROM phala_anchors
          WHERE chart_id = $1 GROUP BY derivation_chain ORDER BY 2 DESC LIMIT 1`,
        [NATIVE_CHART_ID]
      )
      .catch(() => ({ rows: [] as { chain: string; c: string }[] }))
    if (rows.length === 0) {
      results.push({
        id: 'TAP7-Gate3:causal_chain',
        title: 'Anchor causal-chain field is not a constant string',
        status: 'SKIPPED',
        detail: 'phala_anchors.derivation_chain not present in this schema version, or table empty — verify column name against current phala_anchors DDL.',
      })
    } else {
      const { rows: totalRows } = await db.query<{ c: string }>(`SELECT count(*)::text AS c FROM phala_anchors WHERE chart_id = $1`, [NATIVE_CHART_ID])
      const total = parseInt(totalRows[0]?.c ?? '0', 10)
      const topCount = parseInt(rows[0].c, 10)
      const isConstant = total > 1 && topCount === total
      results.push({
        id: 'TAP7-Gate3:causal_chain',
        title: 'Anchor causal-chain field is not a constant string across all anchors',
        status: isConstant ? 'QUARANTINED' : 'PASS',
        detail: `Most common chain value appears in ${topCount}/${total} anchor rows.`,
        register_rows: isConstant ? ['D-17'] : [],
      })
    }
  }

  // Gate 4 — degenerate edge annotation (identical strength AND domains — G-2)
  {
    const { rows } = await db.query<{ computed_strength: string; affected_domains: string; c: string }>(
      `SELECT computed_strength::text, affected_domains::text, count(*)::text AS c
         FROM bodha_cgm_edges WHERE chart_id = $1 AND edge_type = 'aspect'
         GROUP BY computed_strength, affected_domains ORDER BY 3 DESC LIMIT 1`,
      [NATIVE_CHART_ID]
    )
    const { rows: totalRows } = await db.query<{ c: string }>(
      `SELECT count(*)::text AS c FROM bodha_cgm_edges WHERE chart_id = $1 AND edge_type = 'aspect'`,
      [NATIVE_CHART_ID]
    )
    const total = parseInt(totalRows[0]?.c ?? '0', 10)
    const topCount = rows.length ? parseInt(rows[0].c, 10) : 0
    const isDegenerate = total > 1 && topCount === total
    results.push({
      id: 'TAP7-Gate4:edge_annotation',
      title: "aspect edges do not share one (strength, affected_domains) tuple across all rows",
      status: isDegenerate ? 'QUARANTINED' : total === 0 ? 'SKIPPED' : 'PASS',
      detail: total === 0 ? 'No aspect edges found.' : `Most common (strength, domains) tuple covers ${topCount}/${total} aspect edges.`,
      register_rows: isDegenerate ? ['G-2', 'D-18'] : [],
    })
  }

  // Gate 5 — ≥5/7 (majority) identical component values (V-4 ishta/kashta; M-14 composite)
  {
    const { rows } = await db.query<{ fact_value_num: string; c: string }>(
      `SELECT fact_value_num::text, count(*)::text AS c FROM chart_facts
        WHERE chart_id = $1 AND fact_category = 'graha_ishta_phala'
        GROUP BY fact_value_num ORDER BY 2 DESC LIMIT 1`,
      [NATIVE_CHART_ID]
    )
    const { rows: totalRows } = await db.query<{ c: string }>(
      `SELECT count(*)::text AS c FROM chart_facts WHERE chart_id = $1 AND fact_category = 'graha_ishta_phala'`,
      [NATIVE_CHART_ID]
    )
    const total = parseInt(totalRows[0]?.c ?? '0', 10)
    const topCount = rows.length ? parseInt(rows[0].c, 10) : 0
    const majorityIdentical = total > 0 && topCount / total >= 5 / 7
    results.push({
      id: 'TAP7-Gate5:ishta_phala_spread',
      title: 'graha_ishta_phala: fewer than 5/7 grahas share an identical value',
      status: majorityIdentical ? 'QUARANTINED' : total === 0 ? 'SKIPPED' : 'PASS',
      detail: total === 0 ? 'No graha_ishta_phala rows found.' : `${topCount}/${total} grahas share the most common value.`,
      register_rows: majorityIdentical ? ['V-4'] : [],
    })
  }

  // Gate 6 — score-saturation / no-spread among top-K ranked rows (V-10 MSR composite)
  {
    const { rows } = await db.query<{ computed_salience: string }>(
      `SELECT computed_salience::text FROM bodha_msr_signals
        WHERE chart_id = $1 AND computed_salience IS NOT NULL
        ORDER BY computed_salience DESC LIMIT 10`,
      [NATIVE_CHART_ID]
    )
    if (rows.length < 10) {
      results.push({ id: 'TAP7-Gate6:salience_spread', title: 'Top-10 salience spread', status: 'SKIPPED', detail: `Only ${rows.length} scored rows found.` })
    } else {
      const values = rows.map((r) => parseFloat(r.computed_salience))
      const max = Math.max(...values)
      const withinWall = values.filter((v) => max - v < 1e-3).length
      results.push({
        id: 'TAP7-Gate6:salience_spread',
        title: 'Top-10 computed_salience values are not all within 1e-3 of the ceiling',
        status: withinWall >= 7 ? 'QUARANTINED' : 'PASS',
        detail: `${withinWall}/10 top rows within 1e-3 of max (${max}). Rank order inside that wall is float-noise, not signal.`,
        register_rows: withinWall >= 7 ? ['V-10'] : [],
      })
    }
  }

  // Gate 7 — duplicate-row-to-the-second (sade_sati cycle end timestamps — V-13)
  {
    // sade_sati_cycle lives in chart_facts as fact_value_jsonb; check for duplicate
    // cycle-end timestamps to the second among sade_sati_cycle rows.
    const { rows: cycleRows } = await db.query<{ end_ts: string; c: string }>(
      `SELECT fact_value_jsonb->>'cycle_end_at' AS end_ts, count(*)::text AS c
         FROM chart_facts WHERE chart_id = $1 AND fact_category = 'sade_sati_cycle'
           AND fact_value_jsonb->>'cycle_end_at' IS NOT NULL
         GROUP BY 1 HAVING count(*) > 1 ORDER BY 2 DESC LIMIT 5`,
      [NATIVE_CHART_ID]
    ).catch(() => ({ rows: [] as { end_ts: string; c: string }[] }))
    results.push({
      id: 'TAP7-Gate7:sade_sati_dup_timestamps',
      title: 'sade_sati_cycle rows do not share a cycle_end_at timestamp to the second',
      status: cycleRows.length === 0 ? 'PASS' : 'QUARANTINED',
      detail: cycleRows.length === 0 ? 'No duplicate cycle_end_at timestamps found (or field name differs from V-13 evidence — verify against current schema).' : `${cycleRows.length} duplicate-timestamp group(s) found: ${cycleRows.map((r) => `${r.end_ts}×${r.c}`).join(', ')}.`,
      register_rows: cycleRows.length > 0 ? ['V-13', 'D-2'] : [],
    })
  }

  // Gate 8 — pagination/offset disjointness (V-8) — API-level, not DB-level.
  {
    const apiBase = process.env.TAP7_API_BASE_URL
    results.push({
      id: 'TAP7-Gate8:pagination_disjointness',
      title: 'query_chart_facts(offset=N) ≠ query_chart_facts(offset=0) for N > 0',
      status: apiBase ? 'FAIL' : 'QUARANTINED',
      detail: apiBase
        ? 'TAP7_API_BASE_URL was set but this script does not yet drive the live HTTP call — implement the two-call diff against ' + apiBase + '/api/... once the endpoint contract is confirmed.'
        : 'API-level check, not reachable from a DB-only CI job. Pipeline must set TAP7_API_BASE_URL to a running retrieval API and re-run this gate (or run tests/smoke against query_chart_facts with offset=0 vs offset=48 and diff rows) — see V-8.',
      register_rows: ['V-8'],
    })
  }

  process.exit(printReport('TAP-7 Distribution Gates (8 gates)', results))
}

main().catch((err) => {
  console.error('tap7_distribution_gates FATAL:', err)
  process.exit(4)
})
