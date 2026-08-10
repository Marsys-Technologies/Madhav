-- Migration 558: kala_gochara_windows_v2 — W1.4 self-normalizing threshold provenance columns
-- =============================================================================
-- GOCHARA-UTKARSHA campaign, wave W1.4 (self-normalizing thresholds).
--
-- WHY: v1's activation threshold was a fixed β×X crossing that caused windows
-- approximately every 9 days per class — astronomically impossible. W1.4 fixes
-- this by computing an activation threshold as the Pth percentile of the
-- chart's own λ_v3 distribution over a century-scale horizon, where P is
-- derived from brahma_event_ontology.base_rate_by_age (age-appropriate).
--
-- WHAT: four provenance columns on kala_gochara_windows_v2 capturing exactly
-- how the threshold was computed for each (chart × class) build:
--
--   threshold_percentile  NUMERIC(8,6)
--       The percentile P ∈ [0,1] of the century-scale λ_v3 distribution used
--       as the activation threshold. Derived from: P = 1 − base_rate × Δt.
--
--   threshold_lambda      NUMERIC(12,8)
--       The λ_thresh value = percentile P of the distribution. A JD is
--       considered "active" iff λ_v3 ≥ λ_thresh.
--
--   implied_density       NUMERIC(10,4)
--       Windows/year implied by this threshold on this chart×class, estimated
--       from the century sample: (fraction of samples ≥ λ_thresh) × 52.
--       >52 → density_flag='pathological_dense'; 0 on nonzero base_rate →
--       density_flag='starved'.
--
--   base_rate_cited       NUMERIC(8,6)
--       The normalized age-band base rate from brahma_event_ontology.
--       base_rate_by_age that drove P. age bracket 35–50 → band_41_60 for
--       the native (age ~42 at evaluation time).
--
-- All four are NULLABLE: existing rows written before this migration (and any
-- writer operating in v1_parity_mode=True) do not carry threshold provenance
-- and are honestly represented as NULL rather than fabricated values.
--
-- The density_flag is stored in the suppression_state JSONB column (already
-- exists) as a sub-key 'w14_density_flag', keeping the schema extension
-- backward-compatible with the equivalence-report tool's column expectations.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS. Safe to re-run.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── Add W1.4 threshold provenance columns ─────────────────────────────────

ALTER TABLE kala_gochara_windows_v2
  ADD COLUMN IF NOT EXISTS threshold_percentile NUMERIC(8,6),
  ADD COLUMN IF NOT EXISTS threshold_lambda     NUMERIC(12,8),
  ADD COLUMN IF NOT EXISTS implied_density      NUMERIC(10,4),
  ADD COLUMN IF NOT EXISTS base_rate_cited      NUMERIC(8,6);

COMMENT ON COLUMN kala_gochara_windows_v2.threshold_percentile IS
  'W1.4 self-normalizing threshold: percentile P ∈ [0,1] of the century-scale '
  'λ_v3 distribution used as the activation threshold. '
  'Derived from P = 1 − base_rate_cited × Δt (Δt = 1/52 yr). '
  'NULL for rows written before W1.4 or in v1_parity_mode.';

COMMENT ON COLUMN kala_gochara_windows_v2.threshold_lambda IS
  'W1.4: λ_thresh = percentile(P) of the century-scale λ_v3 distribution. '
  'A JD is "active" iff λ_v3 ≥ threshold_lambda. In [0,1]. '
  'NULL for pre-W1.4 rows or v1_parity_mode rows.';

COMMENT ON COLUMN kala_gochara_windows_v2.implied_density IS
  'W1.4: windows/year implied by threshold_lambda on this chart×class, '
  'estimated from the century sample. >52 → density_flag pathological_dense '
  '(v1 pathology); 0 on nonzero base_rate → density_flag starved. '
  'NULL for pre-W1.4 rows.';

COMMENT ON COLUMN kala_gochara_windows_v2.base_rate_cited IS
  'W1.4: normalized age-band base rate from brahma_event_ontology. '
  'base_rate_by_age that drove threshold_percentile. '
  'band_41_60 for native age ~42 at evaluation time. '
  'NULL for pre-W1.4 rows or fallback-only rows.';

COMMIT;
