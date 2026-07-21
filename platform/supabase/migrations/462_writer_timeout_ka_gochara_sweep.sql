-- Migration 462: raise writer_timeout budget for ka_gochara_sweep
-- (D-4b readiness — materialization-completeness gate, BRIEF_D4B.md §0).
--
-- Evidence: chart 482012f1's ka_gochara_sweep rebuild has failed its
-- writer_timeout_seconds=1800 watchdog on all 11 production dispatch attempts
-- since 2026-07-19 (build_runs history). PR #675 (PERF-TRIGGER-CACHE:
-- memoized _fetch_kakshya_boundaries/_fetch_vedha_rules, the same defect
-- class as PR #670's earlier _fetch_av_gate_rows/_fetch_sade_sati_rows fix)
-- measured a real 3x improvement on live re-verification (build_run
-- c74b50f2, deployed image 5132b5bc): 3 substeps committed in ~30 min,
-- vs. ~1 substep/30min pre-fix -- but still hit the same 1800s ceiling
-- before a 4th substep could complete, with ~294 of ~300 planned substeps
-- still remaining. Cloud Run's own job task timeout is 86400s (24h,
-- `gcloud run jobs describe brahma-build-pipeline-job`), far above this
-- 1800s app-level watchdog -- the watchdog, not the platform, is now the
-- binding constraint on how many substeps one dispatch can complete.
--
-- Fix: raise to 21600s (6h), well within the 24h job ceiling, mirroring
-- migration 420's precedent (ka_sangam/bo_laksana budget bumps for the
-- same class of issue: real, correctness-preserving compute that simply
-- needs more wall-clock than the default budget assumed, not a hang to
-- guard against more tightly). This does not change the writer's own
-- code path, resumption semantics, or the per-substep commit discipline
-- (§N.3 delete-then-insert via build_substep_progress) -- only how long
-- the orchestrator lets the asset run before evicting it.

BEGIN;

UPDATE asset_registry SET writer_timeout_seconds = 21600 WHERE asset_id = 'ka_gochara_sweep';

COMMIT;

-- DOWN:
-- UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id = 'ka_gochara_sweep';
