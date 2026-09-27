-- Migration 1088 — R-6 kernel fields reach the table (synergy audit #1)
--
-- RENUMBERED 2026-09-24 (was 1085). The L0 repair branch claimed 1085 first
-- (verified first-commit times: theirs 08:54/11:21 IST, mine 11:25/11:42), and neither
-- side had applied. Under the rule the Gochara stream proposed and this stream accepts —
-- an applied migration keeps its number, otherwise first claim holds — they keep 1085.
-- Safe to renumber precisely because this file is UNAPPLIED; a migration is never
-- renumbered after it has been applied.
--
-- separate_kernel() has returned {activity, valence, applicability, availability}
-- since Phase 2a, and comparability_class / kernel_version have been set on every
-- in-memory window — but the INSERT persisted only `availability`.  The plan's
-- §4.5 never-pool rule ("kernel_version = legacy_i16 is never pooled"; "a
-- projection may rank only within one comparability class") was therefore
-- unenforceable in SQL: the discriminators did not exist as columns.
--
-- Additive only.  No existing column or table is touched, no data is rewritten.
-- Number chosen by scanning every remote branch and BOTH migration directories
-- (1071-1084 were claimed across four branches; the runner keys on filename, not
-- number, but the ordering tie-break is lexical within a number).
--
-- NOT in this migration, and deliberately: `contact_uuid` (R-5 identity).  It is
-- defined over R-3's six-component frame vector, and that vector is emitted
-- NOWHERE in engine or writer today — so a column would either sit NULL or be
-- filled from an invented frame.  Blocked on R-3 + the N-7 producer; recorded as
-- synergy finding #10.

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS activity             NUMERIC,
    ADD COLUMN IF NOT EXISTS valence              NUMERIC,
    ADD COLUMN IF NOT EXISTS applicability        JSONB,
    ADD COLUMN IF NOT EXISTS comparability_class  TEXT,
    ADD COLUMN IF NOT EXISTS kernel_version       TEXT,
    ADD COLUMN IF NOT EXISTS independence_group   TEXT;

COMMENT ON COLUMN kala_convergence.activity IS
    'R-6: non-negative geometric/clock intensity. Never pooled across kernel_version.';
COMMENT ON COLUMN kala_convergence.valence IS
    'R-6: SIGNED phala. Negative values are adverse activity, preserved — the erasure R-6 repaired.';
COMMENT ON COLUMN kala_convergence.applicability IS
    'R-6: per-method applicability map. Carried as data; never a veto (M-4).';
COMMENT ON COLUMN kala_convergence.comparability_class IS
    'R-6/§4.5: a projection may rank only WITHIN one class. Emitted as ka_sangam/<signature_class>. '
    'Rename to `comparable_with` on Gochara''s four-value enum is deferred until that enum is '
    'readable at source (its branch is unpushed) — synergy audit #2.';
COMMENT ON COLUMN kala_convergence.kernel_version IS
    'R-6/§4.5: separated_v2 | legacy_i16. Rows of different kernel_version are NEVER pooled or ranked together.';
COMMENT ON COLUMN kala_convergence.independence_group IS
    'R-6: witness-independence grouping. NULL until the engine emits it (synergy audit #5).';

CREATE INDEX IF NOT EXISTS idx_kala_convergence_kernel_class
    ON kala_convergence (chart_id, kernel_version, comparability_class);
