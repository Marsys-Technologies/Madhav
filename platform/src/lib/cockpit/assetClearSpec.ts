export type ClearOp = { sql: string }

/**
 * Transforms a simple single-table count_sql into the equivalent DELETE statement.
 * Returns null if the count_sql doesn't follow the simple pattern (e.g., subquery sums).
 *
 * Handles both single-line and multiline count_sqls. The regex matches:
 *   SELECT count(*) [AS <alias>] FROM <rest>
 * and replaces only the SELECT...FROM prefix, leaving the WHERE clause intact.
 */
export function deriveDeleteSqlFromCountSql(countSql: string): string | null {
  const sql = countSql?.trim()
  if (!sql) return null
  const transformed = sql.replace(
    /^SELECT\s+count\(\*\)\s*(?:AS\s+\w+\s+)?FROM\b/i,
    'DELETE FROM'
  )
  if (transformed === sql) return null
  return transformed
}

/**
 * Explicit clear operations for assets whose count_sql can't be auto-transformed.
 * null means the asset has no data rows to clear (skip cleanly, not an error).
 */
export const EXPLICIT_CLEAR_OPS: Record<string, ClearOp[] | null> = {
  ga_condition: [
    { sql: 'DELETE FROM ga_condition_composite WHERE chart_id = $1' },
    { sql: "DELETE FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE 'graha_avastha_%_per_varga'" },
  ],

  // ── L2 Bodha — multi-table writers ────────────────────────────────────────
  // Each of these writers emits MORE than one table, but the asset's single
  // target_table + un-derivable compound count_sql meant the clear deleted only
  // the primary table and silently left the secondary tables behind (they then
  // reappeared in the next preview — the "layer won't clear" bug). Every DELETE
  // is chart-scoped; tables are ordered FK-child-first so deletes never violate
  // a foreign key.
  bo_karanajala: [
    // bodha_contradictions is an FK child of bodha_msr_signals (cleared by
    // bo_laksana, which runs later in the reverse-topo order) — delete it first.
    { sql: 'DELETE FROM bodha_contradictions WHERE chart_id = $1' },
    { sql: 'DELETE FROM bodha_cgm_edges WHERE chart_id = $1' },
  ],
  bo_sangati: [
    { sql: 'DELETE FROM bodha_convergence WHERE chart_id = $1' },
    { sql: 'DELETE FROM bodha_cdlm_cells WHERE chart_id = $1' },
  ],
  bo_upaya: [
    // rm chain: resonances ← remedy_prescriptions ← dasha_windowed_prescriptions.
    // Delete deepest child first.
    { sql: 'DELETE FROM bodha_rm_dasha_windowed_prescriptions WHERE chart_id = $1' },
    { sql: 'DELETE FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1' },
    { sql: 'DELETE FROM bodha_rm_resonances WHERE chart_id = $1' },
  ],
  bo_anveshana: [
    { sql: 'DELETE FROM bodha_anomalies WHERE chart_id = $1' },
    { sql: 'DELETE FROM bodha_discoveries WHERE chart_id = $1' },
  ],

  // ── L5 Mīmāṃsā — per_chart multi-table writers + one mis-targeted asset ────
  // Same multi-table-writer gap as L2. mi_adhilepa is additionally mis-specified:
  // its registry target_table was mimamsa_signal_adjustment (a table it never
  // writes), so its real output (mimamsa_load_bearing) was never cleared. No FK
  // constraints exist among the mimamsa tables, so delete order is free.
  mi_bhavisya: [
    { sql: 'DELETE FROM mimamsa_manifestation_sets WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_predictions WHERE chart_id = $1' },
  ],
  mi_pramana: [
    { sql: 'DELETE FROM mimamsa_reliability WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_calibration WHERE chart_id = $1' },
  ],
  mi_pariksha: [
    { sql: 'DELETE FROM mimamsa_attribution WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_discoveries WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_qa_eval WHERE chart_id = $1' },
  ],
  mi_darshana: [
    { sql: 'DELETE FROM mimamsa_insight_embeddings WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_insight_units WHERE chart_id = $1' },
  ],
  mi_adhilepa: [
    { sql: 'DELETE FROM mimamsa_load_bearing WHERE chart_id = $1' },
    // Secondary output tables beyond the registered target_table.
    // count_sql extended in migration 364 to count all three tables.
    { sql: 'DELETE FROM mimamsa_convergence_adjustment WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_anchor_adjustment WHERE chart_id = $1' },
  ],

  // mi_seva's count_sql is the un-scoped `SELECT count(*) FROM mimamsa_preferences`
  // (no WHERE chart_id = $1), so deriveDeleteSqlFromCountSql() would transform it into
  // an unscoped `DELETE FROM mimamsa_preferences` — wiping EVERY user's preferences on
  // a single-chart clear. Protective skip-clean stop-gap (C-D2-10): null disables the
  // auto-derived destructive DELETE. The proper chart-scoped count_sql + clear is a
  // Tier-4 registry migration handled in a later wave.
  mi_seva: null,

  // ── L4 Phala — multi-table writers ───────────────────────────────────────────
  // ph_rectification writes phala_rectification (185 rows) + phala_rectification_best
  // (1 row). phala_rectification_best has an FK to phala_rectification — delete child first.
  ph_rectification: [
    { sql: 'DELETE FROM phala_rectification_best WHERE chart_id = $1' },
    { sql: 'DELETE FROM phala_rectification WHERE chart_id = $1' },
  ],

  // bo_samvada's "table" is the vw_chart_digest VIEW (a derived projection over
  // other bodha tables) — it owns no rows of its own and cannot be DELETEd from.
  // null = nothing to clear, skip cleanly (avoids a spurious failed_tables entry).
  bo_samvada: null,
}
