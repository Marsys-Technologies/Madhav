# Task 9 report — governed local CLI execution

Status: FIX ROUND 1 IMPLEMENTED; local fake-executable, aggregate, type, lint, and repository gates passed. Independent re-review pending.
Fix base: `d5def166cced782ff56f8cb82ad7742683d5999b`.
Worktree: `/Users/Dev/.codex/worktrees/ai-console-design/Madhav`.

## Scope completed

- Added a closed four-product CLI registry. Claude Code 2.1.56 is the only potentially executable product. Under AIC-R020, Codex remains registered and filesystem-detectable but has no executable template, compatible roles, auth/version invocation, catalog, routing target, or executor. Gemini/Antigravity and Kimi remain registered but honestly unavailable under AIC-R019.
- Added a governed runner using `shell:false`, a detached process group, isolated temporary working directories, an explicit environment allowlist, stdin-only prompts, byte/time/process-group concurrency caps, fatal UTF-8 decoding, and terminal cleanup. Every terminal path, including success, sends group SIGTERM, escalates repeatedly to SIGKILL after the grace period, and settles only after the process group no longer exists.
- Bound Claude execution to the exact validated entrypoint and fixed Node interpreter chain. Admission records realpath, device, inode, size, modification time, SHA-256 and exact supported version; the complete identity is recaptured immediately before spawn. A content, symlink target, interpreter, version, process-restart, or instance mismatch fails closed without alternate lookup.
- Exposed exactly one built-in-default model for reachable Claude. The private persistence sentinel is projected back to `modelId:null`; no named CLI models are invented, and non-null execution models are rejected before spawn. Stale Codex database rows are masked from user/admin projections and rejected by persistence, routing, authorization, runner, and executor boundaries.
- Grant-gated every version, auth, validation-probe, and execution spawn through `withCliInvocationAuthorization`. The synchronous handle-transfer boundary rechecks the exact active user/grant and cancels an already-started process exactly once if transaction commit fails.
- Added host-global process-local validation admission plus PostgreSQL row-epoch compare-and-set publication/restoration. Abort and revocation restore the prior terminal state only when the same attempt remains current; an orphaned `validating` predecessor falls back to `untested`, while stale/cross-user completions cannot overwrite a newer outcome or catalog.
- Added global CLI validation/catalog persistence, admin grant/revoke persistence and safe audit, active-user CLI list/validate routes, and a super-admin-only grant route. Ungranted user cards reveal only product identity plus `not_granted`; admin cards reveal only coarse host availability.
- Added the CLI implementation of the common `RoleExecutor`, including exact-target text/structured output, normalized usage, pull-driven streaming, cancellation, and one same-target transient retry. Tool-bearing work fails locally because the common contract supplies definitions but no authorized handler authority.
- Registered the CLI executor in the common executor factory and carried the non-enumerable invoking user identity through the request-local routing plan without adding it to safe snapshots.
- Left the Task 1 migration unchanged; no schema defect was found.

## Security and qualification behavior

- Auth-status stdout is capped and discarded at the runner boundary; account identity is never returned, logged, persisted, audited, or included in route responses. Raw stderr is likewise never returned or logged.
- Claude disables user settings, slash commands, tools, sessions, fallback models, and ambient MCP configuration and is launched through the fixed interpreter. Codex is never invoked. Callers cannot provide executables, arguments, flags, hooks, plugins, working directories, environment variables, or MCP configuration.
- Revocation blocks the next spawn. Validation performs a disclosure-safe grant preflight and each process spawn repeats authorization immediately around synchronous process creation.
- The runner attaches an immediate internal rejection observer before transferring its handle, so a fast child failure followed by authorization-commit failure cannot create an unhandled rejection; the original completion still rejects for its legitimate consumer.
- The retained Codex JSONL parser accepts an answer only when exactly one successful terminal completion follows it. Partial output, terminal-before-answer, duplicate terminal, failure/unknown events, and post-terminal events are rejected.
- The implementation and tests sent prompts only to isolated fake executables. No real Codex, Claude, Gemini/Antigravity, or Kimi generation was invoked.

## TDD evidence

RED was observed before the fix for Codex execution policy, strict Codex terminal parsing, stale validation publication, abort/revocation restoration, host-global admission, executable/interpreter identity swaps, successful process groups with lingering/SIGTERM-resistant descendants, fast rejection during authorization failure, and stale Codex routing/projections. Each regression was then taken to GREEN.

The fake-executable matrix covers supported/unsupported versions, missing/non-executable/unsafe files and parents, escaping symlinks and content/interpreter swaps, exact argv/stdin/environment/cwd, built-in-only models, control/leading-dash/oversize rejection, malformed/partial/invalid-order/fragmented machine output, multibyte stdout/stderr limits, stderr redaction, success/nonzero/signal mapping, timeouts, queued and running aborts, normal-success and abort descendant cleanup, SIGTERM-resistant descendants, temp cleanup, global/per-CLI concurrency, grant denial/recheck, commit-failure cancellation/rejection observation, same-target retry, safe card disclosure, stale-row masking, and honest unsupported-product behavior.

## Verification

- Fix-round focused CLI/executor/routes/routing repository: **8 files passed; 136 tests passed**.
- AI Console + adapters + admin-route aggregate: **23 files passed, 2 DB-gated files skipped; 595 tests passed, 23 skipped**.
- The base Task 9 full repository Vitest evidence remains **1,167 files passed, 80 skipped; 13,017 tests passed, 730 skipped, 2 todo**; the fix round did not rerun that full repository gate.
- TypeScript: `npx tsc --noEmit` passed with no diagnostics.
- Scoped ESLint over every changed Task 9 source/test: passed with no diagnostics.
- Whitespace: passed (`git diff --check`).
- Python: skipped because no Python/orchestrator file changed.

## Qualification boundaries

- Real generation for Codex, Claude Code, Gemini/Antigravity, and Kimi: **UNQUALIFIED**. Codex execution is disabled pending an external read-confinement boundary; Gemini/Antigravity and Kimi remain unavailable until a compliant headless machine-readable interface is independently verified. Claude is only potentially executable through the fixed, tool-free template.
- Node/macOS does not expose a safe portable hard descendant-count limit through `spawn`. The implementation therefore limits concurrent process groups, bytes, time, and inputs, kills the complete group on every terminal path, and reports the hard descendant-count cap as **UNQUALIFIED** rather than claiming one. Platforms without the required POSIX detached-group semantics fail closed; Windows execution is disabled.
- Validated executable identities are deliberately process-local because the existing safe schema has no fingerprint field and this fix does not amend the migration. A restart or another instance has no identity confirmation and execution fails closed until that process validates the CLI.
- PostgreSQL runtime/integration: **UNQUALIFIED** because no approved disposable `AI_CONSOLE_TEST_DATABASE_URL` was available; the existing DB-gated tests remained skipped.
- Browser/UI integration, authenticated live-host acceptance, deployment, and shared-key cutover: outside Task 9 and **UNQUALIFIED**.
- No login, auth/config mutation, credential use, real model prompt, shared/production database access, push, PR, merge, or deployment occurred.
- The intentionally dirty root `CLAUDECODE_BRIEF.md` was preserved and excluded from this task's staging.
