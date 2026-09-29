-- Migration 1087: kala_gochara_contacts inclusivity + completeness_state CHECK +
--                 time_basis CHECK + tier_basis; kala_gochara_coverage fourth
--                 partition_kind (§12.3 tasks 4.13a–d; GOCHARA_NATIVE_RULINGS_
--                 2026-09-24_v1_0.md §1 D-S1/D-S2).
-- Created: 2026-09-24. Author: nirmana l3 autonomous gochara run.
--
-- Numbering: 1087 is the lowest free number by a fresh scan of every
-- origin/* head across both migration directories plus the local head
-- (this family 1080–1084+1086, Saṅgam 1088–1090, 1085 retired per E-010),
-- followed by a MIG-1 guard run (npm run guard:migration-numbers: PASS).
-- Record: ESCALATIONS.md E-011.
--
-- DESIGN ARTIFACT: applied ONLY to the disposable WP6 database (docker
-- gochara-wp6-disposable), after 1081. It must NEVER be applied to a shared
-- or production database; production application is WP10-gated. 1081 has
-- never been applied outside a disposable DB, so the rename half of §12.3
-- (4.13e, claim_grain -> precision_regime) is an in-place edit of 1081 and
-- deliberately NOT in this file.
--
-- ROLLBACK (down-migration):
--   ALTER TABLE kala_gochara_coverage DROP CONSTRAINT IF EXISTS kgcov_partition_kind_ck;
--   ALTER TABLE kala_gochara_coverage ADD CONSTRAINT kala_gochara_coverage_partition_kind_check
--     CHECK (partition_kind IN ('body_target','event_class','moon_on_demand'));
--   ALTER TABLE kala_gochara_contacts DROP CONSTRAINT IF EXISTS kgc_tier_basis_ck;
--   ALTER TABLE kala_gochara_contacts DROP COLUMN IF EXISTS tier_basis;
--   ALTER TABLE kala_gochara_contacts DROP CONSTRAINT IF EXISTS kgc_time_basis_ck;
--   ALTER TABLE kala_gochara_contacts DROP CONSTRAINT IF EXISTS kgc_completeness_state_ck;
--   ALTER TABLE kala_gochara_contacts DROP CONSTRAINT IF EXISTS kgc_inclusivity_ck;
--   ALTER TABLE kala_gochara_contacts DROP COLUMN IF EXISTS inclusivity;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── 4.13b (D-S1(b)): interval inclusivity ───────────────────────────────────
-- t_in and t_out are both in-orb threshold-crossing instants, so every episode
-- interval this family writes is closed at both ends. The alternative is kept
-- in the enum so a future boundary-shaped relation can declare itself instead
-- of overloading NULL.
ALTER TABLE kala_gochara_contacts
  ADD COLUMN IF NOT EXISTS inclusivity TEXT NOT NULL DEFAULT 'closed_closed';
ALTER TABLE kala_gochara_contacts
  DROP CONSTRAINT IF EXISTS kgc_inclusivity_ck;
ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kgc_inclusivity_ck
  CHECK (inclusivity IN ('closed_closed', 'closed_open'));

-- ── 4.13c (D-S2): completeness_state is the closed six-state F06 set ────────
-- The pre-CHECK code emitted 'qualified'; D-S2 migrates that live value to
-- 'applied'. 'inapplicable' is deliberately NOT added to
-- target_resolution_state (N-12 / WP3c R-1 stands).
ALTER TABLE kala_gochara_contacts
  DROP CONSTRAINT IF EXISTS kgc_completeness_state_ck;
ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kgc_completeness_state_ck
  CHECK (completeness_state IN (
    'applied', 'inapplicable', 'unavailable',
    'unqualified', 'contradictory_unresolved', 'unexplored'
  ));

-- ── 4.13d (D-S2): time_basis CHECK + tier_basis ─────────────────────────────
-- time_basis: closed vocabulary pinned at WP1_CONTRACTS.md §3.1. The set has
-- exactly one member today — every contact instant this family writes is the
-- event's UTC instant; a second basis is a contract amendment, not a free
-- string.
ALTER TABLE kala_gochara_contacts
  DROP CONSTRAINT IF EXISTS kgc_time_basis_ck;
ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kgc_time_basis_ck
  CHECK (time_basis IN ('event_time_utc'));

-- tier_basis: 'relative_uncalibrated', or 'calibrated:<gate_id>' naming the
-- gate whose evidence calibrated the row. NULL means no tier claim is made.
ALTER TABLE kala_gochara_contacts
  ADD COLUMN IF NOT EXISTS tier_basis TEXT;
ALTER TABLE kala_gochara_contacts
  DROP CONSTRAINT IF EXISTS kgc_tier_basis_ck;
ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kgc_tier_basis_ck
  CHECK (tier_basis = 'relative_uncalibrated' OR tier_basis ~ '^calibrated:.+$');

-- ── 4.13a (D-S1(a)): fourth coverage partition kind ─────────────────────────
-- find_episodes returns a coverage object on EVERY branch. The non-Moon
-- on-demand branch is interval-scoped like the Moon one, so it gets a
-- symmetric kind rather than per-body body_target rows: a zero-contact search
-- has no bodies to partition by, and mixing live-search coverage into the
-- build manifest's body_target partitions would corrupt its semantics.
ALTER TABLE kala_gochara_coverage
  DROP CONSTRAINT IF EXISTS kala_gochara_coverage_partition_kind_check;
ALTER TABLE kala_gochara_coverage
  DROP CONSTRAINT IF EXISTS kgcov_partition_kind_ck;
ALTER TABLE kala_gochara_coverage
  ADD CONSTRAINT kgcov_partition_kind_ck
  CHECK (partition_kind IN ('body_target', 'event_class', 'moon_on_demand',
                            'bodies_on_demand'));

COMMENT ON COLUMN kala_gochara_contacts.inclusivity IS
  'Interval inclusivity of [t_in, t_out] (D-S1(b)): closed_closed — both are '
  'in-orb threshold crossings; closed_open reserved for future boundary shapes.';
COMMENT ON COLUMN kala_gochara_contacts.tier_basis IS
  'Calibration tier of the row (D-S2): relative_uncalibrated, or '
  'calibrated:<gate_id> naming the calibrating gate. NULL = no tier claim.';
COMMENT ON COLUMN kala_gochara_coverage.partition_kind IS
  'body_target | event_class | moon_on_demand | bodies_on_demand (D-S1(a): the '
  'non-Moon on-demand interval search is first-class coverage).';

COMMIT;
