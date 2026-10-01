-- Migration 1214: F-3 (N-32) -- drop the five kala_* foreign keys into bodha_msr_signals
-- Created: 2026-10-01
-- The migration runner wraps this file in a transaction.
--
-- WHY. kala_{convergence,activation,obstruction,darshana,bhavishya}.signal_id REFERENCES
-- bodha_msr_signals(signal_id) ON DELETE CASCADE (migration 403). bo_laksana's delete-then-insert of
-- bodha_msr_signals therefore deleted the canonical chart's Kala rows as a side effect of an L2
-- rebuild (2026-09-08; diagnosis I-6). Derived rows are regenerable (N-32): the L2 -> L3 cascade is
-- handled by rebuilding downstream in wave order, never by letting a foreign key delete another
-- layer's rows. This migration removes only the constraints.
--
-- WHAT THIS DOES NOT DO.
--  * No data is changed or deleted. Dropping a foreign key deletes nothing.
--  * The three intra-L2 keys into bodha_msr_signals (bodha_contradictions.signal_a_id / signal_b_id,
--    bodha_signal_embeddings.signal_id) are NOT touched here: those tables are owned by
--    data_plane_l2_owner, so dropping their keys is an owner-path change, not an amjis_app migration.
--  * assert_l2_msr_delete_safe is NOT touched (data_plane_l2_owner function, attested digest). It
--    still enforces the admitted-asset context; its catalogue-driven cross-layer refusal finds no
--    Kala key after this migration, so it no longer refuses on Kala dependants.
--
-- WITHOUT THE KEY, a Kala row can dangle if an MSR signal disappears or changes identity.
--  * signal_id is deterministic: bodha_signal_identity() (migration 661) is a uuid v5 of
--    (chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb); an unchanged signal
--    keeps its id across a regeneration, so references stay valid.
--  * A changed or removed signal is DETECTED, not prevented, by
--    platform/scripts/governance/msr_dangling_signal_refs.py (read-only dangling-reference check).
--
-- Locking. DROP CONSTRAINT takes ACCESS EXCLUSIVE on the child table and also locks the referenced
-- bodha_msr_signals (its RI triggers are removed). lock_timeout makes a blocked attempt fail loudly
-- instead of queueing behind, and then stalling, readers of bodha_msr_signals. Re-run when idle.

SET LOCAL lock_timeout = '5s';

ALTER TABLE kala_activation   DROP CONSTRAINT IF EXISTS kala_activation_signal_id_fkey;
ALTER TABLE kala_bhavishya    DROP CONSTRAINT IF EXISTS kala_bhavishya_signal_id_fkey;
ALTER TABLE kala_convergence  DROP CONSTRAINT IF EXISTS kala_convergence_signal_id_fkey;
ALTER TABLE kala_darshana     DROP CONSTRAINT IF EXISTS kala_darshana_signal_id_fkey;
ALTER TABLE kala_obstruction  DROP CONSTRAINT IF EXISTS kala_obstruction_signal_id_fkey;
