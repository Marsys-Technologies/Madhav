# Task 14 Report — MCP mapped-user Default and external synthesis evidence

## Outcome

Implemented the private `AI_CONSOLE_BYOK` branch for high-level MCP
`prashna_ask`. The service gate remains first. Flag-on requests require trusted
API-key/OAuth principal metadata, atomically re-verify that credential mapping,
active profile, chart authority, current symbolic Default, all four roles, and
one immutable MCP snapshot before any executor exists. Managed retries use the
durable job id as snapshot correlation; direct calls mint a fresh UUID.

After commit, the route admits once and constructs tracked Planner, Deep
Planner, and Worker executors only. The captured Synthesizer role is validated
and persisted but never constructed or called. Cancellation is threaded into
the selected planner executor, stream failures are normalized, and the
idempotent admission lease is released on pre-stream error, terminal response,
stream error, or cancellation.

## Evidence contract and compatibility

Flag-on terminal results use `madhav.evidence.v1`, explicitly mark synthesis as
external, and whitelist safe routing and compatibility metadata. The builder
cannot accept arbitrary top-level keys; injected `reading`, model, identity, or
schema overrides are ignored. Synthesizer routing, user identity, credential
version/material, runtime bindings, raw provider errors, full runtime plans,
and internal synthesis results/models are absent. Safety hard stops retain the
fixed safe policy response as `safety_response` without a `reading` field.

Raw evidence retains its independent 1 MiB cap. The final normalized UTF-8
envelope has a dedicated 1.8 MiB ceiling and retrieval arbitration uses a
dedicated evidence budget, not model metadata. Legacy model resolution,
limits, call shape, internal synthesis, progress framing, inquiry behavior, and
raw primitives remain on the flag-off path.

The platform-mcp bridge derives `X-MCP-Auth-Kind` from its authenticated
principal, structurally accepts the evidence outcome, and returns it verbatim
without inventing synthesis.

## Verification

- Initial evidence-boundary red run: 2 tests failed because the server-only
  evidence module did not yet exist.
- Task-focused platform aggregate: 11 files, 264 tests passed.
- Legacy route plus raw primitive registry: 2 files, 102 tests passed.
- platform-mcp bridge: 18 tests passed.
- Platform TypeScript and platform-mcp TypeScript: passed.
- Scoped platform ESLint: zero warnings/errors.
- `git diff --check`: passed.
- Source boundary verifies no synthesis/default-stack imports in the
  evidence-only module; closed-envelope, UTF-8 ceiling, exact API-key/OAuth
  mapping/order, wrong-chart/missing-default, three-executor/no-Synthesizer,
  flag-on route, flag-off compatibility, and bridge regressions are covered.

## Unqualified

- No PostgreSQL runtime or shared/production database was used.
- No real MCP/Firebase/OAuth session, provider, local CLI, account, credential,
  or external monetary cost was exercised.
- No deployment, push, PR, merge, or external runtime qualification occurred.
- `npm ci --ignore-scripts` in `platform-mcp` reported the repository dependency
  baseline of 16 audit findings (9 moderate, 6 high, 1 critical); dependencies
  and lockfiles were not changed by this task.

## Fix round 1

- Managed retries now authorize the durable job before using its id as routing
  correlation or creating a snapshot/executor. Existing snapshots bypass live
  Default and custom-assignment reads, while each pinned role target is
  revalidated against current credential/model or CLI-grant authority.
- Normal and safety-withheld evidence use the same closed plan projection;
  planner parameters, reasons, guidance, raw query fields, and runtime objects
  cannot enter the terminal plan.
- BYOK retrieval/continuation failures log only stable codes plus allowlisted
  trace and tool fields. Provider/adapter error text and objects are excluded;
  flag-off logging remains unchanged.
- Fix-round platform aggregate: 12 files, 273 tests passed; TypeScript, scoped
  zero-warning ESLint, whitespace, credential, import-boundary, and raw-error
  log scans passed.
