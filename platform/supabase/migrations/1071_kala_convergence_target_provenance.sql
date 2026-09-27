-- Migration 1071 — R-1 target provenance + availability persistence for ka_sangam

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS target_provenance JSONB,
    ADD COLUMN IF NOT EXISTS availability JSONB;

COMMENT ON COLUMN kala_convergence.target_provenance IS
    'R-1 (RR-03): sourced target metadata (fact_id, type, frame, ayanamsha_id, derivation) from L1 chart_facts.';

COMMENT ON COLUMN kala_convergence.availability IS
    'R-1/R-6: per-window availability states (target, dasha, vedha, transit_search) — honest data lineage.';
