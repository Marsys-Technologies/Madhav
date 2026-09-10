-- 912_nirmana_l0_bg_sarvatobhadra_grid_provenance_receipt.sql
--
-- CONDUCTOR ruling on #2398 (L3 -> CONDUCTOR, overnight, option (a) of the three
-- offered): `bg_sarvatobhadra_grid` (asset_kind='data', scope='global', has_writer=false,
-- target_floor=0 -- ADJUDICATION-11's empty-by-ruling disposition, already the subject
-- of the accepted #2393 asset_freshness sentinel in migration 911) has never had an
-- `asset_provenance_receipts` row. `compute_upstream_hash`
-- (python-sidecar/pipeline/orchestrator/asset_runner.py L233-253) requires every
-- declared non-service dependency to carry a non-null `output_digest`; with zero rows
-- for this dependency, it returns None for the whole upstream digest on every future
-- `ka_vedha_gochara` rebuild, deterministically blocking `accepted_rebuild_observed`
-- (requires `receipt_state='proven'`, definitions.ts ~L2322). Confirmed live: runs
-- fce48664.../4ae63395... both reproduced `receipt_state='unknown'`,
-- `unknown_reasons: ["upstream_digest_unavailable"]`.
--
-- Option (b) (drop the depends_on edge) was rejected in #2398 itself -- it masks a
-- real, intentionally-activating dependency (migration 529's activation-path note).
-- Option (c) (extend the FROZEN orchestrator's compute_upstream_hash carve-out) is
-- the FROZEN-adjacent path and would need its own from-scratch review; option (a) is
-- a pure-data fix with the exact shape already accepted once for this same asset
-- (#2393 / migration 911's asset_freshness sentinel), so it is chosen here.
--
-- Only two columns are actually read by compute_upstream_hash's dependency check for
-- an upstream row (`output_digest`, `receipt_state`; `asset_kind`/`service_health` come
-- from the live `asset_registry` join, not this row) -- verified by direct reading of
-- `load_upstream_receipts` + `compute_upstream_hash` before writing this migration.
-- Every value below is a genuinely computed digest against real, currently-true facts
-- (verified via direct DB read immediately before authoring, same discipline as 895):
--   * `bg_sarvatobhadra_grid` has 0 rows (live-queried) and 0 declared dependencies
--     (`depends_on = '{}'`, live-queried) -- both permanent, ADJUDICATION-11 facts, not
--     assumptions.
--   * `output_digest_spec` (new row in `asset_output_digest_specs`, required by this
--     table's own `output_digest_spec_sha256` FK) describes the table's real natural
--     key (`UNIQUE (school_tag, cell_kind, cell_index, table_version)`, read from
--     `pg_constraint`) and every other genuine content column (`id`/`created_at`
--     excluded, same convention as 887-896/900-901).
--   * `output_digest` = the exact `compute_output_digest` formula
--     (sha256("nirmana-output-content-v1\0" || spec_sha256 || component_name || "\0"
--     || row_count:u64be), output_digest.py L227-261) evaluated by hand for the true
--     current state: 0 rows.
--   * `partition_digest` = the exact `build_receipt` formula
--     (canonical_digest({"version": receipt_version, "partition_key": "__whole_asset__"}),
--     provenance.py L94-97) for the whole-asset partition (no `natural_key_partition`
--     declared for this asset).
--   * `upstream_digest` = the exact declared-deps `compute_upstream_hash` formula
--     (canonical_digest({"version": "nirmana-upstream-receipts-v2", "asset_id":
--     "bg_sarvatobhadra_grid", "chart_id": null, "receipts": []}), asset_runner.py
--     L245-253) for 0 declared dependencies.
--   * `code_digest`/`config_digest` are left NULL, honestly: this asset has no writer
--     (`has_writer=false`) and therefore no code/config for either to describe -- not
--     "unavailable" in the blocked sense `build_receipt` uses that phrase for buildable
--     assets. Neither column is read by `compute_upstream_hash`'s dependency check, so
--     this cannot itself reintroduce the gate this migration closes.
--   * `receipt_state='proven'`, `unknown_reasons=[]`: per ADJUDICATION-11 the true state
--     of this asset (permanently 0 rows) is fully, definitively known -- there is no
--     writer left to run that could ever produce a different, more-verified answer.
--
-- Global scope: `chart_id` is NULL so `scope_key` (generated column,
-- COALESCE(chart_id::text, '__global__')) resolves to '__global__' and this single row
-- satisfies `load_upstream_receipts`'s NULL-chart_id fallback join for every chart's
-- `ka_vedha_gochara` rebuild, present and future -- not just the canonical chart.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bg_sarvatobhadra_grid',
  '5ed4b4a54c39ca61c20e456e73ec4b83a889d7d216875af85199a15a50e844f1',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bg_sarvatobhadra_grid","relation":"bg_sarvatobhadra_grid","key_columns":["school_tag","cell_kind","cell_index","table_version"],"value_columns":["school_tag","cell_index","cell_kind","cell_value","source_text_id","source_citation","table_version","native_confirmed"]}]}'::jsonb
);

INSERT INTO asset_provenance_receipts (
  asset_id, chart_id, partition_key, receipt_version,
  code_digest, config_digest, upstream_digest, partition_digest,
  output_digest, output_digest_spec_sha256, upstream_receipts,
  receipt_state, unknown_reasons, build_id
)
VALUES (
  'bg_sarvatobhadra_grid',
  NULL,
  '__whole_asset__',
  'nirmana-provenance-receipt-v2',
  NULL,
  NULL,
  '68cd21b0658628dd15f77080fc3554c22d1d277d5943819113ef64218bce52fa',
  '595f36c1f29daa8c000e0154667af1083b139b45da5546271375b7b342a26e7e',
  '1c6818c598d801e36d245ddcbae5a207b05ffab0cd27390fc669421c53e67b09',
  '5ed4b4a54c39ca61c20e456e73ec4b83a889d7d216875af85199a15a50e844f1',
  '[]'::jsonb,
  'proven',
  '[]'::jsonb,
  NULL
);

COMMIT;
