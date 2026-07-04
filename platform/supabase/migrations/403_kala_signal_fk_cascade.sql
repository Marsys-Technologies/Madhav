-- Migration 403: kala_* signal_id FKs → ON DELETE CASCADE
--
-- Five kāla tables reference bodha_msr_signals.signal_id (currently CASCADE or
-- SET NULL in prod). Standardising all to ON DELETE CASCADE so kāla rebuild
-- regenerates cleanly from fresh bodha data.
-- SET LOCAL disables the statement timeout for this transaction only, avoiding
-- the 60-second Supabase default that caused the first deploy attempt to fail.
SET LOCAL statement_timeout = 0;

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
