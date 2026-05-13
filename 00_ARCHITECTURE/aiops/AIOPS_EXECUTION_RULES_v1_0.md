---
artifact: AIOPS_EXECUTION_RULES_v1_0.md
canonical_id: AIOPS_EXECUTION_RULES
version: 1.0
status: CURRENT
authored_at: 2026-05-13
authored_by: Cowork brainstorm session (Opus 4.7)
related: 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
purpose: >
  Operational rules that Claude Code follows when executing AIOps phase briefs
  autonomously via `--dangerously-skip-permissions`. Every phase brief assumes
  these rules — they are not repeated in each brief, only cited.
---

# AIOps Execution Rules v1.0

These rules govern every AIOps phase session (CP.0 → CP.5). They are
referenced from every phase brief; they exist in one place so updates
propagate atomically.

---

## R1 — Session-open handshake

At session open, Claude Code:

1. Reads the project root `CLAUDECODE_BRIEF.md`. If `status: COMPLETE`, halt
   and report — there is nothing to do.
2. If `status: OPEN`, parse the `session_id` field. The brief's body is the
   instructions for this session.
3. Read `00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md §10` to confirm
   the phase identifier matches.
4. Read `CLAUDE.md` for project-wide rules (always honored; AIOps does not
   override them, only operates inside their scope boundaries).
5. Read `00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md` (this file).
6. Confirm on stdout:
   ```
   [AIOPS] session_id=<id> phase=<CP.N> brief=<path> rules=v1.0
   ```
7. Proceed to execute the brief.

---

## R2 — Scope discipline

Each phase brief carries a copy of the master plan's `may_touch` /
`must_not_touch` block. Claude Code must:

- Not write any file outside `may_touch`.
- Not delete any file in `must_not_touch`.
- Not modify any file in `must_not_touch` (read-only).
- If a phase requires touching a path not in `may_touch`, BAIL OUT
  (R6) — do not silently widen scope.

A pre-commit grep verifies the staged changes are all within `may_touch`.
If grep finds a violation, the commit is aborted.

---

## R3 — Acceptance criteria (AC) discipline

Each phase brief lists its ACs. Every AC must be **machine-checkable**:
either a shell command exit code, a file-exists test, a grep result, a
test-suite pass count, or an HTTP response. Subjective ACs are never used.

At phase close, Claude Code runs every AC sequentially and records the
result:

```
[AIOPS-AC] AC.CP{N}.1 PASS — <evidence summary>
[AIOPS-AC] AC.CP{N}.2 PASS — <evidence summary>
[AIOPS-AC] AC.CP{N}.3 FAIL — <error summary>
```

If any AC fails, the phase does not close. Go to R6.

---

## R4 — Commit discipline

Within a phase, Claude Code may make as many commits as it wants. The phase's
**final commit** must:

- Use the message format:
  ```
  feat(aiops-CP.{N}): <one-line summary>

  <multi-line body summarizing the phase's deliverables and AC status>

  AC summary: <N>/<M> PASS, <K> DEFERRED, <0> FAIL
  ```
- Include in the staged changes:
  - The `may_touch` files modified during the phase
  - The updated `CLAUDECODE_BRIEF.md` (rewritten with the next phase's content)
  - Any new artifacts under `00_ARCHITECTURE/aiops/`
- Run `npm run typecheck` and `npm run test` (or whatever the project uses)
  and confirm they pass before the final commit.

---

## R5 — End-of-phase handoff

After the final commit, Claude Code:

1. Reads the next phase brief at `00_ARCHITECTURE/aiops/phase_briefs/PHASE_CP_{N+1}_BRIEF.md`.
2. Copies its contents verbatim to project root `CLAUDECODE_BRIEF.md`,
   overwriting the current brief.
3. Confirms the new brief's `status: OPEN` is set.
4. Commits the brief rotation as part of the final commit (R4).
5. Reports session close:
   ```
   [AIOPS-CLOSE] phase=CP.{N} status=CLOSED next_phase=CP.{N+1}
   ```

If the phase is CP.5 (the last), step 1/2 instead rewrites `CLAUDECODE_BRIEF.md`
with `status: COMPLETE` and a native-acceptance note pointing to the master
plan's §17 checklist.

---

## R6 — BAIL OUT protocol

A phase BAILS OUT if any of the following:

- An AC fails after a reasonable retry attempt (the brief specifies how many
  retries are reasonable for each AC; default is 1 retry).
- A scope violation is detected.
- A typecheck or test failure cannot be fixed within the phase's `may_touch`.
- An external dependency (provider API, DB) is unreachable after retry.
- A configuration ambiguity blocks progress and no `BAIL_OUT_DECISION` rule
  in the brief covers it.

When bailing out, Claude Code:

1. Stops further work immediately.
2. Does NOT make the final commit.
3. Writes a `BAIL_OUT` block into `CLAUDECODE_BRIEF.md`:
   ```yaml
   status: HALTED
   bail_out:
     phase: CP.{N}
     reason: <one-line summary>
     last_completed_step: <step or AC>
     attempted_remediations: [<list>]
     suggested_native_action: <plain-text suggestion>
     stack_trace_or_logs: <truncated to 2KB>
   ```
4. Commits ONLY the `CLAUDECODE_BRIEF.md` change with message
   `wip(aiops-CP.{N}): BAIL OUT — <reason>`.
5. Exits with a non-zero shell code so the calling harness knows the run
   was unsuccessful.

Native then investigates, rewrites the brief, and resumes.

---

## R7 — LLM stack discipline

Per the user's standing rule:

- Any code-time LLM call (probes, eval scripts, scaffolds) defaults to
  **Gemini**, falls back to **DeepSeek**, then **NIM**.
- **Anthropic stack is forbidden** as a code-time default. (Anthropic stack
  is selectable in the UI for production use, but Claude Code itself does
  not call Anthropic models when generating probe code, fixture data, etc.)
- If a phase brief mentions a specific model, that model is the intent.
  Substitution requires a BAIL OUT.

---

## R8 — No native pings during a phase

The whole point of autonomous execution is that the native does not get
pinged mid-arc. Claude Code:

- Does not ask the native for clarification mid-phase.
- Does not open chat dialogs requesting input.
- Does not pause and await a "yes / no" reply.

If the brief is ambiguous: the brief is wrong. BAIL OUT (R6) and let the
native fix the brief.

---

## R9 — Test policy

Each phase brief lists the minimum new tests it must produce. Phase ACs
include a count check ("N new tests added in this phase, all pass").

Test runner: `npm run test` (vitest). All new tests live under `__tests__/`
subdirectories alongside the code they test.

For DB-touching code (migrations, repositories, endpoints): integration
tests against a real Postgres (via the project's existing test setup) are
mandatory; mocks are not acceptable.

Provider catalog fetchers: tests use `nock` (or equivalent) to mock the HTTP
endpoints. Live API calls are NOT made in unit tests; they ARE made in the
Stack Smoke flow at phase close (which is a manual / on-demand operation
gated by an env var).

---

## R10 — Migration policy

All migrations are **additive only**. No `DROP COLUMN`, no `ALTER COLUMN
DROP NOT NULL`, no destructive changes. If a column needs replacement, the
pattern is: add new → backfill → switch reads → switch writes → rename in a
later, separate migration.

Each migration is numbered (next available number in the `platform/supabase/migrations/`
directory; check before naming) and includes both an `up` and `down`
function. The `down` function must cleanly drop only what was created — no
side effects.

---

## R11 — Feature flag discipline

The umbrella flag is `AIOPS_OVERRIDES_ENABLED`:

- Default `false` for the duration of CP.1 → CP.4. While false, all
  `getEffectiveModel/Param` calls fall straight through to `STACK_ROUTING`
  registry defaults — system behavior is byte-identical to today.
- Flipped to `true` in CP.5 after stack-smoke on all six stacks passes.
- Removal scheduled 2 weeks after `true` flip, per Phase 11B's clean-up
  precedent.

No other AIOps flags are introduced unless a phase brief explicitly requires
one.

---

## R12 — Observatory non-interference

The Observatory is a SEALED sibling. AIOps may:

- Add a deep-link pencil to `StackBreakdownCards` (CP.3 only; minimal edit).
- Read from the same audit-event tables that the Observatory reads from.
- Emit new events with `pipeline_stage='aiops_probe'`, `'aiops_smoke'`, or
  `'aiops_config_change'` — these flow through the existing observability
  layer.

AIOps may NOT:

- Modify any file under `platform/src/app/api/admin/observatory/`.
- Modify the Observatory's UI routes, components, or filters.
- Edit `OBSERVATORY_PLAN_v1_0.md`.
- Add columns to existing Observatory tables.

If an Observatory change is genuinely required, BAIL OUT and ask the native
to plan a coordinated Observatory + AIOps update.

---

## R13 — LLM stack registry discipline (CallType extension)

Phase CP.1 extends the `CallType` union in `platform/src/lib/models/registry.ts`.
For each new call type, the `STACK_ROUTING` entry for every existing stack
gains a row. The seed values are:

- `eval_judge`: per stack, point at the same `synthesis.primary`/`fallback` —
  this is the conservative default; users override via the UI.
- `eval_generator`: per stack, point at the `planner_deep.primary`/`fallback`.
- `smoke_synth`: per stack, point at the `synthesis.primary`/`fallback`.
- `checkpoint_4_5/5_5/8_5`: per stack, point at the `worker.primary`/`fallback`.

These seeds put real, working defaults in place from the moment the
extension is shipped; no eval/smoke/checkpoint script breaks because a
required entry is missing.

The MARSYS stack is registered as a separate top-level `STACK_ROUTING['marsys']`
block with `synthesis.primary='gemini-2.5-pro'`, `synthesis.fallback='deepseek-v4-pro'`,
and analogous safe defaults for the other call types. Native edits MARSYS
via the UI; the registry value is the starting state.

---

## R14 — Catalog freshness policy

The first read of a provider's catalog in a session triggers a live fetch
(cached 6h). If the fetch returns `>0` models, the cache is updated and
the in-memory snapshot is replaced.

If the fetch fails (timeout, 401, 5xx), the in-memory snapshot is NOT
invalidated. Instead, the catalog response is enriched with a
`stale: true, last_successful_fetch: <timestamp>` flag, and the UI renders
a yellow banner: "Catalog stale — last successful fetch <timestamp>; using
last-known-good snapshot."

A provider whose catalog has *never* successfully been fetched returns an
empty list with `unconfigured: true`; the UI renders a red banner:
"Catalog not yet fetched for <provider> — check API key."

---

## R15 — Phase brief immutability mid-phase

Once a session opens with a given `CLAUDECODE_BRIEF.md`, Claude Code does
NOT edit the brief mid-phase. The brief is read-only for the duration of
its own execution. Only at phase close does Claude Code write the next
brief.

If a brief is found to be wrong: BAIL OUT (R6), do not silently rewrite.

---

*End of AIOPS_EXECUTION_RULES_v1_0.md*
