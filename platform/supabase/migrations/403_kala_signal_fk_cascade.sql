-- Migration 403: kala_* signal_id FKs → ON DELETE CASCADE
--
-- Five kāla tables reference bodha_msr_signals.signal_id with NO ACTION,
-- blocking bodha layer rebuilds (bo_laksana delete-then-insert pattern).
-- Changing to ON DELETE CASCADE allows bodha_msr_signals rows to be deleted
-- without first manually clearing downstream kāla rows — the cascade
-- handles it automatically so kāla rebuild regenerates from fresh bodha data.

ALTER TABLE kala_activation
  DROP CONSTRAINT kala_activation_signal_id_fkey,
  ADD  CONSTRAINT kala_activation_signal_id_fkey
    FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;

ALTER TABLE kala_bhavishya
  DROP CONSTRAINT kala_bhavishya_signal_id_fkey,
  ADD  CONSTRAINT kala_bhavishya_signal_id_fkey
    FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;

ALTER TABLE kala_convergence
  DROP CONSTRAINT kala_convergence_signal_id_fkey,
  ADD  CONSTRAINT kala_convergence_signal_id_fkey
    FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;

ALTER TABLE kala_darshana
  DROP CONSTRAINT kala_darshana_signal_id_fkey,
  ADD  CONSTRAINT kala_darshana_signal_id_fkey
    FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;

ALTER TABLE kala_obstruction
  DROP CONSTRAINT kala_obstruction_signal_id_fkey,
  ADD  CONSTRAINT kala_obstruction_signal_id_fkey
    FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE;
