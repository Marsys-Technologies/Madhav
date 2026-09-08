-- 935_nirmana_l2_bo_bimba_output_digest_spec.sql
--
-- NIRMĀṆA L1 — RESOLUTION_L1 v5 priority 3 (chain pre-clear). Closes the
-- `asset_output_digest_specs` gap for `bo_bimba`. Confirmed via `SELECT *
-- FROM asset_output_digest_specs WHERE asset_id = 'bo_bimba'` returning ZERO
-- rows before this migration. Without a spec row, `compute_output_digest()`
-- (platform/python-sidecar/pipeline/orchestrator/output_digest.py) always
-- returns `(None, None)` for this asset, so its provenance receipt can never
-- leave `receipt_state = 'unknown'` no matter how clean the writer's data is
-- -- same defect class as migrations 905/906/907/914/915/926/929.
--
-- ── relation + ownership (verified against writer source, NOT assumed) ──────
--
-- `bo_bimba`'s target_table is `bodha_cgm_nodes` (asset_registry.count_sql:
-- `SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = $1`). BUT this table
-- is SHARED, not bo_bimba-exclusive -- `grep -l "INSERT INTO bodha_cgm_nodes"
-- platform/python-sidecar/pipeline/orchestrator/writers/*.py` finds TWO
-- writers: `bo_bimba.py` (node_type IN graha/bhava/domain/yoga/dosha -- see
-- lines 325/380/430/503) and `bo_karanajala.py` (node_type IN
-- arudha/special_lagna -- line 1474, added under D-2 Lane V-4 because
-- bo_karanajala already held write access via its centrality UPDATE below).
-- Live-verified split on the canonical chart (482012f1): graha=45, bhava=60,
-- domain=65, dosha=16, yoga=69 (bo_bimba, 255 rows total) vs arudha=95,
-- special_lagna=35 (bo_karanajala, 130 rows) -- 385 rows total, zero overlap,
-- zero unaccounted node_type values. This spec scopes to bo_bimba's OWN five
-- node_type values only (`where_in`), mirroring the `natural_key_partition`
-- precedent already used for the shared `bodha_msr_signals` table (905/906/
-- 907/926/929) -- an unscoped `WHERE chart_id` alone would have wrongly
-- pulled bo_karanajala's arudha/special_lagna rows into bo_bimba's digest.
--
-- Note left for the record, not fixed here (out of this migration's scope):
-- bo_karanajala also runs a cross-cutting `UPDATE bodha_cgm_nodes SET
-- pagerank_score = ..., eigenvector_centrality = ..., betweenness_centrality
-- = ..., harmonic_centrality = ...` across ALL node_types (its own graph-
-- computation pass, line ~1736) -- this legitimately mutates bo_bimba-owned
-- rows' content after bo_bimba's own write. That is intentional and left
-- IN scope for bo_bimba's digest (these are genuine declared columns of
-- bo_bimba's output; the digest is asking "what does this asset's data look
-- like right now", not "what did bo_bimba's own code write"). bo_karanajala
-- itself still has NO `natural_key_partition` set (`asset_registry.
-- natural_key_partition IS NULL` for bo_karanajala, confirmed live) --
-- flagged for a future migration in this same series, not addressed here.
--
-- ── key + value columns (verified against live data + writer source) ────────
--
-- `node_id` is safe as BOTH `key_columns` and a `value_columns` member: it
-- was historically a random `uuid.uuid4()` (four emit sites) but was fixed
-- to a DETERMINISTIC identity by Nirmāṇa #1888/D-CND-29
-- (`assign_deterministic_node_ids()` in bo_bimba.py:531, deriving via
-- `bodha_cgm_node_identity()` from migration 714) -- same class of fix as
-- `bo_laksana`'s `assign_deterministic_signal_ids()` that makes `signal_id`
-- safe in 905/906/907/926/929's specs. Live-verified on the canonical chart,
-- scoped to bo_bimba's five node_type values: zero duplicate `node_id`, zero
-- duplicate natural key (ayanamsha_id, snapshot_type, node_type,
-- node_subject), zero NULL `node_id` across all 255 in-scope rows.
--
-- Three columns excluded from both `key_columns` and `value_columns`:
--   * `build_id`, `computed_at` -- per-rebuild identifiers, not content
--     (same rationale as every precedent migration).
--   * `node_embedding_vec` (pgvector(768)) -- confirmed 100% NULL for every
--     in-scope row on the canonical chart today (not yet populated by any
--     writer); excluded for parsimony until a future writer populates it and
--     a spec revision adds it deliberately, rather than hashing an all-NULL
--     column now.
--
-- `value_columns` is the remaining 42 columns, including `node_id` itself
-- (matching precedent's inclusion of deterministic identity columns as
-- content, not merely an index).
--
-- ── idempotency pattern ──────────────────────────────────────────────────────
-- Matches precedent 891/893/894/914/915: a plain INSERT, no ON CONFLICT.
-- `bo_bimba` has zero existing rows in `asset_output_digest_specs`
-- (confirmed at the top of this file), so this cannot collide.
--
-- ── spec_sha256 computation (independently verified, not guessed) ───────────
-- Produced by IMPORTING the real modules and calling them directly:
--
--   cd platform/python-sidecar && python3 -c "
--   import sys; sys.path.insert(0, '.')
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec, compute_output_digest
--   spec = {...the exact dict below...}
--   sha = canonical_digest(spec)
--   _validate_spec('bo_bimba', spec, sha)   # raised nothing
--   print(sha)
--   "
--
-- `_validate_spec` raised nothing and printed:
--   fbadd2e78a4e5ae57bd6925734aa6ab76471a0bcf18644d719a27dcf0bfe059a
--
-- Additionally rehearsed the FULL `compute_output_digest()` path against live
-- production data inside a transaction that was rolled back (never
-- committed): inserted this exact spec row, called
-- `compute_output_digest(cur, asset_id='bo_bimba')`, got back a real
-- 64-hex digest with no error
-- (`cf99450f5094c7d07b95f2efbc2e05a3fc6918739420578c92a963b95f0b8fcb`) and
-- confirmed `row_count_in_scope = 255`, then rolled back -- prod was never
-- mutated by the rehearsal, only by this migration's own INSERT below.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_bimba',
  'fbadd2e78a4e5ae57bd6925734aa6ab76471a0bcf18644d719a27dcf0bfe059a',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_cgm_nodes","relation":"bodha_cgm_nodes","key_columns":["node_id"],"value_columns":["node_id","chart_id","ayanamsha_id","snapshot_type","node_type","node_subject","node_label_human","position_in_chart_jsonb","strength_score","dignity_state","source_subsystem","degree_in","degree_out","betweenness_centrality","eigenvector_centrality","pagerank_score","clustering_coefficient","closeness_centrality","harmonic_centrality","core_number","articulation_point_flag","primary_domain","domain_affiliations_jsonb","cluster_membership_array","cgm_subgraph_cluster_id","msr_signal_id","configuration_constituents_array","configuration_lifecycle_state","hub_flag","hub_score","hub_edge_types_array","present_in_traditions_array","cross_ayanamsha_presence_score","ephemeris_audit_jsonb","msr_salience_version_used","cdlm_version_used","graph_compute_library","graph_compute_library_version","verification_pass_status","citation_ref","citation_human","engine_version"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"node_type":["bhava","domain","dosha","graha","yoga"]}}]}'::jsonb
);

COMMIT;
