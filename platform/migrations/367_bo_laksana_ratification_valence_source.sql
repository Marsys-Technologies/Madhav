-- Migration 367: Night-1 Lane 4 (MSR elevation) — bodha_msr_signals columns
-- for ratification-aware weighting (CR-82→CR-65) and judged-valence source
-- tagging (CR-83/CR-42 class: no silent fallback).
--
-- Additive-only, idempotent — safe to re-apply.
--
-- NOTE (LANE2 dependency, verified 2026-07-14): the DAG addition specified by
-- the brief ("bo_laksana.depends_on must gain ga_vichara") is DEFERRED, not
-- applied here. ga_vichara / chart_vichara do not exist anywhere in this
-- campaign's worktrees (LANE2 never built — see Lane 4 handback report).
-- Adding a depends_on edge to a non-existent asset_id would poison the
-- orchestrator's topo-sort for every future build. bo_laksana.py's new
-- loaders (_load_varga_ratification, _load_vichara_valence) are defensive —
-- they degrade to empty/neutral whenever chart_vichara is absent, so this
-- migration is safe to ship standalone. Whoever lands LANE2 must add the
-- depends_on edge (asset_registry + asset_registry_seed.ts) in that same
-- change — do not add it here without the table existing.

BEGIN;

ALTER TABLE bodha_msr_signals ADD COLUMN IF NOT EXISTS ratification_factor numeric;
ALTER TABLE bodha_msr_signals ADD COLUMN IF NOT EXISTS valence_source text;

COMMENT ON COLUMN bodha_msr_signals.ratification_factor IS
  'CR-82->CR-65 (Night-1 Lane 4): multiplier in [0.6,1.4] applied to a per-varga '
  'fact''s salience based on cross-varga agreement (chart_vichara varga_ratification '
  'rows, LANE2 output). NULL = no ratification row matched (neutral / LANE2 not yet '
  'built) -- never a silently-guessed value.';

COMMENT ON COLUMN bodha_msr_signals.valence_source IS
  'CR-83/CR-42 class (Night-1 Lane 4): provenance of the valence column. '
  '''ga_vichara_v1'' = judged valence from chart_vichara valence_pass (LANE2 output); '
  '''keyword_heuristic_v1'' = pre-existing category/substring fallback. Every row '
  'carries one of these two values -- no silent degradation.';

COMMIT;
