# PRE-EXISTING CI STATE — main @ f5113c33 (post docs(elevation) commit, pre-run)

Captured 2026-07-25 ~03:51 IST, locally in `~/madhav-alpha`, before any elev/* branch or lane work.
Purpose: so no stream mistakes a pre-existing failure for its own regression.

## Result: ALL FOUR REQUIRED GATES GREEN. Main is clean.

| Gate | Command | Result |
|---|---|---|
| TypeScript (src only) | `npx tsc --noEmit --skipLibCheck` (filtered to non-test errors, per CI logic) | **PASS** — 0 non-test errors |
| TypeScript — platform-mcp | `npx tsc --noEmit` (platform-mcp) | **PASS** — 0 errors |
| Unit Tests | `NODE_ENV=test npm test -- --reporter=verbose` (platform) | **PASS** — 602 files passed / 32 skipped (634); 6818 tests passed / 317 skipped / 1 todo (7136); 0 failed. Includes the WP-1.7 whitelist-resolution and GT-36 parity_check dedicated gates (both pass, part of the same vitest run). |
| Planner Regression Gate | `NODE_ENV=test npm run eval:planner-regression` (platform) | **PASS** — 2/2 tests, `tests/eval/planner_regression_gate.test.ts` |

## Notable non-fatal warnings during unit-tests (expected local-env noise, not failures)
These are `console.error`/logged warnings from code paths that gracefully degrade when
Cloud SQL / Slack / Pub/Sub / rate-limiter DB credentials aren't available in a bare local run —
none of them failed a test or gate:
- `[observability] persistObservation failed: CloudSQLConnectorError: Missing instance connection name` (repeated)
- `[alerts:dispatch] slack dispatch failed for zero_rows_rate ...`
- `[mcp:rate_limiter] Daily token usage query failed; failing open`
- `[mcp:auth] validateMcpKey DB error`
- `[sse/PUBSUB_FALLBACK] Pub/Sub subscription creation failed — falling back to 5s polling`
- `[budget_guard] setGate failed (gate may be unregistered): UNKNOWN_GATE`

None of these are test failures — every test file that emitted them still passed (the code paths are
designed to fail open / degrade honestly). Streams should expect to see the same lines locally and
not treat them as new defects.

## Not run locally (require live/deployed infra, correctly out of scope for a bare local capture)
Per ci.yml, the workflow also includes: Boot-time pointer validation, Coverage Gate, Density Census,
Governance Gates, ICR PR Gate (continue-on-error by design), MCP per-tool smoke battery (plan mode),
Naming Governance Gate, Secret Scan, Census Battery (skips outside schedule), TAP-5/7/S-13, TAP-6.
These are exercised by the PR CI run itself (see PR #763) rather than by this local capture, which
was scoped to the four gates the brief named: typecheck, typecheck-mcp, unit-tests, planner-regression.

## Environment
- Clone: `~/madhav-alpha` (fresh clone off origin/main, deps installed via `npm install` — not `npm ci`,
  since no prior lockfile-verified install existed; CI itself uses `npm ci`).
- Node: v24.14.0 (CI pins Node 20 — local install intentionally left at the environment's default;
  worth a sanity check if a stream sees a Node-version-specific discrepancy vs CI).
