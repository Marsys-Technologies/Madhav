# Task 13 Report — native Paripraśna exact four-role routing

## Outcome

Implemented the private `AI_CONSOLE_BYOK` serving branch for native Paripraśna,
authenticated Consult, and Consult continuation while preserving legacy paths
when the flag is off.

The flag-on authority order is server-owned: active authentication; strict
selection identity; owner and chart authorization; first-turn selection insert
or existing-turn persisted-selection equality; one resolution; safe immutable
snapshot commit; one non-price BYOK admission; four nonoptional tracked
executors; then streaming. Snapshot or admission failure creates no executor.

## Role routing

- Planner and deterministic Deep Planner receive distinct injected executors.
- Planner structured repair reuses the same selected executor as a separate
  invocation. There is no cross-target retry or fallback.
- Worker is injected into long-history planner compression, durable summary,
  interpretation generation/repair, and title generation. Optional failures
  retain their existing explicit omission, waiver, or deterministic title
  fallback; no alternate AI is called.
- Synthesizer is one pull-driven no-tools stream over gathered evidence. Native
  Paripraśna maps text/reasoning/finish into its existing events; Consult maps
  the same exact executor into its existing AI-SDK wire and shared on-finish
  contract. A flag-on synthesis failure is fatal and cannot become empty
  success.

## Invocation receipts and persistence

Amended unapplied migration 1120 and the repository contract with a
server-generated `invocation_id`. Each actual `generate` or `stream` writes a
start before delegate entry and one succeeded, failed, or cancelled terminal.
Multiple same-role Worker and repair invocations can coexist. Receipt payloads
contain only snapshot, role, invocation, phase/status, and normalized safe error
code.

Persistence uses server-derived Synthesizer identity and records
`ai_routing_snapshot_id`; no runtime binding, credential version, prompt,
output, tool arguments/results, or client model claim is persisted in the new
routing metadata.

## Verification

- Focused preflight, receipt, repository and migration-contract tests: 101 pass.
- Planner/Deep Planner/repair exact-injection plus Consult wire/on-finish tests:
  21 pass.
- Chat/shared/native focused regression aggregate: 107 pass.
- Planner, summaries, interpretation, title and route-port aggregate: 125 pass,
  2 skipped.
- Full Vitest aggregate: 13,148 pass, 730 skipped, 2 todo, with one unrelated
  five-second cache-wiring timeout under aggregate load; the timed-out file
  passed 5/5 immediately in isolation.
- TypeScript: `npx tsc --noEmit` passes.
- Scoped changed-file ESLint (excluding the pre-existing warning-heavy Consult
  monolith): zero warnings. The Consult route retains its pre-existing 63 lint
  warnings; this task introduced no additional scoped warning.
- `git diff --check`: passes.
- Migration number guard: passes with repository baseline warnings only; next
  allocatable migration remains 1121.
- Credential/log scan: no new credential value, prompt/output, runtime binding,
  or raw provider error persistence/logging path found.

## Unqualified

- PostgreSQL-backed migration/isolation tests are skipped without their DB
  prerequisite; no shared or production database was touched.
- No real provider, local CLI, Firebase login, account, credential, or shared
  authentication flow was exercised.
- Exact external monetary cost is intentionally unqualified. The BYOK admission
  path applies rate, concurrency, and request/evidence/output hard caps without
  fabricating provider or subscription pricing.
- No deployment, push, PR, merge, or external runtime qualification occurred.
- Migration 1120 still requires the independently assigned migration review
  required by the execution brief.
