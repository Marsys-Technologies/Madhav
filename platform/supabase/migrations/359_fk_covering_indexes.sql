-- Migration 359: index every foreign-key column that lacks a supporting index
--
-- Postgres does NOT auto-create an index on the REFERENCING side of a foreign key.
-- When a parent row is deleted, every child table is checked for rows referencing it;
-- if the child's FK column has no leading-column index, that check is a SEQUENTIAL SCAN
-- of the entire child table, PER deleted parent row. With large children this makes a
-- delete catastrophically slow (O(deleted_parents × child_rows)).
--
-- Observed impact: a `DELETE FROM bodha_msr_signals WHERE chart_id = $1` (58k rows) hung
-- for 5+ minutes because kala_activation (66k rows), kala_bhavishya and kala_darshana had
-- no usable signal_id index — so the global clear (and any delete-then-insert rebuild of
-- these tables) stalled and left rows behind.
--
-- These indexes make parent deletes index-lookups instead of seq scans. Idempotent.

-- ── children of bodha_msr_signals (signal_id) ────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_kala_activation_signal_id_fk        ON kala_activation (signal_id);
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_signal_id_fk         ON kala_bhavishya (signal_id);
CREATE INDEX IF NOT EXISTS idx_kala_darshana_signal_id_fk          ON kala_darshana (signal_id);
CREATE INDEX IF NOT EXISTS idx_bodha_contradictions_signal_a_fk    ON bodha_contradictions (signal_a_id);
CREATE INDEX IF NOT EXISTS idx_bodha_contradictions_signal_b_fk    ON bodha_contradictions (signal_b_id);

-- ── children of kala_convergence (convergence_id) ────────────────────────────
CREATE INDEX IF NOT EXISTS idx_kala_bhavishya_convergence_id_fk    ON kala_bhavishya (convergence_id);
CREATE INDEX IF NOT EXISTS idx_phala_anchors_convergence_id_fk     ON phala_anchors (convergence_id);

-- ── bodha remediation chain + phala chains ───────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bodha_rm_remedy_target_resonance_fk ON bodha_rm_remedy_prescriptions (target_resonance_id);
CREATE INDEX IF NOT EXISTS idx_bodha_rm_windowed_base_presc_fk     ON bodha_rm_dasha_windowed_prescriptions (base_prescription_id);
CREATE INDEX IF NOT EXISTS idx_phala_suddha_sodhana_anchor_id_fk   ON phala_suddha_sodhana (anchor_id);
CREATE INDEX IF NOT EXISTS idx_phala_rect_best_candidate_id_fk     ON phala_rectification_best (best_candidate_id);
