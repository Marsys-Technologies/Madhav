---
artifact: GOCHARA_FAMILY_ELEVATION_PLAN
version: "0.2"
status: SUPERSEDED
superseded_by: GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md  # after independent review ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md (PROCEED_WITH_AMENDMENTS)
supersedes: GOCHARA_FAMILY_ELEVATION_PROPOSAL_v0_1.md (retained in place, SUPERSEDED)
produced_on: 2026-09-20
produced_by: Claude Code (Fable 5.1), research + verification session at native request
intended_reviewer: Codex / gpt-astra independent challenge, then native ruling
native_priorities: "1. quality  2. build efficiency  3. the surrounding ecosystem matters as much as the asset"
governing_strategy: ../../MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (APPROVED_STRATEGY, DP-SD-017)
governing_execution_brief: ../../MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md
campaign_plan: ../MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md (DRAFT_FOR_NATIVE_REVIEW)
product_parent: ../../../../MADHAV_PRODUCT_DEFINITION_v3_0.md
responds_to: ../discussion_prompts/PROMPT_1_GOCHARA_FAMILY.md
evidence: evidence_gochara/ (7 read-only scripts + OUTPUT_2026-09-20.txt)
source_revision: 5d8252dbe (branch codex/madhav-l3-claude-code, worktree /Users/Dev/madhav-l3/integration)
does_not_authorize: >
  Any production code change, build, rebuild, migration, registry edit, lifecycle change, or release
  of the century hold. The native's 2026-08-21 standing order (no gochara re-materialization without
  fresh explicit authorization) remains in force. Execution-brief §3 already authorizes local source,
  tests, fixtures, benchmarks and disposable databases; nothing beyond that is claimed here.
evidence_limits: >
  The live database was unreachable all session (127.0.0.1:5433 refused). Every executed result used
  the repository's own fixture context (2 resonance targets, conn=None) and Swiss Ephemeris. No
  production row was read. Production target counts per class are therefore unknown.
changelog:
  - "0.2 (2026-09-20): verification pass. F2, F3, F13 moved from inference to EXECUTED. Build cost
     measured per evaluation and per primitive. New findings F14 (activity saturation), F15 (uncited
     kakshya fixture approximation dominates cost and signal), F16 (eclipse proxy timestamps are
     search-window artefacts), F17 (DB protection of the v1 corpus was removed by migration 588).
     Three v0.1 recommendations corrected: kernel home, L0 amendment, history handling. Rulings now
     carry recommendations. Implementation plan rewritten as work packets against the campaign's
     own acceptance machinery."
  - "0.1 (2026-09-20): first proposal, research only."
---

# Gochara family — elevation plan, v0.2

**Evidence classes.**
`[X]` **executed** this session — script in `evidence_gochara/`, output in `OUTPUT_2026-09-20.txt` ·
`[S]` verified in source (file:line) · `[R]` recorded in a repository artifact ·
`[I]` inference · `[U]` unmeasured.

---

## 1. The answer

**Which asset do we keep?** One windows asset, under the id **`ka_gochara`**, with a new
implementation that joins what the three existing writers each got half-right. `ka_gochara_resonance`
is kept and enriched. `ka_gochara_v3_century_materialize` is superseded *after* migration — its
scoring engine, hierarchy and vocabularies move into the successor, so its hold closes by delivery,
not deferral. `ka_gochara_sweep` stays retired; its v1 rows stay where they are, re-guarded (§8 R6).

**Why not just keep one of them as is?**

| | Right | Disqualifying |
|---|---|---|
| `ka_gochara` (W2G) | The native's idea, built: chart-independent arcs, exact event solving, ~1″ `[X]` | **Computes contacts in the wrong zodiac** — sidereal natal degrees solved against tropical arcs. Saturn 763 d, Jupiter 349 d, Mars 33 d from the true contact `[X]`. Also v1 scoring, point classes only, ±3 y. |
| century v3 | The scoring, hierarchy, chain rows, honest vocabularies | Samples a black box: every one of ~1.7×10⁵ evaluations per chart re-runs a transit search `[S]`; the transit term it produces is **saturated at 0.996–1.000 at all times** `[X]`; era windows are the whole decade `[X]`; ≤3 peaks per class per decade `[S]`. |
| sweep v1 | — | 35.6 h, retired, no writer `[R]` |

**The central result of this pass.** λ_v3 is *exactly* a step function of a dated event list
(F2) — so the native's "jump to the likely points" is not an approximation of the current engine,
it is its exact form. A proof of concept gathering events **once** and evaluating in closed form
reproduces the real engine to <10⁻⁹ on seven of eight primitives at **6,745× lower per-instant
cost** `[X]`. The eighth is an artefact (F16).

**And the uncomfortable one.** Speed is the smaller problem. As built, the Gochara *contact* signal
carries almost no information into λ (F14): it is drowned by the Moon and by an uncited fixture
approximation the engine's own docstring says is skipped (F15). What varies in today's windows is
daśā permission and the Moon's tara, not transits. **Quality — the native's first priority — is
therefore where most of the value is, and the fast kernel is what makes repairing it affordable.**

**What I still do not know:** production target counts per class (DB down) — they scale both the
measured build cost and the saturation; whether migration 588 is applied in production; and the
recorded ≥2-era-window case, which my reading of F13 does not explain.

---

## 2. What was verified, and how

| # | Claim | Status | Evidence |
|---|---|---|---|
| F2 | activity(t) is a sum of boxes with edges at event ± 5.0 d | **`[X]`** 223 observed change points, 0 outside a predicted edge | `E2` |
| F2′ | PERMISSION is a weighted count of 12 booleans → also a step function | `[S]` `engine.py:1157-1245` | — |
| F3 | W2G solves sidereal targets on tropical arcs | **`[X]`** real `build_arcs`+`ContactSolver`, checked against Swiss | `E1` |
| F1 | evaluation cost is ~92 % event search | **`[X]`** 64 ms/eval at 2 targets; 58.7 ms is search | `E2`,`E4` |
| F13 | threshold 0.0 with `>=` ⇒ one "active interval" = whole range, even when λ ≡ 0 | **`[X]`** | `E5` |
| F14 | activity is saturated; the Moon supplies 137 of 202 sentences | **`[X]`** | `E3` |
| F15 | kakshya runs an uncited "equal_eighths_fixture_approximation" on the served path; 59 % of cost, 73 % of sentences | **`[X]`**+`[S]` `primitives.py:686-700` | `E3`,`E4` |
| F16 | `eclipse_degree` stamps events at the caller's window edge | **`[X]`** | `E7` |
| PoC | one gather + closed form ≡ engine on 7/8 primitives | **`[X]`** max diff 2.1×10⁻⁴, all from F16 | `E6`,`E7` |
| F17 | DB-level protection of v1 rows removed 2026-08-23 | `[S]` `migrations/588_remove_asset_build_protection.sql` | — |
| F5 | Vedha overlay covers −60/+400 d | `[S]` `ka_vedha_gochara/writer.py:86-87` | — |
| F8 | 8 of 10 mechanisms coded, not invoked | `[R]` `mechanism_register.yaml` MR-19 + `[S]` `engine.py:100-101` | — |
| F10 | seed mis-attributes `ka_gochara`'s table and count | `[S]` `asset_registry_seed.ts:2117-2125` vs `writers/ka_gochara.py:120` | — |

All scripts are read-only, need no database, and resolve the repository root relative to their own
path. `python evidence_gochara/E1_w2g_frame_defect.py` from anywhere.

---

## 3. What Gochara is for

Product v3.0 §3.10 `[S]`: *"Distinguish a background period, enabling interval, specific contact,
inhibiting condition, recurrence and inferred manifestation. A transit coincidence is not a complete
activation mechanism. A precise astronomical timestamp does not confer equivalent precision on a
forecast. … Moving from a long chapter to a short interval must preserve the same evidence
identities. … The search horizon, resolution and method coverage bound any 'no eligible window'
conclusion."*

**True value — ownable, exact, cheap:** the *contact layer of time*. For this chart's own qualified
structures: which body touches which target, by which relation, from when to when, how tightly, in
which branch, under which convention, with what searched coverage — stably identified so that a
chapter, an interval and an instant cite the same evidence. These are strategy §3's **Contact** and
**Search coverage** objects.

**Wishful value — what today's single λ implies:** an event-class intensity that multiplies
background period × contact × inhibition into one scalar labelled by a *generic* class. It is a
useful ranking projection, not the asset's identity and not a probability (strategy §2).

**Achievable with reasonable effort?** Yes — because the capital exists and is merely unjoined
(F4), and because the verification above removes the largest technical unknown. The genuinely hard
part is not engineering: it is the method rulings of §8 R4/R5, which must be made to acharya
standard and cannot be delegated to code.

---

## 4. The family as it is

### 4.1 Table ownership (resolves PROMPT_1's contradiction)

| Asset | Code writes `[S]` | Seed says `[S]` | Verdict |
|---|---|---|---|
| `ka_gochara` | only `kala_gochara_windows_v2`, gen `'2.0'` | `kala_gochara_windows`, count `generation='3.0'` | **Seed wrong** — the cockpit count is another asset's rows (§N.4, §N.8). Strategy L3-A13 is right. |
| century v3 | `_v2` (`'g3_utkarsha'`) **and** `kala_gochara_windows` (`'3.0'`) | `_v2`, count `LIKE 'g3_%'` | Registry counts the staging copy; production rows uncounted. |
| sweep | retired; `kala_gochara_windows` `'v1'` — 38,287 rows, **no registered writer** `[R, mig 588]` | consistent | Irreplaceable except from one dump. |
| resonance | `gochara_resonance_map` | consistent | — |

### 4.2 Four private engines answer "when does a body reach a degree" `[S]`

| Engine | Method | Frame | Used by |
|---|---|---|---|
| `pipeline/transit_search.py` | 0.5–1 d stepping on live Swiss + bisection | sidereal | v1, v3, Sangam, Kshetra S0, Taranga, `bg_sky_calendar` (frozen L0) |
| `services/w2g` + `bg_gochara_arcs` | monotone-arc index + bisection on spline | **tropical, unconverted** | `ka_gochara` |
| `ka_kshetra/stage0_kinematics.py` | Hermite + Brent 10⁻⁶ d; episodes; **dwell weight** | sidereal, correct (`:607`) | Kshetra |
| `bg_sky_calendar` writer | reuses the scan; real Swiss eclipse calls | Lahiri | L0 |

### 4.3 The cutover mechanism already exists `[S]`
`kala_gochara_authority(chart_id → authoritative_generation)`, honoured by every reader I checked:
the three `gochara_*` MCP tools, `reading_checklist.ts:1040-1070`, `engine_tier.ts`, Kshetra stage 4.
The natural key already includes `generation` (migration 568). A new generation can therefore be
written **beside** existing rows, stay invisible, and go live per chart by one row — and roll back
the same way.

---

## 5. Findings

**F1 — Where the day goes `[X]`+`[S]`.** Weekly grid → 50 dense samples → ±7 d day-refinement,
≈620 evaluations/substep × 270 substeps ≈ **1.7×10⁵ evaluations/chart** `[S]`. Each goes through
`_eval_single` with a one-element array and re-runs `_gather_sentences_no_db` over t ± 5 d for every
target × 9 primitives, under the global Swiss lock. Measured: **64 ms per evaluation at 2 targets**,
≈29 ms per target `[X]`. So build ≈ 1.7×10⁵ × 29 ms × T ≈ **1.35 h × T**, T = targets in a class:
T≈18 reproduces the native's ~25 h `[I]` (T unknown — DB down). Nothing is shared across 27 classes
or 10 decades; `ClassContext.fetch` runs 270 times.

**F2 — λ_v3 is exactly a step function `[X]`+`[S]`.** Events are exact crossings only
(`transit_search.py:301-372`); the per-event strength is fixed at the crossing; activity is a
noisy-OR over events within ±5 d (`engine.py:821`). PERMISSION is a weighted count of booleans;
tara, nodal dṛṣṭi and vedha gates change only at ingress or interval edges. Every factor is
piecewise-constant. **Breakpoints are obtainable by arithmetic.**

**F3 — W2G is in the wrong zodiac `[X]`.** `resolve_target_degrees` (`w2g/materialize.py:156`)
passes `chart_facts.longitude_sidereal` straight to a solver whose arcs come from
`ephemeris_daily.tropical_longitude` (`w2g/db_source.py:35,80`). No ayanāṃśa term exists anywhere on
the path. Tests use single-frame fixtures. *Possibly* the real cause of the MR-20 "low equivalence"
finding that PK-R-11 closed as a comparator asymmetry `[I]`. Generation-2.0 rows are not served
(authority is never `'2.0'`), so the harm is contained — but the asset is `CURRENT` and buildable.

**F4 — The right kernel already exists, in two unconnected halves `[S]`.** W2G: the monotone-arc
index — cut at stations and wraps and every crossing is *provably* bracketed, the candidate-coverage
argument strategy §5 demands. Kshetra S0: correct frame, Brent roots, contact **episodes**
(in/peak/out/core), **dwell weight** D/(D+D_nom), trapezoid kernel on *actual* separation. S0's one
disclosed gap — a double root inside one day-pair is missed (`:18-20`) — is precisely what arcs fix.

**F5 — Overlays are ~460 days wide; the century reads "not evaluated" as "clear" `[S]`.** Vedha
`HORIZON_BACK_DAYS=60 / FORWARD=400`; `quality_gates` falls back to 1.0. Strategy L3-U03's named
failure; it also makes a 2027 window and a 2041 window incomparable.

**F6 — Moorti is day-grade against its own rule `[S]`.** Rule: Moon's nakshatra *at the moment of
ingress* (`ka_moorti_nirnaya/logic.py:9-13`); implementation: day-grade, under a rail forbidding
sub-day dependence (`:36-37`). The Moon changes nakshatra roughly daily. Error rate `[U]`.

**F7 — `ka_graha_sancara` PATH-A answers any instant with that day's noon position `[S]`.**

**F8 — Eight of ten mechanisms are cited, coded, tested, never called `[R]`+`[S]`.** Includes
`w25_kota_chakra` and `w27_annual_stack` — so PROMPT_1 Q6's "declared but unconsumed" inputs have
consumers waiting; the edges are aspirational, not false.

**F9 — Targets come from a generic ontology, not this chart's Bodha structures `[S]`.** No L2 input
to resonance; many of 27 classes carry provisional signature models inherited from a sibling; four
of eight target types are the writer's own uncited synthesis (honestly flagged). `ka_yojaka` compiles
L2 mechanisms — for Sangam only.

**F10 — Registry truth** — §4.1.

**F11 — `peak_date` claims more than the function supports `[I]`.** With activity saturated (F14),
the sub-plateau variation that "day-refined true argmax" finds is mostly the daily tara factor. A
legitimate classical refinement — to be *named as such*, since `LAMBDA_V3_ARGMAX` is the only basis
that earns `is_timing_window`.

**F12 — Geometry the scan cannot see, and noise it invents.** Tangency (a station 0.2° short) makes
no sign change, so no event `[S]` — the opposite of classical weighting. The shortest-arc function
flips at the anti-point and emits phantom events with strength 0: **11 of 202 sentences** `[X]`.

**F13 — The era tier is the whole range `[X]`.** `lambda_thresh=0.0` (writer `:1940`) with `>=`
(`threshold.py:393`): every sample qualifies. E5: a range where λ ≡ 0 still yields one "active
interval" spanning it. The served substance is the P90-admitted, 90-day-separated peaks capped at
`MAX_PEAKS_PER_ERA_WINDOW = 3` — a hidden top-K. Recorded production ≈3.5 rows/substep `[R]` agrees.

**F14 — The contact signal is numerically mute `[X]`.** With all bodies, activity ∈ [0.996, 1.000]
at every sampled date. Remove the Moon: 0.00–0.999. Slow bodies only: 0.00–0.90 — *that* varies and
discriminates. Cause: one ±5 d window for every body plus noisy-OR over ~12–34 concurrent sentences.
More targets saturate harder. **Consequence: today's Gochara windows are, in effect, daśā windows
modulated by tara.**

**F15 — An uncited fixture approximation is the largest contributor `[X]`+`[S]`.** On the served
path (`conn=None`) `kakshya_cell_crossing` does *not* degrade to `[]` as `engine.py:1063`'s docstring
states; it falls back to `"equal_eighths_fixture_approximation"`, `uncited_extension=True`
(`primitives.py:686-700`), emitting a crossing for 9 bodies × 8 boundaries per target with a default
strength 0.5. It is **147 of 202 sentences and 59 % of evaluation cost**. The engine removed
`sarvatobhadra_vedha` from activity for exactly this reason (IR-6); the same logic was never applied
here. A §N.7 docstring-versus-behaviour defect, and the cited BPHS Ch.66 boundaries in L1 go unused.

**F16 — `eclipse_degree` timestamps are search-window artefacts `[X]`.** Its events land at
t + 5.0000 / t − 4.9998 — the edge of the caller's window. It is a proximity *state*, not a dated
event; `bg_sky_calendar` already calls the underlying function "a coarse orb-based proxy, not real
eclipse geometry" `[S]`. Real eclipses exist in L0, and `w26_real_eclipses` is written and unwired.

**F17 — The v1 corpus has no database guard `[S]`.** Migration 588 (native instruction 2026-08-23)
dropped the protection triggers because they were keyed on `asset_id` and blocked the legitimate
gen-3.0 writer. 38,287 v1 rows with no writer now rely on one dump
(`control/snapshots/20260823_pre_protection_removal/`). The migration's own advice: *"If protection
is ever reinstated, key it on (table, generation)."* PROMPT_1 and v0.1 of this document both assumed
the guard still existed. Whether 588 is applied in production: `[U]`.

---

## 6. Assumptions challenged

| Inherited | Challenge | Replacement |
|---|---|---|
| Q1: full century **or** compact substrate | Only a trade-off while the century is expensive | Materialise the compact thing **completely** (contact ledger, full century); derive windows. Both. |
| The Moon must be lazy for cost (ADJ-14) | The cost was *scoring* via a ~110 ms v1 call; ADJ-14 itself says build time is not binding `[R]` | Moon **ingress** events: in-kernel, seconds. Moon **degree contacts**: on demand. And per F14 the Moon should not be in the activity noisy-OR at all. |
| "No wave may REQUIRE sub-day precision" | Sensible when precision was costly; now forces a known-wrong Moorti | Free sub-day *computation*; product rule still governs sub-day *claims*. |
| "2.0 changes HOW, never WHAT" | Right as a harness, wrong as a destination (F14–F16) | **Stage E** equivalence, then **Stage M** method repair, separately ruled — strategy §5 mandates the split. |
| λ is the product | Product §3.10 requires the parts kept distinct | Ledger + typed testimony are the asset; λ is one named projection. |
| Daily snapshot vs exact service | Neither — §7.1 | Lock-free interpolant over stored knots. |
| Put the kernel in `ka_graha_sancara` *(my v0.1)* | It is a hub; editing it invalidates four assets' accepted digests (campaign plan §3) | **New module, no asset id**; consumers adopt one packet at a time. |
| Ask L0 to extend the sky diary *(my v0.1)* | L0 is frozen; an amendment is slow and unnecessary | Ingress families are microsecond root-solves; compute them in-kernel. Global materialisation is a later optimisation. |

---

## 7. Target design

### 7.1 "Daily snapshot, or an exact service?" — the best of both
The L0 rows are not used as snapshots in the fast path; they are **knots** (noon UT, tropical, 6 dp)
for a cubic interpolant measured at **0.314″ worst case** against Swiss `[R, W2G V3]`, and E1 shows
the solver landing within ~0.7″ of target `[X]`. For the Moon that is about a second of time. A fast
body's contact between two daily rows is not lost — it is a *root* of a smooth function, bracketed by
the arc index and converged. Nothing is scanned, so nothing falls between samples.

| Tier | Holds | Cost | Role |
|---|---|---|---|
| T1 knots — `ephemeris_daily` | 9 bodies × daily, lon + speed | global, once | exact at knots, convention-free |
| T2 interpolant + arc index — in-process | position/velocity/any-degree crossing at any instant | µs, **no Swiss lock, parallel** | this *is* the exact service |
| T3 ingress/station families — in-kernel (optionally global later) | sign, nakshatra, pada, kakshya, stations; real eclipses from `bg_sky_calendar` | seconds per build | feeds Tara, Moorti, Kota, Sade-Sati, Vedha |
| T4 live Swiss | lagna, sunrise, hora, eclipse visibility; optional polish; audits | locked, rare | the only genuinely live need |

A live service for everything would be slower *and* serial. Snapshots alone are lossy (F7).

### 7.2 Contact kernel — a new pure module
Working name `services/samparka_kernel/` (name is the native's to choose). **Imports** the validated
pieces rather than copying them (the repo has a duplicate-copy audit rail): `w2g` spline/arc/crossing
functions; Kshetra S0's sidereal offset, episode, dwell and kernel functions. The one new element is
the **frame term**: arcs are decomposed on the *sidereal* series (tropical knot − ayanāṃśa(knot)),
per ayanāṃśa — so F3 cannot recur and the five supported ayanāṃśas come from one substrate.
It does **not** edit `transit_search.py`, `gochara_grammar`, `gochara_intensity`, `ka_graha_sancara`
or `w2g` — so no accepted digest closure moves and the frozen L0 `bg_sky_calendar` is untouched.
Reads `bg_gochara_arcs` when present and fingerprint-valid, else builds arcs in memory from T1 —
identical function, identical result, no hard dependency on an L0 global build.
Emits **episodes**: t_in, t_exact *or* t_closest (`exact_crossing=false` for tangency), t_out, core
crossings, branch, dwell, truncation flags, tolerance. Anti-point phantoms cannot occur.

### 7.3 Contact ledger — per chart, class-independent
Strategy §3's Contact object: body · target identity (L1 `fact_id`, or sign / nakshatra / bhava /
kakshya cell, plus optional L2 binding ids — reserved from day one for R8) · relation · qualified orb
+ source + citation flag · branch · times + bracket + tolerance · dwell · convention vector · kernel
version · deterministic `contact_id`. Slow and medium bodies persisted; Moon recomputed with the same
ids. Owned by `ka_gochara` as its stage-0 family.

### 7.4 Typed testimony, never pre-multiplied
Background period (daśā stack per system, with applicability) · enabling interval (slow-body sign
occupation from natal Moon/lagna, Sade-Sati phase, AV state) · specific contact (ledger) · inhibition
(vedha, per school, signed, de-duplicated against Vighnakara per L3-U03) · modifiers (Tara, Moorti,
Kota, annual stack, real eclipses, nodal dṛṣṭi). Each carries method, source, citation state,
applicability and **evaluated / not-evaluated / inapplicable**.

### 7.5 Projections
(1) **Event-class windows** — λ as a *named, versioned* projection, closed-form between breakpoints;
era ⊃ month ⊃ day with parent ids; chain milestones; `peak_basis` extended so a tara-selected day
says so. (2) **Mechanism windows** — same machinery keyed by L2 structure. (3) **Now / ahead /
election** — direct ledger reads, Moon-scale drill-down on demand.

### 7.6 Coverage contract (L3-Q08)
Every partition and projection states horizon requested/completed, bodies and relations searched,
tolerance, conventions, targets resolved vs unresolved, tiers persisted vs on-demand, mechanisms
evaluated vs not. *None in scope* · *outside scope* · *search incomplete* become distinguishable.

### 7.7 Storage and cutover
One table, one new generation (working label `'4.0'`) in `kala_gochara_windows`, written **beside**
v1 and 3.0 — which makes the seed's existing `target_table` claim true by construction. No second
staging copy; calibration scripts select by generation. Go-live and rollback per chart via
`kala_gochara_authority`. `kala_gochara_windows_v2` is left untouched as history.

### 7.8 Cost — now partly measured
Closed-form evaluation: **0.013 ms per instant** `[X]` versus 88.5 ms. Kernel root-solve ≈111 µs per
contact `[R]`: non-Moon ≈1.9×10⁵ contacts ≈ 20 s; arcs ≈48 s once `[R]`. Expectation **single-digit
minutes cold, seconds warm** `[U]` — to be replaced by measurement under strategy §5's benchmark
contract before any claim is made.

---

## 8. Recommendations on the rulings

Ordered by the native's priorities: quality, then build efficiency, with ecosystem risk noted.

**R1 — Disposition. Recommend: ACCEPT** one successor under `ka_gochara`; century superseded after
migration; sweep stays retired. It matches the native's own W6.4 ruling that `ka_gochara` is the
windows authority, and the registry already says so. *Safeguard:* retire nothing until the successor
is `DATA_ACCEPTED` on both canonical charts and has held authority through a soak period. Needs a
DP-SD amendment (22-member denominator changes).

**R2 — Kernel home. Recommend: a NEW pure library module, no asset id** — *not* inside
`ka_graha_sancara` as v0.1 proposed. Zero digest invalidation today; each consumer adopts it inside
its own elevation packet, when its digest is moving anyway.

**R3 — Sub-day rail. Recommend: RETIRE it for computation, KEEP it for claims.** Add a
`precision_class` to served timestamps; `is_timing_window` stays earned.

**R4 — Method repairs (Stage M). Recommend all, in this order, each separately versioned, ablated on
real data, and ruled:**
 1. **Contact-interval activity** — a body contributes while it is *within orb*, scaled by actual
    separation, replacing "an exact crossing happened within ±5 d". Highest value: it is what makes
    the contact term carry information at all (F14), and it is what the code's own docstring already
    describes.
 2. **Take the Moon and the fixture kakshya out of the activity noisy-OR.** The Moon speaks through
    Tara, Moorti and day-tier refinement — its classical roles. Kakshya contributes only from real L1
    BPHS Ch.66 boundaries, never the fixture approximation (the IR-6 precedent, applied consistently).
 3. **Dwell weighting** — stationary and slow passages count for more (already coded in Kshetra S0).
 4. **Honest eras and no peak cap** — era windows from real support; every admitted peak stored;
    budgets applied at serve time (§N.6), which is also Q8's truncation policy.
 5. **Real eclipses** (`w26`) replace the `eclipse_degree` proxy (F16).
 *I am not proposing doctrine.* I note only what the code's own flags say: `degree_contact` is
 `uncited_extension=True` while `bg_transit_rules` (cited) are house-from-Moon sign rules. Which layer
 is primary is a method ruling for the native, at acharya standard.

**R5 — Mechanism wiring. Recommend a two-step admission for each, in this order:** AV gating (`w21`)
→ Sade-Sati (`w24`) → Vedha century-complete → Moorti (`w22`, after exact ingress) → real eclipses
(`w26`) → Kota (`w25`) → annual stack (`w27`, last — it needs Q3's independence ruling). Step one:
appear as *typed testimony*, visible, **no effect on any score**. Step two: enter a projection only
after ablation on a real corpus. This is the guard against repeating UTK-R3, where ten mechanisms
were "admitted" on an ablation against an empty corpus `[R]`.

**R6 — History. Recommend: leave v1 rows in place; write the new generation beside them; cut over by
authority row; AND reinstate a guard keyed on (table, generation) for `'v1'` only**, exactly as
migration 588 advises, plus a restore drill of the dump into a disposable database. *This partially
reverses the 2026-08-23 instruction — in the form that instruction's own migration recommends, and
without blocking any writer, which was the original complaint.*

**R7 — Moon. Recommend:** never persisted full-span; ingress families computed per build; degree
contacts on demand and inside served day-tier windows. Persist Tier B — the rows are slim.

**R8 — L2 binding. Recommend: YES, as phase 2.** Reserve the identity columns now; union Yojaka's
accepted predicate targets into the ledger once Yojaka is elevated (it carries 79 unmatched MSR
references `[R]`). Do not block the successor on it; do not ship the ledger without room for it.

**R9 — Existing generation-2.0 rows. Recommend:** register F3 in the defect register; exclude the
W2G writer from dispatch; label, do not delete. They are not served, so there is no urgency beyond
preventing another build.

**R10 (new) — Registry repair (F10)** through the governed seed/migration route, at cutover.

---

## 9. The ecosystem, explicitly

**Upstream readiness.**

| Upstream | State | Gap → owner |
|---|---|---|
| L0 `ephemeris_daily` | Ready; 0.314″ `[R]` | none |
| L0 `bg_gochara_arcs` | Ready as index; optional | kernel falls back to T1 |
| L0 `bg_sky_calendar` | Ready for real eclipses, stations, Jup–Sat | none needed now |
| L0 `brahma_event_ontology` | Partly — provisional signatures | sourcing pass → **L0 authority; never invented in L3** |
| L0 rules, AV gates, moorti table, vedha scale | usable, cited | executable-coverage map → L0 |
| L1 natal, `chart_dashas`, AV, Sade-Sati, yoga firings, **kakshya boundaries** | Ready | pin generation vector (D4) |
| L2 Bodha mechanisms | Ready, unused here | R8 |
| L3 Vedha, Moorti | not century-ready | re-expressed on the kernel (WP7) |
| L3 Kota, Tithi-praveśa, Sudarśana | built; consumers coded, unwired | R5 |

**Downstream — who reads, and what changes for them.**

| Consumer | Change |
|---|---|
| 3 `gochara_*` MCP tools | none to schema; add the new generation's citation branch (`buildSourceCitation` has explicit per-generation branches — an unknown generation currently returns v1 provenance, MR-03 `[S]`); extend `peak_basis` handling |
| `reading_checklist`, `judgment_query` timing anchor, Paripraśna `engine_tier` | none — all authority-filtered `[S]` |
| L5 prospective ledger | none; gains stable contact ids |
| Kshetra stage 4 cross-check | none; legacy rows remain a *validation* edge |
| `ka_sangam` → 7 dependents | later packet: read the ledger instead of a private scan; savings fund full predicate coverage (strategy P4) |
| Kshetra S0 | later packet: adopt the kernel; one computation, two consumers |
| Vedha / Moorti / Kota | WP7: century-complete, exact ingress |
| `w44`/`w45` calibration scripts | select by generation instead of the staging table |

**Campaign machinery this plan must pass through `[S]`.** Campaign `t3-2026-09-11-8b884eac`, Accepted
0/22. Three streams: the successor spans Stream B (`gochara`) and Stream C (century, `w2g`,
`gochara_v3`) and touches Stream A (`resonance`) — **one named owner is required; I recommend
Stream C.** `asset_analysis_accepted` and `optimization_verdict_accepted` are never gated, so the
contract work can start now. Builds are requested from the single lane, never self-dispatched. Each
L3 source PR shifts `layers.L3.writer_inventory_sha256`; one integrator re-pins. Generated artifacts
are regenerated, never hand-edited. Migration range 1070–1119. `transit_search.py` and
`ka_dasha_kala` are never edited in-stream — this plan needs neither. Known external blocker: the
`data_plane_builder` grant on `asset_registry` (STATE.md N1-C; migration 1070 was deployed for it
today `[R]`).

---

## 10. Implementation plan

**Authority class:** **A** = already authorized by execution-brief §3 (local source, tests, fixtures,
disposable DB). **N** = needs a native ruling first. **P** = needs production build authority and a
release of the century hold.

| WP | Work | Class | Depends | Exit gate |
|---|---|---|---|---|
| **0** | Close the three open unknowns: read production target counts per class; confirm migration 588 state; explain the ≥2-era case. Register F3, F13, F15, F16, F17 in the defect register. | A (read-only) | DB access | findings confirmed/corrected in writing |
| **1** | **Kernel.** New module importing `w2g` + Kshetra S0 functions; sidereal-frame arcs; episodes incl. tangency; in-kernel ingress families. | A | — | vs Swiss on a pre-registered grid: stations, retrograde triple passes, tangencies, wrap, Moon perigee, all 5 ayanāṃśas, nodes; DB reads constant in target count; **E1 re-run shows 0 d error** |
| **2** | **Stage E1 — closed-form scorer on the *legacy* event source.** Same primitives produce the events; only the evaluation changes. Isolates scoring risk from geometry risk. | A | — | bit-parity with the real engine on 7 primitives over pre-registered spans; F16 divergence classified, not smoothed |
| **3** | **Stage E2 — swap the event source to the kernel.** | A | 1, 2 | event-set equality within tolerance; every divergence classified: phantom / tangency / grid artefact / bug. None unclassified. **Benchmark per strategy §5** — the first real build-time number |
| **4** | **Ledger + coverage contract + typed testimony** (no score effect yet). D1 field dossier. | A (design) / N (schema) | 3 | L3-Q08 three-way negative proven; evaluated/not-evaluated states present; D1–D3 dossier reviewed |
| **5** | **Stage M** — R4 items 1→5, one PR each, each with golden values (§N.7) and an explained-delta report against Stage E. | **N** per item | 4 | native ruling per method; ablation on real data; activity demonstrably discriminates (E3 re-run: slow-body signal visible in the *full* term) |
| **6** | **Mechanism admission** — R5 order, two-step. | **N** per mechanism | 4, 5 | step 1: testimony visible, scores byte-identical; step 2: ablation delta on a non-empty corpus |
| **7** | **Overlays on the kernel** — Vedha, Moorti, Kota: century-complete, exact ingress. Each in its own asset packet. | A design / N Moorti method | 1 | coverage = build horizon; Moorti compared at true ingress instant vs day-grade, error rate reported |
| **8** | **Serving** — new-generation citation branch, `peak_basis` vocabulary, `precision_class`; registry repair (R10). | A | 5 | §N.6 density tests; sentinel field survives retrieval, budget and replay (D8) |
| **9** | **Cutover** — guard (R6) + restore drill → build generation `'4.0'` beside → shadow compare → flip authority on one chart → soak → second chart → supersede century. | **P** | 5–8, fresh native authorization | rollback proven by flipping back; serving tools unchanged; D9 verified by ready revision + env SHA |
| **10** | **Consumers** — Sangam and Kshetra S0 onto the ledger; R8 L2 binding via Yojaka. Separate packets, their own owners. | N | 9, Yojaka elevated | per-consumer equivalence first, then caps removed |

**Critical path:** 1 → 3 → 4 → 5 → 9. **WP1 and WP2 are independent and can start together.**
**First slice (all class A, touches nothing live):** WP1 + WP2 + WP3 for one class on one chart in a
disposable database. It ends with the first measured build time and a classified divergence list —
and it is the point at which the plan is either proven or stopped cheaply.

**Mapping to the campaign's ten dimensions.** D1/D2/D3 → WP4. D4 → generation-vector pinning in WP4.
D5 → Swiss as the *independent* geometry oracle (WP1) and a small hand-specified step-function
reference for scoring (WP2) — not old-output parity, because the old output is artefactual in places
(F13–F16). D6 → WP3 benchmark; no reduced cap, horizon or resolution is ever counted as a speedup.
D7 → R6 + WP9. D8 → WP8. D9 → WP9. D10 → value test: does a question like product §12.2 get a
better-discriminated answer than from today's windows?

---

## 11. How this could fail

| Failure | Guard |
|---|---|
| Stage E "proves" parity with an artefactual oracle | Parity is a harness only. Acceptance is against Swiss and a hand-specified reference (D5). |
| Stage M smuggles in doctrine | One method per PR, each natively ruled; I propose none beyond what the code's own citation flags show. |
| Mechanisms admitted on a vacuous ablation again | Two-step admission; step 2 requires a non-empty corpus (R5). |
| A mis-scoped DELETE destroys v1 | R6 guard + restore drill **before** WP9 writes anything. |
| Kernel silently misses a root | Arc decomposition gives the coverage proof; WP1 tests the hard cases explicitly; residual risk named in §13. |
| Cross-stream collision | One named owner; hubs untouched; new module. |
| Digest / layer-pin churn blocks merges | Kernel lands as an unimported module first; one integrator re-pins. |
| Build dispatch blocked by infrastructure | Known (`asset_registry` grant). WP0–WP8 do not need a production build. |
| Saturation and cost findings don't hold at production target counts | WP0 measures T first. Both get *worse* with more targets, so the direction is safe; the magnitude is not. |
| The plan becomes a fourth parallel engine | Explicit strangler sequence: successor → Sangam → Kshetra S0 → Taranga; `transit_search.py` retires only when its last importer leaves. |

## 12. What I would like the reviewer to attack

1. **F2/PoC.** Is there any λ_v3 term that is *not* piecewise-constant? Is 7/8 the right reading?
2. **F3.** Find the ayanāṃśa conversion I missed, or confirm there is none.
3. **Coverage proof.** Do station/wrap cuts on the *sidereal* series bracket every root — including
   the true node's short prograde excursions, and targets within minutes of a station?
4. **F14/F15.** Are they fixture artefacts? What would production target counts and weights do?
5. **R4 ordering.** Is contact-interval activity really the highest-value repair? Is removing the
   Moon from activity defensible, or does it discard a legitimate classical signal?
6. **R6.** Is a generation-keyed guard the right reading of the native's 2026-08-23 instruction?
7. **Interpolant adequacy.** 0.314″ is longitude only. Does any consumer need latitude or distance?
8. **Ecosystem.** Which consumer of `kala_gochara_windows` did I miss? Is Stream C the right owner?
9. **Sequencing.** Would you start somewhere other than WP1+WP2+WP3?
10. Anything stated more confidently than its evidence.

## 13. Not established

Every executed result used a **2-target fixture context with no database**. Production target counts,
weights and row contents were not read. The cost model beyond per-evaluation and per-instant unit
costs is derived. The Moorti error rate and ledger storage size are unmeasured. I did not read the
ten mechanism bodies, Sangam's scoring, or Kshetra stages 1–8 in full. The ≥2-era-window case
(career_setback, MR-44/45) is unexplained. Whether the native's ~25 h refers to the century writer or
the sweep remains, per the repository's own ledger, unresolved — though F1's arithmetic makes the
century writer a sufficient explanation.
