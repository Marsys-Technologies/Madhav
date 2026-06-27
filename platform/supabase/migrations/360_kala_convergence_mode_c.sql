-- Migration 360: allow Mode 'C' in kala_convergence.mode
--
-- ka_sangam's convergence engine was extended (L3-Kāla completeness audit D-series) to emit
-- Mode C = SUBSYSTEM convergence (mode_c_subsystem_period), alongside the original Mode A
-- (transit search) and Mode B (sweep). The kala_convergence_mode_check constraint predates
-- Mode C and only permitted ('A','B'), so ka_sangam's first Mode-C insert raised
-- CheckViolation — failing the whole Kāla→Phala→Mīmāṃsā chain (now caught loudly by the
-- orchestrator upstream gate instead of cascading silently).
--
-- The writer is correct; the constraint is stale. Widen it to include 'C'. Idempotent.

ALTER TABLE kala_convergence DROP CONSTRAINT IF EXISTS kala_convergence_mode_check;
ALTER TABLE kala_convergence
  ADD CONSTRAINT kala_convergence_mode_check
  CHECK (mode = ANY (ARRAY['A'::text, 'B'::text, 'C'::text]));
