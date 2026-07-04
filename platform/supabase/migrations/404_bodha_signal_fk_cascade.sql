-- Migration 404: bodha internal FKs → ON DELETE CASCADE
--
-- bodha_signal_embeddings and bodha_contradictions reference bodha_msr_signals
-- with NO ACTION FKs, blocking bodha layer rebuilds: deleting parent signals
-- fails if embeddings or contradictions rows still exist.
-- Changing to ON DELETE CASCADE so child rows are cleaned up automatically
-- when signals are replaced during a rebuild.
-- SET LOCAL disables the statement timeout for this transaction only.
SET LOCAL statement_timeout = 0;

ALTER TABLE bodha_signal_embeddings
  DROP CONSTRAINT bodha_signal_embeddings_signal_id_fkey,
  ADD  CONSTRAINT bodha_signal_embeddings_signal_id_fkey
    FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;

ALTER TABLE bodha_contradictions
  DROP CONSTRAINT bodha_contradictions_signal_a_id_fkey,
  ADD  CONSTRAINT bodha_contradictions_signal_a_id_fkey
    FOREIGN KEY (signal_a_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;

ALTER TABLE bodha_contradictions
  DROP CONSTRAINT bodha_contradictions_signal_b_id_fkey,
  ADD  CONSTRAINT bodha_contradictions_signal_b_id_fkey
    FOREIGN KEY (signal_b_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;
