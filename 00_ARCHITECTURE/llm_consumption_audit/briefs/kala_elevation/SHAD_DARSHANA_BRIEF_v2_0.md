---
artifact: SHAD_DARSHANA_BRIEF (The Six Views + Supreme Elevation — Implementation Campaign)
canonical_id: SHAD_DARSHANA_BRIEF
version: 2.0
status: READY-FOR-EXECUTION — supersedes v1.0 IN FULL (v1.0 retained in place as historical
  record; no session executes from v1.0). The campaign had NOT started when v2.0 was cut
  (no state ledger existed), so this is a clean pre-kickoff supersession, not a mid-flight swap.
created: 2026-07-28
author: Fable (elevation session with the native)
specification (authority order — highest wins):
  1. briefs/kala_elevation/KALA_SUPREME_ELEVATION_v1_0.md   (RATIFIED round-3, at v1.1: vision,
     goal, E1–E8, Living-LEL, YAJÑA-SETU + contender algorithm + the Mode-3 routing rule,
     Intervention Ledger, tri-plane contract, registry items 36–44, decisions D1–D7)
  2. briefs/kala_elevation/KALA_SIX_VIEWS_DESIGN_v2_0.md    (RATIFIED round-2)
  3. briefs/kala_elevation/KALA_SIX_VIEWS_DESIGN_v1_0.md    (RATIFIED round-1)
  4. briefs/kala_elevation/KALA_LAYER_STOCKTAKE_AND_ELEVATION_v1_0.md (as-is inventory)
     **— NOT PRESENT IN THE REPO as of 2026-07-29** (verified: absent from the working tree and
     from git; cited by four docs, written by none). Its function — the as-is inventory and
     redundancy map — is carried by KALA_TRANSFORMATION_HANDOFF_v1_0.md and by the item table
     in §1 below. **A session MUST NOT halt on this file's absence, and MUST NOT reconstruct
     or invent it.** If the native later supplies it, it re-enters the authority order at this
     rank. Until then, treat items 1–3 + the handoff as the complete spec set.
  5. briefs/kala_elevation/KALA_TRANSFORMATION_HANDOFF_v1_0.md (orientation + rails ledger)
  THE DESIGN DOCS ARE THE SPEC. This brief is the execution contract — where the designs say
  WHAT, this says WHO/WHEN/IN-WHICH-FILES/PROVE-IT.
mode: >
  FULLY AUTONOMOUS · MULTI-SESSION campaign driven by ONE re-pasteable kickoff prompt (§D).
  Each session: Conductor (Opus) reads the STATE LEDGER, executes the next wave(s) within its
  ~8h cap, updates the ledger, closes cleanly. Parallel Sonnet builders (Opus where §5 flags or
  after 2 failed verify cycles) · ONE Opus Verifier per session that never writes code ·
  Dvārapāla duty on the Conductor · no human gates · PR + auto-merge only · explicit deploy via
  the canary pipeline · PRIME RULE: truth over completion.
state_ledger: >
  briefs/kala_elevation/SHAD_DARSHANA_STATE.md — created by the first session (W0.1), updated
  at every wave boundary and session close. Schema in §6. The ledger is the campaign's memory —
  a session that doesn't update it has not closed.
scope_estimate: >
  ALL 44 registry items + E-series (E1–E8) across 9 waves; expect 14–24 sessions. Waves may
  span sessions; every wave gate is independently closeable; PARKED-HONEST with evidence is
  always legal.
  **REVISED 2026-07-29 by native ruling: items 18 and 19 are folded IN.** They were previously
  out-of-campaign (18 = the CR-75 KP sub-lord engine, unbuilt; 19 = GOCHARA-2.0 sub-day, the
  separately-ratified D-6 wave). Two new engine-scale waves carry them — W2G (D-6) and W3K
  (KP) — and the campaign now builds 44 of 44. `OUT-OF-SCOPE-BY-DESIGN` is RETIRED from the
  disposition vocabulary; no item may use it. This roughly doubles the campaign and is a
  deliberate completeness choice, not scope creep.
  **W2G carries a hard human prerequisite (§3 W2G.0): the D-6 design's open items N1–N5 must
  be ratified by the native BEFORE any W2G build work, and N5 (lock granularity) is a
  FROZEN-orchestrator-contract question requiring native + Adjudicator ruling per CLAUDE.md
  §N.2. An autonomous session may NOT decide N5. It parks and reports.**
version_note: >
  v2.0 as cut 2026-07-28, plus the 2026-07-29 adversarial-completeness-review fixes applied in
  place before any session executed (no ledger existed; nothing built from the pre-fix text).
  The four MAJOR fixes: registry item 44 given an execution home (§1, §2, §3 W6, §6); a canned
  W4 Mode-2 test fixture (§3 W4); the binding Mode-3 routing rule adopted from Elevation §8
  (§3 W0/W5); and numeric W6 close thresholds replacing "at/near 100%" (§3 W6).
  SECOND AUDIT PASS (2026-07-29, same pre-kickoff window): residual review minors applied —
  Gate-W1 objectivity, Gate-W2 LEL-absent-scenario assertion + skill-baseline semantics +
  calibration-receipt deliverable, Gate-W4 digest assertion, item-38 W4-pairing column,
  Gate-W2G fixture cross-reference, W3K citation-source hierarchy + existing-KP-substrate
  audit note, kickoff-prompt absolute paths — plus the NEW §2.5 Nirmāṇa build-tracker
  integration contract (seed rows, L0 gating, DAG edges, weights-version acyclicity,
  LEL-triggered recalibration as tracked runs, rolling-horizon refresh, retirement catalog
  hygiene). Spec counterpart: KALA_SUPREME_ELEVATION v1.2.
---

# ṢAḌ-DARŚANA v2 — building the six views, the field-as-science, and the intervention engine

## §0 — Mission

Implement the ratified Kāla transformation END-TO-END at round-3 (Supreme Elevation) depth:

1. **Eight tools:** six views (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`,
   `kala_story_get`, `kala_priority_get`, `kala_explain_get`) + two capabilities
   (`kala_upaya_get`, `kala_ritual_get`), all on the elevated uniform envelope (argument
   reading · question_frame · snapshot pin · tri-plane pointers · 3-state coverage ·
   freshness · calibration_maturity).
2. **The temporal field as a point-process model** — λ as hazard, fitted weights, published
   temporal skill score, time-rescaling GOF, circular-shift null, robustness vectors, insight
   synthesis — built strangler-fig BESIDE the legacy writers.
3. **The three-pillar completeness** — interpretation / prediction / intervention — including
   the Living-LEL calibration plane, YAJÑA-SETU with the contender lattice + parihāra
   adjudication, the unified Intervention Ledger, and tri-plane traversability.
4. **All 44 registry items, all built** (v1.0 §7 items 1–21 · v2.0 §I items 22–35 ·
   Elevation §14 items 36–44) + the E-series envelope/pipeline elevations E1–E8. **Items 18
   (KP sub-lord engine) and 19 (GOCHARA-2.0 sub-day) are IN scope as of the 2026-07-29 native
   ruling**, carried by the two new engine waves W2G and W3K (§3).
5. **Planner integration verified by REAL MCP calls**, then the classified cutover and
   one-at-a-time retirement of the 14 legacy surfaces.

## §1 — The complete item inventory (nothing ships unlisted; nothing listed ships untracked)

Every item below appears in the state ledger with a status. [N]=new computation ·
[J]=join/serve existing · [E]=engine-scale. "Both charts" = 482012f1 (Abhisek) AND 1c826d5a
(Abhinandan) verified to identical coverage — always.

**Read the count honestly.** The register holds 44 items and **this campaign builds all 44**
(native ruling, 2026-07-29). Items 18 and 19 — previously deferred — are folded in as two
engine-scale waves:

- **Item 18 → wave W3K.** The CR-75 KP sub-lord engine does not exist in any form: the
  249-fold sub-lord division, KP's cornerstone, is absent, and KP has been explicitly excluded
  from two prior waves (D-5, GOCHARA-SWEEP-2.0). This is a whole missing capability being
  built from zero, not a join. Its value is that KP is *methodologically independent* of
  Parāśari — it gives Law 2 concurrence a genuinely fourth voice rather than a restatement.
- **Item 19 → wave W2G.** GOCHARA-2.0 is a separately-ratified sub-day rearchitecture with its
  own design (`briefs/doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`) and five open
  ratification items N1–N5. Folding it in means this campaign owns that wave, its migration
  plan, and its cutover.

`OUT-OF-SCOPE-BY-DESIGN` is **RETIRED** from the disposition vocabulary — no item may carry it.
A report may claim "44/44" only when every item, including 18 and 19, is VERIFIED. Anything
short of that is PARKED-HONEST with evidence, per LAW ZERO.

| # | Item | Kind | Wave | Spec ref |
|---|---|---|---|---|
| 1 | Daśā-sandhi calendar, all levels, both directions | N | W3 (serve W1-lite from existing spans) | v1 §7.1 |
| 2 | Recurrence-ladder serving (`activation_predicted_dates_jsonb`) | J | W1 | v1 §7.2 |
| 3 | Sky-event calendar: ingresses, stations, eclipse-to-natal, returns, Guru-Śani double-transit | N | W3 | v1 §7.3 |
| 4 | Moorti-nirṇaya per ingress per chart | N | W3 | v1 §7.4 |
| 5 | Vedha application + REAL Sarvatobhadra grid (closes R-19) | J+N | W3 | v1 §7.5 |
| 6 | Activity-specific muhūrta rule tables (keyed to brahma_activity_ontology) | N | W3 | v1 §7.6 |
| 7 | Muhūrta-lagna computation + strength check | N | W3 | v1 §7.7 |
| 8 | Gochara dual-reference (Moon + lagna) serving | J | W1 | v1 §7.8 |
| 9 | Health/adverse event class in sweep grammar (closes DP-4; S4-05 re-test) | N | W3 | v1 §7.9 |
| 10 | Per-chapter LEL pinning + retrodiction fit | J | W1 | v1 §7.10 |
| 11 | Provenance edges persisted at field-write + citation join | N | W2 | v1 §7.11 |
| 12 | Daśā-system applicability evaluation per chart (Law 1) | J | W2 | v1 §7.12 |
| 13 | Tithi-Praveśa (lunar-return annual) | N | W3 | v1 §7.13 |
| 14 | Janma-anchored election micro-rules | N | W3 | v1 §7.14 |
| 15 | Rarity axis from cohort | J | W2 | v1 §7.15 |
| 16 | Kota-Chakra transit fortress | N | W3 | v1 §7.16 |
| 17 | Sudarśana-Chakra year-wheel (NOTE: `bo_sudarshana.py` exists — collision check + duplicate-copy audit BEFORE naming the writer) | N | W3 | v1 §7.17 |
| 18 | **KP sub-lord clock (CR-75) — FULL BUILD**: 249-fold sub-lord division, ruling planets, significators, KP window stream as an independent Law-2 concurrence voice | E | **W3K** | v1 §7.18 + §3 W3K |
| 19 | **GOCHARA-2.0 sub-day substrate — FULL BUILD** (the D-6 wave, owned by this campaign): ephemeris splines, root-found transitions, sub-day event edges | E | **W2G** | `doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md` |
| 20 | Auto-filed prospective ledger entries per AHEAD window (VIDHI E-2) | J | W2 | v1 §7.20 |
| 21 | Per-tradition per-chart calibration weights (matures as outcomes accrue) | E | W2 harness, ongoing | v1 §7.21 |
| 22 | Synthetic reference cohort (~10⁴⁺) + **matched sub-cohort (E7.3)** | N | W2 | v2 §I.22 + Elev §12.3 |
| 23 | Circular-shift null calibration | N | W2 | v2 §I.23 |
| 24 | Uncertainty-budget propagation (intervals below PD; robustness vector) | N | W1-lite, W2-full | v2 §I.24 |
| 25 | Salience vector + submodular selection | N | W2 | v2 §I.25 |
| 26 | UPĀYA-SETU (diagnosis · alternate routing · efficacy tiers · auto-filed falsifiers · **efficacy reporting E6**) | N | W4 | v2 §C + Elev §6 |
| 27 | `kala_timeline_spec v1` + Pariprashna widget contract | N | W2 | v2 §D |
| 28 | Daśā-lord transit-condition (current + forward) | J | W1 | v2 §I.28 |
| 29 | Chandrāṣṭama + horā + janma-resonance day flags | J | W1 | v2 §I.29 |
| 30 | Mudda daśā joined to varsha plane | J | W1 | v2 §I.30 |
| 31 | Period-echo mining (hypothesis-framed) | N | W3 | v2 §I.31 |
| 32 | Diśā-śūla + gulika-kālam election joins | J | W1 | v2 §I.32 |
| 33 | Absence-of-expected detector | N | W3 | v2 §I.33 |
| 34 | Contrastive EXPLAIN (field diffs) | N | W3 | v2 §I.34 |
| 35 | Planner wiring verified LIVE via real MCP calls (HARD GATE) | gate | W5 | v2 §I.35 |
| 36 | Contender lattice + adjudication engine (lattice · census annotation · parihāra graph · Pareto · gap report); ONE engine for ELECT + YAJÑA | N | W3 | Elev §9 |
| 37 | Ritual-resonance mapping + personal paddhati profile | N | W3/W4 | Elev §8–9 |
| 38 | ELECT ritual-pairing + grading unification | J | W1 facade · W3 depth · W4 pairing (closes only when the rite-pairing half lands at W4) | Elev §8 |
| 39 | Living-LEL incremental calibration plane (Circularity Guard · stage-9 partial rebuild · weights versioning · maturity index · prospective/backfill split) | N | W2 | Elev §7 |
| 40 | `kala_ritual_get` registration + planner wiring | J | W0 stub · W4 real · W5 wiring | Elev §8 |
| 41 | Muhūrta Factor Census + corpus-gap register + parihāra rule-table extraction | N | W3 | Elev §9 |
| 42 | Unified Intervention Ledger (L5-seated; three-armed study) | N | W4 | Elev §10 |
| 43 | Tri-plane traversability contract + no-dead-end CI battery | J | W0–W1 | Elev §11 |
| 44 | Single-temporal-authority enforcement: `authority_basis` on every temporal claim + CI authority-basis census (Phala windows ARE field window-ids) | J | W0 seed · W2 populate · **W6 HARD gate** | Elev §2 C1 + §14.44 |

**E-series (modify existing items; tracked as ledger rows E1…E8):**
E1 point-process formalization + skill score + weight-learning harness (W2) · E2 insight
synthesis stage + 8-type catalog (W2) · E3 argument-shaped reading + specificity gate (W0
skeleton, W2 hard-gate) · E4 question_frame compiler (W0) · E5 field_snapshot_id (W0 field
stub, W2 real hash) · E6 per-view elevations: state_delta, decision_value, digest preset,
frontier, developmental thesis, attention ledger, pedagogy/counterfactual EXPLAIN (W1–W3) ·
E7 substrate: completeness census CI, freshness attestation, matched sub-cohort,
argument-composer lib, skill-score CI (W0-seed, W2-full) · E8 non-elevations register
(standing constraints; verified respected at every gate).

## §2 — Proposed naming + file map (Conductor confirms against live registries at W0; §N.1
underscore convention; NO `bodha.*`/dot ids; collision check against `asset_registry` +
`registry_bridge.ts` census MANDATORY before first migration)

**New/changed Python writers** (`platform/python-sidecar/pipeline/orchestrator/writers/`):
- `ka_kshetra.py` — the field pipeline (stages 0–8 orchestration; tables `kala_field`,
  `kala_field_provenance`, `kala_field_windows`, `kala_insights`). Heavy writer:
  `plan_substeps`/`run_substep`, per §N.2 FROZEN contract.
- `bg_cohort.py` — synthetic reference cohort (global; L0 idempotency = upsert).
- `bg_sky_calendar.py` — chart-independent sky-event diary (ingresses, stations, eclipses,
  returns, double-transit geometry); per-chart contact joins live in `ka_kshetra` stage 1.
- `bg_muhurta_lattice.py` — global boundary/factor lattice tables, rolling horizon (~5y),
  incl. Agnivāsa states, combination-yoga spans, kālams, ghaṭīs (chart-independent parts).
- `bg_parihara_rules.py` — parihāra graph + activity rule tables + factor census registry
  (corpus-extracted, citation-carrying; L0 reference data).
- `mi_bhara.py` — weight-fitting + weights versioning + skill score + GOF (stage 9; L5-seated).
- `mi_sankalpa.py` — Unified Intervention Ledger writer (extends prospective machinery).
- Modified: `ka_gochara_sweep.py` (health/adverse event class — item 9, additive grammar
  only; sweep DATA untouchable), `mi_*` LEL intake path (event-triggered partial rebuild hook).

**New/changed MCP serving** (`platform-mcp/src/`):
- `lib/kala_envelope.ts` — the uniform envelope (ONE implementation, eight consumers):
  argument reading schema, question_frame, snapshot pin, tri-plane pointers, 3-state
  coverage, freshness, calibration_maturity, budget/hardFloor discipline per §N.6.
- `lib/argument_composer.ts` — the shared deterministic prose engine (E7.4).
- `lib/kala_grading.ts` — the candidate grading engine (score vector → tier → ledgers).
- `lib/kala_lattice_query.ts` — query-time lattice annotation + parihāra adjudication +
  Pareto survival + gap report over the `bg_muhurta_lattice`/`bg_parihara_rules` tables.
- `tools/kala_views/` — `now.ts, ahead.ts, elect.ts, story.ts, priority.ts, explain.ts,
  upaya.ts, ritual.ts` + one registration block in `registry_bridge.ts` (one canonical
  registration per tool, asserted by test).
- Modified: `intent_scope_classifier.ts` (+question_frame extraction, view-verb routes),
  `platform/src/lib/vidhi/registry_data.ts` (+8 primitives; three-copy lockstep via
  `npm run codegen:vidhi` + parity test — NEVER hand-edit the mirror).

**Migrations** (`platform/migrations/`): W0 session RESERVES a contiguous range in the ledger
after checking live max (migration-collision rail, handoff IX.14). Expected: kala_field
family, cohort, sky_calendar, muhurta_lattice, parihara_rules, weights_versions,
intervention_ledger, insights — surgical migrations only, migration-guard reviewed.

**CI** (`.github/workflows/` + scripts): specificity gate battery · LEL-invariance test
(field hash invariant under LEL mutation; **seeded at W1 with item 10, not W2** — Elev §7) ·
skill-score regression gate · determinism hash-replay · tri-plane no-dead-end battery ·
minimum-budget prose-survival battery · completeness census diff · **authority-basis census
(item 44): enumerates every temporal-claim-bearing serving path, asserts `authority_basis`
present and no second window computation; seeded at W0 beside the completeness census** ·
**Mode-3 single-route assertion (Elev §8 rule clause 4): a Mode-3-shaped payload to
`kala_ritual_get` must return `wrong_view` + the ELECT pointer, never a slate** ·
domain-vocabulary diff vs live CHECK constraints (Kiran rail) · vidhi three-copy parity
(exists — extend).

## §2.5 — Nirmāṇa build-tracker integration contract (binding on every new asset)

Nirmāṇa (the build tracker at `/clients/[id]/nirmana` + the cockpit APIs) is driven entirely
by `asset_registry`: `scripts/seed/asset_registry_seed.ts` is the single source of truth,
`resolveBuildPlan` (`src/lib/build/plan.ts`) topo-sorts `depends_on`, cockpit stats read the
chart-scoped `count_sql` (§N.4 cockpit-truth rail), and the orchestrator is the SOLE
build-state writer. "When the user builds a chart, everything necessary is correctly listed
and built" is a property of this registry — so it is a contract here, not an afterthought:

1. **Seed row in the same PR as the writer.** Every new `@register` writer lands WITH its
   `asset_registry_seed.ts` row: asset_id · layer · sanskrit/english names · `depends_on`
   resolving to existing ids · `asset_kind` (data vs service) · a chart-scoped `count_sql`
   for data assets (NULL + `asset_kind='service'` for services) · scope (`global` for
   `bg_*`). The catalog-reconciliation CI check (every `@register` id ↔ seed row) must be
   green in the same PR. A writer without a seed row is invisible to Nirmāṇa = the wave gate
   fails. **Every wave gate implicitly includes: the wave's new data assets appear in
   Nirmāṇa with DB-true counts on both canonical charts.**
2. **L0 gating consequence (Nirmāṇa hardening ruling §0a-D1, standing).** The four new
   `bg_*` assets (`bg_cohort`, `bg_sky_calendar`, `bg_muhurta_lattice`, `bg_parihara_rules`)
   build ONLY via explicit super-admin L0 triggers — they are NEVER auto-pulled into a
   user's global chart build. A per-chart build whose L0 upstream is dormant shows the
   dependent as **blocked ("L0 dependency not built — run the Brahmagyan layer first")** —
   correct behavior, not a defect. Therefore the W2/W3 gates include: **the wave's L0 assets
   are built in production BEFORE the first per-chart build that depends on them**, so no
   ordinary user build ever encounters the blocked state.
3. **Proposed DAG edges (Conductor finalizes at wave design; every edge must resolve):**
   `ka_kshetra.depends_on = [ka_dasha_kala, ka_gochara_sweep, ka_gochara_resonance,
   ga_panchanga, <the bo_* judgment/promise assets the promise graph reads>, bg_sky_calendar,
   bg_cohort]` · `mi_bhara.depends_on = [ka_kshetra]` · `mi_sankalpa.depends_on =
   [ka_kshetra]` · W3K's KP assets per their layer seating. Election substrate
   (`bg_muhurta_lattice`, `bg_parihara_rules`) is query-time-read by the serving engine, not
   a per-chart build dependency — it appears as L0 assets with their own rows, not as
   `ka_kshetra` edges.
4. **The weights-version acyclicity rule (prevents an L3↔L5 DAG cycle).** `ka_kshetra` NEVER
   lists `mi_bhara` in `depends_on` — that edge would create ka_kshetra → mi_bhara →
   ka_kshetra and `topoSort`'s cycle detection would reject every plan containing them.
   Instead: **weights v0 (classical structural priors) is seeded by migration**;
   `ka_kshetra` reads the newest weights VERSION from the table (data dependency, not a DAG
   edge); `mi_bhara` writes new versions; the NEXT `ka_kshetra` rebuild pins the newest. The
   calibration loop closes ACROSS builds while the DAG stays acyclic WITHIN every build.
5. **LEL-triggered recalibration is a tracked run.** The LEL-append hook dispatches a
   standard scoped build run (asset/asset_set: `mi_bhara` + the biographical-join refresh)
   through the orchestrator/pipeline, so Nirmāṇa sees state, progress, and throughput like
   any other build. No side-channel recomputation — the orchestrator remains the sole
   build-state writer (§N.2).
6. **Rolling-horizon refresh policy.** `bg_muhurta_lattice` and `bg_sky_calendar` carry a
   ~5y forward horizon that ages: they are refreshed via the explicit super-admin L0 refresh
   trigger on a cadence recorded in the state ledger (and surfaced by the envelope's
   freshness attestation either way — a stale horizon is served as a flag, never silently).
7. **Retirement includes the catalog (see Gate W6).** Retiring a legacy writer retires its
   seed row and rewires every `depends_on` citing it; the catalog-reconciliation test and
   the cascade/clear-preview surfaces are re-verified against the new DAG after EACH
   retirement, not once at the end.
8. **Per-chart idempotency (§N.3).** `ka_kshetra` and every per-chart table in this campaign
   use delete-then-insert scoped to (chart_id × natural key) — a rebuild REPLACES, never
   accretes; Nirmāṇa's rebuild semantics depend on this.

## §3 — Waves (execution order; each independently closeable; gates are binary)

**Nine waves:** W0 → W1 → W2 → **W2G** → W3 → **W3K** → W4 → W5 → W6. The two lettered waves
are the folded-in engines (item 19 and item 18). W2G is gated on a human ratification (N1–N5)
and may park without stalling the campaign; W3K depends on W2's clock machinery. Neither may
be made a prerequisite of W4/W5 — see §4.

### W0 · Foundation + the elevated envelope (first session, blocking)
0.1 Create `SHAD_DARSHANA_STATE.md` (§6 schema), seed all waves/items NOT-STARTED.
0.2 Preflight: repo clean · both canonical charts healthy (LC-5 sweep staleness on 1c826d5a
    CLEARED or ticketed as the W1 precondition) · canary pipeline state noted (IAM grant may
    still be pending — manual canary discipline if so; do NOT block) · **migration range
    reserved in ledger** · duplicate-copy + tool-name census (note: `kala_activations` legacy
    name; `bo_sudarshana.py` collision for item 17) · **Nirmāṇa catalog-reconciliation check
    (§2.5.1) run and its result recorded in the ledger**.
0.3 `lib/kala_envelope.ts` + `lib/argument_composer.ts` v0: argument-shaped reading
    (thesis/evidence/dissent/verdict/falsifier) · `question_frame` param · `field_snapshot_id`
    (stub = substrate build ids until W2) · tri-plane pointer slots (43) · 3-state coverage ·
    freshness attestation · calibration_maturity slot · §N.6 hardFloor discipline. ONE
    implementation, eight consumers.
0.4 Eight facades over EXISTING substrate: six views + `kala_upaya_get` stub +
    `kala_ritual_get` stub. **The ritual stub serves Modes 1–2 only** — an honest
    `not_computed` coverage ledger until W4 — and implements the Mode-3 routing rule
    (Elev §8) from day one: a Mode-3-shaped call returns `wrong_view` naming `kala_elect_get`
    plus the tri-plane pointer. **No Mode-3 passthrough, proxy, or delegation to the muhūrta
    substrate ships in `kala_ritual_get` — at W0 or ever.** Legacy tools gain deprecation
    notes → successor views (aliases live; nothing retired).
0.5 STORY facade fixes parva duplication at serving (dedup by span+level).
0.6 CI skeletons: specificity gate v0 (canonical + existing 4 charts as proxy cohort;
    full-cohort gating from W2) · minimum-budget prose-survival battery · tri-plane
    no-dead-end battery (asserting honest `no_lever` allowed) · completeness census seed ·
    **authority-basis census seed (44)** · **Mode-3 single-route assertion test**.
**Gate W0:** all eight tools live on production, envelope-conformant; naive tool_search
surfaces them by name; sealed-harness regression shows no loss; CI skeletons green (incl. the
Mode-3 assertion and both census seeds); **items 18/19 seeded NOT-STARTED against waves W3K
and W2G, and the W2G N1–N5 ratification block created empty in the ledger so the native's
rulings have a home**; ledger current. Both charts.

### W1 · Tier-A serving joins (cheap, high-yield; parallel builders)
Items: 2 (recurrence ladder → AHEAD) · 8 (dual-reference gochara) · 28 (daśā-lord transit
condition, current+forward) · 32 (diśā-śūla + gulika kālam joins) · 29 (chandrāṣṭama/horā/
janma-resonance flags) · 30 (mudda join) · 10 (per-chapter LEL pinning + retrodiction fit) ·
24-lite (Sūkṣma boundaries as intervals — propagation formula; full budget W2) · 1-lite
(sandhi bands from existing period spans; full calendar W3) · 38-lite (grading-engine facade
unifying ELECT candidate output) · 43 (tri-plane pointers wired on real data) · E6-lite:
proactive 90-day digest preset on AHEAD (D4) · ELECT frontier statement v0.
**Gate W1:** each item live-verified through its view on BOTH charts — **objectively: each
W1 item's new envelope fields present and non-empty, or honest-empty with a served reason, on
both charts** (no "visibly richer" judgment call); digest preset returns a non-empty honest digest (**ritual rows are NOT expected
here — Mode 1 arrives at W4; a ritual-free W1 digest is the correct state, per Elev §6**);
the Circularity-Guard LEL-invariance test ships with item 10 and is green; no regression.

### W2 · The field as science (the heavy central wave; Opus design mandatory)
The ten-stage pipeline (v2 §G) elevated per Elevation §3–§5, §7, §12 — built BESIDE legacy:
- Stages 0–4: kinematics (dwell-time, true velocities, eclipse geometry) · symbolization ·
  promise graph w/ alternate routings · clocks w/ applicability+competence gates (12) +
  intervals below PD (24-full) · field assembly with provenance edges persisted (11),
  **λ formalized as point-process hazard (E1): multiplicative composition, analytic
  integration between events**.
- Stage 5: circular-shift null (23) · robustness vectors (§A.6) · Adṛṣṭa residual.
- Stage 6: salience vector + submodular selection (25) · rarity axis (15) via cohort (22)
  + matched sub-cohort (E7.3).
- **Stage 6.5 (NEW, E2): insight synthesis** — the 8-type catalog, cohort-scored,
  fact-carrying; `kala_insights` table; reading-leads-with-insight enforced in composer.
- Stage 8: `kala_timeline_spec v1` (27) + golden-render test covering the FULL spec surface
  (rail 5).
- **Stage 9 (E1/D3 + 39/D6):** `mi_bhara` weight-fitting harness (holdout, shrinkage to
  classical priors, conservative) · weights versioning pinned into field hash · temporal
  skill score + time-rescaling GOF published for both charts · **Living-LEL plane:**
  Circularity Guard CI (LEL-mutation invariance test) · LEL-append trigger → falsifier
  auto-scoring (20) → weight update → skill recompute → biographical-join refresh ·
  calibration_maturity in every envelope · prospective/backfill separation · **the portal
  calibration event receipt served from the LEL-intake path (`{predictions_scored[],
  hits/misses, maturity_before/after, tier_migrations[]}`, via the existing
  mimamsa/standing-predictions surface — Elev §7)** · **the LEL-append recalibration
  dispatched as a TRACKED scoped build run through the orchestrator, never a side-channel
  recompute (§2.5.5)**.
- E5: `field_snapshot_id` = real field hash. E7: completeness census full · freshness
  attestation live · specificity gate now HARD against real cohort charts (D2).
- **44 (authority-basis population):** real field window-ids exist for the first time here, so
  every temporal-claim-bearing serving path is enumerated into the authority-basis census and
  wired to emit `authority_basis`; Phala windows are re-pointed to field window-ids wherever
  they are not already. **Reported at W2** (scoreboard in the ledger), **gated at W6** — a W2
  shortfall is a tracked number, not a wave blocker.
**Gate W2:** field deterministic (hash-replay) · LEL-invariance test green · skill score +
GOF report published for both charts and regression-gated (**the first published score
becomes the CI baseline; thereafter "regressed" means below the best released value without a
classified reason**) · **the LEL-absent scenario verified: a chart with no LEL serves
structural-prior weights, `no_lived_history_recorded` STORY flags, and an honest
calibration_maturity of zero — the D6 three-scenario contract gated, not just designed** ·
cohort base rates served · null
exceedance on every window · salience vector visible in PRIORITIZE · insight rows lead
readings · timeline spec renders valid · specificity gate HARD-green · legacy writers
UNTOUCHED and still serving.

### W2G · GOCHARA-2.0 — the sub-day substrate (item 19; the folded-in D-6 wave; Opus mandatory)

Spec: `briefs/doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md` — that document is the WHAT;
this section only places it in the campaign and states its gate.

**W2G.0 — THE RATIFICATION PRECONDITION (hard; human-in-the-loop; no exceptions).** D-6 was
never ratified; it carries five open native items. NONE of the build below starts until all
five are ruled and the rulings are recorded verbatim in the state ledger:
- **N1** wave naming (D-6 vs new-arc numbering) · **N2** multi-chart rollout order after
  cutover · **N3** whether the global event calendar backfills pre-1984 history · **N4**
  cutover posture (hard cutover vs dual-serve shadow period with v1 authoritative for N days).
- **N5 — lock granularity. THIS IS A FROZEN-CONTRACT QUESTION.** `acquire_chart_lock` is a
  single chart-level `pg_try_advisory_lock`; the orchestrator refuses concurrent runs per
  chart BY DESIGN (`runner.py` → `sys.exit(3)`), which blocks substep-shard parallelism even
  though the writes were proven disjoint-safe. Granting the 2.0 writer per-asset/per-shard
  locking changes the FROZEN orchestrator contract, which per CLAUDE.md §N.2 means **STOP and
  raise with the native — an autonomous session may NOT decide this.** Native + Adjudicator
  ruling required. If N5 is unresolved when the Conductor reaches W2G, the wave parks
  `PARKED-HONEST (awaiting N5 ruling)`, the campaign proceeds to W3/W3K, and W2G re-enters
  when the ruling lands. **The campaign does not stall on N5, and does not route around it.**

W2G.1 bind-time validations V1–V6 from the design §6 (profile split · `ephemeris_daily`
coverage 1984–2084 × 9 bodies · spline accuracy near stations and Moon perigee, which sets
root-find tolerance · transition-count sizing · v1 corpus provenance readiness · divergence
pilot on one materialized year) · W2G.2 the 2.0 writer built BESIDE v1 (strangler; v1 sweep
data remains untouchable per the standing rail) · W2G.3 equivalence corpus: v1 rows are
ground truth, every divergence classified with evidence · W2G.4 cutover per the N4 ruling.
**Gate W2G:** sub-day transition edges computed and served on BOTH charts · divergence report
complete with zero unclassified rows · v1 sweep data intact · the precision-regime label on
transit-edge constraints flips from day-grade to sub-day, **verified at whichever of
W2G-close / W4-close comes later — if W2G lands after W4 (e.g. after an N5 park), the W4
Mode-2 fixture is re-run and its regime assertions must still pass; if W2G closes first, this
clause is discharged retroactively at W4** · N1–N5 rulings recorded in the ledger.

### W3 · New computations (parallel builders over the field)
Items: 1-full (sandhi calendar) · 3 (sky calendar — `bg_sky_calendar`) · 4 (moorti) · 5
(vedha + REAL Sarvatobhadra grid, closes R-19) · 6 (activity rule tables) · 7 (muhūrta-lagna)
· 9 (health/adverse class; S4-05 scenario re-test) · 13 (Tithi-Praveśa) · 14 (janma-anchored
rules) · 16 (Kota) · 17 (Sudarśana — post collision-audit) · 31 (period-echo) · 33
(absence-of-expected) · 34 (contrastive EXPLAIN) · **36 (contender lattice + parihāra
adjudication + Pareto + gap report — `bg_muhurta_lattice` + `bg_parihara_rules` +
`lib/kala_lattice_query.ts`; ONE engine for ELECT + YAJÑA)** · **41 (Muhūrta Factor Census +
corpus extraction of parihāra/Agnivāsa/combination-yoga tables — citation-carrying;
`not_in_corpus` honestly registered)** · 37-part (paddhati profile schema) · 38-full (ELECT
depth: lattice-backed slates, frontier, gap report) · E6-full: NOW state_delta · AHEAD
decision_value · STORY developmental thesis · PRIORITIZE attention ledger · EXPLAIN
pedagogy + counterfactual.
**Gate W3:** every computation two-pass verified on BOTH charts, served through its view(s),
citation-carrying · ELECT candidates carry judgment ledgers (doṣas → parihāras → residual) ·
the Abhijit-override case demonstrably rescues a candidate · gap report present when the
horizon lacks the ideal · factor census served in coverage · health class passes the S4-05
re-test.

### W3K · The KP sub-lord engine (item 18 / CR-75; built from zero; Opus design mandatory)

KP exists nowhere in this codebase — the 249-fold sub-lord division is absent, and KP was
explicitly excluded from D-5 and from GOCHARA-SWEEP-2.0. This wave builds it, and its worth is
specific: **KP is methodologically independent of Parāśari**, so it gives Law 2's concurrence
test a genuine fourth voice instead of a restatement of evidence already counted.

**Existing-substrate audit FIRST (duplicate-copy rail):** "exists nowhere" must be verified,
not assumed — `ganita_kp_cusps_get` is a live registered tool today, so SOME KP substrate
(cusps at minimum) already exists. K.1's first act is an inventory of every live KP surface
(tools, tables, writers, seeds); the wave EXTENDS what exists and never twins it.

K.1 The sub-lord substrate: Vimśottarī proportional subdivision of each nakṣatra pāda to
sub and sub-sub, as deterministic arithmetic over the existing ephemeris — a new `ga_*`-class
or `bg_*`-class writer per §N.1/§N.2 (Conductor confirms layer seating at design; it is
chart-independent reference geometry plus a per-chart projection, so expect the split).
K.2 Cuspal sub-lords (KP house cusps under the ratified ayanāṃśa policy — **KP's Placidus
convention differs from the project's default; the divergence is served as data per Law 4,
never silently reconciled**), significators, and ruling planets.
K.3 The KP window stream: sub-lord period punctuation offered to the field as an INDEPENDENT
clock, gated by Law 1 applicability exactly as every other system is — it earns concurrence,
it is never privileged.
K.4 Serving: KP rows carry their school tag; NOW/AHEAD show KP concurrence or KP dissent, and
**dissent is served as intelligence per vision property 4, never hidden or averaged away**.
**Gate W3K:** sub-lord division verified against worked examples (two-pass, cited — **the
acceptable citation-source hierarchy, so the Verifier never adjudicates from memory: (i)
ingested KP texts if the corpus holds them → (ii) the CR-75 design doc's worked tables →
(iii) published KP reader examples transcribed into a committed fixture file; if only (iii)
is available, the item is VERIFIED against the fixture and the corpus gap is filed as an
ingestion work item**) ·
cuspal sub-lords computed on BOTH charts · KP appears as a distinct voice in at least one
concurrence insight and at least one served dissent · Law 1 applicability evaluated, not
assumed · ayanāṃśa/house-system divergence from the project default served explicitly ·
the specificity gate still HARD-green with KP prose included.

### W4 · The intervention wave (flagship; Opus design mandatory)
- 26 UPĀYA-SETU full: PACT-link diagnosis · alternate-routing search · efficacy tiers ·
  least-opposed ELECT integration · praśna decision-gate · auto-filed falsifiers · efficacy
  reporting (E6).
- 37-full: ritual-resonance mapping (configuration→rite via remedy/deity ontology) +
  paddhati profile live (divergence served).
- 40: `kala_ritual_get` REAL — Mode 1 (opportunity scan: 4-factor scoring over sky calendar ×
  field × election quality × rarity) + Mode 2 (sky-pattern spec + coarse-to-fine search over
  the lattice; precision-regime labels) · Mode 3 pairing in ELECT (act-time + rite-time as
  one answer) · Mode-1 opportunities feed the AHEAD digest.
- 42: Unified Intervention Ledger (`mi_sankalpa`) — every elected act files
  {intent, class, window, adjudication record, predicted differential, performed?, outcome
  linkage}; three-armed study fields; extends standing-predictions machinery, NO parallel
  store.
**Gate W4:** on 482012f1: a weakly-promised event class returns correct link diagnosis +
honestly-tiered non-empty ledger + filed prospective entry; "pressure without delivery"
verified on an un-promised window; Mode 1 returns ranked (window, rite) pairs with 4-factor
score vectors; **Mode 2 discharges the CANNED FIXTURE below** (the review closed the
"native-specified combination" hole — an autonomous campaign cannot wait on a human to invent
a test); an elected act files a complete Intervention Ledger entry; **the AHEAD digest now
carries ≥1 Mode-1 ritual-opportunity row, or an explicit honest-empty naming the horizon
searched (the D4 digest-includes-rituals clause, gated here where Mode 1 first exists)**.
All mirrored on 1c826d5a.

> **CANNED W4 MODE-2 TEST FIXTURE (`tests/fixtures/yajna_mode2_gate.json`; authoritative — the
> Conductor discharges this exactly, and does not substitute an easier query).** Sky-pattern
> spec, stated as the constraint conjunction the compiler must accept:
>
> - `hora_lord = Guru` **AND** `vara = Guru-vāra` (day-part × weekday interaction)
> - `agnivasa = favorable` **per the native's paddhati profile** (item 37) — and the response
>   must ALSO show the corpus-default residence alongside it whenever the two diverge
> - `karana NOT IN (viṣṭi/bhadrā)` (absence constraint)
> - `tara_bala NOT IN (vadha, vipat, pratyak)` reckoned from the chart's own janma-tārā
>   (chart-relative constraint)
> - `outside rāhu-kālam` (kālam exclusion)
> - horizon: **next 24 months** from the session date
>
> **PASS conditions, all four required:**
> 1. **Non-empty or honestly-empty:** returns ≥1 graded candidate; OR returns zero with the
>    gap report naming which constraint eliminated the horizon and when the pattern next
>    occurs beyond it. An unexplained empty result FAILS.
> 2. **Precision labels correct:** every candidate labels its bounding regime — this fixture
>    is pāñcāṅgika-bound throughout, so candidates must claim **intra-day precision**, not be
>    conservatively degraded to day-grade. A day-grade label here is a FAIL (it would mean the
>    §8 precision-regime honesty is being applied backwards).
> 3. **Judgment ledger present:** each candidate carries `doṣas_present → parihāras_applied
>    (with citations) → residual_doṣas → net standing`, and the paddhati-vs-corpus divergence
>    is served where it exists.
> 4. **Census honesty:** the coverage block enumerates which of the six constraints were
>    computed vs `not_in_corpus` — if the corpus lacks an Agnivāsa rule table at W4, the
>    honest `not_in_corpus` flag plus a filed ingestion work item is a PASS for (4) and the
>    fixture is discharged as **PARKED-HONEST with evidence**, not silently softened.
>
> **Precedence between (1) and (4), so the Conductor never has to judge:** a `not_in_corpus`
> constraint is dropped from the conjunction and the search runs on the remaining five. If
> that reduced search returns candidates, (1) is satisfied normally and the fixture is
> **PARKED-HONEST** solely on the missing rule table. If it returns zero, (1) still requires
> the gap report to name the eliminating constraint. An empty result with neither a
> `not_in_corpus` flag nor a gap report is a FAIL in every case — "it returned nothing" is
> never itself an explanation.
>
> Mirrored on 1c826d5a with its own janma-tārā and paddhati profile — the two charts must
> return *different* candidate sets. Identical output across charts FAILS the fixture
> (it would mean the chart-relative constraints are not actually binding).

### W5 · Planner integration (rides VIDHI-PŪRṆATĀ E-1; reconcile, don't duplicate)
Eight primitives (`now_read, ahead_read, elect_read, story_read, priority_read, explain_read,
upaya_read, ritual_read`) · question_frame threading from `intent_classify` (E4; verify
all-matched-domains fallback, not first-hit — handoff IX.13) · machine-band defaults: every
domain deepdive compiles NOW+AHEAD+PRIORITIZE; undertaking→ELECT; biography→STORY;
ritual/yajña intents→RITUAL; every row id pre-authorizes one EXPLAIN hop · deep_dive binds to
the EXISTING depth contract (verbosity 'exhaustive'; no lossy summary on deep dive — handoff
IX.16) · three-copy registry lockstep per the VIDHI brief.
**NATIVE'S HARD GATE (35 + 40):** every primitive + route verified by REAL MARSYS-JIS MCP
calls from the implementing session — call → response shape → floor presence — recorded in
the ledger. Unit tests do NOT satisfy this gate.
**Gate W5:** live-MCP verification table complete for all 8 primitives × representative
intents; "tell me about my money" demonstrably compiles NOW+AHEAD+PRIORITIZE floors;
"when should I do a Rudra yajña" routes to RITUAL (Modes 1–2). **Mode-3 routing asserted
per Elev §8:** "when should I sign the contract, and what rite should I do first" routes to
**ELECT** — which serves act-time and rite-time as one answer — and the same payload sent to
`ritual_read` returns `wrong_view` + the ELECT pointer. A ritual intent that also names an
undertaking routes to BOTH, with ELECT authoritative for the act-time.

### W6 · Cutover + retirement (strangler completion; v2 §H.3–5)
Per-view cutover with the equivalence discipline (legacy = ground-truth corpus; every
divergence classified legacy-artifact/new-capability/new-bug with evidence; NO divergence
ships unclassified) → retirement of legacy middle-layer writers (sangam/yojaka/kalasutra/
taranga) and the 14 legacy tools ONE at a time, each at zero consumers (catalog census
proof), duplicate-copy audit before each · **each retirement ALSO retires the asset's
`asset_registry` seed row and rewires every `depends_on` that cites it, with the Nirmāṇa
catalog-reconciliation test green and cascade/clear-preview re-verified against the new DAG
after each (§2.5.7)** · clock substrates (chart_dashas, sweep corpus) are
KEEPERS · `kala_timeline`/`kala_convergence_staging` retirement-audited · final battery:
full regression + sealed harness + preserve-list sweep (v1 §9) + minimum-budget battery +
**dark-corpus re-measure (full 21 questions, BOTH charts)** + census invariant locked in CI +
**item-44 authority-basis census HARD-gated** + close report `SHAD_DARSHANA_REPORT_v1_0.md` +
ledger archived COMPLETE.

**Gate W6 (BINARY — the review replaced "at/near 100%" with numbers; every clause below is
pass/fail on inspection, no judgment call):**

1. **Surface:** production serves ONLY the eight tools, plus documented aliases inside their
   final deprecation cycle. Any other temporal tool live = FAIL.
2. **Divergences:** zero unclassified. Every legacy-vs-new divergence carries
   legacy-artifact / new-capability / new-bug + evidence.
3. **Dark corpus — the numeric gate:** temporal-family **bright% ≥ 95% on BOTH canonical
   charts** (measured on the full 21-question re-measure), **and** strictly above the
   PARIŚODHANA baseline on both. The residual ≤5% is legal ONLY as classified
   `PARKED-HONEST` rows, each naming its reason and release condition; an unclassified dark
   question inside the residual = FAIL. Below 95% on either chart = the wave does not close;
   it parks with the shortfall itemized.
4. **Authority (44):** authority-basis census returns 100% of temporal-claim-bearing serving
   paths carrying `authority_basis`, and zero paths computing an independent window. This one
   admits no residual — 100% or FAIL.
5. **Disposition completeness:** every registry item 1–44 (**including 18 and 19**) and every
   E-row E1–E8 carries one of VERIFIED-FIXED / VERIFIED-NO-DEFECT / PARKED-HONEST /
   FAILED-REOPENED. `OUT-OF-SCOPE-BY-DESIGN` is retired and is not a legal disposition. Any
   blank = FAIL. A parked W2G or W3K is legal here, but it must be visible as PARKED-HONEST
   with its reason and release condition — a close report may not read "44/44" over a park.
6. **Skill score:** published for both charts and regression-gated, per W2 — not regressed
   from the best released value without a classified reason.

## §4 — Dependency spine (what blocks what)

envelope+composer (W0) → everything · cohort (22, W2) → rarity (15), insight surprise (E2),
specificity-hard (D2) · field λ (W2) → state_delta, decision_value, contrastive (34),
Mode-1 temporal factor · lattice+census+parihāra (36/41, W3) → ELECT depth (38), Mode 1–2
(40), Mode-3 pairing · sky calendar (3, W3) → Mode 1 scan, STORY/AHEAD punctuation ·
UPĀYA ontology lane (26, W4) → ritual-resonance (37) · Intervention Ledger (42) requires
falsifier machinery (20, W2) · planner (W5) requires all eight tools real · cutover (W6)
last, always.

**The two folded-in engine waves:**
- **W2G (19, GOCHARA-2.0)** is blocked by the N1–N5 ratification (W2G.0) and by nothing else;
  it does NOT block W3, W3K, or W4. Its output UPGRADES precision on transit-edge constraints
  — ELECT hour-precision and AHEAD's honest sub-day edges — so everything downstream must be
  built to work correctly at day-grade first and improve when W2G lands. **No wave may be
  designed to REQUIRE sub-day precision**; that would make the whole campaign hostage to N5.
- **W3K (18, KP)** requires the field's clock machinery (W2) and the Law-1 applicability
  evaluation (item 12, W2). It feeds concurrence insights (E2) and NOW/AHEAD dissent serving,
  so land it before W6's dark-corpus re-measure to get credit for the coverage it adds.
- Both are engine-scale and independently parkable. **If either parks, W6 may still close** —
  but only with that item explicitly PARKED-HONEST with evidence, never as a silent 44/44.

## §5 — Model & effort policy
Sonnet default. **Opus mandatory:** Conductor · Verifier · W2 field/science design ·
W4 UPĀYA/YAJÑA design · the parihāra-graph corpus extraction review (W3, judgment-heavy) ·
**W2G spline/root-find numerics + the divergence adjudication** · **W3K sub-lord doctrine and
the cuspal/ayanāṃśa divergence call** · any builder after 2 failed verify cycles. Effort high
only for W2/W4/W2G/W3K design, W3 item-36/41, and the W6 battery; low for W1 joins and
mechanical work.

## §6 — State ledger schema (v2)
Per-wave: status (NOT-STARTED | IN-PROGRESS <session, worktrees> | VERIFIED-CLOSED <evidence>
| PARKED-HONEST <reason, release condition>). Per-item (**1–44** + **E1–E8**): status +
evidence link + both-charts attestation, drawn from the closed vocabulary VERIFIED-FIXED /
VERIFIED-NO-DEFECT / PARKED-HONEST / FAILED-REOPENED (**`OUT-OF-SCOPE-BY-DESIGN` is RETIRED
as of the 2026-07-29 fold-in ruling — a session that writes it is out of contract**). Plus:
**the N1–N5 ratification block for W2G — each ruling recorded verbatim with its date, and N5
additionally carrying the Adjudicator's ruling; a blank N5 means W2G is parked, not startable**
·
migration range reserved · deployed revisions · open PRs · skill-score scoreboard (per chart,
per release) · specificity-gate status · **authority-basis census scoreboard (item 44: paths
enumerated / carrying `authority_basis` / computing own windows — the last must read 0)** ·
**dark-corpus bright% per chart per re-measure, against the ≥95% W6 gate** · live-MCP
verification table (W5) · **W4 Mode-2 fixture disposition** · NEXT-ACTION line.
Every session: first act read, last act update.

## §7 — Rails (standing + campaign; each traces to a paid incident)
All v1.0 §3 rails carry forward VERBATIM: untouchables (`kala_gochara_windows` data,
`build_substep_progress`, sealed harness) · PR+auto-merge only · deploy = merged-main → real
authenticated verify → canary → cutover → traffic tracks LATEST · real-SDK tests for
registration gates · coverage-gates tested against their own coverage · duplicate-copy audit
before every fix/retirement · never spawn a builder from inside a worktree · merge-state ≠
verification-state · ONE canonical domain vocabulary (shared constant, CI-diffed; the event
grammar and any new event class — item 9 — coordinates through it) · fresh-chart CI smoke
green · registers append-only · no fabrication, honest-empty always · LEL entries native-only
· LAW ZERO · never touch root CLAUDECODE_BRIEF.md · both charts identical coverage.
**New rails (this round):** **CIRCULARITY GUARD** — the field never reads the LEL; CI
invariance test is itself an untouchable gate, live from W1 with item 10 · **ONE-ENGINE RULE**
— ELECT and YAJÑA share the single lattice/adjudication/grading engine; a second
implementation of any of the three is a build error · **MODE-3 ROUTING RULE** (Elev §8) —
ELECT is the sole server of Mode 3; `kala_ritual_get` redirects, never passes through;
CI-asserted · **SINGLE TEMPORAL AUTHORITY** (item 44) — every temporal claim cites a field
window-id via `authority_basis`; a serving path that computes its own window is a build error,
not a divergence to classify · **B.10 prose rule** — the argument composer is template-over-computed-data;
no generative call in any serving path · **weights are versioned artifacts** — a field build
pins its weights version; silent weight mutation = drift failure · **ka_bhavishya domain-drift
fix arrives by REPLACEMENT** (AHEAD supersedes; the legacy writer is not patched outside its
own authorization — but the W-any fleet vocabulary audit still runs).

## §D — Kickoff prompt (single paste; RE-PASTEABLE every session until COMPLETE)

> **SUPERSEDED FOR AUTONOMOUS NIGHT RUNS (2026-07-29):** the operative kickoff prompt is
> `SHAD_DARSHANA_NIGHT_RUN_v1_0.md §D` — the multi-agent overnight orchestration (swarm
> roster, parallel-track sequence, Adjudicator charter). The prompt below remains valid only
> for a manually-supervised single-Conductor session; do not maintain both — edits to kickoff
> language land in the NIGHT_RUN doc.

```
You are the CONDUCTOR of ṢAḌ-DARŚANA v2 (Six Views + Supreme Elevation), FULLY AUTONOMOUS,
no human available. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md —
    the execution contract; §1 inventory, §3 waves, §4 dependencies, §7 rails BIND you;
(2) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_SUPREME_ELEVATION_v1_0.md
    — the round-3 design authority (at v1.2) —
    then KALA_SIX_VIEWS_DESIGN_v2_0.md, then v1_0.md (elevation wins conflicts);
(3) 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_STATE.md —
    the state ledger. If absent, this is the
    FIRST session: create it per brief §6 and begin W0. Otherwise resume from NEXT-ACTION.
Execute as many wave-gates as fit safely (~8h cap): parallel Sonnet builders in
.worktrees/shad-darshana-*, Opus where §5 flags or after 2 failed verify cycles. ONE Opus
Verifier that never writes code accepts every item against LIVE production post-deploy —
four dispositions, no "passed with caveats"; BOTH canonical charts, identical coverage.
Hard gates you may not soften: W5 planner primitives verified by REAL MARSYS-JIS MCP calls;
the specificity gate (from W2) HARD; the Circularity Guard LEL-invariance test (live from W1
with item 10); the skill score published for both charts at W2 close; the canned W4 Mode-2
fixture (brief §3 W4 — discharge it exactly, do not substitute an easier query); the item-44
authority-basis census at 100% with zero self-computed windows; W6 temporal dark-corpus
bright% >= 95% on BOTH charts with every residual row classified. Items 18 and 19 ARE in
scope, carried by waves W3K and W2G; OUT-OF-SCOPE-BY-DESIGN is a retired disposition you may
not write. W2G has a HUMAN PRECONDITION: the D-6 open items N1-N5 must be ratified by the
native first, and N5 (lock granularity) is a FROZEN-orchestrator-contract question you may NOT
decide -- park W2G, report it, proceed with other waves. No wave may be designed to REQUIRE
sub-day precision; build day-grade-correct and let W2G upgrade it. The Mode-3 routing rule
(Elevation §8) is binding: ELECT alone serves Mode 3; kala_ritual_get redirects and never
passes through. Strangler discipline throughout: build beside,
cut over with classified equivalence evidence, retire only at zero consumers after a
duplicate-copy audit; legacy data never destroyed. Nirmāṇa contract (brief §2.5): every new
writer lands WITH its asset_registry seed row + chart-scoped count_sql in the same PR; the
new bg_* assets build only via explicit super-admin L0 triggers and are never auto-pulled
into a user's chart build; ka_kshetra never lists mi_bhara in depends_on (weights flow by
version pin, keeping the DAG acyclic); LEL-triggered recalibration runs as a tracked scoped
build. PR + auto-merge only; deploy via
merged-main → real authenticated verify → canary → cutover, traffic tracking LATEST.
Untouchables: kala_gochara_windows data, build_substep_progress, the sealed evaluator
harness, root CLAUDECODE_BRIEF.md. Before the cap: land or park cleanly, update
SHAD_DARSHANA_STATE.md (statuses, evidence, skill scoreboard, NEXT-ACTION), clean worktrees,
confirm production == main. COMPLETE only when every §3 gate is VERIFIED-CLOSED and
SHAD_DARSHANA_REPORT_v1_0.md is merged. Truth over completion — PARKED-HONEST with evidence
beats a false close. Begin.
```
