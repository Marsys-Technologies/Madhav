---
artifact: MIGRATION_1221_A29_INTENT
version: "1.1"
status: HELD (draft PR). Migration file written (a29 conjunct + ga_structural digest-spec swap); merges ONLY in the S-L1 window, after the ga_structural writer image is deployed and verified, immediately before the ga_structural launch; then verified by production structure.
produced_by: exec-suvarna
produced_on: 2026-10-02
for: the argala L1 lane (PR #2851 carries the ga_structural writer and migration 1219; design note DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md, #2850)
files:
  - platform/migrations/1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql
tests: platform/python-sidecar/tests/test_argala_migration_1221_sql.py executes the real migration file against a disposable local Postgres
changelog:
  - "1.1 (2026-10-02): SS decision A (1221-file route). The ga_structural output-digest spec swap (81 -> 82 categories, adding argala_graha_natal) moves INTO this file from migration 1219 (after the a29 conjunct): served_generation.ts treats a receipt whose output_digest_spec_sha256 is not an ACTIVE spec as receipt_spec_retired, so doing it at the integration's deploy (1219) would leave ga_structural unresolved for serving until rebuilt; here a29 already stales ga_structural, so the swap adds nothing to the degraded set. Added: SERVING EFFECT AT APPLY statement, the gap-direction analysis (old spec active between the integration deploy and W1), the W1 combined-apply matrix, and tests for the combined effect, the shas, the validator and the digest gap."
  - "1.0 (2026-10-02): split out of the 1219/1221 explanation document (the explanation document of #2851, now MIGRATION_1219_INTENT_v1_0.md) by SS decision on the migration-guard review: the routine runner applies every merged file at the next deploy before that deploy's images roll, so 1221 cannot ride with the writer PR. The SQL is the file; this document carries none. Added: SET LOCAL lock_timeout = '5s' (1218 pattern)."
---

# Migration 1221: the a29 integrity conjunct and the ga_structural digest-spec swap (HELD)

## 1. What it does

Adds ONE conjunct, (a29) [SS N-61, AR-3; CLAUDE.md N.8], to `ga_structural`'s `integrity_check_sql`: for every argala-offset cell (2, 4, 5, 11) of `argala_natal_matrix`, the cell is NULL with `fact_value_text = 'no_occupant'` exactly when its source sign holds no graha, and a non-NULL score with no text when it does. Conjunct (e27) is vacuously true on a NULL score, so before this a NULL on an occupied cell, or a stale 1.0 on an empty one, passed. Scoped to the canonical chart (migration 904's disclosed tradeoff). Done as a guarded `replace()` at the single `AS integrity_passed` anchor: refuses unless (g28) is present and the anchor occurs exactly once, no-op when (a29) is already there, asserts the result afterwards.

**Part 2: the ga_structural output-digest spec swap.** Retire the one active spec (migration 914, 81 categories, sha `b2490646...`), insert the same spec plus `argala_graha_natal` (82 categories, sorted and unique, sha `d480c829...` = `canonical_digest`, which reproduces 914's stored sha exactly). Retired, not deleted (609 / 1086 precedent); refuses if any active ga_structural spec is neither of the two shas; asserts one active new row afterwards. It comes after the a29 conjunct in the same file.

**Serving effect at apply.** ga_structural freshness goes stale on every chart (a29: `UPDATE OF integrity_check_sql` fires `nirmana_registry_receipt_invalidation`) AND its receipts read `receipt_spec_retired` until rebuilt. Degraded set at W1 = ga_structural (and with 1222/1223/1226: ga_vargas, ga_dashas, ga_yoga); all rebuilt in the window. Proved by `test_the_combined_effect_ga_structural_freshness_stale_and_its_receipt_spec_retired_nothing_else_moves` against the real trigger function body read from the live database.

## 2. Why it is a separate, held PR

- **Merge = apply.** `platform/scripts/migrate.ts` applies every unapplied file in `platform/migrations` at the next deploy, and every deploy job `needs` the migrate job, so the migration runs before that deploy's images roll.
- **An old-image `ga_structural` rebuild after a29 fails its post-write integrity check** (the old writer still stores 1.0 on empty cells). So a29 must never apply before the new writer image is live.
- **a29 reads red on live canonical data until S-L1 writes the NULL cells** (every empty-source argala cell is stored 1.0 today). It is read at build time (the asset runner's post-write gate), by the Nirmana `integrity_verified` acceptance detector, and is part of the registry-contract fingerprint.
- **`UPDATE OF integrity_check_sql` stales `ga_structural`'s freshness** (trigger 596, `nirmana_registry_receipt_invalidation`): its direct dependents fail DEP-ASSERT until the next governed receipt. Applied immediately before S-L1 this costs nothing, because S-L1 rebuilds `ga_structural` anyway.

## 3. When to merge (the order)

1. #2851 (the `ga_structural` writer and migration 1219) is merged, its writer image is deployed, and the deployed image is verified (LC-1 digest equality).
2. At the S-L1 window, immediately before the `ga_structural` launch, with **0 active runs** for `ga_structural` (read-only check in the file header; expected 0), merge this PR.
3. After the deploy applies it, verify by production structure, not the deploy log (CLAUDE.md N.4, Trap 103): `SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry WHERE asset_id = 'ga_structural'` returns `t`; expect `integrity_passed = false` on the canonical chart until S-L1 writes the NULL cells, then true.
4. Launch the S-L1 `ga_structural` rebuild. From apply until the canonical rebuild has written the NULL cells, no `ga_structural` build for any chart may run: the post-write gate runs per build, but (a29) reads the canonical rows.

## 4. The gap before this file (old 81-category spec still active) and its direction

Between the integration deploy (new argala writer live, migration 1219 applied) and W1, the OLD spec stays active. Nothing builds ga_structural in that gap. If something did, `asset_runner.py` (line 1385) calls `compute_output_digest`, which loads the ACTIVE spec (`load_output_digest_spec`: `retired_at IS NULL`) and filters each component by `where_in` (`fact_category = ANY(...)`). The old `where_in` does not contain `argala_graha_natal`. So the build **succeeds**; the receipt records the **old** spec sha and a digest that does **not** cover the argala rows: a **silent coverage gap, not a loud failure** (nothing compares written categories with the spec). After this file applies, that receipt reads `receipt_spec_retired` anyway. Tested with the real `compute_output_digest` on a real cursor (`test_the_gap_with_the_old_spec_active_argala_rows_do_not_move_the_digest_and_the_build_would_not_fail`): argala rows leave the digest byte-identical under the old spec, a covered category moves it, and after the swap argala rows move it.

## 5. The W1 combined apply (1221, 1222, 1223, 1226)

`migrate.ts` applies them in numeric order. Guards read versus writes (all four read from their own files / intent):

| migration | guards read | writes | trigger side effect |
|---|---|---|---|
| 1221 part 1 (a29) | `ga_structural.integrity_check_sql`: contains (g28), anchor unique, (a29) absent (idempotence) | `ga_structural.integrity_check_sql` | ga_structural freshness stale, all charts |
| 1221 part 2 (spec) | `asset_output_digest_specs` rows of `ga_structural` only: every active sha in {b2490646..., d480c829...} | retire b2490646; insert d480c829 (ga_structural) | none (no trigger on the specs table) |
| 1222 | one `ga_vargas` registry row; md5 of `ga_vargas.integrity_check_sql` = 255af7c5...; post-check md5 = d2f89753... | `ga_vargas.integrity_check_sql` | ga_vargas freshness stale |
| 1223 (intent only, not written) | `ga_vargas` active spec = 5f332a48... (count 1) | retire 5f332a48; insert 9c278d21... (ga_vargas) | none |
| 1226 | existence (all-or-nothing) and `is_active` of ga_dashas, ga_yoga, ga_vargas, ga_sensitive; `depends_on` closure acyclic from the edited consumers | `depends_on` of ga_dashas, ga_yoga, ga_vargas (append) | ga_dashas, ga_yoga, ga_vargas freshness stale |

No migration writes a column or row another migration's guard reads: 1221 and 1223 write different assets' spec rows (the one-current index is per asset); 1222 reads and writes `ga_vargas.integrity_check_sql` while 1226 writes `ga_vargas.depends_on` and reads only `depends_on` / `is_active` / existence; 1221's `integrity_check_sql` write is on ga_structural, which no other guard reads (1226's acyclicity closure reads `depends_on` only). The registry trigger is idempotent (`registry_changed` is added once), so the overlapping stale of ga_vargas (1222 and 1226) is harmless.

Verified ad hoc on a disposable Postgres (not committed: 1222 and 1226 are on other PRs): fixture registry with the live `depends_on` graph, the real trigger function body, the real serving tables, ga_vargas on migration 884's real body (md5 255af7c5...), the real 914 and 883 specs, and the 1223 statements simulated from its intent text. All six orders of 1221, 1222, 1226 and all 24 orders with the 1223 simulation applied with no guard tripping and one identical final state: stale = ga_dashas, ga_structural, ga_vargas, ga_yoga; ga_structural spec d480c829 active (b2490646 retired); ga_structural receipt reads spec-retired; the three `depends_on` rows as expected; ga_vargas integrity md5 d2f89753 (1222's post-check value); count_sql and target_floor untouched.

## 6. The SQL

There is no SQL copy in this document: the file is the migration. `test_argala_migration_1221_sql.py` runs it against a disposable local Postgres: apply once, idempotent re-run, three refusal cases, one-transaction rollback, and the six (a29) mutants including the one (e27) passes.
