---
artifact: JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT
version: 1.0
status: ACTIVE
authorized_by: native
authorized_on: 2026-09-27
coordination_request: JATAKA-REQ-01
migration_reservation: 1120_jataka_conversation_archive_context.sql
changelog:
  - v1.0 (2026-09-27): Initial native-authorized parallel local-execution amendment.
governs:
  worktree: /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
  branch: codex/jataka-chart-workspace
  plan: platform/docs/superpowers/plans/2026-09-27-jataka-chart-workspace.md
  specification: platform/docs/superpowers/specs/2026-09-27-jataka-chart-workspace-design.md
supersedes: none
---

# Jātaka Chart Workspace — Parallel Local-Execution Amendment

## 1. Decision and relationship to the active campaigns

The native authorizes the Jātaka chart-workspace feature as a narrow, local-first product
workstream that may run in parallel with the active L3 Kāla and Pūrṇa Anveṣaṇa campaigns. This
amendment does **not** close, replace, pause, reinterpret or take territory from either campaign.
It is the specific exception required by root `CLAUDECODE_BRIEF.md`; all unmentioned governance
rules remain in force.

The authority applies only when all of these assertions are true:

1. Worktree is exactly `/Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav`.
2. Branch is exactly `codex/jataka-chart-workspace`.
3. Commit `f95a8a4ca` is an ancestor of `HEAD`.
4. The worktree is clean at session open except for ignored dependency/runtime files.
5. The session declares this amendment, `JATAKA-REQ-01`, and the implementation plan in its
   validated session-open handshake.

Failure of any assertion is a stop condition, not permission to repair another worktree or branch.

## 2. Authorized delivery ceiling

Claude Code may inspect, implement, test, document and commit the plan's **Tasks 1–8** locally.
It may use mocks, unit/component tests and source-level contract tests that require neither a real
Firebase session nor a database. It may create the reserved migration source file, but it may not
apply it to any database under this phase.

This authority does not include push, pull-request creation, merge, deployment, traffic change,
production or shared database access, migration application, chart rebuild, real-user chart edit,
credential/secret/IAM/infrastructure changes, or mutation of any foreign branch/worktree/campaign
state. Those require later, separately recorded authority.

## 3. Exact source scope

The authoritative file allowlist is the implementation plan's `File Map` plus the task-specific
`Files` blocks for Tasks 1–8. The following paths are discovery bounds, not blanket authority to
edit unrelated files:

- `platform/src/app/dashboard/page.tsx`
- `platform/src/app/clients/[id]/**`
- `platform/src/app/api/charts/[id]/**`
- `platform/src/app/api/cockpit/runs/route.ts`
- `platform/src/app/api/cockpit/runs/__tests__/route*.test.ts`
- `platform/src/app/api/chat/consult/**`
- `platform/src/app/api/conversations/[id]/route.ts`
- `platform/src/app/api/pariprashna/__tests__/route.test.ts`
- `platform/src/components/dashboard/**`
- `platform/src/components/profile/**`
- the exact client, dialog, consume and Paripraśna component/test files named by the plan
- `platform/src/lib/charts/**`
- `platform/src/lib/build/**`
- `platform/src/lib/conversations.ts`
- `platform/src/lib/conversations/**`
- `platform/src/lib/pariprashna/pipeline/safety_gate.ts`
- `platform/src/lib/roster/types.ts`
- `platform/supabase/migrations/1120_jataka_conversation_archive_context.sql`
- `platform/tests/unit/migrations/jataka_conversation_archive_context.test.ts`

The linked design, implementation plan and this amendment may be updated only to correct execution
facts or record evidence; they are not a route to enlarge product scope silently.

## 4. Explicit exclusions

- All `platform/python-sidecar/**` code, frozen `WriterBase`, runner/asset-runner transaction
  contracts, Jyotish computations, governed asset definitions and generated L3/Pūrṇa artifacts.
- Every L3 Kāla source/state/evidence path, its worktree/branches and migrations `1070–1119`.
- Every Pūrṇa source/state/evidence path, its worktree/branches and migrations `1042–1069`.
- Production/shared Firebase, PostgreSQL, Cloud Run, GCP, GitHub protected integration and real
  chart/user data.
- The shared checkout `/Users/Dev/Vibe-Coding/Apps/Madhav` as an implementation surface.
- A Firebase Auth emulator path. That is an architectural addition and needs a separate amendment.

If implementation reveals that a correct solution needs any excluded surface, stop and report the
exact dependency. Do not weaken the feature or broaden scope to work around it.

## 5. Migration ruling

`1080` is invalid because `1070–1119` is reserved for L3 Kāla. `JATAKA-REQ-01` reserves the first
cross-cutting number, `1120`, for
`platform/supabase/migrations/1120_jataka_conversation_archive_context.sql`.

The reservation is recorded on authoritative `origin/campaign-coordination`. Immediately before
creating the migration file, re-fetch protected `origin/main`, inspect every open pull request's
migration file list, and run the repository migration-number guard. If `1120` has acquired a newer
claim, stop, reserve the next free number at or above `1121`, and update the plan and coordination
record before writing the file. The numeric guard alone is not sufficient.

## 6. Two-phase execution and environment gate

### Phase A — authorized now

Implement plan Tasks 1–8 with TDD and the plan's per-task commits. Tests may use mocks and local
fixtures that cannot contact external services. This phase can establish source/local-test
evidence only.

### Phase B — blocked until separately evidenced

Plan Task 9 and the browser/full-recompute acceptance journey remain blocked until all three exist:

1. Firebase Admin credentials for a non-production test project, supplied through an ignored local
   environment file without printing or committing values.
2. A disposable local PostgreSQL database whose parsed hostname is `localhost`, `127.0.0.1` or
   `::1`, owned by this workstream and not by another session.
3. An approved local L0 seed/snapshot or deterministic seed procedure sufficient for the frozen
   rebuild to finish.

Do not copy the shared checkout's `.env.local`, use production credentials/data, or reuse the
PostgreSQL instances on ports `55432`/`55433` owned by other L0 sessions. If the gate is still
closed after Tasks 1–8, record Task 9 and acceptance criterion 11 as `Blocked`. Do not claim the
feature is locally proven, accepted, complete or ready to ship.

## 7. Evidence and close rules

- Per-task source tests must pass before each task commit.
- Run migration-number, formatting, type and affected test checks named in the plan.
- Preserve exact failing output for any blocked or failed check; do not convert unavailable proof
  into a pass.
- A Phase-A close may say `Tasks 1–8 implemented and mock-tested`; it may not say `complete`.
- No implementation-session edit to this amendment, root `CLAUDECODE_BRIEF.md`, L3 state or Pūrṇa
  state is allowed merely to remove a blocker.

## 8. Close condition

This amendment stays `ACTIVE` while Phase A is being implemented. It becomes `COMPLETE` only after
the native receives an evidence-backed report that either:

- Phase B passed against the approved disposable environment; or
- the workstream closed honestly with Phase B explicitly blocked or deferred.

Changing this status does not change the status of L3 Kāla or Pūrṇa Anveṣaṇa.
