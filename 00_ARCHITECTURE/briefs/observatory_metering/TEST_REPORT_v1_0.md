---
artifact: OBSERVATORY_METERING_LOCAL_TEST_REPORT
version: 1.0
status: LOCAL_VERIFIED_PARTIAL
created: 2026-09-30
---
# Observatory metering: local verification follow-up

The dedicated token-free acceptance gate passed on 2026-09-30 in the isolated
`codex/observatory-metering` worktree. This verifies local behavior, not
production operation, provider billing or a signed-in hosted browser flow.
The gate is `python3 platform/scripts/observatory/local_metering_acceptance.py`;
its machine-readable result is [results.json](verification/2026-09-30/results.json).

| Check | Observed result |
|---|---|
| Metering plus affected route tests, flag enabled | 270 passed, 11 skipped |
| Disposable PostgreSQL migration and ledger | 11 passed |
| Whole existing suite, flag default-off | 14,407 passed, 761 skipped, 2 todo |
| Lint | 0 errors, 583 existing warnings |
| TypeScript | Passed |
| Production build with synthetic Firebase values | Passed; nonfatal `@google-cloud/error-reporting` dependency warning about `request` |
| Built-app anonymous HTTP | Usage/admin APIs returned 401; user/admin pages redirected to login (307) |

New enabled-mode tests verify that an owned connection probe persists a start
before fake HTTP, persists safe terminal usage, refuses the HTTP call if start
storage fails, and records a failed probe with unknown usage. They also verify
that shared SDK models fail closed without ownership and keep two concurrent
request attributions separate across awaits. These use synthetic responses and
do not send a prompt to a provider. The database suite tests real PostgreSQL
constraints, RLS, idempotency, pricing freeze, owner scope and recovery in a
temporary loopback cluster.

An exploratory `MARSYS_FLAG_AI_METERING_ENABLED=true npm test` remains red:
133 tests in 19 legacy adapter/validation files failed. Direct adapter tests
have no authenticated metering context; the validation fixture has no ledger
storage and returns zero inserted rows. Fail-closed behavior is the common
cause, not evidence that 133 production flows are broken. We did not weaken
the production attribution rule or silently suppress the flag. The explicit
enabled-mode gate is the meaningful local signal, and a signed-in hosted
flow remains unverified.

The inherited AI Console route audit returned 90 findings in this worktree
and the same 90 in an untouched `HEAD` archive: [delta evidence](verification/2026-09-30/static-audit-delta.json)
shows zero new findings. Clearing those existing routing findings is a
separate AI Console remediation, not a metering regression.

Local `--version` checks made no model call. The [version inventory](verification/2026-09-30/cli-versions.json)
shows Gemini Antigravity 1.2.13 matches its registry pin; Codex 0.155.1 vs
0.158.0, Claude Code 2.1.239 vs 2.1.284, and Kimi Code 2.0.2 vs 2.1.1 do
not match. The local binary paths and `--help` checks alone cannot approve a
pin change. Any live CLI acceptance should first validate the intended
runtime host, exact binary identity, auth and machine output using a small
owned test routed through Madhav, so its aggregate receipt is recorded.

No production migration, provider/CLI generation, deployment, application
commit or protected merge was performed. The metering flag remains default-off.
