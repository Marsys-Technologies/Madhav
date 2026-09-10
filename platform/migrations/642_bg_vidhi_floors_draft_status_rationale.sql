-- 642_bg_vidhi_floors_draft_status_rationale.sql
--
-- NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md L0-W2 DECIDE, MUST item 2
-- (L0_W2_DECIDE_v1_0.md §2): bg_vidhi_floors is the only non-CURRENT
-- (catalog_status=DRAFT) asset among all 40 L0 assets, while its dependency
-- bg_vidhi_primitives is CURRENT. L0-W1/W2 investigated whether DRAFT is
-- accurate (genuine content immaturity) or stale (should have flipped to
-- CURRENT alongside its dependency).
--
-- Finding: DRAFT is ACCURATE, not stale. The writer's own in-code
-- provenance tags (pipeline/orchestrator/writers/bg_vidhi_floors.py) mark
-- 12 of the 14 intent floors "[MANDATORY]" (settled) but explicitly mark
-- education_deepdive and progeny_deepdive "[CANDIDATE]" (VIDHI-PURNATA P-2,
-- not yet fully ratified) -- a real, deliberate signal of partial content
-- immaturity, not an oversight. Per CLAUDE.md B.8 (registries must not
-- disagree, and status must be discoverable, not just correct), this
-- migration does NOT flip catalog_status to CURRENT -- that would be
-- fabricating settledness two floors don't have -- it instead makes the
-- rationale for DRAFT discoverable in the registry itself, so a future
-- reader does not have to re-derive it from writer source the way this
-- analysis pass had to.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
   SET english_description =
     'Per-intent-class acharya floor + machine band header + ordered floor items -- '
     || 'the compiled scope_tuple->contract input (D-2 Lane V-1). catalog_status=DRAFT '
     || 'is intentional, not stale: 12/14 intent floors are writer-tagged [MANDATORY] '
     || '(settled), but education_deepdive and progeny_deepdive remain writer-tagged '
     || '[CANDIDATE] (VIDHI-PURNATA P-2, not yet fully ratified). Re-verify against the '
     || 'writer source before flipping to CURRENT.'
 WHERE asset_id = 'bg_vidhi_floors';

COMMENT ON COLUMN asset_registry.catalog_status IS
  'DRAFT/CURRENT/RETIRED lifecycle status. A DRAFT row''s english_description should '
  'state WHY it is draft (see bg_vidhi_floors, migration 642) rather than leaving the '
  'reader to infer immaturity vs. staleness.';

-- Forward reversal (safe at any time): re-run with the original
-- english_description text restored, or DROP COMMENT ON COLUMN
-- asset_registry.catalog_status.
