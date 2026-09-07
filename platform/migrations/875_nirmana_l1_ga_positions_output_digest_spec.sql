-- 875_nirmana_l1_ga_positions_output_digest_spec.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors ga_positions' output-digest specification -- fix 2 of adjudication
-- #2180's second ruling (2026-09-07T01:45:02Z). Without a spec,
-- compute_output_digest() returns (None, None) for this asset, so its
-- asset_freshness row is stuck at freshness_state='unknown' with
-- unknown_reasons including "output_digest_spec_unavailable" /
-- "output_digest_unavailable" even after fix 1 (natural_key_partition,
-- migration 868, PR #2205) cleared "partition_undeclared" -- the same
-- D-CND-27 per-asset-authoring gap #1840 already established for
-- mi_vistara/mi_jivanaghatana/mi_kula (migrations 820/821/822). This is the
-- last of the two authorized registry-configuration fixes before wave 1
-- (per #2180's ruling) can genuinely dispatch and read this asset back as
-- 'fresh'.
--
-- ga_positions writes to the SHARED table chart_facts (target_table for all
-- seven co-writers backfilled by migrations 868-874), so the digest -- like
-- fix 1's natural_key_partition -- must scope to exactly ga_positions' own
-- declared slice, not the whole table: chart_id = the canonical chart
-- (where_equals, same reviewed-filter mechanism migration 820 used for
-- mi_jivanaghatana's own per-chart scoping) AND fact_category IN the same
-- four categories migration 868 already verified against
-- ga_positions_writer.py's actual write sites (graha_position,
-- graha_sign_attributes, bhava_cusps, house_chalit) -- via where_in, sorted
-- and deduplicated per output_digest.py's _where_in validator requirement.
--
-- key_columns = ["fact_id"], chart_facts' actual registered primary key
-- (chart_facts_pkey). Confirmed via _fact_id() in ga_positions_writer.py
-- (issue #1747 / PR #1898, the same fix cited in this session's own prior
-- acceptance evidence) that fact_id is now a deterministic SHA-256 of
-- (category, subject, key, chart_id, ayanamsha_id) alone -- build_id was
-- removed from the hash precisely so fact_id stays stable across rebuilds
-- of identical content, so using it as the sort key does not make the
-- digest depend on which build produced the row.
--
-- value_columns names every real content column on chart_facts (25 total)
-- EXCEPT two pipeline-bookkeeping columns: computed_at (row-insert
-- timestamp -- the same exclusion class migration 820/821/822 documented
-- for created_at/updated_at) and build_id (an arbitrary per-run UUID with
-- no business content of its own; including it would make the digest
-- differ on every single rebuild even when nothing computed actually
-- changed, defeating the digest's own purpose of detecting real content
-- drift -- the same reasoning that motivated removing build_id from
-- fact_id's own hash in #1747). fact_id itself IS included in value_columns
-- (mirrors the mi_jivanaghatana precedent, which included its own key
-- columns chart_id/event_id in value_columns too) since it is now genuine,
-- stable, deterministic content, not a volatile artifact.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                     # == the literal below
--   print(_validate_spec('ga_positions', spec, sha))  # passes the server's own validator
--   "
-- Additionally end-to-end rehearsed live (read-only, rollback-only
-- transaction: INSERT the spec row, call the real
-- compute_output_digest(cur, asset_id='ga_positions') against production,
-- then ROLLBACK) to prove the where_equals/where_in filters and the full
-- component SQL actually execute against live data before this migration
-- lands -- not just that the spec shape validates offline. Result:
-- digest=d5837f053d6fc7f192f851ecd538057a950b4acf6af1315681d486f4c82c120f
-- over 1115 live rows for the canonical chart across the four declared
-- categories, zero NULL-key rows, transaction rolled back, 0 rows left
-- behind (independently re-verified via a fresh SELECT count(*) afterward).

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_positions',
  '474b77debe7776ee7f84a1d6b225b386d7846452cbeb2cc258a98706168e3c9f',
  '{"components":[{"name":"chart_facts","relation":"chart_facts","key_columns":["fact_id"],"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject","fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref","citation_human","source_calculation","verification_pass_status","engine_version","salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag","near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text","cross_ayanamsha_divergence_arcsec","formula_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"fact_category":["bhava_cusps","graha_position","graha_sign_attributes","house_chalit"]}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
