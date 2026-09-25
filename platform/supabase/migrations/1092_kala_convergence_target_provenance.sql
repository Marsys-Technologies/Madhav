-- Migration 1092 — R-1 target provenance + availability persistence for ka_sangam
-- RENUMBERED 1071 -> 1092 on 2026-09-25 (native decision 15). The Gochara branch claimed 1071 for
-- a different migration; two files, one number, two unmerged branches. Neither was applied, so the
-- protocol's remedy is a renumber to max+1 across BOTH migration directories (1091 -> 1092), not a
-- disclosed exception, which is reserved for collisions whose files are already applied.
-- The SQL body is unchanged; only the number and this note moved.

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS target_provenance JSONB,
    ADD COLUMN IF NOT EXISTS availability JSONB;

COMMENT ON COLUMN kala_convergence.target_provenance IS
    'R-1 (RR-03): sourced target metadata (fact_id, type, frame, ayanamsha_id, derivation) from L1 chart_facts.';

COMMENT ON COLUMN kala_convergence.availability IS
    'R-1/R-6: per-window availability states (target, dasha, vedha, transit_search) — honest data lineage.';
