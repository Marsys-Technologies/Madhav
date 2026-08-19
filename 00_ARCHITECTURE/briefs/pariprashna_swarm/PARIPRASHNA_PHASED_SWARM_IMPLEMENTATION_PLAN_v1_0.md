---
artifact: PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0
canonical_id: PARIPRASHNA_SWARM_IMPLEMENTATION_PLAN
version: 1.0
status: PROPOSAL — execution architecture for building the ratified v1.0 architecture; authorizes no code
produced_during: PARIPRASHNA-V012-PHASE1 follow-on (Cowork, Fable 5, 2026-08-19)
date: 2026-08-19
authoritative_side: claude
role: >
  Five large, foundation-first phases that build PARIPRASHNA_ARCHITECTURE v1.0 —
  each executed by a dynamically-sized agentic swarm running autonomously from BIND
  to gate, with worktree isolation, verifier-gated merges, and production kept in
  sync with main at every phase close. Supersedes nothing; it is the HOW for the
  roadmap's WHAT.
relates_to:
  - 00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md (PPR requirements built here)
  - PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md (the 30 lanes phased here)
  - 00_ARCHITECTURE/PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md (gate batteries)
  - 00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md (the isolation law this obeys)
  - 00_ARCHITECTURE/briefs/pariprashna_build/CAMPAIGN_PB_MASTER_BRIEF_v1_0.md (the campaign idiom)
changelog:
  - "1.0 (2026-08-19): initial plan."
---

# Paripraśna — Phased Swarm Implementation Plan

## §0 — The autonomy contract (read this first; everything else depends on it)

The instruction is "each phase runs fully autonomously without interruption."
Three classes of work cannot be made autonomous, and pretending otherwise
would build a plan that stalls at 3am:

| Class | Examples | Why not automatable |
|---|---|---|
| **Ruled-human** | AC-15 week-of-use verdict (W-4); HS-3 sensitive-reading sign-off | Native judgment is the deliverable, by ruling. Never simulated or proxied. |
| **Console/credential** | Cloud SQL PITR enable, restore drill on a scratch instance, `ANTHROPIC_API_KEY` provisioning, `amjis_app` rotation | Elevated infra permissions and secret material outside any agent's reach |
| **Irreversible-by-design** | The retirement commit that deletes the fallback surface; flag deletion | Rollback ceases to be a flag flip; the decision to cross that line is yours |

**The resolution: pre-authorize at the seam, never interrupt mid-phase.**

1. Every phase opens with an **OPERATOR PACKET** — the console/credential
   actions, each a copy-paste command or console path with its verification
   check. You do these *before* dispatch (10–30 minutes), and the phase's BIND
   step verifies them and refuses to start if any is missing. The swarm never
   waits on you.
2. Every phase opens with an explicit **PRE-AUTHORIZATION BLOCK** you sign
   once: which irreversible actions the swarm may take, which deploys it may
   push, the spend ceiling, and the halt conditions. Inside those bounds it
   never asks again.
3. **Ruled-human work is a phase SEAM, not a phase step.** AC-15 sits between
   Phase III and Phase IV as its own human interval. No swarm waits on it.
4. **Halt, don't hang.** On a halt condition the swarm stops at the last green
   integration point, pins rollback, writes the finding, and ends. You wake up
   to a report, never to a hung queue.

Everything below is designed so that between "dispatch" and "gate report" you
are not needed.

---

## §1 — Swarm doctrine (identical in every phase; sized differently)

### §1.1 Roles — the taxonomy is fixed, the counts are derived

| Role | Charge | Count formula |
|---|---|---|
| **CONDUCTOR** | The workflow script itself. Deterministic orchestration: fan-out, barriers, merge trains, gate dispatch. Never improvises. | 1 (the script) |
| **SCOUT** | Pre-flight discovery: enumerate real work, produce the **file-collision map** that defines lane boundaries, find the traps. Read-only. | = distinct subsystems the phase touches (3–6) |
| **BUILDER** | One lane, one isolated worktree, one branch. TDD where a test can exist. | = independent lanes from the collision map |
| **VERIFIER** (PARĪKṢAKA) | Independently **re-derives** the lane's claim against live state. Never re-reads the builder's summary as evidence. Its PASS is the only thing that admits a merge. | = builders, 1:1, never the same agent |
| **ADVERSARY** (REFUTER) | Tries to **break** an `[integrity]`-class claim. Prompted to refute; defaults to REFUTED under uncertainty. Majority kills the claim. | = 3 × integrity-class assertions in the phase |
| **JUDGE PANEL** | Only where taste or method correctness is the deliverable (visual design, statistical method). Independent scoring, then synthesis. | 3–5 per judged artifact |
| **INTEGRATOR** | Owns one merge train: lane branches → integration branch, conflict resolution, CI green. | = merge trains (usually 2: schema/infra and application) |
| **GATE-RUNNER** | Fresh context. Runs the gate battery against the **deployed** artifact. Plus an **anti-gaming** twin whose only job is to find the gate run cheating. | 2 per gate |
| **SCRIBE** | Ledgers, lane state shards, phase report, session-close artifacts. | 1 |
| **OPERATOR-LIAISON** | Packages what humans must do next; verifies the operator packet at BIND. | 1 |

**Sizing is a function, not a guess.** The CONDUCTOR computes it at runtime
from the SCOUT output:

```js
const lanes      = collisionMap.independentLanes          // volume drives builders
const builders   = lanes.length
const verifiers  = builders                                // 1:1, independent
const adversaries = integrityClaims.length * 3              // 3 refuters per claim
const scouts     = subsystems.length
const total      = 1 + scouts + builders + verifiers + adversaries
                     + judges + integrators + 2 + 1 + 1
```

### §1.2 The concurrency truth (stated, not hidden)

The orchestrator admits **min(16, cpus−2) concurrently running agents** and up
to **1000 per workflow lifetime**. So "maximum agents" means *hundreds queued
and pipelined across a phase, ~16 executing at any instant* — real massive
parallelism, achieved by pipelining rather than by simultaneity. The plan
exploits this by using `pipeline()` (no barriers) as the default: lane A can be
in verification while lane B is still building. Barriers appear only where a
stage genuinely needs all prior results (dedup, gate batteries, merge trains).

### §1.3 Isolation and freeze law

- **Every builder gets its own git worktree** (`isolation: 'worktree'`). The
  shared checkout is never a build surface — the project's own
  WORKTREE_ISOLATION_PROTOCOL requires this, and it is what makes 16
  simultaneous writers safe.
- **The collision map is the lease register.** Two lanes may never declare the
  same path in `may_touch`. If the SCOUT finds an unavoidable overlap, those
  lanes are *serialized* — the only legitimate source of sequence inside a
  wave.
- **FREEZE-1 (integration freeze):** while a gate battery runs, the integration
  branch accepts no merges. The artifact under test must not move.
- **FREEZE-2 (schema freeze):** once a migration is applied to production in a
  phase, no further migration lands in that phase. Schema changes cluster into
  one train, early.
- **FREEZE-3 (main freeze at close):** between the phase's final main merge and
  the production deploy verification, main takes no other campaign's merges.
  Coordinated through CAMPAIGN_COORDINATION leases.

### §1.4 Git, deploy, and production-sync cadence (identical every phase)

```
 BIND commit ─────────────────────────────────────── preconditions + fingerprints
   │
   ├─ wave: builder worktrees → lane branches  (parallel, per-lane commits)
   │    commit form: <type>(<phase>/<lane>): <what> [SWARM]
   │
   ├─ VERIFIER PASS  ──▶ INTEGRATOR merges lane → integration branch
   │    (a builder's own claim NEVER admits a merge)
   │
   ├─ CI green on integration ──▶ PR to main ──▶ merge queue ──▶ main
   │
   ├─ DEPLOY to production from main   (features flag-OFF by default)
   │
   ├─ POST-DEPLOY SMOKE (demonstrated-can-fail) ──▶ FREEZE-1
   │
   ├─ GATE BATTERY on the DEPLOYED artifact  +  anti-gaming pass
   │
   └─ PHASE CLOSE: flags flipped per pre-authorization · tag `pariprashna/pN-close`
        · Baseline regenerated · ledgers + CURRENT_STATE + SESSION_LOG · report
```

**Production stays in sync with main at every phase close** — the deploy
happens *before* the gate, so the gate tests what production actually runs.
New capability ships flag-OFF and is flipped only by the pre-authorization.

### §1.5 Failure policy (this is what makes unattended running safe)

| Event | Response |
|---|---|
| Builder produces nothing / stalls | Retry once with a sharpened prompt; then PARK the lane with a written finding. **The wave continues.** |
| Verifier FAILS a lane | One fix-loop with the finding fed back; second failure → PARK, never merge. |
| Adversary majority refutes a claim | The claim dies; dependent lanes re-scoped by the CONDUCTOR; recorded, not hidden. |
| CI red on integration | Integrator bisects; the offending lane reverts out of the train, PARKED. |
| Post-deploy smoke red | **Immediate rollback to the prior revision.** Never forward-fix a red production route (W-3). Phase halts. |
| Gate assertion fails | Phase halts at the last green point; rollback pinned; report written. No partial-credit close. |
| Spend ceiling reached | Phase halts cleanly at the next lane boundary with state preserved for resume. |
| Anything touching a path outside the lease | Hard stop for that lane; scope violation recorded. |

**Never-do list, encoded in every builder prompt:** never background a slow
step and end the turn (the PRATIJÑĀ stall pattern, 6 occurrences); never claim
a PASS without a detector that could have returned false (§N.8); never merge on
your own say-so; never edit an applied migration; never regenerate the estate
in one PR (strangler); never write outside your worktree.

---

## §2 — THE FIVE PHASES

Foundation first; each phase is a floor the next stands on.

```
 P1 FOUNDATION ────────────── the walls, the floors, the ground truth
      │  (nothing may be exposed or built on until these hold)
 P2 THE READING MADE TRUE ─── presentation truth + epistemic truth
      │  (the reading becomes what it claims to be)
 P3 ONE ENGINE, ONE DOOR ──── genuine parity, then the default flip
      │
 ═══ HUMAN SEAM: AC-15 ═══════ your week of daily use. The verdict (W-4).
      │
 P4 THE OLD DIES, THE INSTRUMENT REMEMBERS ── retirement + accrual
      │
 P5 EARNED CALIBRATION ────── the loop starts paying out, per earned cell
```

---

### PHASE I — FOUNDATION
*The walls, the floors, and the ground truth.*

**Mission.** Make the system safe to expose and safe to build on. Every later
phase's code runs inside these walls; every later claim rests on this
phase's ground truth. Nothing in P2–P5 is legitimate if P1 is skipped.

**Why it is the foundation.** Three of its lanes are load-bearing for the
mission itself: the Ethical Framework becomes runtime-enforceable (mission
item 6 becomes possible), the NO-LEAKAGE wall becomes a database-level fact
rather than an application convention (mission item 5 becomes trustworthy),
and the irreplaceable data becomes recoverable (mission items 3 and 5 stop
being one incident from gone).

**Lanes** (roadmap G1-A…G1-H + two ground-truth lanes):

| Lane | Deliverable | Integrity claims |
|---|---|---|
| P1-A | SafetyPolicyGate + HS-1..HS-6 at three enforcement points | 6 |
| P1-B | Consent schema, native_self strictness, minor exclusion, withdrawal→verified deletion | 3 |
| P1-C | Five DB roles, app off `amjis_app` for reads, chart-scoped RLS on C1/C3, out-of-process ledger writer, append-only audit grants | 4 |
| P1-D | Middleware + per-user rate limits + $2/turn · $40/day pre-dispatch ceilings, both doors | 2 |
| P1-E | PITR verified, restore drill executed, RPO/RTO + DR runbook, logical export schedule | 2 |
| P1-F | Provider posture doc; ANTHROPIC key provisioned or delisted | — |
| P1-G | Injection containment + answer-side entitlement scan | 2 |
| P1-H | PB-9-DETECTOR (no-auto-promotion CI detector) | 1 |
| P1-I | **Ground truth:** re-verify every UNVERIFIED Baseline row live (PITR, roles, flag env, serving revision); regenerate the Baseline | — |
| P1-J | **Ground truth:** design-plan (v0.3) grounding pass — it still describes the removed rail and predates the dock; P2's design lanes need it | — |

**Swarm composition** (computed at BIND; indicative):
scouts 4 (DB/infra · safety surface · route+middleware · consent data model) ·
builders 10 · verifiers 10 · adversaries 20 × 3 = **60** · integrators 2
(schema/infra train, application train) · gate-runners 2 · scribe 1 ·
operator-liaison 1 → **≈ 90 agents**, ~6 concurrency waves.

Adversary weighting is deliberate: this phase's claims are the ones where a
false PASS is dangerous rather than merely wrong. Every hard stop faces three
refuters whose prompt is *"find the input that gets a date-of-death past this
gate."*

**Parallelization.** P1-A/B/C/D/E/F/G/H/I/J are mutually independent by file
scope except: P1-C (roles) must land before P1-I re-verifies role state, and
P1-A shares the pre-wire scan file with P1-G — those two serialize. Everything
else fans out at once. The schema train (P1-B consent migration, P1-C
grants/RLS) is one integrator; all application work is the other.

**Operator packet (before dispatch):** enable Cloud SQL PITR · create the
scratch instance for the restore drill and grant the drill role · provision or
delist `ANTHROPIC_API_KEY` · confirm the `amjis_app` rotation window.

**Pre-authorizations:** may apply migrations to production (surgical, verified
per §N.4) · may deploy · may rotate `amjis_app` at the stated window · features
ship flag-OFF; the safety gate flips ON at close.

**Gate (LIVE rung, deployed artifact):** psql role/grant matrix + write-denial
probe · RLS cross-context denial · every HS fixture observed blocking, each
demonstrated-can-fail against a seeded violation · caps observed blocking ·
consent-absent chart refusing interpretive serving · executed restore-drill log
· arm-4 canary green · anti-gaming pass.

**Close:** safety gate ON in production · tag `pariprashna/p1-close` ·
Baseline regenerated with every UNVERIFIED row resolved.

---

### PHASE II — THE READING MADE TRUE
*Presentation truth and epistemic truth, together.*

**Mission.** Make the reading actually be what it claims: typographically
structured, cited at first paint, honestly controlled, durably persisted — and
carrying a machine-checkable receipt that proves its coverage, its derivations,
its alternatives, and its confidence types. This is the phase where
"beyond-acharya-grade" stops being an aspiration.

**Why it stands on P1.** The receipt has a `safety_decision` field that only
exists because P1 built the gate. The consent state it records comes from P1's
schema. And a phase that changes the wire format and the persistence protocol
must not also be the phase that discovers its database has no backup.

**Why these two gates are one phase.** They are one product claim, and they
share files: block typing (G2-A) is the prerequisite for `prose_binding`
(G3-A) and for voice enforcement's block policy (G3-D). Splitting them would
create a phase seam in the middle of a dependency.

**Lanes** (G2-A…H + G3-A…G):

*Presentation truth:* P2-A semantic blocks on the wire (+ `prediction_card` as
a first-class event → unlocks the in-stream confirm affordance) · P2-B
citations at first paint + server-derived grounding · P2-C honest controls
(model/length plumbed or removed; depth from the scope tuple) · P2-D durable
persistence (outbox, crash recovery, semantic-hash parity) · P2-E observability
(wire the dead cost/latency schema; TTFT; lint firing rate) · P2-F mobile +
a11y · P2-G edge-state lexicon + classifier fold · P2-H sidebar, empty state,
the Seal.

*Epistemic truth:* P2-I receipt emission + validator · P2-J three
interpretations + falsifier · P2-K typed confidence + T-8 precision scan ·
P2-L voice enforcement (remedial imperative, pacing) · P2-M reader affordances
("Read it another way", "What would change my mind") · P2-N the quality corpus
(12 query classes, 13 scored dimensions) · P2-O model qualification suites.

**Swarm composition:** scouts 5 · builders 15 · verifiers 15 · adversaries
(receipt fields, B.4 sets, confidence typing, parity hash — ~14 integrity
claims) 42 · **judge panel 5** (the Seal, typography, and the two reader
affordances are taste deliverables — independent scoring, then synthesis from
the winner) · integrators 2 · gate-runners 2 · scribe 1 → **≈ 87 agents**.

**Parallelization.** Two internal waves, pipelined not barriered: the
presentation wave fans out immediately (8 lanes, disjoint files); the epistemic
wave's P2-I begins the moment P2-A's wire change is verified, and P2-J/K/L/M
pipeline behind P2-I. P2-N (corpus) and P2-O (qualification) are authored in
parallel from the start and run last. **The only true serialization is
A → I → {J,K,L,M}.**

**Operator packet:** none (this phase is code and fixtures).

**Pre-authorizations:** deploy per wave · flip the semantic-block and
first-paint-citation flags at close · corpus may call production models within
the spend ceiling.

**Gate:** a real reading on the deployed route renders a daśā table as a table
and a verse as a verse with its gloss, chips at final geometry from first
paint · crash kill-test shows a visible incomplete state, outbox recovers ·
receipts audit-clean with B.4 sets present wherever the significance trigger
fires and a monitored waiver rate · a planted-contradiction fixture surfaced,
not smoothed · P1's safety assertions re-run green on the new artifact.

---

### PHASE III — ONE ENGINE, ONE DOOR
*Genuine parity, then the flip.*

**Mission.** Make "one engine, two doors" true in fact rather than in
aspiration — the MCP door gets the same gates, the same receipt, the same floor
— and then make Paripraśna the default surface.

**Why it stands on P2.** Parity is meaningless until there is something worth
being at parity with: the receipt is the parity instrument. And per your
NCD-1 ruling, the flip waits for fidelity so that AC-15 judges the real
product.

**Lanes:** P3-A unified plan type (`PipelinePlan` ↔ `VidhiPlan`, the
`tool_name ↔ primitive_id` map + CI proof) · P3-B headless loop extraction and
`prashna_ask` re-based onto it with all gates · P3-C canonical store completion
(history/user turns, tool_call/tool_result/reasoning parts) · P3-D door-parity
contract tests (normalized receipt-hash equality) · P3-E CI post-deploy smoke,
demonstrated-can-fail (PB-4 F-6) · P3-F **the flip** (PB-4 F-5 steps 1–2:
default routing everywhere, flag retained as the rollback lever, then seven
consecutive green smokes — W-1, counter resets on any red).

**Swarm composition:** scouts 3 · builders 6 · verifiers 6 · adversaries
(parity hash, floor equivalence, plan subsumption — 6 claims) 18 · integrators
1 · gate-runners 2 · scribe 1 → **≈ 37 agents**.

**Parallelization.** A/B/C/D/E all parallel; **F is strictly last and strictly
serial** — the flip is one act, and the seven-smoke hold is a wall clock the
swarm simply waits out (cheap, no agents burning).

**Pre-authorizations:** may execute the default flip · may run the seven-smoke
hold autonomously and declare it green **only** on seven consecutive passes
with the counter reset by any red · rollback = flag flip, no approval needed.

**Gate:** the same question through both doors yields receipt-hash-equal
semantic projections · fresh session lands on the default route from dashboard
and global nav · seven green smokes recorded in CI history *before* close ·
flag retained (deletion is Phase IV).

---

### ═══ HUMAN SEAM — AC-15 ═══
*Your week. No swarm runs.*

Daily use on the default surface, seven 60-second rubric cards (felt friction
y/n + where · trust moment y/n + which · register break y/n · one free line),
then the verdict — binary, yours, non-automatable, never claimed on your
behalf (W-4). The rubric exists only to preserve *why* for the record.

**The one thing the swarm does here:** nothing. Phase IV's BIND reads your
verdict as its precondition. A NO sends the findings back as a P2-prime
remediation wave rather than proceeding to retirement — which is precisely why
retirement sits *after* this seam.

---

### PHASE IV — THE OLD DIES, THE INSTRUMENT REMEMBERS
*Retirement, then accrual.*

**Mission.** Delete the fallback and the legacy estate; then build the layer
that makes the instrument a companion across years rather than a series of
consultations.

**Why it stands on the seam.** You never delete the fallback before the
verdict, and you never build accrual features on a surface whose base is still
in question.

**Lanes:**

*Retirement:* P4-A consult/consume retired (308 route redirects, 410 + pointer
for API callers per the inbound inventory) · P4-B dead-tree deletion per the
**refreshed** census, leaf-first, with line-by-line verifier review of the
deletion diff (W-2) · P4-C flag deletion (`PARIPRASHNA_ENABLED` grep = 0) +
residue sweep (`audience_tier` type/schema vestiges, the second error
classifier) · P4-D Q-2 graded readings + docs seal (design plan →
RATIFIED-AS-BUILT, Baseline regenerated).

*The remembering:* P4-E recall wired with **independent-then-compare** (the
current reading composes before prior conclusions are retrieved — the
anti-anchoring rule) · P4-F the arrival line from L1/Kāla truth, never
model-composed · P4-G **the window-opening ask** — the highest-leverage
unbuilt feature in the architecture · P4-H dispute capture + the feedback
endpoint restored · P4-I digest transport + DB journal · P4-J signal reader
text, top-cited-first, generate-review-freeze · P4-K the post-six-views
narration audit.

**Swarm composition:** scouts 4 · builders 11 · verifiers 11 · adversaries
(deletion warrant, recall-firewall, arrival-line truthiness, dispute
non-folding — ~10 claims) 30 · judges 3 (the arrival line and the window-ask
are voice deliverables) · integrators 2 · gate-runners 2 · scribe 1 →
**≈ 65 agents**.

**Parallelization.** Retirement and remembering run as two concurrent trains
with disjoint file scopes — the deletions touch the legacy tree, the accrual
work touches the Paripraśna tree. Within retirement, **A → B → C is strictly
serial** (redirects before deletions before deflagging). P4-J (editorial reader
text) is embarrassingly parallel and soaks up idle capacity all phase.

**Pre-authorizations (the heaviest set):** may execute the irreversible
retirement commit and flag deletion after the verifier's line-by-line diff
review passes · rollback after deflag = git revert of the retirement commit +
rollback-pin redeploy, pre-authorized without further approval.

**Gate:** zero orphaned importers (build + grep proof) · redirect assertions
green · `PARIPRASHNA_ENABLED` absent · every prior phase's integrity assertion
re-run green on the deployed default artifact · a returning thread greets with
where the daśā stands · a closed window gets asked about in conversation and
the answer reaches the ledger.

---

### PHASE V — EARNED CALIBRATION
*The loop starts paying out, one earned cell at a time.*

**Mission.** Build the calibration sink and the scoring science, then let cells
activate as — and only as — they earn it. This is the phase that turns the
mission's central claim from a structure into evidence.

**Why it is last.** It is gated by time, not by work: windows must close and
outcomes must accrue. Everything buildable is built here; the payout arrives
over years.

**Lanes:** P5-A the sink, exactly per DVA Rulings 55/79 **plus**
`calibration_method_version` (your NCD-11 amendment) · P5-B immutable `model_p`
at detection, with rejected-UPDATE proofs · P5-C scoring (full outcome
taxonomy incl. censoring, proper rules by type, coverage-stamped figures,
hierarchical partial pooling, reliability diagrams, temporal cutoffs,
held-out/prospective partitions kept separate) · P5-D per-cell activation on
the ruled gate (±0.15 interval half-width on effective n, ≥60% coverage) ·
P5-E the calibration observatory panel.

**Swarm composition:** scouts 2 · builders 5 · verifiers 5 · **judge panel 5 —
statistical method correctness is the deliverable here, and a wrong estimator
that runs is worse than none** · adversaries (immutability, exclusion
correctness, activation arithmetic — 8 claims) 24 · integrators 1 ·
gate-runners 2 · scribe 1 → **≈ 45 agents**.

**Parallelization.** A → B serial (column on the table); C and E parallel; D
last. The judge panel runs against C's method spec *before* C's code is
written — method review precedes implementation.

**Gate:** immutability triggers reject UPDATEs · `unverifiable` excluded from
Brier at all three enforcement layers · the first activated cell serves
interval + n + coverage and nothing else · below-gate cells serve the honest
flag · collect-only reversion proven as the rollback.

---

## §3 — Reference workflow script (Phase I shape; the pattern for all five)

```js
export const meta = {
  name: 'pariprashna-p1-foundation',
  description: 'Phase I: safety gate, consent, roles+RLS, caps, durability — swarm build to gate',
  phases: [
    { title: 'BIND' }, { title: 'Scout' }, { title: 'Build' },
    { title: 'Verify' }, { title: 'Refute' }, { title: 'Integrate' }, { title: 'Gate' },
  ],
}

// ── BIND: preconditions, operator packet, fingerprints. Halt, never hang.
phase('BIND')
const bind = await agent(BIND_PROMPT, { schema: BIND_SCHEMA, effort: 'high' })
if (!bind.operator_packet_complete || !bind.preconditions_met) {
  log(`HALT at BIND: ${bind.blocking.join('; ')}`)
  return { halted: 'bind', blocking: bind.blocking }
}

// ── SCOUT: volume discovery → the collision map that DEFINES the lanes
phase('Scout')
const scouts = await parallel(SUBSYSTEMS.map(s => () =>
  agent(scoutPrompt(s), { label: `scout:${s}`, schema: SCOUT_SCHEMA })))
const map    = buildCollisionMap(scouts.filter(Boolean))   // plain code, no agent
const lanes  = map.independentLanes                        // ← agent count derives HERE
const serial = map.serializedPairs
log(`${lanes.length} independent lanes · ${serial.length} forced-serial pairs · ` +
    `${map.integrityClaims.length} integrity claims → ${map.integrityClaims.length * 3} refuters`)

// ── BUILD → VERIFY → REFUTE, pipelined per lane (no barriers: lane A verifies
//    while lane B still builds). Worktree isolation per builder.
const built = await pipeline(lanes,
  lane => agent(buildPrompt(lane, map), {
    label: `build:${lane.id}`, phase: 'Build',
    isolation: 'worktree', schema: LANE_RESULT, effort: 'high',
  }),
  (result, lane) => result?.ok
    ? agent(verifyPrompt(lane, result), {                 // independent re-derivation
        label: `verify:${lane.id}`, phase: 'Verify',
        isolation: 'worktree', schema: VERDICT, effort: 'high' })
        .then(v => ({ lane, result, verdict: v }))
    : { lane, result, verdict: { pass: false, reason: 'builder produced nothing' } },
  async (vr, lane) => {                                   // adversaries only on integrity claims
    if (!vr.verdict?.pass) return vr
    const claims = lane.integrityClaims ?? []
    const votes  = await parallel(claims.flatMap(c =>
      [0, 1, 2].map(i => () => agent(refutePrompt(c, vr, i), {
        label: `refute:${lane.id}:${c.id}:${i}`, phase: 'Refute', schema: REFUTATION }))))
    const killed = claims.filter((c, ci) =>
      votes.slice(ci * 3, ci * 3 + 3).filter(Boolean).filter(v => v.refuted).length >= 2)
    return { ...vr, killedClaims: killed, admissible: killed.length === 0 }
  })

// ── INTEGRATE: two merge trains. Only VERIFIER-PASSED, unrefuted lanes merge.
phase('Integrate')
const admissible = built.filter(b => b?.admissible && b.verdict.pass)
const parked     = built.filter(b => b && !(b.admissible && b.verdict.pass))
log(`${admissible.length} admissible · ${parked.length} PARKED (findings written, wave continued)`)
const trains = await parallel(['schema', 'application'].map(t => () =>
  agent(integratePrompt(t, admissible), { label: `integrate:${t}`, schema: TRAIN_RESULT,
    effort: 'high' })))
// integrator handles: lane→integration merge, CI green, PR→main, deploy, post-deploy smoke

// ── GATE: fresh context on the DEPLOYED artifact + anti-gaming twin. FREEZE-1 active.
phase('Gate')
const [gate, antiGame] = await parallel([
  () => agent(GATE_PROMPT,      { label: 'gate:runner',     schema: GATE_RESULT, effort: 'max' }),
  () => agent(ANTI_GAMING_PROMPT,{ label: 'gate:anti-gaming', schema: GAMING_RESULT, effort: 'max' }),
])
return { gate, antiGame, parked: parked.map(p => p.lane.id), trains }
```

Four properties of this shape matter more than its details: **agent counts are
computed from scout output, never hardcoded**; **pipeline() not parallel() is
the default**, so nothing waits that needn't; **a builder's claim never admits
a merge**; and **every exit is a return value, never a hang.**

---

## §4 — Phase summary

| Phase | Mission | Lanes | Agents (indicative) | Human involvement |
|---|---|---|---|---|
| **P1 Foundation** | walls, floors, ground truth | 10 | ≈ 90 | operator packet (~30 min) + pre-auth |
| **P2 The reading made true** | presentation + epistemic truth | 15 | ≈ 87 | pre-auth only |
| **P3 One engine, one door** | parity, then the flip | 6 | ≈ 37 | pre-auth only |
| **— seam —** | **AC-15** | — | 0 | **your week; the verdict** |
| **P4 Old dies, instrument remembers** | retirement + accrual | 11 | ≈ 65 | pre-auth (irreversible set) |
| **P5 Earned calibration** | the loop pays out per earned cell | 5 | ≈ 45 | pre-auth + threshold review |

**≈ 324 agents across the build**, five autonomous runs, one human week, and
production in sync with main at every phase close.

## §5 — What to author next

One **phase brief per phase**, authored just before dispatch (never all five up
front — each phase's brief should be written against the Baseline the previous
phase regenerated). Each contains: the operator packet, the pre-authorization
block, the lane table with `may_touch` leases, the integrity-claim register,
the gate battery, and the workflow script. Phase I's brief is the immediate
next deliverable.

*End PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN v1.0.*
