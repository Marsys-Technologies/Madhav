-- 911_bo_nakshatra_semantic_add_ga_structural_dep.sql
--
-- NIRMĀṆA L2 Bodha — issue #2403 (D-NATIVE-12 Conductor ruling, 2026-09-07T23:37:34Z).
--
-- REGISTRY DRIFT fix (same class as migration 416's ga_structural/ga_condition edge):
-- `nakshatra_semantic_emitter.py` reads `chart_facts` rows with
-- `fact_category IN ('graha_position', 'graha_dispositor_chain', ...)` — the
-- `graha_dispositor_chain` category is written exclusively by `ga_structural`
-- (verified: `grep graha_dispositor_chain platform/python-sidecar/ga_writers/*.py`
-- matches only `ga_structural_writer.py`). But the live `asset_registry.depends_on`
-- for `bo_nakshatra_semantic` was `{ga_positions,ga_nakshatra}` — `ga_structural` was
-- never declared, despite being a real read dependency.
--
-- Consequence (traced end-to-end by a fresh-context verifier subagent, filed as
-- #2403): the orchestrator's delta-skip gate (`asset_runner.py::compute_upstream_hash`)
-- only hashes DECLARED deps x their `last_built_at`. When `ga_structural` was rebuilt
-- after `bo_nakshatra_semantic`'s first (orphaned) run, the rebuild was invisible to
-- the gate, which concluded "no delta" on the second dispatch and the writer never
-- re-executed. `bodha_msr_signals.constituent_facts_array` position 5
-- (`dispositor_fact_id`) for all 45 rows now points at fact_ids deleted by
-- `ga_structural`'s delete-then-insert rebuild (SS N.3) — a dangling reference,
-- a hard SS N.5 violation.
--
-- Blast-radius check (Conductor-ruled precondition before this migration): grepped
-- `special_lagna_emitter.py` and `vargottama_dhana_emitter.py` (the other two
-- #1770-extension co-writers) for any `graha_dispositor_chain`/ga_structural read —
-- zero matches in either. Their declared `depends_on` ({ga_sensitive} and
-- {ga_vargas,ga_positions} respectively) already cover their actual reads exactly.
-- No fix needed for those two; not touched by this migration.
--
-- This corrects the LIVE `asset_registry.depends_on` only (migration 730's scope
-- caveat applies identically here) — the TypeScript seed file
-- (platform/scripts/seed/asset_registry_seed.ts) is left as-is per that precedent.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
SET depends_on = (
  SELECT array_agg(DISTINCT d ORDER BY d)
  FROM unnest(depends_on || ARRAY['ga_structural']) AS d
)
WHERE asset_id = 'bo_nakshatra_semantic'
  AND NOT ('ga_structural' = ANY(depends_on));

-- DOWN:
-- UPDATE asset_registry
-- SET depends_on = array_remove(depends_on, 'ga_structural')
-- WHERE asset_id = 'bo_nakshatra_semantic';
