-- Migration 412: BA Phase 2.5 fast-follow #4 — bo_upaya real resonance inputs.
--
-- bo_upaya (Remediation Map / RM) now reads 3 tables it previously did not
-- declare as dependencies, in order to wire real already-computed values into
-- 3 of the 5 resonance_score_v1 inputs that were hardcoded to 0.0 (dispositor
-- chain weakness, dasha-timing proximity, CGM motif weakness):
--
--   1. chart_facts rows with fact_category = 'composite_dispositor_strength'
--      (owned by ga_structural) — dispositor_chain_weakness.
--   2. chart_dashas (owned by ga_dashas, GA7) — dasha_proximity_activation_score,
--      same covering-interval query pattern as ga_sade_sati_writer.py's
--      _lookup_dasha_lord_at().
--   3. bodha_cgm_motifs (owned by bo_cgm_motifs) — cgm_motifs_weakest_node.
--
-- The other 2 hardcoded inputs (cancellation_burden, cdlm_weakest_constituent_count)
-- have no already-computed source anywhere in the codebase yet and remain honest
-- 0.0 placeholders (documented in bo_upaya.py inline comments + ephemeris_audit_jsonb;
-- no depends_on change needed for them).
--
-- Same registry-only correction pattern as migration 406
-- (BA_FULL_ASSET_AUDIT depends_on completeness pass). No writer behavior change
-- from this migration itself — bo_upaya.py's code change is the behavior change;
-- this migration only makes the DAG edges honest.
--
-- Idempotent (UPDATE by asset_id; re-running sets the same array).
-- Applied surgically — never via deploy.yml. No rebuild triggered by this migration.

BEGIN;

UPDATE asset_registry
   SET depends_on = ARRAY['bo_laksana', 'bo_sangati', 'ga_structural', 'ga_dashas', 'bo_cgm_motifs']::text[]
 WHERE asset_id = 'bo_upaya';

COMMIT;
