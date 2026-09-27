# Task 9 report — governed local CLI execution

Status: IMPLEMENTED; local fake-executable, aggregate, and repository gates passed. Independent review pending.
Base: `501e7070a2edbd77c99243ca566e811fe4003212`.
Worktree: `/Users/Dev/.codex/worktrees/ai-console-design/Madhav`.

## Scope completed

- Added a closed four-product CLI registry. Only the independently inspected Codex 0.155.1 and Claude Code 2.1.56 absolute executable/version/template combinations are enabled. Gemini/Antigravity and Kimi remain registered but honestly unavailable under AIC-R019.
- Added a governed runner using `shell:false`, a detached process group, isolated temporary working directories, an explicit environment allowlist, stdin-only prompts, byte/time/concurrency caps, fatal UTF-8 decoding, process-group TERM/KILL cancellation, pipe draining, and terminal cleanup.
- Hardened executable admission around fixed absolute candidates, accepted realpath prefixes, exact version parsing, executable/owner/writability checks on the file and allowlisted parent tree, and no PATH or alternate-target search.
- Exposed exactly one built-in-default model for each supported CLI. The private persistence sentinel is projected back to `modelId:null`; no named CLI models are invented, and non-null execution models are rejected before spawn.
- Grant-gated every version, auth, validation-probe, and execution spawn through `withCliInvocationAuthorization`. The synchronous handle-transfer boundary rechecks the exact active user/grant and cancels an already-started process exactly once if transaction commit fails.
- Added global CLI validation/catalog persistence, admin grant/revoke persistence and safe audit, active-user CLI list/validate routes, and a super-admin-only grant route. Ungranted user cards reveal only product identity plus `not_granted`; admin cards reveal only coarse host availability.
- Added the CLI implementation of the common `RoleExecutor`, including exact-target text/structured output, normalized usage, pull-driven streaming, cancellation, and one same-target transient retry. Tool-bearing work fails locally because the common contract supplies definitions but no authorized handler authority.
- Registered the CLI executor in the common executor factory and carried the non-enumerable invoking user identity through the request-local routing plan without adding it to safe snapshots.
- Left the Task 1 migration unchanged; no schema defect was found.

## Security and qualification behavior

- Auth-status stdout is capped and discarded at the runner boundary; account identity is never returned, logged, persisted, audited, or included in route responses. Raw stderr is likewise never returned or logged.
- Claude disables user settings, slash commands, tools, sessions, fallback models, and ambient MCP configuration. Codex uses the inspected ephemeral, ignore-config/rules, read-only sandbox template. Callers cannot provide executables, arguments, flags, hooks, plugins, working directories, environment variables, or MCP configuration.
- Revocation blocks the next spawn. Validation performs a disclosure-safe grant preflight and each process spawn repeats authorization immediately around synchronous process creation.
- The implementation and tests sent prompts only to isolated fake executables. No real Codex, Claude, Gemini/Antigravity, or Kimi generation was invoked.

## TDD evidence

RED was observed before the corresponding production changes for the absent runner, registry/validation/executor/routes, catalog-only model enforcement, auth-output disposal, unsafe parent-directory acceptance, and live stream cancellation. Focused regressions were then taken to GREEN.

The fake-executable matrix covers supported/unsupported versions, missing/non-executable/unsafe files and parents, escaping symlinks, exact argv/stdin/environment/cwd, built-in-only models, control/leading-dash/oversize rejection, malformed and fragmented machine output, multibyte stdout/stderr limits, stderr redaction, success/nonzero/signal mapping, timeouts, queued and running aborts, detached descendant cleanup, temp cleanup, global/per-CLI concurrency, grant denial/recheck, commit-failure cancellation, same-target retry, safe card disclosure, and honest unsupported-product behavior.

## Verification

- Task 9 focused CLI/executor/routes: **7 files passed; 36 tests passed**.
- AI Console + adapters + admin-route aggregate: **41 files passed, 2 DB-gated files skipped; 919 tests passed, 23 skipped**.
- Full repository Vitest gate: **1,167 files passed, 80 skipped; 13,017 tests passed, 730 skipped, 2 todo**.
- TypeScript: passed both `npx tsc --noEmit` and the repository `--skipLibCheck` gate with no diagnostics.
- Scoped ESLint over every changed Task 9 source/test: passed with no diagnostics.
- Full repository ESLint: exit 0 with **0 errors and 590 pre-existing warnings**.
- Whitespace: passed (`git diff --check`).
- Python: skipped because no Python/orchestrator file changed.

## Qualification boundaries

- Real generation for Codex, Claude Code, Gemini/Antigravity, and Kimi: **UNQUALIFIED**. Codex and Claude are enabled only from inspected command contracts; Gemini/Antigravity and Kimi remain unavailable until a compliant headless machine-readable interface is independently verified.
- PostgreSQL runtime/integration: **UNQUALIFIED** because no approved disposable `AI_CONSOLE_TEST_DATABASE_URL` was available; the existing DB-gated tests remained skipped.
- Browser/UI integration, authenticated live-host acceptance, deployment, and shared-key cutover: outside Task 9 and **UNQUALIFIED**.
- No login, auth/config mutation, credential use, real model prompt, shared/production database access, push, PR, merge, or deployment occurred.
- The intentionally dirty root `CLAUDECODE_BRIEF.md` was preserved and excluded from this task's staging.
