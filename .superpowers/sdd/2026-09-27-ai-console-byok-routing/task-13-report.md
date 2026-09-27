# Task 13 Report — native Paripraśna exact four-role routing

## Outcome

Implemented the private `AI_CONSOLE_BYOK` serving branch for native Paripraśna,
authenticated Consult, and Consult continuation while preserving legacy paths
when the flag is off.

The flag-on authority order is server-owned. One per-user advisory-lock
transaction now covers active-owner and chart authority, first-turn
conversation/selection initialization or existing-selection equality, exact
resolution, and immutable snapshot insert. A concurrent picker/default update
therefore occurs wholly before or after the turn decision; a failed first-turn
resolution rolls back the conversation and selection together. Only after that
transaction commits does one non-price BYOK admission create four nonoptional
tracked executors.

## Role routing

- Planner and deterministic Deep Planner receive distinct injected executors.
- Planner structured repair reuses the same selected executor as a separate
  invocation. AIC-R031 is implemented as one server-only typed validation
  failure with a private bounded candidate: only that discriminator or a local
  parse/schema failure may enter repair. Provider, authorization, rate, billing,
  and abort failures never repair. The candidate cannot be serialized, logged,
  audited, persisted, or returned.
- Worker is injected into long-history planner compression, durable summary,
  interpretation generation/repair, and title generation. Optional failures
  retain their existing explicit omission, waiver, or deterministic title
  fallback; no alternate AI is called.
- Synthesizer is one pull-driven no-tools stream over gathered evidence. Native
  Paripraśna maps text/reasoning/finish into its existing events; Consult maps
  the same exact executor into its existing AI-SDK wire and shared on-finish
  contract. A flag-on synthesis failure is fatal and cannot become empty
  success.

## Lifecycle hardening

- One request `AbortSignal` reaches planner-history compression, Planner/Deep
  Planner primary and repair, durable summary, interpretation primary and
  repair, title, and Synthesizer/Consult/continuation. Every optional model call
  checks cancellation before it starts; cancellation does not trigger repair.
- Every flag-on role request carries an explicit governed `maxOutputTokens`.
  Hydrated evidence plus attachments are measured against the hard evidence cap
  before a consuming stage, without taking a second admission.
- The admission release is idempotent and attached to all pre-stream setup,
  writer/on-finish, persistence, stream error, cancellation, and normal terminal
  paths. It remains held while streaming.
- Tracked stream cancellation marks intent before waiting for the start receipt,
  prevents a late delegate start, cancels an in-flight pull, and commits one
  cancelled terminal. Continuation cancels every unfinished reader in `finally`.

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

- Focused AI Console, atomic preflight, typed validation, receipts, planner,
  interpretation, native, Consult and continuation aggregate: 528 pass, 25
  prerequisite-skipped.
- Full Vitest aggregate: 13,158 pass, 732 skipped, 2 todo.
- TypeScript: `npx tsc --noEmit --skipLibCheck` passes.
- Full ESLint: zero errors and 587 repository-baseline warnings. Scoped
  changed-file ESLint excluding the pre-existing warning-heavy Consult monolith
  has zero warnings; Consult retains 62 pre-existing warnings and gained none.
- `git diff --check`: passes.
- Migration number guard: passes with repository baseline warnings only; next
  allocatable migration remains 1121. Migration contract: 9 pass; disposable
  PostgreSQL migration/isolation suites: 25 prerequisite-skipped.
- Added real-client concurrency tests for picker serialization and first-turn
  rollback; they are present but remain unqualified until the disposable local
  PostgreSQL prerequisite is supplied.
- Credential/log scan: no new credential value, prompt/output, runtime binding,
  structured candidate, or raw provider error persistence/logging path found.

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
