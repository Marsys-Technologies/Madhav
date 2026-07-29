---
artifact: SHAD_DARSHANA_BRIEF (The Six Views — Implementation Campaign)
canonical_id: SHAD_DARSHANA_BRIEF
version: 1.0
status: SUPERSEDED-BY-v2.0 (2026-07-29) — retained in place as a historical record per the
  ONGOING_HYGIENE_POLICIES §A archival retain-in-place rule. **NO SESSION EXECUTES FROM THIS
  FILE.** The campaign had not started when v2.0 was cut (no state ledger existed), so this is
  a clean pre-kickoff supersession, not a mid-flight swap. The live execution contract is
  `SHAD_DARSHANA_BRIEF_v2_0.md`, which absorbs this brief's waves and registry items 1–35 and
  extends them with items 36–44, the E-series E1–E8, and the round-3 design authority
  `KALA_SUPREME_ELEVATION_v1_0.md` (at v1.1).
superseded_by: briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md
created: 2026-07-27
author: Fable (Cowork planning session)
specification:
  - briefs/kala_elevation/KALA_SIX_VIEWS_DESIGN_v1_0.md   (RATIFIED — the six views, laws, tools)
  - briefs/kala_elevation/KALA_SIX_VIEWS_DESIGN_v2_0.md   (RATIFIED — reconciliation stack,
    salience rebuild, Adṛṣṭa/UPĀYA-SETU, presentation contract, master algorithm, §H strangler
    ruling, §I build registry — ALL TIERS APPROVED by the native)
  - briefs/kala_elevation/KALA_LAYER_STOCKTAKE_AND_ELEVATION_v1_0.md  (inventory + overlap map)
  THE DESIGN DOCS ARE THE SPEC. This brief is the execution contract only — where the designs
  say WHAT, this says WHO/WHEN/PROVE-IT. On any conflict, v2.0 > v1.0 > stocktake > this brief.
mode: >
  FULLY AUTONOMOUS · MULTI-SESSION campaign driven by ONE re-pasteable kickoff prompt (§D).
  Each session: Conductor (Opus) reads the STATE LEDGER, executes the next wave(s) within its
  ~8h cap, updates the ledger, closes cleanly. Parallel Sonnet builders (Opus only where §4
  flags or after 2 failed verify cycles) · ONE Opus Verifier per session that never writes
  code · Dvārapāla duty on the Conductor · no human gates · PR + auto-merge only · explicit
  deploy via the canary pipeline · PRIME RULE: truth over completion.
state_ledger: >
  briefs/kala_elevation/SHAD_DARSHANA_STATE.md — created by the first session (W0.1), updated
  at every wave boundary and session close. Schema: per-wave status
  (NOT-STARTED | IN-PROGRESS <session-id, worktrees> | VERIFIED-CLOSED <evidence> |
  PARKED-HONEST <reason, release condition>), per-build-item (§I registry ids 1..35) status,
  deployed revisions, open PRs, and a NEXT-ACTION line. Every fresh session's first act after
  reading the spec is reading this ledger; every session's last act is updating it. The ledger
  is the campaign's memory — a session that doesn't update it has not closed.
---

# ṢAḌ-DARŚANA — building the six temporal views

## §0 — Mission
Implement the ratified six-views re-architecture of the Kāla layer end-to-end: six retrieval
tools + `kala_upaya_get`, the consolidated temporal field beneath them, all approved build-
registry items (v1.0 §7 items 1–21 + v2.0 §I items 22–35, ALL tiers), planner integration
verified live over MCP, and the strangler-fig migration through to old-surface retirement —
across as many autonomous sessions as needed, resumable from the state ledger at every point.

## §1 — Waves (the execution order; each wave independently closeable)

**W0 · Foundation (first session, blocking).**
0.1 Create `SHAD_DARSHANA_STATE.md` (schema above), seed all waves NOT-STARTED.
0.2 Preflight: repo clean, canonical charts healthy, canary pipeline green (the IAM grant on
    `mcp-canary-key` was flagged to the native — if it is still missing, deploys use the
    pre-canary discipline manually and the ledger notes it; do NOT block the campaign).
0.3 **The uniform envelope** (v1.0 §0.2) as a shared lib: reading (hardFloored) + headline +
    currents + coverage + calibration_state + drill + budget. One implementation, six consumers.
0.4 **Six facades + `kala_upaya_get` stub** over EXISTING substrate (v2.0 §H.1): `kala_now_get`,
    `kala_ahead_get`, `kala_elect_get`, `kala_story_get`, `kala_priority_get`,
    `kala_explain_get`. Each facade composes today's best available data into the envelope —
    imperfect content behind a stable contract. Legacy temporal tools gain deprecation notes
    pointing at their successor view (aliases stay live; nothing retired yet).
0.5 STORY facade fixes the parva duplication at the serving layer immediately (dedup by
    span+level — the visible embarrassment goes first).
**Gate W0:** all seven tools live on production, envelope-conformant, naive tool_search
surfaces them by name; sealed-harness regression shows no loss vs baseline.

**W1 · Tier-A serving joins (cheap, high-yield; parallel builders).**
Items (registry #): recurrence ladder (1) · Sūkṣma spine w/ uncertainty intervals — intervals
mandatory below PD (24-lite: propagation formula first, full budget later) · dual-reference
gochara (8) · daśā-lord transit condition, current+forward (28) · intra-day election joins:
panchanga blocks, gulika kālam, diśā-śūla (32) · chandrāṣṭama/horā/janma-resonance flags (29) ·
mudda join (30) · per-chapter LEL pinning + retrodiction fit (10).
**Gate W1:** each item live-verified through its view; NOW/AHEAD/ELECT/STORY visibly richer on
both canonical charts; no regression.

**W2 · The field + the honesty machinery (the heavy central wave; Opus design).**
`kala_field` built BESIDE existing writers (v2.0 §H.2): the ten-stage pipeline (v2.0 §G) —
kinematics w/ dwell-time weighting, symbolization, promise graph w/ alternate routings, clocks
w/ applicability+competence gates, field assembly w/ provenance edges persisted (11), the
**synthetic reference cohort** (22), **circular-shift null calibration** (23), **full
uncertainty budget** (24), **salience vector + submodular selection** (25), obstruction as
dated signed suppression, `kala_timeline_spec v1` presentation contract (27).
**Gate W2:** field deterministic (hash-replay test); cohort base-rates served; null exceedance
on every window; salience vector visible in PRIORITIZE; presentation block renders a valid
spec; old writers UNTOUCHED and still serving (strangler discipline).

**W3 · New computations (parallel builders over the field).**
Daśā-sandhi calendar (1✳ compute half) · sky-event calendar: ingresses, stations, eclipse-to-
natal contacts, returns, Guru-Śani double-transit (3) · moorti-nirṇaya (4) · vedha application
+ REAL Sarvatobhadra grid data (5, closes R-19) · activity-rule muhūrta tables (6) ·
muhūrta-lagna computation (7) · health/adverse event class in the sweep grammar (9, closes
DP-4) · Tithi-Praveśa (13) · janma-anchored election rules (14) · rarity axis (15) ·
Kota-Chakra (16) · Sudarśana-Chakra (17) · period-echo mining (31) · absence-of-expected
detector (33) · contrastive EXPLAIN (34).
**Gate W3:** each computation two-pass verified on both canonical charts, served through its
view(s), citation-carrying; the health class specifically re-tested against the S4-05 scenario.

**W4 · UPĀYA-SETU (26; the flagship asset; Opus design).**
PACT-link diagnosis · alternate-routing search over the promise graph · intervention ledger
with efficacy tiers (`classically_attested`/`traditional`/`speculative_extension`) ·
least-opposed-window ELECT integration · praśna decision-gate · auto-filed falsifiable
prospective entries. Serves through `kala_upaya_get` + intervention pointers on AHEAD windows.
**Gate W4:** for a weakly-promised event class on 482012f1, the tool returns a correct
diagnosis of the failing link + a non-empty, honestly-tiered intervention ledger + a filed
prospective entry; the "pressure without delivery" label verified on an un-promised window.

**W5 · Planner integration (rides VIDHI-PŪRṆATĀ E-1's lane; reconcile, don't duplicate).**
Six Vidhi primitives + `upaya_read` · intent routes ("when should I…"→ELECT, "why…"→EXPLAIN) ·
machine-band defaults: every domain deepdive compiles NOW+AHEAD+PRIORITIZE; undertaking→ELECT;
biography→STORY; every row id pre-authorizes one EXPLAIN hop · the three-copy registry trap
(canonical → codegen mirror → DB seed, parity test + CI gate) handled per the VIDHI brief §1.
**NATIVE'S HARD GATE: every primitive and route verified by REAL MARSYS-JIS MCP CALLS from the
implementing session** — call → response shape → floor presence — recorded in the ledger. Unit
tests alone do NOT satisfy this gate.
**Gate W5:** live-MCP verification table complete for all 7 primitives × representative
intents; naive "tell me about my money" demonstrably compiles NOW+AHEAD+PRIORITIZE floors.

**W6 · Cutover + retirement (strangler completion; v2.0 §H.3–5).**
Per-view cutover from legacy substrate to the field with the equivalence discipline: legacy
surface = ground-truth corpus, every divergence classified (legacy-artifact / new-capability /
new-bug) with evidence, NO divergence ships unclassified. Then retirement: legacy middle-layer
writers (sangam/yojaka/kalasutra/taranga) and the 14 legacy serving tools retired ONE at a
time, each only at zero consumers (catalog census proof). Duplicate-copy audit BEFORE each
retirement (the thrice-proven "fix landed in one of two copies" class — grep for twin
implementations; one canonical registration per tool, asserted by test). Clock substrates
(chart_dashas, sweep corpus) are KEEPERS. Final: full regression battery + sealed harness +
preserve-list sweep + dark-corpus re-measure (full 21 questions, both charts) + close report
`SHAD_DARSHANA_REPORT_v1_0.md` + ledger archived COMPLETE.
**Gate W6:** production serves ONLY the six+one tools (plus documented aliases in final
deprecation cycle); zero unclassified divergences; dark-corpus bright% materially above the
PARIŚODHANA baseline; every §I registry item dispositioned.

## §2 — What each session does (the resumability contract)
1. Read spec docs → read `SHAD_DARSHANA_STATE.md` → announce the wave(s) this session will
   attempt (respect wave order; a wave may span sessions; parallel builders WITHIN a wave).
2. Execute with builders in `.worktrees/shad-darshana-*`; Verifier accepts each item against
   live production post-deploy; four dispositions, no "passed with caveats."
3. Before the session cap: land or park cleanly (no half-merged state), update the ledger
   (statuses, evidence links, NEXT-ACTION), clean worktrees, confirm production == main.
   A session that cannot finish a gate marks the wave IN-PROGRESS with exact resumption notes.

## §3 — Rails (standing + campaign-specific)
Untouchables: `kala_gochara_windows` data (until W6's classified cutover replaces serving —
the DATA is never destroyed; 2.0-style rebuilds only under their own ratified wave),
`build_substep_progress`, the sealed evaluator harness (run, never modify) · PR + auto-merge
only; main is protected · deploy via merged-main → real authenticated verify → canary →
cutover → confirm traffic tracks LATEST (pipeline preferred; manual discipline if IAM grant
still pending) · registration-time gates need real-SDK integration tests, never mocks ·
coverage-gates must be tested against their own coverage (the single-fixture lesson) ·
duplicate-copy audit before every fix/retirement · never spawn a builder from inside a
worktree · merge-state asserted separately from verification state · one canonical domain
vocabulary, shared constant + CI diff vs live CHECK constraints (the Kiran rail) · fresh-chart
CI smoke stays green · annotate registers append-only · no fabrication; honest-empty always ·
LEL entries native-only · LAW ZERO from the design: no claim served at a precision the input
uncertainty cannot support.

## §4 — Model & effort policy
Sonnet default everywhere. Opus: Conductor, Verifier, W2 field design, W4 UPĀYA-SETU design,
and any builder after 2 failed verify cycles. Effort: high only for W2/W4 design and final W6
battery; low for W1 joins and mechanical work. Output/cost balance per the standing doctrine —
where this brief + the design docs name the file, the formula, and the gate, the work needs
execution, not effort.

## §D — Kickoff prompt (single paste; RE-PASTEABLE — same prompt every session until COMPLETE)

```
You are the CONDUCTOR of ṢAḌ-DARŚANA (Six Views Implementation), FULLY AUTONOMOUS, no human
available. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v1_0.md —
    the execution contract; its §1 waves, §2 session protocol, and §3 rails BIND you;
(2) briefs/kala_elevation/KALA_SIX_VIEWS_DESIGN_v2_0.md then KALA_SIX_VIEWS_DESIGN_v1_0.md —
    THE SPEC (ratified; all build tiers approved; v2.0 wins conflicts);
(3) briefs/kala_elevation/SHAD_DARSHANA_STATE.md — the campaign state ledger. If it does not
    exist, this is the FIRST session: create it per the brief frontmatter schema and begin
    W0. Otherwise resume exactly from its NEXT-ACTION line, respecting wave order.
Execute as many wave-gates as fit safely in this session (~8h cap): parallel Sonnet builders
in .worktrees/shad-darshana-*, Opus only where brief §4 flags or after 2 failed verify
cycles. ONE Opus Verifier that never writes code accepts every item against LIVE production
post-deploy — four dispositions, no "passed with caveats". W5's hard gate: planner primitives
verified by REAL MARSYS-JIS MCP calls, recorded in the ledger — unit tests do not satisfy it.
Strangler discipline throughout: build beside, cut over with classified equivalence evidence,
retire only at zero consumers after a duplicate-copy audit; legacy data never destroyed.
PR + auto-merge only; deploy via merged-main → real authenticated verify → canary → cutover,
traffic tracking LATEST. Untouchables: kala_gochara_windows data, build_substep_progress, the
sealed evaluator harness. Never touch root CLAUDECODE_BRIEF.md. Before the cap: land or park
cleanly, update SHAD_DARSHANA_STATE.md (statuses, evidence, NEXT-ACTION), clean worktrees,
confirm production == main. The campaign is COMPLETE only when every §1 gate is
VERIFIED-CLOSED and SHAD_DARSHANA_REPORT_v1_0.md is merged. Truth over completion —
PARKED-HONEST with evidence beats a false close. Begin.
```
