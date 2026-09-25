# DEFECT (filed, not executed) — apply_migration.sh never writes `_migrations_applied`

- **Filed:** 2026-09-25, L0 Brahmagyan execution session (W-L0-5 follow-up, on the
  strategy session's correction of the ledger-block premise).
- **Owner:** whoever owns the CONDUCTOR build-orchestrator lane. Explicitly NOT
  the L0 execution session (mandate boundary) and NOT madhav-65's reconciliation
  (there is nothing for madhav-65 to reconcile — see below).
- **Severity:** recurrence class, not an active break. The eight known drifted
  files are accounted for; without this fix the NEXT out-of-band apply drifts
  again.

## The defect

`00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/apply_migration.sh`
applies migrations staging → idempotency check → production via raw `psql -f`
and never records the application:

    grep -c "_migrations_applied" 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/apply_migration.sh
    # 0

The ledger writer is `platform/scripts/migrate.ts`, which reads BOTH
`platform/migrations/*.sql` and `platform/supabase/migrations/*.sql`
(`migrate.ts` header line 3; directory resolution at line 835). Any migration
applied via `apply_migration.sh` is live in production and invisible to
`migrate.ts`'s ledger — including to its refusal logic.

## Observed instance (verified by structural probe, 2026-09-25)

Eight files on `origin/l3/gochara-autonomous-wp0-7` were applied to production
out-of-band (recorded in commit `5ee6280bd`; the 1075/1076 → 1080/1081 renumber
in `aa92cbc4e`). Probe verdicts against production:

| File | Effect | Verdict |
|---|---|---|
| 1080_nirmana_l3_gochara_resonance_target_resolution_state | 2 columns + CHECK on gochara_resonance_map | LIVE, unrecorded |
| 1081_nirmana_l3_gochara_ledger_coverage_publication | 4 tables + trigger + function | LIVE, unrecorded |
| 1082_nirmana_l3_vedha_moorti_stamp_columns | 7 columns on kala_vedha_gochara / kala_moorti_nirnaya | LIVE, unrecorded |
| 1083_l5_ledger_contact_id | contact_id on brahma_prospective_ledger + mimamsa_predictions | LIVE, unrecorded |
| 1084_wp7_k1_v1_registry_edges | ka_vedha_gochara edges on ka_kshetra / ka_sangam | LIVE, unrecorded |
| 1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec | digest-spec revision | **NOT APPLIED** — old spec 3743484c… still active, new spec 52a0d253… absent. Not a ledger gap; simply pending. |
| 1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis | 2 columns + 5 CHECKs on the contacts/coverage tables | LIVE, unrecorded |
| 1091_wp10_ka_gochara_registry_repin | kala_gochara_cutover_step05_snapshot + ka_gochara registry repin | LIVE, unrecorded |

The seven live-but-unrecorded rows are **backfill work for the L3 gochara
lane**, to be recorded when that branch merges. Re-apply is idempotent
(`IF NOT EXISTS` throughout; 1084's `array_append` is guarded), so the backfill
is ledger honesty, not safety.

## What is NOT defective (verified, do not re-investigate)

- `_migrations_applied` itself: 869 rows, exactly six in 1060–1130 (1070,
  1075–1079), all correct. 1075–1079 live in `platform/supabase/migrations/`
  on `origin/main` (`b6690928f`, PR #2727).
- `migrate.ts`'s renumber refusal: `assertNotRenumberedReapply()` (throws
  `MigrationRenumberedError`, matches by sha256 AND normalised `sql_identity`)
  plus the disclosure files `platform/scripts/ci/migration_renumber_disclosed.json`
  and `platform/scripts/ci/migration_hash_disclosed_residuals.json` (DVA
  RULING 73) already cover the renumber/hash-drift classes — including a prior
  692→808→810→812→821 parallel-lane race of the same shape.

## Required fix (either, owner's call)

1. Teach `apply_migration.sh` to write the ledger row itself (filename,
   sha256, normalised `sql_identity`) after a successful production apply —
   the same fields `migrate.ts` computes, so `assertNotRenumberedReapply()`
   keeps working across both paths; OR
2. Forbid `apply_migration.sh` for production application and route everything
   through `migrate.ts --target`.

Until one of these lands, every production apply must be assumed to leave no
ledger trace, and deployment state must continue to be decided structurally
(`to_regclass`, `information_schema`, `pg_constraint`, `pg_trigger`,
`pg_proc`, registry rows) — never by reading `_migrations_applied`.
