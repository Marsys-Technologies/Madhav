-- 1021_nirmana_l3_ka_taranga_ka_jivana_parva_output_digest_specs.sql
--
-- NIRMANA v2.5 -- L3 (Kala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- RESOLUTION_L1 v8 FINAL TASK: close the output_digest_spec gaps found by
-- prior sweeps before standing down. Two of the 11 live gap-list assets
-- (`ka_taranga`, `ka_jivana_parva`) have real content-derived unique keys
-- and clean live data for the canonical chart -- unambiguous, mirroring
-- the established pattern (ka_gochara #2545, bo_upaya #2538/#2544,
-- ph_nimitta #2539) -- authored and applied without waiting for a ruling,
-- per the brief's own instruction. The other 9 gap-list assets are NOT
-- included here; each needed genuine judgment and is logged separately
-- (see STATE_l1.md this cycle for the full disposition table), not
-- silently dropped.
--
-- ka_taranga (kala_taranga): writer's own `_INSERT_SQL`
-- (ka_taranga.py) writes exactly chart_id, month, scope_kind, scope_id,
-- activation, components, formula_version via an
-- `ON CONFLICT (chart_id, month, scope_kind, scope_id) DO UPDATE` upsert
-- -- that 4-column tuple is the table's own real UNIQUE CONSTRAINT
-- (`kala_taranga_chart_id_month_scope_kind_scope_id_key`), not a surrogate.
-- `taranga_id` (gen_random_uuid() surrogate PK) and `computed_at`
-- (write-time DEFAULT now()) excluded from value_columns, the same two
-- exclusion classes as every prior spec in this campaign. Live-verified
-- against the canonical chart (482012f1): 92,412 rows, 0 NULL across the
-- 4 key columns, 0 duplicate-key groups.
--
-- ka_jivana_parva (kala_jivana_parva): key_columns
-- (chart_id, source_citation, start_year) matches the table's own real
-- UNIQUE index `idx_kala_jivana_parva_natural_key` exactly (not the
-- alternate `(chart_id, parva_index)` unique index -- chosen because
-- `source_citation` is a content-derived string built in
-- `ka_jivana_parva.py` from the dasha level/planet, not a bare positional
-- counter, matching this campaign's "deterministic derivation from real
-- content" convention more directly). `id` (bigserial surrogate PK) and
-- `computed_at` excluded from value_columns. Live-verified against the
-- canonical chart: 100 rows, 0 NULL across the 3 key columns, 0
-- duplicate-key groups.
--
-- Grant pre-flight (both tables): `has_table_privilege
-- ('nirmana_evidence_ingress_writer', '<table>', 'SELECT')` = true for
-- both `kala_taranga` and `kala_activation`... i.e. both target tables,
-- live-verified. `asset_registry.integrity_check_sql` non-null for both
-- `ka_taranga` and `ka_jivana_parva` (live-verified). No grant or
-- integrity_check_sql migration needed for either asset.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented (same pattern as migration 1018):
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below, per asset
--   print(canonical_digest(spec))                              # == the literal below
--   print(_validate_spec('<asset_id>', spec, sha).asset_id)     # passes the server's own validator
--   "
--
-- Rehearsed end-to-end against live prod inside a ROLLED-BACK transaction
-- (psycopg3, autocommit=False, dict_row): INSERTed both exact spec rows ->
-- called the REAL `compute_output_digest(cur, asset_id=...)` for each ->
-- got back clean 64-hex digests with no exception on the key preflight ->
-- `conn.rollback()` -> re-queried `asset_output_digest_specs` from a fresh
-- connection afterward and confirmed 0 rows for both asset_ids, i.e.
-- genuinely rolled back, nothing persisted by the rehearsal.
--
-- Applied DIRECTLY to production ahead of this migration's deploy, per
-- this lane's established apply-then-PR precedent (bo_upaya #2538,
-- ph_nimitta #2539, bo_upaya-narrow #2544, ka_gochara #2545 -- Conductor
-- DB-fast-path ratification, #2514): the exact INSERTs below were
-- committed live, then re-queried from a fresh autocommit connection to
-- confirm 1 non-retired row per asset, then `compute_output_digest`
-- called again against those live rows (fresh transaction) and returned
-- the SAME digests as the rehearsal for both assets -- confirming the
-- applied specs match what was rehearsed, not a re-derivation. This
-- migration file is the durable, reviewable record; re-applying it via
-- the deploy-time `migrate.ts` runner is an idempotent no-op
-- (`ON CONFLICT (asset_id, spec_sha256) DO NOTHING`).
--
-- Numbering note: highest migration file on disk at cycle start was 1020
-- (bo_anveshana, PR #2555, MERGED). `gh pr list --state open
-- --json files` shows no open PR claiming any `migrations/1021*` path.
-- 1021 confirmed free. Authored on a FRESH branch off origin/main per
-- STATE precedent.
--
-- Post-apply verification (SN.8 -- never trust a silent no-op): expect
--   SELECT asset_id FROM asset_output_digest_specs
--    WHERE asset_id IN ('ka_taranga','ka_jivana_parva')
--      AND retired_at IS NULL  -- expect 2 rows

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_taranga',
  '181059b54729ac55a3ae454a38b306e1672c1644b4a0a7b14c12188d233700bd',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_taranga","relation":"kala_taranga","key_columns":["chart_id","month","scope_kind","scope_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["chart_id","month","scope_kind","scope_id","activation","components","formula_version"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_jivana_parva',
  'ab00c0682991ab3bb167fed1edd8426924eed3bb6fb1aad4fcaea6bd510b96bc',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_jivana_parva","relation":"kala_jivana_parva","key_columns":["chart_id","source_citation","start_year"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"value_columns":["chart_id","parva_index","parva_level","start_year","end_year","dasha_planet","dominant_signal_class","parva_quality","theme_keywords","narrative","high_convergence_count","avg_effective_score","source_citation"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
