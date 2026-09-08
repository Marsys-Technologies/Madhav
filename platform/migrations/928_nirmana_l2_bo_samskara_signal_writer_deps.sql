-- 928_nirmana_l2_bo_samskara_signal_writer_deps.sql
--
-- NIRMĀṆA L2 Bodha — issue #2434 (Conductor ruling, cycle 225, 2026-09-08 ~11:21Z), item (b).
--
-- Discharges the durable half of the signal-embedding cascade gap: any bodha_msr_signals
-- writer's delete-then-insert rebuild (§N.3) silently strands its rows in
-- bodha_signal_embeddings, because bo_samskara (the embedding writer) only declared
-- `depends_on: [bo_laksana]` — a sibling signal-writer rebuilding does not re-trigger it.
-- Item (a) of the same ruling (RESOLUTION_L2 v3.4, drain-order: bo_samskara now runs LAST
-- in each wave) is the stopgap that stops the gap from widening; this migration is the
-- structural fix the ruling authorized L2 to implement — the orchestrator itself now
-- re-triggers embedding regeneration after any of these siblings rebuilds.
--
-- Verified against the live registry (`asset_registry.target_table = 'bodha_msr_signals'`)
-- which bodha_msr_signals writers besides bo_laksana itself (already declared) actually
-- INSERT/DELETE rows rather than only UPDATE in place:
--   - bo_arudha, bo_special_lagna, bo_nakshatra_semantic, bo_sudarshana,
--     bo_vargottama_dhana — all five named explicitly in the ruling; confirmed real
--     bodha_msr_signals producers via asset_registry.target_table.
--   - bo_laksana_rerank — also targets bodha_msr_signals, but its own docstring
--     (BoLaksanaRerankWriter, pipeline/orchestrator/writers/bo_laksana.py) states
--     "UPDATE-only; never deletes or re-inserts bodha_msr_signals rows" — confirmed by
--     reading its run() body (UPDATE ... WHERE signal_id = %s only, no INSERT/DELETE).
--     No new/changed signal_ids means no embedding-FK cascade; correctly excluded.
--
-- This corrects the LIVE `asset_registry.depends_on` only, following the established
-- precedent of migrations 676/730/913: the TypeScript seed file
-- (platform/scripts/seed/asset_registry_seed.ts) is deliberately left as-is — the seed
-- file is the as-originally-authored record; migrations are the living correction layer.
--
-- Item (c) of the ruling (idempotent backfill of the 149 currently-unembedded signals)
-- is explicitly sequenced AFTER this migration lands AND bo_nakshatra_semantic unblocks
-- (PR #2440) — not performed here.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
SET depends_on = (
  SELECT array_agg(DISTINCT d ORDER BY d)
  FROM unnest(depends_on || ARRAY[
    'bo_arudha', 'bo_special_lagna', 'bo_nakshatra_semantic',
    'bo_sudarshana', 'bo_vargottama_dhana'
  ]) AS d
)
WHERE asset_id = 'bo_samskara';

-- DOWN:
-- UPDATE asset_registry
-- SET depends_on = array_remove(array_remove(array_remove(array_remove(array_remove(
--   depends_on, 'bo_arudha'), 'bo_special_lagna'), 'bo_nakshatra_semantic'),
--   'bo_sudarshana'), 'bo_vargottama_dhana')
-- WHERE asset_id = 'bo_samskara';
