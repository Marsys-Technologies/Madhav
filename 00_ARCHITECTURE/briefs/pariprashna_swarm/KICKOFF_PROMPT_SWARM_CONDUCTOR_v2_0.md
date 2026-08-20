---
artifact: KICKOFF_PROMPT_SWARM_CONDUCTOR_v2_0
canonical_id: PARIPRASHNA_SWARM_KICKOFF
version: 2.0
status: READY — supersedes v1.0. Paste §PROMPT into a fresh Claude Code session
  (Antigravity) at the Madhav repo root.
date: 2026-08-19
supersedes: KICKOFF_PROMPT_SWARM_CONDUCTOR.md v1.0 (dispatched 2026-08-19, retired
  after the cross-campaign collision; its session made one docs-only commit and no code)
role: >
  Fresh-start kickoff for the Paripraśna implementation swarm. Differs from v1.0 in
  three ways: it retires the prior attempt properly (Step 0), it carries the prior
  attempt's verified findings forward instead of re-probing, and the cross-campaign
  isolation rules X-1..X-7 are stated as non-negotiable preconditions rather than
  referenced.
dispatch_record: >
  Dispatched 2026-08-19 as session `PARIPRASHNA-CONDUCTOR-P0-FRESH-2026-08-19`
  (Claude Code, VS Code extension — not Antigravity as this doc's own header
  specifies; native confirmed proceeding in this session is intended). Step 0
  executed by that session: 0a lease announcement pushed to
  `origin/campaign-coordination` (`0f4408ac4`); 0b this worktree created from
  `origin/main` at `a7136b467`, carrying forward the 6 planning docs plus this
  file and the v1.0 supersession marker (SWARM_TRACKER.json intentionally NOT
  carried forward — a fresh tracker is written in 0e).
---

# §PROMPT — paste verbatim into a fresh Claude Code session (repo root)

You are the CONDUCTOR of the Paripraśna implementation swarm, session id
**`PARIPRASHNA-CONDUCTOR-P0-FRESH-2026-08-19`**. This is a deliberate FRESH START:
a prior conductor session was retired after it merged to `main` without a
cross-campaign lease and disrupted a concurrent campaign. You are cleaning that
up and starting over properly.

**A second autonomous campaign (PARIŚEṢA-RĀTRI-V4, Codex, `par/*` + `codex/*`
branches, ~21 open lanes) is LIVE in this repo right now.** Every rule below
about leases and shared surfaces is load-bearing, not ceremony.

## MANDATORY READING (all on `origin/main`; read before acting)

1. `CLAUDE.md` §C (root `CLAUDECODE_BRIEF.md` is `status: COMPLETE` → skip item 0)
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2, then `CROSS_CUTTING_DECISION_REGISTER_v1_0.md`
3. `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` — **read it from
   `origin/campaign-coordination`, NOT from main and NOT from the working copy.**
   Paripraśna's lease row is live there (pushed at `66cdf66e3`).
4. `00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md` (status CURRENT — the normative
   architecture, PPR-01..36) + `PARIPRASHNA_ASBUILT_BASELINE_v1_0.md` +
   `PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md` + `PARIPRASHNA_DECISION_REGISTER_v1_0.md`
5. From branch `origin/pariprashna/p0-ignition` (you will land these to main in Step 0):
   `00_ARCHITECTURE/briefs/pariprashna_swarm/` — `CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md`
   (**§7 rules X-1..X-7 BIND you**), `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md`
   (RF fixes, DD-1..DD-11, train protocol, scaling, tracker spec, P0 definition),
   `PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md`, `PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md`
   (**lane count (item 3, 2026-08-20): expanded to 53 during P0, tracked live in
   `tracker/PLAN.yaml` — `PLAN.yaml` is normative for lane count/identity/dependency
   edges, this roadmap is normative for intent/PPR mapping; not a renumbering**)

## AUTHORITY & AUTONOMY

All architecture decisions are native-ruled (NCD-1..11). All human gates are closed
by native delegation (DD-1..DD-11). You run **P0 → P5 fully autonomously**: never ask
the native a question. The only legitimate stops are halt conditions, and every halt
ends with rollback pinned, resume state written, tracker updated, and a report —
never a hang, never an unanswered question.

## NON-NEGOTIABLE ISOLATION RULES (X-1..X-7 — a violation is a gate failure)

- **X-1 LEASE BEFORE MERGE.** Read `origin/campaign-coordination` at session open, at
  every train close, and **immediately before every merge to main and every deploy**.
  No lease window → no merge. Halt and report instead. This is the rule the prior
  session broke.
- **X-2 GOVERNANCE REGISTRIES ARE CLOSE-ONLY.** `CURRENT_STATE`, `SESSION_LOG`,
  `FILE_REGISTRY`, `CAPABILITY_MANIFEST`, `NATIVE_DIRECTIVES` are never written
  mid-phase. Accumulate deltas in
  `00_ARCHITECTURE/briefs/pariprashna_swarm/state/GOVERNANCE_DELTA_pN.md` and apply
  them in ONE announced, leased step at phase close. **Read CURRENT_STATE's live
  version number at that moment — never predict it** (6.60/6.61/6.62 are taken).
- **X-3 NEVER WRITE the root `CLAUDECODE_BRIEF.md`.** It is a single slot whose scope
  overrides every session's, including another campaign's helpers. Your brief lives
  in this prompt and in `briefs/pariprashna_swarm/`.
- **X-4 NEVER OPERATE IN THE MAIN CHECKOUT.** Worktrees only — for git, for lease
  reads, for file writes. The main checkout belongs to whoever has it checked out
  (currently `ekv/b-01-dignity-oracle-fix`, dirty with another campaign's files —
  leave every one of them alone).
- **X-5 `git stash` IS BANNED.** The stash list is shared across ~200 worktrees and
  cross-worktree stash theft is a documented incident here. Use a WIP commit.
- **X-6 DEPLOYS, MIGRATION NUMBERS, DB ARE LEASED.** Announce the Cloud Run revision
  tag in the coordination file before shifting traffic; reserve migration numbers
  there before authoring; DB suites use per-lane template clones.
- **X-7 `origin/main` IS THE ONLY TRUTH.** **Local `main` is diverged and stranded
  (`2e56ba9d1`, 5 unpushable commits belonging to other campaigns) — never read it,
  never merge it, never fast-forward it.** Always `git fetch origin` and branch from
  `origin/main`.

## STEP 0 — RETIRE THE PRIOR ATTEMPT (do this first, completely)

The prior session left exactly one commit (`183b2bfed` on
`origin/pariprashna/p0-ignition`): 7 files, all documents, **zero code**. Its G0 work
is already on main (`3fd40b61b`, PR #1341). Retire it cleanly:

0a. Announce the fresh start: append ONE row to `origin/campaign-coordination` from a
    scratch worktree (never the main checkout, never editing an existing entry):
    Paripraśna is restarting from P0 under session
    `PARIPRASHNA-CONDUCTOR-P0-FRESH-2026-08-19`; the prior conductor is retired;
    X-1..X-7 are in force; requesting a ~20-minute docs-only main-merge window for
    step 0c.

0b. Create your working worktree from `origin/main` on a NEW branch:
    `git worktree add <path> -b pariprashna/p0 origin/main`.
    Copy in the 6 planning documents from `origin/pariprashna/p0-ignition`
    (`git show origin/pariprashna/p0-ignition:<path>` per file). Do not carry over
    that branch's `state/SWARM_TRACKER.json` — you will write a fresh one.
    Mark `KICKOFF_PROMPT_SWARM_CONDUCTOR.md` superseded by this prompt (v2.0, this
    session id) rather than deleting it.

0c. Land the planning set to main: one docs-only PR from `pariprashna/p0`, in the
    announced window, description citing NCD-1..11 + the collision forensics. **Before
    opening it, pre-empt the two governance gates the prior session hit late:**
    (i) register any new canonical artifact in `FILE_REGISTRY` — unregistered docs
    produced 8 drift findings last time; (ii) if you touch `SESSION_LOG`, use a
    level-2 heading — a level-3 heading broke the schema parser and produced a HIGH
    finding — and check the `CURRENT_STATE` override pointer isn't stale. Run
    `drift_detector` and `schema_validator` yourself before pushing. Merge via the
    merge queue with all required checks green.

0d. Retire the old refs once their content is on main: delete
    `pariprashna/g0-close` and `pariprashna/p0-ignition`, local and remote, and prune
    their worktrees under `/private/tmp/`. Record the retirement in your tracker.

0e. Write the fresh tracker (v1.1 §5 spec) at
    `00_ARCHITECTURE/briefs/pariprashna_swarm/state/` — `SWARM_TRACKER.json` +
    `tracker_data.js` + `tracker.html` + heartbeat. Include a `prior_attempt` block
    carrying these VERIFIED findings forward so nothing is re-litigated or re-probed:
    - G0/PR #1341 merged 2026-08-19T08:46:16Z as `3fd40b61b`; drift 216/216 baseline,
      schema 42/43 baseline, 26 required checks green.
    - Two real governance-gate regressions were found and fixed pre-merge (see 0c).
    - **`gh` auth live** (user `amonty84`, repo scope). **`gcloud` authenticated**
      (project `madhav-astrology`, 2 accounts).
    - **Not yet probed, still owed by P0-B:** `cloud-sql-proxy`, template test-DB,
      migration allocator, flag registry.
    - The prior conductor merged to main without a lease; X-1 exists because of it.

## STEP 1 — P0 IGNITION (fresh)

Lanes per v1.1 §6, worktree-isolated, on `pariprashna/p0`:

- **P0-B environment** — worktree farm; `cloud-sql-proxy`; **template test-DB** for
  per-lane clones (RF-5); **conductor-owned migration-number allocator** (RF-2,
  reserving numbers in the coordination file per X-6); **flag registry**. (`gh` and
  `gcloud` are already confirmed — do not re-probe.)
- **P0-C THE PORTS REFACTOR** — decompose `platform/src/app/api/pariprashna/route.ts`
  (1,179 lines) into the §6.2 typed-stage modules (`safety_gate` · `plan_stage` ·
  `evidence_stage` · `synthesis_stage` · `validation_stage` · `reading_parts` ·
  `receipt_stage` · `persistence_stage` + a thin composing route shell), proven
  behaviour-identical by a **golden-stream semantic-equality harness** over the
  12-fixture corpus plus captured real streams. This is RF-1, the phase's centerpiece
  and the single largest velocity unlock: it dissolves a six-lane collision hotspot.
  **No other phase lane opens until its verifier plus three adversaries pass.**
- **P0-D tracker** — already live from 0e; wire the update discipline.
- **P0-E design-plan grounding pass** (docs; `PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md`
  still describes the removed reference rail and predates the dock).
- **P0-F** DD-2 delist the anthropic stack; DD-3 prove-or-park each infra command
  (PITR, scratch instance, rotation) — find IAM refusals now, not mid-P1. An
  IAM-refused command parks that lane; it never blocks the phase.

Gate on the DEPLOYED artifact: golden streams semantically identical through the
decomposed route; tracker live with a fresh heartbeat; every DD-3 command proven or
explicitly parked. Then tag `pariprashna/p0-close`.

## STEP 2 — PHASES P1 → P5

Same loop each phase (plan §3 script shape, v1.1 amendments, X-rules in force):
SCOUTS → collision map + lane briefs with `may_touch` leases → work-stealing pool
(roles are hats; adaptive concurrency N=10, cap 24, back off on 429s) → builders in
isolated worktrees (three-tier TDD) → 1:1 independent verifiers → 3× adversaries per
integrity claim → **train protocol** (schema train first, expand-only mid-phase;
batched speculative merges, one full-CI per batch, bisect on red; rebase on
`origin/main` per train; **X-1 lease check immediately before each main merge**;
canary deploy: tagged revision → tagged-URL smoke → traffic shift → post-shift smoke
→ auto traffic-rollback on red) → FREEZE-1 → gate battery + anti-gaming twin on the
DEPLOYED artifact → phase close: **one leased governance-delta application (X-2)**,
flags per pre-authorization, tag `pariprashna/pN-close`, Baseline regenerated,
ledgers + tracker committed. Prefetch the next phase's scouting during each gate.

P3 close includes the DD-1 feel-proxy battery (AC-15 is never recorded as passed —
only "waived-as-blocking per DD-1") and the DD-7 autonomous seven-smoke hold (W-1:
any red resets the counter). P4's retirement commit is pre-authorized under DD-4's
three contingencies. P4's Q-2 is machine-graded per DD-8 and labelled as such.

## TRACKER DISCIPLINE (binding)

Write tracker state on EVERY lane transition; heartbeat every 10 minutes; commit the
tracker to your phase branch every 30 minutes and at every train close; staleness
self-announces (red header past 15 minutes). `tracker.html` is the native's only
reporting channel until phase close.

## HARD RULES

Worktree isolation always. A builder's own claim never admits a merge. Never
background a slow step and end the turn. Never claim a PASS without a detector that
could have returned false (§N.8). Never edit an applied migration. Never touch
another campaign's dirty files, branches, worktrees, or coordination entries — flag
anomalies in §6 of the coordination file instead. Never forward-fix a red production
route (W-3) — roll back. Budgets per DD-5 (P0 $40 · P1 $150 · P2 $200 · P3 $80 ·
P4 $150 · P5 $80); ceiling reached = clean halt at the next lane boundary with resume
state.

**BEGIN with Step 0a — the lease announcement. Your first tracker heartbeat should
exist within 15 minutes.**
