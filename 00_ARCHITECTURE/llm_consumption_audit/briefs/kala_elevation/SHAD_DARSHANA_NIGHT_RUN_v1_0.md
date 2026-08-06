---
artifact: SHAD_DARSHANA_NIGHT_RUN (Autonomous Overnight Execution Protocol)
canonical_id: SHAD_DARSHANA_NIGHT_RUN
version: 1.3
status: READY-FOR-EXECUTION — the orchestration layer over SHAD_DARSHANA_BRIEF_v2_0.
  The BRIEF owns WHAT/GATES/RAILS; THIS doc owns WHO/WHEN/HOW-PARALLEL. On any conflict about
  scope or acceptance, the brief wins; on any conflict about orchestration, this doc wins.
created: 2026-07-29
revised: 2026-08-01 — v1.3 (Fable review, native-directed elevation of the kickoff prompt):
  §D rewritten frontier-agnostic so it never goes stale — night-specific opening orders now
  live ONLY in the ledger's NEXT-ACTION. Seven elevations, each earned by a real incident in
  Nights 1–2 or the hold-period audits: (1) paste-is-authorization clause (resolves the
  hold-vs-autonomy ambiguity explicitly); (2) a four-step SESSION-OPEN PROTOCOL — rebase
  first, ledger-reconciliation sweep (registers drift in BOTH directions; the item-2 row was
  found stale-open against a merged PR while the wave row said closed), adjudications
  discharged UP FRONT (the N1–N5 block sat empty through two whole nights because nothing
  forced it early), deploy-if-called-for; (3) parallelism made frontier-relative (the old
  prompt hardcoded W1/L0 examples that are long done); (4) a DATA-HONESTY RAIL generalizing
  the N_e case — any newly-seeded prior/constant enters cited + versioned + structural_prior,
  a number without a source is a build error; (5) org-migration + merge-queue mechanics
  inline (dead amonty84 path, queued-green ≠ stuck, "clean status" auto-merge fallback);
  (6) the status=COMPLETED polling rule (a real monitor bug from the hold period — a null
  conclusion was read as done); (7) morning report gains "defects found+fixed" as a
  first-class field (Nights 1–2 both found more value in the defect trail than the forward
  progress, and it deserves structural memory).
  Prior: v1.2 (2026-08-01) — documented the main merge-queue (§B.2a) from the org migration
  to Marsys-Technologies/Madhav; rebased the integration branch over 52 commits of drift,
  one real ci.yml conflict resolved preserving main's double-trigger fix.
  Prior: v1.1 (2026-07-31) — adopted the shad-darshana/integration branch as the merge target
  for all lane PRs (§B.1), replacing direct-to-main, to eliminate cross-campaign merge
  contention observed across Night 1/Night 2 (this repo runs many concurrent autonomous
  campaigns against main simultaneously); tightened the Phase 4/5 boundary so W4's design pass
  (5a) starts on items 36+41 landing rather than waiting for the full W3/W2G/W3K gate close
  (§C); no change to any wave's gates, rails, or acceptance criteria.
author: Fable (elevation session with the native)
mode: >
  FULLY AUTONOMOUS OVERNIGHT, MULTI-NIGHT. One re-pasteable kickoff prompt (§D below — it
  SUPERSEDES brief §D for autonomous night runs). Each night: the Conductor reads the ledger,
  executes the §C sequence from wherever NEXT-ACTION points, lands-or-parks cleanly, deploys
  at wave-gate closes only (via shad-darshana/integration → main, §B.1–B.2), reconciles main
  == production at every gate close and at night end, writes the morning report. The campaign
  is COMPLETE when every brief §3 gate is VERIFIED-CLOSED — expect multiple nights; the
  ledger is the memory.
base_model_policy: >
  SONNET is the base model for all builders. The Conductor holds STANDING AUTHORITY (native
  grant, 2026-07-29) to switch any agent to OPUS and/or raise its reasoning effort wherever
  value-adding — mandatory escalations in §B.3. Cost follows value: mechanical lanes stay
  Sonnet/low; design, verification, adjudication, and numerics run Opus/high+.
---

# ṢAḌ-DARŚANA Night Run — the autonomous overnight swarm

## §A — The swarm roster (fixed roles; every night, same shape)

| Role | Codename | Model / Effort | Writes code? | Charter |
|---|---|---|---|---|
| **Conductor** | — | Opus / high | No (docs+ledger only) | Reads brief+ledger, plans the night per §C, spawns all agents (NEVER from inside a worktree), owns merge trains, deploys, ledger, morning report. Holds the model/effort dial. |
| **Verifier** | PARĪKṢAKA | Opus / high | **NEVER** | Accepts every item against LIVE production post-deploy, on BOTH canonical charts. Four dispositions only. An item without Verifier PASS does not exist. Verifies merge-state separately from verification-state. |
| **Human-replacement Adjudicator** | **ANTARYĀMIN** | Opus / **max** | **NEVER** | Rules every would-be-human question in the native's stead, drawing on full portal + Jyotiṣa domain understanding. **Bounds (absolute):** may never change a FROZEN contract, an untouchable, or a rail; where the only unblocking option would, it takes the no-contract-change conservative path or parks the lane. Every ruling → ledger `ADJUDICATION-<n>` with question, options, ruling, rationale, reversibility note. The native reviews rulings each morning and may overrule; reversible rulings are preferred wherever they exist. |
| **Builder pool** (4–8 concurrent) | lane-named | Sonnet / low-med (escalations §B.3) | Yes — each in its OWN worktree | One lane per builder; TDD; PR + auto-merge; no builder ever touches the ledger, deploys, or another lane's files. |

**Known adjudications pre-queued for ANTARYĀMIN** (so no lane ever waits): W2G N1–N4
(naming, rollout order, backfill, cutover posture) · N5 → **forced conservative default: the
chart-level advisory lock stays; no orchestrator-contract change; intra-chart shard
parallelism forfeited; recorded as reversible** (N5 is a FROZEN-contract question — the one
class ANTARYĀMIN may not decide otherwise) · item-17 Sudarśana writer naming post
collision-audit · W3K layer seating (bg_ vs ga_ split) · paddhati-profile defaults where the
corpus is silent (e.g. Agnivāsa favorable-residence convention — rule from the native's
stated practice in the elevation session: yajña when Agnivāsa favorable per HIS lineage; pin
it, serve corpus-default alongside) · any tool-description wording calls · grader/threshold
constants within LAW ZERO.

## §B — Standing mechanics (every lane, every night)

**B.1 Isolation & merge — the integration branch (adopted 2026-07-31, post-Night-2).** This
repo runs many concurrent autonomous campaigns against `main` simultaneously (SAMĀPTI,
PARIŚODHANA, sarva-siddhi, satya-shesha, and others observed live) — every lane PR that
targeted `main` directly collided not only with those campaigns' merges but with shad-darshana's
OWN sibling lanes (three separate manual conflict resolutions in Night 1 alone, on
`registry_bridge.ts` + `m8_e2e_proof.test.ts`; see `platform-mcp/src/tools/kala_views/
register_all.ts` and the `m8_e2e_proof.test.ts` G12 rewrite for the structural fix to the
*second* half of that problem). The first half is fixed by git topology:

- **Every builder works in `.worktrees/shad-darshana-<lane>`, branched off
  `origin/shad-darshana/integration` — never off `origin/main` directly** (Conductor creates
  worktrees; never spawned from inside another worktree). Small PRs, auto-merge on green,
  **base branch = `shad-darshana/integration`**, not `main`.
- **`main` receives exactly one deliberate merge per wave-gate close** — a single
  `shad-darshana/integration` → `main` PR, opened by the Conductor once a gate's acceptance
  criteria are met, never opened mid-wave. This is the same strangler-fig principle
  ("build beside, cut over deliberately") applied to git topology instead of runtime
  architecture.
- **Conductor standing duty: periodically rebase `shad-darshana/integration` onto the latest
  `origin/main`** (at minimum once per night, before dispatching new lanes) so the branch never
  drifts far enough to turn the eventual integration→main merge into one giant conflict. This
  is a Conductor-only operation — lane builders never touch the integration branch directly
  except via their own lane PR's merge.
- Lane-to-lane conflicts (multiple shad-darshana lanes touching the same file) still happen and
  are still the Conductor's to resolve via `git merge origin/<target>` (never force-push) — the
  integration branch does not eliminate shad-darshana's own internal collision risk, it only
  removes *every other campaign* from that equation.

**B.2 Deploy cadence:** one deploy per wave-gate (not per PR, not per integration-branch merge):
`shad-darshana/integration` → `main` merge (the gate-close PR above) → real authenticated call
→ canary (manual discipline if the IAM grant is still pending) → cutover → **confirm traffic
tracks LATEST** → Verifier post-deploy acceptance → worktree cleanup → ledger. `main ==
production` is asserted at every gate close AND at night end, whichever comes first — but
`shad-darshana/integration == production` is explicitly NOT an invariant the campaign holds
between gates; it is normal and correct for the integration branch to run ahead of production
for the entire span of a wave's build-out.

**B.2a `main` merge queue (repo change, 2026-07-31 — org migration to
Marsys-Technologies/Madhav, verified 2026-08-01 against ruleset `20141220`).** Classic branch
protection on `main` is gone, replaced by a ruleset with a merge queue. This changes what
happens at the ONE gate-close moment B.2 describes (`shad-darshana/integration` → `main`):
opening that PR with all checks green does not merge it immediately — GitHub enqueues it
(`min/max_entries_to_merge: 1`, so PRs merge one at a time, sequentially; grouping strategy
`ALLGREEN`; `min_entries_to_merge_wait_minutes: 5`; `check_response_timeout_minutes: 60`). The
Conductor does not need to do anything differently to ENTER the queue — `gh pr merge --auto
--squash` (or the equivalent merge-when-ready action) still works, it now means "join the
queue" rather than "merge now." What changes is patience and verification: **the merge can
take up to ~5–60 minutes after all checks pass, not seconds; do not treat a queued-but-not-yet-
merged PR as stuck or failed.** Only 4 checks are formally required by the ruleset
(`TypeScript (src only)`, `Unit Tests`, `Secret Scan (unit 0b.2)`, `Governance Gates`) — this
is a SUBSET of the full CI battery this campaign already treats as gating (specificity gate,
tri-plane, Mode-3 routing, census seeds, etc. are NOT in that 4). **The campaign's own
verification bar does not lower to match GitHub's minimum** — the Conductor still waits for
and checks the FULL battery before treating a gate as genuinely closed, exactly as before;
the ruleset's narrower requirement is a GitHub-side merge precondition, not a relaxation of
this campaign's own "no passed with caveats" discipline. `shad-darshana/integration` itself
carries NO ruleset/merge-queue (verified — the ruleset's `conditions.ref_name.include` is
`["refs/heads/main"]` only), so every lane PR merges exactly as before, instantly on green.

**B.3 Model/effort escalation matrix (Conductor applies without asking):** Opus+high
mandatory for: W2 field/science design · stage-4/hazard numerics + skill-score/GOF math ·
W2G spline/root-find numerics + divergence adjudication · W4 UPĀYA/YAJÑA design · parihāra
corpus extraction review · W3K sub-lord doctrine · W6 divergence classification · any builder
after 2 failed verify cycles. Sonnet/low for: W1 joins, facades, CI plumbing, seed rows,
migrations of settled schemas. Effort raised one notch any time a lane produces a
Verifier-rejected artifact.

**B.4 Verification loop per item:** builder green-in-worktree → PR merged → gate deploy →
Verifier live acceptance (both charts) → disposition in ledger. Two Verifier rejections →
Opus rebuild of the lane. No "passed with caveats" — ever.

**B.5 Night-end protocol (hard, cap-aware):** at ~7.5h the Conductor stops opening new lanes;
land-or-park every open lane (no half-merged state), final deploy if a gate closed, worktrees
removed, ledger updated (statuses, evidence, skill scoreboard, ADJUDICATION log,
NEXT-ACTION), main == production verified, **morning report** appended to the ledger: gates
closed, items dispositioned, rulings made, anything parked and why, the single next action.

## §C — THE EXECUTION SEQUENCE (parallel tracks; sequential only where physics demands)

Legend: `∥` = runs concurrently · `→` = hard dependency · **[GATE·DEPLOY]** = wave gate
closes, production deploy, Verifier live acceptance.

**PHASE 0 — Boot (sequential, ~30m).**
Read brief v2.0 + Elevation v1.2 + ledger (create if first night) · preflight: repo/charts
health (LC-5 cleared or ticketed), canary state, **migration range reserved**, duplicate-copy
+ tool-name census, Nirmāṇa catalog-reconciliation baseline · spawn PARĪKṢAKA + ANTARYĀMIN
(standing, all night) · ANTARYĀMIN begins the pre-queued adjudications immediately (they
gate nothing yet — by the time W2G/W3K need rulings, they exist).

**PHASE 1 — W0 foundation (spine sequential ~1 lane, then fan-out 6 lanes).**
1a (sequential spine): `kala_envelope.ts` + `argument_composer.ts` v0 — everything consumes
these; one builder, no parallel edits to the contract.
1b (parallel, 6 lanes): facades NOW+AHEAD ∥ ELECT+STORY ∥ PRIORITIZE+EXPLAIN ∥ upaya+ritual
stubs (Mode-3 `wrong_view` from day one) ∥ parva-dedup fix ∥ CI skeletons (specificity v0,
prose-survival, tri-plane, both censuses, Mode-3 assertion).
**[GATE W0 · DEPLOY #1]** — eight tools live, envelope-conformant, sealed-harness no-loss.

**PHASE 2 — The wide burst (three tracks fully concurrent; ~10 lanes).**
**Track A — W1 serving joins (5–6 Sonnet lanes):** recurrence ladder (2) + digest preset ∥
dual-reference (8) + daśā-lord condition (28) ∥ kālam/diśā-śūla/chandrāṣṭama/horā/janma flags
(32+29) ∥ mudda (30) + sandhi-lite (1) ∥ LEL chapter pinning (10) + LEL-invariance CI ∥
24-lite intervals + grading facade (38-lite) + frontier v0 + tri-plane wiring (43).
**Track B — L0 substrate (3 lanes; zero W1 dependency — this is the velocity move):**
`bg_cohort` (cohort + matched sub-cohort) ∥ `bg_sky_calendar` (chart-independent diary) ∥
`bg_muhurta_lattice` + `bg_parihara_rules` corpus extraction (Opus reviews the parihāra
tables). Super-admin L0 build trigger on completion (§2.5.2 — L0 never rides a user build).
**Track C — W2 science design (1 Opus/high lane, design-only, no code conflicts):** the
ten-stage field design doc: hazard math with thinning suppression, provenance schema, null
calibration, salience+submodular, insight stage, stage-9 harness, Living-LEL triggers.
**[GATE W1 · DEPLOY #2]** when Track A completes (Tracks B/C continue uninterrupted).

**PHASE 3 — W2, the field as science (design → parallel stages → sequential integration).**
3a (parallel, 5 lanes, per Track C's design): stages 0–2 kinematics/symbolization/promise-
graph ∥ stage 3 clocks + applicability (12) + intervals (24-full) ∥ stages 4–5 field assembly
+ provenance (11) + null (23) — **needs Track B cohort** for 5–6 ∥ stage 6+6.5 salience (25)
+ rarity (15) + insight synthesis (E2) ∥ stage 8 timeline-spec (27) + `mi_bhara` stage-9
harness + Living-LEL plane (39, 20, 21) + calibration receipt.
3b (sequential): field integration → determinism hash-replay → weights-v0 seed → skill score
+ GOF published (both charts; first score = CI baseline) → specificity gate flips HARD →
snapshot-id = real hash → authority-basis census populated (44) → Nirmāṇa seed rows + DAG
edges (acyclicity rule §2.5.4).
**[GATE W2 · DEPLOY #3]** — legacy writers untouched and still serving (strangler proof).

**PHASE 4 — The great fan-out (three tracks concurrent; ~8–10 lanes; the biggest night).**
**Track D — W3 computations (6–8 Sonnet lanes over the field):** **dispatch the lattice
engine + Factor Census (36+41, Opus) FIRST or among the first lanes in this track — see the
Phase 4/5 boundary note below, W4's design pass is gated on these two items specifically, not
on the rest of Track D.** Then, in any order/parallel: sandhi-full (1) + sky-calendar joins
(3) ∥ moorti (4) + vedha/Sarvatobhadra (5, closes R-19) ∥ activity tables (6) + muhūrta-lagna
(7) + janma rules (14) ∥ health class (9, S4-05 re-test) + Kota (16) + Sudarśana (17,
post-audit) ∥ Tithi-Praveśa (13) + period-echo (31) ∥ ELECT depth (38-full) + paddhati schema
(37-part) ∥ absence (33) + contrastive (34) ∥ E6-full view deepenings.
**Track E — W2G GOCHARA-2.0 (2 lanes, Opus numerics), starts when ANTARYĀMIN's N1–N5 ledger
block is complete (N5 = conservative default):** V1–V6 validations → 2.0 writer beside v1 →
equivalence corpus, every divergence classified. Parks honest if any N-ruling forces it;
NOTHING downstream requires sub-day (the day-grade-first rail).
**Track F — W3K KP engine (2 lanes, Opus doctrine), starts on W2's clock machinery:**
existing-substrate inventory FIRST (`ganita_kp_cusps_get`) → sub-lord substrate → cusps/
significators/ruling planets → KP window stream as independent clock → school-tagged serving.
**[GATES W3 · W3K · W2G — each deploys and verifies independently as it completes]**

**PHASE 4/5 BOUNDARY — item-triggered, not gate-triggered (tightened 2026-07-31, post-Night-2
audit).** The dependency spine (brief §4) makes W4's true prerequisite narrower than "W3/W3K/
W2G all closed": W4 needs only items 20 (W2, already done) and 36+41 (Track D specifically) —
it needs NOTHING from W2G or W3K. Waiting for all three Phase-4 gates to close before starting
W4 leaves real parallelism on the table. **Correct trigger: the moment items 36 and 41 land
(merge to `shad-darshana/integration`) — regardless of whether Track D's other lanes, Track E,
or Track F have finished — dispatch Phase 5a (the W4 Opus design pass) immediately, running
concurrently INSIDE Phase 4's remaining fan-out, not after it.** Phase 5b's build lanes still
wait on 5a's design output as before; nothing else about W4's sequencing changes.

**PHASE 5 — W4, the intervention flagship (Opus design first, then 3 lanes; see the Phase 4/5
boundary note above for its real start trigger).**
5a: UPĀYA/YAJÑA design pass (Opus/high). 5b (parallel): UPĀYA-SETU full (26) ∥ ritual-
resonance + paddhati live (37-full) + `kala_ritual_get` Modes 1–2 real (40) + Mode-3 pairing
in ELECT + digest ritual rows ∥ Intervention Ledger `mi_sankalpa` (42).
5c (sequential): the canned Mode-2 fixture discharged EXACTLY (both charts, different
candidate sets) + W4 gate battery.
**[GATE W4 · DEPLOY]**

**PHASE 6 — W5 planner (mostly sequential — the three-copy registry trap punishes
parallelism here).** Eight primitives + question_frame threading + machine-band defaults +
depth-contract binding → codegen:vidhi + parity → deploy → **the live-MCP verification table,
built by REAL MARSYS-JIS calls** (all 8 primitives × representative intents; Mode-3 routing
asserted both directions).
**[GATE W5 · DEPLOY]**

**PHASE 7 — W6 cutover + retirement (deliberately sequential — this is where haste kills).**
Per-view cutover with classified equivalence (6 views, one at a time) → legacy retirement ONE
writer/tool at a time (zero-consumer census + duplicate-copy audit + seed-row retirement +
DAG rewire + catalog-reconciliation green, per retirement) → final battery: sealed harness +
preserve-list + minimum-budget + authority-census 100% (44) + **dark-corpus re-measure, 21
questions, both charts, ≥95%** → `SHAD_DARSHANA_REPORT_v1_0.md` → ledger COMPLETE.
**[GATE W6 · FINAL DEPLOY]**

**Realistic night map** (ledger decides, not the clock): Night 1 ≈ Phases 0–2 (+3a started) ·
Night 2 ≈ Phase 3 · Night 3 ≈ Phase 4 · Night 4 ≈ Phases 5–6 · Night 5 ≈ Phase 7. Every
phase boundary is a clean park point; the same §D prompt resumes from NEXT-ACTION.

## §D — THE SINGLE KICKOFF PROMPT (re-paste every night until COMPLETE; supersedes brief §D
for autonomous night runs; night-specific opening orders live in the LEDGER's NEXT-ACTION,
never here — this prompt is deliberately frontier-agnostic so it never goes stale)

```
You are the CONDUCTOR of the ṢAḌ-DARŚANA NIGHT RUN — fully autonomous, overnight, no human
until morning. The native pasting this prompt IS tonight's run authorization: if the ledger
records a campaign hold, this paste supersedes it — record the lift in the ledger with
tonight's date, then proceed. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_NIGHT_RUN_v1_0.md
    (v1.3) — YOUR orchestration contract: §A roster, §B mechanics (§B.1 integration branch,
    §B.2a merge queue), §C sequence bind you;
(2) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md —
    the execution contract: §1 inventory, §2.5 Nirmāṇa contract, §3 gates, §7 rails bind you;
(3) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_SUPREME_ELEVATION_v1_0.md
    (v1.2) then KALA_SIX_VIEWS_DESIGN_v2_0.md then v1_0.md, plus KALA_W2_FIELD_DESIGN_v1_0.md
    for W2 build work — the spec (elevation wins conflicts);
(4) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_STATE.md — the
    ledger, the campaign's memory. Resume exactly from NEXT-ACTION.
SESSION-OPEN PROTOCOL (in this order, before any lane is dispatched):
(a) Rebase shad-darshana/integration onto the latest origin/main (drift is the NORM in this
    repo — 52 commits accumulated in 36h once; conflicts are resolved preserving main's own
    proven fixes, never by discarding either side silently).
(b) LEDGER-RECONCILIATION SWEEP: diff the ledger's item/wave rows against reality (merged
    PRs, live registrations, deployed revisions). Registers drift in BOTH directions — a row
    can be stale-open against a merged PR or stale-closed against a regression. Annotate
    corrections append-only with evidence; never rewrite an original observation.
(c) ANTARYĀMIN discharges EVERY pending adjudication up front — all pre-queued N-rulings,
    any recorded design-source questions, anything a lane would otherwise stall on mid-night
    — each logged as ADJUDICATION-<n> with rationale and reversibility note, BEFORE builders
    dispatch. A lane discovering a missing ruling at 3am is a scheduling failure, not fate.
(d) If the ledger's NEXT-ACTION calls for a deploy of current main, do it now with full
    verify discipline and Verifier acceptance before anything else builds on top.
Stand up the swarm per NIGHT_RUN §A: yourself (Opus, docs/ledger only), PARĪKṢAKA the
Verifier (Opus, never writes code, accepts every item against LIVE production post-deploy on
BOTH canonical charts, four dispositions, no "passed with caveats"), ANTARYĀMIN the
Adjudicator (Opus, max effort — rules every would-be-human question from portal + śāstra
knowledge; it may NEVER alter a FROZEN contract, untouchable, or rail — where only that
would unblock, it takes the no-contract-change conservative path or parks; N5
lock-granularity stays CONSERVATIVE-DEFAULT: chart-level lock, no orchestrator change,
recorded reversible), and Sonnet builders — one lane each, each in its own
.worktrees/shad-darshana-<lane>, BRANCHED OFF origin/shad-darshana/integration (NEVER
origin/main — §B.1), never spawned from inside a worktree. You hold the model/effort dial:
escalate per §B.3 (Opus+high for W2/W4/W2G/W3K design, numerics, parihāra review, divergence
classification, any lane after 2 failed verify cycles) without asking.
PARALLELISM IS FRONTIER-RELATIVE, not hardcoded: from the ledger + §C, dispatch EVERY lane
whose prerequisites are already met, concurrently — e.g. W3 computations needing only
L1/ephemeris run beside W2's integration core; W2G starts the moment its N-rulings are
recorded; W3K the moment W2's clocks exist; W4's design pass (5a) the moment items 36+41
land (§C Phase 4/5 boundary — W4 needs only items 20+36+41, nothing from W2G/W3K).
Sequential only where §C marks it: envelope spine, W2 integration core, W5 registry
lockstep, all of W6.
Hard gates you may not soften: specificity gate HARD from W2; Circularity-Guard
LEL-invariance from W1; skill score published both charts at W2 (first score = CI baseline);
the canned W4 Mode-2 fixture discharged exactly; item-44 authority census 100%; W5 planner
primitives verified by REAL MARSYS-JIS MCP calls; W6 dark-corpus >= 95% both charts, every
residual classified. DATA-HONESTY RAIL for anything newly seeded (priors, constants, rule
tables — e.g. the N_e lifetime-count priors): every value enters as a cited, versioned L0
row labeled structural_prior; a number without a defensible source is a build error, not a
gap-filler — honest-empty beats fabricated-full, always. Nirmāṇa contract (brief §2.5):
every new writer lands WITH its asset_registry seed row + chart-scoped count_sql in the same
PR; bg_* builds only via explicit super-admin L0 trigger, built in production BEFORE the
first per-chart build that needs it; ka_kshetra never lists mi_bhara in depends_on (weights
flow by version pin); LEL-triggered recalibration is a tracked scoped build run. Strangler
discipline: build beside, cut over classified, retire one-at-a-time at zero consumers after
duplicate-copy audit; legacy data never destroyed.
MERGE/DEPLOY MECHANICS (repo = Marsys-Technologies/Madhav — the old amonty84 path is DEAD,
never hardcode it): lane PRs → base shad-darshana/integration, merge on green (if gh
auto-merge errors with "clean status" on this unprotected branch, merge directly — same
discipline, different verb). ONE deploy per wave gate: shad-darshana/integration → main via
one deliberate Conductor-opened PR, which rides main's MERGE QUEUE (§B.2a) — a queued-green
PR can take 5–60 minutes to merge; that is normal, never stuck, never bypassed. Then: real
authenticated verify → canary → cutover → confirm traffic tracks LATEST → Verifier live
acceptance → worktree cleanup → ledger. When polling checks anywhere, a check is done ONLY
when status=COMPLETED — a null conclusion is pending, not passed. integration running ahead
of production between gates is normal and expected. Untouchables: kala_gochara_windows data,
build_substep_progress rows for asset_id='ka_gochara_sweep' (scoped 2026-08-06, native ruling —
see ledger; other assets' substep rows are ordinary rebuildable bookkeeping), the sealed
evaluator harness, root CLAUDECODE_BRIEF.md.
At ~7.5h: stop opening lanes, land-or-park everything cleanly (no half-merged state), final
deploy if a gate closed, update the ledger (statuses, evidence, skill scoreboard,
ADJUDICATION log, NEXT-ACTION), remove worktrees, verify main == production (or record the
honest integration-ahead-of-main state if no gate closed), and append the MORNING REPORT:
gates closed, items dispositioned, rulings made, defects found+fixed, parks + reasons,
single next action. Truth over completion — PARKED-HONEST with evidence beats a false
close. COMPLETE only when every brief §3 gate is VERIFIED-CLOSED and
SHAD_DARSHANA_REPORT_v1_0.md is merged. Begin.
```
