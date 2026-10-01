-- 1213_nirmana_l3_service_selftest_output_digest_specs.sql
--
-- Suvarna Track I-5 (CANONICAL_CHART_REBUILD_PLAN_v1_0 blocker B-2: `ka_sangam`'s
-- NULL upstream digest). Transaction ownership belongs to platform/scripts/migrate.ts.
-- Data-only: two INSERTs into asset_output_digest_specs (amjis_app-owned); no table is
-- altered. NOT applied by this change.
--
-- ROOT CAUSE (code-traced): asset_runner.compute_upstream_hash returns NULL when any
-- declared dependency's latest receipt has no output_digest (asset_runner.py:236-247);
-- the NULL makes ka_sangam's own receipt 'unknown' (provenance.build_receipt,
-- 'upstream_digest_unavailable'), and ka_sangam has 7 in-plan dependents. ka_sangam
-- declares two services, ka_dasha_kala and ka_muhurta_seva. The section-7.2 service
-- accommodation in compute_upstream_hash accepts a healthy service's receipt without
-- 'proven', but it still requires an output_digest, and its docstring names the digest
-- `_persist_probe_receipt` writes. Only the legacy health_probe path (bg_* services)
-- runs `_persist_probe_receipt`. Both of these are writer-backed services and run through
-- `_run_data_writer` (asset_runner.py "if is_service: ... get_writer"), whose receipt
-- takes output_digest from compute_output_digest(asset_id). With no spec that returns
-- (None, None): the receipt carries NO output_digest, so the accommodation never applies
-- and ka_sangam's upstream digest stays NULL no matter how often they run.
--
-- FIX WITHOUT TOUCHING THE FROZEN ORCHESTRATOR OR THE 'proven' PREDICATE: give each
-- service the same thing every data asset has, a reviewed output-digest spec over what
-- its writer actually produces. migration 933 records that each writes exactly three
-- columns onto its OWN asset_registry row (service_health, last_selftest_at,
-- selftest_detail), nothing else. The spec digests that row's service_health and
-- selftest_detail (the self-test verdict and its deterministic payload: system list and
-- window counts for ka_dasha_kala, the FORENSIC check strings for ka_muhurta_seva);
-- last_selftest_at is excluded as volatile. Receipts then carry a real, content-sensitive
-- digest AND a spec sha, so they are 'proven' (not merely accommodated), and a changed
-- self-test outcome changes the digest. Scoped by where_equals asset_id = <asset>:
-- other registry rows never move it.
--
-- WHAT THIS DOES NOT DO: it does not backfill. ka_dasha_kala's current receipt (no
-- digest) and ka_muhurta_seva's (none) are replaced only when each service is rebuilt
-- after this lands, so BOTH must be in the plan ahead of ka_sangam (ka_dasha_kala is not
-- in the 26-asset plan today). Same class, not covered here (no declared dependent in
-- scope): ka_graha_sancara, ka_tulana, bg_panchanga.
--
-- Tests: platform/python-sidecar/tests/l3/test_i4_i5_output_digest_specs.py.
--
-- Post-apply verification (CLAUDE.md N.4): expect 2 rows
--   SELECT asset_id FROM asset_output_digest_specs
--    WHERE asset_id IN ('ka_dasha_kala','ka_muhurta_seva') AND retired_at IS NULL;

SET LOCAL lock_timeout = '5s';

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_dasha_kala',
  'c5dfe575a78b9b9e0eb9a3f1bb158ff002671e4a667f70fc5d86a5c51e73681d',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"service_selftest","relation":"asset_registry","key_columns":["asset_id"],"where_equals":{"asset_id":"ka_dasha_kala"},"value_columns":["asset_id","service_health","selftest_detail"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_muhurta_seva',
  'dbcdba8a8616178362a9913c324575b57333eea374f402d804980cf666269ed4',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"service_selftest","relation":"asset_registry","key_columns":["asset_id"],"where_equals":{"asset_id":"ka_muhurta_seva"},"value_columns":["asset_id","service_health","selftest_detail"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
