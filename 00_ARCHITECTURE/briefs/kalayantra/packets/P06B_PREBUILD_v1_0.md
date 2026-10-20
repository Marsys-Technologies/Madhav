---
artifact: P06B_PREBUILD_v1_0.md
version: "1.0"
status: DRAFT — built preparation; independent acceptance and operational gates remain
produced_on: 2026-10-16
changelog:
  - "1.0: port reviewed P06b preparation, close occurrence/ray detector omissions and establish guarded migration replay."
---

# P06B preparation and replay contract

This packet prepares P06b and P06B-NB-01/02/03 under A6 D-40. It does not activate a generation, change the J DAG, publish completion receipts, enable P08, seal production or change serving authority.

## Source custody and landing order

The job's base is `ef14167bcc35a321b11d4d189a6b752bf3c658b8`. Its local `origin/main` has neither P06's near-miss builder/storage/census implementation nor the shared CI discovery/generated-output pipeline named by the launcher. The reviewed P06b source is `12ae42611629be4a2e4e8823ff5e078a151f6bdb`, accepted at merged dependency head `82405b252c181714f511d7625b091763cb9bfd17` by job `X-20261015T231059Z-review-p06b`.

(I) INTERPRETATION: build and verify the P06-dependent integration in a job-local copy of that reviewed stack while porting only P06b changes to this branch. P06 must land before this packet's final integration/merge and exact-head CI. The alternative is absorbing the whole P06 campaign packet here. The new verifier and the two required test modules carry their reviewed parent bodies because these paths do not yet exist on this base. They are not replacements for P06's missing builder, SQL migrations or snapshot implementation.

Preserve current main's settled-daśā identity code and the J-4p B4/B5 golden/guards when merging; do not replace current files wholesale with the older reviewed stack. In particular, retain P06's `near_miss`/`nd_h_tables` module registrations and scored-class census alongside P06b's verifier registration and layer pin. Union the migration-ledger lists and CI profiles. Machine-owned outputs remain CI-owned and are never regenerated in this branch.

## Prepared behavior

| Item | Implementation and detector |
|---|---|
| P06b | Allocated migration 1381 carries literal predecessor function bodies plus near-miss blocks; `platform/migrations/1381_gochara_near_miss_seal_integration.sql:18`, `:130`, `:143`, `:192`. Versioned manifest pin, independent generation stage, precision/stationless refusals, digest custody and four readback scripts are included. |
| P06B-NB-01 | Independent UUID-v8 encoding of the object identity and reconstructed full-domain ordinal; `services/gochara_kernel/near_miss_verifier.py:492`. A mismatch refuses as `near_miss_identity_mismatch`, before replacing an attestation. |
| P06B-NB-02 | The independent geometry selects the ray; its canonical level must match the stored claim. Refusal is `near_miss_level_mismatch`; `near_miss_verifier.py:282` and `:566`. |
| P06B-NB-03 | Explicit `--replay-gochara --only ...` mode preflights every selected ledger hash, then repeats SELECT-only readbacks without tracker DDL or migration execution; `platform/scripts/migrate.ts:845`. Raw 1381 replay continues to refuse at the predecessor pin. |

Python service paths in the table are relative to `platform/python-sidecar/`. Real Jupiter corruption tests change only the UUID or ray level, leave production row guards enabled, and verify that refusal leaves the attestation unchanged. Synthetic identity/ray tests independently pin UUID bytes, full-domain ordinal reuse, missing values, Decimal values and longitude wrap.

(I) INTERPRETATION: NB-03 is resolved through a guarded, tested replay contract. Direct SQL repeatability is not claimed. Editing applied 1381 or creating an unallocated successor is the rejected alternative. Migration 1381 remains byte-for-byte the reviewed file, SHA-256 `8dd3ec863d58f77939314429a937a3412b359205bba5aba8afb8fc61c5056586`; the allocation file reserves 1381 for P06b and reserves no child migration.

## Required tests and CI

The P06b tests use the pinned local Swiss corpus and guarded suite-owned PostgreSQL fixtures. The job result records the two verification contexts separately: current-main-compatible regressions and the reviewed P06 dependency stack. Its reversion receipts name the copy, exact command, failing reverted exit and passing fixed exit for every claim. These are builder proofs, not independent review receipts.

(I) INTERPRETATION: because this base lacks `ci_discovery.py`, a bounded `platform/scripts/gochara/ci_p06b.py` consumer uses the shared `ci.test_suites/1` profile format. The profiles are consumed in the existing required Unit Tests and DB Integration Tests jobs. Includes are globs, empty families refuse, Vitest disables caching, and the Python invocation retains required DB/ephemeris flags. No test-file paths were added to `ci.yml`. Once the shared discovery pipeline lands, preserve these profile entries while reconciling consumers; waiting without wiring or replacing the other pipeline's in-flight implementation was the alternative.

Local evidence: the 111-test focused stack suite and additional policy controls passed; both current-main ordinary-golden comparisons, 67 TypeScript tests and three CI profile checks passed. All 41 per-claim reversion/fixed pairs passed. The actual migration CLI also repeated readback on a PostgreSQL-enforced read-only fixture connection. Full-project TypeScript checking still reports the unchanged `platform/tests/unit/gochara_seal_workflow_static.test.ts:193` missing `NODE_ENV`; an isolated copy from HEAD reproduces it without this packet's changed files. Changed TypeScript checks and ESLint passed. One inherited optional external Stream B probe was skipped; selected DB suites were run locally.

The current-main golden retains its immutable J-4p capture, B4 positive-bounds comparison and B5 period guard. P06b permits only its one manifest layer-catalogue probe and the implementation identities changed by the new geometry/window code. All other statement ordering, parameter counts, row counts, outcomes and vector components remain compared. The historical captures are unchanged.

(I) INTERPRETATION inherited from the reviewed P06b tests: layer-on/off comparisons hold the manifest layer pin constant. The schema-off control is unsealable; its scored rows still must equal the schema-on rows without deleting identity/digest columns from the comparison. Comparing different manifest identities is the rejected alternative.

## Executor-only steps, prepared and not executed

1. Reconcile the final merged P06/P06b head, exact-head independent review, required CI and CI-produced implementation/aggregate outputs. Retain J-4b/J-4c prerequisites and all existing J edges.
2. Rehearse the predecessor chain on the production major version; local job results identify PostgreSQL 15.17 only. Migration 1381 pins exact function definitions. A differing predecessor refuses; it is not permission to repin applied SQL.
3. Use the existing protected public-schema migration workflow with its approved bounded request, lease, backup/restore evidence and human environment approval. Apply the reviewed allocated chain and obtain independent per-migration readbacks, including 1308 and 1381, bound to the same operation/request. A source merge or a printed catalogue is not this acceptance.
4. For an already-applied hash-matching file, the supported read-only replay command is:

   ```sh
   cd platform
   npx tsx scripts/migrate.ts --replay-gochara --only 1381_gochara_near_miss_seal_integration.sql
   ```

   The executor supplies its already-approved connection. Missing ledger rows, changed hashes, unknown readback filenames and mixed replay/apply-preview options refuse. Do not execute migration 1381 SQL directly for a replay. Existing `--only` applies remain ledger-idempotent and perform per-migration readback after commit.
5. Retain FINAL_BUILD_SCOPE §11.1–11.2: actual layer noninterference with negative controls, and whole-horizon contact/ordinal/record/digest equality against the saved measuring golden. The source specification is `00_ARCHITECTURE/briefs/pravaha/decisions/FINAL_BUILD_SCOPE_v1_0.md:198–205` at `82405b252`; it is absent on this job's main snapshot. The guarded tests prove the new seal guard's positive/negative boundary and readback contracts; they do not seal a FINAL production generation.
6. FB-66 final-rules candidate evidence, required reports/density/residual decisions, independent protected acceptance and P08 enablement remain gated. Under `all_null_candidate/1`, endpoint/ranking identity stays `vacuous_under_policy`, never green. OD-1 restores the numerical identity duty on the final-rules candidate; it is not decided by this packet.

No production connection, service activation, Git write, credential access, deployment or controller receipt publication was performed by the builder.
