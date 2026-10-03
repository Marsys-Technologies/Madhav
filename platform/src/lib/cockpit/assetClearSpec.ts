/**
 * JL-020 clear-allowlist classification (BA Phase 2.5 J10): every per-chart-clearable
 * table is either REBUILDABLE (writer-derived output; safely wiped and regenerated on
 * rebuild) or IRREPLACEABLE (native-authored input, recorded real-world outcomes, or an
 * append-only ledger — must survive any clear/rebuild). This file is the enforcement
 * point: an asset with no entry here gets the default target_table-fallback DELETE
 * (correct for REBUILDABLE assets); IRREPLACEABLE assets MUST have an entry that either
 * scopes the DELETE to exclude irreplaceable rows, or is `null` to skip the clear
 * entirely.
 *
 * Known IRREPLACEABLE surfaces protected below:
 *   - mimamsa_journal.native_answer/answered_at (mi_abhilekha)      — scoped DELETE
 *   - mimamsa_predictions + mimamsa_manifestation_sets (mi_bhavisya) — null (full skip; SS N-104)
 *   - mimamsa_preferences (mi_seva)                                 — null (full skip)
 *   - mimamsa_export_log (mi_vistara)                                — null (full skip)
 * Everything else in this map exists to fix multi-table-writer coverage gaps or
 * un-derivable count_sql shapes for otherwise-REBUILDABLE assets.
 */
export type ClearOp = {
  sql: string
  /**
   * Optional pre-execution guard (WP7 packet C-1, Option A). When present, the
   * execute route runs `guard.sql` (with the same $1 chart binding as the op)
   * BEFORE any statement of the asset runs. If the guard returns ≥1 row and the
   * principal is NOT the release authority, the whole asset op is refused —
   * pushed to failed_tables with `refuse_message`, zero statements executed.
   * The release authority proceeds, and `guard.cascade` statements (if any) run
   * as additional ops inside the same per-asset SAVEPOINT.
   */
  guard?: {
    sql: string
    refuse_message: string
    cascade?: string[]
  }
}

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
  // A count_sql joining a second table (e.g. an ownership/lookup table) cannot be
  // mechanically turned into a DELETE by this prefix-swap — `DELETE FROM t JOIN ...`
  // is not legal Postgres (JOIN requires `USING`, and even then the semantics differ
  // from a plain WHERE-scoped delete). Bail out to null so the caller falls through
  // to "no clear spec resolved" (an honest, surfaced failure) instead of silently
  // executing invalid SQL that looks like an ordinary per-asset failure but is really
  // a generation bug. A JOIN-based count_sql needs an explicit EXPLICIT_CLEAR_OPS entry.
  if (/\bJOIN\b/i.test(sql)) return null
  const transformed = sql.replace(
    /^SELECT\s+count\(\*\)\s*(?:AS\s+\w+\s+)?FROM\b/i,
    'DELETE FROM'
  )
  if (transformed === sql) return null
  return transformed
}

/**
 * Operator-facing message for an asset whose clear is an EXPLICIT null because its rows are
 * history (SS N-104). A null spec issues no statement, but a silent skip would let an operator
 * believe something was cleared, so every clear route returns this message for such an asset
 * (execute route: `notices`; invalidateAssets: `InvalidationResult.notices`). Every key MUST be
 * an `EXPLICIT_CLEAR_OPS` null (pinned by a test). Other skip-clean nulls (lel_events, mi_seva,
 * ...) keep their existing behaviour: this map is the deliberate, narrow opt-in.
 */
export const EXPLICIT_CLEAR_NOTICES: Record<string, string> = {
  mi_bhavisya: 'mi_bhavisya is append-only (N-104): nothing cleared',
}

/**
 * Explicit clear operations for assets whose count_sql can't be auto-transformed.
 * null means the asset has no data rows to clear (skip cleanly, not an error).
 */
export const EXPLICIT_CLEAR_OPS: Record<string, ClearOp[] | null> = {
  // ga_structural's count_sql (migration 410_ga_structural_category_ownership.sql) joins
  // chart_facts to fact_category_ownership to scope the count to categories this writer
  // owns — deriveDeleteSqlFromCountSql() correctly refuses to auto-transform a JOIN-bearing
  // count_sql (see that function's own JOIN guard) rather than emit invalid
  // `DELETE FROM ... JOIN ...` SQL, so this asset needs its own explicit op. Uses the same
  // ownership-table subquery the count_sql itself joins against, so any future category
  // added to fact_category_ownership for owning_asset_id='ga_structural' is automatically
  // covered here too — no hardcoded category list to keep in sync.
  ga_structural: [
    {
      sql: `DELETE FROM chart_facts WHERE chart_id = $1 AND fact_category IN (
        SELECT fact_category FROM fact_category_ownership WHERE owning_asset_id = 'ga_structural'
      )`,
    },
  ],

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
    // R6 fix: bo_sangati.py also writes bodha_triangulation (its own writer correctly
    // idempotent-deletes it scoped by chart_id+ayanamsha_id on every real rebuild — this
    // asset was never behind stale data, only the manual "Clear" button never reached it).
    { sql: 'DELETE FROM bodha_triangulation WHERE chart_id = $1' },
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
  // mi_bhavisya (SS N-104, an application of N-46): mimamsa_predictions and
  // mimamsa_manifestation_sets are calibration HISTORY, not rebuildable state. The writer is
  // append-only (it never deletes or rewrites a row), so a cockpit "clear" must not delete them
  // either: a pending prediction's emitted_at is the only evidence of WHEN the claim was made,
  // and mimamsa_manifestation_sets.citation_ref keeps the original freeze id. null = nothing
  // is cleared for this asset (skip cleanly); it is NEVER a DELETE, scoped or otherwise.
  // Previously this entry deleted the chart's manifestation sets and its pending/due predictions.
  // The strict chart-correction policy classifies it in CORRECTION_PRESERVATION
  // (src/lib/build/assetInvalidation.ts); a correction marks predictions stale instead
  // (src/lib/charts/chartContextStaleness.ts).
  mi_bhavisya: null,
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
  // Jātaka Phase-A2 integrity fix: mi_sankalpa has no explicit entry here, so a
  // correction's strict clear falls through to the generic count_sql-derived
  // DELETE — an unconditional per-chart wipe of mimamsa_intervention_ledger.
  // That table holds native-FILED, attested rows (services/mi_sankalpa/db.py:
  // "rows are FILED live, at serve time" — a native's real elected intervention,
  // whether performed and its outcome_event_id are known or not). The writer's
  // own idempotency predicate (delete_unresolved()) is scoped to exactly the
  // rows this writer's own rebuild is entitled to touch — elected-pending,
  // never performed, never linked to a real-world outcome. This mirrors that
  // predicate verbatim rather than reinventing it, so the two never drift.
  mi_sankalpa: [
    {
      sql: "DELETE FROM mimamsa_intervention_ledger WHERE chart_id = $1 AND study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL",
    },
  ],
  mi_adhilepa: [
    { sql: 'DELETE FROM mimamsa_load_bearing WHERE chart_id = $1' },
    // Secondary output tables beyond the registered target_table.
    // count_sql extended in migration 364 (3 tables) and migration 369 (all 5 tables).
    { sql: 'DELETE FROM mimamsa_convergence_adjustment WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_anchor_adjustment WHERE chart_id = $1' },
    // Added migration 369: signal + fact overlay tables written by mi_adhilepa
    // but previously absent from count_sql (dark tables). No FK constraints among
    // mimamsa tables — delete order is free.
    { sql: 'DELETE FROM mimamsa_signal_adjustment WHERE chart_id = $1' },
    { sql: 'DELETE FROM mimamsa_fact_adjustment WHERE chart_id = $1' },
  ],

  // mi_kula is a GLOBAL catalog writer (no chart_id column on either table).
  // The writer does: DELETE FROM mimamsa_negative_controls; DELETE FROM mimamsa_signal_families;
  // then re-seeds from the embedded static catalog. deriveDeleteSqlFromCountSql() cannot
  // produce a correct unscoped DELETE from the summed count_sql, so we hardcode both here.
  // Delete negative_controls first (logically depends on families; no FK but safe order).
  mi_kula: [
    { sql: 'DELETE FROM mimamsa_negative_controls' },
    { sql: 'DELETE FROM mimamsa_signal_families' },
  ],

  // mi_seva's count_sql is the un-scoped `SELECT count(*) FROM mimamsa_preferences`
  // (no WHERE chart_id = $1), so deriveDeleteSqlFromCountSql() would transform it into
  // an unscoped `DELETE FROM mimamsa_preferences` — wiping EVERY user's preferences on
  // a single-chart clear. Protective skip-clean stop-gap (C-D2-10): null disables the
  // auto-derived destructive DELETE. The proper chart-scoped count_sql + clear is a
  // Tier-4 registry migration handled in a later wave.
  mi_seva: null,

  // mi_vistara's count_sql is the un-scoped `SELECT count(*) FROM mimamsa_export_log`
  // (no WHERE chart_id = $1) — it is an append-only, global-scope export-integrity
  // ledger that build-time never populates per-chart. Same danger shape as mi_seva
  // above: deriveDeleteSqlFromCountSql() would transform it into an unscoped
  // `DELETE FROM mimamsa_export_log`, wiping the export log for ALL charts on any
  // single-asset clear. BA_FULL_ASSET_AUDIT (2026-07-05) flagged this as the
  // identical bug shape already stop-gapped for mi_seva but never mirrored here.
  // null disables the auto-derived destructive DELETE.
  mi_vistara: null,

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

  // Kāla service-health writers: each runs a self-test, updates only the global
  // asset_registry health fields, and returns rows_inserted=0. Neither owns a
  // chart-scoped data surface, so a chart clear has deliberately nothing to do.
  ka_dasha_kala: null,
  ka_tulana: null,

  // JL-020 / BA_FULL_ASSET_AUDIT: mi_abhilekha's registered target_table is
  // mimamsa_journal, count_sql is null, so it fell through to the target_table
  // fallback DELETE — wiping native_answer/answered_at rows (the native's real,
  // irreplaceable journal answers) on every per-chart clear alongside the
  // never-answered prompt scaffolding. Scoped to only clear unanswered prompts;
  // answered rows are IRREPLACEABLE and must survive any clear/rebuild.
  mi_abhilekha: [
    { sql: 'DELETE FROM mimamsa_journal WHERE chart_id = $1 AND answered_at IS NULL' },
  ],

  // ── LEL — user-authored source data (BA-LEL R2.2 Step 1) ──────────────────────
  // lel_events (migration 423) is a per-chart, user-authored, IRREPLACEABLE source
  // corpus (has_writer=false): the native's real recorded life events + their
  // chart-state index, intaken via the LEL save API — NOT regenerable by any build.
  // Its count_sql is 'SELECT count(*) FROM life_events WHERE chart_id = $1', which
  // deriveDeleteSqlFromCountSql() WOULD transform into a per-chart DELETE — wiping
  // EVERY one of the native's logged events (an append-as-logged corpus whose size is a
  // live quantity, not a fixed 57 — NIRMĀṆA L5 W3-3, §N.7 item 3) and, via a companion
  // op, event_chart_state_index, on any
  // clear/rebuild. That is exactly the JL-010 / JL-020 IRREPLACEABLE-loss failure
  // mode. null disables the auto-derived destructive DELETE entirely: a per-chart
  // clear/rebuild leaves every life_events + event_chart_state_index row intact.
  // LEL rows are only ever mutated by the intake API, never by the asset build path.
  lel_events: null,

  // ── L3 Kāla Gochara — the registered writer's own output (migration 1230) ──────
  // ka_gochara's registry row counts, checks and clears exactly what its REGISTERED
  // WRITER writes: kala_gochara_windows_v2 at generation '2.0' (writers/ka_gochara.py
  // TABLE / GENERATION_V2) and that writer's delta-aware bookkeeping,
  // kala_gochara_v2_build_state at the same generation. The bookkeeping MUST go with the
  // windows: the writer skips a class whose stored class_fingerprint is unchanged
  // ("delta-aware invalidation skip, no recompute, no rewrite"), so a Clear that removed
  // only the windows would leave a rebuild that writes nothing.
  // Scope is exactly (chart_id, generation '2.0'): the century asset's g3_* rows in the
  // same windows_v2 relation, the protected v1 / '3.0' rows in kala_gochara_windows and
  // the '4.0' / '4.1' / '5.0' ledgers (other assets, other generations) are unreachable
  // here. No JOIN (§6.4).
  //
  // This replaces WP7 packet C-1's entry, which cleared the '4.0' ledger (coverage →
  // contacts → windows) behind an authoritative-generation refusal guard: it was tied to
  // migration 1091's '4.0' re-pin of count_sql, which migration 1230 reverts (1091's pin
  // returns together with the writer switch at D-FLIP — and so does that entry). A '4.0'
  // authority can no longer be reached from a ka_gochara Clear, so the guard has nothing
  // left to refuse.
  ka_gochara: [
    { sql: "DELETE FROM kala_gochara_windows_v2 WHERE chart_id = $1 AND generation = '2.0'" },
    { sql: "DELETE FROM kala_gochara_v2_build_state WHERE chart_id = $1 AND generation = '2.0'" },
  ],
}
