---
artifact: ESCALATION_POLICY_v1_0
type: DECISION-ROUTING POLICY (amends CONDUCTOR_PROTOCOL.md §4 routing, §5 model/effort matrix, §8.8.iv)
version: 1.1
status: ACTIVE
authored_by: Cowork (Opus), native-directed 2026-07-18; Fable-5 dual review folded in same day
purpose: >
  Restore full autonomy by routing every milestone decision to where it belongs. The campaign lost
  autonomy in practice (engineering/process decisions surfaced to the native via manual paste-back)
  not by design. This policy says which decisions AUTO-PROCEED, which route to the Adjudicator
  (ADJUDICATOR_CHARGE_v1_0.md), and which — a deliberately small set — the wave halts-and-reports for
  ASYNC native review. Default: do not pause for the human.
precedence: >
  Where this policy and CONDUCTOR_PROTOCOL disagree (retry/PARK arithmetic, auto-proceed set, model +
  effort matrix, ceilings), THIS POLICY GOVERNS and the named protocol sections are amended
  accordingly. Everything this policy does not touch, the protocol still governs verbatim.
activation: >
  These two docs are dead letters unless the conductor reads them. REQUIRED WIRING (apply once):
  (1) CONDUCTOR_PROTOCOL §0 reading list → five items: this protocol + wave brief + previous
  REPORT_<wave>.md + ESCALATION_POLICY_v1_0.md + ADJUDICATOR_CHARGE_v1_0.md. (2) CONDUCTOR_PROTOCOL §4
  opens with "routing governed by ESCALATION_POLICY_v1_0.md; the Adjudicator operates under
  ADJUDICATOR_CHARGE_v1_0.md." (3) CLAUDECODE_BRIEF.session_open_instruction mirrors the five-item
  list. (4) CLAUDECODE_BRIEF.native_directives gains: "Amended 2026-07-18 — escalation per
  ESCALATION_POLICY_v1_0.md; its §2 native surfaces supersede the bare 'no human gates' line."
---

# Escalation Policy

## §0 — AUTO-PROCEED (no pause; no native involvement)

Protocol mechanics, not decisions. The conductor proceeds the instant the precondition holds. All of
these are done autonomously, at machine speed, in parallel where possible.

- **SPAWN a lane** — when the **clean Binder pass** (brief stamped `BOUND` + `BIND_<wave>.md`
  committed + §1.1 remit respected) and **gate-zero** hold. *gate-zero* = the Track-2 DONE-ASSERTION:
  `ref_planet_transit_get` answers without 401 AND `kala_temporal_bundle` reports
  `sidecar_available:true`. **Parallelism is maximal by default: every lane without a brief-declared
  data/merge dependency spawns concurrently; a lane runs serially only where the brief names the
  specific dependency forcing it. Undeclared serialization is a close-report defect.**
- **The full git cadence is auto-proceed** — per-lane commits in the lane worktree, pushing
  lane/integration branches to origin, `gh pr create`, merging a fully-receipted PR in the brief's
  declared merge order, and pushing `main`. No git operation short of history-rewrite / force-push
  (§4 irreversible class) waits on anyone. **State-ledger and decision-memo commits are PUSHED at
  every transition — an unpushed checkpoint is not a checkpoint** (a crashed conductor with local-only
  commits defeats §6 resume).
- **INTEGRATE** — when all cycle lanes are verifier-ACCEPT (independent reproduction, §1.7) with zero
  cross-lane interference in the sweep.
- **DEPLOY** — when integration is clean, CI green, and deploy is the only way to obtain a required
  live-MCP acceptance read.
- **SCOPE-LIMITED REBUILD** of 482012f1 — when R-5/protocol §8.2 requires it for a touched serving
  surface. (Full L1→L5 only if the Binder ruled it required. Abhinandan never rebuilt — CR-87 guard.)
- **CLEANUP is auto-proceed and MANDATORY at two points.** (i) *Per-lane, on merge:* the moment a lane
  is merged into the integration branch and the post-merge assertion sweep is green, its worktree is
  removed and its `wave/<wave>/<lane>` branch deleted (the merge commit is the record). A PARKED lane
  keeps its branch per protocol §4.3 but still drops its worktree. (ii) *At wave close:* protocol
  §2.8's verified sweep confirms zero `wave/*` worktrees and zero un-merged/un-parked branches remain.
  **A wave exiting via a §2 halt or §4 breaker still runs per-lane cleanup for every already-merged
  lane before ending the session. Stranded worktrees are a close-report defect.**
- Advance the wave pointer, write STATE/BIND/REPORT artifacts, run regression guards.

If a precondition is not met, it is not an auto-proceed — it becomes an Adjudicator decision (§1) or a
halt-and-report (§2), never a silent skip.

## §1 — ROUTE TO THE ADJUDICATOR (in-session; no native involvement)

The Opus Adjudicator rules per ADJUDICATOR_CHARGE §2, records ruling + reason + falsifier in the
ledger, the conductor continues. None of these reach the native.

- **Engineering forks:** rebuild-or-supersede, fold-into-later-lane vs standalone, which of two
  implementations, whether a diagnosed bug is on the critical path.
- **RE-BASELINE a moved served value** (this is an ADJUDICATION, not a §0 mechanic): the Adjudicator
  applies CHARGE §1.2 — the delta must be **arithmetically reconciled** and attributed to a **named
  merged change or a named intended feature landing**, recorded with a falsifier, before any re-pin.
  A re-pin that cannot name the change and reproduce the decomposition is REJECTED → treat as a
  regression. **Integrity-gate assertions (any assertion the brief marks `integrity: true`, always
  including the retrodiction/falsification gate) are NEVER re-baselined by the Adjudicator — a move
  there is §2.1, native-only.**
- **Lane disposition on a CONTESTED verifier result only.** Routine verifier receipts stand and do
  NOT route through the Adjudicator (that would serialize the swarm). The Adjudicator is invoked only
  when a CHARGE §1 standing rule bites on an ACCEPT, or a lane requests adjudication. Retry/PARK
  arithmetic is the protocol's: **up to 3 verification attempts (§2.3), then the lane PARKS (§4.3) and
  the wave routes around it** — the Adjudicator may order the next attempt but may **never** convert a
  verifier REJECT into an ACCEPT.
- **Artifact reconciliation:** stale bind-record values, transcription slips, register sync
  (the Adjudicator rules; per protocol §8.8.ii the **conductor** performs the register write / DR-n
  allocation — single-writer discipline).
- **Provisional doctrine** (Fable seat): record a provisional `DR-n`, continue; batch-ratified at
  campaign close (§3).
- **Carryover-artifact preconditions:** e.g. a scorer defect that must be fixed and re-validated on
  the train split before an admission loop can measure deltas — the Adjudicator gates the loop, in
  session.

## §2 — HALT-AND-REPORT for ASYNC native review (never blocks in-session; never auto-proceeds)

The wave does **not** sit waiting for a human and no agent polls for an answer. On a §2 trigger the
conductor writes a one-screen decision memo (`MEMO_<wave>_<n>.md` in this directory: what, why it
halted, options, the Adjudicator's provisional lean, the falsifier), commits+pushes it with the state
ledger in a `blocked` status, and **ends the session cleanly** (protocol §6.1). The native reviews the
memo asynchronously; the next conductor session resumes (§6.2) only after disposition. What
distinguishes §2 is that the wave **may not continue past it** — not that a human sits in the loop.

Exactly three trigger classes:

1. **A RED INTEGRITY GATE** — above all the retrodiction / falsification gate. If the kernel does not
   beat control, or beats it only within small-n noise (CHARGE §1.5), the run halts and reports the
   result AS-IS. **The Adjudicator may not disposition a red integrity gate toward green.** This is
   the campaign's reason for existing; it keeps a human witness at the one place a rule is most
   gameable.
2. **Contested + behavior-changing doctrine** (CHARGE §3) — a ruling that flips a served verdict and
   on which the classics genuinely disagree. (Non-behavior-changing or uncontested doctrine is a §1
   provisional `DR-n`, not a halt.)
3. **A circuit-breaker trip** (§4).

Note: a **lane PARK** (protocol §4.3 — 3 failed attempts, a lane-scoped destructive migration, etc.)
is NOT a §2 halt. The wave **routes around** a parked lane and continues; the parked item is async
native review at the next session, per protocol §4.3. Only a **wave-level** breaker (§4) or a red
integrity gate stops the whole run.

## §3 — THE NATIVE AS ASYNC REVIEWER (batched, non-blocking)

Everything the native should SEE but need not GATE accrues to a review queue, drained when convenient —
never per-milestone, never blocking a wave:

- the `DR-n` doctrine ratification queue (ratified/overturned in batch at **campaign close**, per
  protocol §4.1 / CLAUDECODE_BRIEF close_condition — not a wave-close blocker);
- each wave `REPORT_<wave>.md` (lanes, gates, findings, re-baselines with provenance);
- new register findings (example: the three `/api/retrieval/capability` callers logged for a future
  audit — an illustrative D-2 artifact, not a standing item);
- the Adjudicator's ledger of in-session rulings (spot-checkable, not re-litigated).

## §4 — CIRCUIT-BREAKERS (hard halt → §2 memo; override auto-proceed)

Autonomy runs free until one trips, then the wave stops per §2:

- **FROZEN §N.2 instinct** — a lane appears to need an orchestrator-contract change.
- **Test-set contact** — any read of the held-out LEL test split (events on/after the **2020-01-01**
  boundary; authoritative split = `BIND_<wave>.md`'s recorded split manifest) or the scoring harness
  by a build/admission agent. **Detection is structural, not self-report:** the harness path and the
  test-split artifact are on every build/admission lane's `must_not_touch`; the verifier's
  scope-warden pass greps the lane diff + transcript for access. Only the gate runner and anti-gaming
  verifier may read the test split; a builder/admission agent doing so → lane RED + wave halt.
- **Irreversible / destructive action** — data deletion, history rewrite, force-push, prod-credential
  change, anything a rollback pin can't undo.
- **Partial deploy** — one service promoted while another (web/mcp/sidecar/pipeline-job) failed.
  Default action: roll back to the §B rollback pin, then halt-and-report.
- **Budget breach** — cycle wall-clock/token ceiling exceeded (protocol §8.8.iv: PARK + report).
- **Repeated red** — a lane that has PARKED at 3 attempts AND its function is wave-critical (the wave
  cannot meaningfully close without it). Non-critical parks route around (§2 note) and do not halt.

**Breaker semantics mid-swarm:** in-flight sibling lanes are allowed to run to their next commit
(not killed), then the ledger is marked `state: halted_breaker`, `REPORT_<wave>.md` is written with
`status: blocked`, worktrees for un-merged lanes are preserved (merged lanes cleaned per §0), and the
session ends. The next session resumes via protocol §6.2.

## §5 — MODEL + EFFORT policy (efficiency without losing the floor)

**Amends the CONDUCTOR_PROTOCOL §1/§5 model matrix for the implementer and conductor seats.**

- **Implementer / conductor lanes — free MODEL choice per task.** Haiku for mechanical fan-out (greps,
  census probes, receipt collection, formatting), Sonnet for real builds, stronger where warranted.
  (This supersedes the fixed "Implementation model = Sonnet" assignment for these seats.)
- **Implementer / conductor lanes — free EFFORT choice per task** (standing, promoted from
  BRIEF_D2 §F1.6.2): dial reasoning-effort DOWN (`low`/`medium`) for mechanical work, UP (`high`) for
  real builds and root-cause analysis. Model and effort are two dials, chosen by the same
  task-complexity judgment.
- **Verifiers, Adjudicators, gate runner, anti-gaming verifier, migration guard — Opus or stronger
  (Fable for the doctrine seat), never below Opus, and always HIGH effort.** The party that says
  "done," "ACCEPT," or "gate green" is never a floor model and never a low-effort pass. This is the
  accuracy guarantee; it is not traded for speed. *(Exception preserved from protocol §5: D-2's
  synthesis gate deliberately ran on the weakest production model — a "weakest-reader" acceptance
  test, distinct from the Opus verification floor; see CHARGE §1.6 note.)*

## §6 — Net effect

| Decision class | Before (D-3 this session) | After |
|---|---|---|
| Spawn / integrate / deploy / push / PR / merge | human paste-back gate | AUTO |
| Per-lane + wave-close worktree cleanup | ad hoc | AUTO, mandatory |
| Rebuild? fold? diagnose a move? re-baseline? | human paste-back gate | Adjudicator, in-session |
| Retry / PARK | human "your call" | protocol §2.3 (3 attempts → PARK, route around) |
| Provisional doctrine | mixed | Fable `DR-n`, continue; ratify at campaign close |
| Red integrity gate / contested-doctrine / breaker | — | **halt-and-report, async native** |
| DR-n ratification, findings, reports | ad hoc | native, **async** |

Autonomy stops for the native at three things instead of forty. Efficiency comes from removing the
manual bridge and from per-task model+effort dials; accuracy is preserved by the Opus/high-effort
verification floor and the ported judgment in ADJUDICATOR_CHARGE §1; the human stays exactly where a
rule cannot safely stand in — the falsification gate.

*Changelog: v1.1 (2026-07-18) — Fable dual-review fixes: added §0 activation/wiring + precedence;
aligned retry/PARK to protocol §2.3/§4.3 (removed the invented "one re-run"); reframed §2 to
halt-and-report-async (no synchronous gate); split lane-PARK (route around) from wave-halt; added
parallelism-default, full git cadence, two-point worktree cleanup; moved RE-BASELINE into §1 with
arithmetic-reconciliation + integrity-gate carve-out; added EFFORT dial (§5) + model-matrix
supersession; defined gate-zero / clean-Binder-pass; made the test-set breaker structurally detectable;
specified breaker-mid-swarm + partial-deploy semantics; DR-n ratifies at campaign close; conductor is
single-writer for DR-n/register. v1.0 (2026-07-18) — initial.*
