---
artifact: KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md
status: ACTIVE — the dated record of owner decisions and owner-delegated calls for KĀLA-YANTRA v3
version: 1.1
authored_on: 2026-10-11
changelog:
  - "1.1 (2026-10-16): records D-OWNER-TESTS-20261016; campaign-wide optimum testing supersedes conflicting reversion and review-round rules."
record_rule: >
  Append a dated block per decision event. Owner decisions are the native's words; delegated
  calls name the delegate and the owner's delegating instruction. A delegated call never
  alters an owner decision. The surrogate's runtime decisions live in run/DECISIONS_SURROGATE.jsonl
  and the tracker, not here.
---

## 2026-10-11 (morning) — owner decisions (native, in chat)
1. Planner at xhigh. 2. 3 builders + 2 verifiers, scaling up on demand. 3. Re-scope to the
critical path. 4. The five-part Suvarṇa exit signal is the launch gate. 5. No token caps or
budgets. 6. ADHIKĀRIN on demand. 7. All Claude; no Codex; no local model. 8. Launch by a
pasted prompt in an interactive session.

## 2026-10-11 (afternoon) — delegated calls D-1…D-3 (delegate: Claude Code, Fable 5.1; instruction: "take a call on my behalf and close them")
- **D-1** Control-plane changes permitted in Wave B, scoped per packet, independently
  reviewed, installed with a hash-bound receipt; campaign builders keep the prohibition.
- **D-2** Rework from scratch (v2.0) then Astra; iterated to PROCEED-WITH-FIXES (v2.2).
- **D-3** The N-467 stop is lifted by an explicit recorded act (see D-7 for the autonomous form).

## 2026-10-11 (B-0a) — owner decision record (native via the owner surrogate; commit c35a316ae)
Worktree dispositions approved; 8/7 share of the 15 places; overrun rule; stray-process
handling. (Recorded in WORKTREE_DISPOSITIONS_v2_1.md / _v2_2.md.)

## 2026-10-11 (evening) — owner direction and delegated calls D-4…D-8, Q1–Q4
**Owner direction (native, in chat):** (1) sessions must be resumable at the owner's
discretion — open a new session, paste, resume; (2) fully autonomous, multi-agent,
interactive execution with a persistent owner surrogate that resolves every owner-wait;
(3) high velocity, zero idle, without loss of accuracy. Delegate: Claude Code (Fable 5.1);
instruction: "take a call on my behalf" on the planner's four questions.

- **D-4 Owner surrogate.** Authority: every owner-wait within the plan, including worktree
  dispositions, PR merges after independent review, capacity, packet/plan clarifications,
  Q-type questions, start/resume after the gate. Veto classes (30-minute window, owner
  notified): protected-window approval, campaign start/resume, plan-bundle changes, capacity
  above the configured maxima. Hard stops (owner-only): FROZEN-contract changes (§N.2);
  changes to the owner decisions; production data deletion/restore; Suvarṇa's integration
  branch or `ri02` before certification-done; credentials.
- **D-5 Merges.** The surrogate merges independently reviewed PRs; the owner no longer
  merges by hand. Rationale: the independent review is the accuracy gate; the merge is
  mechanical.
- **D-6 Merging during the certification hold.** Only PRs confined to `00_ARCHITECTURE/**`,
  `fleet/**`, `scripts/token_economy/**`, `platform/scripts/governance/pravaha_tracker/**`,
  `.claude/agents/**` (no `platform/src/generated/**`, writers, migrations or app code),
  batched, with a §6 coordination note to Strategic Suvarṇa 30 minutes before; SS may
  object. Rationale: these cannot restale Suvarṇa's integration PR; a merge still triggers
  a no-op deploy, hence batching.
- **D-7 Start/resume.** When `kygate.sh --pre-resume` prints `READY_TO_START`, the surrogate
  schedules the N-467 resume as a veto-class decision; on expiry it writes
  `run/OWNER_RESUME.json` and starts the conductor loop. The owner's cockpit `resume` does
  the same at once.
- **D-8 Resume-anywhere sessions.** No automatic hand-off thresholds; checkpoints after
  every step; the owner opens a new session whenever they judge the context has grown.
- **Q1** P-1 (`--bare` cannot sign in → `--setting-sources project`, explicit
  `--permission-mode`) and P-2 (`CLAUDE_BIN` ≥ 2.1.296; the owner ran `claude update`)
  adopted in plan v2.3 §7/§5.
- **Q2** KV3-SCHEMA-1 (tier column on `bg_gochara_citation_resolution`, a Brahmagyan
  table): Kāla builds it as an Opus schema-prerequisite packet (additive migration,
  protected window if required) with a §6 coordination note to SS; if SS objects within
  24 h it reverts to Suvarṇa's custodian; K-CERT stays blocked until the column lands.
  Rationale: Suvarṇa's single rebuild is complete and its campaign is wrapping up; waiting
  on it would stall the critical path; the K0-SV alignment governs declarations, not a
  column on a table Kāla's certification consumes.
- **Q3** PR #3441 does not affect the running tracker (it reads the detached mirror at
  `wt/campaign`), but it is a Kāla main merge under `HOLD_MERGES`; it merges under D-6.
- **Q4** The eight orphaned pytest processes (PGID 13606, PPID 1, ~15 h) were terminated
  with SIGTERM on 2026-10-11 (all exited; no SIGKILL needed).

## 2026-10-11 (night) — amendments after Astra's delta review of v2.3 (delegate: Claude Code, Fable 5.1)
- **D-4 amended.** The GitHub protected-environment reviewer approval is a human act that no
  surrogate can supply (KV-08). The surrogate's effective decision authorises the bounded
  campaign request; the approval click stays with the owner, batched (≤ 2 windows per wave),
  recorded as an external approval dependency while independent work continues.
- **D-6 revised.** No PR merges to main during the certification hold: Astra showed that
  every successful main CI run deploys the web app and can run routine migrations, so the
  "docs-only no-op deploy" rationale was false. Main merges are queued and executed by the
  surrogate after certification-done, each recorded with its actual workflow outcome.
- **D-9 (new).** Bootstrap and campaign installation use the independently accepted,
  immutable branch head bound in the installation receipt (never an unreviewed or
  assumed-merged tree). PR #3441 therefore stays open under the hold; B-0/B-1 install from
  its reviewed head.
- **Veto-class decisions** become effective only when the `veto` controller publishes them
  at the window's expiry after rechecking the unchanged target (KV-05); nothing is published
  at proposal time.
- **Bundle-change authorisation (KW-04, clarifying D-4).** A change to the plan/prompt/card
  bundle takes effect only through an activation record chaining to the previous one, with
  independently reviewed immutable source and either the owner's authorisation (commit id)
  or an effective D-4 surrogate decision after its veto window. Changes to the owner
  decisions themselves remain owner-only.

## 2026-10-16 (~16:03Z) — D-OWNER-TESTS-20261016 (owner, in chat)

The owner directed: "adopt this testing strategy for the entire campaign … make this an authoritative decision and amend any rules that exist." The authoritative verbatim standard and supersession are recorded in [D-OWNER-TESTS-20261016](DECISION_TESTING_STANDARD_v1_0.md).

One bounded review round; a second only for a BLOCKING finding. The reviewer enumerates every distinct production claim in the verdict and proves one source-cited oracle per claim passes at the pinned merged head and fails under its single planted reversion. Every real defect is fixed with fail-on-revert proof. Already-covered variants and changes with no production behaviour are non_blocking and never block MET or trigger another round. No per-mutant oracles, combinatorial variants or golden-capture of current output. N.8, N.7.6, SR-A4-01, A1 and personal-data handling remain unchanged.

(I) INTERPRETATION — model versioning: `plan_model.json` appends `+testing-standard-20261016` to `model_version`, following the existing additive suffix convention (`fleet/kyreconcile.py:343`). All blanket reversion `measures` descriptions and the tests glossary adopt this decision; detector types, paths, patterns and receipt shapes remain unchanged.
