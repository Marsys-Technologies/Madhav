# NTAP tracker reliability — final-review fix report

## Status

Complete in one bounded final-review wave. All five final-review findings were
addressed without changing campaign, build, dispatcher, or frozen-orchestrator
behavior. No migration was applied outside a disposable test database; no
scheduler, deployment, production endpoint, campaign command, or build command
was invoked.

## Findings resolved

### 1. Baseline operator contract

`docs/runbooks/ntap-tracker-monitor.md` now requires an authorized operator to
take both `candidate_definition_sha256` and `candidate_catalogue_sha256` from the
same fresh authenticated Audit Drawer observation. The obsolete statement that
the catalogue digest is unavailable, and the corresponding halt language, were
removed. The prohibitions on direct SQL, historical JSON/JSONL, manual progress,
manual digest substitution, and scheduler-endpoint bypass remain in force.

### 2. Real PostgreSQL migration contract in CI

`.github/workflows/ci.yml` now provisions a dedicated
`nirmana_monitor_test` database on the existing disposable `postgres:16` service
and runs
`src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/migration-contract.db.test.ts`
with only `NIRMANA_MONITOR_TEST_DATABASE_URL` set. The test itself refuses any
non-loopback host or any database name other than `nirmana_monitor_test`, so it
cannot fall back to `DATABASE_URL` or target production. The local CI service
password is passed through the step environment and is not printed.

### 3. Program-sync ETag regression

The snapshot route regression now makes two otherwise-identical authenticated
reads with fixed time and different candidate definition/catalogue digests, then
asserts distinct ETags. Mutation proof was demonstrated by temporarily removing
`program_sync` from the generation digest: the new test failed because both ETags
became identical; restoring the production hash made it pass.

### 4. Normative audit provenance

The baseline acceptance transaction already had the correct safe provenance
surface: its actor-attributed `asset_label_catalogue_accepted` receipt is written
to the append-only `nirmana_elevation_campaign_events` table in the same
serializable transaction as the frozen definition and label rows. New receipts
now carry `audit_provenance: "normative"`, and the label transaction test asserts
the exact digest, asset count, provenance role, and server-derived actor.

The later `admin_audit_log` write remains intentionally secondary and
best-effort. It is an operator index on an unrelated admin table, is not in the
acceptance transaction, and cannot create, roll back, or erase acceptance. A
transactional outbox was not introduced because the append-only campaign receipt
already provides atomic normative provenance; making acceptance depend on the
admin table would add an unrelated failure domain without improving the source of
truth.

### 5. Per-actor mutation limiting

The explicit `accept_baseline_candidate` command now uses the existing project
per-key RPM limiter with a route-qualified key derived from the authenticated
actor UID. Authorization and schema validation still run first; a denied request
returns `429`, `Retry-After`, and `Cache-Control: no-store` before any acceptance
transaction or secondary audit call. An unexpected limiter failure returns a
sanitized fail-closed `503` before the transaction begins.

This is the same established limiter used by the existing admin MCP-key mutation
route. It is defense in depth: the serializable advisory lock, exact two-digest
check, super-admin authorization, and immutable receipt remain the authoritative
atomicity and provenance controls.

## Verification evidence

- TDD red: the rate-limit route test expected `429` but received `500` before
  limiter wiring; the transaction had begun.
- TDD red: the normative receipt test failed because the receipt payload lacked
  `audit_provenance`.
- Mutation red: removing `program_sync` from the generation hash made the ETag
  regression fail with equal ETags.
- Focused NTAP and limiter suite: 9 files, 179 passed, 6 skipped, 0 failed.
- Real PostgreSQL 16 migration contract: 6 passed, 0 failed against a fresh
  disposable `nirmana_monitor_test` database.
- `npx tsc --noEmit`: passed.
- `actionlint .github/workflows/ci.yml`: passed.
- `git diff --check`: passed.

## Commit

The coherent fix wave uses commit subject:
`fix(nirmana): close NTAP tracker final review`.

## Residual concerns

- The established per-key RPM limiter is process-local and resets when an app
  instance restarts. It is suitable as the requested existing-project-style
  per-actor mutation throttle, but it is not represented as a fleet-wide abuse
  control. The explicit command remains safe under retries and concurrency because
  its authorization, serializable lock, exact digest comparison, and immutable
  receipt do not depend on the limiter.
- Protected CI wiring is authored and syntax-checked here. Only an actual hosted
  CI run can prove the GitHub runner/service-container environment; the same exact
  migration contract passed locally against PostgreSQL 16.
- The secondary admin audit row remains non-authoritative by design. Operators
  must use the append-only campaign receipt when establishing whether acceptance
  occurred.

## Explicit non-actions

No Terraform apply, migration apply to shared/production state, Cloud Scheduler
mutation, deployment, production database access, monitor invocation, acceptance
command invocation, campaign transition, build dispatch, historical-ledger import,
or orchestrator change was performed.
