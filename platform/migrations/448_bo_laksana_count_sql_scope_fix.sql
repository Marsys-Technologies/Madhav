-- Migration 448: tighten bo_laksana.count_sql to bo_laksana-owned classes only (F2)
-- Created: 2026-07-16
--
-- F2 (orchestrator state-commit race verifier finding, carried at BIND_D-2.md
-- §B.3 / §B.1 check 5, assigned to V-4 ledger row 40): bo_laksana's
-- asset_registry.count_sql was
--   SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1
-- which counts EVERY row in the shared bodha_msr_signals table for the chart,
-- including bo_sudarshana's sudarshana_agreement rows (and any future sibling
-- writer's rows) that bo_laksana does not own and does not delete. Same class
-- of defect as PR #574's delete-scope bug, on the count side: the cockpit-truth
-- count for bo_laksana would silently include another writer's output.
--
-- Fix: scope count_sql to exactly BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES (the
-- closed allowlist already defined and used by bo_laksana.py's delete-then-
-- insert idempotency helper — see bo_laksana.py module docstring / migration
-- history for the D-1.5b full-rebuild post-mortem this allowlist was built
-- to fix on the delete side). This migration applies the same allowlist to
-- the count side.

BEGIN;

UPDATE asset_registry
   SET count_sql = $sql$SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ANY(ARRAY[
     'yoga','dosha','sade_sati','panchanga','karaka_alignment','tradition_specific',
     'parivartana','configuration','varga_pattern','annual','medical','vastu',
     'composite_state','varga_ratification_divergence','bhavat_bhavam_amplifier'
   ])$sql$
 WHERE asset_id = 'bo_laksana';

COMMIT;
