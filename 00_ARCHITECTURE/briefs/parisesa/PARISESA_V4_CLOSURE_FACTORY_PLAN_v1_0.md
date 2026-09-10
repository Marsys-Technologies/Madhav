---
artifact: PARISESA_V4_CLOSURE_FACTORY_CLAUDE_CODE_PLAN_v1_0.md
title: "PARIŚEṢA V4 Closure Factory — Governed Drain-to-Close and Claude Code Continuity Plan"
version: "1.0"
status: STAGED_FOR_OWNER_ADOPTION
authored_on: 2026-08-19
authoring_tool: Codex side conversation
campaign: PARIŚEṢA-RĀTRI V4
finding_corpus: 141
staged_path: /Users/Dev/shad_overnight/par-night/state/codex-v4/PARISESA_V4_CLOSURE_FACTORY_CLAUDE_CODE_PLAN_v1_0.md
canonical_target: 00_ARCHITECTURE/briefs/parisesa/PARISESA_V4_CLOSURE_FACTORY_PLAN_v1_0.md
goal: >
  Preserve the current campaign safely, establish one reconciled 141-finding truth
  ledger, and execute a gated autonomous closure factory in Claude Code until every
  finding has a defensible terminal disposition and the campaign has release proof.
architecture: >
  A single root conductor owns an append-only event journal and deterministic ledger
  projection. Bounded proof, code, contract, and protected-data trains operate through
  isolated leased worktrees, a single protected merge queue, explicit release proof,
  and human gates for policy, security, privacy, and protected writes.
stack: >
  Git and Git worktrees; GitHub protected pull requests and Ganga checks; existing
  PARIŚEṢA state and evidence files; Python/TypeScript project tests; Cloud Run and
  direct MCP proof where authorized; governed session-open and session-close schemas.
spec: >
  This document is the operational specification and execution plan. It becomes
  canonical only after the active Codex session adopts it through the governed
  preservation and handoff procedure.
constraints:
  - Never treat chat history as campaign state.
  - Never write through the dirty primary checkout or a worktree owned by another session.
  - Never use a blanket add, blanket commit, reset, clean, prune, or force operation.
  - Never equate static checks with deployed, live-service, or protected-data proof.
  - Never perform a protected data action without an exact countersigned execution packet.
  - Never let more than one process write the canonical campaign ledger.
---

# PARIŚEṢA V4 Closure Factory

## Governed Drain-to-Close and Claude Code Continuity Plan

## 1. Executive decision

Adopt a **Closure Factory** operating model for the remainder of PARIŚEṢA V4.

The old execution is not abandoned and the new execution is not started on top of it.
The transition is a controlled sequence:

1. Drain the current Codex run without dispatching new work.
2. Preserve every campaign-owned branch, commit, worktree, result, evidence item, and
   reviewed uncommitted change without absorbing unrelated dirt.
3. Produce an explicit stop receipt and preservation manifest.
4. Open Claude Code from a new isolated worktree and a validated session-open record.
5. Reconcile the full 141-finding corpus into one executable ledger.
6. Close the low-risk proof backlog first, then bounded code trains, then contract-led
   repairs, then protected-data work.
7. Seal the campaign only when every row and every programme-level gate is terminal.

This model is **gated autonomous**. Claude Code should continue without asking for
routine implementation decisions, but it must pause at the explicit authority gates
defined in this plan.

## 2. Intended outcome

The campaign is complete only when all of the following are true:

- Exactly 141 unique finding IDs exist in the canonical ledger.
- Every finding has one terminal programme disposition supported by current evidence.
- Every code repair that requires release is reviewed, merged through the protected
  path, deployed to the affected service, and proven at the correct layer.
- Every data-affecting repair has a countersigned packet, narrow lease, before-images,
  execution receipt, postconditions, and service proof where applicable.
- Every control finding is either proven current or closed as an explicitly governed
  residual; a red or unshown control is not described as green.
- Every architecture, security, privacy, or content-authority hold has an owner ruling
  or is recorded as a valid external terminal hold under the campaign policy.
- The generated tracker, summary, board, and handoff all derive from the same canonical
  ledger revision.
- No inflight campaign worker, lock, merge item, deployment, rebuild, or unrecorded
  worktree remains at programme close.
- The final session-close record validates, the repository state is synchronized, and
  the final close report identifies any surviving external obligations without calling
  them complete.

## 3. Why this plan is needed

The campaign has produced substantial value, but end-to-end closure velocity is lower
than implementation velocity because work is fragmented across several truth surfaces:

- the original 141-row closure matrix;
- later manual JavaScript overlays in the generated tracker;
- an older 71-lane board model;
- an append-only event journal with repeated sequence values;
- stale liveness, lock, and external-operation records;
- many branches and worktrees at different source bases;
- evidence that proves code, tests, deployment, or service behavior at different layers;
- protected-data and architecture items that correctly require separate authority.

The bottleneck is therefore not simply writing code. It is converting work into a
current, independently reviewable, released, and terminal finding outcome. The Closure
Factory makes that conversion the unit of throughput.

## 4. Current evidence snapshot and mandatory revalidation

This plan was staged while the active campaign was still changing. The observed facts
below are orientation evidence, not the truth cut:

- The corpus baseline is 141 findings.
- The tracker continued receiving overlays through at least
  `2026-08-19T18:05:00Z`.
- `origin/main` was observed at `9db457dccd07edbc4ca4056e7e522fa5f77897b5`.
- The base `closure-matrix.json` was older than later tracker overlays.
- `inflight.json` was empty when inspected, but stale locks and a stale continuation
  owner were still present.
- The event journal contained 382 records and five repeated sequence values when
  inspected.
- The primary checkout was dirty, six commits ahead of its tracking branch, 34 commits
  behind it, and contained unrelated tracked and untracked work.

These values can drift. Phase 0 must independently recompute all counts and pins after
the current execution has produced a stop receipt.

## 5. Scope

### 5.1 In scope

- All 141 PARIŚEṢA V4 findings.
- Reconciliation of source, review, PR, merge, deployment, data, direct-service,
  governance, and operator evidence.
- Preservation and continuity between the current Codex session and Claude Code.
- Minimal campaign-state tooling needed for deterministic closure tracking.
- Normal reviewed code repair and protected merge-queue delivery.
- Authorized read-only production-shaped verification.
- Explicitly authorized protected-data execution packets.
- Programme close, release proof, tracker generation, and final handoff.

### 5.2 Out of scope without a new owner decision

- New product features unrelated to a finding.
- Broad architecture rewrites that are not required for closure.
- Credential creation, retrieval, rotation, or disclosure.
- Infrastructure mutation, scheduler activation, or workflow-policy changes.
- Database writes, rebuilds, backfills, migrations, or customer-facing actions not
  covered by an exact approved packet.
- Force merges, direct pushes to protected branches, check bypasses, history rewriting,
  worktree cleanup, or deletion of preserved evidence.
- Reclassifying a blocker as complete simply to reach 141/141.

## 6. Governing authority and source order

When sources conflict, use this order:

1. Explicit current owner instruction.
2. Root `CLAUDE.md` and its mandatory-reading sequence.
3. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`.
4. `00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md`.
5. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`.
6. `/Users/Dev/shad_overnight/par-night/PROTOCOL.md`.
7. Validated session-open record and exact work order.
8. Canonical Closure Factory ledger and append-only journal.
9. Direct primary evidence: Git, checks, deployment receipts, database read-only proof,
   MCP responses, and exact result artifacts.
10. Generated tracker, board, summaries, and chat narration.

Claude Code and Codex are equal consumers of governed repository state. Neither tool's
conversation is a source of truth for the other.

## 7. Operating architecture

```text
Current Codex execution
        |
        v
Controlled drain -> preservation manifest -> STOP_RECEIPT
        |
        v
Claude Code session-open + isolated leased worktree
        |
        v
141-row truth cut -> owner Gate A
        |
        v
Append-only events -> deterministic reducer -> canonical ledger
        |
        +--> proof-only train
        +--> bounded code trains -> protected merge queue -> release proof
        +--> contract-first train
        +--> protected-data train -> owner Gate C
        |
        v
141 terminal rows -> programme red team -> final close receipt
```

### 7.1 Single-writer rule

One root conductor is the sole writer of the canonical journal and ledger. Workers may
write only their assigned source files and atomic result artifacts. They do not edit the
tracker, ledger, board, liveness record, or campaign summary directly.

### 7.2 Derived-state rule

The canonical ledger is reduced from append-only events. These are generated views:

- human tracker HTML;
- board summary;
- phase and wave counts;
- blocker queue;
- handoff brief;
- final closure report tables.

Manual tracker overlays stop after the truth cut. A generated view may never silently
override the ledger.

### 7.3 Work isolation rule

- One dedicated Claude Code coordination worktree with a live campaign lease.
- One worktree per active repair train or exact bounded finding bundle.
- No source edits in `/Users/Dev/Vibe-Coding/Apps/Madhav` during this campaign.
- No two active worktrees own the same file.
- A file-level lease conflict is a finding and a dispatch blocker.

## 8. Canonical closure record

Every finding row must contain at least:

```yaml
finding_id: F-001
corpus_checksum: sha256
source_pin: git_sha
classification:
  kind: defect|control|historical|governance
  severity: tier
  mechanism_bundle: [id]
current_reproduction:
  status: reproduced|not_reproduced|not_applicable|blocked
  evidence: [artifact]
repair:
  status: not_required|required|candidate|reviewed|merged
  commits: [sha]
  prs: [number]
verification:
  focused_tests: [receipt]
  independent_review: receipt_or_status
  broad_gate: receipt_or_status
release:
  required: true|false
  deployment: receipt_or_status
  direct_service_proof: receipt_or_status
data:
  action_required: true|false
  packet: path_or_status
  execution: receipt_or_status
authority:
  required: true|false
  ruling: decision_id_or_status
programme_disposition: terminal_status
next_executable_action: one_atomic_action
owner: role
dependencies: [finding_or_gate]
last_meaningful_update: iso_timestamp
evidence_invalidating_conditions: [condition]
```

The real schema may use project naming conventions, but it must preserve these
semantics and must be mechanically validated.

## 9. Terminal disposition policy

A row is terminal only under one of the following policies.

### 9.1 `SERVICE_CLOSED`

Use when the current defect is repaired and all required layers are proven:

- current source or a current reproduction establishes the finding;
- focused tests pass;
- independent review passes on the exact candidate;
- required broad controls are green or a documented exact baseline-aware ruling applies;
- merge through the protected path is complete;
- affected deployment is complete and traffic is verified when required;
- direct service proof passes when the defect is externally observable;
- required data materialization is current.

### 9.2 `HISTORICAL_STALE_CLOSED`

Use when a fresh, current reproduction does not reproduce the historical defect and
the current mechanism is directly evidenced. Source inspection alone is insufficient
when the historical claim was about live behavior.

### 9.3 `CONTROL_CLOSED`

Use when the exact current control, fixture, or detector is executed and its expected
positive and negative behavior is demonstrated. An allowlisted residual remains visible.

### 9.4 `NOT_APPLICABLE_CLOSED`

Use only with a precise current architecture or scope reason and independent review.

### 9.5 `EXTERNAL_HOLD_TERMINAL`

Use only if campaign policy explicitly allows a terminal hold and the owner rules it.
Record the external owner, missing authority, trigger to resume, risk, and the fact that
the underlying work is not complete. This status cannot be converted to
`SERVICE_CLOSED` by narration.

### 9.6 Non-terminal statuses

The following are never programme closure by themselves:

- code fixed;
- tests pass;
- review complete;
- PR open;
- merged;
- deployed;
- data handoff required;
- canary blocked;
- architecture decision required;
- privacy held;
- control source verified;
- current defect reproduced.

## 10. Work-in-progress and flow controls

The default limits are:

- one root state writer;
- two active code trains;
- one proof-only train;
- one contract/spec train;
- one protected merge-queue item at a time;
- one affected-service deployment under proof at a time;
- zero concurrent protected-data writers;
- one protected-data execution only after Gate C.

The conductor may reduce WIP in response to failure. Increasing these limits requires
evidence that queue time, not review/release/proof, is the current bottleneck and that
file ownership remains non-overlapping.

Bundle three to six findings only when they share the same mechanism, affected files,
release unit, and proof path. Never bundle unrelated findings to improve count velocity.

## 11. Phase D0 — Controlled drain of the current Codex execution

### 11.1 Objective

Reach a verified quiescent boundary while retaining all useful work and evidence.

### 11.2 Freeze immediately

After accepting the drain prompt, the current session must not initiate:

- new diagnosis, review, build, or agent dispatch;
- new branch, rebase, PR, merge-queue entry, or deployment;
- new live canary;
- new database, rebuild, migration, scheduler, workflow, credential, or customer action;
- new tracker architecture or campaign-state migration.

### 11.3 Work allowed to reach a terminal boundary

Only operations already authorized and already started may finish:

- an atomic local test or independent review already running;
- an already queued protected merge on an unchanged head;
- an already started deployment and its mandatory verification;
- an already started read-only verification that does not expand scope.

If the session cannot prove an operation was already started and authorized, it stops
that operation and records it as incomplete.

### 11.4 Drain inventory

Inventory, without mutation, all campaign processes, inflight records, locks, leases,
worktrees, branches, detached heads, dirty files, commits not reachable from main, open
PRs, merge-queue state, workflows, deployments, protected packets, results, and event
journal tail. Process matching must be campaign-scoped and must not touch unrelated
automation.

### 11.5 Preservation rules

For each campaign-owned worktree:

1. Record absolute path, branch or detached state, HEAD, merge base, upstream, ahead and
   behind counts, dirty status, and assigned finding IDs.
2. Record every tracked and untracked campaign-owned path with a SHA-256 hash.
3. If the useful work is already committed, record the commit and do not rewrite it.
4. If useful work is uncommitted and exact ownership is proven, choose one governed
   preservation method:
   - create a scoped local commit in that owning worktree only when the current owner
     instruction and latest CCD permit it; or
   - preserve a binary patch plus explicit copies of campaign-owned untracked files
     under a timestamped preservation directory.
5. If ownership is unclear or the worktree contains unrelated dirt, do not commit it.
   Preserve the worktree in place, hash the state, record the collision, and hand it off.
6. Do not use `git stash` as the primary handoff because it hides ownership and is easy
   for another session to overwrite or misapply.
7. Do not push unless separately authorized. Claude Code on the same repository can
   consume local branches, commits, patches, and preserved worktrees.

### 11.6 Canonical plan adoption

The active Codex session may adopt this staged document into the repository only after
it has verified an unowned, isolated preservation worktree and current governance
authority. The intended repository path is:

`00_ARCHITECTURE/briefs/parisesa/PARISESA_V4_CLOSURE_FACTORY_PLAN_v1_0.md`

The adoption commit must contain only this plan and any mechanically required registry
or governed decision entry. It must not be made in the dirty primary checkout or shared
coordination worktree.

### 11.7 Drain artifacts

Create these under `/Users/Dev/shad_overnight/par-night/state/codex-v4/`:

- `PARISESA_V4_CODEX_STOP_RECEIPT_<UTC>.md`
- `PARISESA_V4_WORK_PRESERVATION_MANIFEST_<UTC>.json`
- `preservation/<UTC>/` for patches or explicit untracked-file copies when needed

The stop receipt must include:

- freeze accepted at;
- last allowed operation and its terminal outcome;
- process verification;
- inflight, lock, and lease reconciliation;
- PR, queue, workflow, deployment, and protected-action reconciliation;
- source and journal pins;
- exact preservation-manifest path and checksum;
- unresolved collisions and external operations;
- statement that no new work was dispatched;
- `safe_to_open_claude_code: true|false`;
- reason if false;
- resume entrypoint.

### 11.8 D0 gate

Claude Code must not begin campaign mutations until:

- the stop receipt exists;
- `safe_to_open_claude_code` is true;
- no campaign process or external mutation remains unaccounted for;
- preserved state is readable;
- any remaining live lease is either transferred through the governed procedure or
  released.

## 12. Phase G0 — Claude Code governed session open

### 12.1 Objective

Establish a new tool session without inheriting transient authority or stale state.

### 12.2 Required opening sequence

1. Start Claude Code at `/Users/Dev/Vibe-Coding/Apps/Madhav` only for orientation.
2. Read root `CLAUDE.md` in full and complete its mandatory-reading sequence.
3. Read `CURRENT_STATE`, the CCD register, the governance integrity protocol, the V4
   protocol, this plan, the stop receipt, and the preservation manifest.
4. Verify that `CLAUDECODE_BRIEF.md` is not being used as authority if it is marked
   `COMPLETE`.
5. Inspect all repo and campaign worktrees; do not edit any existing dirty worktree.
6. Create or select a dedicated Claude Code task worktree only through the governed
   lease procedure.
7. Emit and validate the session-open record, including tool identity, model, worktree,
   lease, scope, must-not-touch paths, source pins, mandatory-reading fingerprints, CCD
   consumption, and predecessor stop receipt.
8. Stop if the session-open validator fails.

### 12.3 Initial allowed scope

Before Gate A, the Claude Code session is limited to read-only reconciliation and
creation of new Closure Factory state artifacts in its isolated worktree or designated
state directory. It does not repair findings yet.

## 13. Phase 0 — The 141-finding truth cut

### 13.1 Objective

Produce one current, executable, 141-row ledger from all preserved evidence.

### 13.2 Reconciliation order

For every finding:

1. Confirm unique corpus identity and original claim.
2. Pin the current `origin/main` and relevant service revisions.
3. Reconcile historical ledger events and result artifacts.
4. Resolve candidate branch, commit, review, PR, merge, and deployment status.
5. Determine whether current reproduction is required and safe.
6. Distinguish code proof, release proof, service proof, and data proof.
7. Classify the next executable action.
8. Identify authority and dependency blockers.
9. Assign one owner and one terminal policy.
10. Record evidence-invalidating conditions.

### 13.3 Required outputs

- canonical 141-row ledger;
- append-only normalized event journal;
- source and evidence pin manifest;
- inconsistency report covering all truth-surface conflicts;
- preserved-work adoption map;
- exact counts by terminal status, work class, risk, dependency, and next action;
- critical-path graph;
- proposed first three closure waves;
- Gate A decision packet.

### 13.4 Truth-cut invariants

- row count equals 141;
- finding IDs are unique and match the corpus checksum;
- every evidence reference resolves;
- every commit exists locally or is identified as missing;
- every PR and deployment claim has direct evidence or is marked unverified;
- no row is terminal solely because an older tracker said so;
- generated count totals equal ledger totals;
- conflicting evidence remains explicit until ruled.

### 13.5 Gate A — owner truth-cut approval

Pause and ask the owner to approve:

- the 141-row truth cut;
- terminal-policy definitions;
- architecture/security/privacy/content-authority holds;
- wave ordering and first execution tranche;
- the autonomy envelope for normal PR, merge queue, deployment, and read-only proof.

No repair wave begins before Gate A.

## 14. Phase 1 — Minimal Closure Factory spine

### 14.1 Objective

Make state updates deterministic without turning state tooling into a new campaign.

### 14.2 Minimum capability

Implement only what is needed to:

- validate one event schema;
- append events atomically;
- reject duplicate event identity while retaining historical duplicate-sequence evidence;
- reduce events deterministically into the 141-row ledger;
- validate terminal transitions;
- render tracker, board, blocker queue, and handoff from the ledger;
- prove a clean replay produces byte-stable canonical output.

### 14.3 Acceptance tests

- 141-row uniqueness and checksum test;
- duplicate event idempotency test;
- out-of-order event test;
- invalid terminal transition rejection test;
- missing evidence reference rejection test;
- source-pin invalidation test;
- stable replay golden test;
- tracker-to-ledger count parity test;
- crash-safe atomic-write test.

### 14.4 Scope brake

Do not build a general programme-management platform. If a feature does not reduce
closure-state ambiguity or state-writer contention in this campaign, defer it.

## 15. Phase 2 — Proof-only closure train

### 15.1 Objective

Convert already fixed, historical-stale, merged, deployed, or control-verified work into
terminal outcomes without unnecessary source changes.

### 15.2 Priority order

1. Current source plus safe direct-service reproduction not reproduced.
2. Merged and deployed changes missing one bounded canary.
3. Current controls missing one safe replay.
4. Documentation or governance handoffs with no policy ambiguity.
5. Items blocked by privacy, content authority, or external access.

### 15.3 Per-row proof loop

1. Pin source and deployed revision.
2. Re-run focused evidence where cheap and non-mutating.
3. Execute the minimum safe direct proof at the layer named by the finding.
4. Independently review the evidence against the terminal policy.
5. Append the event and regenerate all views.
6. Reopen immediately if the evidence contradicts the presumed closure.

### 15.4 Proof-train outcomes

Each item exits as:

- terminal;
- reproduced and routed to a code/contract/data train;
- authority held with an exact decision request;
- external dependency held with owner, trigger, and risk.

## 16. Phase 3 — Bounded code closure trains

### 16.1 Objective

Repair current defects in small, releasable mechanism bundles.

### 16.2 Train lifecycle

```text
current red -> exact contract -> implementation -> focused green
-> independent review -> exact broad-gate receipt -> protected PR
-> merge queue -> affected deployment -> direct proof -> terminal ledger event
```

### 16.3 Bundle qualification

A bundle is eligible only when:

- findings share mechanism and release unit;
- file ownership is non-overlapping with active trains;
- acceptance tests are explicit before code;
- no protected-data write is hidden inside the repair;
- the branch starts from a recorded current source pin;
- the full bundle can be independently reviewed as one unit.

### 16.4 Merge and release discipline

- Freeze a candidate before independent review.
- Any post-review change invalidates the review and exact receipts.
- Use normal protected PR and merge-queue paths only.
- Rebase sequentially when bundles share a base or broad gate.
- A green deploy workflow is not sufficient; verify affected traffic and service behavior.
- Record exact PR head, merge SHA, workflow IDs, service revision, traffic state, and
  direct proof.

### 16.5 Failure routing

- Test failure returns to the builder with the exact failing receipt.
- Review failure returns to a reviser, not a new unrelated builder.
- Broad baseline failure pauses only the affected train unless it invalidates the shared
  source pin.
- Deployment failure blocks terminal closure and starts a release diagnosis; it does not
  erase the reviewed code result.
- Direct proof failure reopens the finding even if code, PR, and deployment are green.

## 17. Phase 4 — Contract-first wave

### 17.1 Objective

Resolve findings whose main blocker is not coding but an undefined cross-surface or
content contract.

### 17.2 Contract packet

Each packet must contain:

- defect statement and current reproduction;
- authoritative source and consumers;
- typed input/output or data contract;
- failure and degradation semantics;
- content, classical, privacy, or architecture authority where relevant;
- compatibility constraints;
- migration or rebuild impact;
- test matrix;
- release and direct-proof plan;
- decision options and recommended ruling.

### 17.3 Gate B — policy or architecture decisions

Pause only for decisions that materially select architecture, security posture, privacy
scope, content authority, or public semantics. Once ruled and recorded in the CCD
register where required, convert the packet into a normal bounded code train.

## 18. Phase 5 — Protected-data and rebuild wave

### 18.1 Objective

Execute only the data work that remains necessary after code and contracts are stable.

### 18.2 Required execution packet

Every protected action packet must identify:

- exact finding IDs and approved scope;
- code and schema revision;
- target environment, assets, tables, charts, partitions, or rows;
- live registry closure and affected-set derivation;
- read-only preflight queries;
- before-images and count/checksum invariants;
- serialized lease and writer identity;
- dry-run or shadow-run evidence;
- exact write command or job invocation;
- timeout and abort rules;
- compensation or rollback procedure;
- post-write database proof;
- downstream materialization proof;
- direct service proof;
- privacy and secret-handling constraints;
- expected cost and duration;
- countersignature fields.

### 18.3 Gate C — exact protected-action approval

Pause before every database write, migration, backfill, rebuild, scheduler invocation,
or state flip. Approval for one packet does not authorize another packet or a larger
affected set.

### 18.4 Execution discipline

- Zero concurrent protected writers.
- Reconfirm source, packet checksum, affected set, and lease immediately before action.
- Abort on scope drift, unexpected counts, missing before-images, stale code, lease loss,
  or privacy uncertainty.
- Write an execution receipt even on abort.
- Never call a code merge a data repair.

## 19. Phase 6 — Convergence and programme close

### 19.1 Closure sweep

Recompute all 141 rows from the journal and verify:

- no open next action lacks an owner;
- no terminal status lacks its required evidence;
- no evidence points at a stale source or service revision;
- no protected packet is half-executed;
- no PR, queue item, workflow, deployment, or canary is unaccounted for;
- no worker, lock, or lease is live;
- no generated view differs from the ledger.

### 19.2 Independent programme red team

Use default-REFUTED review of the programme claim. Sample every terminal class and all
high-risk items, data actions, architecture rulings, privacy holds, and release units.
Any material contradiction reopens affected rows and programme close.

### 19.3 Final artifacts

- final 141-row ledger and checksum;
- final event-journal pin;
- generated tracker and board;
- finding-to-commit/PR/deploy/data/proof traceability table;
- protected-action execution receipts;
- external-hold register, if any;
- programme red-team verdict;
- release manifest;
- validated session-close record;
- CURRENT_STATE and SESSION_LOG synchronization;
- final campaign close report.

### 19.4 Gate D — final owner acceptance

Pause for the owner to accept the programme close or the explicitly disclosed terminal
hold set. Do not claim unconditional 141/141 completion if any row is only held.

## 20. Autonomy envelope

### 20.1 Pre-authorized after Gate A

Subject to the project protocols and exact scope, Claude Code may autonomously:

- perform read-only repo, Git, PR, workflow, deployment, and state inspection;
- reconcile evidence and regenerate derived state;
- create isolated leased worktrees;
- implement bounded repairs in approved waves;
- run local focused, type, build, and governance tests;
- request independent review within the execution environment;
- open normal protected PRs;
- enqueue exact unchanged heads through the approved merge queue;
- observe CI and deployments;
- perform safe non-secret read-only canaries covered by the approved wave;
- preserve receipts and continue to the next eligible row.

### 20.2 Mandatory pause conditions

Claude Code must pause for owner input before:

- architecture, security, privacy, or content-authority rulings;
- database writes, rebuilds, migrations, backfills, state flips, or scheduler actions;
- credential, infrastructure, permission, or workflow-policy changes;
- bypassing a required check, force operation, direct protected-branch push, or history
  rewrite;
- expanding the finding corpus or campaign scope;
- accepting an external hold as terminal;
- increasing data-writer concurrency;
- final programme acceptance.

### 20.3 Fail-closed conditions

Stop dispatch and preserve state if:

- the operator says stop or pause;
- another live writer owns the target worktree, file, ledger, or lease;
- the source pin changes unexpectedly;
- the ledger fails replay or count parity;
- evidence or a result artifact is corrupt or missing;
- a credential or private payload appears in output;
- a protected action exceeds its packet;
- a merge or deployment changes after review without requalification;
- cost or time limits are reached;
- three consecutive train attempts fail for the same systemic cause.

## 21. Roles and accountability

### 21.1 Root conductor

- owns state writes, WIP, routing, gates, and stop decisions;
- never implements inside a worker-owned file set while that worker is active;
- records all external operation states;
- keeps the user-facing report short while durable artifacts carry detail.

### 21.2 Truth reconciler

- classifies current state from direct evidence;
- cannot close its own disputed reconciliation without independent review.

### 21.3 Builder/reviser

- owns exact files and tests for one train;
- returns atomic results, commit, diff summary, and evidence;
- never edits campaign state.

### 21.4 Independent reviewer

- reviews an exact frozen candidate and acceptance contract;
- records PASS, QUALIFIED PASS, or RETURN with file-and-line evidence;
- re-reviews after any candidate change.

### 21.5 Release verifier

- verifies protected merge, affected deployment, traffic, and direct behavior;
- distinguishes service proof from data proof.

### 21.6 Protected-data operator

- exists only for an approved packet;
- owns the exact lease and execution receipt;
- has no authority to expand scope.

### 21.7 Programme ratifier

- performs the final default-REFUTED review;
- does not rely on tracker color or campaign narration.

## 22. Prioritization algorithm

Rank eligible work using:

1. terminal closures per unit of safe effort;
2. critical-path unblocking power;
3. release-unit reuse;
4. shared mechanism reuse;
5. severity and user harm;
6. evidence freshness risk;
7. probability of authority or data delay;
8. file collision risk.

Apply this default order:

1. safe proof-only closures;
2. already reviewed/merged/deployed gaps missing one release proof;
3. bounded low-collision code repairs;
4. contracts that unlock multiple findings;
5. high-risk correctness repairs;
6. protected-data packets and execution;
7. policy-held or external-held residues;
8. programme close.

Do not prioritize by finding number, age, or ease of making the tracker look green.

## 23. Metrics and operating cadence

### 23.1 Primary metric

`terminal_findings / elapsed_day`, measured from the canonical ledger.

### 23.2 Supporting metrics

- median finding cycle time from current classification to terminal;
- proof-only conversion rate;
- code-train first-pass review rate;
- merge-queue wait time;
- deployment-to-direct-proof time;
- reopened terminal count;
- stale-evidence count;
- blocked findings by authority class;
- WIP age by train;
- state-write time as a fraction of total effort;
- ledger/tracker parity failures;
- protected packet lead time.

### 23.3 Daily report

Report only:

- terminal count and delta;
- new reproductions;
- active trains and WIP age;
- merged/deployed/proven releases;
- top three blockers and exact requested decisions;
- projected finish range based on the last three completed waves;
- safety or evidence incidents.

## 24. Schedule estimate and recalibration

The pre-truth-cut working estimate for this model is:

- controlled drain and preservation: 0.5–1 day;
- truth cut and minimal spine: 1–2 days;
- proof-only wave: 1–2 days;
- bounded code and contract waves: 2–4 days;
- protected-data wave and final close: 1–3 days.

Expected elapsed range: **5–8 working days** if owner gates are answered promptly,
normal CI/deployment paths remain healthy, and protected-data packets do not reveal a
large rebuild expansion. A more conservative calendar range is **7–12 days**.

Reforecast after Gate A using row-level effort classes and again after the first two
waves. Do not preserve this estimate if the truth cut changes the critical path.

## 25. Principal risks and mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| Current and new sessions overlap | double writes and contradictory state | verified stop receipt before Claude Code mutation |
| Dirty primary checkout absorbs unrelated work | corrupted handoff and unsafe commit | isolated worktree, path-level manifest, no blanket add |
| Tracker overlays differ from base matrix | false counts and wrong dispatch | one truth cut, event reducer, generated-only views |
| Too many workers | review, merge, and state bottlenecks | WIP 2 code trains, one queue, one state writer |
| Static proof presented as live proof | premature closure | layer-specific terminal policies |
| Stale base invalidates review | rework and false defects | pin base, freeze candidate, renew review after rebase |
| Protected rebuild expands unexpectedly | data-integrity risk | exact affected-set packet and Gate C |
| Owner gates wait too long | idle critical path | prepare decision packets early and continue independent safe work |
| Automation tooling becomes the product | delayed closure | minimum spine and explicit scope brake |
| Hidden uncommitted work is lost | duplicated or missing repair | preservation manifest, patches/copies, worktrees retained |

## 26. Execution checklist

### Milestone M0 — Safe handoff

- [ ] Current Codex session accepts the drain prompt.
- [ ] New dispatch and mutation classes are frozen.
- [ ] Already-started authorized operations reach terminal or are recorded incomplete.
- [ ] Campaign-scoped process, lock, lease, PR, workflow, and deployment state is reconciled.
- [ ] All campaign-owned work is preserved without unrelated dirt.
- [ ] Plan is adopted into a safe isolated repo worktree if governance permits.
- [ ] Stop receipt and preservation manifest are written and checksummed.
- [ ] `safe_to_open_claude_code: true` is proven.

### Milestone M1 — Governed Claude Code open

- [ ] Root and mandatory governance documents are read in full.
- [ ] Stop receipt and preservation manifest are ingested.
- [ ] A dedicated leased worktree is established.
- [ ] Session-open validates with scope and must-not-touch paths.

### Milestone M2 — Truth cut

- [ ] 141 unique rows reconcile against current source and evidence.
- [ ] Inconsistencies, collisions, stale claims, and missing artifacts are explicit.
- [ ] Critical path and first waves are generated.
- [ ] Gate A is approved.

### Milestone M3 — State spine

- [ ] Event schema, reducer, validator, and renderers pass acceptance tests.
- [ ] Tracker and ledger counts match.
- [ ] Manual overlays are retired from the active path.

### Milestone M4 — Proof train

- [ ] Safe proof-only backlog is exhausted.
- [ ] Each row exits terminal, routed, or authority held.
- [ ] Reopened findings are immediately reclassified.

### Milestone M5 — Code and contract trains

- [ ] Eligible code bundles follow current-red-to-release-proof lifecycle.
- [ ] Contract packets receive necessary Gate B decisions.
- [ ] Merge and deployment evidence is exact and current.

### Milestone M6 — Protected data

- [ ] Every data action has a complete exact packet.
- [ ] Gate C is granted separately for each packet.
- [ ] Writes are serialized and fully receipted.
- [ ] Data and downstream service proof passes.

### Milestone M7 — Programme close

- [ ] All 141 rows are terminal under approved policy.
- [ ] No live worker, lock, lease, queue item, workflow, or action remains.
- [ ] Independent programme red team passes.
- [ ] Final artifacts and governed session-close validate.
- [ ] Gate D owner acceptance is recorded.

## 27. Exact prompt for the current Codex session

Copy the prompt below into the currently executing Codex session.

```text
OWNER INSTRUCTION — CONTROLLED DRAIN, PRESERVATION, AND CLAUDE CODE HANDOFF

Transition PARIŚEṢA-RĀTRI V4 from this Codex execution to the approved Closure Factory plan. Do not start any new diagnosis, review, build, agent dispatch, branch, rebase, PR, merge-queue entry, deployment, canary, database action, rebuild, migration, scheduler action, workflow change, credential action, or customer-facing action after accepting this instruction.

Allow only already-authorized operations that were already started to reach an atomic terminal boundary: a running local test/review, an already queued protected merge on an unchanged head, an already started deployment with its required verification, or an already started read-only verification. If you cannot prove that an operation was both authorized and already started, stop it safely and record it incomplete. Any explicit stop instruction overrides all earlier autonomy.

Read and obey the current root CLAUDE.md, its mandatory-reading sequence, CURRENT_STATE, the CROSS_CUTTING_DECISION_REGISTER, GOVERNANCE_INTEGRITY_PROTOCOL §P, SESSION_CLOSE_TEMPLATE, the project session-close skill, and /Users/Dev/shad_overnight/par-night/PROTOCOL.md. Treat governed files and direct evidence as authority, not this or any prior conversation.

Use this staged plan as the handoff specification:
/Users/Dev/shad_overnight/par-night/state/codex-v4/PARISESA_V4_CLOSURE_FACTORY_CLAUDE_CODE_PLAN_v1_0.md

Drain procedure:
1. Freeze new work and record the acceptance timestamp.
2. Reconcile campaign-scoped processes, inflight work, locks, leases, worktrees, branches, dirty files, commits not on main, result files, evidence, journal tail, PRs, merge queue, workflows, deployments, data packets, and any external operation. Use campaign-scoped process matching and do not disturb unrelated sessions or automation.
3. Preserve all campaign-owned good work. Never use blanket git add/commit, reset, clean, prune, force, checkout-overwrite, or history rewriting. Do not use the dirty primary checkout or a worktree owned by another writer.
4. For each worktree, record path, branch/detached state, HEAD, merge base, upstream, ahead/behind, status, finding ownership, changed/untracked paths, and SHA-256 hashes. If useful work is already committed, record it. If useful work is uncommitted and ownership is exact, make a scoped local preservation commit only if current owner authority and the latest CCD permit it; otherwise preserve a binary patch plus explicit copies of campaign-owned untracked files under the timestamped preservation directory. If unrelated dirt or ownership uncertainty exists, leave the worktree intact, hash it, and record the collision. Do not use stash as the primary handoff. Do not push unless separately authorized.
5. If a safe isolated preservation worktree and current governance authority exist, adopt the staged plan at 00_ARCHITECTURE/briefs/parisesa/PARISESA_V4_CLOSURE_FACTORY_PLAN_v1_0.md in a commit containing only that plan plus any mechanically required governed registry or CCD entry. Do not adopt it through the primary checkout or shared dirty coordination worktree. If safe adoption is not possible, leave the staged file in place and record that Claude Code must adopt it after session open.
6. Write /Users/Dev/shad_overnight/par-night/state/codex-v4/PARISESA_V4_WORK_PRESERVATION_MANIFEST_<UTC>.json and, where needed, /Users/Dev/shad_overnight/par-night/state/codex-v4/preservation/<UTC>/.
7. Write /Users/Dev/shad_overnight/par-night/state/codex-v4/PARISESA_V4_CODEX_STOP_RECEIPT_<UTC>.md. Include the last allowed operation and outcome, process verification, inflight/lock/lease state, PR/queue/workflow/deployment state, source and journal pins, preservation-manifest path and checksum, plan path and checksum, collisions, unresolved operations, and the exact resume entrypoint. Set safe_to_open_claude_code true only if no campaign mutation is unaccounted for and state is readable.
8. Run the governed session-close procedure. Validate before appending SESSION_LOG or claiming close. Update only the governed state required by the validated close and release only leases owned by this session through the established procedure.

Return a concise drain report with: STOPPED or BLOCKED; safe_to_open_claude_code; stop-receipt path; preservation-manifest path; plan path; source pin; uncommitted-work summary; live external operations; unresolved collisions; and the exact next Claude Code command/prompt entrypoint. Do not resume implementation after the report.
```

## 28. Exact prompt for the new Claude Code session

Run Claude Code against the same local repository after the stop receipt says it is
safe. Paste the prompt below.

```text
GOAL — PARIŚEṢA V4 CLOSURE FACTORY: GOVERNED 141-FINDING TERMINAL CLOSE

You are the root conductor for a gated-autonomous continuation of PARIŚEṢA-RĀTRI V4 in Claude Code. Your objective is to bring every one of the fixed 141 findings to a defensible terminal programme disposition, deliver all required release and data proof, and close the campaign under project governance. Continue autonomously through routine, pre-authorized work; pause only at the explicit gates below.

Do not inherit authority or state from this prompt or any prior chat. Begin by reading the repository root CLAUDE.md in full, then complete its mandatory-reading sequence. Read, in this order, 00_ARCHITECTURE/CURRENT_STATE_v1_0.md, 00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md, 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §P, /Users/Dev/shad_overnight/par-night/PROTOCOL.md, the newest /Users/Dev/shad_overnight/par-night/state/codex-v4/PARISESA_V4_CODEX_STOP_RECEIPT_*.md, its referenced preservation manifest, and the Closure Factory plan. Prefer the canonical repo copy if it exists; otherwise read:
/Users/Dev/shad_overnight/par-night/state/codex-v4/PARISESA_V4_CLOSURE_FACTORY_CLAUDE_CODE_PLAN_v1_0.md

Do not use a CLAUDECODE_BRIEF.md marked COMPLETE as current authority. Do not edit the dirty primary checkout, a shared dirty coordination worktree, or any worktree with a live owner. Verify safe_to_open_claude_code is true. If it is false, absent, stale, or contradicted by a live campaign process/external operation, fail closed and report the exact blocker.

Open correctly:
1. Inventory repo and campaign worktrees and preserved work without mutation.
2. Acquire/verify the governed campaign lease and use a new isolated Claude Code task worktree.
3. Emit and validate SESSION_OPEN with tool/model identity, predecessor stop receipt, mandatory-reading fingerprints, worktree, live lease, current origin/main pin, CCD entries consumed, declared may-touch paths, and explicit must-not-touch paths.
4. Before owner Gate A, perform only read-only reconciliation and creation of new Closure Factory state artifacts in the isolated governed scope.

Execute the plan phase by phase:
D0 is complete only if the stop receipt remains valid.
Phase 0: independently reconcile all 141 findings against current source and direct evidence. Produce one canonical 141-row ledger, normalized append-only event journal, source/evidence pin manifest, inconsistency report, preserved-work adoption map, critical path, exact counts, and first three proposed waves. Do not trust old tracker counts or manually layered HTML. Pause for Gate A with a compact decision packet.
Phase 1: after Gate A, implement only the minimal deterministic event/reducer/validator/rendering spine. One root writer owns state. Tracker, board, blocker queue, and handoff are generated views. Prove 141-row parity, idempotency, invalid-transition rejection, source invalidation, stable replay, and atomic writes.
Phase 2: exhaust safe proof-only closures first. Every row exits terminal, reproduced-and-routed, or explicitly authority/external held. Static checks are never live proof.
Phase 3: run at most two bounded code trains, one proof train, one contract train, and one protected merge item. Bundle only common mechanisms and release units with non-overlapping file leases. Use current red -> contract -> focused green -> exact independent review -> exact broad gate -> protected PR -> merge queue -> affected deployment -> direct proof -> terminal event. Any candidate change invalidates review and receipts.
Phase 4: produce contract packets for cross-surface, architecture, security, privacy, and content-authority gaps. Pause at Gate B only for material policy decisions; record rulings in the CCD register when required, then continue autonomously.
Phase 5: prepare exact protected-data packets but perform no database write, rebuild, migration, backfill, state flip, scheduler action, or infrastructure action without a separate Gate C owner approval for that exact packet and affected set. Use zero concurrent data writers, a narrow lease, before-images, abort rules, compensation, and post-write plus direct-service proof.
Phase 6: when all rows are terminal under the approved policy, run a default-REFUTED independent programme red team, reconcile every process/lock/lease/PR/queue/workflow/deployment/action, generate the final traceability and release artifacts, validate SESSION_CLOSE, synchronize governed state, and pause for Gate D owner acceptance. Do not claim unconditional 141/141 if any item is only held.

Autonomy after Gate A includes read-only inspection, deterministic state updates, isolated worktrees, bounded source/test changes, local checks, independent review, normal protected PRs, approved merge-queue use, observing CI/deployments, and approved non-secret read-only canaries. Pause before architecture/security/privacy/content rulings; credentials; permissions; infrastructure or workflow changes; all protected data actions; bypass/force/history rewrite; scope expansion; terminalizing an external hold; or final programme acceptance.

Safety rules:
- Explicit owner pause/stop overrides everything.
- Never blanket add/commit, reset, clean, prune, force, or overwrite another worktree.
- Never let workers edit the canonical ledger or tracker; they return atomic results to the root writer.
- Never equate code fixed, tests passed, PR merged, or deploy green with full service/data closure.
- Never print or retain credential values or private payloads.
- Stop dispatch on writer collision, stale source, ledger replay failure, corrupt evidence, scope drift, lease loss, or three repeated systemic train failures.
- Preserve useful local work using scoped commits when governed authority permits, otherwise a checksummed manifest plus patches/untracked copies; never hide the handoff in stash.

Maintain a concise durable cadence: update the canonical ledger after each atomic result; report terminal count and delta, active WIP, releases proven, top blockers, and forecast after each wave. Keep working until a mandatory gate, a fail-closed condition, or verified programme close is reached.

Your first response must state: proposed governed session name; documents and stop receipt located; safe-to-open verdict; intended isolated worktree/lease; exact pre-Gate-A scope; and the Phase 0 reconciliation actions. Then execute those actions rather than merely restating this prompt.
```

## 29. Operator launch sequence

1. Paste the §27 prompt into the current Codex execution.
2. Wait for a stop receipt with `safe_to_open_claude_code: true`.
3. Verify the receipt names the preservation manifest and plan checksum.
4. Start a fresh Claude Code session in the same repository.
5. Paste the §28 prompt.
6. Review and decide Gate A when Claude Code returns the truth-cut packet.
7. Thereafter answer only Gate B, Gate C, and Gate D decisions or unexpected
   fail-closed escalations; routine work should continue autonomously.

## 30. Success statement

This plan succeeds when the transition preserves all current value without cross-session
collision, Claude Code reconstructs the campaign from governed durable evidence, and the
Closure Factory converts the 141-row corpus into verified terminal outcomes with an
auditable release and data trail. Speed is improved by reducing state ambiguity, limiting
WIP, prioritizing proof conversion, and keeping one continuous path from finding to
release proof—not by weakening the definition of done.
