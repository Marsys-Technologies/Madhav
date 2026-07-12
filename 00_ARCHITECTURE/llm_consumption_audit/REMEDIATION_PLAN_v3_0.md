---
artifact: REMEDIATION_PLAN_v3_0
type: REMEDIATION_MASTER_PLAN (plan §10 step 2 output — SUPERSEDES REMEDIATION_PLAN_v2_0.md)
version: 3.0
status: RATIFIED — native, 2026-07-12 (incl. all §8 rulings); conductor brief flipped ACTIVE same day
authored_by: Fable 5 (Cowork) + native, session LLM-CONSUMPTION-REMEDIATION-PLANNING-2026-07-12
consumes_from: PLANNING_SESSION_HANDOFF_v1_0.md · LLM_CONSUMPTION_AUDIT_v1_0.md ·
  deliverables/findings.jsonl (1,009) · MARSYS_DEFECT_GAP_REGISTER_v2_0.md (LCA-1..19, R-37..48, KP-4) ·
  GATE_RATIFICATION_v1_0.md (E-2/E-4/E-5/E-6/E-7c/E-8 bind) ·
  briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §0-§2.1 (doctrine, inherited verbatim) + §9 (P-1..P-13) ·
  state/LANE9.md · Lane-10 ledger
coverage_manifest: deliverables/wp_coverage.jsonl — ALL 1,009 finding_ids → exactly one WP; 0 unmapped
execution_vehicle: CLAUDECODE_BRIEF.md at project root (single kickoff; conductor-run; §7)
chart_ids: 482012f1 (Abhisek, native) · 1c826d5a (Abhinandan, verification chart)
native_rulings_incorporated_v3: per-wave deploy cadence · W0→W4 in one kickoff, end-to-end ·
  root CLAUDECODE_BRIEF.md as kickoff vehicle · end-state definition (§1) is the program's
  constitution · main↔production sync verification at close
changelog:
  - v3.0 (2026-07-12): third pass per native directive — (a) §1 END-STATE DEFINITION added:
    the target from the consuming LLM's perspective (E1-E7), inheriting the audit plan's
    §0-§2.1 doctrine verbatim-by-reference; demand-side chase posture elevated to a served
    consumption protocol (WP-1.6 widened); (b) §7 CONDUCTOR EXECUTION MODEL: single kickoff
    prompt via root CLAUDECODE_BRIEF.md — conductor self-provisions environment + worktrees,
    implements, commits, merges, pushes to GitHub, deploys per wave close (W0/W1/W2/final),
    live-verifies on prod after every deploy, and closes with full cleanup + main↔production
    sync proof; (c) §8 pre-ratified decisions extended with deploy/cleanup rulings.
  - v2.0 (2026-07-12): machine-verified coverage (wp_coverage.jsonl, 0 unmapped); register
    sweep added WP-1.8 + widened WP-2.5; autonomous swarm + per-intervention domain verification.
  - v1.0 (2026-07-12): initial wave structure (superseded in place).
---

# LLM Consumption Remediation — Master Plan v3.0

## §1 — End-state definition (the program's constitution; every WP, brief, verifier, and gate serves THIS)

Native intent, consolidated. The end state is defined **from the perspective of the
consuming LLM** — not from the presence of data in any layer (audit plan §0, inherited:
*"if data exists but is not retrieved accurately, consistently, and in usable form, there
is no meaning to having the data"*).

- **E1 — Complete in width and depth, over the wire.** The LLM receives, through the
  retrieval tools, evidence complete on both axes (audit doctrine §2, verbatim): WIDTH —
  the full span of data points relevant to a question, every relevant-but-unreceived
  point root-caused; DEPTH — the full dossier of every entity entering a synthesis (the
  Mercury standard: strength, avastha, yoga/dosha membership, dispositor chain,
  varga-wise placement, temporal presence, structural×temporal convergence,
  bhava-sandhi/cusp flavor, combustion, and every other facet the system holds).
- **E2 — The extensive factor space, not the usual suspects.** The information span is
  tested against the UNION of (1) the classical canon's concept inventory, (2) the
  system's own asset inventory (DB + CAPABILITY_MANIFEST, enumerated, not remembered),
  and (3) the L2/L3 derived surfaces — never against an example list (audit doctrine
  §2.1, binding). Where canon exceeds system, that delta is WP-2.5-class work; where
  system exceeds serving, that is WP-1.3-class work.
- **E3 — Demand-side chase, never supply-side satisfaction.** On receiving a query, the
  LLM first forms the most extensive set of evidence it EXPECTS (narrow question →
  narrow but comprehensive list; broad question → wide comprehensive list), then chases
  it across ALL appropriate tools — tracking received-vs-needed and continuing until
  each item is fetched or honestly exhausted. Whatever arrives beyond the plan is bonus,
  never the frame. Not finding everything is acceptable; not chasing is not. **The
  approach is the requirement** (native, verbatim intent). This program ships the
  instruments that make the posture possible (capability map, acquisition-tracker
  schema, served consumption protocol — WP-1.6); the full planner doctrine (P-12
  behavioral layer) completes in the doctrine campaign.
- **E4 — Small to huge volumes, processed recursively.** The LLM can handle any evidence
  volume the question generates — from a single fact to tens of thousands of signals —
  by recursive, staged movement between tools (plan → aggregate surfaces → drill →
  re-aggregate), map-reduce over families, and running-state synthesis (WP-1.4). Flat
  top-K walls and un-budgeted dumps are both end-state violations (proportionality,
  audit doctrine §2).
- **E5 — Tools deliver completely; they never error out and never serve blank.** Every
  tool returns the complete relevant information it is expected to provide: no dead
  registry seams, no silent parameter drops, no advertised-empty stages, no
  envelope-vs-payload lies, no wrong-chart data. Honest emptiness (a true zero with its
  reason) is the ONLY permitted empty (WP-0.1, 1.1, 1.3, 1.5, 1.7, 2.2).
- **E6 — Every asset delivers its full declared promise.** Tools front assets; each
  asset was built against a promise (build brief, asset_registry, layer closure, tool
  description). The promise ledger is the contract: every gap between promise and
  delivery is addressed — served fully, or parked with a disclosed flag (§8.3); silent
  shortfall is abolished (WP-1.3, 2.2; measured by the Lane-10 instrument at W4).
- **E7 — Correct, complete, consistent, usable, proportionate** (the audit's five-word
  constitution, §2, inherited whole): value correctness vs L1 truth, cross-tool
  consistency (one quantity, one answer), usable form (text with IDs, budget-bounded,
  attributed), proportionate salience (chart-defining ≠ trivia).

W4's gates (§2 table) are the measurable projection of E1-E7 onto the frozen
instruments. A WP whose acceptance criteria pass but whose outcome visibly violates an
E-clause is NOT done — the E-clauses outrank the mechanical criteria, and verifiers
grade against both.

## §2 — Baseline → gates (frozen 2026-07-12; measured at W4)

| Metric | Baseline | Instrument | W4 gate (§8.1) | E-clause |
|---|---|---|---|---|
| Questions fully SUFFICIENT | 4/328 (1.2%) | Lane-2 matrix | ≥60% SUFFICIENT; ≤10% INSUFFICIENT | E1/E2 |
| Class-9 improvisation | 328/328 | Class-9 logs | measured + categorized (doctrine campaign gates it) | E3 |
| Asset promise delivery | 28/67 (42%) | Lane-10 ledger | ≥85% DELIVERS | E6 |
| Families reachable (real channels) | 2,318/3,058 (76%) | C×R matrix (E-8) | ≥95%; remainder carries ratified disposition | E1/E5 |
| Heavy-question synthesis | 0/7 | Lane-7 spec | 7/7 composed with ledger | E4 |
| Ranked-row attribution | 0% | Lane-6 §7.4 raw | 100% resolvable ledger | E7 |
| Domain discrimination (wealth∩relationship) | 95% overlap | Lane-6 | ≤25%, rationale inline (E-2) | E7 |
| Dossier synthesizability | 1/20; 73.5% | Lane-8 | ≥18/20; ≥90% avg depth | E1 |
| Envelope-vs-payload contradictions | multiple | Lane-4 (deployed, all tools) | 0 | E5 |
| Tool hard-failures (500/dead/blank-dishonest) | 19 dead + sidecar + consult | census | 0 | E5 |

## §3 — Coverage guarantee (the "not one point missed" mechanism)

1. **Finding-level:** `deliverables/wp_coverage.jsonl` maps all 1,009 finding_ids →
   exactly one WP (or DOCTRINE-DEFERRED); 0 unmapped; machine-checked. Distribution:
   WP-1.3=295 · WP-1.7=172 · DOCTRINE-DEFERRED=135 · WP-1.2=79 · WP-1.5=78 · WP-2.3=66 ·
   WP-1.4=48 · WP-2.4=40 · WP-2.5=29 · WP-2.1=27 · WP-2.2=19 · WP-1.8=10 · WP-1.1=7 ·
   WP-0.1=4. All 30 CRITICALs owned (WP-0.1:1, 1.2:5, 1.3:7, 1.4:7, 1.7:1, 2.1:2, 2.2:5,
   2.4:1, 2.5:1).
2. **Register-level:** every OPEN audit class named in exactly one WP — LCA-1..19
   (incl. -3-EXT, -9a-1, -9b-1..5), R-37..R-48, KP-4.
3. **Ledger-level:** Lane-10's 25 SHORTFALL + 14 PARTIAL assets enumerated in
   WP-1.3/WP-2.2; the 114 held-but-not-received dossier facets (LCA-9) resolve through
   WP-1.3 + WP-1.7.
4. **Residual-level:** every declared audit hole owned in §9.
5. **Enforcement (autonomous):** W4 conductor recomputes the manifest vs the register;
   any finding without REMEDIATED/CLOSED/DEFERRED disposition blocks close.
6. **Doctrine boundary:** the 135 class-9 findings transfer to the post-W4 doctrine
   campaign as its requirements corpus — a tracked disposition, not a gap.

## §4 — Wave DAG (parallel-first; per-wave deploy)

```
W0: WP-0.1 ──► DEPLOY+VERIFY ─┐   (isolation proven before any concurrent swarm work)
                              ▼
W1 (seven lanes PARALLEL, worktree-isolated, merge-ordered):
    WP-1.1  WP-1.2  WP-1.3  WP-1.4(design+skeleton)  WP-1.5  WP-1.8  ∥  WP-1.7(bench)
    WP-1.6 (capability map + consumption protocol) LAST in W1
    ──► MERGE WAVE ► DEPLOY+LIVE-VERIFY (whole W1 acceptance suite on prod) ─┐
                              ▼
W2 (five writer packages PARALLEL — disjoint writer families):
    WP-2.1(ka_*)  WP-2.2(bo_* shells + ph_narration)  WP-2.3(bo_cgm graph)
    WP-2.4(bo_laksana)  WP-2.5(new ga_* + L0 seed)
    ──► MERGE WAVE ► DEPLOY (writers + JOB image MUST be live before W3) ─┐
                              ▼
W3: WP-3.1 Abhinandan rebuild (SEQUENTIAL; snapshot + golden catches + auto-restore)
     └─ green ► WP-3.2 native-chart rebuild (autonomous; FORENSIC 7/7 mandatory)
                              ▼
W4: WP-4.1 re-audit (lanes PARALLEL) ──► FINAL DEPLOY (any W4-loop fixes)
                              ▼
CLEANUP + CLOSE: branches/worktrees deleted · all merges pushed · main↔production
    sync PROVEN (§7.6) · register dispositions flipped · governance close
```

Sequencing rationale unchanged from v2 (W0 also poisons swarm testing itself; W1
verifiable against existing data; W2 batched so ONE rebuild verifies; cross-wave
non-blocking dependencies: WP-1.3e acceptance completes post-W3; WP-1.4 deep acceptance
at W4; WP-1.2d fully verified after WP-2.4 rebuilds).

## §5 — Work packages

Unchanged from v2.0 §5 in scope, coverage, root-cause context, and verifier assignment —
**incorporated here by reference** (v2 §5 is the normative WP text; retained in the
superseded file per retain-in-place). v3 deltas only:

- **Every WP header gains an E-clause line** (which §1 clauses it serves): WP-0.1→E5/E7 ·
  WP-1.1→E5 · WP-1.2→E7 · WP-1.3→E1/E5/E6 · WP-1.4→E4 · WP-1.5→E5/E7 · WP-1.6→E3 ·
  WP-1.7→E5 · WP-1.8→E7 · WP-2.1→E1/E6 · WP-2.2→E5/E6 · WP-2.3→E1 · WP-2.4→E2/E7 ·
  WP-2.5→E2 · WP-3.x→verification · WP-4.1→measurement.
- **WP-1.6 widened (E3 made servable):** in addition to the machine-readable capability
  map (concept→tool/service, per-channel) and the acquisition-tracker record schema,
  WP-1.6 now ships a **served consumption protocol** — an MCP-exposed instruction
  surface (prompt/resource) that teaches ANY consuming LLM the demand-side posture:
  form the extensive expected-evidence set first (from the capability map + the
  question's domain), chase every item across tools, track received-vs-needed, declare
  honest exhaustion per item, treat volunteered extras as bonus. This makes the E3
  approach operative from the moment W1 deploys, ahead of the doctrine campaign's full
  planner. Verifier addition: the jyotish-domain agent runs three live consumption
  sessions (narrow / medium / broad question) following the served protocol and grades
  whether the chase actually reaches the expected set.
- **WP-4.1 gains the E3 probe:** W4's Lane-2 re-run executes in demand-side mode against
  the WP-1.6 map (exactly as the original Lane 2 did manually), logging every place the
  map was missing/wrong — those logs seed the doctrine campaign.

## §6 — Verification architecture

Unchanged from v2.0 §6.1–§6.4 (swarm model; parallelization rules; per-intervention
blind verification protocol; domain-specific verifier roster of five: jyotish-domain,
serving-wire, data-plane, security/entitlement, infra) — **incorporated by reference.**
v3 deltas:

- **Post-deploy verification is per-WAVE and mandatory** (§7.4): after each wave deploy,
  the wave's ENTIRE acceptance suite re-runs against production — local-green ≠
  deployed-green is an audit-proven failure mode; a wave is closed only on prod-green.
- **E-clause grading:** every verifier verdict cites which §1 E-clauses the intervention
  serves and affirms non-violation — mechanical criteria AND constitution.

## §7 — Conductor execution model (single kickoff → fully autonomous → clean close)

### §7.1 — The kickoff
One prompt, one vehicle: **`CLAUDECODE_BRIEF.md` at the project root** (CLAUDE.md §C
item 0 — auto-read by every Claude Code session). This planning session authors it
(staged, status-gated per §8.5); the native flips `status: ACTIVE` and issues the
one-line kickoff. From that moment the Program Conductor owns everything to program
close or honest halt.

### §7.2 — Self-provisioning
The conductor establishes its own working state without human help: verifies repo sync
(fetch; main == origin/main; clean tree), provisions the local bench it needs early
(WP-1.7 is deliberately a W1 lane — the conductor may pull its infra sub-items forward
if its own verification needs the bench), confirms DB/proxy/deploy credentials by
read-only probes, creates the run-ledger artifact, and spins worktrees per §6.2
(`git worktree` per implementation lane — the proven R5.3 pattern; no lane ever works on
main directly).

### §7.3 — Commit / merge / push discipline
- **Commit:** per intervention, in its worktree lane, conventional-commit format citing
  WP + finding IDs (`fix(wp-1.3b): honor system_id in query_dasha_periods [F-0354]`).
- **Merge to main:** per WP close, conductor-owned, ONLY after §6.3 verification is
  green — with the standing zero-regression suite (R6A yoga-integrity tests, WP-0.1
  concurrency harness once it exists, canary battery) run on the merge result.
- **Push to GitHub:** at every wave close at minimum (per-WP pushes permitted; the
  invariant is that a wave close never leaves unpushed local state).
- **Migrations:** surgical only (§N.4 — never deploy.yml-auto, never bulk migrate.ts);
  each migration individually applied and individually verified.

### §7.4 — Deploy cadence (native-ruled: per wave)
- **Deploy points:** W0 close · W1 close · W2 close (writers + JOB image must be live
  before the W3 rebuild — the rebuild runs on deployed code by definition) · final
  (post-W4 loop fixes, if any).
- **Deploy protocol per point:** push → build/deploy the affected services (serving
  plane and/or JOB image) → **live re-verification on production**: the closing wave's
  full acceptance suite re-executed against the deployed channel by the verifier agents
  (not the implementers), quoted payloads, both charts. A failed prod verification
  auto-rolls-back (previous image), files the defect, and loops the owning WP under the
  §8.4 iteration budget.
- W3 performs no deploy of its own (it consumes W2's); W4 deploys only if its loop
  produced fixes.

### §7.5 — The W3 rebuild inside the conductor flow
Snapshot → WP-3.1 Abhinandan cascade via orchestrator "click Build" on deployed W2 code
→ full post-W3 acceptance suite (every WP-2.x verifier block) → golden catches → green:
WP-3.2 native rebuild (FORENSIC 7/7, motif>0, chain configurations reachable) → any
failure: auto-restore snapshot, file, loop W2's owning writer, re-deploy, re-run —
autonomously, within budget.

### §7.6 — Cleanup + close (the native's sync mandate, made checkable)
Program close (after W4 gates pass, or at honest halt) REQUIRES, in order:
1. Every intervention branch merged or explicitly abandoned-with-reason in the ledger;
   all worktrees removed; no orphan branches on origin (audit `git branch -a` against
   the ledger).
2. main pushed; `git status` clean; local main == origin/main.
3. Final deploy executed; then **main↔production sync PROOF**: the deployed services'
   image/build commit SHA(s) resolved from the deploy target and shown EQUAL to
   origin/main HEAD (or to the ratified release commit), recorded verbatim in the close
   report. "Probably deployed" does not close the program.
4. Post-deploy smoke: the standing canary battery + one demand-side consumption session
   (per WP-1.6's protocol) against production, green.
5. Governance: register dispositions flipped; TRACEABILITY_MATRIX remediation column;
   CURRENT_STATE + SESSION_LOG atomic close; root CLAUDECODE_BRIEF.md `status: COMPLETE`;
   run ledger sealed.

### §7.7 — Context-decay defense
The conductor chains FRESH sub-sessions per wave (and per WP where large), each
re-grounded from this plan + the brief + the run ledger — never one long context
(the audit's own §12 anti-dilution architecture, reused). The run ledger is the
persistent memory; every sub-session opens by reading it and closes by appending
state, so any interruption resumes losslessly.

## §8 — Pre-ratified decisions (ratify once with this plan; then zero human gates)

- **§8.1 W4 exit gates:** as tabled in §2 — immutable once ratified (R5.3 precedent).
- **§8.2 Ayurdaya:** compute ALL THREE classical methods (Pindayu/Nisargayu/Amsayu),
  method-attributed, with the classical applicability rule served alongside; no
  autonomous doctrinal adjudication (that is P-3, doctrine campaign).
- **§8.3 Unserved-asset disposition:** default SERVE; PARK only behind a genuine design
  question, flagged `parked_pending_native_review`, disclosed at close; autonomous
  RETIREMENT forbidden. Same rule for WP-2.2 empty shells (populate default; retirement
  = parking flag + tool surface removed with it).
- **§8.4 Iteration budgets:** 3 fix-iterations per failed acceptance criterion per WP;
  2 re-entries per wave loop (W3 golden-catch, W4 gate, §7.4 prod-verification
  rollback). Past budget → honest halt report. Honest NOT-MET beats gate-gaming.
- **§8.5 Kickoff gate:** the root CLAUDECODE_BRIEF.md ships `status: STAGED`; a session
  reading it at STAGED must NOT execute (the brief itself enforces this). The native's
  single act: flip to ACTIVE + kickoff line. This is the §7.6-of-v2 "one standing human
  touchpoint," now including deploy authority: ACTIVE status IS the standing
  authorization for all §7.3/§7.4 commit/merge/push/deploy actions and the §7.5
  rebuilds, within this plan's scope.
- **§8.6 HALT conditions (never autonomous):** FROZEN orchestrator contract change
  (§N.2); entitlement regression; budget exhaustion; anything requiring writes outside
  the ratified scope. Halts land in a safe state (snapshot-restored where applicable) +
  honest report; they never wait mid-air on a question.

## §9 — Inherited residuals (owned)

| Residual | Owner |
|---|---|
| R-38/R-41 deployed receipt-honesty retest | WP-1.5 |
| Fused verifier disagreement #1 | WP-1.5 Lane-4 re-run |
| Consult-pipeline behaviors unaudited (E-7c(ii)) | WP-1.1 smoke + W4 |
| `amjis-pending-stream-reaper` silent cron failure | WP-1.7 (proven `x-marsys-cron-secret` pattern) |
| 583 down-pipeline + 157 truly-unreachable families | W4 re-grade (E-8); §8.3 dispositions |
| Class-9 corpus + Lane-2 evidence-plan corpus + W4's fresh class-9 logs | Doctrine campaign (post-W4): P-1..P-9, P-13 |
| R5.1 deferred shelf (portal/UI, rate limiting, cross-chart pool, JL-022-B) | Separate track, unchanged |

## §10 — Program mechanics

- Briefs: the conductor's Brief Foundry authors per-WP briefs FROM this plan (each cites
  its v2-§5 block, its wp_coverage.jsonl slice, its verifiers, its §8 rulings, its
  E-clauses).
- Traceability: WP close → finding IDs REMEDIATED-PENDING-W4; W4 → CLOSED/re-opened;
  wp_coverage.jsonl is the join key; the register is the permanent record.
- Governance: session-open/close per protocol on every sub-session; CURRENT_STATE at
  every wave close; B.8 versioning throughout; red-team cadence per §M applies.

*End of REMEDIATION_PLAN_v3_0 — supersedes v2.0 (retained in place; v2 §5/§6 remain the
normative WP + verification text, incorporated by reference). Companion artifact:
root `CLAUDECODE_BRIEF.md` (the staged conductor kickoff). Single pending act: native
ratification + status flip to ACTIVE.*
