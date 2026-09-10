-- 894_nirmana_l1_ga_condition_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 199: `ga_dashas` froze (adjudication #2276's guard fix), opening
-- `ga_condition` as newly `OPEN-PENDING-PIN`. Closes the fleet-wide `asset_output_digest_specs`
-- gap for `ga_condition`, authored before dispatch (the `ga_dashas`-cycle-189/190 lesson).
--
-- Spec design verified against live data before authoring:
--   * `ga_condition_composite` already carries a genuine DB UNIQUE constraint,
--     `ga_condition_composite_unique (chart_id, ayanamsha_id, graha)` -- no live
--     collision-check reasoning needed, the DB itself enforces this key's uniqueness.
--   * Live-checked (not assumed): 0 NULLs across all 3 key columns for the canonical chart's
--     45 live rows.
--   * `id` (PK, serial) and `build_id` are excluded from `value_columns` -- both are
--     per-rebuild identifiers, not content. `computed_at` (wall-clock write timestamp)
--     excluded for the same reason.
--   * Every other column is genuine condition-composite content and is included.
--
-- Note: this asset's own `integrity_check_sql` conjunct (a) is documented (F-C8) as currently
-- RED on the canonical chart's pre-fix, already-built rows -- the writer-level fix (dignity
-- text-label fallback) already landed and was independently re-verified live in cycle 175;
-- this dispatch's fresh rebuild is exactly what resolves the stale-data half of that finding.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_condition',
  '9569f7246afffa08339c5645df809d5a150d39b123762988321e723a11a1365c',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"ga_condition_composite","relation":"ga_condition_composite","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","graha"],"value_columns":["chart_id","ayanamsha_id","graha","dignity_d1","dignity_score_d1","varga_dignity_spread","varga_dignity_composite","avastha_baladi","avastha_jagradadi","avastha_deeptaadi","avastha_lajjitaadi","avastha_sayanadi","motion_state","speed_degrees_per_day","is_retrograde","combustion_arc_from_sun","is_combust","is_deeply_combust","naisargika_relation","tatkalika_relation","panchadha_relation","graha_yuddha_with","graha_yuddha_result","condition_score","condition_formula_version","condition_score_breakdown","peak_dasha_periods","weak_dasha_periods"]}]}'::jsonb
);

COMMIT;
