---
artifact: KALA_TRANSFORMATION_HANDOFF
canonical_id: KALA_HANDOFF_v1_0
version: 1.0
status: HANDOFF — the single self-contained context document for the Kāla-layer transformation.
  Take this to Claude Code for extensive pre-implementation work. Nothing else is strictly
  required to understand the mission; the three SPEC docs below are the deep authority for
  algorithms and per-view detail.
created: 2026-07-27
author: Fable (Cowork planning session), consolidating the full session context
audience: A Claude Code session (or human engineer) with ZERO memory of the planning
  conversation. Assume the reader knows Vedic astrology and software, but knows nothing about
  this codebase's history, culture, or the specific incidents that shaped its rules.
authority_order: KALA_SIX_VIEWS_DESIGN_v2_0 > _v1_0 > KALA_LAYER_STOCKTAKE > SHAD_DARSHANA_BRIEF
  > this handoff. This handoff is the ORIENTATION and the CONNECTIVE CONTEXT; the design docs
  are the SPEC; the campaign brief is the EXECUTION contract.
spec_documents (all in 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/):
  - KALA_SIX_VIEWS_DESIGN_v1_0.md      — the six views, the five reconciliation laws, tool names
  - KALA_SIX_VIEWS_DESIGN_v2_0.md      — reconciliation stack, salience rebuild, Adṛṣṭa/UPĀYA-
                                          SETU, presentation contract, 10-stage master algorithm,
                                          architecture ruling, build registry §I (items 22–35)
  - KALA_LAYER_STOCKTAKE_AND_ELEVATION_v1_0.md — the as-is inventory + redundancy map
  - SHAD_DARSHANA_BRIEF_v1_0.md        — the multi-session campaign (waves W0–W6, state ledger)
---

# Kāla-Layer Transformation — Master Handoff

> **One paragraph.** The MARSYS-JIS platform is a deterministic Vedic-astrology intelligence
> system. Its Layer 3 ("Kāla," time) answers "WHEN?" — but it was built five times by five
> campaigns under five names, computes nearly everything a world-class timing instrument needs,
> and serves a small fraction of it through fourteen overlapping tools that sometimes disagree.
> The transformation replaces that with **six clean retrieval views** (NOW, AHEAD, ELECT, STORY,
> PRIORITIZE, EXPLAIN) plus an intervention engine (UPĀYA-SETU), all serving from **one
> consolidated temporal field**, reconciled by principled astrological/astronomical/statistical
> laws, and reachable by the planner. This document is everything a builder needs to understand
> WHY before touching HOW.

---

## PART I — ORIENTATION: the program you are joining

### I.1 What MARSYS-JIS is (the six layers)
A layered pipeline; each layer is a set of "writers" (Python, in the orchestrator) that compute
and persist facts, plus MCP "tools" (TypeScript) that serve them to a consuming LLM.
- **L0 Brahmagyan** — reference/ephemeris substrate (classical constants, Swiss-Ephemeris).
- **L1 Gaṇita** — computed chart facts (positions, dignities, shaḍbala, vargas, ashtakavarga,
  dashas, panchanga — thousands of fact families per chart).
- **L2 Bodha** — synthesis: signals (MSR), causal graph (CGM), convergence, discoveries,
  remedies. The "what does it mean" layer.
- **L3 Kāla** — timing. **This is what you are transforming.**
- **L4 Phala** — outcomes/prediction/mitigation anchored to L3 windows.
- **L5 Mīmāṃsā** — calibration: the falsifiable ledger that (eventually) learns from real
  outcomes. Currently sealed in "structural" mode: it has never ingested an outcome, so every
  prediction is a `structural_prior`, never yet `calibrated`.

The consuming LLM (an agent like you, reached over the `MARSYS-JIS` MCP connector) receives a
user's question, calls tools, and composes the answer. **The entire product's value depends on
the right facts reaching that LLM in a form it can speak from.** Most of this program's history
is about closing the gap between "computed" and "served-and-reflected."

### I.2 The environment (concrete facts you will need)
- **Repo root** (on the operator's machine, via the device bridge): the `Madhav/` folder.
  Key trees:
  - `platform/python-sidecar/pipeline/orchestrator/writers/` — the L1–L5 writers (`ka_*` = Kāla).
  - `platform/python-sidecar/pipeline/services/` and `.../orchestrator/writers/services/` —
    some writers are thin `@register` shims over a service module (e.g. ka_dasha_kala,
    ka_muhurta_seva). Confirm each writer's real home before editing.
  - `platform/migrations/` — 155+ SQL migrations, applied in number order. Relevant recent:
    **386** (canonical_domain_normalization — the domain vocabulary CHECK constraint that the
    Kiran drift bug violates), **440** (vidhi_registry_schema — the planner floor seed),
    **454/455** (kala_activation cardinality), **459** (gochara_resonance_map), **460/461**
    (kala_gochara_windows + continuity), **462/463** (vidhi_purnata seed + gate fix).
  - `platform-mcp/src/tools/` — the MCP serving layer (TypeScript). `registry_bridge.ts` is the
    central registration; `register_p1_*.ts`, `register_p2_dasha_lord.ts`, `kala_timeline.ts`,
    `muhurta_finder.ts` register temporal tools. `intent_scope_classifier.ts` + the vidhi
    registry drive the planner.
  - `platform/src/lib/vidhi/registry_data.ts` — the planner's floor registry (CANONICAL copy).
    **Three-copy trap:** a generated mirror at `platform-mcp/src/resources/vidhi/registry_data.ts`
    (never hand-edit; `npm run codegen:vidhi`) and the migration-440 DB seed must stay in
    lockstep; parity is enforced by `vidhi_codegen_parity.test.ts`.
- **Deploy targets:** two Cloud Run services in project `madhav-astrology`, region `asia-south1`:
  **`amjis-mcp`** (the MCP server the connector hits) and **`amjis-web`**. Deploy discipline:
  build from merged `main` → verify with a REAL authenticated call → canary → cutover → confirm
  traffic tracks LATEST (never a pinned revision). A canary pipeline exists but needs an IAM
  grant to run (see Open Items).
- **git:** `main` is branch-protected (4 required checks, `enforce_admins`); merges are PR +
  auto-merge only — a direct push is rejected (GH006). Worktrees live in `.worktrees/`.
- **Canonical charts** (the fixtures every verification runs against):
  - `482012f1-710e-4a25-994a-93821f5871aa` — **Abhisek** (the native/operator). Aries lagna
    12.43°; Saturn exalted in Libra 7th (dominant graha, fires Śaśa Mahāpuruṣa yoga, rules 10th
    & 11th); Moon Aquarius 11th; Sun+Mercury Capricorn 10th (Budha-Āditya); Venus weakest graha,
    debilitated in D9; Rahu exalted Taurus 2nd; Mars neutral Libra 7th (debilitated in D2/D6,
    NOT D1 — a common misread). Currently Mercury MD → Saturn AD, to Aug 2027; then Ketu MD
    2027–34; Venus MD 2034–54.
  - `1c826d5a-41cb-4450-b4dc-59d440e5f75a` — **Abhinandan** (second canonical / operator-E2E
    chart). Historically under-covered — verifications sometimes ran only on Abhisek; this
    campaign holds BOTH to identical coverage.
  - `acdf0d66-…` Arunima, `cb73cd3d-…` Kiran — additional charts; Kiran is a fresh post-migration-386
    build and is where the domain-drift bug surfaces (see I.4).
- **Ayanāṁśa:** operational default **Lahiri (chitrapaksha)**; charts may carry multiple
  ayanāṁśas. Cross-ayanāṁśa behavior matters (see the reconciliation stack).

### I.3 The culture you are inheriting (read this or you will trip the same wires)
This codebase has survived a long arc of remediation campaigns (names you will see in ledgers:
Elevation, UAT-DARPANA, SATYA-ŚEṢA, PŪRṆA-VIRĀMA, ŚODHANA/-ŚEṢA, SAMĀPANA, ŚUDDHA-VĀCA,
PARIŚODHANA). The operating doctrine that emerged, which you MUST honor:

- **Truth over completion.** A `PARKED-HONEST` disposition with evidence is a legitimate,
  respected outcome. A false "done" is the cardinal sin. Four dispositions only: VERIFIED-FIXED,
  VERIFIED-NO-DEFECT, PARKED-HONEST, FAILED-REOPENED. Never "passed with caveats."
- **A dedicated Verifier that never writes code** accepts every item against LIVE production,
  post-deploy. Nothing is "done" until it does.
- **The Offer Law (proven 4×):** any architecture that makes the correct action an *optional
  extra step* will see that step skipped by the consuming LLM. Corollary that governs this
  whole design: **completeness must be affordable or enforced** — never merely offered.
- **Honesty fields are load-bearing, not decoration.** `judgment_flags`, `trim_report`,
  `coverage`, `n_support`, `calibration_state`, `empty_reason` are why defects are detectable at
  all. Never trade them for compactness.
- **Register drift is real and measured.** PARIŚODHANA found that of ~40 "open" register items,
  **21 were already fixed and never documented** — the registers were wrong in BOTH directions.
  Hence: verify-before-fix, and annotate registers in place.

### I.4 The incident ledger — every rail below was paid for in a real failure
You will see these rules repeated as "rails." They are not bureaucracy; each traces to a
production incident. Internalize the pattern, because your work will be judged against it:
1. **Traffic-pin class (×2):** `amjis-mcp` traffic was pinned to a stale revision; "successful"
   deploys silently went nowhere while CI was green. → Rail: verify production with a real
   authenticated call; confirm traffic tracks LATEST; never trust a green badge.
2. **Mocked-SDK test:** a registration-time gate shipped a crash-loop because its test used a
   mocked SDK. → Rail: registration-time gates need real-SDK integration tests.
3. **Coverage-gate self-blindness:** a golden byte-equality gate exercised 1 of 12 fixtures and
   reported green. → Rail: a gate must be tested against its own coverage.
4. **Duplicate-copy class (×3):** a fix landed in one of two copies of the same logic
   (holistic_bundle twice, a stale duplicate registry, discovery double-registration) while
   production ran the other. → Rail: duplicate-copy audit before every fix/retirement; one
   canonical registration per tool, asserted by test.
5. **Schema-migrates-writer-doesn't (the "Kiran" class):** migration 386 rewrote the domain
   CHECK constraint; `ka_bhavishya_lekha.py` still emits the old labels (`finance`/`spiritual`
   vs canonical `wealth`/`spirituality`), crashing any post-386 chart that classifies a
   projection there — and *silently downgrading* unrecognized canonical domains to `general` on
   the non-crashing path (this is the root of the MC-026 "projections all general" defect). Both
   canonical charts predate 386, so nothing caught it. → Rail: ONE canonical domain vocabulary
   as a shared constant, CI-diffed against live CHECK constraints; a fresh-chart CI smoke that
   builds a synthetic post-migration chart end-to-end.
6. **Verifier-PASSED ≠ merged; conductor's todo ≠ agent state:** lanes sat unmerged while
   ledgers called them closed. → Rail: assert merge-state separately from verification-state;
   verify agent state directly.
7. **Spawning a builder from inside a worktree** caused isolation collisions. → Rail: never do it.

---

## PART II — THE KĀLA LAYER AS-IS (what exists today, precisely)

### II.1 The 16 writers (L3), with what each computes and its distinct value
Location: `platform/python-sidecar/pipeline/orchestrator/writers/`. (★ = value-bearing;
service-kind writers marked.)

| Writer | Table(s) | Serving tool today | Answers | Keep-value |
|---|---|---|---|---|
| `ka_dasha_kala` | `chart_dashas` (+eligibility) | `ganita_dashas_get`, `ganita_dasha_periods_get` | "what period?" (8 systems, L1–L5) | ★ the daśā clock; 536k rows; Sūkṣma depth exists but is capped ≤3 in serving |
| `ka_avadhi` | `kala_avadhi` | `kala_bundle_get` excerpt | "about this period" | ★ period dossier unit |
| `ka_jivana_parva` | `kala_jivana_parva` | `kala_life_arc_get` | "life in chapters" | ★ biographical arc; **currently emits DUPLICATE spans w/ contradictory quality labels** |
| `ka_graha_sancara` | — (self-test service) | — | transit-position self-test | infra only |
| `ka_gochara` | (K2 transit-search) | (internal) | "search transits" | engine, superseded by sweep |
| `ka_gochara_resonance` | resonance map | (feeds sweep) | "which degrees matter to this chart" | ★ the chart's antenna map |
| `ka_gochara_sweep` | **`kala_gochara_windows`** | `gochara_activation_get`, `gochara_forecast_get`, `gochara_election_avoidance_get` | "when does the sky press?" | ★★ the transit field — signed λ, shape-aware windows, DR-16 honesty, 20h materialized corpus. **UNTOUCHABLE DATA.** |
| `ka_taranga` | `kala_taranga` | `ganita_av_transit_gating_get` | "AV damp/amplify?" | ★ AV gating + kakṣyā |
| `ka_sangam` | `kala_convergence` (+`_staging`) | `kala_bundle_get` convergence | "when do currents agree?" | ★ convergence engine. **Historically held a hardcoded native-constant bug (CR-87), since fixed + guarded.** |
| `ka_yojaka` | `kala_activation` + `kala_activation_predicates` | `kala_windows_get` | "which promises activate, when?" | ★ predicate bridge; **`activation_predicted_dates_jsonb` holds the full recurrence ladder — largely UNSERVED** |
| `ka_kalasutra` | (bounded activation) | `kala_windows_get` family | "bounded dated version" | ★ deterministic date resolution |
| `ka_tulana` | (ranking overlay) | `kala_priority_ranking_get` | "what deserves attention?" | ★ triage — but salience is broken (see II.4) |
| `ka_vighnakara` | `kala_obstruction` | `kala_bundle_get` obstructions | "what blocks the promise?" | ★ the only negative-space asset; real ephemeris + panchanga; **rows carry no date range** |
| `ka_kala_darshana` | `kala_darshana` | `kala_bundle_get` snapshot | "state right now?" | ★ now-synthesis + readiness |
| `ka_bhavishya_lekha` | `kala_bhavishya` | `kala_projections_get` | "probabilistic future" | weakest asset; **the Kiran domain-drift bug lives here; MC-026 degenerate output** |
| `ka_muhurta_seva` | (panchanga-muhurta service) | `kala_muhurta_get` | "auspicious time?" | ★ election; post-fix carries tārā-bala veto notes |

Tables (migrations): `kala_convergence`(+`_staging`), `kala_gochara_windows`, `kala_obstruction`,
`kala_timeline`, `kala_avadhi`, `kala_jivana_parva`, `kala_taranga`, `kala_activation`(+predicates),
`kala_darshana`, `kala_bhavishya`. `kala_timeline` is an early-gen artifact — retirement-audit
candidate. `kala_convergence_staging` persists beside its target — retire post-consolidation.

**Adjacent surfaces consumed as "temporal" but owned elsewhere:** `ganita_sade_sati_get` (L1),
`ganita_tajaka_get` (L1 annual/Varṣaphala), `panchanga_*` L1 daily facts, `pact_query`
ACTIVATION/TRIGGER stages, `phala_*` timing (L4), `standing_predictions_read` (L5).

### II.2 The five redundancy clusters (the reason for the whole project)
1. **"What is active NOW?" answered by FIVE surfaces** (gochara_activation, kala_windows(as_of),
   darshana snapshot, priority_ranking, bundle-snapshot). The consuming LLM can't tell which is
   authoritative. **This cluster caused the S4-05 trust-breaking veto:** silence from the *wrong*
   now-surface was read as an all-clear on a health question.
2. **"What's COMING?" answered by four, three under-delivering** (gochara_forecast=good;
   kala_projections=degenerate/MC-026; kala_windows forward=0 windows/R-11; phala_outlook=L4
   overlap) — while the recurrence ladder that would fix "forward" sits computed and unserved.
3. **"Pick a good time" exists three times, unreconciled** (kala_muhurta, election_avoidance,
   phala_muhurta) — the R-20 deferred unification.
4. **Period-narrative written twice** (ka_avadhi + ka_jivana_parva), with visible duplicate rows.
5. **Activation math fragmented across four writers/tables** (sangam→yojaka→kalasutra→taranga) —
   where maintenance cost and drift concentrate (the Kiran bug is a fragmentation casualty).

**Cross-layer leakage rule to enforce:** L3 owns WHEN (windows, intensity, timing); L4 owns
WHAT-THEREFORE (outcomes, mitigation, predictions that *reference L3 window ids*). Today both
emit windows.

### II.3 Known temporal defects mapped to the transformation (from the program registers)
These are the live/known issues the new architecture must resolve or explicitly carry:
- **MC-026** kala_projections degenerate (25 near-identical rows, 22/25 "general") — root is the
  ka_bhavishya domain drift (I.4 #5); AHEAD replaces it.
- **R-11 / forward windows = 0** — AHEAD serves the recurrence ladder.
- **R-20 / muhurta not unified over the signed field** — ELECT unifies.
- **R-12 / no suppression-adjusted windows** — the field's signed obstruction channel delivers it.
- **R-19 / Sarvatobhadra vedha grid has zero rows** (honest approximation flagged
  `uncited_extension`) — W3's vedha work forces the real grid.
- **DP-4 / gochara sweep has no health/adverse event class** — the data root of the only
  trust-breaking veto class; W3 builds it.
- **MC-030 / salience floors fired rare events below descriptor rows** (a fired pushkara ranks
  below a "dignity: neutral" row); **MC-022 / no domain filter**; **CR-65/81/82 / MSR ranking 93%
  noise with inert class-prior and mis-shaped tier-ceiling** — the salience rebuild (v2.0 §B)
  fixes the class at root.
- **CR-87 / hardcoded native constants in ka_sangam** — FIXED and regression-guarded; do not
  reintroduce chart-specific constants into shared engine code (a forbidden-token test enforces).
- **LC-5 / chart 1c826d5a gochara sweep staleness** — second-chart parity item.

### II.4 Why salience specifically is broken (you will rebuild it — understand the root)
Today salience is a single opaque scalar composed from unexamined factors. Measured
consequences: descriptor rows (dignity=neutral) outrank fired rare events (MC-030); wealth
queries return character rows (MC-022); one signal type fills 14 of 15 served rows (CR-65)
because the class-prior term is literally `1.0` (CR-81, inert) and the tier-ceiling is mis-shaped
(CR-82). The v2.0 §B rebuild replaces the scalar with a **five-factor served vector**
(informativeness, consequence, relevance, reliability, actionability) + **submodular top-K
selection** (coverage of independent information, not top-K-by-score). This is a first-principles
rebuild, not a patch — read v2.0 §B in full before touching ranking.

---

## PART III — THE TARGET ARCHITECTURE (what you are building)

> The deep spec is in the two design docs. This is the orientation; do not implement from this
> section alone — implement from v2.0 (deepest) cross-checked against v1.0.

### III.1 The organizing idea: One Field, Two Clocks, Six Views
Declare ONE per-chart **Temporal Field**: `(chart, domain, event_class, t) → signed intensity +
provenance`, fed by two clocks (daśā from within, gochara from without) and one modulation stack
(resonance map, AV gating, obstruction, convergence). Everything user-facing becomes a **named
read-only view** of this field. Each question has exactly ONE canonical surface.

**Substrate (consolidated):** `kala_clock_dasha` (the 8-system daśā clock, kept),
`kala_clock_gochara` (sweep + resonance, absorbs ka_gochara*), `kala_field` (merges
sangam+yojaka+kalasutra+taranga into one pipeline/table — convergence, predicates, bounded
dates, AV modulation become stages/columns, not sibling tables), `kala_vighna` (obstruction as a
first-class signed-suppression channel, which also delivers suppression-adjusted windows).

**Views (the only user-facing vocabulary — six MCP tools + one capability tool):**
`kala_now_get` · `kala_ahead_get` · `kala_elect_get` · `kala_story_get` · `kala_priority_get` ·
`kala_explain_get` · `kala_upaya_get`. Names chosen for naive tool-affinity (the name is the
router — this is a direct Offer-Law countermeasure).

### III.2 The uniform envelope (every view, no exceptions)
`{ reading (2–6 sentences composed substance, hardFloored, NEVER trimmed), headline (typed
self-contained rows), currents (per-tradition agreement/dissent), coverage (attestation),
calibration_state (per row), drill (pre-authorized EXPLAIN pointers by id), budget (trim report;
prose+honesty trim-immune) }`. The `reading` is what lets the consuming LLM answer from one call;
substance buried in JSON does not reach the user (proven repeatedly).

### III.3 The reconciliation stack (v2.0 §A — the intellectual core)
Disagreement is resolved by principle, never by mathematical average, across FIVE axes:
- **Schools** (five laws, v1.0): applicability-before-aggregation; concurrence multiplies &
  dissent is served; the promise hierarchy (natal→daśā→transit) as a graded gate (see III.5);
  school-tagged currents for per-chart calibration later; a fixed uncertainty vocabulary
  (`structural_prior`/`concurrent`/`calibrated`) — never a % before calibration exists.
- **Ayanāṁśa** = physics (a precession estimate, not an opinion): pinned default + boundary-
  distance robustness on every claim + **mandatory error propagation below PD** (at Sūkṣma depth,
  birth-time+ayanāṁśa uncertainty exceeds the period length → boundaries served as INTERVALS,
  never instants; the rectification posterior plugs in). **LAW ZERO: no claim served at a
  precision the input uncertainty cannot support.**
- **Daśā systems** = jurisdiction + competence class (Vimśottarī names the actor, Chara names
  the stage — compose, don't reconcile; conditional daśās evaluated for applicability).
- **Internal surfaces** = one authority per fact class (§N.5: L1), cited via `authority_basis`,
  CI-diffed stored-vs-derived (kills the GA.1 disagreement class).
- **Statistics** = three honest instruments: the **synthetic reference cohort** (~10⁴⁺ charts →
  honest base rates), **circular-shift null calibration** (a window is "notable" only if it beats
  the chart's own time-shifted noise floor — matched-filter discipline), hierarchical shrinkage
  on outcomes (when L5 accrues).
- **Unifying instrument:** every claim carries a **robustness vector** `{ayanamsha_robust,
  birth_time_robust, system_concurrent, null_exceeding, authority_clean}`; confidence = the
  MINIMUM across dimensions, weakest named.

### III.4 Salience rebuilt (v2.0 §B) — five served factors + submodular selection. (See II.4.)

### III.5 Law 3 amended + UPĀYA-SETU (v2.0 §C) — the flagship
The promise gate becomes **graded with a named residual (Adṛṣṭa, "the unseen")** — windows over
weak/absent promise are SERVED, labeled "pressure without delivery," never suppressed (classical
warrant: BPHS remedial chapters, Praśna literature, daiva; formally identical to DR-17's
`unmodeled_variance` humility term). **UPĀYA-SETU** (`kala_upaya_get`) answers "this outcome is
unlikely for me — what would raise its likelihood, and when?": diagnose the failing PACT link →
map interventions to the link (targeted remedy / least-opposed windows / **alternate-routing
search over the chart's own promise graph** / decision-time praśna) → efficacy-tiered ledger →
auto-file a falsifiable prospective entry (self-calibrating from birth). This is a study design
that exists nowhere in the field. Serves THROUGH the views (AHEAD windows carry intervention
pointers; ELECT accepts `for_intervention`).

### III.6 The presentation contract (v2.0 §D)
One payload, three renderings: `reading` (prose, for the LLM), `compact` (chat cards, for
Pariprashna the internal chat), `presentation` (a renderer-agnostic `kala_timeline_spec v1`,
opt-in so MCP budgets don't pay for it by default). EXPLAIN ids thread through all three so a
user can click any bar and the chat answers "why?" via `kala_explain_get(id)`. This is part of
the engine, not a UI afterthought.

### III.7 The master algorithm (v2.0 §G) — the 10-stage pipeline
0 kinematics → 1 symbolization → 2 promise graph (w/ alternate routings) → 3 clocks (multi-system,
intervals below PD) → 4 field assembly (provenance edges persisted) → 5 calibrated notability
(null exceedance + robustness vector + Adṛṣṭa reserve) → 6 salience (five-factor + submodular) →
7 view projections + UPĀYA diagnosis → 8 presentation (three renderings) → 9 learning loop
(auto-filed falsifiers → L5 → per-chart per-tradition calibration). Stages 0–8 are pure functions
(hash-replay deterministic); stage 9 is the only growing state.

### III.8 Architecture ruling (v2.0 §H): strangler-fig, NOT replace-in-place
Because this codebase's signature failure is *two surfaces disagreeing while docs drift*, a
half-migrated hybrid is that failure at maximum intensity. Therefore: (1) six facades first over
existing substrate; (2) the field built BESIDE existing writers; (3) per-view cutover with
equivalence verification (legacy surface = ground-truth corpus; every divergence classified
legacy-artifact/new-capability/new-bug with evidence; NO divergence ships unclassified);
(4) retirement only at zero consumers, one writer at a time, catalog-census-proven, with a
duplicate-copy audit first; (5) the two clock substrates and the sweep corpus are KEEPERS.

---

## PART IV — THE COMPLETE BUILD REGISTRY (35 items, all approved)

The native ratified ALL tiers (A, B, C). v1.0 §7 holds items 1–21; v2.0 §I holds 22–35. Codes:
**[N]** new computation · **[J]** join/serve existing data · **[E]** engine-scale.

**Tier A (contract-required):** 1 [N] daśā-sandhi calendar · 2 [J] recurrence-ladder serving ·
3 [N] sky-event calendar (ingresses, stations, **eclipse-to-natal contacts**, **returns**
Jupiter/Saturn/nodal, **Guru-Śani double-transit**) · 4 [N] moorti-nirṇaya per ingress · 5 [J+N]
vedha application + **real Sarvatobhadra grid data (R-19)** · 6 [N] activity-specific muhūrta
rule tables · 7 [N] muhūrta-lagna computation · 8 [J] gochara dual-reference (Moon+lagna) ·
9 [N] health/adverse event class in the sweep (DP-4) · 10 [J] per-chapter LEL pinning +
retrodiction fit · 11 [N] provenance edges persisted at field-write + citation join · 12 [J]
daśā-system applicability evaluation · 22 [N] synthetic reference cohort · 23 [N] circular-shift
null calibration · 24 [N] uncertainty-budget propagation (intervals below PD + robustness vector)
· 25 [N] salience vector + submodular selection · 27 [N] `kala_timeline_spec v1` + Pariprashna
widget contract · 28 [J] daśā-lord transit-condition (current+forward).

**Tier B (differentiators):** 13 [N] Tithi-Praveśa (lunar-return annual) · 14 [N] janma-anchored
election micro-rules · 15 [J] rarity axis from cohort · 16 [N] Kota-Chakra transit fortress ·
17 [N] Sudarśana-Chakra year-wheel · 18 [E] KP sub-lord clock (CR-75; slot designed now, an
independent concurrence voice) · 26 [N] **UPĀYA-SETU** (flagship) · 29 [J] chandrāṣṭama/horā/
janma-resonance flags · 30 [J] Mudda daśā join · 31 [N] period-echo mining · 32 [J] diśā-śūla +
gulika-kālam election joins · 33 [N] absence-of-expected detector · 34 [N] contrastive EXPLAIN.

**Tier C (learning loop):** 20 [J] auto-filed prospective ledger entries (VIDHI E-2) · 21 [E]
per-tradition per-chart calibration weights (Law 4, once outcomes accrue). · 19 [E] GOCHARA-2.0
sub-day substrate — **its own separately-ratified wave (D-6), not folded here**; ELECT hour-
precision and AHEAD honest sub-day edges depend on it but the six views ship honest at ≥1-day
until it lands.

**Item 35 [gate]:** planner wiring verified LIVE via real MARSYS-JIS MCP calls (not unit tests).

**The consciously-EXCLUDED register (v2.0 §F)** — proof of exhaustiveness, each with a re-entry
condition: Pañcapakṣī, Śiva-svarodaya/breath, Aṣṭamaṅgala/Deva-praśna, Western progressions/
outers, Nadi varga-transit triggers, Lal Kitab cycles, numerology, pre-natal syzygy points
(cheap later), heliocentric, deeper AV kakṣyā sub-timing, and **Praśna-at-every-query** (reserved
to the decision-time channel deliberately, to protect the natal instrument's identity — a product
decision the native may revisit).

---

## PART V — THE IMPLEMENTATION CAMPAIGN (how it actually runs)

Full contract: `SHAD_DARSHANA_BRIEF_v1_0.md`. Summary for orientation:

- **Multi-session, one re-pasteable prompt, driven by a state ledger** (`SHAD_DARSHANA_STATE.md`).
  Each session reads the ledger, executes the next wave(s) within ~8h, updates the ledger, closes
  clean. The ledger IS the campaign's memory.
- **Seven waves:** W0 facades+envelope (six names live day one, parva-dup fixed) → W1 Tier-A
  serving joins (cheap, high-yield) → W2 the field + honesty machinery (cohort, null, uncertainty
  budget, salience — the heavy center) → W3 new computations (sandhi, sky-calendar, moorti, vedha
  +Sarvatobhadra, health class, Tithi-Praveśa, Kota, Sudarśana, echoes, absence, contrastive) →
  W4 UPĀYA-SETU → W5 planner wiring (live-MCP-verified) → W6 classified cutover + one-at-a-time
  retirement + duplicate-copy audit + full regression/harness/dark-corpus re-measure + report.
- **Swarm:** Conductor (Opus) + parallel Sonnet builders in `.worktrees/shad-darshana-*` (Opus
  for W2/W4 design or after 2 failed verify cycles) + one Opus Verifier (never writes code) +
  Dvārapāla duty on the Conductor for any would-be human gate.
- **Each wave is independently closeable and gated;** a wave may span sessions.

---

## PART VI — RAILS (absolute; each earned by an incident in I.4 or the arc)
1. Untouchable DATA: `kala_gochara_windows` rows, `build_substep_progress`, the sealed evaluator
   harness (run it, never modify its grader/prompts/list). The sweep corpus is never destroyed;
   retirement replaces *serving paths*, not data.
2. PR + auto-merge only; `main` protected; never a direct push.
3. Deploy: merged-main → real authenticated verify → canary → cutover → confirm traffic tracks
   LATEST. Green CI is not evidence of a live deploy.
4. Registration-time gates: real-SDK integration test, never a mock.
5. Coverage-gates must be tested against their own coverage.
6. Duplicate-copy audit before every fix/retirement; one canonical registration per tool, tested.
7. One canonical domain vocabulary (shared constant, CI-diffed vs live CHECK constraints); the
   fresh-chart CI smoke stays green (the Kiran class).
8. Never spawn a builder from inside a worktree.
9. Merge-state asserted separately from verification-state; verify agent state directly.
10. Registers annotated append-only; never rewrite an original observation.
11. No fabrication; honest-empty always; LEL entries are native-only.
12. **LAW ZERO:** no claim served at a precision the input uncertainty cannot support.
13. Never touch the root `CLAUDECODE_BRIEF.md` pointer while another campaign may be live.
14. Both canonical charts held to identical coverage (no single-chart verification).

---

## PART VII — OPEN ITEMS & NATIVE DECISIONS PENDING
- **IAM grant (blocks the canary pipeline):** `gcloud secrets add-iam-policy-binding
  mcp-canary-key --member="serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com"
  --role="roles/secretmanager.secretAccessor" --project=madhav-astrology`. Until run, deploys use
  the manual canary discipline (pipeline fails safely closed). Not a campaign blocker.
- **GOCHARA-SWEEP-2.0 (D-6):** separately-ratified sub-day rearchitecture (its design is
  `briefs/doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`). The six views ship honest at ≥1-day
  precision without it; ELECT hour-precision and AHEAD sub-day edges upgrade when it lands. Its
  open native decision N5 (lock granularity for intra-chart parallelism) is unresolved.
- **VIDHI-PŪRṆATĀ:** the planner-completeness wave (`briefs/vidhi_purnata/BRIEF_VIDHI_PURNATA_v1_0.md`)
  whose E-1 lane is where §V's W5 planner wiring rides. Reconcile, don't duplicate — its three-copy
  registry flow and gate are the template for W5.
- **Praśna-at-every-query:** deliberately reserved (VI.F exclusion) — a product call to revisit.
- **KP sub-lord engine (item 18):** designed slot; a full build is its own wave.
- **The ka_bhavishya domain-drift bug** (I.4 #5): noted, parked by the native's instruction, NOT
  to be worked outside its own authorization — but AHEAD supersedes ka_bhavishya, so the fix may
  arrive by replacement. Do a fleet-wide vocabulary audit as part of W-anything that touches
  writers.

## PART VIII — GLOSSARY (so nothing in this handoff is opaque)
Daśā (planetary period; MD=Mahā/major, AD=Antar, PD=Pratyantar, Sūkṣma=4th level, Prāṇa=5th) ·
Gochara (transit) · Vimśottarī (120-yr daśā, the default) · Jaimini Chara (sign-based daśā) ·
Yogini/Kalachakra/Ashtottari/Mudda/Naisargika (other daśā systems) · Ayanāṁśa (precession offset;
Lahiri = default) · Varga (divisional chart; D9=Navāṁśa, D2=Horā/wealth, D10=Daśāṃśa/career, etc.)
· Shaḍbala (six-fold planetary strength) · Ashtakavarga/AV (a benefic-point transit-strength
system; kakṣyā = its 3.75° sub-divisions) · Moorti-nirṇaya (gold/silver/copper/iron quality of a
transit by the Moon at the transit-lord's ingress) · Vedha (transit obstruction point) ·
Sarvatobhadra (a vedha grid chakra) · Sāde-Satī / Kaṇṭaka / Aṣṭama Śani (Saturn transit hardship
periods) · Tārā-bala / Chandra-bala (nakṣatra- and Moon-based day-strength; Vadha/Vipat/Pratyak =
inauspicious tārā classes) · Tājika / Varṣaphala (annual solar-return system; Muntha = a progressed
point; Mudda = its daśā) · Tithi-Praveśa (annual lunar-return chart) · Muhūrta (electional
astrology) · Praśna (horary; the asking-moment chart) · Pañcāṅga (the five daily limbs: tithi,
vara, nakṣatra, yoga, karaṇa) · Chandrāṣṭama (Moon transiting 8th from natal Moon) · Gulika/Māndi
(a shadow-point/upagraha) · Diśā-śūla (inauspicious travel direction of the day) · Kota-Chakra
(protective/danger transit fortress) · Sudarśana-Chakra (a tri-lagna rotating annual wheel) ·
KP (Krishnamurti Paddhati; sub-lord system) · Upapada/UL (a special lagna for relationships) ·
Sensitive degrees (puṣkara [auspicious], gaṇḍānta [junction-danger], mṛtyu-bhāga [death-degree],
64th navāṁśa, 22nd drekkāṇa) · PACT (the promise→activation→confirmation→trigger serving grammar) ·
Adṛṣṭa (the unseen; the reserved probability for un-promised events) · Upāya (remedy) · LEL (Life
Event Log; the native's 57 dated life events, used for retrodiction/calibration; native-only) ·
MSR/CGM/Bodha (L2 synthesis surfaces) · Dvārapāla (the gatekeeper/escalation agent role) ·
"structural_prior/concurrent/calibrated" (the three honesty tiers) · λ_e (the signed intensity
function the field integrates).

---

## PART IX — SECOND-PASS COMPLETENESS SWEEP (added deliberately, per the native's instruction)
A re-read of everything above surfaced these items that a builder could otherwise miss. They are
recorded here rather than silently assumed:

1. **Determinism is a hard contract, not a nicety.** Stages 0–8 must be pure functions of
   (chart, corpus, pinned config): same inputs → byte-identical field, hash-verified. This is the
   regression floor for every cutover in W6. `Date.now()`/random are forbidden in the field path.
2. **The uncertainty budget interacts with rectification.** Chart 482012f1 (and others) has an
   open 185-candidate birth-time rectification posterior (WL-6, unresolved, `lel_fit_score:0` — a
   real bug). Sūkṣma boundary intervals must widen to reflect it; when rectification closes they
   tighten. Do NOT serve Sūkṣma instants as if birth time were exact.
3. **The event grammar / domain vocabulary is shared with the planner and L2.** The canonical
   13-value domain set (migration 386) is the SAME vocabulary the planner floors and the event
   classes use. One constant, imported everywhere, CI-diffed. Adding an event class (e.g. the W3
   health/adverse class) touches this shared vocabulary — coordinate it.
4. **"currents" per-tradition tags are cheap now, load-bearing later.** Even before L5
   calibration exists, every current MUST carry its `tradition` tag from day one, because Law 4's
   per-chart per-tradition calibration cannot retroactively tag history. Tagging is a W0/W2
   obligation, not a W-C afterthought.
5. **Coverage attestation must distinguish three states, not two:** `served` / `empty_for_this_chart
   (honest negative — a real finding)` / `not_computed (build gap)`. Conflating "empty" with "not
   computed" is a named historical defect (the S4-03 class). Every view's `coverage` block carries
   all three.
6. **The `reading` prose is composed by deterministic template over already-computed data — NO
   generative call in the serving path** (rule B.10 in the codebase). The prose is dense grounded
   substance assembled by template, not an LLM call inside the tool.
7. **Budget/trim discipline (§N.6):** the densest, most-actionable layer (reading, headline,
   honesty fields) is `hardFloor` — the LAST thing trimmed, never the first. Raw id-arrays trim
   first. This inversion has regressed before (W7.4/MC-005); assert it with a battery test that
   calls every view at minimum budget and checks prose survives untruncated.
8. **Second canonical chart parity is a gate, not a courtesy.** Every W1–W4 item is verified on
   BOTH 482012f1 and 1c826d5a; 1c826d5a's own sweep staleness (LC-5) must be cleared as a
   precondition, or the parity gate cannot pass.
9. **The presentation `kala_timeline_spec` needs a versioned schema and a golden-render test** —
   and per rail 5, that test must exercise the full spec surface, not one fixture.
10. **Aliases during deprecation must not create a second answer to one question.** Each legacy
    tool, during its one-cycle deprecation, points at its successor view and returns the SAME
    data (an alias, not a fork) — never two divergent live answers (the duplicate-copy class).
11. **The `pact_query` ACTIVATION/TRIGGER stages and `standing_predictions_read` are the seams to
    L4/L5.** UPĀYA-SETU's auto-filed falsifiers and STORY's retrodiction ride these. Do not build
    a parallel prediction store; extend the existing L5 ledger surface.
12. **Watchlist/proactive surface (stocktake §4 Tier-2 item 8):** the field knows every upcoming
    window but nothing tells the native. A "next 90 days" digest per chart is the first proactive
    product surface — fold it into AHEAD's contract as a horizon preset rather than a new tool.
13. **`intent_classify` currently returns a classifier *prompt* in some paths (CR-28, a RATIFY
    item).** W5 must confirm the six view-verbs route deterministically and that intent_classify
    emits ALL matched domains (fallback collects all hits, not first-hit-wins) — a known planner
    subtlety.
14. **Migration numbering is a shared sequence across concurrent campaigns** — CR-number and
    migration collisions have happened. Reserve a migration range for this campaign in the ledger
    before writing SQL.
15. **The graha_portrait / shaḍbala golden table is the L1 accuracy anchor** just closed by
    ŚUDDHA-VĀCA; anything the field reads from L1 strength must match it — do not recompute
    strength in the field path, read the authority (§N.5).
16. **The views MUST bind to the existing depth contract.** SAMĀPANA shipped `reading_depth:
    'deep_dive'` + a `verbosity: 'exhaustive'` tier + a hard-guard forbidding any lossy summary
    form on a deep dive. Every temporal view honors it: a deep-dive reading compiles NOW+AHEAD+
    PRIORITIZE at maximal fidelity, and no summary/guaranteed-fits projection may ever apply to a
    deep dive. Do not invent a parallel depth knob — extend the one that exists.
17. **Envelope-size is a hard constraint, learned painfully.** `assess_*` tools historically
    overflowed the MCP token cap (146KB+) and spilled to disk — which makes them UNCONSUMABLE by
    a fileless endpoint. Each view must FIT the MCP envelope by contract (budget the response;
    prose+honesty hardFloored; raw arrays paged/trimmed first). A view that can overflow is a
    defect, not a large success. Provide `budget_kb` paging where a full drill is large (the
    dossier `budget_kb` pattern), but the default response always fits.
18. **Two presentation audiences, one payload.** The `reading`/`compact`/`presentation` triad
    serves BOTH the MCP channel (external consuming LLM — needs `reading` + fitting envelope) and
    **Pariprashna, the internal chat** (needs `compact` cards + the `kala_timeline_spec` widget).
    The native explicitly wants temporal information presented well in Pariprashna; the
    presentation contract is how, and it must be built into the engine, not bolted onto one channel.
19. **Charts may carry a non-default ayanāṁśa pin.** The field is computed per the chart's pinned
    ayanāṁśa (Lahiri by default, but some charts differ); the robustness dimension spans the
    others as sensitivity, not as parallel truths. A view must read the chart's actual pin, never
    hardcode Lahiri.
20. **Tool-name collision check.** The six view names + `kala_upaya_get` must not collide with
    live tools; note `kala_activations` already exists as a registered name — confirm the census
    before registering, and route the legacy name through its successor view during deprecation.
21. **The dark-corpus metric is the campaign's external scorecard.** PARIŚODHANA re-measured
    "bright %" (fraction of computed concepts actually served); the temporal views should MOVE
    that number for the timing concept families. W6's dark-corpus re-measure (full 21 questions,
    both charts) is the honest proof the transformation served what it computes — report it
    whatever it shows.

---

*This handoff, the four spec docs it points to, and the state ledger are the complete context.
A builder who has read Part I (why), Parts II–III (as-is + target), Part IV (what to build),
Parts V–VI (how + rails), and Parts VII–IX (open items + the completeness sweep) has everything
the planning conversation held. Begin with the SHAD_DARSHANA §D kickoff; let the state ledger
carry you across sessions.*
