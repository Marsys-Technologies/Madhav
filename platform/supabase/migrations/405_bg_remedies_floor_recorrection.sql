-- 405_bg_remedies_floor_recorrection.sql
-- =============================================================================
-- Re-correct asset_registry.target_floor for bg_remedies back to its achieved
-- row count (266), after it drifted back to a stale aspirational value (800)
-- despite migration 231 (2026-06-16) already fixing it once.
--
-- Root cause: scripts/seed/asset_registry_seed.ts hardcoded target_floor: 800
-- for bg_remedies (a "cross-text remedy universe target" narrative that
-- predates the writer's actual design). Whenever that seed script is re-run
-- (setup/reseed), it overwrites the corrected value with the stale 800,
-- silently undoing migration 231. The seed script itself is fixed in the same
-- audit pass (target_floor: 266 + updated volume_explanation) so this cannot
-- recur; this migration is the complementary live-data hygiene fix.
--
-- brahma_remedy_corpus is a deliberately fixed, ZERO-LLM, ZERO-fabrication
-- deterministic corpus per the writer's own docstring
-- (pipeline/orchestrator/writers/bg_remedies.py):
--   gen_planet_matrix()  → 108 rows
--   DOSHA_REMEDIES       → 102 rows
--   LEGACY_REMEDIES      →  54 rows
--   + corpus_sweep net-new (migrations 192/199/231)
-- Measured live count (2026-07-05): 266 rows — the writer's designed ceiling.
--
-- Per CLAUDE.md §N.4: target_floor = achieved count after build, never a
-- fabrication target. 800 was never reachable by this writer's design.
--
-- Idempotent (UPDATE by asset_id; re-running sets the same value).
-- Applied surgically — never via deploy.yml.
-- =============================================================================

BEGIN;

UPDATE asset_registry
   SET target_floor = 266,
       volume_explanation = '266 remedies = writer''s designed deterministic ceiling: '
                         || 'gen_planet_matrix(108) + dosha-linked(102) + legacy(54) + '
                         || 'corpus_sweep net-new(2). Floor = achieved count per '
                         || 'floors-are-aspirational policy (CLAUDE.md §N.4); ZERO LLM, '
                         || 'ZERO fabrication is a hard writer constraint, so this floor '
                         || 'cannot be raised without a native-judgment decision to expand '
                         || 'the deterministic corpus design. Re-corrected 2026-07-05 after '
                         || 'drifting back to a stale 800 via asset_registry_seed.ts.'
 WHERE asset_id = 'bg_remedies';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--
-- BEGIN;
-- UPDATE asset_registry SET target_floor = 800 WHERE asset_id = 'bg_remedies';
-- COMMIT;
-- =============================================================================
