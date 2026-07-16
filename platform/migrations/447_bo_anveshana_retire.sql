-- Migration 447: bo_anveshana retirement (CR-78, D-2 Lane V-4) — PARKED
-- Created: 2026-07-16
--
-- CR-78 originally asked for bo_anveshana (Discovery Engine) to be retired —
-- discoveries become mechanism-derived (bo_yantra_mechanism, migration 445).
--
-- DISPOSITION: PARKED, not executed (CONDUCTOR_PROTOCOL §4.3 PARK class 2/3).
-- Live read-only probe (postgres, this session) found:
--   SELECT asset_id FROM asset_registry WHERE depends_on @> ARRAY['bo_anveshana']
--   -> bo_chart_gestalt, bo_pramana_mapa, ph_nimitta
-- All three are OUTSIDE V-4's may_touch glob. Deactivating bo_anveshana
-- (has_writer=false) without first confirming (a) the orchestrator's
-- dependency resolution tolerates a depends_on edge onto a has_writer=false
-- asset without a DEP-ASSERT, and (b) whether those three writers actually
-- CONSUME bodha_discoveries/bodha_anomalies rows (vs. only using bo_anveshana
-- for build-ordering) risks breaking three live downstream writers this lane
-- cannot repoint (their files are not in V-4's may_touch glob). That is
-- exactly the class of destructive/irreversible, outside-idempotent-pattern,
-- cross-lane-breaking change CONDUCTOR_PROTOCOL §4.3 requires STOPPING and
-- flagging rather than improvising.
--
-- This migration deliberately makes NO functional change: bo_anveshana keeps
-- building as before (see bo_anveshana.py's run() — the deprecation guard
-- originally drafted for this migration was REVERTED in the same commit for
-- the reason above). It records the finding as a durable, guard-reviewable
-- comment so the next session (native or D-3) has the exact blocking fact
-- without re-deriving it.
--
-- Full CR-78 retirement requires, in order: (1) confirm/repoint
-- bo_chart_gestalt / bo_pramana_mapa / ph_nimitta's actual data dependency
-- (read bodha_discoveries/bodha_anomalies vs. depends_on-only) onto
-- bo_yantra_mechanism where they truly consume discovery data; (2) THEN set
-- bo_anveshana.has_writer=false and update the three depends_on arrays in the
-- same migration; (3) THEN disposition existing bodha_discoveries/
-- bodha_anomalies rows (a bulk multi-chart purge remains its own PARK-class
-- decision, native-visible, not auto-adjudicated).

BEGIN;

COMMENT ON TABLE bodha_discoveries IS
  'CR-78 (D-2 Lane V-4, migration 447): retirement PARKED, not executed — '
  'bo_chart_gestalt / bo_pramana_mapa / ph_nimitta still depends_on bo_anveshana '
  'and are outside V-4''s may_touch glob. bo_anveshana keeps building as before. '
  'Discoveries are INTENDED to become mechanism-derived via bo_yantra_mechanism '
  '(migration 445) once the three downstream consumers are repointed — not yet done.';

COMMENT ON TABLE bodha_anomalies IS
  'CR-78 (D-2 Lane V-4, migration 447): retirement PARKED, not executed — see '
  'bodha_discoveries comment for the full disposition and blocking finding.';

COMMIT;
