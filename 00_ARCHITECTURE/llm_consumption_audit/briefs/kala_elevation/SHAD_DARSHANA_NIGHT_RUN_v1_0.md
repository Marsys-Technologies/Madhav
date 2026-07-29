---
artifact: SHAD_DARSHANA_NIGHT_RUN (Autonomous Overnight Execution Protocol)
canonical_id: SHAD_DARSHANA_NIGHT_RUN
version: 1.0
status: READY-FOR-EXECUTION — the orchestration layer over SHAD_DARSHANA_BRIEF_v2_0.
  The BRIEF owns WHAT/GATES/RAILS; THIS doc owns WHO/WHEN/HOW-PARALLEL. On any conflict about
  scope or acceptance, the brief wins; on any conflict about orchestration, this doc wins.
created: 2026-07-29
author: Fable (elevation session with the native)
mode: >
  FULLY AUTONOMOUS OVERNIGHT, MULTI-NIGHT. One re-pasteable kickoff prompt (§D below — it
  SUPERSEDES brief §D for autonomous night runs). Each night: the Conductor reads the ledger,
  executes the §C sequence from wherever NEXT-ACTION points, lands-or-parks cleanly, deploys,
  reconciles main == production, writes the morning report. The campaign is COMPLETE when
  every brief §3 gate is VERIFIED-CLOSED — expect multiple nights; the ledger is the memory.
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

**B.1 Isolation & merge:** every builder in `.worktrees/shad-darshana-<lane>` (Conductor
creates; never spawned from inside another worktree). Small PRs, auto-merge on green (main is
branch-protected, 4 checks). Conductor runs the merge train — rebase-conflict lanes are
serialized by the Conductor, never resolved by force-push.

**B.2 Deploy cadence:** one deploy per wave-gate (not per PR): merged main → real
authenticated call → canary (manual discipline if the IAM grant is still pending) → cutover →
**confirm traffic tracks LATEST** → Verifier post-deploy acceptance → worktree cleanup →
ledger. Main == production is asserted at every gate close AND at night end, whichever comes
first.

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
**Track D — W3 computations (6–8 Sonnet lanes over the field):** sandhi-full (1) + sky-
calendar joins (3) ∥ moorti (4) + vedha/Sarvatobhadra (5, closes R-19) ∥ activity tables (6)
+ muhūrta-lagna (7) + janma rules (14) ∥ health class (9, S4-05 re-test) + Kota (16) +
Sudarśana (17, post-audit) ∥ Tithi-Praveśa (13) + period-echo (31) ∥ **lattice engine + Factor
Census (36+41, Opus)** + ELECT depth (38-full) + paddhati schema (37-part) ∥ absence (33) +
contrastive (34) ∥ E6-full view deepenings.
**Track E — W2G GOCHARA-2.0 (2 lanes, Opus numerics), starts when ANTARYĀMIN's N1–N5 ledger
block is complete (N5 = conservative default):** V1–V6 validations → 2.0 writer beside v1 →
equivalence corpus, every divergence classified. Parks honest if any N-ruling forces it;
NOTHING downstream requires sub-day (the day-grade-first rail).
**Track F — W3K KP engine (2 lanes, Opus doctrine), starts on W2's clock machinery:**
existing-substrate inventory FIRST (`ganita_kp_cusps_get`) → sub-lord substrate → cusps/
significators/ruling planets → KP window stream as independent clock → school-tagged serving.
**[GATES W3 · W3K · W2G — each deploys and verifies independently as it completes]**

**PHASE 5 — W4, the intervention flagship (Opus design first, then 3 lanes).**
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
for autonomous night runs)

```
You are the CONDUCTOR of the ṢAḌ-DARŚANA NIGHT RUN — fully autonomous, overnight, no human
until morning. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_NIGHT_RUN_v1_0.md
    — YOUR orchestration contract: §A roster, §B mechanics, §C sequence bind you;
(2) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md —
    the execution contract: §1 inventory, §2.5 Nirmāṇa contract, §3 gates, §7 rails bind you;
(3) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_SUPREME_ELEVATION_v1_0.md
    (v1.2) then KALA_SIX_VIEWS_DESIGN_v2_0.md then v1_0.md — the spec (elevation wins);
(4) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_STATE.md — the
    ledger. Absent → first night: create per brief §6, start §C Phase 0. Present → resume
    exactly from NEXT-ACTION.
Stand up the swarm per NIGHT_RUN §A: yourself (Opus, docs/ledger only), PARĪKṢAKA the
Verifier (Opus, never writes code, accepts every item against LIVE production post-deploy on
BOTH canonical charts, four dispositions, no "passed with caveats"), ANTARYĀMIN the
Adjudicator (Opus, max effort — rules every would-be-human question from portal + śāstra
knowledge, logging ADJUDICATION-<n> entries; it may NEVER alter a FROZEN contract,
untouchable, or rail — where only that would unblock, it takes the no-contract-change
conservative path or parks; N5 lock-granularity is ruled CONSERVATIVE-DEFAULT: chart-level
lock stays, no orchestrator change, recorded reversible), and Sonnet builders — one lane
each, each in its own .worktrees/shad-darshana-<lane>, never spawned from inside a worktree.
You hold the model/effort dial: escalate per NIGHT_RUN §B.3 (Opus+high for W2/W4/W2G/W3K
design, numerics, parihāra review, divergence classification, and any lane after 2 failed
verify cycles) without asking.
Execute NIGHT_RUN §C maximally parallel: while W1 join lanes run, the L0 substrate lanes
(bg_cohort, bg_sky_calendar, bg_muhurta_lattice, bg_parihara_rules) and the W2 Opus design
lane run beside them; W2G and W3K run beside W3 once their preconditions exist; sequential
only where §C marks it (envelope spine, W2 integration, W5 registry lockstep, all of W6).
Hard gates you may not soften: specificity gate HARD from W2; Circularity-Guard
LEL-invariance from W1; skill score published both charts at W2 (first score = CI baseline);
the canned W4 Mode-2 fixture discharged exactly; item-44 authority census 100%; W5 planner
primitives verified by REAL MARSYS-JIS MCP calls; W6 dark-corpus >= 95% both charts, every
residual classified. Nirmāṇa contract (brief §2.5): every new writer lands WITH its
asset_registry seed row + chart-scoped count_sql in the same PR; bg_* builds only via
explicit super-admin L0 trigger, built in production BEFORE the first per-chart build that
needs it; ka_kshetra never lists mi_bhara in depends_on (weights flow by version pin);
LEL-triggered recalibration is a tracked scoped build run. Strangler discipline: build
beside, cut over classified, retire one-at-a-time at zero consumers after duplicate-copy
audit; legacy data never destroyed. PR + auto-merge only; one deploy per wave gate:
merged-main -> real authenticated verify -> canary -> cutover -> confirm traffic tracks
LATEST -> Verifier live acceptance -> worktree cleanup -> ledger. Untouchables:
kala_gochara_windows data, build_substep_progress, the sealed evaluator harness, root
CLAUDECODE_BRIEF.md. At ~7.5h: stop opening lanes, land-or-park everything cleanly, final
deploy if a gate closed, update the ledger (statuses, evidence, skill scoreboard,
ADJUDICATION log, NEXT-ACTION), remove worktrees, verify main == production, and append the
MORNING REPORT (gates closed, items dispositioned, rulings made, parks + reasons, single
next action). Truth over completion — PARKED-HONEST with evidence beats a false close.
COMPLETE only when every brief §3 gate is VERIFIED-CLOSED and SHAD_DARSHANA_REPORT_v1_0.md
is merged. Begin.
```
