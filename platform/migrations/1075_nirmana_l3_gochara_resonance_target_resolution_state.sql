-- RENUMBERED 1071->1075 on 2026-09-23: 1071/1072 and 1073/1074 were found claimed on other unmerged
-- branches (sangam/stage3 + l3/kala-elevation-readiness in platform/supabase/migrations;
-- l3/kala-p1-1-b1-clear-guard and l3/kala-p1-2-builder-grants-timeout in platform/migrations).
-- 1075/1076 were the lowest numbers free across every remote branch at renumbering time.
-- Migration 1071: gochara_resonance_map — target_resolution_state + target_qualifier
-- Created: 2026-09-23
-- WP3c (N-12 pre-approved honesty fixes R-5/R-6, GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §WP3c;
-- WP1_CONTRACTS.md §2.1 closed enum). Author: nirmana l3 autonomous gochara run.
--
-- R-6: target_resolution_state TEXT NOT NULL DEFAULT 'resolved'
--   CHECK IN ('resolved','unavailable','unqualified') — the honest null is STORED,
--   never inferred. Vocabulary pinned by WP1_CONTRACTS.md §2.1:
--     resolved    — the target-resolution contract produced a point or an interval
--     unavailable — the cited input fact/relation is absent (karaka fact missing;
--                   dangling yoga id; LAGNA fact absent; lord graha_position absent)
--     unqualified — the resolution chain exists but cannot be completed honestly
--                   (rulership row missing; mechanism operand unwired)
--   ('inapplicable' from the plan's sensitive_degree row is deliberately NOT a
--   stored state: N-12 rules that negative-result sensitive rows are REMOVED at
--   the resonance layer — WP3c R-1 — and produce zero target rows.)
--
-- R-5: target_qualifier TEXT NULL — preserves ontology qualifiers (today:
--   'afflicted' on lord refs; 'bhanga_active' on yoga_constituent firings) that
--   F-12 showed being stripped. target_ref keeps its clean natural-key form
--   ('10L', the yoga id, the chart_facts fact_id) so existing consumers reading
--   target_ref cannot break; the qualifier rides this column.
--
-- Honest-backfill note: pre-existing rows receive the DEFAULT 'resolved' as a
-- storage backfill only. Their true state is re-derived per row by the
-- ka_gochara_resonance writer (WP3c R-1..R-5 build-time validation) on the
-- next per-chart rebuild — delete-then-insert scoped to chart_id replaces the
-- whole partition, so no stale 'resolved' backfill survives one rebuild cycle.
--
-- DESIGN ARTIFACT ONLY for WP3c: this file must NEVER be applied to a real
-- database from WP3c. Application/validation against a disposable instance is
-- WP6's gate.
--
-- ROLLBACK:
--   ALTER TABLE gochara_resonance_map DROP CONSTRAINT IF EXISTS gochara_resonance_map_target_resolution_state_check;
--   ALTER TABLE gochara_resonance_map DROP COLUMN IF EXISTS target_qualifier;
--   ALTER TABLE gochara_resonance_map DROP COLUMN IF EXISTS target_resolution_state;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

ALTER TABLE gochara_resonance_map
  ADD COLUMN IF NOT EXISTS target_resolution_state TEXT NOT NULL DEFAULT 'resolved';

ALTER TABLE gochara_resonance_map
  ADD COLUMN IF NOT EXISTS target_qualifier TEXT;

COMMENT ON COLUMN gochara_resonance_map.target_resolution_state IS
  'WP3c R-6 (N-12): closed enum per WP1_CONTRACTS.md §2.1 — the honest null is stored, '
  'never inferred. resolved | unavailable (cited input fact/relation absent) | '
  'unqualified (chain exists but cannot complete honestly, e.g. rulership row '
  'missing). Negative-result sensitive_degree rows produce ZERO rows (R-1), so '
  'they have no state to store.';

COMMENT ON COLUMN gochara_resonance_map.target_qualifier IS
  'WP3c R-5 (N-12, F-12): preserved ontology qualifier — afflicted (lord refs), '
  'bhanga_active (yoga_constituent). NULL when the source carries no qualifier. '
  'target_ref intentionally keeps its clean natural-key form.';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'gochara_resonance_map_target_resolution_state_check'
  ) THEN
    ALTER TABLE gochara_resonance_map
      ADD CONSTRAINT gochara_resonance_map_target_resolution_state_check
      CHECK (target_resolution_state IN ('resolved','unavailable','unqualified'));
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE gochara_resonance_map DROP CONSTRAINT IF EXISTS gochara_resonance_map_target_resolution_state_check;
--   ALTER TABLE gochara_resonance_map DROP COLUMN IF EXISTS target_qualifier;
--   ALTER TABLE gochara_resonance_map DROP COLUMN IF EXISTS target_resolution_state;
--   COMMIT;
-- =============================================================================
