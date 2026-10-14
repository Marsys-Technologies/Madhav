-- Migration 1376: K7-3 producer-stored verification on the six stage sources.
-- Created: 2026-10-14. 1375 reserved by pending K6-123 PR #3495; 1376 checked by migration_number_guard.
-- Nullable, without DEFAULT/backfill: existing rows have no new verification proof.
-- Producers use UNVERIFIED_DEFAULT; only a future independent detector may promote.
BEGIN;

ALTER TABLE public.kala_darshana ADD COLUMN IF NOT EXISTS verification_pass_status text
  CHECK (verification_pass_status IN ('classical_match', 'computed_extension', 'divergent_flagged', 'documented_approximation', 'external_computation_required', 'floored', 'not_defined_for_nodes', 'pending_w3_verification', 'scope_cap_sentinel', 'single', 'single_pass', 'skipped_malformed_source', 'two_pass_verified'));
COMMENT ON COLUMN public.kala_darshana.verification_pass_status IS 'Canonical verification_vocab.py status earned for this output; NULL means no stored proof. Scores, roles and upstream tiers do not verify this row.';

ALTER TABLE public.kala_obstruction ADD COLUMN IF NOT EXISTS verification_pass_status text
  CHECK (verification_pass_status IN ('classical_match', 'computed_extension', 'divergent_flagged', 'documented_approximation', 'external_computation_required', 'floored', 'not_defined_for_nodes', 'pending_w3_verification', 'scope_cap_sentinel', 'single', 'single_pass', 'skipped_malformed_source', 'two_pass_verified'));
COMMENT ON COLUMN public.kala_obstruction.verification_pass_status IS 'Canonical verification_vocab.py status earned for this output; NULL means no stored proof. Scores, roles and upstream tiers do not verify this row.';

ALTER TABLE public.kala_gochara_contacts ADD COLUMN IF NOT EXISTS verification_pass_status text
  CHECK (verification_pass_status IN ('classical_match', 'computed_extension', 'divergent_flagged', 'documented_approximation', 'external_computation_required', 'floored', 'not_defined_for_nodes', 'pending_w3_verification', 'scope_cap_sentinel', 'single', 'single_pass', 'skipped_malformed_source', 'two_pass_verified'));
COMMENT ON COLUMN public.kala_gochara_contacts.verification_pass_status IS 'Canonical verification_vocab.py status earned for this output; NULL means no stored proof. Scores, roles and upstream tiers do not verify this row.';

ALTER TABLE public.kala_bhavishya ADD COLUMN IF NOT EXISTS verification_pass_status text
  CHECK (verification_pass_status IN ('classical_match', 'computed_extension', 'divergent_flagged', 'documented_approximation', 'external_computation_required', 'floored', 'not_defined_for_nodes', 'pending_w3_verification', 'scope_cap_sentinel', 'single', 'single_pass', 'skipped_malformed_source', 'two_pass_verified'));
COMMENT ON COLUMN public.kala_bhavishya.verification_pass_status IS 'Canonical verification_vocab.py status earned for this output; NULL means no stored proof. Scores, roles and upstream tiers do not verify this row.';

ALTER TABLE public.kala_convergence ADD COLUMN IF NOT EXISTS verification_pass_status text
  CHECK (verification_pass_status IN ('classical_match', 'computed_extension', 'divergent_flagged', 'documented_approximation', 'external_computation_required', 'floored', 'not_defined_for_nodes', 'pending_w3_verification', 'scope_cap_sentinel', 'single', 'single_pass', 'skipped_malformed_source', 'two_pass_verified'));
COMMENT ON COLUMN public.kala_convergence.verification_pass_status IS 'Canonical verification_vocab.py status earned for this output; NULL means no stored proof. Scores, roles and upstream tiers do not verify this row.';

ALTER TABLE public.kala_jivana_parva ADD COLUMN IF NOT EXISTS verification_pass_status text
  CHECK (verification_pass_status IN ('classical_match', 'computed_extension', 'divergent_flagged', 'documented_approximation', 'external_computation_required', 'floored', 'not_defined_for_nodes', 'pending_w3_verification', 'scope_cap_sentinel', 'single', 'single_pass', 'skipped_malformed_source', 'two_pass_verified'));
COMMENT ON COLUMN public.kala_jivana_parva.verification_pass_status IS 'Canonical verification_vocab.py status earned for this output; NULL means no stored proof. Scores, roles and upstream tiers do not verify this row.';

COMMIT;
