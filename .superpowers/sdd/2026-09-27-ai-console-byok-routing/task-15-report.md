# Task 15 Report — safe AI routing Observatory and audit metadata

## Outcome

Implemented one strict flag-on observation path at `trackRoleExecutor`. Every
actual native or MCP role invocation now writes its durable terminal receipt
first, then projects the immutable routing snapshot, safe executor descriptor,
and bounded terminal facts into `madhav.ai-routing.v1`. The projection rejects
unknown keys and contains no prompts, completions, provider bodies, headers,
credentials, encryption fields, executable/auth paths, stdout/stderr, or raw
error text. Observatory persistence is non-fatal and cannot repeat model work
or alter receipt truth.

Direct, custom-configuration, Default/explicit, provider, and CLI identities
remain exact. Google alone normalizes to Observatory `gemini`; xAI, Kimi, and
OpenRouter remain distinct, while CLI records provider `cli`, exact product,
and an honest nullable model/built-in-default marker. Missing token usage and
unavailable retry facts remain `NULL`. Known success and safe failure retry
counts propagate through request-local/server-only facts. Monetary cost remains
`NULL` unless exact input and output pricing rows match the provider, model, and
invocation time; CLI calls are never priced.

Native BYOK synthesis is observed once by the tracked Synthesizer executor.
The legacy synthesis observer now explicitly rejects BYOK mode while preserving
flag-off behavior. MCP constructs/observes only actual Planner, Deep Planner,
and Worker calls and writes one idempotent, strict non-usage
`external_synthesis_handoff` marker to `llm_call_log`; its fixed
`not_observed` status says only that Madhav delegated synthesis to the external
host. It assigns no model, provider, tokens, cost, or completion claim.

Migration 1120, which remains unapplied, now widens legacy Observatory
provider/stage/status vocabularies, permits absent conversation identity,
allows null model/provider only for the non-usage marker path, and adds a
named conditional shape constraint plus partial unique marker index. The safe
audit vocabulary separately records
confirmed validation success and rejected validation with an allowlisted error
code; database and Zod checks reject raw details.

## Independent-review fix round 1

- `llm_call_log` now enforces both legal row variants: only the external
  synthesis handoff has null model/provider, while every Madhav-executed stage
  requires both values. Static tests assert the full named constraint body and
  the DB-gated suite exercises both accepted/rejected variants plus replay when
  a disposable baseline database is supplied.
- Stream success commits at the semantic `finish` event before that event is
  exposed. EOF and cancellation after finish are idempotent and cannot replace
  success. Finish-without-EOF and cancel-after-finish are covered.
- Provider and CLI abort paths retain bounded server-only retry facts. Tracked
  cancellation records exact zero before execution and exact one after a
  retry, without exposing upstream abort detail.
- Observatory writes are safely scheduled only after the durable terminal
  receipt and never awaited by generate, stream, or MCP response delivery.
  Never-settling telemetry tests cover all three paths; rejection remains
  internally handled.
- `llm_usage_events.conversation_id` nullability is reflected in the database
  row, public list/detail types, both OpenAPI event schemas, endpoint JSON, and
  the Observatory UI's null handling.

## Independent-review fix round 2

- Migration contract tests now extract each exact named Observatory CHECK
  statement and compare the complete provider, pipeline-stage, and status
  allowlists in order. Values merely appearing elsewhere in migration 1120 can
  no longer create a false pass.
- The disposable-DB lane inserts an accepted usage row for every allowed
  provider, stage, and status, then proves one unknown value in each dimension
  is rejected with CHECK violation `23514`. Safe prompt ids are deleted in the
  test cleanup. This behavior remains runtime-unqualified when the guarded
  database prerequisite is absent.

## Verification

- Focused AI Console/execution/MCP/synthesis/observability/migration aggregate:
  40 files passed, 3 prerequisite-skipped; 685 tests passed, 28 skipped.
- Full platform suite: 1,186 files passed, 80 skipped; 13,272 tests passed,
  732 skipped, 2 todo.
- TypeScript: `npx tsc --noEmit --skipLibCheck` passed.
- Scoped ESLint: `npx eslint --max-warnings=0 ...` passed with zero warnings.
- Migration number guard: passed; migration 1120 remains the highest platform
  migration and no new collision was introduced. Pre-existing disclosed
  duplicate/header warnings were unchanged.
- `git diff --check`: passed.
- Credential/literal-key, environment-key, raw-error logging, and Observatory
  sensitive-family scans found no new secret value or unsafe BYOK persistence.
- Review-fix focused suite: 180 passed, 14 prerequisite-skipped; no failures.
- Review-fix full platform suite: 1,189 files passed, 80 skipped; 13,294 tests
  passed, 733 skipped, 2 todo. The one unrelated capability-cache timeout from
  the immediately preceding run passed 5/5 on targeted rerun before the clean
  full-suite run.
- Review-fix TypeScript, scoped zero-warning ESLint, `git diff --check`,
  migration-number guard, and credential/environment/raw-error scans passed.
- Review-fix round 2 migration focus: 11 passed, 15 DB-gated skipped;
  TypeScript, scoped zero-warning ESLint, and whitespace checks passed.

## Unqualified

- PostgreSQL runtime/concurrency/schema behavior remains `UNQUALIFIED`: the 28
  DB-gated tests require `RUN_DB_TESTS=1` and a localhost
  `AI_CONSOLE_TEST_DATABASE_URL` disposable database, neither was provided.
- No real provider key, provider call, local CLI generation, Firebase/OAuth/MCP
  principal, provider pricing/billing result, or external subscription was used.
- No browser acceptance, deployment, push, PR, merge, shared database, or
  production mutation occurred.
- The DB-gated constraint/replay and complete-vocabulary tests were authored
  but did not execute because no approved localhost `ai_console_test_*`
  database was provided.
