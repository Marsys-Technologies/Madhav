---
artifact: WP7_REVIEW_REQUEST_P3
packet_id: P-3
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-24
branch: l3/gochara-autonomous-wp0-7
---

# REVIEW REQUEST — P-3 (L5 ledger `contact_id` for frozen-claim identity)

## What landed

- **Migration `platform/migrations/1083_l5_ledger_contact_id.sql`** (next free
  number per repo convention; BEGIN/COMMIT, idempotent
  `ADD COLUMN IF NOT EXISTS`): nullable `contact_id TEXT` on
  `brahma_prospective_ledger` AND `mimamsa_predictions` (the packet names both
  L5 ledgers), with COMMENT ON COLUMN documenting WP1 §3.2 semantics. No CHECK
  constraint — format/existence are enforced at filing time, keeping the column
  valid for pre-contact-ledger backfill rows (NULL).
- **`platform/src/lib/lel/prospective_ledger.ts`**:
  - `FileProspectivePredictionInput.contact_id?: string`;
    `ProspectiveLedgerRow.contact_id: string | null`.
  - `assertContactIdResolves(chartId, contactId)`: (1) format
    `^sha256:[0-9a-f]{64}$`; (2) explicit `kala_gochara_authority` read — an
    ABSENT row rejects the filing (N-10: unpublished, never a `'v1'` default;
    there is no ledger to resolve against); (3) existence under
    `(chart_id, authoritative_generation, contact_id)` in
    `kala_gochara_contacts` — a dangling id is rejected, never stored
    (F-18 orphan class one layer up). The check is a SELECT; no write access to
    gochara relations.
  - INSERT column list + params (+`contact_id`, `$15`, default NULL) and all
    three RETURNING/SELECT lists (`fileProspectivePrediction`,
    `listProspectivePredictions`, `matchOpenPredictionsForLelEvent`) carry
    `contact_id`.
- `record_outcome` untouched structurally, per packet.

## Test evidence

- New `src/lib/__tests__/lel/prospective_ledger.contact_id.test.ts` — 5 tests:
  real-fixture id files and returns on the row (existence checked under the
  authoritative generation, INSERT param verified); tampered id (one hex char)
  rejected with no INSERT issued; malformed id rejected before any SQL; absent
  authority row rejects contact-anchored filings; NULL-contact (backfill-era)
  claim still files, lists, and outcome-matches unchanged.
- Pre-existing `prospective_ledger.test.ts` (38 tests) green (one fixture row
  gained `contact_id: null`).
- L4_phala + L5_mimamsa layer batteries: 260 passed.
- `npx tsc --noEmit --skipLibCheck`: 0 errors.

## Items flagged for independent review

1. **Generation source for the existence check**: the packet says
   `(chart_id, generation, contact_id)` but the filing input carries no
   generation; I resolve it from `kala_gochara_authority` (N-10 discipline).
   A claim meant to anchor a non-authoritative generation's episode has no
   path — flagged as a deliberate narrowing.
2. **`mimamsa_predictions` got the column but no TS read/write path** — the
   packet's anchors are all `brahma_prospective_ledger`/`prospective_ledger.ts`;
   the mīmāṃsā ledger's writers are sibling-owned. Column is in place for that
   owner to adopt.
3. **migration-guard review not dispatched**: the create-migration skill's
   step 4 calls for a migration-guard subagent; this session has no subagent
   dispatch capability, so the migration is unreviewed beyond the packet's own
   spec (additive nullable, idempotent, no CHECK).
4. Live-DB acceptance (filing script + psql) not runnable here; tests mock the
   DB client per the module's existing convention.
