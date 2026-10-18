---
status: HISTORICAL — superseded by v3.0 (A8)
artifact: KALAYANTRA_RELAUNCH_PLAN_v2_7.md
status: DRAFT — for Astra's confirmation review, then native approval. Supersedes v2.2 (ASTRA_REVIEW v2.2: PROCEED-WITH-FIXES, KU-01…KU-03 → B-0c). v2.7 applies Astra's confirmation review of v2.6 (PROCEED-WITH-FIXES, KY-01); v2.6 applied KX-01…KX-03; v2.5 applied KW-01…KW-06; v2.4 applied the delta review of v2.3 (KV-01…KV-08) to the autonomy model the owner directed on 2026-10-11 (resume-anywhere sessions, a persistent owner surrogate, headless loops under launchd, zero-idle scheduling) and the two launch defects the planner proved by execution (P-1 `--bare` cannot sign in; P-2 program version). On approval this plan and its paired prompts and cards are the only operating rules of KĀLA-YANTRA v3; CHARTER v1.2 keeps §0 (goal) and its five hash-pinned specification documents; the VELOCITY AMENDMENT is retired; the strategy is historical rationale only.
version: 2.7
authored_by: Claude Code (Fable 5.1), worktree kalayantra/relaunch-plan
authored_on: 2026-10-11
audience: Astra (reviewer); native (approver); the cockpit session (KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md); the headless loop controllers and their jobs
paired_prompts:
  - KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md        # the ONE prompt the owner pastes into any new session (resume-anywhere)
  - fleet/prompts/CONDUCTOR_LOOP_v2_4.md         # headless conductor loop prompt (B-0c deliverable; never pasted)
  - fleet/prompts/PLANNER_LOOP_v2_4.md           # headless planner loop prompt (B-0c deliverable; never pasted)
owner_decisions_file: KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md
pairing_rule: >
  ONE owner paste (the cockpit prompt). Its <APPROVED_SOURCE_COMMIT> binds the plan, the
  cockpit prompt, the owner decisions, the strategy and the surrogate agent definition
  (byte-identical to their tracked blobs at that commit, checked by `git cat-file -e` and
  `git diff --quiet`). B-0c generates an independently reviewed **bootstrap manifest**
  (`run/VERSIONS.bootstrap.json` + its review receipt) binding every generated card, schema,
  launcher input and loop prompt to that source commit; the bootstrap supervisor verifies
  the manifest and its review receipt before every bootstrap launch. **Final activation**
  (B-5) records an immutable `run/ACTIVATION_RECORD.json` {final manifest digest, source
  commit, authorising act: owner cockpit command or effective D-4 surrogate decision id};
  the launcher passes that approved digest to every conductor job as an argument taken from
  the activation record, never from the installed manifest it is verifying. Bundle changes
  follow the same reviewed activation procedure; changed inputs invalidate the affected
  acceptance receipts. **Successor bundles (KW-04):** the initial owner-pasted source
  commit remains the trust root. A bundle change requires independently reviewed immutable
  source and either an owner authorisation or an effective D-4 surrogate decision (changes
  to the owner decisions stay owner-only). Each change writes an immutable activation record
  linking the preceding record, old/new source commits, old/new manifest digests, review
  receipts and the authorising act; a bootstrap activation authorises bootstrap sources only,
  never campaign admission. On every fresh cockpit entry the session first loads the trusted
  cockpit instructions from the original commit, verifies the authorisation chain to the
  active source, then verifies the active files against that authorised commit and loads
  its prompt; with no valid successor chain it falls back to the original five-file
  comparison and stops on mismatch. A successor is never accepted merely because the installed files or an activation pointer
  name it. **Bundle entrypoints (KX-03):** the initial trust root uses its five explicitly
  named files; every successor manifest includes a reviewed `entrypoints` mapping for
  `plan`, `cockpit_prompt`, `owner_decisions`, `strategy` and `surrogate_agent` with
  repository-relative paths and blob hashes, and the activation record binds that
  manifest's digest. After validating the authorisation chain, the session verifies the
  mapped files against their tracked blobs at the authorised source commit `C` and loads
  the mapped cockpit prompt; a successor need not keep the root bundle's versioned
  filenames; a changed owner-decisions blob additionally requires owner authorisation.
  **Surrogate authority loading:** the caller supplies the authorised source commit and the
  verified entrypoint binding in the immutable job input; the surrogate reads the mapped
  active plan (§4a, §15), the mapped owner-decisions record and the reviewed source-bound
  OWNER_SURROGATE card before ruling, refuses missing or mismatched bindings, and never
  falls back to a retired plan or infers authority from installed filenames. The former
  two-paste workflow is retired everywhere.
authority_precedence: root CLAUDE.md (§I, §N; read first, as always) > owner decisions (§15) > this plan > cards > packets > anything a job infers
evidence: 00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md (audit worktree, 758e0dbb4); reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v1_0.md and _v2_0.md; scratch notes_ky_state.md, notes_suvarna_state.md, notes_workflow.md, KY_MECHANICS_CATALOGUE.md (2026-10-11)
---

# KĀLA-YANTRA v3 — relaunch plan v2.7 (Claude, event-driven, fully autonomous, essential governance only)

## 0. Goal, definition of done, scope (KS-01)

**Goal (CHARTER §0, unchanged):** build the Kāla layer as one engine per PLAN v1.1 §9 /
ALGO v1.1 (21 cards), absorb Gochara 5.0 to its "5.0" flip, rebuild and serve the layer
for chart `482012f1`, ship certification mappings, close with a validated SESSION_CLOSE
and a finalizer receipt. Suvarṇa certifies the Kāla assets afterwards.

**Retained acceptance set (owner decision §15.4):** (i) Kāla serves `482012f1`
end-to-end — every published Kāla read model answers for that chart from a rebuilt
layer; (ii) the Gochara 5.0 flip is sealed; (iii) certification mappings exist for every
served Kāla asset; (iv) a guarded close.

**Closure procedure (B-0, reproducible):**
1. First commit `00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v2_1.json`: an
   acceptance-to-item mapping for (i)–(iii), each root citing the producing item's brief
   and detector. The old `JOIN-ALL`/C-chain is **not** a scope root; the mechanical close
   chain is regenerated afterwards from the retained set.
2. Compute prerequisites from those roots: `depends_on` supplies item edges; `steps`
   are intra-item obligations, not item IDs; joins use `done_by: join` consistently with
   `join`; `requires_outcome` supplies decision conditions, with explicit dependencies
   on unresolved decisions. Preserve `accepts_not_applicable_dependencies` and propagate
   skipped-input gaps: a skipped prerequisite can never silently satisfy a retained
   acceptance. Output `CLOSURE_v2_1.json` (deterministic; two runs give one hash).
3. Everything in the closure is **(a) critical path**. Outside it: **(b) deferred**
   (`ky park --as steward --detail "…; re-entry: …"`, never counted as closed) or
   **(c) dispositioned** (inherited Pravāha material, per an independently accepted
   `J0_DISPOSITION` artifact). A missing required column is never evidence that its
   consumer is deferrable: it becomes an Opus schema-prerequisite item (new namespaced
   id `KV3-SCHEMA-<n>`, additive migration, protected window if needed) or an explicit
   blocked contract decision.
4. Retirement by decision: register `D-RETIRE-B-K-INBOX` and `D-RETIRE-B-CLAIM-RECOVERY`
   in the model; map each unfinished item's `requires_outcome` to `approved`, and stage
   the owner-authorised `refused` decision to be published by the installation/model
   migration action (B-2), never by a test. Newly registered relaunch bootstrap work uses
   new namespaced ids (`KV3-B-*`).
5. Two reconciliation tests (checked in): **path-only migration** — identical item
   states from one hashed EVENTS prefix, one captured detector-result map and one fixed
   clock; **triage** — compared against a reviewed expected delta covering
   dependencies, dispositions, readiness and close membership, preserving earned
   guarded completions and their evidence.

**Deferral candidates examined first:** J-7 (optional Tier-2 Sudarśana, outside sealed
5.0), J-7b (documentation-only), D-T2 and L0-K (only if the closure shows their corpus
work is not needed for (i)–(iii)). No reduced count is claimed before the closure exists.
Partial failure closes `CLOSED-PARTIAL` with the (b) list attached.

## 1. Principles

1. Single-pointed: accurate, high-velocity implementation of the critical path;
   governance and security kept where they protect correctness, production or honesty.
2. Jobs, not lanes: a model runs only for a named job with a packet, then exits.
3. Deterministic first: scheduling, claims, locks, gates, routing, allocation, test
   installation, regeneration, metering are scripts with tests and negative fixtures.
4. Packets carry the truth the builder needs; immutable pins are separated from the
   checkout base and the migration allocator.
5. Every signal is earned (CLAUDE.md §N.8): detector + negative fixture, or WAIT/unknown.
6. Token economy by construction: no idle model turns, small fixed context per job,
   diff-first review with independent tests, bounded conductor, one accounting owner per
   session.

## 2. Starting point — what exists and is reused

| asset | state | reuse |
|---|---|---|
| Tracker `ky` (pravaha_tracker on 8767; EVENTS.jsonl) | lock-safe claims, guarded typed `ky done`, verdict identity, `ky next --json`, `ky inbox --wait`, steward override | the single ledger; wrappers re-pointed and made override-preserving (§5) |
| Live plan model (148 items; uncommitted mirror edits) | 39 guarded completions + 1 join + 6 decisions = 46 of 148 (31.1 % plain; 37.6 % weighted) | committed and reconciled in B-0 |
| 20 merged engine items, `kala_core`, CI canary, `Kāla DB Tests` job | on main | built upon; the DB job is retained as an admission check (§3) |
| 11 ACCEPTED-unmerged PRs | frozen by HOLD_MERGES | Wave 0 under the patch-proof inheritance rule (§6) |
| Five hash-pinned specification documents | hashes match | packet sources |
| Item briefs | 148 live | packet inputs after contract reconciliation (§8) |
| `fleet_live/*` helpers, `executor.py` + `executor_ops.json`, protected-window mechanism | work for the old topology | kept; re-pointed, extended and re-tested in B-1; executor authority boundary unchanged |
| Learned rules (KARAKA/PARIKSAKA) | written by the campaign | folded into cards |
| Token audit + baseline script (scratch source recorded in the audit) | audit worktree | independently reviewed, installed from a receipt-bound immutable source head and proven to cover the reported sessions before any v3 total is reported (§13; no merge required) |
| Astra reviews v1.0, v2.0 | reviews/ | closure maps in §17 |

## 3. Essential governance and security — kept vs cut (KS-10)

**Kept:**
- Root CLAUDE.md §I and §N, carried into cards by COVERAGE (every applicable MUST of
  §I and §N, charter §0 and the retained acceptance contracts maps to a card line, a
  packet clause or an executable check; the ≤ 300-token summary in a card cannot
  substitute for an omitted binding rule).
- The FROZEN contract: one explicit manifest `fleet/FROZEN_PATHS.txt` shared by
  `precheck.sh` and `kyroute.py`, seeded from ORCHESTRATOR_CONVERGENCE_CLOSE §2 and
  precheck's existing prohibitions (`asset_runner.py`, `runner.py`, `staleness.py`,
  `writers/__init__.py`, …). New conforming writers remain permitted; a frozen change is
  STOP for native authorisation.
- The tracker as the only ledger; typed guarded completion; verdict identity with
  evidence-aware re-review and full history.
- Verification: independent verifier running the packet's applicable item tests, named
  mutations and compatibility checks itself (builder results are inputs, not
  substitutes); the required CI checks; **`Kāla DB Tests (throwaway Postgres)` for
  relevant code changes** — absent, skipped or failed DB evidence is not success; the
  semantic acceptance obligations of retained items (Gochara endpoint completeness,
  actual teardown where required).
- Production safety: protected-window flow (owner-approved GitHub action); request-bound
  pre-acceptance, backup/restore/dry-run and quiescence evidence for executor operations;
  migration allocation; no worker holds `DATABASE_URL`; no model merges or dispatches
  production.
- Frontier-by-rule routing with fixtures; escalation grants no authority.
- One governance record pair: the C-2 banner + SESSION_LOG entry, and the C-4 close.

**Cut (measured waste or ceremony without a detector):** standing lanes, heartbeats,
idle cycles, claim-renewal model turns; the ADHIKĀRIN standing lane and surrogate
charter (→ authority card + RULING jobs on `ky request`); NEW ITEM reports and the
reservation ceremony (replaced by the allocator for migration numbers and the item
lock for shared worktrees — not merely by a typed block); per-cycle digests; ledger
PRs and branches; SESSION_OPEN ceremony beyond B-5; charter §3/§5/§11 and the
amendment as operating text; whole-document reads per job; LLM "packet exits" where a
deterministic check suffices; the periodic claim-only LIVENESS job (its claimed
DB/worktree proof was unsupported — admission checks replace it, §6).

## 4. Roster and capacity (owner decisions)

| role | model / effort | mode |
|---|---|---|
| Planner | Opus 5.5 **xhigh** | COCKPIT while holding the planner fence; bounded headless PLAN jobs at `--effort xhigh` |
| SŪTRADHĀRA | Opus 5.5 high | bounded headless conductor jobs supervised by the deterministic controller; observed and steered through COCKPIT |
| PRAHARĪ (dispatcher) | script | background, 60 s tick, atomic instance lock |
| KĀRAKA | Sonnet 5.5 high | BUILD / REWORK |
| KĀRAKA-escalated | Opus 5.5 high | BUILD / REWORK (routing or escalation) |
| PARĪKṢAKA | Opus 5.5 high | VERIFY / PRE-ACCEPT / POST-READBACK / ARTIFACT, source-read-only |
| ADHIKĀRIN (doctrine rulings) | Opus 5.5 high | RULING on demand |
| **OWNER SURROGATE** (§4a) | Opus 5.5 high | SURROGATE job on demand: resolves every owner-wait within its charter; the dispatcher launches it whenever an `awaiting` condition arises |
| Bootstrap builder (Wave B) | Opus 5.5 high | control-plane packets under D-1 |
| **COCKPIT** (the owner's interactive session) | Opus 5.5 high (xhigh during Wave B) | any new session the owner opens with the COCKPIT prompt; resumes from state; observes, steers, vetoes; may do planning work; never required for progress |

Capacity `KY_BUILDERS_MIN=3 / MAX=6`, `KY_VERIFIERS_MIN=2 / MAX=4`; `min(max, demand)`
per kind; the surrogate may raise the maxima when ready work exceeds live builders. No
token caps (§15.6). On a subscription refusal (structured error in the stream **or**
terminal log text) the dispatcher backs off adaptively (5 → 10 → 20 → 30 min), reports it,
and resumes automatically; nothing else is ever idle by design (§4a).

## 4a. Autonomy model (owner direction 2026-10-11; delegated calls D-4…D-8 in §15)

**Principle.** The campaign runs **headless under launchd** and needs no open session to
make progress. The owner's interactive session is a **cockpit**, opened whenever the
owner wishes (for example when its context has grown), with one prompt that always
resumes from persisted state.

1. **Resume-anywhere sessions, crash-safe (KV-02).** No role has an automatic hand-off
   threshold. **State ownership (KW-02):** each role-state file (`run/<ROLE>_STATE.json`) has one
   fenced writer — the role's deterministic controller, or, before a controller exists, the
   cockpit while it exclusively holds the role lock. The controller is the sole role-lock
   holder and role-state writer across child jobs: it verifies the approved bundle, acquires
   ownership, reconciles actions and surviving children, validates resume/gates, and gives
   each child an immutable state snapshot and a fenced job identity; **children never
   reacquire the role lock nor write the shared role-state file** — they return results and
   checkpoint/action requests which the controller validates and persists. Controller
   identity and child provider-session identity are separate fields; child rollover never
   replaces controller ownership or resets campaign failure/no-progress history. Cockpit
   commands enter a durable command queue (`run/commands/<ts>-<id>.json`) and never
   overwrite a loop's session identity; an observing cockpit (not holding the lock) submits
   any hand-off request through the queue and checkpoints nothing on exit. Acceptance cases:
   first child under a live controller, successive child sessions, observer exit,
   stale-child write refusal. **Action records:** before any side effect
   (push, PR, merge, tracker event, launch, notification) the actor persists
   `run/actions/<action_id>.json` {inputs, target identity, intended transition}; after it,
   the observed result, atomically (write-then-rename). **Recovery** reconciles unfinished
   action records against GitHub, tracker and process evidence before retrying; a message
   lock is always followed by a fresh handled-state check. Historical checkpoints are
   preserved; file evidence is validated by hash, external evidence by typed commit/event
   references. **Legacy migration (KW-01), once, under exclusive planner ownership:** detect the
   legacy state schema before reading `active`; preserve the original state and historical
   checkpoints; derive the compact active index from `in_progress`, `deferred` and the next
   step's dependencies; initialise absent `actions`, `awaiting`, `commands` and `loops`
   collections as empty without treating their absence as proof that no process exists.
   Migrate evidence **by type**: retain `trust-anchor` against its recorded source commit
   and perform a new trust check against the currently authorised source; retain
   `coordination.notice` as commit `b9fda0ccc8da51ec30ccf7e3622cddb57b48477f`; retain
   `B-0b.pr` as PR #3441 with its historical observed commit, refreshing external state
   when needed — none of these is relabelled as file evidence or a superseded proposal.
   Only `plan-change.proposal` is rebound to its verified file blob at `e3b5294e2`, keeping
   its existing SHA-256 and recording adoption by v2.3 §5/§7; its owner-wait is not
   recreated. The migration runs idempotently through an action record, preserves failure
   history, and updates session identity only while holding the planner fence. Resume reads a compact active-state index and a bounded journal tail,
   validating only the dependency chain of the next action. Exit callbacks are best-effort;
   correctness never depends on them. A harness context warning forces checkpoint-and-stop.
2. **Headless loops = launchd + a deterministic controller (KV-04).** launchd
   (`KeepAlive`) supervises `kyloop.py <role>`, a script controller — never an unconditional
   chain of model invocations. The controller holds the role lock with its own and its
   child's PID/PGID/start identities, reconciles surviving children before any replacement,
   and honours durable state before **every** launch: `enabled`, STOP, completion, quota
   backoff and the circuit breaker. Explicit stop and finalisation disable model admission
   across controller restarts (`run/loops/<role>.json {enabled:false, reason}`). **Waiting
   happens in the controller**, not in a model: it waits on inboxes, gate changes, PR/CI
   events and deadlines, deduplicates actionable events, and launches one bounded model
   job only for an actionable event or an eligible work item (the conductor job receives a
   batch of handled-state-checked messages; it never runs `ky inbox --wait`). Roles:
   `dispatcher` (30 s tick; §6), `planner` (Wave B: `PLANNER_LOOP` jobs per pending step),
   `conductor` (after activation), `veto` (the veto-window controller, §4a.3). **Progress**
   means an accepted step/result or a changed external dependency — never a heartbeat,
   timestamp or journal append. No-progress counts persist across restarts; after three
   no-progress runs the breaker opens and reopening requires recorded changed evidence
   (also when the surrogate decides). Test databases are bound to their originating session
   and cleaned up on its termination, including crashes (KU-02); closing a cockpit neither
   adopts nor deletes another session's databases. B-0c probes (KV-06) cover duplicate
   start, orphan recovery, STOP, completion, shutdown and unchanged-condition restart refusal.
3. **Owner surrogate first.** Any point where a role would wait for the owner writes
   `run/awaiting/<id>.json` (question, options, evidence, deadline). The dispatcher launches
   a SURROGATE job (Opus 5.5 high, charter `fleet/cards/OWNER_SURROGATE.md`, agent
   `.claude/agents/kalayantra-owner-surrogate.md`) which decides within its authority,
   records `ky decide … --as steward --delegated` and `run/DECISIONS_SURROGATE.jsonl`, and
   notifies the owner (`kynotify.sh`: macOS notification + journal line; the record stores
   the submission result — delivery is never evidence that the owner read it). **Decision
   states:** `PROPOSED → EFFECTIVE → EXECUTED` for routine classes (effective at once);
   `PROPOSED → PENDING_VETO → EFFECTIVE → EXECUTED | VETOED | FAILED` for the **veto classes**
   (campaign-level authorisation of a protected window, campaign start/resume, plan-bundle
   changes, capacity above the maxima). At proposal time **nothing is published**: no
   `ky decide`, the awaiting item stays open, immutable target parameters, evidence digests,
   the notification result and the deadline are stored. The `veto` controller serialises
   veto, expiry and execution: at expiry it rechecks the unchanged target, authority,
   relevant holds and prerequisites, then publishes the effective decision (`ky decide …
   --as steward --delegated`) and executes through an idempotent action record; a failed
   notification or changed evidence prevents activation. An explicit owner pause is never
   undone by the surrogate. Hard stops stay visible as unresolved; no delegated approval is
   ever published for them.
   **Owner-only (hard stops, never delegated):** FROZEN-contract changes (§N.2); changes to
   the owner decisions themselves (§15.1–8, D-1…D-9); production data deletion or restore;
   anything touching Suvarṇa's integration branch or `ri02` before certification-done;
   credentials; **the protected-environment human approval in GitHub** (KV-08: the
   surrogate's effective decision authorises the bounded campaign request; the platform's
   reviewer approval is a separate human act the campaign records as an external approval
   dependency and continues independent work — it never impersonates the owner, retrieves
   credentials, relaxes environment protection or substitutes a veto deadline for the
   approval). Root CLAUDE.md §I scope, §L restrictions and §N.2 remain inherited hard
   boundaries beyond this list. A hard stop pauses that item only, never the campaign, and
   notifies the owner.
4. **Zero idle, parallel by default.** The dispatcher launches the moment a job exists
   (VERIFY when checks turn green, REWORK on rejection, MERGE on acceptance, COMPLETE on
   merge). Planning work (B-0c…B-5 and PLAN jobs) is parallelised across bounded subagents
   or headless jobs — cards, schemas, packets, reviews concurrently — the planner
   orchestrates and never serialises what is independent. Accuracy is kept by the unchanged
   acceptance machinery (§6–§9, independent review, enforced verifier boundary).
5. **Cockpit commands** (chat, applied immediately): `status` · `veto <decision-id>` ·
   `decide <awaiting-id>: <answer>` · `pause` / `resume` · `priority <item>` · `builders <n>` /
   `verifiers <n>` · `loops start|stop|status` · anything the plan allows.
6. **Double-action guard.** Every message, awaiting item, action and job carries a lock
   keyed by its id **and** a durable handled-state record; a lock is followed by a fresh
   handled-state check, and external actions are reconciled through their action records
   (item 1) so that sequential duplication is prevented, not only simultaneous access.

## 5. Topology, paths, allocation (KS-02, KS-06)

- `KY_ROOT=/Users/Dev/kalayantra`, `KY_RUN=$KY_ROOT/run`, `KY_FLEET=$KY_ROOT/fleet_live`,
  `KY_SCRATCH=/Users/Dev/scratch.noindex/claude/madhav/<YYYYMMDD>-kalayantra-v3/`
  (dated per owner policy; temporary files, job logs, DB dumps, fixture trackers). Every
  path in scripts, prompts, cards and packets is absolute; persistent job records store
  the absolute paths they used.
- **Job and dispatcher I/O (KT-08):** each job records `JOB_SCRATCH=$KY_SCRATCH/jobs/$JOB_ID`
  and absolute `prompt_path`, `stdout_path`, `stderr_path`, `tmp_path` beneath it, created
  before launch and used for stdin, logs and `TMPDIR`. The dispatcher log lives under
  `$KY_SCRATCH/dispatcher/`, its absolute path recorded in persistent dispatcher state.
  `run/` keeps only durable control state, compact measured receipts and evidence
  references. Before removing finished session scratch, usage is reconciled and evidence
  required by retained receipts is preserved; at session close finished scratch is
  removed and unfinished material is reported with its reason.
- `CLAUDE_BIN=/Users/Dev/.local/bin/claude` (resolved on this host before any scrub,
  asserted executable and **version ≥ 2.1.296** — 2.1.239 refused `claude-opus-5-5`
  (P-2, resolved by the owner's `claude update` on 2026-10-11) — recorded in
  `run/INSTALL_RECEIPT.json`; a version below the pin refuses launch).
- **Campaign checkout:** branch `kalayantra/campaign` (upstream `origin/main`) at
  `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, created in B-2;
  fast-forwarded each tick.
- **Capacity reality:** the registration count under the Claude/Madhav policy root is a
  measured value reported by `status` (33 on 2026-10-11 morning, 41 by the evening review)
  against a ceiling of 15. **No new copy is created until the owner has disposed of
  enough existing ones** (B-0 inventory → owner dispositions → `git worktree remove` +
  `prune`, preserving dirty/unpushed work by push or bundle). The planner works in the
  existing relaunch-plan checkout (branch switches, no new copy) until then.
- **Work worktrees:** `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item-id-lower>/`,
  one per item branch, created at claim; **one item lock** serialises every author and
  reviewer access to it; removed after guarded completion once pushed.
- **Base contract (KT-04):** each job record carries worktree, branch, `base_sha`, its test
  digests and, for each code prerequisite, the accepted final PR head and — once merged —
  the observed mapping from that head to `mergeCommit.oid` (squash). Admission requires
  either the accepted head or the verified corresponding merge commit to be contained in
  the job base; missing, changed or unverified mappings refuse admission. Artifact and
  schema prerequisites use their typed acceptance receipts, never invented Git heads.
  Tracker readiness alone does not prove code availability. Tests: accepted unmerged
  stacks, squash-landed prerequisites, missing code, incorrect head→merge mappings.
- **Migration allocator** (`kyalloc.py`): an atomic, persistent reservation keyed by
  item/branch against the repository-wide migration namespace and active reservations;
  all concurrent migration writers observe the same authority; until it is installed,
  the existing reservation procedure stays in force. Tests: concurrent allocation,
  restart/reuse, conflicting external reservation.
- **Slot DBs** `ky_b1..b6`, `ky_v1..v4` on `ky-pg:55433` via the repository `local_db.sh`
  (registry-inclusive seed; mandatory schema/ledger/registry hashes in each slot
  receipt), supported throughout DB guards, preflight, model worktree/branch
  authorisation, executor and cleanup. Negative fixture: the 1320 prerequisite failure
  and a missing registry are detected.
- **Preflight v3** derives expectations from configured slots, runs a Claude-only smoke,
  and is the install receipt's precondition. Model `streams[].worktrees[]`, detector and
  executor paths migrate in B-0/B-1.

## 6. Dispatcher — full lifecycle (KS-05, KS-08)

`$KY_FLEET/kydispatch.py` (launchd `KeepAlive`, 30 s tick); atomic instance lock via
`kylock.sh` (session identity + PID/PGID + process-start identity); `--dry`, `--once`;
fixtures under
`fleet/tests/dispatch/` with checked-in expected job lists.

**Precedence each tick:** `run/STOP_dispatcher` → exit. `$KY_ROOT/HOLD` → no admissions
of any kind (bootstrap included). `run/HOLD_MERGES` → no queue submission of any kind.
Release gate (§10): while WAIT, only bootstrap-tagged jobs. Recovery: jobs recorded live
whose process group (PID/PGID + start identity) is gone → release claim, `interrupted`,
re-queue once. Freshness: `ky next --json` must come from the live tracker (a snapshot
fallback is refused; `version` must advance or match the EVENTS prefix hash). Then
refresh the campaign checkout and compute.

**Admission checks (replace LIVENESS):** tracker freshness, assigned worktree present
and locked, disposable slot DB READY with bound hashes, packet admitted by `kypacket.py`
(§8), base contains prerequisite heads, routing recomputed, turn/time caps set.

**Item declaration:** every retained executable item declares `completion_kind:
code | artifact | packet | operation`, its producer stream, reviewer identity rule,
detector and required step evidence (B-0 adds the fields).

| kind | trigger | model | identity / claim | post-action (script) |
|---|---|---|---|---|
| BUILD (code) | K item ready, unclaimed, no open PR, PRIORITY order | by routing (§9) | `KY_STREAM=K KY_LANE=<slot> ky claim <ID> --worker <slot> --lease 10800`; item lock | must end in `ky review <ID> --detail "PR #n @ <head>"` or `ky block`; else `interrupted` |
| BUILD (artifact) | K-owned artifact item ready | by routing | K claim; author identity recorded before review | registers path + digest via `ky review`; schedules ARTIFACT |
| REWORK | REJECTED at head, or **code-class** CI failure (classified; infra/flaky → RETRY-CI without a model) | routing; loop +1; escalation §9 | same worktree, item lock | as BUILD; evidence history retained |
| STEP | a required `step` whose named detector passes | script | — | `ky step <ID> <step> --evidence <path>` only after the detector passes |
| VERIFY | item in review; PR head without a verdict at (item, pre_merge, head, evidence-fp); required checks green; `Kāla DB Tests` green where the diff is relevant | Opus | **no item claim**; job lock (item, phase, head); item lock | verifier writes a **proposed** result; controller publishes (below) |
| ARTIFACT | artifact/packet item registered by its author, or a MODEL artifact | Opus | reviewer slot ≠ author identity; V claim only for V-owned items; S-owned artifacts get no V claim | `KY_STREAM=V … ky verdict <ID> --artifact-digest <sha256> --phase artifact …` (external review binding where the V-owned item requires it) |
| REGEN | PR DIRTY/CONFLICTING confined to declared generated outputs | script, pinned generator | item lock | merge base; regenerate only declared outputs; run applicable tests; record hashes; push; **register `ky review … @ <new head>`**; inheritance only by the patch predicate (below), else VERIFY |
| MERGE | ACCEPTED at the **registered** head (head-match guard), required checks + DB job success, base correct, protected-window listing satisfied, no hold | script | — | `gh pr merge "$PR" --auto --squash --match-head-commit "$REGISTERED_HEAD"` after the checks; a head mismatch refuses submission; once queued, any head change cancels the queue/auto-merge authorisation and requires fresh admission; workers never push under an outstanding queue authorisation; branch/ref evidence retained until guarded completion |
| COMPLETE | merged (code) / accepted artifact / receipted operation | script | K completes K items; S completes S items and independently accepted N/V items | typed `ky done` (`--pr n --reviewed-head <final PR head>` \| `--artifact-path` \| `--operation-receipt … --operation-id …` \| `--packet-verdict`); deployment containment and post-deploy use the **squash merge commit**; refusals logged by code; `deps_open_strict` → wait |
| REQUEST-PREP | ready N-owned operation | script + PLAN where the request needs authoring | N actor | request binds the reviewed merged script, request digest, lease, expiry, backup/restore/dry-run evidence per `executor.py` and the approved operation table |
| PRE-ACCEPT | prepared request | Opus (independent V slot) | job lock | acceptance record the executor requires |
| EXECUTE | pre-accepted request | script (`executor.py`, authority boundary unchanged) | — | receipt in `run/ops/receipts/`; GitHub protected-window dispatch stays an owner-approved workflow action |
| POST-READBACK | (a) deployed `writes_data` code item; (b) receipted operation item | Opus after a readback request | (a) job lock (item, post_deploy, squash merge sha, evidence-fp); (b) job lock (item, operation id, receipt sha256, evidence-fp) | two typed exits: (a) propose `--phase post_deploy` at the squash merge commit; (b) review the completed executor receipt, operation/request identity, measured readback and quiescence evidence and propose `--phase artifact --artifact-digest <receipt sha256>`; the controller publishes only after independence, boundary and unchanged-evidence checks; operation COMPLETE then uses `--operation-receipt <that receipt> --operation-id <that id>` under the existing typed guard; negative fixtures: script-head verdict, pre-acceptance record, wrong receipt digest, executor exit without semantic readback — none completes the operation |
| MODEL | S-owned model/close work (triage, joins, PRIORITY, C-1/C-2 artifacts, REPIN) | Opus PLAN job | S actor | artifact + ARTIFACT review where required |
| RULING | `ky request D-…` pending (doctrine/charter) or N inbox unread | Opus | N actor | `ky decide … --as steward --delegated …`; `ky ack` |
| SURROGATE | an unresolved `run/awaiting/<id>.json` with **no handled proposal for its current immutable target/evidence fingerprint**; handled state re-read under the lock before launch; `PENDING_VETO`, hard-stop and external-approval items launch no further SURROGATE job unless recorded material evidence changes | Opus (owner-surrogate charter) | steward actor; lock on the awaiting id | **routine:** publish at once through an idempotent action record (`ky decide --as steward --delegated`, `DECISIONS_SURROGATE.jsonl`, `kynotify.sh`); **veto class:** persist `PENDING_VETO`, retain the awaiting item, publish **no** tracker decision; successful notification submission + durable cockpit visibility start the 30-min window, failed notification prevents effectiveness; only the deterministic `veto` handler (in `kyloop.py`, or the qualified staged bootstrap supervisor during Wave B) serialises veto, expiry, publication and execution after rechecking authority, target, evidence, holds and prerequisites, reconciling its action record before any retry; hard-stop classes → owner notification, item paused. Acceptance: one proposal across repeated ticks/restarts; zero effective publication before expiry; refusal after veto, notification failure or target change |
| PLAN | wave boundary or `run/REPACKET.txt` | Opus **xhigh** | S actor | packets + tests; ARTIFACT review of the packet set |

**Claims, locks, renewals.** Only the owning stream claims; the dispatcher renews only
jobs that hold claims (`KY_LANE=<slot> ky renew --lease 10800` every 20 min); timeout →
reap the process group (PID/PGID + start identity) → release → `timed_out`. Job identity
(`job_id`, provider `session_id` when observed — never invented before launch —, item,
kind, slot, head/digest, evidence-fp, failure-class fingerprint and attempt count) is
persisted in `run/jobs/<job_id>/state.json`. On adoption, legacy claims, PRs and
checkpoints are reconciled into job state (B-2).
**Terminal release (KT-07):** every terminal job path (success, blocked exit, timeout,
interruption) persists its result and checkpoint, confirms the recorded process group has
exited, and releases any held tracker claim **before** freeing the slot; successful
`ky review` registration is not claim release. Release is bound to the job's persisted
item, worker and `claim_id`: the controller verifies that `run/claims/<slot>.json`
matches the job before `KY_LANE="$SLOT" ky release`, serialises release with slot reuse,
and on mismatch keeps the slot unavailable and reports "reconciliation required".
Renewal stops once termination begins. Claimless verifiers release only their job/item
locks. Tests: three successive successful BUILD jobs on one slot; immediate REWORK after
review; blocked exit; restart between checkpoint persistence and claim release.

**Verdict publication (controller-owned).** After a VERIFY/ARTIFACT job exits the
controller checks: exit status, reviewed HEAD unchanged, `git status --porcelain` clean,
tracked-file hash set unchanged, boundary evidence (§7). Only then does it publish
`KY_STREAM=V KY_LANE=<vslot> ky verdict …`. A boundary failure never publishes
ACCEPTED. If a published acceptance is later invalidated, an explicit REJECTED is
appended before any queue action.

**Inheritance predicate (one implementation, used by dispatcher and tracker):** bind old
head, new head, their exact base commits and a comparison of the reviewed patch;
ancestry alone is insufficient; any substantive resolution or unproven difference
requires review of the new head. Applied to every inherited Wave 0 head. After every
head change the owning stream registers `ky review <ID> --detail "PR #<n> @ <new-head>"`.

**Failure accounting:** failure-class fingerprints and attempt counts persist across
retries, escalation, restart and repacketisation; the third identical failure blocks
automatic attempts until a recorded changed condition permits retry.

**Messaging:** the dispatcher routes every owner-wait to a SURROGATE job first; it
writes to the conductor/cockpit journal (and notifies the owner) only for surrogate
decisions, hard stops, verdict invalidation, gate change, wave complete, quota backoff,
dispatcher error, ceiling hit, unclassifiable CI failure.

**Tests (B-1):** fixtures for every kind and transition, recovery, timeout reaping, hold
precedence, gate WAIT with bootstrap exemption, ceiling refusal, stale-snapshot refusal,
duplicate instance refusal, head-match guard, inheritance predicate (substantive
resolution fixture), failure fingerprint persistence.

## 7. Worker launch (`$KY_FLEET/kyjob.sh <job_id>`) (KS-02, KS-06, KS-08)

```
# all values from $KY_RUN/jobs/<job_id>/state.json; every path absolute
cd "$WORKTREE" || exit 70
exec env -i HOME="$HOME" PATH="$KY_ROOT/bin:$NODE_BIN:/opt/homebrew/bin:/usr/bin:/bin" \
  LANG=en_US.UTF-8 TERM=dumb USER="$USER" TMPDIR="$TMP_PATH" \
  ZDOTDIR="$KY_ROOT/zdotdir" KY_ROOT="$KY_ROOT" KY_RUN="$KY_RUN" KY_FLEET="$KY_FLEET" \
  KY_STREAM="$STREAM" KY_LANE="$SLOT" KY_ITEM="$ITEM" KY_PY="$KY_ROOT/venv/bin/python" \
  SE_EPHE_PATH="$SE_EPHE_PATH" SWE_EPHE_PATH="$SWE_EPHE_PATH" TESTS="$TESTS_NEWLINE_LIST" \
  "$CLAUDE_BIN" -p --setting-sources project --permission-mode "$PERMISSION_MODE" \
    --model "$MODEL" --effort "$EFFORT" --max-turns "$MAX_TURNS" $EXTRA_LEAN_FLAGS \
    --strict-mcp-config --mcp-config "$MCP_CONFIG" $DISALLOWED \
    --output-format stream-json --verbose --add-dir "$KY_ROOT" \
    < "$PROMPT_PATH" > "$STDOUT_PATH" 2> "$STDERR_PATH"
```
- `EFFORT` is role-specific: `xhigh` for PLAN, `high` otherwise. `PERMISSION_MODE` is always
  passed explicitly (`bypassPermissions` for builders and bootstrap jobs; never inherited —
  the host's user settings default to it). **P-1:** `--bare` never reads the stored sign-in
  and accepts only an API key, which §7 forbids, so no `--bare` job can start; measured
  fixed start-up context without it is ≈ 31 K input tokens (probe, Sonnet 5.5, empty
  directory). `EXTRA_LEAN_FLAGS` (e.g. `--disable-slash-commands`) are chosen by the B-0c
  probes. **Launch qualification (KV-06):** a launch configuration is usable only with a
  passing qualification receipt (`run/QUALIFICATIONS/<role>-<model>.json`) bound to the
  resolved executable path and hash, version, exact argv, model/effort, role permissions,
  working directory, environment policy and prompt/configuration hashes. Missing or
  non-positive turn limits or wall-clock deadlines refuse launch for every role, SURROGATE
  and both loop roles included. Probes run in the **exact launchd user-agent context**
  (correct user/domain, absolute executable/cwd/PATH, stored sign-in without credential
  copying, the intended tools completing without a TTY or an unanswered permission prompt,
  project CLAUDE.md visibility, excluded hooks/plugins/skills/MCP, observed model identity,
  measured input overhead in the real role worktree) using observable canaries and
  configuration evidence, not model self-report alone; negative probes cover missing
  authentication, inaccessible keychain, denied tools, invalid settings, timeout,
  termination and restart. A required safety or operability result that is false **or
  unknown** refuses that configuration. Changed binaries/configurations are requalified at
  installation; an unsupported model produces a launch refusal, not retries.
- `kyjob.sh` exits 78 if `DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY` is set
  in its own environment; `no_wrappers` behaviour preserved (tested). For fixture runs it
  forwards the validated `PRAVAHA_*` fixture configuration (§14 B-3).
- `MCP_CONFIG` (KT-02): bootstrap jobs use the independently reviewed, manifest-hashed
  empty configuration `{"mcpServers":{}}` staged in the bootstrap source tree
  (`fleet/mcp.none.json`), recorded per job as an absolute path; campaign jobs use the
  installed configuration whose hash is in the installation receipt (`mcp.none.json`
  unless the packet declares `needs_chart_data: true` → `mcp.marsys-only.json`).
- Bootstrap (B-1) launches do **not** go through `kyjob.sh` or the dispatcher: the planner
  prepares and validates the absolute worktree, executable `CLAUDE_BIN`, admitted bootstrap
  prompt, job state, scratch input/output/TMPDIR paths, environment values and deadline
  (missing inputs refuse launch), launches and supervises the process directly, records
  its process-group identity and termination result, and obtains independent review.
- Without `--bare` the project `CLAUDE.md` of the job's worktree loads automatically;
  cards still carry the applicable §I/§N rules per COVERAGE and never rely on that load;
  B-3's visibility fixture repeats the probe on the installed bundle and records the result
  in the install receipt.
- `precheck.sh` is fixture-aware through `KY_RUN`; the launcher writes the manifest
  precheck actually consumes **or** passes newline-delimited test paths in `TESTS`.
- **Verifier boundary** (enforced, not claimed): the launcher provides a read-only
  source/Git-metadata boundary (a sandboxed verifier worktree whose tracked files and
  `.git` are owned by a separate non-writable mapping — implemented and proven in B-1;
  same-user `chmod` alone is **not** accepted as the boundary), with writes limited to
  declared evidence, caches, `TMPDIR` and the slot DB; acceptance fixtures attempt Bash
  edits, chmod/replace, Git-index changes and shared-control writes and must all fail.
- Turn caps: BUILD 150, REWORK 100, VERIFY 60, PRE-ACCEPT/POST-READBACK 40, RULING 30,
  PLAN 300.
- Session persistence stays on (reconciliation evidence, §13).
- Prompt file = role card (≤ 1.5 k tokens) + packet (≤ 4 k) + job header (job id, slot,
  worktree, branch, `base_sha`, prerequisite heads, allocated migration number if any,
  loop, max loops, deadline). Oversized packets are rejected at admission, not at launch.

## 8. Packets (KS-07)

`00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md`, ≤ 4 k tokens; schema
`fleet/schemas/packet.json`; admitted by `kypacket.py check` (schema, hashes, size, test
availability, excerpt and reconciliation claims validated against pinned sources; a
failure names its reason). `packet_sha256` is computed over canonical content excluding
that field.

Front matter: `id, kind (feature | artifact | operation | schema-prerequisite |
bootstrap), wave, build_tier + routing_reason, needs_chart_data, max_loops (3),
plan_version, spec_sources[] (path, revision, section range, sha256),
schema_receipt_id, intended_schema (schema-prerequisite packets only),
original_failing_base (feature packets), test_commits[] (sha, digest, path),
expected_failing_assertion, pw_mechanism_version, release_pins (`not_applicable:
bootstrap` for Wave B packets), packet_sha256`.

Sections, inline:
1. **Immutable pins** — specification revisions/hashes; the build snapshot id
   (`dash_build`, `registry_revision`) from `run/RELEASE_RECEIPT.json` (bootstrap
   packets: `not_applicable`). Never `main_sha`, never a migration number (allocated at
   job start). A later L1 rebuild triggers a REPIN MODEL job that revalidates packets.
2. **Owns (floor) + allowed classes** — exact paths plus: declared generated outputs,
   tests, exports, direct consumers of a changed signature (disclosed in the PR).
   Prohibited: `FROZEN_PATHS.txt`, cross-campaign files, and — for **campaign** builders —
   control-plane code; **bootstrap** packets enumerate the D-1 control-plane source paths
   they may change. A prohibited path → `ky block --detail "freeze: <path>"` → STOP.
3. **Spec excerpt** — verbatim with path/revision/section/hash, plus the planner's
   contract-reconciliation line (e.g. protected-window steps now use
   `kala_protected_migrations.txt` + the deploy job, not `migrate.ts`/`deploy.yml`).
4. **Signatures / contract** — real columns from the admitted schema receipt;
   schema-prerequisite packets declare both the admitted existing schema and the intended
   additive contract; consumers wait for that prerequisite's verified schema receipt.
5. **Migration metadata** — `brief.migration` and `brief.op` populated consistently
   with the tracker's `writes_data` classifier (normalised values; prose or the string
   `NONE` is never truthy production metadata); `migration_class` and window batch id.
6. **Acceptance** — feature packets: the immutable original failing base, exact test
   digests and the observed failing assertion. **At admission** the dispatcher installs
   missing tests idempotently into the item branch and classifies the current result:
   expected-red → new implementation; already-green → an independent already-satisfied
   assessment (ARTIFACT), never automatic rejection or completion; REWORK and inherited
   heads keep their evidence history and run the relevant regression checks. Artifact and
   operation packets state explicit semantic acceptance and negative fixtures (no
   invented red test). Plus `KY_ITEM=<ID> bash $KY_FLEET/precheck.sh --item`.
7. **Evidence template** — `run/jobs/<job_id>/inspection.json` keys; readback request
   template for `writes_data`.
8. **PR template** — title (`[PROTECTED-WINDOW]` when required), body sections, then
   `ky review <ID> --detail "PR #<n> @ <40-hex head>"`.
9. **Do-not list** — no ledger PRs, no control-plane edits (campaign builders), no
   rebase/force-push, merge `origin/main` only when DIRTY outside generated files (else
   REGEN), one PR per item, no credential reads, no production access.

Verifier packet = the same file + `gh pr diff` + the independent test run the verifier
performs itself + gate outputs.

## 9. Routing and escalation (KS-10, KS-12)

`kyroute.py` normalises `owns`/`shared`/diff paths to repository-relative; prose entries
are resolved by the planner or routed to Opus. Opus is forced by: a migration file or
non-NONE migration metadata; any path under
`platform/python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**`,
`platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**`,
`platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py`, `**/*ephemeris*`,
`platform/scripts/temporal/**`, `platform/scripts/migrate.ts`, `platform/migrations/**`,
`platform/src/proxy.ts`, `platform/src/lib/{auth,security,share,limits,mcp}/**`,
`platform/src/app/api/{auth,admin,db}/**`, `.github/workflows/**`, `infra/**`,
`platform/scripts/governance/**` (including `platform/scripts/governance/pravaha_tracker/**`),
`00_ARCHITECTURE/briefs/kalayantra/fleet/**`; any diff line touching `'lit'` state or
writing `verification_pass_status`; an import of `swisseph`/`jhora`. Paths in
`FROZEN_PATHS.txt` are not routed: STOP for native authorisation. Routing runs on the
packet and again on the actual diff before VERIFY: a Sonnet diff that hits an Opus rule
is **preserved** and re-queued as an Opus REWORK that assesses it (not discarded).
Fixtures: KA-1e, K1-2, K6-4 → Opus; a `platform/src/lib/auth/**` diff → Opus.

Escalation: Sonnet red after `max_loops` → Opus REWORK; one REJECTED on a Sonnet head →
Opus REWORK; Opus REJECTED twice → `ky block` → conductor → RULING or PLAN.

## 10. Release gate and the N-467 resume (KS-04)

`run/RELEASE_RECEIPT.json` (schema `fleet/schemas/release_receipt.json`): one
`release_id`, schema version, digest; every condition binds its evidence to that
release: certification → coordination commit/record id; pins → rebuild producer and run;
regeneration → main commit, generator version, output digest; PR dispositions → an
exhausted paginated API traversal with `{merged|parked|closed, owner, re_entry}`;
coordinator closure → SS's enumerated hand-off records. Missing or inconsistent evidence
is WAIT. Condition 5 has no producer today and stays WAIT until SS publishes it.

Both gate modes also require **final Wave B acceptance** (KT-03): the final
`run/VERSIONS.json` and a final installation receipt binding that manifest, the loaded
tracker revision, B-3's tested component hashes and measured rehearsal results, B-4's
independently accepted coverage and admitted packet hashes, and the validated B-5
governance backfill. `kygate.sh --pre-resume` validates the five release conditions and
that acceptance, and prints `READY_TO_START` only when every prerequisite is satisfied
and the sole missing launch authorisation is the matching N-467 resume record; it
authorises no campaign job. Negative fixtures: bootstrap-only installation, absent
rehearsal, stale tested hashes, missing coverage, changed final manifest. **Start (D-7):** when `READY_TO_START` holds, the SURROGATE proposes the N-467 resume as a
veto-class decision with the release-receipt digest and final manifest digest bound before
the window (30 minutes, owner notified); at expiry the `veto` controller revalidates both
the release gate and final Wave B acceptance against those bound inputs, then writes
`run/OWNER_RESUME.json` (binding `N-467`, the release-receipt digest,
`approved_bundle_digest` = the final manifest digest, the deciding identity — owner or
surrogate decision id — and timestamp) and `kyctl.sh` starts the conductor loop. The owner's
cockpit `resume` writes the same record at once. The conductor loop's first job, after
version validation and exclusive instance acquisition, verifies that record and runs the
full gate. D-3 is thereby an explicit, recorded act; nothing further is required. The recorded certification-hold owner
releases `HOLD_MERGES` when its documented condition is met; the conductor never removes
a hold it did not set. STOP and global HOLD dominate bootstrap and campaign admission;
HOLD_MERGES blocks every queue submission. Negative fixtures: stale resume, mixed
release ids, each surviving hold, each missing field.

## 11. Conductor (KS-11) — headless loop; the cockpit is the owner's view

Setup only exports paths and changes directory — **no checkout mutation** (`git pull`)
before verification and locking; campaign refresh belongs to the dispatcher under its
serialised checkout ownership (KT-01). The **controller** (`kyloop.py conductor`) performs atomic instance acquisition
(`kylock.sh acquire conductor <controller identity>`: `mkdir`-atomic, records PID/PGID and
process-start identity; a transient tool-shell PID is never an identity). Controller
start-up: manifest digest (from the activation record) → `kyversion.sh
--expected-manifest-digest` → lock → state reconciliation → `OWNER_RESUME.json` → full
gate. **Conductor child jobs acquire no lock and write no role state** (§4a.1, KW-02): they
receive the snapshot and job identity, act through the tracker, and return checkpoint and
action requests. **Session state (KT-06):** on entry compare the observed
session identity with `CONDUCTOR_STATE.json`; re-entry into the same session preserves
`started_at` and counters; a different session preserves validated checkpoints,
deferred messages and campaign decisions, archives the previous session summary, and
initialises the new session's `started_at` and counters to zero; campaign failure
fingerprints and attempt counts are never reset by rollover (the same rule governs
`PLANNER_STATE.json`). Idempotent dispatcher start by the same helper
(detached stdin, managed logs; no extra owner question — the paste authorises it);
reconcile **both** inboxes (`ky ack <id>` for S, `ky ack <id> --steward` for steward,
after action or durable deferral). **Waiting is the controller's job (KV-04):** `kyloop.py conductor` waits on the S and
steward inboxes, gate changes, PR/CI events and deadlines; a conductor model job is launched
only with a deduplicated batch of actionable, handled-state-checked messages (never
`ky inbox --wait` inside a model). **No hand-off thresholds (§4a.1):** each job checkpoints
after every handled message (`CONDUCTOR_STATE.json`, `JOURNAL_CONDUCTOR.md`, action
records) and exits at `--max-turns` or on a harness context warning; the controller
launches the next job only for the next actionable batch. The cockpit session, when open,
reads the same state and acts through the command queue; two actors never act on one
message (lock on `msg_id` + handled-state record).

## 12. Finalisation (KS-09) — outside the ordinary dispatcher

`finalize.sh` v3: stop new admissions; drain or terminate recorded job groups within
their deadlines, preserving dirty/unpushed work; verify process identity by recorded
PID/PGID + process-start identity; write `$KY_RUN/DRAIN_RECEIPT.json` from measured drain
facts; a finalizer-owned, bounded independent reviewer (headless Opus, different
identity) accepts its exact digest; then `KY_STREAM=S ky done C-3 --artifact-path
"$KY_RUN/DRAIN_RECEIPT.json"`. Remove eligible owned item worktrees and session DBs;
write `$KY_RUN/FINAL_RECEIPT.json` binding the accepted drain digest, close-report
evidence and physical-absence observations; one bounded independent close review
outside ordinary dispatch (bound external review where the V-owned item requires it);
after it exits, independently recheck process, worktree and DB absence; publish its
digest-bound verdict only if the receipt is unchanged; then `KY_STREAM=S ky done C-4
--artifact-path "$KY_RUN/FINAL_RECEIPT.json"`. The tracker stays available throughout.
Any survivor, changed receipt, missing close claim or failed cleanup prevents acceptance.

## 13. Measurement (KS-12; owner: no caps)

- The baseline implementation must be independently reviewed, installed from a
  receipt-bound immutable source head and proven to cover the reported sessions **before**
  any v3 total is reported (a main merge is not a prerequisite). Missing source or coverage
  is reported as unknown, never zero.
- Accounting ownership is defined for every provider session and child session;
  repeated result events are de-duplicated; transcript usage is used only for uncovered
  calls; whether parent usage includes children is proven before child totals are added.
  Fixtures: normal completion, duplicate results, killed job, parent/child sessions,
  interactive planner/conductor sessions, bootstrap jobs, missing records.
- Reported separately: distinct guarded-completed item ids, decision completions, joins,
  accepted heads, weighted progress — each with its scope denominator and observation
  boundary (historical 46 = 39 guarded + 1 join + 6 decisions).
- Persistent failure fingerprints and attempt counts (§6); `no_progress_jobs`;
  escalations; rejection rate; CI-infra retries; lead time p50/p90; four-class tokens by
  role, kind and per guarded completion.
- **Signals and their detectors (Astra v2.3 Part 5):** *loop healthy* = verified controller identity, the authorised bundle and a timely
  successful control iteration; when a child is expected, additionally its matching process
  identity and liveness; when none is expected, a legitimate recorded waiting state and no
  unreconciled child; a stopped loop reports STOPPED; missing children during legitimate
  waiting never trigger model admission — a loaded plist is not health;
  *platform approval verified* = deterministic GitHub readback bound to the expected
  repository, workflow run/attempt, environment, source SHA and required owner approval;
  an owner's report alone is `approval_reported_unverified` and keeps the external
  dependency; approval, workflow completion and semantic operation acceptance are separate
  states; *loop making progress* =
  accepted work or changed external dependency (timestamps are a proxy, never the signal);
  *probe PASS* = exact configuration + observed result + negative control + evidence hash;
  *surrogate decision* = its state (proposed / pending-veto / effective / executed / vetoed /
  failed), not a journal line; *owner notified* = submission recorded + cockpit visibility
  (reading unknown); *veto expired* = the `veto` controller's check under the decision lock;
  *WAVE_B_DONE* = derived from accepted B-0…B-5 evidence and the final receipt, never a
  file's existence; *READY_TO_START* = the release/final-acceptance detector re-run against
  the bound inputs when D-7 activates.
- Savings and throughput remain **cannot be estimated** until comparable completed work
  and reconciled four-class usage exist; the audit's 64 % is an upper bound on historical
  addressable classes, not a forecast.

## 14. Waves (KS-01, KS-02, KS-03, KS-10)

**Wave B — bootstrap during the hold (KW-03).** D-1 and D-9 apply. B-0c may activate
its separately reviewed immutable bootstrap supervisor; B-2 installs the independently
accepted immutable source bundle. **Neither requires a main merge.** Order is mandatory.

| id | work | by | acceptance |
|---|---|---|---|
| B-0a | **Capacity inventory**: `git worktree list --porcelain` → `WORKTREE_DISPOSITIONS_v2_1.md` (keep / remove / archive per copy, dirty and unpushed state noted); **owner disposes**; no new copy before the count is ≤ 14 | planner → owner | registration count ≤ 14 before B-1 |
| B-0b | **Reconcile the model** per §0: commit the mirror edits; `ACCEPTANCE_ROOTS`; `CLOSURE`; triage; completion_kind/producer/reviewer/step fields; namespaced bootstrap ids; D-RETIRE decisions registered (staged refusal); `streams[].worktrees[]`, detector and executor paths migrated; schema receipt admitted; joins regenerated; both reconciliation tests | planner (in the relaunch-plan checkout, branch switch) | validator green; path-only test identical; triage test equals the reviewed expected delta; closure hash reproducible |
| B-0c | **Bootstrap prerequisites**: BOOTSTRAP card, fixture builder/verifier cards, `fleet/schemas/packet.json` (bootstrap kind), `fleet/schemas/release_receipt.json`, the staged empty MCP configuration `fleet/mcp.none.json` (`{"mcpServers":{}}`), the bootstrap launch-input template (worktree, `CLAUDE_BIN` ≥ 2.1.296, prompt, job state, scratch paths, environment, `PERMISSION_MODE`, deadline), the **probe jobs** (one per roster model, interactive and under launchd: sign-in, CLAUDE.md visibility, no user-level hooks/plugins/MCP, fixed overhead → `run/PROBES.json`), the **owner-surrogate charter** `fleet/cards/OWNER_SURROGATE.md` + `.claude/agents/kalayantra-owner-surrogate.md`, `kynotify.sh`, `kyctl.sh`, `kyloop.py` (controller) + the launchd plists under `fleet/launchd/`, the **bootstrap supervisor** `kyboot.py` (separately reviewed; activated from an immutable staged source bundle = the reviewed branch head; its own proven instance lock; directly supervises B-1 jobs per §7; never starts the campaign dispatcher and never uses `fleet_live` as a shortcut), the loop prompts `fleet/prompts/{PLANNER_LOOP,CONDUCTOR_LOOP}_v2_4.md`, Astra KU-01…KU-03 replacements, and the bootstrap version manifest `run/VERSIONS.bootstrap.json` recording <APPROVED_SOURCE_COMMIT>; one independent review (parallel subagents may draft; one reviewer accepts) | cockpit/planner + reviewer | reviewed; bootstrap manifest + review receipt bind every generated artifact to the source commit; qualification receipts PASS for every launch configuration (KV-06; "recorded" is not acceptance); until `kyboot.py` is qualified the cockpit performs B-0c itself and invokes the source-bound surrogate with the reviewed staged card; status reports missing helpers as unavailable |
| B-1 | **Implement, one packet each** (bootstrap kind; release pins `not_applicable`; enumerated D-1 paths): `kydispatch.py`, `kyjob.sh` (+ verifier boundary), `kylock.sh`, `kyalloc.py`, `kyverdicts.py` (+ the shared inheritance predicate, also applied to the tracker), `kyroute.py` + `FROZEN_PATHS.txt`, `kypacket.py`, `kygate.sh` (+ `--pre-resume`), `kyregen.sh`, `kyreport.py` + baseline import, `kyversion.sh`, override-preserving `ky`/`kybrief` wrappers, `local_db.sh` (repository, registry seed, slots), `preflight.sh` v3, `finalize.sh` v3, `install.sh`, tracker semantic changes (declaration fields, inheritance predicate, decision staging), executor table additions (incl. K9-23's), `precheck.sh` fixture-awareness | Opus bootstrap jobs launched and supervised **directly** by the planner (CLAUDE_BIN, cwd = bootstrap worktree, `--mcp-config` = the staged `mcp.none.json`; process-group identity and termination recorded; no `kyjob.sh`, no dispatcher) | each packet names its command, expected result and negative cases; fixtures per §5–§12; tests and review independent of the not-yet-built dispatcher |
| B-2 | **Review and install (KX-02, D-9).** Independent review accepts the exact immutable source head or component heads assembled into the installation bundle. `install.sh` verifies those heads, review receipts and manifest hashes, then installs the fleet, tracker, wrappers, approved plan, prompts, cards and manifest. `run/INSTALL_RECEIPT.json` records source commits, tree/component hashes, review references, qualifications, `CLAUDE_BIN` and the running tracker's loaded revision; a merge commit is optional historical metadata, never an installation prerequisite. Prove that old supervisors/sweeps cannot dispatch (`STOP_*` + process-absence evidence); create the campaign checkout within capacity; publish the staged D-RETIRE decisions; reconcile legacy claims, PRs and checkpoints; mark the receipt `mode: bootstrap`. Under `HOLD_MERGES` merge intentions remain durable local requests with no GitHub queue submission; the surrogate executes them after certification-done | Opus job + surrogate | installed hashes match the reviewed component heads bound by the manifest; `preflight.sh launch` and `kyversion.sh --bootstrap` pass; only the accepted bootstrap receipt permits isolated rehearsal activation — receipt-file existence alone grants no authority |
| B-3 | **Isolated rehearsal** on the installed, version-checked bundle: fixture wrapper preserving validated `PRAVAHA_HOME/EVENTS/PLAN_MODEL/REPO/HOLD/URL/TRACKER_PORT`; a **second tracker** on a reserved unused loopback port with HOME, model, EVENTS, claims, snapshots and backups under `$KY_SCRATCH/fixture/`; no production DB configuration; fixture-local detectors only (`/api/verify` included); a fixture backend for Git pushes, PR creation/read/checks/merge, deploy observations and executor submission (local fixture remotes; production executor and credentials denied); the real CLI, claim, verdict and typed completion paths against the fixture tracker; includes the CLAUDE.md-visibility fixture and the verifier-boundary fixtures | dispatcher + jobs | live EVENTS size/hash unchanged; no fixture connection to port 8767; zero external PR/queue/production requests; expected fixture transitions; fixture server, DBs and worktrees cleaned up; **tested component hashes and measured rehearsal results recorded** for the final receipt |
| B-4 | **Cards + packets**: KARAKA, PARIKSAKA, ADHIKARIN cards with `COVERAGE.md` (§I + §N + charter §0 + retained acceptance contracts); one independent card-coverage review; packets + tests for Wave 0 and Wave 1, `kypacket.py check` green | planner | coverage review ACCEPTED; packets admitted; **accepted coverage and admitted packet hashes recorded** for the final receipt |
| B-5 | **Governance backfill and final acceptance**: CURRENT_STATE §2 banner + SESSION_LOG entry (validated); the campaign handshake from Codex to Claude; the final `run/VERSIONS.json`; a **final installation receipt** binding that manifest, the loaded tracker revision, B-3 evidence, B-4 evidence and the validated backfill. Any changed component afterwards requires reviewed installation and the affected acceptance checks before a new final receipt | planner | `schema_validator.py` green; normal `kyversion.sh` green against the final manifest and receipt |

**Wave 0 — after `READY_TO_START`, the effective D-7 decision and the activation record.** In order: the necessary
`J-0c → J-0d → J-0 → J-0m` chain (artifact BUILD exits + ARTIFACT reviews, respecting
earned completions); `J-4p` after `K0-SV`; then pin-consuming work: the 11 ACCEPTED PRs
under the inheritance predicate (K4-2a #3379 [PW] → K4-2aw → K4-2b → K4-3 → K6-5a [PW] →
K6-5 → K6-123 [PW]; K7-1a #3333 (REGEN) → K7-1b → K7-2; K-CERT-2 #3426 in the Suvarṇa
window); protected migrations 1351–1356 (+1362) in **one** owner-approved window; retire
#3283/#3275 by decision; #3272 refresh-or-close; K7-3 repacketed.

**Wave 1 — the computed closure**, in dependency order (owed steps of K3-1 and L0-M,
KA-3a/3b after J-0m, K3-2 after J-5s, KA-4b, K7-3/K7-4, the K5/VC/K6-4/K8-REG/K9/KR
members, schema prerequisites). DB-touching items in ≤ 2 windows.

**Wave 2 — Gochara 5.0 sealing prerequisites and Pravāha disposition** (accepted
`J0_DISPOSITION` artifact; the 37 inherited PRs merged/parked/closed by decision).

**Wave 3 — certification mappings and close**: K-CERT re-packeted against the admitted
schema (after KYD-150's tier column), V-track exits as deterministic checks or
ARTIFACT jobs, N decisions, `finalize.sh` v3 (§12), SESSION_CLOSE validated.

## 15. Owner decisions and delegated calls (unchanged from v2.0)

1 planner xhigh · 2 3+2 scaling on demand · 3 re-scope to the critical path · 4 the
five-part gate · 5 no token caps · 6 ADHIKĀRIN on demand · 7 all Claude · 8 launch by
paste. **D-1** control-plane changes in Wave B under review + install receipt (campaign
builders keep the prohibition). **D-2** rework from scratch, then Astra. **D-3** the N-467
resume is an explicit recorded act — the owner's `resume` in the cockpit, or the
surrogate's decision after the veto window (§10) — no further approval.

**Delegated calls of 2026-10-11 (evening), recorded in KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md:**
**D-4 (amended in v2.4, KV-08)** owner-surrogate authority and hard-stop list as in §4a.3;
the GitHub protected-environment approval is a human act outside the surrogate's reach and
is recorded as an external approval dependency (the owner approves batched windows). **D-5** the surrogate
merges independently reviewed PRs (the owner no longer merges by hand). **D-6 (revised in v2.4, KV-07)** during the
certification hold **no PR merges to main** (every successful main CI run deploys the web
app and can run routine migrations; the "no-op deploy" rationale was false); bootstrap
installs from reviewed immutable branch heads (D-9); main merges are queued and executed by
the surrogate after certification-done, each treated as deploying and recorded with its
actual workflow outcome. **D-9** bootstrap and campaign installation use the independently
accepted branch head bound in the receipt, never an unreviewed or merged-by-assumption tree. **D-7** campaign start/resume by the surrogate after the veto window (§10).
**D-8** sessions are resume-anywhere with no automatic hand-off (§4a.1).
**Q1** P-1/P-2 adopted (§7, §5). **Q2** KV3-SCHEMA-1 (tier column on
`bg_gochara_citation_resolution`): Kāla builds it as an Opus schema-prerequisite packet
with a coordination note to SS; SS may object within 24 h, in which case it reverts to
Suvarṇa's custodian; K-CERT stays blocked until the column lands. **Q3** PR #3441 is safe
for the running tracker (it reads the detached mirror); it stays open and unmerged under
`HOLD_MERGES` (D-6 revised); B-0/B-1 install from its reviewed head (D-9) and it merges
after certification-done. **Q4** the eight orphaned
pytest processes (PGID 13606) were terminated on 2026-10-11.

## 16. Owner steps (one prompt, any time)

1. Open a new Claude Code session (Claude Desktop app, macOS) in
   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan`, Opus 5.5
   (xhigh during Wave B, high afterwards) → paste **KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md**
   with the approved source commit. The session verifies the bundle, resumes from
   checkpoints, performs or supervises the remaining bootstrap (the campaign dispatcher is
   activated only after B-2's accepted receipt), and shows status. Close it whenever you like; open a
   new one whenever you like; progress does not depend on it.
2. You are asked for nothing routine. Hard stops (§4a.3) and veto-class decisions reach you
   as macOS notifications and in the cockpit `status`; `veto <id>` within 30 min reverses a
   veto-class decision.
3. Bundle changes follow the authorisation rule in the pairing rule: independently
   reviewed immutable source plus either your authorisation (by commit id) or an effective
   D-4 surrogate decision, each written as an activation record that chains to the previous
   one; changes to your decisions themselves remain yours alone.

## 17. Closure maps

**KS-01…KS-12 (review v2.0) → v2.1**

| finding | closed by |
|---|---|
| KS-01 | §0 closure procedure (roots first; field semantics; two tests; D-RETIRE decisions; namespaced ids); Wave 0 J-chain → J-4p after K0-SV |
| KS-02 | §5 capacity (33 > 15 → owner dispositions first; planner works by branch switch); B-0c prerequisites before B-1; bootstrap packets with `release_pins: not_applicable` and enumerated D-1 paths; `CLAUDE_BIN` + `cd "$WORKTREE"` in §7; implementation packets incl. `install.sh`, allocator, tracker changes; B-2 installs plan/prompts/cards/manifest and records the loaded tracker revision; B-3 on the installed bundle; new receipt after any change |
| KS-03 | B-3 isolation contract (override-preserving wrapper; second tracker on a reserved port under the dated scratch root; fixture detectors; fixture backend for git/PR/deploy/executor; acceptance incl. live EVENTS hash unchanged) |
| KS-04 | §10 (`--pre-resume` → `READY_TO_START`; release_id/digest binding; resume written after version validation + lock, then full gate; hold ownership; negative fixtures); §11 and §16 ordering |
| KS-05 | §6 (completion_kind declarations; artifact BUILD; STEP; author identity; REQUEST-PREP / PRE-ACCEPT / EXECUTE / POST-READBACK; K9-23 → B-1; legacy reconciliation; renew only claim holders; item lock) |
| KS-06 | §5 (base contains prerequisite heads; `kyalloc.py`; dated scratch root; registry seed; slots everywhere); §7 (`CLAUDE_BIN`, cwd, role-specific `--effort`, precheck via `KY_RUN`, `TESTS` newline list) |
| KS-07 | §8 (original failing base; admission classification incl. already-green assessment; artifact/operation semantic acceptance; schema-prerequisite dual declaration; `brief.migration`/`op` consistency; canonical `packet_sha256`; reasons on admission failure) |
| KS-08 | §6 verdict publication by the controller; enforced verifier boundary (§7); explicit REJECTED on invalidation; one inheritance predicate; `ky review` after every head change; head-match guard; final PR head vs squash merge commit |
| KS-09 | §12 finalisation outside the dispatcher; `DRAIN_RECEIPT.json` for C-3; PID/PGID + start identity; bounded independent reviewers; `FINAL_RECEIPT.json` for C-4 |
| KS-10 | §3 (Kāla DB Tests retained; COVERAGE includes §I; `FROZEN_PATHS.txt` manifest shared with precheck); §9 `platform/`-prefixed security and tracker globs; LIVENESS deleted → admission checks; B-4 extra sign-off wording removed |
| KS-11 | pairing rule (manifest digest named in each paste; `kyversion.sh` scope stated); `kylock.sh`; idempotent detached dispatcher start without an extra question; state init and all-return counting; planner checkpoints; `ky ack --steward`; strategy v1.2 §§2–4 made historical |
| KS-12 | §13 (baseline import before totals; session/child ownership and fixtures; separate completion measures with denominators; failure fingerprints; structured quota errors; Sonnet diff preserved on reroute) |

**KT-01…KT-08 (review v2.1) → v2.2**

| finding | closed by |
|---|---|
| KT-01 | pairing rule (source-commit anchor for planning; final-manifest digest for the conductor); planning read item 2 qualified; conductor setup has no `git pull` (§11); `OWNER_RESUME.approved_bundle_digest` = supplied digest (§10) |
| KT-02 | B-0c staged `fleet/mcp.none.json` + launch-input template; §7 `MCP_CONFIG` per job; planner launches/supervises B-1 directly |
| KT-03 | `kyversion.sh --bootstrap` for B-2/B-3; B-3/B-4 evidence recorded; B-5 final manifest + final receipt; both gate modes require final Wave B acceptance; negative fixtures (§10, §14) |
| KT-04 | §5 base contract with head→merge-commit mapping; §6 MERGE with `--match-head-commit`, queue cancellation on head change, no pushes under queue authorisation |
| KT-05 | §6 POST-READBACK two typed exits; operation COMPLETE via receipt + operation id; identity and negative fixtures |
| KT-06 | §11 session-state rule (same-session re-entry vs new-session reset; fingerprints never reset); applied to planner state; acceptance with consecutive hand-offs (B-1 tests) |
| KT-07 | §6 terminal release bound to item/worker/claim id; serialised with slot reuse; renewal stops at termination |
| KT-08 | §5 job scratch paths and dispatcher log under the dated scratch root; §7 launch I/O paths; cleanup rules |

**KV-01…KV-08 (Astra v2.3 delta review) → v2.4:** KV-01 pairing rule (single paste,
bootstrap manifest + review receipt, activation record, retired two-paste wording); KV-02
§4a.1 (state ownership, command queue, action records, recovery, checkpoint migration);
KV-03 §14 B-0c/B-2 (`kyboot.py` from an immutable staged bundle; dispatcher activation only
by the accepted bootstrap receipt); KV-04 §4a.2/§11 (deterministic controller, durable
stop/breaker, waits outside models, progress definition, DB session binding); KV-05 §4a.3
(decision state machine, `veto` controller, nothing published at proposal); KV-06 §7
(qualification receipts, launchd-context probes, unknown = refuse); KV-07 §15 D-6/D-9, B-2
(no main merges during the hold; install from reviewed heads); KV-08 §4a.3 hard stops
(platform approval is human; inherited §I/§L/§N.2 boundaries). KU-01…KU-03 remain B-0c
obligations (carried, not closed).

**KW-01…KW-06 (Astra v2.4 confirmation) → v2.5:** KW-01 §4a.1 legacy migration by evidence
type; KW-02 §4a.1/§11 controller as sole lock holder and state writer; KW-03 §14 Wave B
heading and B-2 (no main merge required; receipt-bound installation), §2/§13 baseline
prerequisite; KW-04 pairing rule successor chain + §16.3; KW-05 §6 SURROGATE trigger and
post-action; KW-06 §13 loop-health and platform-approval detectors, cockpit `approve-window`.

**KY-01 (Astra v2.6 confirmation) → v2.7:** cockpit step 7 write-scope clause replaced by
the scoped file-placement rule with the plan's authorised lifecycle exceptions (B-0a
disposals/archives, B-0c launch actions, B-2 installation paths, Git metadata), all via
action records; §5 capacity figure made a measured value.

**KX-01…KX-03 (Astra v2.5 confirmation) → v2.6:** KX-01 cockpit step 1 rewritten as
sequential phases (root prompt displayed, `C` assigned, no temp file); KX-02 B-2 row
replaced (no merge prerequisite anywhere); KX-03 entrypoints mapping for successor
bundles, surrogate authority loading from the caller's binding, roster modes.

**P-1/P-2 (planner's v2.3 proposal, proven by execution):** §7 launch line and probes; §5
`CLAUDE_BIN` version pin. **Owner direction 2026-10-11 (resume-anywhere, surrogate,
autonomy, zero idle):** §4a, §6 SURROGATE, §10 D-7, §11, §14 B-0c, §15 D-4…D-8, §16.

**KR-01…KR-12 (review v1.0):** KR-01/03/08/10 closed directly; KR-02/04/05/06/07/09/11/12
closed through the KS and KT replacements above (Astra v2.1 Part 1).

## 18. Risks
One subscription, headroom unreadable (backoff-and-report; one conductor; owner checks
twice daily) · Sonnet on L3 logic (routing, tests-first, Opus verifier, escalation) ·
dispatcher defects (fixtures per transition, `--dry` in CI, admission checks,
`no_progress_jobs`) · Suvarṇa slips (Wave B proceeds; the gate waits for the receipt) ·
scope creep (closure committed; additions need a MODEL job) · worktree ceiling (owner
dispositions precede any copy).

## Changelog
- v2.7 (2026-10-11): Astra v2.6 finding KY-01 applied; capacity figure measured, not fixed.
- v2.6 (2026-10-11): Astra v2.5 confirmation findings KX-01…KX-03 applied.
- v2.5 (2026-10-11): Astra v2.4 confirmation findings KW-01…KW-06 applied (see §17).
- v2.4 (2026-10-11): Astra v2.3 delta findings KV-01…KV-08 applied (see §17); D-4 amended,
  D-6 revised, D-9 added.
- v2.3 (2026-10-11): autonomy model (§4a) — resume-anywhere sessions, owner surrogate,
  headless launchd loops, zero-idle scheduling, cockpit prompt; P-1/P-2 launch fixes;
  delegated calls D-4…D-8 and Q1–Q4; `READY_TO_START` → `READY_TO_START`. Supersedes the
  planner's `KALAYANTRA_RELAUNCH_PLAN_v2_3_PROPOSED.md`.
- v2.2 (2026-10-11): KT-01…KT-08 applied (non-circular paste anchors; staged MCP config and
  direct B-1 supervision; bootstrap vs final version modes; squash-aware prerequisite
  containment and head-bound queueing; typed operation readback; session-state rollover;
  terminal claim release; scratch-root I/O).
- v2.1 (2026-10-11): all KS-01…KS-12 replacements applied; LIVENESS removed; verifier
  boundary made enforceable; finalisation moved outside the dispatcher; gate pre-resume
  mode; closure procedure made reproducible.
- v2.0 (2026-10-11): rebuilt from scratch after Astra v1.0. v1.0 withdrawn.
