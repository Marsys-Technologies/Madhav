---
artifact: J6M_R1_REPLAY_CONTRACT
version: '1.0'
status: PREBUILD_WAITING_ON_GATE
item: J6M-R1
produced_on: 2026-10-16
idempotency: runner_ledger
migration: 1382_gochara_authority_no_truncate.sql
migration_sha256: b15fbbacc29a18ce9b33714cc6f4d6025f619cf8971bccd4e972fa20de483f21
raw_replay_sqlstate: '42710'
requires_catalog_readback: true
activation: false
changelog: '1.0: specify and exercise runner-level replay semantics; preserve immutable SQL and all operational gates.'
---

# J6M-R1 — migration 1382 replay contract

**(I) INTERPRETATION:** accept runner-ledger idempotency as the intended replay
contract for this immutable migration. The review explicitly permits this
resolution: `X-20261015T174958Z-review-j6m/result.json:20` under the campaign job
root `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/`.
Alternative: make raw SQL replay succeed in an allocated additive follow-up.
No migration number is allocated to J6M-R1, and editing applied SQL is forbidden
by `CLAUDE.md:114`. Only the disposable test databases' ledgers change during
verification.

The supported deployment entry point is `platform/scripts/migrate.ts` through
the existing approved protected-window workflow. On first application it runs
the SQL and inserts the filename, SHA-256 and SQL identity in the same
transaction (`migrate.ts:934–950`). On a repeat it verifies the recorded byte
hash and skips SQL execution (`migrate.ts:895–900`); the preview has the same
hash check (`migrate.ts:860–867`). A changed byte hash fails with
`MigrationHashMismatchError`, including a comment-only edit. This migration has
no disclosed hash-mismatch exception. The tests pass empty disclosure maps so
the general historical-disclosure mechanism cannot hide a regression.

Raw execution of `1382_gochara_authority_no_truncate.sql` twice is **not** a
supported idempotent replay mechanism. Its unconditional `CREATE TRIGGER`
(`platform/migrations/1382_gochara_authority_no_truncate.sql:25`) raises
`DuplicateObject`, SQLSTATE `42710`, on the second execution. The failure must
roll back; it must not be swallowed, relabelled successful, or followed by a
drop/recreate workaround. The prior authority rows and exact trigger remain.

An unapplied 1382 remains deferred by the routine runner. The protected list
continues to govern application; a local test's `only` selection is a guarded
fixture invocation, never production authorization. A hash-matching applied
file is skipped on both routine and protected paths.

## Readback and acceptance remain separate

A successful ledger skip does **not** inspect or repair live schema drift.
After approved application, independently read the validated
`kga_sealed_authority_ck` and the trigger on `public.kala_gochara_authority`:
`kala_gochara_authority_no_truncate`, non-internal, `tgenabled = 'A'`,
`tgtype = 34` (BEFORE, STATEMENT, TRUNCATE), no arguments or predicate, calling
`public.ka_gochara_refuse_truncate()`. Verify refusal and unchanged authority
rows in origin and replica modes. A disabled or altered trigger fails this
readback even if the filename/hash check succeeds; never turn that skip into
an activation receipt. The original 1382 postflight remains unchanged.

`platform/python-sidecar/tests/l3/gochara/test_j6m_authority_admission_db.py`
imports the real TypeScript runner against the suite's own guarded disposable
database, applies the real predecessor SQL and 1382, and measures first apply,
repeat/preview, byte drift, routine deferral, catalog drift and raw SQL refusal.
Rows, tracker records and trigger OID/definition are compared across repeats.
`test_j6m_prebuild_static.py` requires this explicit contract and unchanged SQL
hash. Both files already run in the mandatory A5.3 CI step
(`.github/workflows/ci.yml:526–553`); no new CI path entry is needed.

This is **built, waiting on gate** under A6 D-40, not J-6m completion. Retain
independent exact-head review/CI, J-6a operational evidence, approved protected
application and readbacks of 1379/1382, deployment containment, J-6r consumer
rollback rehearsal, D-FLIP and executor authorization. The parent model's
`packet_oracles_verified` and `authority_constraint_applied_readback` remain
independent earned requirements
(`00_ARCHITECTURE/control/kalayantra/plan_model.json:19766–19786`). No authority
switch, production operation, model activation, or `publish_head`/`rollback_head`
enablement is performed here.
