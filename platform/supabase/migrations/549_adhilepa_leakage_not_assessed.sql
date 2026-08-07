-- Migration 547: adhilepa overlay tables — permit 'not_assessed' leakage_status
-- SIDDHANTA Phase 2 (lane-p2-adhilepa-fix).
--
-- Root cause:
--   mi_adhilepa._overlay_row() correctly sets leakage = None per §N.7
--   ("a verification flag must have a real detector behind it, or be null"),
--   but mimamsa_signal_adjustment.leakage_status (and the three sibling overlay
--   tables) are defined as text NOT NULL (migration 350), a constraint that
--   existed only because the old code always wrote "clean" — a lie (no leakage
--   detector exists). The honest null was therefore forbidden by a schema
--   encoding the dishonest assumption.
--
--   All FOUR overlay tables share this defect:
--     mimamsa_signal_adjustment
--     mimamsa_fact_adjustment
--     mimamsa_convergence_adjustment
--     mimamsa_anchor_adjustment
--
-- Fix:
--   Add 'not_assessed' as the explicit honest named state (preferred over bare
--   NULL per the kala_lattice_query.ts precedent at line 364-376: explicit name
--   > bare null for serving-layer consumers). Set it as the column DEFAULT so
--   writers that omit leakage_status get the honest value automatically.
--   Backfill any existing NULL or "clean" rows to 'not_assessed'.
--   Restore NOT NULL with the new default.
--
-- Vocabulary (recorded in COMMENT):
--   'not_assessed' — no leakage detector has run (§N.7/§N.8 honest state); DEFAULT.
--   'clean'        — detector ran and found no leakage.
--   'leaked'       — detector ran and found leakage; row excluded from calibration.
--
-- Companion writer fix (Part b): mi_adhilepa._overlay_row() now emits
--   leakage = "not_assessed" instead of None.
-- Companion consumer fix (Part c): mi_gunanaka's calibration-evidence loop
--   only excludes rows where leakage_status = 'leaked'; 'not_assessed' and
--   'clean' rows are both admitted (§N.8 Earned-Signal Principle).

BEGIN;

-- Part (a-1): Temporarily allow NULLs so we can update existing rows.
ALTER TABLE mimamsa_signal_adjustment ALTER COLUMN leakage_status DROP NOT NULL;
ALTER TABLE mimamsa_fact_adjustment ALTER COLUMN leakage_status DROP NOT NULL;
ALTER TABLE mimamsa_convergence_adjustment ALTER COLUMN leakage_status DROP NOT NULL;
ALTER TABLE mimamsa_anchor_adjustment ALTER COLUMN leakage_status DROP NOT NULL;

-- Part (a-2): Backfill existing NULL or "clean" rows to the honest state.
-- NULL rows: previously blocked by NOT NULL, now visible; set honest state.
-- "clean" rows: were written by the old code without any real detector behind
--   them — they are 'not_assessed' by the §N.8 earned-signal principle.
UPDATE mimamsa_signal_adjustment
    SET leakage_status = 'not_assessed'
    WHERE leakage_status IS NULL OR leakage_status = 'clean';

UPDATE mimamsa_fact_adjustment
    SET leakage_status = 'not_assessed'
    WHERE leakage_status IS NULL OR leakage_status = 'clean';

UPDATE mimamsa_convergence_adjustment
    SET leakage_status = 'not_assessed'
    WHERE leakage_status IS NULL OR leakage_status = 'clean';

UPDATE mimamsa_anchor_adjustment
    SET leakage_status = 'not_assessed'
    WHERE leakage_status IS NULL OR leakage_status = 'clean';

-- Part (a-3): Set DEFAULT and restore NOT NULL with the honest default.
ALTER TABLE mimamsa_signal_adjustment
    ALTER COLUMN leakage_status SET DEFAULT 'not_assessed';
ALTER TABLE mimamsa_fact_adjustment
    ALTER COLUMN leakage_status SET DEFAULT 'not_assessed';
ALTER TABLE mimamsa_convergence_adjustment
    ALTER COLUMN leakage_status SET DEFAULT 'not_assessed';
ALTER TABLE mimamsa_anchor_adjustment
    ALTER COLUMN leakage_status SET DEFAULT 'not_assessed';

ALTER TABLE mimamsa_signal_adjustment ALTER COLUMN leakage_status SET NOT NULL;
ALTER TABLE mimamsa_fact_adjustment ALTER COLUMN leakage_status SET NOT NULL;
ALTER TABLE mimamsa_convergence_adjustment ALTER COLUMN leakage_status SET NOT NULL;
ALTER TABLE mimamsa_anchor_adjustment ALTER COLUMN leakage_status SET NOT NULL;

-- Part (a-4): Document the vocabulary on each table.
COMMENT ON COLUMN mimamsa_signal_adjustment.leakage_status IS
  'Leakage detection status: ''not_assessed'' (no detector exists — §N.7/§N.8 honest state; DEFAULT), '
  '''clean'' (detector ran and found no leakage), ''leaked'' (detector found leakage — excluded from calibration). '
  'Honest-until-proven-clean: default is not_assessed, not clean.';

COMMENT ON COLUMN mimamsa_fact_adjustment.leakage_status IS
  'Leakage detection status: ''not_assessed'' (no detector exists — §N.7/§N.8 honest state; DEFAULT), '
  '''clean'' (detector ran and found no leakage), ''leaked'' (detector found leakage — excluded from calibration). '
  'Honest-until-proven-clean: default is not_assessed, not clean.';

COMMENT ON COLUMN mimamsa_convergence_adjustment.leakage_status IS
  'Leakage detection status: ''not_assessed'' (no detector exists — §N.7/§N.8 honest state; DEFAULT), '
  '''clean'' (detector ran and found no leakage), ''leaked'' (detector found leakage — excluded from calibration). '
  'Honest-until-proven-clean: default is not_assessed, not clean.';

COMMENT ON COLUMN mimamsa_anchor_adjustment.leakage_status IS
  'Leakage detection status: ''not_assessed'' (no detector exists — §N.7/§N.8 honest state; DEFAULT), '
  '''clean'' (detector ran and found no leakage), ''leaked'' (detector found leakage — excluded from calibration). '
  'Honest-until-proven-clean: default is not_assessed, not clean.';

COMMIT;

-- DOWN (rollback): revert to NOT NULL without default, backfill to "clean".
-- WARNING: this restores the dishonest default. Only use for emergency rollback.
-- To reverse this migration, run:
--
--   BEGIN;
--   ALTER TABLE mimamsa_signal_adjustment ALTER COLUMN leakage_status DROP DEFAULT;
--   ALTER TABLE mimamsa_fact_adjustment ALTER COLUMN leakage_status DROP DEFAULT;
--   ALTER TABLE mimamsa_convergence_adjustment ALTER COLUMN leakage_status DROP DEFAULT;
--   ALTER TABLE mimamsa_anchor_adjustment ALTER COLUMN leakage_status DROP DEFAULT;
--   UPDATE mimamsa_signal_adjustment SET leakage_status = 'clean' WHERE leakage_status = 'not_assessed';
--   UPDATE mimamsa_fact_adjustment SET leakage_status = 'clean' WHERE leakage_status = 'not_assessed';
--   UPDATE mimamsa_convergence_adjustment SET leakage_status = 'clean' WHERE leakage_status = 'not_assessed';
--   UPDATE mimamsa_anchor_adjustment SET leakage_status = 'clean' WHERE leakage_status = 'not_assessed';
--   COMMIT;
