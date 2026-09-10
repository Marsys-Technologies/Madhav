# Nirmāṇa Campaign Spine — Post-Rebase Focused-Test Fix

- Branch: `codex/nirmana-tracker-campaign-spine`
- Starting head: `cef42bfa1e5b43534c101ef763bd451bf53768cb`
- Completed at: `2026-08-26T12:56:40+05:30`
- Status: focused post-rebase test repaired locally; production behavior unchanged

## Diagnosis and fix

`recordNirmanaElevationEvidence` legitimately executes its transaction protocol before the
build-run authorization query: `BEGIN`, revision advisory lock, idempotency receipt lookup, and
current-frozen-definition check. The rebase added these queries to the tested path.

The `authorizes build runs only for execution-permitting manifest obligations` test did not invoke
the shared `useEvidenceTransaction()` helper. Its unconfigured transaction mock therefore returned
`undefined`; the `ROLLBACK` error handler then attempted `.catch()` on that non-promise and masked
the real result. PostgreSQL's `PoolClient.query()` returns a promise, so this was a test-fixture
gap rather than a production regression.

The test now installs the transaction mock before specifying its authorization and insert results.
It continues to assert the fail-closed execution-obligation predicate:
`execution_obligation IN ('build', 'probe')`.

## Verification

- Definitions test: `npx vitest run src/lib/nirmana-elevation/__tests__/definitions.test.ts` — 40/40 passed.
- Evidence route test: `npx vitest run src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts` — 30/30 passed.
- Scoped ESLint for the changed test and definitions module — passed with zero findings.
- TypeScript: `npx tsc --noEmit --skipLibCheck` — passed with zero errors.
- `git diff --check` — passed.

## Scope boundary

Only the focused unit-test fixture and this report were changed. No production implementation,
campaign state, receipt/evidence data, database, migration, deployment, or external system was
modified. The result is local verification evidence only; protected CI and release/deployment
proof remain separate.
