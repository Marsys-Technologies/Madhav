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
`external_synthesis` marker to `llm_call_log`; it assigns no model, provider,
tokens, or cost to the external host.

Migration 1120, which remains unapplied, now widens legacy Observatory
provider/stage/status vocabularies, permits absent conversation identity,
allows null model/provider only for the non-usage marker path, and adds a
partial unique marker index. The safe audit vocabulary separately records
confirmed validation success and rejected validation with an allowlisted error
code; database and Zod checks reject raw details.

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

## Unqualified

- PostgreSQL runtime/concurrency/schema behavior remains `UNQUALIFIED`: the 28
  DB-gated tests require `RUN_DB_TESTS=1` and a localhost
  `AI_CONSOLE_TEST_DATABASE_URL` disposable database, neither was provided.
- No real provider key, provider call, local CLI generation, Firebase/OAuth/MCP
  principal, provider pricing/billing result, or external subscription was used.
- No browser acceptance, deployment, push, PR, merge, shared database, or
  production mutation occurred.
- Failed/cancelled stream retry count remains honestly nullable when the
  underlying executor cannot expose a terminal attempt fact; it is never
  invented as zero.
