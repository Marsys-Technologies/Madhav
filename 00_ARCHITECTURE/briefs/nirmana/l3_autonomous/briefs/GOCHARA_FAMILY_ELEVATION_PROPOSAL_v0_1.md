---
artifact: GOCHARA_FAMILY_ELEVATION_PROPOSAL
version: "0.1"
status: SUPERSEDED
superseded_by: GOCHARA_FAMILY_ELEVATION_PLAN_v0_2.md  # same day; v0.2 replaces inference with executed evidence and corrects three recommendations
produced_on: 2026-09-20
produced_by: Claude Code (Fable 5.1), research session at native request
intended_reviewer: Codex / gpt-astra independent challenge, then native ruling
governing_strategy: ../../MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (APPROVED_STRATEGY, DP-SD-017)
product_parent: ../../../../MADHAV_PRODUCT_DEFINITION_v3_0.md
responds_to: ../discussion_prompts/PROMPT_1_GOCHARA_FAMILY.md
source_revision: 5d8252dbe (branch codex/madhav-l3-claude-code, worktree madhav-l3/integration)
does_not_authorize: >
  Any code change, build, rebuild, migration, registry edit, lifecycle change, or release of the
  century hold. The native's 2026-08-21 standing order (no gochara re-materialization without fresh
  explicit authorization) and the ka_gochara_sweep protection remain fully in force.
evidence_limits: >
  Source read at the revision above. The live database was NOT reachable this session (local proxy
  127.0.0.1:5433 refused); no claim below rests on a live query. Nothing was executed or measured.
changelog:
  - "0.1 (2026-09-20): first proposal. Research only."
  - "0.1 -> SUPERSEDED (2026-09-20): retained in place as the pre-verification record. Do not review this file; review v0.2."
---

# Gochara family — elevation proposal for independent review

**Evidence tags used throughout.**
`[S]` verified in source this session (file:line given) ·
`[R]` recorded in a repository artifact (cited; not re-verified live) ·
`[I]` my inference from `[S]`/`[R]` — plausible, not demonstrated ·
`[U]` unmeasured; a number that must be produced before it is relied on.

A reviewer should treat every `[I]` and `[U]` as an invitation to refute.

---

## 1. The proposal in one page

**The question asked.** Of `ka_gochara_sweep`, `ka_gochara`, `ka_gochara_v3_century_materialize`
(and `ka_gochara_resonance`): which do we keep, how do we get the most value at acharya-grade
quality, and how do we stop paying ~a day of build per chart.

**The answer proposed.**

1. **None of the three window-producers survives as it is; one successor does.** Each holds half of
   the right design and a disqualifying defect. `ka_gochara` (W2G) has the right *computation*
   (chart-independent arcs, event-driven) but the old scoring, a narrow scope, and — finding F3 — a
   reference-frame defect that invalidates its candidate instants. The century writer has the right
   *scoring and output shape* (bounded signed λ, hierarchy, chain milestones, honest vocabularies)
   but reverted to sampling a black box, which is where the day of build goes. The sweep is
   correctly retired history.
2. **The native's 2026-07-21 idea — "jump to the likely points without scanning everything" — is
   not merely a faster route to the same answer. It is the exact representation of what the v3
   engine computes.** As coded, λ_v3's activity term is a sum of fixed-height boxes around discrete
   events (F2). The current builder spends hours numerically probing a step function whose
   breakpoints are obtainable by arithmetic from an event list.
3. **Elevate the idea one level further: build one contact kernel and one class-independent contact
   ledger per chart, and make everything else a projection of it.** Transit geometry does not
   depend on event class, and most of it does not depend on the chart either. Today it is
   recomputed per class × per decade × per sample, and separately again by Sangam, Kshetra,
   Taranga and the sky calendar (F4). Geometry should be computed once; the 27 event classes,
   Sangam's predicates, Kshetra's primitives, and the Vedha/Moorti/Kota/Tara overlays become cheap
   reads of the same identified contacts.
4. **Quality rises with speed, not against it.** The same move removes a hidden cap of 3 peaks per
   decade per class (F13), makes overlays century-complete instead of ~460 days around "now" (F5),
   lets tangential near-stations register at all (F12), fixes day-grade Moorti (F6), and gives the
   coverage contract the strategy demands (L3-Q08).
5. **Expected cost: minutes per chart, not a day** `[U]` — derivation in §6.8; the repository's own
   ADJUDICATION-14 already recorded "build time is NOT the binding constraint (Tier A ≈ 40 s/chart)"
   `[R]`. No figure here is a promise; the benchmark contract of strategy §5 is the gate.

**What I am least sure of:** F3 is a source trace, not a runtime reproduction. F11/F13 are readings
of control flow that one executed substep would confirm or kill. The whole cost model is derived.
See §13.

---

## 2. What Gochara is *for* — true value versus wishful value

Product v3.0 §3.10 and §7 `[S]` set the bar, and they are stricter than what the family builds
today:

> "Distinguish a background period, enabling interval, specific contact, inhibiting condition,
> recurrence and inferred manifestation. A transit coincidence is not a complete activation
> mechanism. A precise astronomical timestamp does not confer equivalent precision on a forecast."
>
> "Moving from a long chapter to a short interval must preserve the same evidence identities."
>
> "The search horizon, resolution and method coverage bound any 'no eligible window' conclusion."

**True value (what Gochara can honestly own).** The *contact layer* of time: for this chart's own
qualified structures, which moving body touches which target, by which relation, from when to when,
how tightly, in which branch (direct/retrograde/stationary), under which convention, with what
searched coverage — identified stably so a chapter, an interval and an instant cite the same
evidence. This is strategy §3's **Contact** and **Search coverage** objects. It is geometry plus
qualification. It is knowable exactly and cheaply.

**Wishful value (what the current λ implicitly claims).** A single scalar "event-class intensity"
λ = PROMISE × PERMISSION × activity × modifiers × gates. That product multiplies together exactly
the things the product definition says to keep distinct — background period (daśā permission),
contact (activity), inhibition (vedha gates) — and labels the result by a *generic* event class
("marriage"), not by this chart's mechanism. It is a useful ranking projection. It is not the
asset's identity, and it is not an event probability (strategy §2: "Activation, intensity, evidence
agreement, event probability and external manifestation remain distinct").

**Reasonable-effort judgment.** The true value is achievable with modest effort *because almost all
of the required capital already exists in the repository* — it is scattered and unjoined, not
missing (§4 F4, F8). The wishful value (calibrated event probability) is L5's job and depends on
outcome data accruing; Gochara should feed it clean typed evidence and stop impersonating it.

---

## 3. The family as it actually is

### 3.1 Table ownership — resolving PROMPT_1's seed-vs-strategy contradiction

Method: read each writer's own table constants and DML, not its docstring or the registry.

| Asset | What the code writes `[S]` | What the seed registry says `[S]` | Verdict |
|---|---|---|---|
| `ka_gochara` (W2G) | **only** `kala_gochara_windows_v2`, generation `'2.0'` — `writers/ka_gochara.py:120`; the production table's name appears in the module only inside comments | `target_table: kala_gochara_windows`, `count_sql … generation='3.0'` — `asset_registry_seed.ts:2117-2125` | **Seed is wrong.** The cockpit count for `ka_gochara` is counting rows written by a *different asset* (the century writer). §N.4 cockpit-truth + §N.8 earned-signal defect. Strategy L3-A13 is right. |
| `ka_gochara_v3_century_materialize` | **both** `kala_gochara_windows_v2` (staging, `'g3_utkarsha'`) **and** `kala_gochara_windows` (production, `'3.0'`) — writer `:360, :482-487` | `target_table: kala_gochara_windows_v2`, `count_sql … generation LIKE 'g3_%'` — seed `:2196+` | Registry counts the *staging* copy; production rows are uncounted under this asset. |
| `ka_gochara_sweep` | retired; historically `kala_gochara_windows`, generation `'v1'` | RETIRED, same table, `generation='v1'` | Consistent. Protected by migration 540 `[R]`. |
| `ka_gochara_resonance` | `gochara_resonance_map` | same | Consistent. |

So `kala_gochara_windows` holds **v1 (protected) + 3.0 (century)**; `kala_gochara_windows_v2` holds
**2.0 (W2G) + g3_utkarsha (century staging)**. Two tables, four generations, three writers, and a
registry that attributes one writer's rows to another. Any delete-then-insert on either table is
generation-scoped in code, which is what currently keeps this safe — a convention, not a structure.

### 3.2 What each one really computes

| | `ka_gochara_sweep` (v1) | `ka_gochara` (W2G, "2.0") | century v3 |
|---|---|---|---|
| Finds dates by | daily grid, 36,525 days | arc substrate: exact contact instants | weekly grid over a black-box λ, then day-refine |
| Scores with | v1 `compute_lambda_e` (unbounded exp, negatives clamped) | **same v1 function, unchanged** ("changes HOW never WHAT") | v3 bounded signed λ, 2 of 10 mechanisms wired |
| Scope | 3→6 classes, century | point-shaped classes only, Tier-A bodies only, **±3 years** | 27 classes, century, all shapes |
| Recorded clean wall-clock | 35.6 h `[R]` | 6.5 h `[R]` | never cleanly measured; 270 substeps; one run OOM-killed at 6h21m `[R]` |
| Status | RETIRED, protected | active | active, **ON HOLD** |

Timing sources: `control/PLAN_FIGURE_RECONCILIATION_v1_0.md:176,325,1271`; SAMPŪRTI Δ3 log
2026-08-15; PARIŚEṢA ledger F-52 (which also records that the native's "~30 h" may have referred to
the sweep rather than the century writer — unresolved `[R]`). PK-R-12 formally retired the
century's "≤15–20 min" target as never-derived `[R]`.

### 3.3 Answer authorities outside the registry denominator

Four more places decide "when does a body reach a degree", each with its own numerics `[S]`:

| Engine | Where | Method | Frame handling |
|---|---|---|---|
| Scan | `pipeline/transit_search.py:301` | 0.5–1.0-day stepping on live Swiss + 20-iteration bisection | sidereal via Swiss flag |
| Arcs | `services/w2g/{arcs,crossings,solver}.py` + L0 `bg_gochara_arcs` | monotone-arc index + bracketed bisection on cubic spline, 1″ tolerance | **tropical, never converted — F3** |
| Kinematics | `services/ka_kshetra/stage0_kinematics.py` → `kala_field_kinematics` | cubic Hermite spline + Brent `xtol=1e-6 d`; contact *episodes* with dwell weight + trapezoid kernel | sidereal, correct (`:607`) |
| Sky diary | `writers/bg_sky_calendar.py` | reuses the scan; real Swiss eclipse functions | Lahiri only |

Importers of the scan engine: v1 and v3 gochara, `ka_sangam` (`engine.py:1087,1363`),
`ka_kshetra` stage 0, `taranga_service`, `bg_sky_calendar`, `ka_gochara/service.py`.

---

## 4. Findings

### F1 — Where the day goes `[S]` structure, `[U]` magnitudes
`interval_solver.find_threshold_crossings` evaluates λ on a 7-day grid, then 50 dense samples per
interval, then (`resolution_hierarchy`) ±7 days at 1-day steps per retained peak. Every evaluation
goes through `_eval_single` (`interval_solver.py:116`) with a **one-element array** — the function
named `evaluate_lambda_vector` never vectorizes. Every evaluation calls
`_gather_sentences_no_db` (`engine.py:1063`), which runs a **transit search over t±5 days for every
target × 9 primitives × up to 9 grahas**. Consecutive weekly samples search overlapping 10-day
windows. Off-grid sample times are unique floats and miss the exact-JD `lru_cache`
(`transit_search.py:202`). The whole function is under the global Swiss lock
(`engine.py:469 @serialized_swiss_state`), so threads cannot help (strategy §5 says as much). None
of it is shared across the 27 classes or 10 decades, although geometry is class-independent and
`ClassContext.fetch` is repeated 270 times (strategy P3 already names this).
Derived scale `[U]`: ≈620 evaluations × 270 substeps ≈ 1.7×10⁵ evaluations/chart; a ~25 h build
implies ≈0.5 s per evaluation.

### F2 — λ_v3's activity is a step function of an event list `[S]`
`find_aspect_events` (`transit_search.py:301-372`) emits only **exact crossings**; `orb_deg` never
defines an interval — it only scales a strength computed *at the crossing*, where the orb is ≈0.
`_compute_activity_v3` (`engine.py:821`) uses that per-event constant. Therefore
activity(t) = noisy-OR over events with |t − t_event| ≤ 5 d, each with a fixed p_i — a **sum of
boxes**. Its breakpoints are t_event ± 5.0 d. Consequences:
(a) the century curve is exactly reconstructible from events with zero sampling;
(b) bisection to 0.1 d is spending ~7 searches to locate a value known by subtraction;
(c) corroboration `[R]`: the R3 conformance battery reported `orb_decay` "flat at the disclosed
default with zero drift".
*Not fully read:* `_compute_permission_from_context` (guru-shani, AV, return legs use ephemeris).
If any leg is genuinely continuous in t, (a) weakens to "piecewise-smooth with few breakpoints" —
which the design in §6 still handles. **Reviewer: please check this.**

### F3 — W2G joins sidereal targets against tropical arcs `[S]` — HIGH, needs runtime repro
`resolve_target_degrees` (`w2g/materialize.py:156`) returns `target_longitude_deg`, which
enrichment reads from `chart_facts.longitude_sidereal` under `lahiri_chitrapaksha`
(`gochara_intensity/enrichment.py:139-150`). Those degrees go unmodified into
`ContactSolver.solve` over `DbArcSource`, whose arcs are built from `ephemeris_daily` rows with
`ayanamsha_id='tropical'` / column `tropical_longitude` (`w2g/db_source.py:35,80`;
`l0_ephemeris.py:16` "Lahiri subtracted at consumption"). I found **no ayanamsha term anywhere
between them** — not in `arcs.py`, `crossings.py`, `solver.py`, `materialize.py`, the writer, or
migration 538. Tests use single-frame synthetic fixtures and cannot see it.
If this trace is right, W2G's "exact contact instants" are the moments a body's *tropical*
longitude equals a *sidereal* number — ≈23.6°–25° away from the real contact: roughly two years
off for Saturn, ten months for Jupiter. Rows still get written because v1 scoring at those wrong
instants can be non-zero for other reasons `[I]`. This would also be a candidate explanation for
the MR-20 "low equivalence" finding that PK-R-11 closed as a comparator-scope asymmetry `[I]`.
**Kshetra stage 0 does this conversion correctly** (`stage0_kinematics.py:607`), which is part of
why §6 builds on it. *A one-body, one-degree check against Swiss settles this in minutes.*

### F4 — The repository already contains the elevated kernel, in pieces `[S]`
W2G contributes the **monotone-arc index**: cut each body's history at stations and 360° wraps and
every crossing is provably bracketed — a genuine candidate-coverage argument, which strategy §5
requires before sparse search is acceptable. Kshetra stage 0 contributes the **physics and
semantics**: Hermite spline, Brent roots, sidereal frame, contact *episodes* (t_in, t_peak, t_out,
core crossings), a **dwell weight** w = D/(D + D_nom) that makes slow and stationary passages count
for more, and a trapezoid kernel on *actual* separation. Stage 0's one disclosed weakness — a root
with no sign change on the daily grid is missed (`:18-20`) — is exactly what the arc decomposition
removes. Neither module knows the other exists.

### F5 — Overlays cover ~460 days; the century treats "not evaluated" as "clear" `[S]`
`ka_vedha_gochara/writer.py:86-87`: `HORIZON_BACK_DAYS = 60`, `HORIZON_FORWARD_DAYS = 400`; Moorti
likewise rolling and day-grade `[R, strategy L3-A06]`. v3's `quality_gates` "falls back to 1.0 when
no vedha rows overlap" (`engine.py` step 4d). Across ~98% of a century build, obstruction was never
evaluated and scores as unobstructed. This is strategy L3-U03's named failure ("unavailable
evaluation cannot look clear") and makes windows *incomparable across the horizon*: a 2027 window
is scored with vedha, a 2041 window without.

### F6 — Day-grade Moorti contradicts its own rule `[S]` rule, `[U]` error rate
Moorti grades a whole sign-stay by the Moon's nakshatra **at the moment of ingress**
(`ka_moorti_nirnaya/logic.py:9-13`). The implementation is "day-grade precision throughout" under a
campaign rail "No wave may be designed to REQUIRE sub-day precision" (`:36-37`). The Moon changes
nakshatra about once a day, so a day-grade ingress picks the wrong nakshatra a material fraction of
the time `[U]` — and the tier table changes between adjacent nakshatras. This is the concrete case
for the native's sub-day intuition.

### F7 — `ka_graha_sancara` PATH-A returns the day's noon position for any instant `[S]`
`ka_graha_sancara/engine.py` header: PATH-A reads the daily row, memo "keyed on
(T_rounded_to_day, ayanamsha)"; intra-day precision requires PATH-B, a live locked Swiss call on
the Moshier ephemeris. Four overlays sit on this service.

### F8 — Eight of ten v3 mechanisms are coded, cited, tested — and not called `[R]`+`[S]`
`mechanism_register.yaml` (MR-19 re-adjudication) records all ten as "DEFINED + CITED + CODED, NOT
ENGINE-WIRED". Since then only `w23_tara_bala` and `w30_nodal_drishti` are invoked
(`engine.py:100-101, 607, 628`). Un-invoked `[S]`: `w21_av_gating`, `w22_moorti_nirnaya`,
`w24_sade_sati`, `w25_kota_chakra`, `w26_real_eclipses`, `w27_annual_stack`, plus structural
`w28`/`w29` — ≈2,900 LOC imported only by calibration scripts. **This answers PROMPT_1 Q6:** the
consumers for Kota and the annual stack exist as modules; the declared `depends_on` edges are
aspirational, not false. Product §11.2 calls this "stranded knowledge".

### F9 — Targets come from a generic ontology, not from this chart's Bodha structures `[S]`
`ka_gochara_resonance/writer.py:1-40`: targets derive from `brahma_event_ontology` signature models
and `bg_transit_rules` (L0) plus L1 facts, yoga firings and MD lords. **No L2 input.** Four of eight
target types are the writer's own uncited synthesis (honestly flagged). Many of the 27 classes carry
"provisional" signature models inherited from a sibling class (`COVERAGE_QUALITY_NOTES`). Meanwhile
`ka_yojaka` compiles L2 mechanisms into predicates — for Sangam only. So the chart's *own*
mechanisms are timed by one engine and generic event classes by another, and product §12.2 ("a
participant's nearest transit contact is not automatically the activation of the whole
configuration") cannot be answered from Gochara at all.

### F10 — Registry truth (see §3.1) `[S]`

### F11 — `peak_date`'s precision claim outruns the function `[I]`
If activity is boxes (F2), the only sub-plateau variation in λ is the daily tara factor and gate
edges. "Day-refined true argmax" (`LAMBDA_V3_ARGMAX`, the only basis that earns `is_timing_window`)
would then mostly select the best-tara day inside a ~10-day plateau. That is a legitimate classical
refinement — but it should be *named as that*, not as a located extremum of contact intensity.

### F12 — Geometry the scan cannot see, and noise it invents `[S]`
(a) **Tangency:** a body that stations 0.2° short of a target never produces a sign change, so it
produces no event and contributes zero — while a fast exact crossing contributes fully. Classical
weighting is the reverse. Strategy §5 lists tangencies among what "must survive".
(b) **Phantom events:** `_shortest_arc_diff` flips sign at the anti-point; the crossing test fires
there, the bisection converges on the discontinuity, and an event is emitted with orb ≈180° and
strength 0 — harmless to the score, noise in `active_sentences`, and wasted search.
(c) **One window for all bodies:** ±5 d is sensible for Saturn and smears a two-hour Moon contact
across ten days, so with several targets the Moon is nearly always "on" — a background hum inside
`activity` `[I]`.

### F13 — The era tier is the decade; the real product is ≤3 peaks per class per decade `[I]`
The writer sets `lambda_thresh=0.0` (`:1940`); `is_above_threshold` is `>=` (`threshold.py:393`);
λ ∈ [0,1]. Every sample is "above", so each substep yields one era window spanning its decade —
corroborated by the writer's own docstring, which derived its row bound "assuming exactly one era
window per substep". Served substance is then the P90-admitted, 90-day-separated peaks, capped at
`MAX_PEAKS_PER_ERA_WINDOW = 3`. Recorded production: 943 rows for the native across 270 substeps
`[R]` ≈ 3.5 rows/substep — consistent. A cap of three timing claims per decade per class is a
**hidden top-K**, which the strategy forbids as evidence of absence. *The recorded ≥2-era case
(career_setback, MR-44/45) is not explained by my reading — a reviewer should probe it.*

---

## 5. Challenging the inherited assumptions

| Inherited position | Challenge | Proposed replacement |
|---|---|---|
| **Q1: "full century materialisation *or* a compact substrate with refinement"** | False dichotomy. It is only a trade-off while the century is expensive. | Materialise the **compact thing completely** (the contact ledger, full century), and derive windows from it deterministically. Both halves of Q1 are satisfied. |
| **"The Moon must be lazy because of cost"** (ADJ-14) | The cost that motivated this was *scoring* each candidate through a ~110 ms v1 call, not geometry. ADJ-14 itself says build time is not binding; storage and serving density are — and its 849 MB/chart figure assumed 3.2 KB *window* rows, not ~100 B *contact* rows. | Keep the three-rate idea, change its basis: Moon **ingress-type** events are chart-independent → global, once. Moon **degree contacts** are recomputable in microseconds → never persisted full-span, always available inside any window. |
| **"No wave may REQUIRE sub-day precision"** | A sensible rail when precision was expensive. It now forces a known-wrong Moorti (F6) and a day-rounded position service (F7). | Sub-day *computation* is free with the interpolant; sub-day *claims* stay governed by the product rule that a precise timestamp does not confer forecast precision. Separate the two. |
| **"2.0 changes HOW, never WHAT"** | Right as a verification discipline, wrong as a destination: the WHAT has defects (F2, F12). | Two explicit stages: **E — equivalence** (reproduce current semantics exactly from events; proves the machine) then **M — method repair** (orb-interval activity with dwell; versioned, explained deltas, native-ruled). Strategy §5 already mandates this separation. |
| **λ is the product** | Product §3.10 requires the components kept distinct. | The ledger and typed testimony are the asset; λ is one named, versioned projection among several. |
| **Daily snapshots vs. an exact service** | See §6.1 — neither. | A lock-free interpolant over stored knots *is* the exact service, at the cost of a table read. |
| **Two tables, four generations** | Safety by convention. | One owned surface per live authority; history moved to an immutable snapshot. |
| **Per-class substeps (270)** | An artefact of class-scoped geometry. | One geometry stage + 27 light projections. |

---

## 6. Target design

### 6.1 Astronomy in four tiers — answering "snapshot or service?"
The L0 store is **not used as a daily snapshot** in the fast path. It is a set of *knots* (noon UT,
tropical, 6-decimal) for a cubic interpolant whose measured worst error against Swiss is **0.314″**
`[R, W2G V3]`. For the Moon that is about half a second of time; for any body it is orders of
magnitude below an orb with astrological meaning. So between-snapshot motion is not lost — it is
*solved for*: a contact is a root of a smooth function, bracketed by the arc index and converged to
1″. Nothing is scanned, so nothing falls between samples.

| Tier | Holds | Cost profile | Why here |
|---|---|---|---|
| **T1 knots** — `ephemeris_daily` | 9 bodies × daily, longitude + speed | built once, global | tiny, exact at knots, convention-free (tropical) |
| **T2 interpolant + arc index** — in-process library over T1 and `bg_gochara_arcs` | position/velocity at any instant; every crossing of any degree | microseconds, **no Swiss lock, parallelisable** | this *is* the "exact service", without service overhead |
| **T3 sky diary** — `bg_sky_calendar` (extended) | chart-independent events: sign / nakshatra / pada / kakshya-boundary ingresses, stations, eclipses, slow conjunctions, combustion, tithi boundaries | once per ayanamsha, global | every chart reads the same diary; Tara, Moorti, Kota, Sade-Sati, Vedha become joins against it |
| **T4 live Swiss** | location-dependent quantities (lagna, sunrise, hora, eclipse visibility); optional *polish* of a served instant; audits | locked, serial, rare | the only place a live call is genuinely needed |

A live service for everything would be slower *and* serial (global lock); snapshots alone are
lossy (F7). T2 gives exactness without the overhead. Multi-ayanamsha comes free: one tropical
substrate, sidereal = tropical − ayanamsha(t), where ayanamsha(t) is smooth and ~50″/yr — which is
also the correct fix for F3.

### 6.2 The contact kernel
One library, the union of what already works: **arc index** (coverage proof; constant DB reads) +
**sidereal frame term** + **Brent/bisection to declared tolerance** + **episodes** (t_in, t_exact
or t_closest, t_out, core crossings, branch, truncation flags) + **dwell weight**. Tangency becomes
a first-class episode with `exact_crossing=false` and a closest-approach orb. Anti-point phantoms
cannot occur. Proposed home: **elevate `ka_graha_sancara`** (L3-A01, literally "planetary
movement", already the declared T0 service under Vedha/Moorti/Kota/Sudarshana) from
position-at-noon to position-and-contact-at-T. No new asset id; the 22-member denominator is
unchanged; the DAG already routes through it. `pipeline/transit_search.py` is **not edited** —
consumers migrate off it one at a time — so strategy items P3/P4 no longer collide with the frozen
L0 `bg_sky_calendar` closure. (That answers PROMPT_1's `transit_search.py` change-protocol item:
the protocol is *don't change it; strangle it*.)

### 6.3 The contact ledger (per chart, class-independent)
Strategy §3's **Contact** object, literally: moving body · target identity (`fact_id` of the L1
point, or sign/nakshatra/bhava/kakshya cell) · relation (conjunction, graha-dṛṣṭi offset,
rāśi-dṛṣṭi, ingress, return) · qualified orb + source · branch · t_in / t_exact / t_out + bracket
+ tolerance · dwell · convention vector · kernel version · deterministic `contact_id`.
Target set = **union** of resonance targets, Yojaka predicate targets and Kshetra primitives, so one
solve serves all three. Persist slow and medium bodies (≈1.9×10⁵ slim rows/chart `[R, V4]`→
tens of MB `[U]`); recompute Moon contacts on demand with the same ids. Whether to persist Tier B
is a storage ruling, not a compute one.

### 6.4 Typed testimony, kept apart
Background period (daśā stack, per system, with applicability) · enabling interval (slow-body sign
occupation, Sade-Sati phase, AV gate state) · specific contact (ledger) · inhibition (vedha, per
school, signed, de-duplicated against Vighnakara per L3-U03) · modifiers (Tara, Moorti, Kota, annual
stack, real eclipses, nodal dṛṣṭi — i.e. the eight stranded mechanisms, each now an interval
function over T3, century-complete). Each carries method, source, applicability, and an
**evaluated / not-evaluated / inapplicable** state — so "unavailable" can never again read as
"clear" (F5).

### 6.5 Projections
(1) **Event-class windows** — today's λ as a *named, versioned* projection, computed in closed
form between breakpoints; era ⊃ month ⊃ day hierarchy with parent ids preserved; chain milestones
unchanged; `peak_basis` vocabulary extended so a tara-selected day says so (F11); **no peak cap** —
all admitted peaks stored, serving budgets apply at serve time (§N.6). (2) **Mechanism windows** —
the same machinery keyed by L2 structure instead of event class, feeding Sangam/Kalasutra.
(3) **Now / ahead / election** reads — direct ledger queries, including Moon-scale drill-down.

### 6.6 Coverage contract (L3-Q08)
Every ledger partition and every projection states: horizon requested/completed, bodies and
relations searched, tolerance, conventions, targets resolved vs unresolved (e.g. bhava targets with
no exact degree), tiers persisted vs on-demand, and mechanisms evaluated vs not. Three answers
become machine-distinguishable: *none in the searched scope* · *outside the searched scope* ·
*search incomplete*.

### 6.7 What stays exactly as it is
Frozen `WriterBase`/orchestrator (the successor is an ordinary heavy writer with far fewer
substeps); §N.3 delete-then-insert; §N.5 (every target is an L1 `fact_id` reference — and frame
conversion is a *reference* to `l0_ephemeris`'s convention, as stage 0 already does); fingerprint
delta-skip (MR-38/F-52 machinery carries over); migration-540 protection; serving schema and the
three `gochara_*` tools; honest-empty discipline.

### 6.8 Cost model — derived, not measured `[U]`
Arcs for the whole epoch: ~48 s, once, global `[R]`. Contact solve ≈111 µs each `[R]`: Tier A
≈4×10⁴ contacts ≈ 5 s; all non-Moon ≈1.9×10⁵ ≈ 20 s; even all nine bodies ≈7.9×10⁵ ≈ 90 s.
Closed-form projection over ≈10⁴–10⁵ breakpoints × 27 classes: seconds to low minutes. DB write of
~10⁵ slim rows by COPY/batch: tens of seconds. **Expectation: single-digit minutes cold, seconds
warm** — to be replaced by measurement under strategy §5's benchmark contract (wall, CPU, RSS,
Swiss-lock time, SQL count, WAL; cold/warm/resume/horizon-extension/dependency-correction).

---

## 7. Disposition — which assets we keep

| Asset | Disposition | Preserved | Notes |
|---|---|---|---|
| `ka_gochara_sweep` | **Stay retired.** Snapshot-protected, never rebuildable. | v1 corpus as validation capital | Move its rows out of the live table only via an authorised, restorable migration — a ruling, not a default. |
| `ka_gochara_resonance` | **Retain and enrich.** | 8 target types, citation discipline | Add L2-structure bindings via Yojaka (L3-U01); stop first-root de-dup; route provisional signature models to the L0 authority. |
| `ka_gochara` | **Retain the id as the single Gochara windows authority; replace the implementation.** | arc solver, fingerprinting, horizon attestation, protection rails | Its v1 scoring, point-only/Tier-A/±3y scope and frame defect do not carry over. |
| `ka_gochara_v3_century_materialize` | **Supersede after migration — its engine becomes `ka_gochara`'s scoring.** | λ_v3, signed channels, hierarchy, chain rows, all vocabularies, scoring signature, the 10 mechanisms | The *hold closes legitimately*: not by deferral, but because the capability is delivered by the successor. |
| `ka_graha_sancara` | **Enrich** into the contact kernel (§6.2). | Swiss state safety, PATH-B | F7 repaired. |
| `bg_gochara_arcs`, `bg_sky_calendar` (L0) | **Reuse; bounded amendment request** to L0 for diary families (nakshatra/pada/kakshya ingress, combustion, per-ayanamsha). | everything | L0 is frozen: this is an owner-routed amendment, not an L3 edit. |

Net: **two per-chart Gochara writers (resonance + windows) on one shared kernel**, versus three
active writers and four private engines today. Consolidating A13+A14 changes the strategy's
22-member denominator and therefore needs a strategy amendment (DP-SD) — flagged in §11.

---

## 8. Upstream readiness — is what Gochara stands on good enough?

| Upstream | State for this use | Gap → owner |
|---|---|---|
| L0 `ephemeris_daily` | **Ready.** 0.314″ `[R]` | none; note tropical/noon/6-dp conventions are load-bearing |
| L0 `bg_gochara_arcs` | **Ready as an index.** | consumer must apply the frame term (F3) → L3 |
| L0 `bg_sky_calendar` | **Partly.** Sign ingress, stations, real eclipses, Jup–Sat only; Lahiri only | diary families + ayanamsha variants → L0 amendment |
| L0 `brahma_event_ontology` | **Partly.** Many provisional signature models | dedicated sourcing pass → L0; *not* to be invented in L3 |
| L0 `bg_transit_rules`, AV gates, moorti table, vedha scale | usable, cited | per-rule executable coverage map → L0 |
| L1 natal facts, `chart_dashas` (7 systems), AV, Sade-Sati, yoga firings | **Ready** (accepted L1) | pin generation/digest per strategy §4 |
| L2 Bodha mechanisms | **Ready upstream, unused here** | the largest value gap (F9) → resonance + Yojaka contract |
| L3 Vedha, Moorti | **Not century-ready** (−60/+400 d, day-grade) | re-express over T3; becomes cheap and complete |
| L3 Kota, Tithi-praveśa, Sudarśana | built; consumers coded but unwired (F8) | wire behind a *qualified operator* each, with ablation — native/method ruling per mechanism |

Two things are **not** fixable by engineering and must be routed, not smoothed: provisional
ontology signatures, and any mechanism whose classical method qualification is missing.

---

## 9. Synergy — how Gochara uses and feeds the other time assets

**Uses (computational inputs):** resonance targets · L1 natal/daśā/AV/Sade-Sati · L0 diary and rules
· Vedha/Moorti/Kota/annual stack as *typed testimony* (not silent multipliers).
**Feeds (one geometry, many readers):**

| Consumer | Today | With the ledger |
|---|---|---|
| `ka_sangam` (7 of 21 assets hang off it) | private live scan per predicate/mode; caps | reads identified contacts; savings fund *full* predicate coverage (strategy P4) |
| `ka_kshetra` S0/S1 | private Hermite/Brent pass, 33.8 h asset | S0 *is* the kernel; one computation, two consumers |
| `ka_vedha_gochara`, `ka_moorti_nirnaya`, `ka_kota_chakra` | rolling day-grade scans on a day-rounded service | century-complete interval joins on T3; Moorti at the true ingress instant |
| `ka_kalasutra`, `ka_vighnakara`, `ka_taranga` | inherit Sangam's geometry and caps | inherit complete recurrence; Taranga stops re-scanning |
| `ka_muhurta_seva` / `ka_tulana` | separate election path | Moon-scale drill-down from the same kernel; matched candidates carry contact ids |
| L4 Phala, L5 prospective ledger, `judgment_query` timing anchor, Paripraśna confidence tier | read windows | same schema, plus stable evidence ids from chapter → interval → instant |

Edge typing per strategy §6.3: the kernel is a **shared definition/service** edge, not a build
dependency between per-chart assets — so it adds no serial ordering. The ledger is a **computation**
edge for Gochara and a candidate one for Sangam/Kshetra; legacy Gochara rows remain a
**validation** edge for Kshetra. No L3→L4/L5→L3 cycle is introduced.

---

## 10. Sequence and gates

No step below is authorised by this document. Steps 0–2 touch no production data.

| Step | Work | Gate |
|---|---|---|
| **0 — Settle the facts** | Reproduce F3 (one body, one degree, vs Swiss). Execute one century substep under a profiler: confirm F1 split, F2 (breakpoints at t_event ± 5 d), F13 (era = decade). Read `_compute_permission_from_context` fully. | Findings confirmed, corrected or withdrawn — in writing |
| **1 — Kernel, disposable DB** | Unify arc index + stage-0 physics + frame term behind `ka_graha_sancara`. | Agreement with Swiss to declared tolerance incl. stations, retrograde triple passes, tangencies, wrap, Moon perigee; read-count constant in targets |
| **2 — Stage E (equivalence)** | Event-driven reproduction of *current* λ_v3 semantics for the protected charts, offline. | Byte/row parity with the gen-3.0 corpus where v3 was right; every divergence classified (grid artefact / v3 defect / new bug) — none unclassified. Measured benchmark |
| **3 — Ledger + coverage contract** | Persisted contact ledger; typed testimony; honest states. | Strategy §3 field dossier; L3-Q08 three-way negative proven |
| **4 — Stage M (method repair)** | Orb-interval activity with dwell; per-body windows; uncapped peaks; wire mechanisms one at a time with ablation. | **Native method ruling per change**; explained deltas vs Stage E; §N.7 golden values |
| **5 — Consumers** | Vedha/Moorti/Kota onto T3; Sangam and Kshetra S0 onto the ledger. | Per-consumer equivalence, then caps removed |
| **6 — Cutover** | Authorised rebuild; registry repair (F10); supersede century; snapshot history. | Fresh native authorisation; restorable rollback; serving tools unchanged |

First vertical slice: **Step 0 + Step 1 + Step 2 for one class on one chart.** It is small, touches
nothing live, and either validates or kills the central claim.

---

## 11. Rulings needed from the native

1. **Disposition:** accept "one successor under the `ka_gochara` id; century superseded after
   migration"? (PROMPT_1 Q1/Q2.) Requires a strategy denominator amendment.
2. **Kernel home:** elevate `ka_graha_sancara`, or a new shared service?
3. **Sub-day rail:** retire "no wave may require sub-day precision" for *computation*, keeping the
   product rule on *claims*?
4. **Stage M changes**, each separately: orb-interval activity; dwell weighting; per-body activity
   window; removing the 3-peak cap.
5. **Mechanism wiring (F8 / PROMPT_1 Q6):** integrate Kota, annual stack, Moorti, AV, Sade-Sati,
   real eclipses — which, in what order, under what qualification?
6. **Protected history (PROMPT_1 Q4):** keep v1 rows in the live table under generation scoping, or
   move to an immutable snapshot table by authorised migration?
7. **Moon policy:** persist Tier B? Moon strictly on-demand?
8. **Targets (F9):** bind Gochara to L2 structures via Yojaka in this campaign, or defer?
9. **F3:** if confirmed, how are existing generation-2.0 rows to be labelled in the meantime?

## 12. What I would like the reviewer to attack

- **F2 is the keystone.** Is there any term in λ_v3 that varies continuously in t? If so, does the
  closed-form projection still hold between breakpoints?
- **F3.** Find the ayanamsha conversion I missed, or confirm there is none.
- **Coverage proof.** Does cutting at stations and wraps truly bracket *every* root, including
  ayanamsha-shifted targets within minutes of a station, and the true node's short prograde
  excursions?
- **Interpolant adequacy.** 0.314″ was measured for longitude; are there consumers needing latitude
  or distance (eclipse magnitude, graha-yuddha) that the knots cannot serve?
- **Does consolidation hide a legitimate variant?** Is there any consumer that needs W2G's
  v1-scored rows or the century's staging copy as such?
- **Kernel-in-`ka_graha_sancara`:** does making a T0 service richer create a fan-out risk that a
  separate asset would contain better?
- **Stage E parity target.** If v3's own output is artefactual (F11, F13), is parity with it the
  right acceptance test, or should Stage E be validated against an independently specified small
  reference instead (strategy §5 says the old output "is not the unquestioned parity oracle")?
- **Anything here that is more confident than its evidence.**

## 13. Not established

No code was run. No live row was read. F3, F11, F13 and the entire cost model are unverified by
execution. The Moorti error rate, ledger storage size, and the fraction of build time in each F1
component are unmeasured. I did not read `_compute_permission_from_context`, the w2x mechanism
bodies, Sangam's scoring, or Kshetra stages 1–8 in full. The recorded ≥2-era-window case is
unexplained by my reading of F13. Whether the native's ~25 h refers to the century writer or the
sweep remains, per the repository's own ledger, unresolved.
