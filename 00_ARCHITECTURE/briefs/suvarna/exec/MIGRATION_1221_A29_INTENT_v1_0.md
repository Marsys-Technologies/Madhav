---
artifact: MIGRATION_1221_A29_INTENT
version: "1.0"
status: HELD (draft PR). Migration file written; merges ONLY in the S-L1 window, after the ga_structural writer image is deployed and verified, immediately before the ga_structural launch; then verified by production structure.
produced_by: exec-suvarna
produced_on: 2026-10-02
for: the argala L1 lane (PR #2851 carries the ga_structural writer and migration 1219; design note DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md, #2850)
files:
  - platform/migrations/1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql
tests: platform/python-sidecar/tests/test_argala_migration_1221_sql.py executes the real migration file against a disposable local Postgres
changelog:
  - "1.0 (2026-10-02): split out of the 1219/1221 explanation document (MIGRATION_1219_1221_INTENT v1.1, on #2851) by SS decision on the migration-guard review: the routine runner applies every merged file at the next deploy before that deploy's images roll, so 1221 cannot ride with the writer PR. The SQL is the file; this document carries none. Added: SET LOCAL lock_timeout = '5s' (1218 pattern)."
---

# Migration 1221: the a29 integrity conjunct (HELD)

## 1. What it does

Adds ONE conjunct, (a29) [SS N-61, AR-3; CLAUDE.md N.8], to `ga_structural`'s `integrity_check_sql`: for every argala-offset cell (2, 4, 5, 11) of `argala_natal_matrix`, the cell is NULL with `fact_value_text = 'no_occupant'` exactly when its source sign holds no graha, and a non-NULL score with no text when it does. Conjunct (e27) is vacuously true on a NULL score, so before this a NULL on an occupied cell, or a stale 1.0 on an empty one, passed. Scoped to the canonical chart (migration 904's disclosed tradeoff). Done as a guarded `replace()` at the single `AS integrity_passed` anchor: refuses unless (g28) is present and the anchor occurs exactly once, no-op when (a29) is already there, asserts the result afterwards.

## 2. Why it is a separate, held PR

- **Merge = apply.** `platform/scripts/migrate.ts` applies every unapplied file in `platform/migrations` at the next deploy, and every deploy job `needs` the migrate job, so the migration runs before that deploy's images roll.
- **An old-image `ga_structural` rebuild after a29 fails its post-write integrity check** (the old writer still stores 1.0 on empty cells). So a29 must never apply before the new writer image is live.
- **a29 reads red on live canonical data until S-L1 writes the NULL cells** (every empty-source argala cell is stored 1.0 today). It is read at build time (the asset runner's post-write gate), by the Nirmana `integrity_verified` acceptance detector, and is part of the registry-contract fingerprint.
- **`UPDATE OF integrity_check_sql` stales `ga_structural`'s freshness** (trigger 596, `nirmana_registry_receipt_invalidation`): its direct dependents fail DEP-ASSERT until the next governed receipt. Applied immediately before S-L1 this costs nothing, because S-L1 rebuilds `ga_structural` anyway.

## 3. When to merge (the order)

1. #2851 (the `ga_structural` writer and migration 1219) is merged, its writer image is deployed, and the deployed image is verified (LC-1 digest equality).
2. At the S-L1 window, immediately before the `ga_structural` launch, with **0 active runs** for `ga_structural` (read-only check in the file header; expected 0), merge this PR.
3. After the deploy applies it, verify by production structure, not the deploy log (CLAUDE.md N.4, Trap 103): `SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry WHERE asset_id = 'ga_structural'` returns `t`; expect `integrity_passed = false` on the canonical chart until S-L1 writes the NULL cells, then true.
4. Launch the S-L1 `ga_structural` rebuild.

## 4. The SQL

There is no SQL copy in this document: the file is the migration. `test_argala_migration_1221_sql.py` runs it against a disposable local Postgres: apply once, idempotent re-run, three refusal cases, one-transaction rollback, and the six (a29) mutants including the one (e27) passes.
