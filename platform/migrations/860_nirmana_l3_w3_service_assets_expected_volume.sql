-- 860_nirmana_l3_w3_service_assets_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for L3's four `asset_kind='service'` assets in one
-- migration (unlike migrations 852-859, one asset each): `ka_dasha_kala`, `ka_graha_sancara`,
-- `ka_muhurta_seva`, `ka_tulana`. All four share the IDENTICAL, verified-live reason
-- `expected_volume_formula` was NULL: they are health-probe services, not row-producing data
-- writers, so there is no per-chart table to count in the first place.
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-859's convention for this range).
--
-- Verified live for all four, not assumed from the naming alone: `asset_kind='service'`,
-- `asset_type='service'`, `storage_type='service'`, `target_table IS NULL`, `count_sql IS NULL`,
-- `health_probe IS NOT NULL`. All four already have `health_probe` contracts and go through
-- `asset_runner.py`'s "verify-then-conditionally-regenerate" path
-- (`is_service = asset_kind=='service' or asset_type=='service'`; `has_check and rebuild_policy`
-- -> `_probe_asset`/`_mark_probe_green`, asset_runner.py:1402-1417) rather than the row-count
-- `zero_rows_is_complete`/`target_floor` path (asset_runner.py:1054-1069) that governs data
-- writers. Build completion for these four is therefore governed by the health probe's own
-- pass/fail, not by any row count -- `expected_volume_formula`/`target_floor` do not apply to
-- them in the sense F-L3-4 asks the other 19 L3 assets to answer, and this migration says so
-- explicitly rather than leaving the field an ambiguous NULL that could be misread as "not yet
-- derived."
--
-- `target_floor` is intentionally left untouched by this migration (0 for `ka_dasha_kala`/
-- `ka_tulana`, NULL for `ka_graha_sancara`/`ka_muhurta_seva`) -- that inconsistency was checked
-- against the specific code path that would make it matter (asset_runner.py's row-count
-- `zero_rows_is_complete` branch) and confirmed NOT to apply here, since all four take the
-- probe-based completion path instead; changing `target_floor` is out of scope for this F-L3-4
-- migration and not attempted.

UPDATE asset_registry
   SET expected_volume_formula = 'N/A, service-kind asset, health-probe governed, no per-chart row-producing table',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'service_no_row_volume',
         'chart_scoped', false,
         'reason', 'asset_kind=''service'', target_table IS NULL, count_sql IS NULL. Build completion is governed by health_probe pass/fail (asset_runner.py''s verify-then-conditionally-regenerate path), not by a row count',
         'verified_live', jsonb_build_object('asset_kind', 'service', 'asset_type', 'service', 'storage_type', 'service', 'health_probe_present', true),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not applicable: this is a health-probe service asset (asset_kind=service), not a row-producing data writer. It has no target_table and no count_sql to begin with, so there is no row volume to derive a formula for. Build completion is governed entirely by the health probe''s own pass/fail result.'
 WHERE asset_id IN ('ka_dasha_kala', 'ka_graha_sancara', 'ka_muhurta_seva', 'ka_tulana')
   AND expected_volume_formula IS NULL;
