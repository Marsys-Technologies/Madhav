-- 844_nirmana_l1_ga_tajaka_volume_explanation_fix.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, fifth in the 840-859 range (adjudication #2101, L1
-- continuation 5). Closes F-E17 (L1_W1_ANALYSIS_BATCH_E.md): `ga_tajaka`'s
-- `volume_explanation` made a false claim -- "varshas outside the precomputed window are
-- computed on-demand by the retrieval tool via ga_tajaka_writer.compute_varsha()" -- but
-- `compute_varsha()` has ZERO callers (confirmed live, cycle 106: 3 repo hits total -- its own
-- `def`, its own self-referential comment, and this same seed line). `get_tajik.ts` is a pure
-- SELECT with no on-demand computation path; its own `empty_reason` honestly discloses
-- out-of-window varshas as genuinely not computed. The TOOL was already honest; only the
-- REGISTRY lied.
--
-- This migration corrects `volume_explanation` to describe the actual windowed-storage
-- behavior. `ga_tajaka_writer.py`'s own internal `storage_strategy` build-summary string (a
-- separate, matching false claim) and `platform/scripts/seed/asset_registry_seed.ts`'s seed
-- source are corrected in the same PR so the registry and its own seed source cannot drift
-- apart again. `target_floor` (240) and `count_sql` are untouched -- both already correct.

BEGIN;

UPDATE asset_registry
SET volume_explanation = 'target_floor = 240 = achieved canonical count for chart 482012f1 (2026-06-11): A7 hybrid window varsha 1..48 × 5 ayanamshas. Windowed storage — only varshas inside the precomputed window (1..48) are stored; varshas outside that window are NOT computed on-demand (get_tajik.ts honestly reports them via its own empty_reason disclosure).'
WHERE asset_id = 'ga_tajaka';

COMMIT;
