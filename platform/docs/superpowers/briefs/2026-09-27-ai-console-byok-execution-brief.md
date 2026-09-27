---
artifact: CLAUDECODE_BRIEF_AI_CONSOLE_BYOK
type: CLAUDECODE_BRIEF
version: 1.0
status: ACTIVE
authored_by: Native-approved AI Console planning session, 2026-09-27
authority: >
  The native explicitly approved implementation of the AI Console BYOK and user-directed
  routing feature, including an autonomous native surrogate and independent verifier, for
  local development in the isolated codex/ai-console-design worktree. This brief governs
  only that worktree and does not supersede the active L3 brief in any other checkout.
---

# AI Console BYOK and user-directed routing — local implementation

## Objective

Implement every task in
`platform/docs/superpowers/plans/2026-09-27-ai-console-byok-routing.md` against
`platform/docs/superpowers/specs/2026-09-27-ai-console-byok-routing-design.md`.

The result is local-first, additive, secure user-owned AI configuration and routing for exactly
four roles: Synthesizer, Planner, Deep Planner, and Worker. It includes seven API providers,
four locally installed subscription CLIs, named custom configurations, one exact per-user default,
Paripraśna conversation choice, backend default resolution, MCP external synthesis, safe
observability, and Paripraśna-native design.

## Execution location

- Worktree: `/Users/Dev/.codex/worktrees/ai-console-design/Madhav`
- Branch: `codex/ai-console-design`
- Do not mutate `/Users/Dev/Vibe-Coding/Apps/Madhav` or another worktree.
- The root `CLAUDECODE_BRIEF.md` in this worktree is a temporary local dispatcher copy of this
  brief. Never stage or commit that temporary root override. Restore the branch's committed L3
  brief before final branch review and prove the final tracked diff does not change it.

## Governing documents

Read in this order before implementation:

1. Root `CLAUDE.md` and its required session-open sequence.
2. This execution brief.
3. `platform/AGENTS.md` and any nearer `AGENTS.md` for a changed path.
4. The approved AI Console design spec.
5. The AI Console implementation plan.
6. Relevant installed Next.js 16 documents under `platform/node_modules/next/dist/docs/` before
   App Router, route-handler, or caching changes.

The approved spec is product authority. The plan is its implementation argument. Resolve any
conflict in favor of the spec and record the ruling before action.

## May touch

Only plan-required changes inside these surfaces:

- `platform/migrations/1120_ai_console_byok_routing.sql`, or a later unclaimed cross-cutting
  number at or above 1120 selected under the migration rule below.
- `platform/src/lib/ai-console/**`
- `platform/src/app/api/ai-console/**`
- `platform/src/app/ai-console/**`
- `platform/src/components/ai-console/**`
- The exact adapter, model-registry, admin, navigation, Paripraśna, authenticated consult,
  MCP `prashna_ask`, conversation-title, monitoring, and feature-flag files named by the plan.
- The exact unit, DB, Paripraśna gate, mobile gate, and AI Console E2E tests named by the plan,
  including plan-authorized files under `platform/tests/pariprashna/**`.
- `platform/scripts/ai-console/**`, `platform/docs/runbooks/ai-console-local-cutover.md`,
  `platform/package.json`, and the governed example environment template named by the plan.
- The approved spec, implementation plan, and this execution brief only when a discovered
  contradiction must be corrected and the native surrogate records the ruling.
- Git-ignored `.superpowers/sdd/2026-09-27-ai-console-byok-routing/**` for briefs, reports,
  review packages, and the durable progress ledger.

## Must not touch

- The shared checkout, foreign worktrees, foreign branches, or another campaign's state.
- L3 Kāla source/data, its reserved migrations 1070–1119, Pūrṇa migrations 1042–1069, or any
  applied migration.
- Frozen WriterBase/orchestrator contracts, protected corpus/history, L4/L5 doctrine/data,
  unrelated retrieval/capability generators, or unrelated portal work.
- Production, deployed services, shared databases, production data, IAM, secrets, credentials,
  provider accounts, provider terms, billing, branch protection, CI/deploy workflows, or GitHub
  state.
- Root `CLAUDE.md`, `CURRENT_STATE`, `SESSION_LOG`, `CAPABILITY_MANIFEST`, or the live
  `campaign-coordination` branch.
- Security, auth, integrity, migration, watchdog, or test gates may not be weakened.
- No force push, direct-main write, destructive Git cleanup, destructive database operation,
  credential reading/copying/rotation, or fabricated evidence.

## Migration rule

`npm run migration:next` reported 1080 at setup, but 1070–1119 is reserved for L3. Immediately
before Task 2, fetch and read the live coordination ledger and scan both migration directories.
Use 1120 only if it is still unclaimed; otherwise use the next free number at or above 1120 and
update all plan references in the same implementation commit. This local work may proceed with a
provisional non-conflicting number, but a remote coordination claim is a separate external side
effect and is not authorized by this local brief.

## Autonomous decision authority

The primary Claude Code session is the Conductor. A fresh Native Surrogate answers every routine
question that would otherwise wait for the user. The surrogate may:

- interpret the approved spec and plan;
- choose reversible internal structures and task sequencing;
- resolve implementation ambiguity;
- approve focused test repairs and scoped refactors;
- adjudicate reviewer disagreements after the defined fix loop;
- commit plan-scoped local work.

Every material ruling is appended to the SDD ledger as:

`AIC-R### — question — evidence/options — ruling — governing basis — reversibility — cost if wrong`

The surrogate may not change approved product decisions, expand scope, edit applied migrations,
weaken safety, invent credentials or evidence, accept terms, incur unapproved charges, act in an
external account, push, open/merge a PR, deploy, mutate production, or claim acceptance that was
not independently demonstrated.

Missing keys, CLI authentication, a local database, or another external prerequisite does not
pause independent code work. Mark the affected qualification `UNQUALIFIED` with the exact missing
prerequisite and continue every independent task. Never turn a mock into a real-provider PASS.

## Implementation and review topology

- Execute Tasks 1–16 continuously using subagent-driven development.
- One fresh implementer owns one task at a time; implementations are sequential because the plan
  has overlapping interfaces. Implementers do not spawn helpers or reviewers.
- Record the task base SHA, generate its brief, require TDD evidence where specified, focused tests,
  a full relevant gate before commit, self-review, and a durable report.
- After every task, generate a diff package and dispatch a fresh task reviewer for both spec
  compliance and code quality. Critical/Important findings enter the bounded fix and re-review
  loop. Never let an implementer certify itself.
- Dispatch the repository migration guard after Task 2 and the security reviewer after Tasks 3,
  5, 6, 8, 9, 11, 13, 14, and the final cutover work when relevant.
- After all tasks, dispatch one fresh read-only Independent Verifier that did not implement any
  task. It must reconstruct the branch claims from the spec, plan, diff, code, tests, database
  evidence, and running UI rather than trusting implementer reports.
- High or medium final findings return as one consolidated fix wave followed by one scoped
  re-review. The Conductor records residual rulings honestly.

## Independent verification contract

The verifier must explicitly assess:

- exact four-role fidelity and absence of Inspector;
- exactly-one default, live Default, pinned explicit choices, atomic versioning, immutable
  pre-execution snapshots, and append-only actual-role invocation receipts;
- cross-user isolation and authenticated MCP principal-to-user mapping;
- encrypted credentials, request-scoped/non-serializable runtime bindings, redaction, and absence
  of secrets from payloads, logs, audits, fixtures, screenshots, and observability;
- fixed provider hosts plus redirect/body/time limits;
- fixed trusted CLI executables, `shell:false`, isolated temp directories, stripped environment,
  limits/cancellation, and a grant re-check immediately before spawn;
- no provider/model/connection/CLI fallback after an exact choice is resolved;
- flag-off byte compatibility during additive development and no shared-key user-route fallback
  after genuine local cutover;
- MCP internal Planner/Deep Planner/Worker behavior with external synthesis only;
- concurrent default replacement, concurrent configuration versioning, duplicate turn correlation,
  credential replacement in flight, and revocation between resolution and invocation;
- AI Console's three sections only, inline default controls, Paripraśna visual parity,
  accessibility, mobile behavior, and fixed three-row scrolling composer geometry;
- honest separation of code-complete, mocked-contract-tested, DB-tested, locally UI-tested,
  real-provider-qualified, real-CLI-qualified, shared-key audit clean, public CLI terms approved,
  and deployed/live accepted.

## Continuity and stop conditions

The SDD ledger is the recovery authority across compaction or restart. Resume from the first task
without a clean completion line; do not redispatch completed work. Do not ask the user routine
questions or pause between tasks.

If an irreversible/destructive action, security-sensitive external action, push/merge/publish/
deployment, or a plan defect that leaves every path as guesswork is encountered, quarantine that
lane with its exact unblock condition and continue every independent lane. Never broaden authority
to remove the stop.

## Completion

Local execution is complete only when all independently executable plan tasks are committed,
reviewed, and verified; all available focused and broad gates have fresh evidence; the running UI
has been inspected where local prerequisites permit; unavailable real-key/real-CLI/DB evidence is
listed as `UNQUALIFIED`; the shared-key audit state is explicit; every surrogate ruling is listed;
and the final tracked branch diff does not contain the temporary root brief override.

No push, PR, merge, deployment, production change, provider login, or credential entry is part of
this brief.
