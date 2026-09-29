-- Migration 1083: L5 ledger contact_id — frozen-claim identity chain (WP7 P-3)
-- Created: 2026-09-24
--
-- Additive, nullable `contact_id TEXT` on both L5 prediction ledgers
-- (`brahma_prospective_ledger` — the live filing path in
-- platform/src/lib/lel/prospective_ledger.ts — and `mimamsa_predictions`, the
-- mīmāṃsā ledger). Carries the `sha256:<hex>` id of one kala_gochara_contacts
-- episode (WP1_CONTRACTS §3.2) when a frozen claim rests on a specific Gochara
-- contact. Nullable because most claims are not gochara-contact-anchored;
-- non-gochara claim paths are untouched. No CHECK constraint: format and
-- existence are validated at filing time in application code
-- (fileProspectivePrediction), keeping the column usable by ledgers whose
-- claims predate the gochara contact ledger (backfill = NULL).

BEGIN;

ALTER TABLE brahma_prospective_ledger
  ADD COLUMN IF NOT EXISTS contact_id TEXT;

COMMENT ON COLUMN brahma_prospective_ledger.contact_id IS
  'WP7 P-3: sha256:<64 hex> id of the kala_gochara_contacts episode this frozen '
  'claim rests on (WP1_CONTRACTS §3.2), when it rests on one; NULL otherwise. '
  'Immutable under repartition/republish — a convention change implies new '
  'contact ids, so a dangling id is detectable, never silently re-pointed.';

ALTER TABLE mimamsa_predictions
  ADD COLUMN IF NOT EXISTS contact_id TEXT;

COMMENT ON COLUMN mimamsa_predictions.contact_id IS
  'WP7 P-3: sha256:<64 hex> id of the kala_gochara_contacts episode this frozen '
  'claim rests on (WP1_CONTRACTS §3.2), when it rests on one; NULL otherwise.';

COMMIT;
