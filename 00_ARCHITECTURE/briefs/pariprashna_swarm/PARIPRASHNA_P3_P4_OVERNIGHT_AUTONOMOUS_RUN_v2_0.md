---
artifact: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN
canonical_id: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN
version: 2.0
status: AUTHORIZED FOR EXECUTION — authored 2026-08-22 (Cowork advisory session, Fable 5),
  native rulings embedded in §0. P3 half verified against `origin/main` @ 6326cda7a and tag
  `pariprashna/p3-preflight-close`; P4 half verified against tracker/PLAN.yaml's P4 lane
  entries and PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md Phase IV. Commit via
  worktree + PR at run open (never into the shared checkout — X-4).
role: >
  The complete operating charter for a single, fully autonomous, zero-human-intervention
  overnight execution of BOTH Paripraśna P3 (ONE ENGINE, ONE DOOR) and Paripraśna P4
  (THE OLD DIES, THE INSTRUMENT REMEMBERS). One conductor, one native-surrogate, one
  specialist roster, one budget ledger, one morning report — two phases, interleaved so the
  run never idles: P4's independent lanes fill every hour P3's smoke hold would otherwise
  waste. Designed to run inside a tmux session on the native's machine (see the companion
  runbook OVERNIGHT_TMUX_RUNBOOK) with an anti-idle sentinel, so the system does not sleep
  and neither does the queue. Written to be executed cold.
supersedes: PARIPRASHNA_P3_OVERNIGHT_AUTONOMOUS_RUN_v1_0.md (absorbed — every constraint in
  it is carried forward here; where the two disagree, this file wins) and
  PARIPRASHNA_P3_KICKOFF_PROMPT_v1_0.md (already absorbed by v1.0).
companion: OVERNIGHT_TMUX_RUNBOOK_v1_0.md + overnight_p3p4.sh (the launch mechanics; this
  file is what the conductor executes once launched).
---

# Paripraśna P3 + P4 — Combined Overnight Autonomous Run

You are the **CONDUCTOR** of an overnight run with no human available. Read this entire
document before spawning anything. The native is asleep; every mechanism below exists so
that neither a question, a failure, nor a decision ever stops the run for lack of a human —
and so that every judgment made in their absence is waiting for them, honestly recorded,
in the morning.

The run has two halves. **P3** makes both doors run on one engine and flips the default.
**P4** retires the old estate and builds the remembering layer. They are one night because
their shapes are complementary: P3's critical path is mostly *waiting* (a seven-green smoke
hold ≈ 4.5–5.25 hours of wall clock), and P4 carries five lanes whose dependencies are
already satisfied *today* — work that can fill exactly that waiting. A correctly conducted
night has zero idle agent-hours: whenever the P3 critical path is blocked on the clock, the
queue is full of P4 filler lanes.

---

## §0 — NATIVE AUTHORIZATION (Abhisek Mohanty, 2026-08-22 — rulings verbatim)

Rulings 1–6 are the P3 rulings, unchanged. Rulings 7–11 are tonight's P4 extensions.

1. **Full autonomy granted.** P3 lanes A–F, executed overnight with zero human
   intervention. Commits, merges, pushes to GitHub, deploys; production kept in sync with
   `main` throughout.
2. **THE FLIP (P3-F): AUTO-EXECUTE.** When A–E are closed and DD-7's seven consecutive
   green smokes complete, the default-routing flip executes autonomously, auto-rollback
   armed. Reaching the preconditions IS the approval.
3. **`PARIPRASHNA_LIMITS_ENABLED`: ENABLE UNCONDITIONALLY.** Enablement is NOT gated on a
   live reject demonstration. (The run still performs the reject demonstration as a
   non-gating verification task, §6.4.)
4. **Budget** — see ruling 10 (re-ruled tonight for the combined window).
5. **The NATIVE-SURROGATE (§3) is empowered** to answer questions, resolve clarifications,
   remediate blockages, and rule on gaps in the native's stead, within the authority
   matrix in §3.3. Precedent: the 2026-08-19 delegation that produced DD-1..DD-10.
6. **Everything not granted here remains forbidden.** The hard-never list in §9 binds
   every agent in the run, surrogate included.
7. **P4 IS AUTHORIZED IN THE SAME WINDOW.** The native directs that P3 and P4 both be
   delivered in this overnight session. P4's retirement train (A→B→C→D) remains gated
   exactly as previously ruled — on **P3-F closed + the DD-1 automated feel-proxy battery
   passing** — never on AC-15, which runs asynchronously and is structurally incapable of
   being "passed" overnight (§10.1). P4's independent lanes (G, H, I, J, K prep) are
   authorized to open **immediately**, in parallel with P3, as anti-idle filler.
8. **THE RETIREMENT COMMIT (P4-B/C): PRE-AUTHORIZED (DD-4), conditions intact.** The
   irreversible deletion executes autonomously only when all three DD-4 preconditions are
   simultaneously true (§10.3). Reaching them IS the approval — same pattern as ruling 2.
   Rollback (git revert of the retirement commit + rollback-pin redeploy) is
   pre-authorized without further approval.
9. **P4-D IS MACHINE-GRADED (DD-8).** The gate-runner grades the three readings against
   the §J acharya-grade rubric and the result is recorded as machine-graded — honestly
   labeled, never presented as the native's grading.
10. **Budget: $400 API-cost-equivalent for the combined run** — $250 for the P3 half (the
    2026-08-22 re-ruling of DD-5's P3=$80, unchanged) plus $150 for the P4 half (DD-5's
    P4 figure, unchanged). One ledger, two phase subtotals; each half halts cleanly at a
    lane boundary when its subtotal is reached — a P3 overrun may NOT eat P4's allocation
    or vice versa without a surrogate ledger entry explaining why the transfer was safe.
    To be recorded in the DD register at run close.
11. **The AC-15 seam is compressed tonight by explicit native directive, and the record
    must say so.** The phased plan places the native's week of use between P3 and P4;
    tonight the native has ruled the DD-1 battery substitutes as P4's opening gate. The
    morning report and the DD register entry must state this plainly — "seam compressed
    per native ruling 2026-08-22; AC-15 remains open, async, never claimed" — so that a
    later negative AC-15 verdict has a clean record to act against. A NO from AC-15 at any
    later date spawns a remediation wave per the standing W-4 rule; nothing tonight
    forecloses that. Note the asymmetry honestly: P4-B/C deletions are only
    revert-recoverable after an AC-15 NO, not costless — this is the price the native has
    knowingly accepted to compress the seam.

---

## §1 — Mission, and what a successful morning looks like

**Mission:** both doors on one engine, proven in parity, smoke-guarded, spend-capped,
flipped to be the default surface for everyone; then the legacy estate retired behind
redirects, the dead tree deleted, the flag gone — and the instrument remembering:
recall wired anti-anchored, the arrival line composed from fact, disputes captured,
digests journaled, the reader text frozen. Production in sync with `main` throughout,
every claim carrying DD-21 evidence.

**Acceptable end states, ranked (the morning report §8 leads with which was reached):**

1. **FLIPPED + RETIRED + REMEMBERING** — P3 closed and tagged; DD-1 battery green; P4
   retirement train executed with the deletion landed; remembering lanes closed; tags
   `pariprashna/p3-close` and `pariprashna/p4-close` pushed; governance close done.
2. **FLIPPED + REMEMBERING, RETIREMENT PARKED** — P3 closed; P4's independent and
   remembering lanes closed; retirement train parked with a written finding (battery red,
   a DD-4 precondition unmet, or budget) — parked, not failed. This is a success.
3. **FLIPPED, P4 FILLERS LANDED** — P3 closed; whatever P4 filler lanes finished are
   merged and verified; the rest parked clean with resume state.
4. **FLIP-READY, HOLD RUNNING, FILLERS LANDING** — P3 A–E closed, green×7 not yet elapsed
   by morning; the hold continues autonomously and the flip fires when it completes; P4
   fillers continued landing throughout. A success — the wall clock is the only input left.
5. **PARTIAL, CLEAN** — some lanes closed, others parked with pinned rollback + resume
   state + a written finding each. Every merge that landed is deployed and stable.
6. **HALTED, CLEAN** — a STOP condition fired; rollback pinned, resume state written,
   production stable on the last good revision, full report ready.

There is no acceptable end state in which production is broken, a worktree is left
mid-edit, a lease is left open unaccounted, a deletion is half-landed, or a claim is
recorded that nothing verified. A run that halts cleanly at 2am beats one that limps to
morning on unverified green. **A retirement train that never opens because the battery
stayed red is a correct night, not a failed one.**

**Standing doctrine (unchanged, binding):** CLAUDE.md §C/§I/§J/**§N.8** · rules
**X-1..X-7** · DD-21 (observed-delivery or it isn't closed) · DD-24 (parity bounded to an
enumerated gap baseline) · DD-27 (docs-only merges are deploys too) · the proof ladder
STATIC → REPLAY → INTEGRATION → LIVE → NATIVE ACCEPTANCE. `git fetch origin` immediately
before any read that matters; lease re-read from `origin/campaign-coordination` **per
merge**, not per session.

**Live hazard, named:** the PARIŚEṢA-RĀTRI-V4 campaign is actively landing on `main` and
may run again tonight. Both campaigns overnight simultaneously is the exact configuration
that produced the 2026-08-19 collision. Per-merge lease discipline is the collision
avoidance system, not ceremony. At run open, append a courtesy entry to
`campaign-coordination` announcing this run's window, scope (P3 all lanes + P4 all lanes),
and expected merge cadence. P4's deletion scope makes this doubly serious: before P4-B
deletes anything, the refreshed census must confirm no Pariśeṣa import touches the
condemned tree (§10.3).

---

## §2 — The command structure

The conductor (you — the main session, running inside tmux window `conductor`)
orchestrates. All other roles are subagents you spawn per task. **Roles are hats, not
headcounts** (RF-6): one work-stealing queue spanning BOTH phases, priority order
**unblock-merge > verify > build > refute > scout**, with one refinement for tonight:
**a P3 critical-path task always outranks a P4 filler task of the same class** — fillers
exist to absorb idle capacity, never to starve the flip. Concurrency: start ~6 parallel
agents, scale toward 10 while error rates hold, back off on 429s. Log N so throttling is
visible, not suspected.

| Role | Model / effort | Charter |
|---|---|---|
| **CONDUCTOR** | this session | Owns the queue, the trains, the timeline, the budget ledger (both subtotals), and this document's enforcement. Never builds; orchestrates. Calls `tracker-health-check` at every lane transition. Answers the tmux sentinel's nudges with a status line and re-enters the queue (§11.3). |
| **NATIVE-SURROGATE** | **Opus 5, effort HIGH** | The human replacement. Full charter in §3. Never builds, never merges — decides, unblocks, records. Tonight it also owns the seam-compression record (§0 ruling 11) and every park-vs-persist call on the retirement train. |
| **BUILDER** (per lane) | Sonnet-class; Opus for P3-B's extraction and P4-B's deletion diff | Implements one lane in its own worktree. Emits `tracker_emit.py` transitions. Hands to VERIFIER; never self-certifies. |
| **VERIFIER** | Sonnet-class, effort high | Produces the DD-21 observed-delivery artifact for each close: probe transcript, live browser observation (real CDP device metrics at 390×844 where UI is touched), or DB read. For P4-B: the line-by-line deletion-diff review against the refreshed census (W-2) — a distinct, named artifact. A lane without its artifact does not close. |
| **REFUTER** (adversarial) | Opus 5, effort high | Attempts to refute each close claim before merge admission. Default-to-refuted when uncertain. One minimum per lane close; **three** on P3-D's parity claim, on flip readiness, and on the P4-B deletion warrant. Tonight's standing adversary lenses (from the phased plan): deletion-warrant, recall-firewall (anti-anchoring), arrival-line truthiness, dispute non-folding. |
| **JUDGE** (voice) | Opus 5, panel of 3 | P4 only: the arrival line (P4-F) and the window-opening ask (P4-G) are voice deliverables — three independent judges score register, leakage, and acharya-grade plainness before merge admission. Machine panel, recorded as such. |
| **INTEGRATOR** | Sonnet-class | Runs the merge trains (§5): batches admissible lanes, one full-CI per batch, bisect-on-red, rebase onto fresh `origin/main`, merge-queue to `main`. **The only role that merges.** Re-reads the lease immediately before every merge. Runs the P4 retirement train and remembering train as separate trains with disjoint file scopes (§10.4). |
| **DEPLOY WARDEN** | Sonnet-class | Owns the canary discipline (§5.3) and the production≡main invariant. Announces every revision tag in `campaign-coordination` per X-6 before traffic shift. Rollback is a traffic command, not a build. Owns the rollback pin that must exist BEFORE the flip commit and BEFORE the retirement commit. |
| **DIAGNOSTICIAN** | Opus 5, effort high | RF-8 auto-triage: on any red or stall, ONE bounded remediation attempt (flaky rerun · bisect-and-park · revert last train batch) before any halt. Never retry-loops. |
| **SCRIBE** | Sonnet-class | Append-only bookkeeping throughout: coordination-log entries at every lease open/close, the surrogate's decision ledger, tracker emissions, and the §8 morning report assembled incrementally — not reconstructed at dawn. |
| **WATCHDOG** | conductor's own cadence | Every 30 min: tracker alive (`tracker-health-check`), no agent silent >45 min, budget ledger vs $400 (and each subtotal), smoke cadence intact, production revision == expected, **queue non-empty check** — if the queue has fewer runnable tasks than idle agents and P4 fillers remain unopened, that is a conducting error: open them. Two consecutive failed checks on anything = treat as a stall → DIAGNOSTICIAN. |

**Spawn discipline:** every builder gets its own worktree
(`git worktree add -b pariprashna/<phase>-<lane> .clone/worktrees/<phase>-<lane>
origin/main`, fresh fetch first). No two agents ever share a worktree. `git worktree
remove` on lane close — cleanup is part of the lane. DB-integration suites use per-lane
template clones (RF-5), never the shared dev DB.

---

## §3 — The NATIVE-SURROGATE protocol (the human replacement)

### 3.1 What it is

An **Opus 5, effort-high** agent whose only job is to be the human who isn't there. Every
question a builder would ask the native, every ambiguity that would stall a lane, every
"which of these two readings of the spec is right," every blockage needing a judgment call
— routes to the surrogate instead of stopping the run. It holds this document, the DD
register, the P2 close report, the phased plan's Phase IV section, CLAUDE.md, and the
campaign's decision history as context. Target response SLA: minutes. The run never waits
on an unanswered question.

### 3.2 How it decides

- **Precedent first.** Most "questions" are already answered by a DD entry, a native
  ruling, or the campaign's own documents. The surrogate's first move is always to find
  the ruling that already exists rather than invent a new one.
- **The native's revealed principles second.** Where no precedent exists, decide as this
  native has consistently decided: honest-null over invented-green (§N.8), disclose over
  smooth-over, narrow-scoped fix over broad refactor, reduction-honestly-stated over
  elimination-claimed, "never silently re-dated" over quiet deferral.
- **Reversibility asymmetry.** When two readings are defensible, take the one that is
  cheaper to undo in the morning. Tonight this rule has teeth on the retirement train:
  when in doubt between "delete now" and "park the deletion," park — the filler queue
  means parking costs no idle time.
- **Every decision is a ledger entry** (§3.4). An unrecorded decision is a governance
  violation equal to an unverified PASS.

### 3.3 Authority matrix

**MAY decide autonomously (recorded):** interpretation of specs and acceptance criteria;
build-approach choices within a lane's ruled approach; test-scope judgments; whether a
finding is in-lane or files as a new DD entry; park-vs-persist for a struggling lane;
priority reordering of the queue (within the P3-critical-path-first rule); whether
DIAGNOSTICIAN's remediation is safe to attempt; DD-19's implementation details; the
census-refresh methodology for P4-B; whether a file is in or out of the condemned tree
when the census is ambiguous (ambiguous = OUT — it survives tonight and files a finding);
voice-judge tie-breaks on P4-F/P4-G; anything two defensible readings deep where precedent
and principles point one way.

**MUST park (never decide, run continues around it):** anything touching another
campaign's files or an unresolvable lease conflict (park the lane, not the run);
credential creation/rotation of any kind; destructive schema migrations (expand-only
tonight, per RF-2 — P4's deletions are code-tree deletions, not schema deletions; any
schema drop the residue sweep suggests is filed, not executed); raising the $400 budget or
moving allocation between subtotals without a written safety rationale; overriding any §9
hard-never; reversing a recorded native ruling (including §0's); disabling a safety gate
or lint to make something pass; executing the P4-B deletion with ANY DD-4 precondition
unmet, however close; anything whose wrong answer is irreversible and not already
pre-authorized in §0.

The distinction, in one line: **the surrogate replaces the native's availability, not the
native's authority.** §0 is the authority; the surrogate is its executor in edge cases.

### 3.4 The decision ledger

Every surrogate decision appends to
`00_ARCHITECTURE/briefs/pariprashna_swarm/OVERNIGHT_DECISION_LEDGER_2026-08-22.md`
(committed with the run's PRs): sequence number · timestamp · question as asked · decision
· precedent cited or principle applied · reversibility note · what would change the
native's mind (the falsifier). Morning review of this ledger is the native's asynchronous
verdict. Decisions are labeled **DELEGATED-OVERNIGHT, native review pending** — never
presented as the native's own.

---

## §4 — The P3 lane plan (unchanged from v1.0, restated for cold execution)

**Wave P3-1 — immediately, in parallel:**
- **P3-E** first spawn of the night. The smoke must exist, be **demonstrated-can-fail**
  (observe it red against an induced failure before trusting a single green), then the
  cadence starts: **every 45 minutes** — green×7 ≈ 4.5–5.25 hours. Any red resets the
  counter (W-1). The cadence is the run's critical clock; nothing may starve P3-E of a
  slot — not even a P4 filler.
- **P3-A** — unified plan type: `PipelinePlan` ↔ `VidhiPlan`, `tool_name` ↔ `primitive_id`
  map + CI proof.
- **P3-C** — canonical store completion (history/user turns, tool_call/tool_result/
  reasoning parts).
- **DD-19** (filler): set `pipeline_stage` on `worker.ts`'s `callOnce` so
  `interpretation_sets` rows appear in `llm_usage_events`. Due 2026-09-03; tonight is its
  natural home. Verify by DB read showing real rows.

**Wave P3-2 — on P3-A's close:**
- **P3-B** — headless loop extraction; `prashna_ask` re-based onto it with all gates.
  Confirm DD-22's merge from the fetched tip first (both touch `commitBlock()`); write the
  **DD-24 gap enumeration before extracting** — every known web-door gap marked
  `propagated-knowingly` or `fixed-first`. That document is P3-D's input.
- **Limits enablement** (§0 ruling 3, unconditional): DEPLOY WARDEN sets
  `PARIPRASHNA_LIMITS_ENABLED` via Cloud Run env under the canary discipline. VERIFIER
  confirms normal turns still succeed post-enable. §6.4's reject demo follows, non-gating.

**Wave P3-3 — on P3-B's close:**
- **P3-D** — door parity. **Precondition first:** the wire↔persisted byte-agreement test
  on the web door exists and is green before the lane opens. Parity hashes the persisted
  receipt object; the assertion is bounded to the Wave-2 gap enumeration (DD-24). Three
  refuters on the parity claim.

**Wave P3-4 — THE FLIP (P3-F), auto-executing per §0 ruling 2, when ALL of:**
1. P3-A/B/C/D/E closed with DD-21 artifacts;
2. green×7 complete on the cadence (CI history is the declarer, no agent's word);
3. limits enabled and verified live;
4. REFUTER panel (three, independent) fails to refute flip readiness;
5. lease re-read clean at the moment of the flip merge;
6. rollback pin committed BEFORE the flip commit — the un-flip is a ready traffic/env
   command, tested in syntax, before the flip happens.

Then: flip → post-flip smoke (demonstrated-can-fail battery against the live default
route) → **both doors probed live post-flip** → tag `pariprashna/p3-close` → **the DD-1
feel-proxy battery (§10.1) runs immediately** → P4 retirement gate evaluation.

If morning arrives mid-hold: end state 4. Do not compress the cadence to beat the
sunrise — seven greens at a real cadence is the point.

---

## §5 — Git, merge, and deploy discipline (production ≡ main, all night)

### 5.1 Commits
Small, real commits at every coherent point inside each worktree — never one monolith at
lane end, never a WIP dump. Conventional format (`feat(pariprashna/p3-a): …` ·
`feat(pariprashna/p4-e): …` · `fix:` · `docs:` · `test:` · **`revert:` reserved for the
pre-authorized retirement rollback**). **`git stash` is banned** (X-5) — a WIP commit on
the lane branch is the parking mechanism. Push each lane branch to origin at every
commit — an unpushed overnight branch is work that a crash erases.

### 5.2 Trains (the only path to main)
INTEGRATOR batches admissible lanes (verifier PASS + refuters cleared + judges cleared
where voice is in scope + impacted-suite CI green) → one full-CI run per batch → red =
bisect by halving, park the offender with a written finding, rerun → green → rebase onto
freshly-fetched `origin/main` → **lease re-read** → merge queue. Trains run as batches
fill — a lane verified at 1am is on main by 2am. Tonight there are up to three concurrent
train identities with disjoint scopes: **T-P3** (engine/door work), **T-P4-REMEMBER**
(Paripraśna tree accrual), **T-P4-RETIRE** (legacy tree — strictly serial A→B→C→D, opens
only post-gate). Schema changes ride T-SCHEMA before any app train; **expand-only
migrations tonight**. Migration numbers reserved in `campaign-coordination` before
authoring; every migration verified actually applied (§N.4).

### 5.3 Deploys (every merge, including docs-only — DD-27)
Every `main` merge triggers `Build & Deploy Web` — including pure-docs PRs, which deploy
whatever sits on `main` at that moment, possibly Pariśeṣa's. So EVERY merge gets the full
treatment: check what is on `main` → announce the revision tag in `campaign-coordination`
(X-6) → tagged revision at 0% → smoke against the tagged URL → 100% → post-shift smoke →
any red = **automatic traffic rollback** + DIAGNOSTICIAN. DEPLOY WARDEN confirms after
every shift: serving revision == the revision just verified. Production drifting from
main overnight is a STOP condition, not a note.

### 5.4 GitHub state at morning
Every merged branch deleted; every parked branch pushed with its finding linked in the
ledger; no orphan worktrees (`git worktree list` shows only the shared checkout + any
parked lane explicitly named in the report); local `main` untouched (X-7 — the shared
checkout stays exactly as found, detached HEAD and all).

---

## §6 — Verification standard (both phases, uniformly)

1. **DD-21, uniformly.** Every close carries a probe transcript, a live browser
   observation, or a DB read. Merged+green+flagged+tested remains insufficient, tonight
   like every night. P4 specifics: P4-A closes on an *observed* 308 (browser) and an
   *observed* 410+pointer (API probe), not on route-table inspection; P4-H closes on a
   dispute submitted end-to-end and read back from the DB; P4-I closes on a digest row in
   the journal table, not a log line; P4-E closes on a live turn where recall provably
   composed AFTER the independent reading (ordering evidenced from the trace, §10.5).
2. **§N.8 on every new signal.** Anything built tonight that reports a status must be
   demonstrated capable of reporting failure first. P3-E's smoke shown red before its
   first counted green; P3-D's parity suite fed a deliberately mismatched receipt; **the
   DD-1 feel-proxy battery fed a deliberately register-broken reading and observed to
   fail it** before its first real pass counts (§10.1); P4-A's redirect assertions shown
   red against a deliberately unredirected route first.
3. **Refuters default to refuted.** A close claim survives only if the refuter, trying to
   break it, cannot. Three independent refuters on the three highest-stakes claims:
   P3-D parity, P3-F readiness, **P4-B deletion warrant**.
4. **The ceiling reject demo (non-gating, per §0 ruling 3).** After limits enable: drive a
   synthetic user past $2/turn (or $40/day) on a tagged 0%-traffic revision via the probe
   harness — synthetic chart only — observe the refusal, then observe a normal turn
   succeeding after it. Note DD-26 honestly in the result: >200K-token inputs remain
   under-priced until it lands.

---

## §7 — Halt policy, self-healing, and the close

- **Auto-triage before any halt** (RF-8): DIAGNOSTICIAN gets ONE bounded attempt. Halt
  only if it fails. Never hang, never retry-loop.
- **STOP conditions (halt the run, clean):** unresolvable lease conflict on the critical
  path; production≡main broken and not restored by one rollback; combined ledger ≥ $400;
  the tracker dead and unrestorable; post-flip smoke red after auto-rollback (rollback,
  then halt — do not retry the flip tonight); **post-retirement build/deploy red after the
  pre-authorized revert+redeploy (execute the revert, confirm production stable, then
  halt — do not retry the deletion tonight)**; any situation where continuing requires a
  MUST-PARK decision from §3.3.
- **PARK-not-STOP conditions (the run continues):** DD-1 battery red (park retirement,
  continue remembering + fillers, battery findings to the ledger); a single P4 filler
  lane stuck (park it, queue refills); one phase's budget subtotal exhausted (park that
  phase's remaining lanes, continue the other's within its own subtotal).
- **Every halt ends with:** rollback pinned · resume state written (what was mid-flight,
  exact next command per lane) · leases released or explicitly handed to the resume
  state · worktrees committed-and-pushed or removed · morning report finalized with the
  halt as its lead item.
- **Governance close (end of run, any end state):** batched registry write in ONE
  serialized step under an announced lease (X-2 — live version numbers read at write
  time, never predicted). DD register updated with what actually happened: the $400
  combined ruling, the seam-compression record (§0 ruling 11), DD-19's close, the
  reject-demo result, the DD-1 battery result, the deletion warrant and its refuter
  panel, every surrogate park, every lane's honest state. Tags per end state
  (`pariprashna/p3-close` and/or `pariprashna/p4-close` only for closes that actually
  happened; `p4-partial-<date>` markers in resume state otherwise). Missing
  lease-closing entries: write them.

---

## §8 — The morning report

Assembled incrementally by the SCRIBE all night at
`00_ARCHITECTURE/briefs/pariprashna_swarm/OVERNIGHT_RUN_REPORT_2026-08-22.md`, committed
with the close. Leads with the end state (§1's six), then: lanes closed per phase with
DD-21 evidence links · **the surrogate's decision ledger in full** (the first thing the
native should read) · the seam-compression record and the DD-1 battery result with its
demonstrated-can-fail evidence · the deletion record (census hash, warrant, refuter
verdicts, the revert command that was pinned) or the honest reason retirement parked ·
every park with its finding · the flip record with the exact serving revision · spend vs
$400 with both subtotals · anomalies the tracker flagged · new DD entries filed · the
three things most worth the native's attention today. Honest lengths: a quiet success is
short; a halt is thorough.

If the flip executed, the report says so in its first line. If the deletion executed, the
report says so in its second line, with the exact commit hash and the one-command revert.
The native should not have to hunt for whether their instrument changed underneath them
overnight — and tonight it may have changed twice.

---

## §9 — Hard-nevers (bind every agent, surrogate included, all night)

- Never write `CLAUDECODE_BRIEF.md` (X-3). Never operate in the shared checkout (X-4).
  Never `git stash` (X-5). Never bare `git status` in the main checkout —
  `--no-optional-locks` always.
- Never touch another campaign's files, worktrees, or dirty state — park instead. Never
  merge without the lease re-read that immediately precedes THAT merge (X-1).
- Never hand-set lane/phase status — `tracker_emit.py` claims, observatory derives.
- Never disable, weaken, or route around a safety gate, register lint, voice lint, or
  mortality scan to make a lane pass. The safety surfaces are the product.
- Never touch the native's real chart (`482012f1-…`) — probes use the synthetic chart
  only. Never provision a plaintext provider key into a worktree.
- Never destructive migrations, credential operations, or budget self-raises.
- **Never delete outside the census.** P4-B's diff may contain no path absent from the
  refreshed census's condemned list — one extra path fails the warrant, whole train
  parks. Never delete with a census older than the fetch that precedes the deletion PR.
  Never let the residue sweep (P4-C) grow into a refactor — residue is what grep finds,
  nothing more.
- Never present machine grading (P4-D) or machine judging (P4-F/G panels) as the
  native's judgment — label every such artifact machine-graded.
- Never a claim without a detector that could have called it false. Never a close without
  its artifact. Never a decision without its ledger entry. **The register is long because
  nothing was allowed to disappear. Tonight of all nights — keep it that way.**

---

## §10 — THE P4 PROGRAM (the elevation)

### 10.1 The gate: the DD-1 feel-proxy battery, and what it is not

P4's retirement train opens on **P3-F closed AND the DD-1 automated feel-proxy battery
passing** — never on AC-15. The battery is the automated proxy for "does the default
surface feel right": register/voice lint across a probe set of real readings on the
synthetic chart, leakage scan (no internal taxonomy reaching the reader), latency and
first-paint thresholds, citation integrity, and the §J plainness checks — run against the
**post-flip live default surface**, not a fixture. Per §N.8 it must be demonstrated
capable of failing: feed it one deliberately register-broken reading and observe the
battery fail it BEFORE its first real pass counts. Battery red = retirement parks
(PARK-not-STOP), remembering continues.

**What P4 is not, recorded so no agent re-litigates it at 3am:** AC-15 is never "passed"
— it is the native's own week of use, recorded only as waived-as-blocking with the
verdict welcome asynchronously. `PARIPRASHNA_LIMITS_ENABLED` is not revisited — resolved
in P3, Wave 2. The battery substitutes for the seam TONIGHT ONLY by §0 ruling 11, and the
record says so.

### 10.2 The lanes, with tonight's dependency truth

From `tracker/PLAN.yaml` (verify from the fetched tip at run open — the graph below is
what was true at authoring):

| Lane | Depends on | Train | Work |
|---|---|---|---|
| **P4-A** | P3-F | RETIRE | `consult`/`consume` retired: 308 redirects (browser), 410 + pointer (API callers), per the inbound inventory |
| **P4-B** | P4-A | RETIRE | Dead-tree deletion per the **refreshed** census, leaf-first, W-2 line-by-line verifier review of the deletion diff |
| **P4-C** | P4-B | RETIRE | `PARIPRASHNA_ENABLED` deletion (grep = 0) + residue sweep (`audience_tier` type/schema vestiges, the second error classifier) |
| **P4-D** | P4-C | RETIRE | Q-2 graded readings (three, machine-graded per DD-8 against the §J rubric) + docs seal: design plan → RATIFIED-AS-BUILT, Baseline regenerated |
| **P4-E** | P3-F | REMEMBER | Recall wired, **independent-then-compare**: the current reading composes before prior conclusions are retrieved |
| **P4-F** | P3-F | REMEMBER | The arrival line, composed from L1/Kāla truth — never model-composed prose |
| **P4-G** | P2-A ✓, P1-B ✓ | FILLER | The window-opening ask — proactive prompts tied to open prediction windows; the highest-leverage unbuilt feature |
| **P4-H** | — | FILLER | Dispute capture + feedback endpoint restored (currently discards silently) |
| **P4-I** | — | FILLER | Digest transport wired to a real DB journal, not logs |
| **P4-J** | P2-I ✓ | FILLER | Signal reader text, top-cited-first, generate-review-freeze; embarrassingly parallel — soaks idle capacity all night |
| **P4-K** | — | FILLER(build) / post-flip(run) | The post-six-views narration audit: build the audit harness early; execute against the live default surface post-flip |

**Five of eleven lanes are runnable from minute one.** That is the anti-idle design: G,
H, I, J, and K's harness open in Wave P3-1 alongside P3's own first wave, and the queue
never empties while the smoke hold ticks.

### 10.3 The deletion protocol (P4-B/C — the second least-reversible act of the night)

The DD-4 pre-authorization fires only when ALL THREE are simultaneously true, verified at
the moment of the retirement commit, not earlier in the evening:

1. **A verifier's line-by-line deletion-diff review passes against a census refreshed
   AFTER P4-A's redirects landed** — the census is re-derived from the live post-redirect
   `main` (imports, routes, dynamic references, the inbound inventory), hashed, and the
   diff is checked path-by-path against it. The census must also confirm no
   PARIŚEṢA-RĀTRI file imports from the condemned tree — a single cross-campaign import
   parks the train with a finding rather than deleting under another campaign's feet.
2. **Seven consecutive green smokes are already banked (W-1)** — post-flip smokes on the
   45-minute cadence count; the counter must read ≥7 consecutive at commit time, any
   intervening red resets it for this purpose too.
3. **A rollback pin is committed BEFORE the retirement commit** — the exact
   `git revert <hash>` + rollback-pin redeploy command, syntax-tested, sitting in the
   ledger before the deletion lands.

Then: leaf-first deletion in one reviewed PR per DD-4's scope · **three refuters on the
deletion warrant** (can any deleted path still be reached? does any test, migration, or
cron reference it? does the build prove zero orphaned importers?) · merge on T-P4-RETIRE
· full canary deploy · post-deploy smoke · **then and only then** P4-C deletes the flag
(grep = 0 proven in CI, residue sweep bounded to grep findings) · P4-D seals the docs.
Gate to call retirement closed (from the phased plan, verbatim intent): zero orphaned
importers (build + grep proof) · redirect assertions green · `PARIPRASHNA_ENABLED`
absent · every prior phase's integrity assertion re-run green on the deployed default
artifact.

### 10.4 The two trains, and why they never collide

RETIRE touches only the legacy tree (`platform/src/app/**` legacy routes, the condemned
paths); REMEMBER and the fillers touch only the Paripraśna tree
(`platform/src/lib/pariprashna/**` and its surfaces). Disjoint scopes, separate trains,
separate leases — announce them separately in `campaign-coordination` so Pariśeṣa's
conductor sees two narrow scopes rather than one broad one. Within RETIRE, **A→B→C→D is
strictly serial** — redirects before deletions before deflagging before sealing; no
overlap, no pipelining, each lane's close artifact filed before the next opens.

### 10.5 The remembering standard (what "wired" means tonight)

- **P4-E (recall):** the anti-anchoring rule is structural, not promissory — the trace of
  a live turn must show the current reading fully composed before any prior-conclusion
  retrieval executed. The refuter's recall-firewall lens attacks exactly this ordering.
  Close on a live probe turn whose trace proves it, plus a returning-thread turn where
  recall demonstrably surfaced a prior conclusion *as comparison, not as anchor*.
- **P4-F (arrival line):** composed from L1/Kāla facts by deterministic assembly — never
  model-generated prose. Verifier proves it by construction (the assembly path) AND by
  observation (a live arrival line traced to its source facts). Three-judge voice panel
  on register. The phased plan's acceptance echo: *a returning thread greets with where
  the daśā stands.*
- **P4-G (window-opening ask):** proactive prompt fires only against a genuinely open
  prediction window (DB-verified), reaches the conversation surface, and its
  answer reaches the ledger — the phased plan's acceptance echo: *a closed window gets
  asked about in conversation and the answer reaches the ledger.* Three-judge voice
  panel; dispute non-folding lens on the capture path.
- **P4-H (disputes):** end-to-end — submit a dispute through the restored endpoint on the
  live surface, read it back from the DB, prove the silent-discard path is gone by
  demonstrating what USED to happen (§N.8: the old behavior is the can-fail baseline).
- **P4-I (digest journal):** a real digest row written and read back; log-only transport
  demonstrably retired.
- **P4-J (reader text):** generate top-cited-first → review (voice lint + citation gate)
  → freeze; frozen artifact hashed and recorded. Parallelize generation freely; the
  freeze is a single serialized step.
- **P4-K (narration audit):** harness built early (filler), executed post-flip against
  the live default surface across six-view sequences; findings filed as DD entries or
  in-lane fixes per the surrogate's in-lane/new-DD call.

### 10.6 The P4 timeline inside the night

- **T0 (run open):** Wave P3-1 opens (P3-E, P3-A, P3-C, DD-19) **plus** P4 fillers G, H,
  I, J, K-harness. Queue depth ≥ 9 lanes from the first hour.
- **While the smoke hold ticks (the 4.5–5.25h window):** fillers build, verify, refute,
  and ride T-P4-REMEMBER trains to main under the standard canary discipline. Each
  filler merge's deploy also keeps proving the deploy pipeline the flip will use.
- **On P3-F + battery green:** RETIRE train opens (P4-A). REMEMBER train opens P4-E and
  P4-F in parallel. P4-K's audit executes.
- **RETIRE runs serial to its seal (P4-D)**, REMEMBER drains in parallel; governance
  close batches once both trains are drained or parked.
- **If the flip is still holding at dawn:** end state 4 — fillers will have landed
  regardless; retirement waits for the gate it was always going to wait for.

---

## §11 — TMUX OPERATIONS ANNEX (how this run physically survives the night)

The companion runbook (`OVERNIGHT_TMUX_RUNBOOK_v1_0.md` + `overnight_p3p4.sh`) launches
this charter inside a tmux session on the native's machine. What the conductor must know
about its own container:

### 11.1 The session shape

tmux session **`prp-night`**, four windows: **`conductor`** (this Claude Code session,
wrapped in `caffeinate` so the Mac cannot sleep) · **`sentinel`** (the anti-idle loop) ·
**`pulse`** (30-min external health probes: fetch, CI runs, prod HTTP, disk) ·
**`logs`** (live tails of the decision ledger and morning report). The native attaches
with `tmux attach -t prp-night` in the morning; detaching never stops anything.

### 11.2 The anti-idle contract ("the system doesn't sleep")

The sentinel captures the conductor pane every 5 minutes and hashes the tail. Three
consecutive identical hashes (≈15 min of visible stillness) = a **NUDGE** is typed into
the conductor session: `WATCHDOG NUDGE <n> — report end-state ranking, queue depth,
smoke-counter state, budget subtotals; then resume the queue. If blocked, route the
blocker to the NATIVE-SURROGATE now.` If the pane is dead (crash, exit), the sentinel
respawns Claude Code with `--continue` so the session resumes its own transcript, then
re-issues the boot line. The sentinel never makes decisions — it only restores motion.

### 11.3 The conductor's reciprocal duties

- **Answer every nudge** with one status line, then act — a nudge answered with silence
  is a stall by definition and escalates to DIAGNOSTICIAN on the next cycle.
- **Never end a turn with only background work pending and nothing queued** — the
  PRATIJÑĀ stall pattern. While any wall-clock hold runs, the conductor's turn always
  ends having dispatched or checked something with a bounded return time.
- **Long waits are scheduled, not slept:** between smoke-cadence events, process the
  queue; if the queue is truly empty and all agents are mid-flight, run the WATCHDOG
  checklist early rather than idling.
- **Crash recovery is a first-class path:** on `--continue` resume, first action is
  re-orientation — `git fetch origin`, re-read the lease log tail, re-read the tracker
  state, reconcile the budget ledger against actual API spend, verify production
  revision — then resume the queue from derived state, never from memory.

### 11.4 What the pulse window is for

The pulse log is the native's independent, agent-free record of the night: every 30 min
it timestamps `origin/main` HEAD, the last 5 CI runs, production's HTTP status and
serving revision, and disk headroom. If the morning report and the pulse log disagree,
the pulse log wins and the discrepancy files as a finding. No agent writes to it.

---

*End PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN v2.0. Two phases, one night, zero idle
hours, everything written down. Good night; build well; delete carefully; remember
honestly.*
