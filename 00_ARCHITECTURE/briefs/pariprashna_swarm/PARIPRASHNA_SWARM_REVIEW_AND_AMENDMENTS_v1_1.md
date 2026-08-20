---
artifact: PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1
canonical_id: PARIPRASHNA_SWARM_PLAN_AMENDMENTS
version: 1.1
status: CURRENT-FOR-EXECUTION — Fable-5 adversarial review of the v1.0 swarm plan;
  its amendments BIND the execution. Where this file and the v1.0 plan disagree,
  this file wins.
produced_during: PARIPRASHNA-SWARM-REVIEW (Cowork, Fable 5, 2026-08-19)
date: 2026-08-19
authoritative_side: claude
role: >
  (1) Review findings RF-1..RF-12 — gaps and challenged assumptions that would have
  become roadblocks or velocity sinks, each with its binding fix. (2) The Delegated
  Decision register DD-1..DD-10 — every human gate closed by native delegation
  (this conversation, 2026-08-19), so the build runs with zero human gates.
  (3) The merge/deploy train protocol. (4) The swarm scaling policy. (5) The
  live tracker specification. (6) Amended phase structure (P0 IGNITION added).
relates_to:
  - PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md (amended by this file)
  - PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md (lane inventory)
  - 00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md (the PPR requirements)
changelog:
  - "1.1 (2026-08-19): full adversarial review; P0 IGNITION added; all human gates
    closed via DD register under explicit native delegation."
---

# Swarm Plan — Fable-5 Review & Binding Amendments

## §1 — Review findings (assumptions challenged, gaps closed)

### RF-1 · CRITICAL · The file-disjointness assumption is FALSE at the plan's center
v1.0 assumed the collision map would yield mostly independent lanes. It will not:
**`app/api/pariprashna/route.ts` is 1,179 lines and is touched by at least six
lanes** across P1/P2 (safety gate, injection scan, block typing, S-3 wiring,
honest controls, receipt assembly). The collision map would serialize the heart
of the build behind one file — the single largest hidden velocity sink in v1.0.
**FIX (binding): P0 IGNITION includes a PORTS REFACTOR** — decompose route.ts
into the §6.2 typed-port stage modules (`safety_gate.ts` · `plan_stage.ts` ·
`evidence_stage.ts` · `synthesis_stage.ts` · `validation_stage.ts` ·
`reading_parts.ts` · `receipt_stage.ts` · `persistence_stage.ts`, thin route
shell composing them), proven behavior-identical by a golden-stream semantic-
equality harness over the 12-fixture corpus + captured real streams BEFORE any
phase lane opens. After P0, each later lane owns its own stage file and the
six-way collision dissolves. This is the single biggest velocity unlock
available and it must come first.

### RF-2 · HIGH · Migration-number collisions between parallel lanes
Multiple lanes author migrations concurrently → sequence-number collisions and
nondeterministic apply order. **FIX: conductor-owned migration allocator** —
numbers reserved centrally at lane-brief time; **expand/contract discipline**:
mid-phase migrations are additive-only (new tables/columns/roles), destructive
changes cluster at phase close; the schema train always merges and deploys
before the app train.

### RF-3 · HIGH · Micro-collisions on shared files beyond route.ts
Barrels/`index.ts`, shared `types.ts`, `feature_flags.ts`, `package.json`/
lockfile, and `protocol/events.ts` will be touched by many lanes. **FIX:
ownership rules** — protocol/event changes are ONE designated lane per phase
(additions batched, event schema versioned once); barrel and lockfile edits are
integrator-only; lanes add new files in preference to editing shared ones;
`feature_flags.ts` additions go through a conductor-reserved flag registry.

### RF-4 · HIGH · The real merge bottleneck is CI wall-time, not agent count
Ten lanes × full CI serially consumes the day. **FIX:** the train protocol
(§3): batched speculative merges with ONE full-CI run per batch and bisect-on-
red; lane-level CI runs impacted suites only; the full battery runs at train
and gate level.

### RF-5 · MED · Test-database contention between parallel builders
Concurrent DB-integration suites against one dev DB corrupt each other's state.
**FIX:** per-lane database clones from a template DB (`CREATE DATABASE lane_x
TEMPLATE …`), allocated/dropped by the conductor; DB-heavy suites tagged and
also run once at train level against the shared instance.

### RF-6 · MED · Static 1:1 role allocation starves the pool
Verification (live probes) is slower than building; late-phase, builders idle
while verifiers queue. **FIX: roles are hats, not headcounts** — one
oversubscribed work-stealing queue; any free agent slot takes the next task of
any role, priority order: unblock-merge > verify > build > refute > scout-next-
phase. This is also the direct answer to "agent availability must never
throttle velocity": **the queue, not the pool, is the constraint** (§4).

### RF-7 · MED · Main is moving underneath the phases
The log shows active concurrent work landing on main (EKAVĀKYATĀ, night-tick
BOARD refreshes, engine fixes). Long-lived integration branches will drift.
**FIX:** integration branch rebases onto origin/main at every train close; a
**conflict-forecast task** (cheap, recurring) diffs incoming main deltas
against the collision map and re-orders the queue when a collision approaches;
phase lease registered in CAMPAIGN_COORDINATION.

### RF-8 · MED · A night-time halt wastes the run
v1.0 halts cleanly but immediately. **FIX: auto-triage tier** — before any
halt, a diagnostician agent gets ONE bounded remediation attempt (flaky-suite
rerun · bisect-and-park the offending lane · revert the last train batch).
Halt only after that fails; halts always end the phase with pinned rollback +
resume state + report. Never hang, never retry-loop.

### RF-9 · LOW · TDD-everything taxes trivial lanes
**FIX: three verification tiers** — integrity lanes: TDD + adversaries;
behavior lanes: tests-with-code + verifier; content/fixture lanes (lexicon,
reader text, docs): verifier review only.

### RF-10 · MED · The gate battery is a barrier that idles the whole pool
**FIX: prefetch** — during FREEZE-1 and the gate run, the pool executes the
NEXT phase's scouting and lane-brief drafting (read-only, zero risk). No idle
slots anywhere in the run.

### RF-11 · Assumption "deploy per wave is safe" — refined, not accepted
Continuous flag-OFF deploys stand. **Added canary discipline:** every deploy
creates a tagged Cloud Run revision at 0% traffic → smoke battery against the
tagged URL (demonstrated-can-fail) → traffic shift to 100% → post-shift smoke
→ any red = automatic traffic shift back + auto-triage. Rollback is a traffic
command, not a build.

### RF-12 · Assumption "the operator packet must be human" — DISPROVEN
PG-1 ran live `gcloud sql instances describe` from a session: the machine has
authenticated gcloud. PITR enable, scratch-instance creation, restore drill,
and credential rotation are all automatable via gcloud/psql under existing
IAM. The one genuinely non-automatable item (a secret nobody possesses) is
closed by decision DD-2. Residual risk is IAM refusal on a specific call —
handled per DD-3 (park that lane, never block the phase).

## §2 — The Delegated Decision register (all human gates CLOSED)

Authority: explicit native delegation, this conversation, 2026-08-19 — "take
the decisions on my behalf and close all human gates." Each DD is a native
decision made through that delegation, recorded here as the ADR; the swarm
treats them as ruled. DD-1 and DD-3 supersede prior sequencing rulings and are
flagged for the Decision Register at next docs close.

| # | Gate closed | Decision |
|---|---|---|
| **DD-1** | **AC-15 / W-4 (the week-of-use verdict)** | Converted from a BLOCKING gate to an ASYNC signal. P3→P4 proceeds when the automated feel-proxy battery passes — the design plan's own machine metrics at their stated targets (M1 CLS=0 above the tail · M2 caret orphaning 0 · M3 <300ms first signal · M5 internal-ID leakage 0 · M6 chip transmutation 0 · M8 mobile 100% · M9 axe clean) plus the edge-state fixture suite. **W-4's soul is preserved: the swarm never records an AC-15 PASS** — it records "waived-as-blocking by native directive 2026-08-19; native verdict welcome asynchronously." A negative verdict at any time spawns a remediation wave against the then-current phase. |
| **DD-2** | ANTHROPIC_API_KEY provisioning | **Delist the anthropic stack** from pickers and config (it has failed-instantly-but-masked since 2026-08-01 anyway; production default is Gemini). Re-enlisting later = one config change + the qualification suite. No secret required from anyone. |
| **DD-3** | Console/infra operator packet (PITR enable, scratch instance, restore drill, `amjis_app` rotation) | **Automated via gcloud/psql under existing IAM.** If IAM refuses a specific call, THAT LANE parks with the exact failing command in the report and the phase CONTINUES; the gate records the park honestly (downgraded from phase-blocking to lane-parking for the IAM-refused subset only). |
| **DD-4** | The irreversible retirement commit + flag deletion (P4) | **Pre-authorized**, contingent on: verifier line-by-line deletion-diff PASS against the refreshed census (W-2 intact) + seven consecutive green smokes already recorded (W-1 intact) + rollback pin committed before the retirement commit. |
| **DD-5** | Build-run spend | Per-phase build budgets: P0 $40 · P1 $150 · P2 $200 · P3 $80 · P4 $150 · P5 $80 (API-cost equivalent). Ceiling hit = clean halt at the next lane boundary with resume state. (Runtime app caps stay $2/turn · $40/day per NCD-8 — unrelated to build spend.) |
| **DD-6** | Taste calls (the Seal, typography, arrival-line voice, empty-state) | **Judge-panel majority decides**; the native may dispute any post-hoc as a remediation item. No mid-phase design review. |
| **DD-7** | The seven-smoke hold (P3) | Autonomous wall-clock wait; the conductor sleeps between smoke runs; any red resets the counter (W-1 intact); green×7 declared by the CI history, no human. |
| **DD-8** | Q-2 reading grading + docs seal (P4) | Gate-runner grades the three readings against the §J rubric, honestly labeled MACHINE-GRADED; the design-plan RATIFIED-AS-BUILT flip proceeds on it. |
| **DD-9** | G0 PR merge | Pre-authorized: kickoff step 0 opens and merges the `pariprashna/g0-close` PR (doc-only diff) if not already merged, before anything else. |
| **DD-10** | CAMPAIGN_COORDINATION dirty-file conflict | Never touch another workstream's dirty file: register the phase lease the moment the file is clean; until then log the deferral each phase (the G0 precedent). |
| **DD-11** | Dead observatory during a lane transition (added 2026-08-20, PARIPRASHNA-CLOSEOUT session, item 2; status corrected 2026-08-20, same session, item 2 follow-up; deadline consolidated into DD-12, 2026-08-20, PARIPRASHNA-CLOSEOUT-FINAL session, item 1) | **Status: IN FORCE — NOT YET WIRED.** The rule: the conductor calls `tracker-health-check` (`00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/tracker-health-check`) at every lane transition; a non-zero exit is a HALT condition, same shape as every other DD-5-style halt (halt at the next lane boundary, pin rollback, write resume state, restore the observatory, report, then resume). **Nothing calls it mechanically yet** — a P2 lane-transition entry on `origin/campaign-coordination` (2026-08-20, the presentation-truth wave) records one manual, read-only invocation (`OBSERVATORY HEALTHY`) and a commitment to keep invoking it by hand for the rest of P2, which is real signal but still agent-remembered, not structural. This is the tier that actually closes the loop the tracker-v2 observatory (§7) built: T1–T4 keep the *observer* alive, but every one of them is itself something that can be down; the subject (the conductor) checking the observer is the only watcher guaranteed to be running at the exact moment it matters. The 2026-08-19 23m37s blind window (tracker-v2 README, "The 2026-08-19 incident") would have been caught in seconds by this, had it existed then. **Deadline and resolution: see DD-12** — the structural finding DD-11's own investigation surfaced, and the single P2-close decision point that now governs both rows; DD-11 no longer carries its own separate deadline clause. |
| **DD-12** | Structural finding: per-lane discipline in this campaign is agent-remembered, not mechanized (added 2026-08-20, PARIPRASHNA-CLOSEOUT-FINAL session, item 1 — arising directly from the DD-11 investigation) | **Finding:** lane transitions in this campaign are **prose-only**. There is no deterministic per-lane hook anywhere in the swarm plan or its tooling — not for tracker event emission, not for `tracker-health-check` (DD-11), not for `may_touch` territory/lease enforcement, not for budget accounting against the DD-5 per-phase ceilings. Every one of those depends on an agent remembering to perform it at each transition, not on a mechanism that runs regardless of whether anyone remembers. **This is the narrated-versus-derived problem one layer up**: the tracker-v2 observatory (§7) was rebuilt specifically to DERIVE its state from git/`gh`/filesystem ground truth rather than trust agent self-report (CLAUDE.md §N.8) — but the *emission points feeding that observatory* are still sentences in a kickoff prompt, not code. The observatory's completeness is therefore bounded by agent diligence at exactly the boundary where the 2026-08-19 23m37s blind window occurred: a bare `launchctl bootout` run outside any tracked mechanism. **Proposed shape:** a single `lane(...)` wrapper every transition is invoked through — called at a lane's start and at its close — which performs tracker event emission, a `tracker-health-check` invocation (halt on non-zero, per DD-11), a `may_touch` scope assertion, and budget-ceiling recording, all as **side effects of being called**, not as separate steps an agent has to remember on top of doing the actual work. Once this hook exists, **DD-11 wires itself**: halt-on-non-zero becomes a property of the wrapper, not a discipline layered on top of it. **Deadline: P2 CLOSE** — the same boundary DD-11 already carried; this entry is now the one decision point for both rows. **Binary outcome, both branches acceptable:** (a) the `lane` wrapper is built and adopted before P2 closes → DD-11's status moves to **WIRED**; or (b) it is not → DD-11 is downgraded to **ADVISORY**, with a written acknowledgement (this entry, updated in place) that per-lane discipline in this campaign is agent-remembered, not mechanically enforced, and stays that way until a future phase revisits it. **A third pass that leaves DD-11 at NOT YET WIRED with a freshly pushed-out deadline is explicitly not an acceptable outcome at P2 close** — the choice must be made, not deferred again. |
| **DD-13** | Fast-follow: two disclosed residuals in the mortality phrasing-scan gate, accepted-as-scoped at go-live (added 2026-08-20, PARIPRASHNA-GOLIVE-EXECUTE session, item 1 — native ruling on 2e: `PARIPRASHNA_SAFETY_GATE_ENABLED` → ON now, both residuals accepted as scoped, with this ticket as the mandatory fast-follow) | **Status: OWNED — UNDATED. Deadline requested from native, not invented here.** Both residuals are stated in `platform/src/lib/pariprashna/safety/phrasing_scan.ts`'s own module header, not newly discovered: **(a) the third-sentence pairing gap** — the mortality-term/date cross-sentence scan (`CROSS_SENTENCE_WINDOW = 2`) only pairs a term and a date within two sentences of each other; a pair separated by an intervening third sentence is, in the module's own words, "a KNOWN residual, not a covered case," and is not detected. **Scope of fix:** widen `CROSS_SENTENCE_WINDOW` past two sentences, or add an independent same-sentence-count scan that doesn't share the two-sentence assumption — whichever closes the gap without regressing the existing round-3 (M-3/H-4) boundary-sweep tests (`phrasing_scan_round3.test.ts`), which fail if either constant shrinks. **(b) the streaming un-send asymmetry** — nothing can retract a token already streamed to the reader; if a mortality term is emitted before its paired date arrives, the gate can withhold the date but not the already-sent term. The module's own framing: this is a real reduction ("a reader may see a mortality term whose date is then withheld") not an elimination ("a reader may see a complete mortality claim"), and is written down as such rather than rounded up. **Scope of fix:** evaluate a short pre-display buffer for mortality-adjacent spans specifically (hold suspect prose back one span-width before emitting it, mirroring how `StreamingMortalityScanner` already holds prose back to the last sentence boundary for HS-1), weighed explicitly against the P2 first-paint-citation guarantee (`PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED`) — **do not silently regress that guarantee to close this gap**; if the two are in real tension, that tension is itself part of what this ticket needs to report back, not something to resolve unilaterally. No deadline is set by this entry — ask the native for one, the same way DD-11's deadline was handled via DD-12 rather than invented by the session that found the gap. |

**Effective at the next phase boundary (P1 close), not mid-phase — landed,
but landing is not the same as wired.** DD-11 was written as a new standing
rule, not a hotfix to something broken right now — the P1 conductor was
mid-phase when it was authored, and inserting a new mandatory
per-lane-transition call into a running phase would have risked exactly the
kind of disruption DD-11 exists to prevent (an interruption at an unplanned
moment). P1 finished under the rules it started under; P2 opened under
DD-11's *text*, but not its *enforcement* — investigated 2026-08-20 (same
session, item 2 follow-up): the live P2 conductor session was found running
from a worktree branched before this rule (or the script it calls) existed
on `main`, and there is no deterministic per-lane hook in this campaign for
any session to attach a check to short of editing the conductor's own
in-flight files, which risks the disruption this rule was written to avoid
in the first place. Editing prose a live session has already loaded into its
own context does not change what that session does — only a session that
starts fresh (or is deliberately resynced) after this text lands actually
picks it up. Landing the rule's *text* is not the same claim as landing its
*enforcement*, and the row above says so plainly rather than reading as
closed.

**2026-08-20 update (PARIPRASHNA-CLOSEOUT-FINAL, item 1):** that investigation's
root cause — no deterministic per-lane hook exists for *any* per-lane
discipline in this campaign, not just DD-11's — is now its own entry, DD-12,
immediately above. DD-11's deadline clause has been removed in favor of
DD-12's single P2-close decision point, so this file carries one obligation
here, not two.

**Result: zero human gates.** The only stops are halt conditions, and every
halt ends with rollback pinned, state resumable, and a report — never a hang.

## §3 — The merge & deploy train protocol (the "smart merge queue")

```
 lane branch ──verifier PASS + refuters clear + impacted-suite CI──▶ ADMISSIBLE
                                                                        │
   ┌────────────────────────────────────────────────────────────────────┘
   ▼
 TRAIN BATCHING (integrator): collect all currently-admissible lanes (≤5),
   order by conflict-prediction (shared-type/protocol touchers FIRST, leaf
   lanes last), speculative merge onto the integration branch
   │
   ├─ ONE full-CI run per batch
   │     red → BISECT by halving → park the offender (finding written) → rerun
   │     green ↓
   ├─ integration branch REBASES onto origin/main (RF-7), re-verify quick suite
   ├─ PR → main via merge queue  (only Paripraśna merges during FREEZE-3)
   ▼
 DEPLOY (canary): tagged Cloud Run revision @ 0% → tagged-URL smoke
   (demonstrated-can-fail) → 100% traffic → post-shift smoke
   red at any step → AUTO traffic-rollback → auto-triage → halt if unresolved
```

Two trains per phase, strictly ordered: **T-SCHEMA** (migrations + grants +
RLS; merges and deploys FIRST, expand-only mid-phase) then **T-APP**
(everything else, batched). Trains run repeatedly as batches fill — a lane
verified at hour 2 is on main by hour 3; nothing waits for the phase to end.
Gate batteries run under FREEZE-1 against the deployed artifact, per v1.0.

## §4 — Swarm scaling policy ("availability never throttles velocity")

- **One oversubscribed work-stealing queue; roles are hats** (RF-6). Every
  slot always holds the highest-priority available task.
- **Adaptive concurrency:** start N=10 concurrent worker sessions; every 15
  minutes, if p95 task latency and API error rate are under threshold, N+=2
  (cap 24 — beyond that, local CPU and provider rate limits invert the gain);
  on 429s or latency spikes, N−=4 immediately, recover gradually. The
  conductor logs N over time in the tracker so throttling is visible, not
  suspected.
- **Honest physics:** hundreds of agents per phase are QUEUED and PIPELINED;
  ~10–24 execute at any instant. Velocity comes from zero idle (work-stealing
  + prefetch + trains that ship hourly), not from pretending simultaneity.
- **Builder oversupply rule:** the lane queue is always ≥2× the concurrency
  cap deep (pulling forward next-wave lanes whose leases are already free),
  so no slot ever waits for work to be defined.

## §5 — The live tracker (real-time, never stale)

**Files** (in `00_ARCHITECTURE/briefs/pariprashna_swarm/state/`):
- `SWARM_TRACKER.json` — machine state: phase · wave · per-lane
  {id, role-stage: queued|building|verifying|refuting|admissible|merged|parked,
  worktree, branch, last_event_ts, verifier_verdict, refuter_votes} · trains
  {batch, ci_status, merged_sha} · deploys {revision, traffic, smoke} · gate
  results · budget {spent, ceiling} · concurrency N · **heartbeat_ts**.
- `tracker_data.js` — the same state as `window.TRACKER = {...}` (file://-safe).
- `tracker.html` — self-contained dark dashboard (no server needed: open the
  file, it includes tracker_data.js and reloads itself every 30s): phase strip,
  lane board grouped by stage, train/deploy timeline, budget bar, concurrency
  sparkline, and a **staleness banner that turns the header red if
  heartbeat_ts is older than 15 minutes** — a stale view announces itself.
- `TRACKER.md` — human digest, regenerated at wave boundaries.

**Update discipline (binding on the conductor):** write JSON+js on EVERY lane
state transition; heartbeat write every 10 minutes even when nothing changed;
commit tracker state to the phase branch every 30 minutes and at every train
close (visible remotely via GitHub as well as locally); final loud line +
tracker commit at phase close or halt.

## §6 — Amended phase structure

```
 P0 IGNITION (new)      env + ports refactor + tracker + G0 absorption
 P1 FOUNDATION          as v1.0, minus the operator packet (DD-3), 10 lanes
 P2 READING MADE TRUE   as v1.0, 15 lanes (now collision-free thanks to P0)
 P3 ONE ENGINE/DOOR     as v1.0 + DD-7 autonomous smoke hold + DD-1 feel-proxy battery
 (no human seam — DD-1) P4 proceeds on the proxy battery; native verdict async
 P4 OLD DIES/REMEMBERS  as v1.0 + DD-4 pre-authorized retirement + DD-8 machine-graded Q-2
 P5 EARNED CALIBRATION  as v1.0
```

**P0 IGNITION lanes** (small phase by count, foundation by nature):
P0-A merge G0 (DD-9) · P0-B environment (worktree farm, gh/gcloud auth checks,
cloud-sql-proxy, template test-DB, migration allocator, flag registry) ·
P0-C **ports refactor of route.ts** with the golden-stream equality harness
(RF-1 — the phase's centerpiece; verifier + 3 adversaries on the equality
claim) · P0-D tracker scaffold (§5) live from minute one · P0-E design-plan
grounding pass (docs) · P0-F DD-2 anthropic delist + DD-3 infra automation
probes (find IAM refusals NOW, not mid-P1). Gate: golden streams
byte/semantically identical through the decomposed route on the deployed
artifact; tracker live; every DD-3 command proven or parked.

## §7 — Addendum (2026-08-19, post-P0 close): §5's tracker superseded going forward

P0 (including P0-D, the tracker scaffold this §5 specified) closed before this
addendum was written — `origin/campaign-coordination @ 3bdcc752a`, PR #1349
merged as `9db457dcc`, all 5 P0 lanes (Step 0 + P0-B/C/D/E/F) closed, deploy
verified live. §5's tracker was built and merged exactly as specified:
`00_ARCHITECTURE/briefs/pariprashna_swarm/state/{SWARM_TRACKER.json,
tracker.html, tracker_data.js, TRACKER.md}`. So the standing instruction this
addendum's own kickoff brief carried — "P0-D reduces to wiring lane
transitions into tracker_emit.py" — no longer applies verbatim: there was no
still-open P0-D to redirect. What follows instead.

**The Paripraśna Execution Observatory (tracker-v2)** —
`00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/` (code, versioned) +
`~/.pariprashna-tracker/` (runtime state, outside the repo) — was built as a
**separate, standalone session**, retargeted at **P1 onward** rather than at
P0: derived-not-narrated lane state (git/`gh`/`gcloud`/filesystem ground
truth, never a self-report, per CLAUDE.md §N.8 applied to the instrument
itself), an out-of-process daemon (`trackerd.py`) with a three-tier dead-man's
switch (20s heartbeat · launchd watchdog restart on >90s staleness · client-
side staleness computed independently of the backend), append-only per-writer
event logs, a declarative `PLAN.yaml` carrying the real 53-lane inventory from
`PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md §2/§4` (not the
approximate "30 lanes" this kickoff brief itself cited), and a falsifiable
`--selftest` suite exercised against deliberately broken inputs before being
trusted (README + session report carry the full acceptance evidence,
including the observed-failing runs).

**§5 of this file is superseded going forward.** The P1+ conductor does not
build its own tracker: whatever spawns P1's lane agents wires one
`tracker_emit.py` call per lane-state transition (`kind: "lane_state"`,
`evidence_class: "CLAIMED"` for states with no artifact, e.g. `BUILDING`
before a branch exists — the observatory itself derives `MERGED`/`CLOSED`
independently from git/GitHub once a branch or PR exists, and flags an
`anomaly` if a claim and the derived evidence disagree). §5's file paths
(`state/SWARM_TRACKER.json` etc.) are retained in place as the historical P0
record, not deleted, not updated further.

*End addendum. §1–§6 above remain the historical record of the P0-era
review — unedited except for this pointer.*

*End SWARM_REVIEW_AND_AMENDMENTS v1.1 — this file binds execution; v1.0
remains the narrative plan of record beneath it.*
