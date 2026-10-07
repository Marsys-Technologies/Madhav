---
artifact: KALA_LAYER_CODE_ARCHITECTURE_PLAN
canonical_id: KALA_LAYER_CODE_ARCHITECTURE_PLAN
version: "1.0"
status: DRAFT — for the native's reading, then Astra's independent review, then the native's seal. Nothing here authorises a build, a migration, a data clear, a registry edit, a deploy, or a change to any campaign's state or holds.
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1) session; second pass over KALA_LAYER_VALUE_REVIEW_v1_0.md at the native''s request (code architecture, not data state)'
grounded_at: 'origin/main @ 09fd39b4d · worktree cooperative-racer @ c751f3bd8 (module inventory, line counts, consumer trace) · l3/sangam-final @ fbbbb9414 (pipeline concept v1.1) · suvarna/hq @ 79ab6b509 and bd944059b (campaign plan v1.5, focus families v1.4, decisions) · Pravāha GOCHARA_DESIGN_SPECS v1.4 FROZEN @ eea2610d0 · A5_3_REGISTERED_WRITER_BRIEF v1.33 · LEVEL_MAP.json frozen 2026-10-03 · ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0 §2'
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa only (Pravāha D-SCOPE; Suvarṇa N-12)"
evidence_labels: "[S] source read at the named ref · [D] doctrine, document named · [A] taken from a sub-agent digest, not re-read by the author · [I] inference or design judgement · [U] unverified"
companion: 'KALA_LAYER_VALUE_REVIEW_v1_0.md (same folder) — the evidence base; KALA_ASSET_ALGORITHM_ELEVATIONS_v1_0.md (same folder) — the per-asset domain-logic elevations this plan''s packets implement; neither is repeated here'
supersedes_in_scope: >
  Nothing sealed. It consolidates, for code only, the asset-level plans the three family exercises produced and the
  pipeline concept note v1.1, and extends them to the whole layer. Where it proposes a change to something owned by
  Pravāha (the judge), Strategic Suvarṇa (campaign rules) or a sealed ruling, §12 says so and routes it.
reviewer_of_record: "Astra (Codex gpt-6), by the native's standing choice for Kāla (2026-10-06: Fable 5.1 + Astra only)"
changelog:
  - "1.0 (2026-10-06): first version. Plain-terms value today vs after per asset (§0.1), design principles (§1), the one-engine architecture (§2), the duplication register and shared core library (§3), stage and projection contracts (§4), the serving plane (§5), build and rebuild efficiency (§6), certification by construction against the nine gates as measured by the engine (§7), asset-by-asset code dispositions (§8) with the three family plans folded item by item (§8.1), work packets and dependencies (§9), tests and oracles (§10), risks (§11), decisions routed to other owners (§12), questions for the reviewer (§13). Same-day revision after the native's reading: value restated as the goal and certification as its receipt; §0.1 and §8.1 added."
---

# Kāla — code architecture and build plan

**Written for:** the native, then Astra as the independent reviewer, then the sessions that will implement each work packet and the Suvarṇa engine that will certify the result.

## §0 · One page

**Brief.** Design the Kāla layer's *code* so that, for any chart, the data it generates delivers the most temporal value: every asset doing one thing well, the assets reinforcing one another instead of recomputing one another, and the whole rebuilding cheaply whenever L0–L2 regenerate. That is the goal. Suvarṇa certification is the receipt the layer earns along the way, not the purpose; the plan is written so certification follows from the design rather than being pursued separately (§7). Data state today is out of scope: everything upstream is being rebuilt, so everything downstream will be rebuilt.

**In plain terms, what changes for the person asking (§0.1 has the asset-by-asset version).** Today the layer can tell you which planetary period you are in, where the sky stands relative to your Moon and Lagna, which hours to avoid today, your annual context, and good days for a rite. It cannot tell you when a particular promise in your chart becomes active, whether a rough patch is coming, which of two windows is better supported, why the methods disagree, or what it predicted and what happened. After the elevation, every one of those questions is answered from one engine: a dated, cited window with the clock and the contact that produced it, what helps and what obstructs it, how much independent agreement it has against chance, how far the search looked, and a written forecast that is later scored against your life.

**The one decision.** Replace three engines that each recompute the sky, the promises and the clocks (Gochara's five generations of code at about 36,000 lines, Kṣetra at 14,000, Saṅgam at 3,000, plus 10,000 lines of writers; measured in §3.1: eight ephemeris/transit-scan implementations, two aspect tables that disagree on the nodes, six daśā readers, five promise formulas, four tārā tables, six sign-lord tables, no shared event-ontology loader, three private resume ledgers) with **one temporal engine**: a shared core library of pure primitives, three evaluated stages in a fixed order (judge → jury → forecaster) plus one typed negative-space producer, one atomic publication manifest, and every other output a *projection* over those stages. No asset id is created or deleted; eleven existing writers become cheap projection writers; four become stage writers; the rest stay as adapters or services.

**Why this is worth it, in three measures.**
- *Value.* Every window the native sees will carry the same six things: the clock, the contact, the structure engaged, the enabling and inhibiting conditions, the coverage of the search, and the typed null where something could not be derived. Agreement between methods becomes a measured quantity with a null, not a count. Negative space has six honest states. Forecast probability appears only under a declared event model. None of this is possible while three engines store three shapes.
- *Structure.* One object model (assertion · issued_forecast · outcome) and one evidence algebra (roles, roots, derivation parents) make duplicate counting impossible by type, not by review. Every projection is a SQL view over stage tables, so it is idempotent, lineage-complete and seconds to rebuild.
- *Build.* Geometry, interpretation and evaluation are three lineages across the whole layer, not just inside Gochara. An L2 rebuild re-runs F1, the jury, the forecaster and the projections; it never re-solves a contact. A convention change re-solves geometry once, for every stage. Dense materialisation (8.57 million field rows) is replaced by a compact evaluator whose segment count is bounded by the knots of the terms actually in the model. Chart preparation happens once per generation and is content-hashed; every substep binds to that hash.

**What this plan leaves untouched.** The judge (Gochara 5.0) is Pravāha's and its spec is FROZEN; this plan *consumes* it and proposes exactly three amendments through the steward (§12). Kṣetra's ten rulings and B8-6 stand. N-32 stands. D-SCOPE stands. The FROZEN orchestrator contract is not extended; every stage is a `WriterBase` writer on `ctx.db_conn`.

**Every asset's algorithm is elevated, not only its plumbing.** The companion KALA_ASSET_ALGORITHM_ELEVATIONS_v1_0.md gives each of the twenty-two assets a card at the Gochara depth: the algorithm as the code computes it today (constants quoted), its astrological and computational defects, the elevated algorithm as typed inputs → computation → outputs → nulls, the classical basis with each citation checked against the ingested corpus this session, what it gives to and takes from the other assets, and the oracle that would fail if it were wrong. Fourteen algorithm-level findings came out of that pass (its §4), among them that the field's clock term has been identically zero in every stored build and that the muhūrta cancellation doctrine the election view says is missing is in the corpus and was never extracted. The packets in §9 implement those cards; §5 of the companion maps card to packet.

**The three family plans are folded in, item by item.** §8.1 maps every ruled or decided item of the Gochara-family plan (v2.2 and the 2026-09-24 rulings), the Kṣetra ecosystem plan (v1.17, rulings 1–10, PCD-1/2, B8-*) and the Saṅgam packet (R-1…R-6, E1…E6, the concept note v1.1) to the module and work packet that now carries it, or says which later ruling superseded it. Nothing ratified is dropped silently.

**What must be ruled before code starts.** Three things (§12): that the core library may import the judge's pure modules (an amendment to the Pravāha brief, not to the spec); that a shared-domain registry row for the sky substrate is in scope (Suvarṇa N-12 excludes "new assets", and the cleanest design needs one, with a fallback that needs none); and that the views move from the MCP facade package into the retrieval registry (a Paripraśna-side change).

---

### §0.1 · In plain terms: what each asset gives the person today, and after

"Today" is what a direct tool caller can get for the native's chart on 2026-10-06 (review §4). "After" is what the same asset delivers once the plan is built and the data regenerated. No probability or accuracy is implied anywhere in the "after" column; those are earned later, from scored forecasts.

| Asset (plain name) | Today | After |
|---|---|---|
| `ka_graha_sancara` (sky positions) | Answers "where is each planet at a moment" for a few tools; no Kāla writer uses it | The single sky source every stage reads, so no two parts of the layer can disagree about the sky |
| `ka_dasha_kala` (the clock) | Tells which planetary periods run at a date across seven systems, with an unproven "agreement" score | The one clock of the layer: each system's applicability stated, exact period boundaries with honest error bars from birth-time uncertainty, period-change bands |
| `ka_avadhi` (period dossiers) | A snapshot from August of how each period's lord stands; reachable only inside one bundle tool | "How will my Ketu period be": the lord's condition at the period's start, the promises that attach to it, the boundaries with error bars, all from the same clock everything else uses |
| `ka_yojaka` (the promise bridge) | Fifty thousand rows linking chart structures to activation rules; almost all point at structures that no longer exist; nothing reaches you | The promise graph: every structure in your chart with its supporting and opposing mechanisms, exceptions and cancellations, built from the chart's facts and cited rules; the one list of "what could happen" every timing stage reads |
| `ka_gochara_v5` (transits, the judge) | The served transit layer gives decade-wide context rows; none is a timing claim for the coming year; it did no better than chance on your logged events | Dated, cited windows per life-event class: the exact transit contact, the period that permits it, obstructions as intervals, how far the search looked, and an uncertainty on every instant |
| vedha · mūrti · kota · tithi-praveśa · sudarśana (classical overlays) | Shown for about fifteen months ahead; two use contested methods, one has no primary citation; nothing downstream uses them | Inputs to the judge's rules where their method is qualified; clearly labelled "contested" where not; horizon disclosed; century coverage through the judge |
| `ka_vighnakara` (what obstructs) | Empty; its design scored obstructions as one number | Six honest states: outside the risk set · method not applicable · information unavailable · evaluated and silent · obstruction active (what, by what, until when) · measured lower rate. "Nothing stands in the way" is said only when something was checked |
| `ka_sangam` (agreement, the jury) | Empty; its design counted "currents" measured against the wrong reference point | Measured agreement between independent timing methods on the same stretch of time, with a chance baseline; disagreements shown as contests rather than averaged away; turning points where several life domains converge |
| `ka_kshetra` (the intensity field, the forecaster) | Eight and a half million rows from a build that never finished, on a shifted time axis; nothing serves them | A compact intensity curve per life-event class with a chance test, sourced base rates, and "what deserves attention"; odds only when an event model and calibration justify them |
| `ka_kalasutra` (activation intervals) | Empty | When a given structure's window opens, closes and recurs, as a view over the judge and jury |
| `ka_kala_darshana` (what is active now) | Empty | The published "now" view with its net reading, from one manifest, so every tool shows the same state |
| `ka_jivana_parva` (life chapters) | Chapters whose "convergence counts" come from a table that has been empty for a month | Chapters from the clock, each summarising the real assertions inside it; "how does this chapter differ from the last" |
| `ka_bhavishya_lekha` (forecasts) | Empty; its design assigned "probability tiers" with no event model behind them | Issued forecasts: written once, dated, with an information cutoff, never edited; scored later against what actually happened. This is the mission's testable prediction |
| `ka_taranga` (the shape of a year) | Ninety-two thousand rows no tool can reach | Monthly intensity per life domain as a view: the shape of the year ahead |
| `ka_tulana` (priority) | Registered as the ranker; the priority tool never calls it | Ranks windows across life domains by agreement, coverage and salience, and drives the priority view |
| `ka_muhurta_seva` and the election view | Election candidates with a factor census; works today on the general calendar | Election over qualified methods, grounded in your own windows and clocks: "when should I act" within what the judge and jury found |
| `ka_gochara_resonance` (transit targets) | Per-class target lists with known citation defects | Folded into the promise graph and the judge's relationship records |
| century materializer · sweep · 4.1 candidate | Held, retired, or engineering proof | Historical capital, kept; nothing rebuilt |

---

## §1 · Design principles (binding on every packet)

1. **Compute each temporal primitive once; store the smallest evaluable representation; serve by manifest.** A primitive is: a sky boundary event, a contact, a period boundary, a promise-graph edge, a rule evaluation, a segment support vector, a field coefficient. If two stages need it, it lives in the core library and in one table.
2. **Three lineages, layer-wide** (Gochara spec §0, generalised): geometry (contacts, boundaries) · interpretation (records, rule paths, promise graph) · evaluation (windows, agreement, field, forecasts). A change re-runs only the lineage it alters and everything downstream of it. The dependency decides, never the label on the change.
3. **One object model.** Every stage writes `assertion` rows of one shape (concept note §2); forecasts are `issued_forecast`; outcomes are `outcome`. Projections never invent a fourth shape.
4. **The evidence algebra is a type, not a convention.** `role ∈ {selects, conditions, qualifies, corroborates, explains}`, `roots`, `derivation_parents`, `used_for_selection`, `operator_role ∈ {scored, testimony}`. A reused root yields no increment; testimony weights nothing; both are enforced by the library and by mutation tests, not by reviewers.
5. **Typed nulls, no defaults.** One `null_reason` vocabulary for the layer (`outside_risk_set · method_inapplicable · information_unavailable · evaluated_silent · obstruction_active · measured_lower_rate · source_table_empty · not_computed`). A literal default in a stage module fails lint.
6. **Generation-scoped everything.** Every row carries `generation`; nothing is shared across generations; an absent manifest row means `unpublished`; delete-then-insert is scoped `(chart_id × generation × grain)` and lives inside the substep that owns the grain (§N.3; Gochara pin 5).
7. **Projections are SQL over stage tables.** A projection writer's `run(ctx)` is a deterministic query plus delete-then-insert; it carries no formula, no threshold, no default. If it needs one, it is a stage, not a projection.
8. **Verification is a stage's own substep, written to its own verification table, by an independent code path** (the judge's `inventory_verifier`/`window_verifier` pattern). A stage without a verifier has no `PASS`.
9. **Frozen contracts are consumed, not extended.** `WriterBase` (`run` / `plan_substeps` + `run_substep`, `ctx.db_conn` never committed), the Gochara spec v1.4, the Kṣetra rulings, N-32. If a packet needs more, it stops and routes (§12).
10. **Certification by construction.** Every gate in §7 maps to a library mechanism and a CI lint, so an asset passes because of how it is built, not because a reviewer looked.

---

## §2 · The architecture

### 2.1 Shape

```
                    ┌──────────────────────── kala_core (library; no writer; pure + readers) ────────────────────────┐
                    │ sky · clocks(F2) · promise(F1) · rules · calendar · overlays · assertion · measure · manifest · verify │
                    └───────────────────────────────────────────────────────────────────────────────────────────────┘
          shared domain                 chart domain, in level order (one build slot; waves per LEVEL_MAP)
  ┌──────────────────────┐   ┌───────────┐  ┌──────────┐  ┌───────────────┐  ┌────────┐  ┌───────────────┐  ┌──────────────┐
  │ sky_event_substrate  │──▶│ F2 clocks │─▶│ F1 graph │─▶│ JUDGE         │─▶│ NEG.   │─▶│ JURY          │─▶│ FORECASTER   │
  │ (per convention;     │   │ ka_dasha_ │  │ ka_yojaka│  │ ka_gochara_v5 │  │ SPACE  │  │ ka_sangam     │  │ ka_kshetra   │
  │ Moon on demand)      │   │ kala +    │  │          │  │ (Pravāha)     │  │ ka_vigh│  │               │  │ (compact)    │
  └──────────────────────┘   │ ka_avadhi │  └──────────┘  └───────────────┘  │ nakara │  └───────────────┘  └──────────────┘
                             └───────────┘                                   └────────┘            │                 │
                                                                                                   ▼                 ▼
                                   PUBLICATION MANIFEST (atomic, per generation; compare-and-swap; serving guard)
                                                                                                   │
            PROJECTIONS (SQL writers): kala_activation (ka_kalasutra) · kala_darshana (ka_kala_darshana) · kala_jivana_parva ·
                                       kala_taranga (monthly ∫λ) · issued_forecast registrar (ka_bhavishya_lekha)
                                                                                                   │
            VIEWS (retrieval-registry composites; MCP facades become aliases): NOW · AHEAD · EXPLAIN · PRIORITY (ka_tulana) ·
                                       ELECT/RITUAL (ka_muhurta_seva) · STORY · UPĀYA · gochara_*
            ADAPTERS (method inputs to the judge/F1; keep their tables): vedha · moorti · kota · tithi-praveśa · sudarśana
            SERVICES: ka_graha_sancara (sky facade) · ka_muhurta_seva · ka_tulana
```

### 2.2 What each box owns and must not do

| Box | Owns | Must not do |
|---|---|---|
| **sky_event_substrate** | boundary events per body per convention (sign, nakṣatra, kakṣyā, station, eclipse instant); solver method and uncertainty; Moon on demand with a coverage record | know any chart; store Moon rows; store roles or labels |
| **F2 clocks** | `period_context(chart, t, system) → {MD, AD, PD, applicability, σ, scenario}`; `boundaries(chart, system)`; the correct covariance (`dB = (1−kv)dT + k dA`); sandhi bands; applicability per system stored once | restate L1 values (reads `chart_dashas` by pinned build and ayanāṃśa); compute a prior; use a static fallback |
| **F1 promise graph** | signed mechanism graph from L1 facts + versioned L0 rules; preconditions, exceptions, cancellations; frame; event-class mapping as a separate reviewable inference; L2 MSR/CGM *attachments* | treat an L2 reading as the universe of promise; carry W2's default conductance / noisy-OR as "promise strength" |
| **Judge** (frozen) | contacts, relationship records, rule paths and admissibility, three-field valence, permission per instant, vedha intervals, annual objects, publication of its generation | cross-school dependency accounting; attaching windows to reading claims; odds; attention; the life map |
| **Negative space** | six typed states from the judge's own obstruction/cancellation/exception records plus F2 applicability; release conditions; what-by-what-until-when | score, suppress, or net anything; invent a universal bādhaka or māraka multiplier |
| **Jury** | declared witness groups and their shared dependencies; evidence algebra; elementary segments and support vectors; `D(W)` with its conditional null; turning points; contests; canonical-forecast attachment of reading claims | compute sky; run a prior; admit or exclude; give a reused root an increment; emit a confidence label; call a group independent |
| **Forecaster** | compact piecewise log-linear field with `∫λ`, risk masks, uncertainty scenarios; alignment null; sourced base rates with provenance; odds only under a declared event model; salience axes; snapshot | compute promises or clocks; read L4 directly; materialise dense rows; call an alignment tail an odds |
| **Manifest** | one row per publication pinning natal facts, conventions, F1, F2, judge, jury, forecaster, rule registry, calibration artefacts, evidence cutoff; compare-and-swap authority switch (the N-29 "authority switch or disclosure" rule, generalising `kala_gochara_authority`); completeness attestation; reachability retention | let three stage heads serve a mixture never evaluated together; hold a rebuild because output exists (Idem) |
| **Projections** | joins and aggregations over stage tables, keyed by assertion ids | a formula, a threshold, a default, a read of a non-stage table |
| **Views** | one implementation per view in the retrieval registry; density contract; drill pointers; honest-empty | a computation; a second copy in the MCP package |
| **Adapters** | their method's output as rows with provenance and `method_qualification`; consumed by the judge's rule paths or F1 | be read by a view directly while `method_contested` |

---

## §3 · The shared core library — `kala_core`

### 3.1 The duplication register (why a library, measured) [A, code trace at c751f3bd8]

| Primitive | Independent implementations today | Where they disagree or waste |
|---|---|---|
| Ephemeris lookup and transit scan | **8 paths**: `pipeline/transit_search.py` daily/half-day step loops (958 lines; used by grammar, v3, `ka_gochara` service, Saṅgam, Taranga, trigger) · `gochara_v3/interval_solver` 7-day grid + bisection + 1-day refine · `gochara_kernel/legacy_semantics` re-implementing the same · `gochara_kernel` knots/arcs/contacts/episodes (noon-UT sidereal knots, spline arcs, Swiss-refined roots; also used by moorti) · `w2g` global arcs over `bg_gochara_arcs` (the kernel's `arcs.py` says it was adopted from `w2g/arcs.py`) · `ka_kshetra/stage0` own Hermite spline + Brent roots per chart over 100 years · the three overlays' own `ephemeris_daily` day-grid reads, each with its own ayanāṃśa-offset function · ad-hoc `swe.calc_ut` point lookups in `ka_vighnakara`, `ka_sangam`, `gochara_v3`, `stage3_clocks` | three spline/root solvers for one geometry; chart-independent events (ingress, station, syzygy) computed globally in two paths and per chart in two others; `ka_graha_sancara.get_ephemeris` has **no caller among the L3 writers** |
| Aspect / dṛṣṭi tables | `gochara_grammar/primitives.py:192` (Rāhu/Ketu cast 5/7/9) · `gochara_kernel/convention.py:45` (nodes cast none, N-14) · two deliberate verifier restatements · `gochara_rules/drishti.py` graduated strengths · symmetric `[0,60,90,120,180]` in `ka_yojaka/binder.py`, `ka_sangam/engine.py` (four sites), `kala_trigger`, `taranga_service` | **the two special-aspect tables disagree on the nodes**; v1/v3 scoring still uses the legacy node aspects |
| Daśā period lookup / active-at-t / boundaries | `KaDashaKalaService` tree walk (used only by Saṅgam and `ph_nimitta`) · `gochara_grammar/dasha_data` (used by intensity, v3, w2g, sweep, kernel) · `gochara_kernel/dasha_read` (pinned tier/build) · `ka_temporal/date_resolver.load_dasha_timeline` (no tier filter; kalasutra, vighnakara) · `ka_kshetra/stage3_clocks` seven direct queries · inline SQL in `ka_avadhi`, `ka_jivana_parva`, `ka_taranga`, `taranga_service`, `kala_permission`, resonance · hardcoded native schedules in `brahmagyan/kala/*` | column choice (`start_iso` vs `start_date`) and tier pinning differ per reader; `period_lord_relation` exists three times; birth-date derivation five times; sign-lord tables six times |
| Promise / L2 → event class | `ka_yojaka` 8 signature classes over MSR · resonance's 27-class target map over `bg_transit_rules` + ontology · Kṣetra `stage2_promise` k-shortest routes over CGM/Pratijñā with noisy-OR · `gochara_intensity.promise` noisy-OR (reproduced in `legacy_semantics`) · `taranga_kernel.promise` salience × valence × varga; class universes in five places | five promise formulas over three different L2 inputs; no single event-class roster |
| Vedha / obstruction | `ka_vedha_gochara/logic+gate` · `gochara_rules/vedha*` (+ independent oracle) · `gochara_grammar/sarvatobhadra` · `gochara_v3/context` + suppression constants (duplicated in `legacy_semantics`) · `gochara_kernel/window_sweep.vedha_attenuation` · `ka_sangam/engine._c11_vedha_factor` · unused `stage1.build_vedha_primitive`; obstruction detectors in `ka_vighnakara` (4), `kala_trigger` (2), grammar `kartari`, intensity suppression, Kṣetra S-term, `brahmagyan/kala/obstruction` | the same evidence can attenuate twice (TRIGGER and Vighnakara) |
| Aṣṭakavarga gating | grammar primitives · v3 context/engine/w21 · `gochara_rules/ashtakavarga` (P5) · `ka_sangam` C7 + Mode D · `taranga_service` SAV · Kṣetra records it only as a coverage gap | six readers of one L1 table |
| Pañcāṅga / tārā | `ka_muhurta_seva` · Saṅgam `_c_panchanga_quality` · Vighnakara `_check_panchanga_obstruction` · four tārā tables (Saṅgam, w23, `gochara_rules/p6`, grammar) besides `panchang_engine.tara_bala` | four tārā tables |
| Event ontology (`brahma_event_ontology`) | ≥ 14 separate readers across Kṣetra, intensity, v3, century, sweep, resonance, grammar, yojaka, avadhi, taranga | no loader |
| Intensity / score formulas | noisy-OR (5 sites) · multiplicative × saturating (Saṅgam I-16) · exponential (intensity, duplicated in v3) · log-linear hazard (Kṣetra) · geometric-mean modifiers (w21/w27/w30/legacy) · harmonic mean (taranga) · linear weighted (tulana) | **two functions named `orb_strength_score` with different formulas** (`transit_search.py:131` linear ×1.2 applying; `ka_sangam/engine.py:761` cos² ×0.7 separating; `taranga_service` imports the second) |
| Ayanāṃśa handling | five patterns (sidereal flag; tropical minus a constant offset at a reference date; per-JD `get_ayanamsa_ut`; a supported-set map; `compute_positions(..., 'lahiri')`); `CANONICAL_AYANAMSHA` restated in 11 modules | the overlays' constant-offset pattern drifts across a century |
| Resume ledger (`build_substep_progress`) | three private copies (Saṅgam, Kṣetra, sweep); the orchestrator's `completed_keys` is never passed, so resume is entirely writer-side | no helper |
| Idempotency | every L3 writer inlines its `DELETE`; neither `ga_writers/_idempotency.py` nor `bodha_writers/_idempotency.py` is imported by any `ka_*` writer | — |

### 3.2 The package

A Python package under `platform/python-sidecar/services/kala_core/`, importable by every stage, projection and service writer. **No writer of its own; no registry row.** It is the layer's "shared substrate brief type" the concept note said was missing (§11). Each module below names what it is extracted from, so the extraction is a move with tests, not a rewrite. The kernel's `arcs.py` already being "adopted from `w2g/arcs.py`" is the precedent: this is the third copy becoming the only copy.

| Module | Contents | Extracted / consolidated from (today) | Replaces (never again implemented locally) |
|---|---|---|---|
| `sky/` | ephemeris at T (two read paths, memo cache); boundary-event enumeration per body; contact solver (arc-index bracket → Swiss refinement; stations always refined); directed graduated dṛṣṭi geometry (forward count, nodes cast none); canonical physical identity and occurrence ordinals; coverage records | `gochara_kernel/substrate.py`, `knots.py`, `episodes.py`; `ka_graha_sancara`; `gochara_v3/interval_solver.py`; `w2g/{arcs,crossings,solver}.py` | `ka_sangam/engine.py`'s own ephemeris scan and symmetric aspect table (G-7); `ka_kshetra/stage0_kinematics.py`'s own kinematics (held per B8-6 as *evaluation-only* until equivalence is demonstrated); the century materializer's per-class×decade solver loop; `pipeline/transit_search.py`'s duplicate aspect search |
| `clocks/` (F2) | `period_context`, `boundaries`, applicability per system, hierarchy walk L1–L4, sandhi bands, σ with the correct linearisation, scenario sets; pinned `chart_dashas` read contract (build id, ayanāṃśa, tier) | `ka_dasha_kala/service.py`; `ka_kshetra/stage3_clocks.py` (the one place σ_t exists); `ka_avadhi` readers; the NOW `dasha_sandhi` lite logic (TypeScript, re-implemented once here and served from the table) | Saṅgam's `KaDashaKalaService` prior with the static 0.5 fallback; Kṣetra's `chart_dashas` read without `ayanamsha_id` (rank-3a); every reader's own "is period X active at t" |
| `promise/` (F1) | signed mechanism graph builder from L1 `chart_facts`, `ga_yoga_firings`, `chart_divisionals` + versioned L0 rules; cancellation and exception edges; frame; event-class mapping; L2 attachment loader (MSR, CGM, Pratijñā ledgers) with `missing_fact` vs `evaluated_empty` | `ka_yojaka` signature-class templates and predicate compiler; `ka_kshetra/stage2_promise.py`; `ka_gochara_resonance` target discovery (relationship-record projection) | Kṣetra's own promise nodes/edges/routes; Yojaka's one-domain, 0°-Aries-target predicates; resonance's "first root only" dedup |
| `rules/` | rule registry read model: paths, prerequisites in evaluation order, soft factors, versions, `provenance`, `operator_role`, source locators; admission predicate | `gochara_kernel/rule_registry.py` (read side) | any stage keeping its own rule constants |
| `calendar/` | pañcāṅga primitives (tithi, vara, nakṣatra, yoga, karaṇa, horā, gulika, diśā-śūla), location-mandatory; muhūrta scoring; Tāra-bala | `ka_muhurta_seva`, `panchang_engine`, `muhurat/finder.py` | the NOW/AHEAD TypeScript re-implementations of daily primitives (they become reads) |
| `overlays/` | adapters that read `kala_vedha_gochara`, `kala_moorti_nirnaya`, `kala_kota_chakra`, `kala_tithi_pravesha`, `kala_sudarshana_varsha` into assertions with `method_qualification ∈ {qualified, method_contested, uncited_extension}` and coverage | the five writers' own output contracts | each consumer's own join to these tables |
| `assertion/` | the object model: `Assertion`, `IssuedForecast`, `Outcome`; `null_reason`; `role`; evidence algebra operations (`increment_allowed(root, stage)`, `attach(claim, forecast)`); canonical forecast identity | concept note §2, §5.3; `gochara_kernel/record_store.py` identity discipline | every stage's private row shape |
| `measure/` | elementary half-open segments and support vectors; `D(W)` centred difference with conditioning; conditional and whole-pipeline shift nulls with `(b+1)/(R+1)`; surrogate-diagnostic flag when exchangeability fails; interval score; four-way verdict type `pass · fail · insufficient_evidence · not_evaluable`; exposure manifests | `ka_kshetra/stage5_null.py`, `dhara_sweep.py`, `dhara_term_matrix.py`; `gochara_eval/*` (offline scorer); Saṅgam's Mode A–D scoring (retired as row producers, kept as fixtures) | per-stage p-value layers; Saṅgam's `confidence_*`, `independent_current_count`, `rarity_years` |
| `manifest/` | generation identity; `input_vector` (content hash of everything a substep consumed); publication manifest row; compare-and-swap; completeness attestation; reachability retention; serving-guard check | `gochara_kernel/{ledger,input_vector,seal_brief}.py`; `kala_gochara_authority` / `kala_gochara_publication` pattern; Kṣetra's W7 design | Kṣetra's own snapshot/publication; `LIMIT 1` binds; `'v1'` COALESCE fall-throughs |
| `verify/` | verifier harness: recompute from stored inputs by an independent path, compare digests, write a verification row; mutation-test helpers | `gochara_kernel/{inventory_verifier,window_verifier,verification_job}.py` | per-stage ad-hoc integrity SQL |
| `vocab/` | closed vocabularies: frames, event classes, grains, roles, states, operator roles, null reasons, method qualifications; generates the Vocab declarations | scattered enums and vocab modules (`peak_basis_vocab`, `shape_conformance_vocab`, `verification_vocab`) | string literals in writers |
| `idempotency/` | `replace_partition(conn, table, chart_id, generation, grain_key, rows)`; mirrors `ga_writers/_idempotency.py` | per-writer delete-then-insert code | accretion |
| `ontology/` | one loader for `brahma_event_ontology` (shape, valence, milestones, class roster) with the 27-class universe from `gochara_rules/registry.py` as the single roster | ≥ 14 readers (§3.1) | per-module ontology SQL |
| `resume/` | `build_substep_progress` ledger helper: content-bound fingerprint per grain, read in `plan_substeps` (never destructive), checked in `run_substep` | three private copies | per-writer ledgers; a `plan_substeps` that deletes |
| `ayanamsha/` | one policy: pinned convention id, per-instant sidereal offset through the `swiss_state` lock, `CANONICAL_AYANAMSHA` defined once | five patterns in 11 modules | constant-offset drift in the overlays |

**Ownership constraint.** `gochara_kernel` is Pravāha's and the judge is frozen. `kala_core.sky`, `rules`, `assertion`, `manifest`, `verify` must therefore *import* the kernel's pure modules (or thin re-exports) rather than move them, until the Pravāha steward rules on relocation (§12 R-1). The library's public API is designed so the import direction can be flipped later without touching stage code.

---

## §4 · Stage and projection contracts

### 4.1 Build order and grains (one build slot; the orchestrator commits per substep)

| Order | Asset id | Kind | `plan_substeps` grain | Idempotency scope | Reads | Writes |
|---|---|---|---|---|---|---|
| 0 | sky substrate (judge-owned tables `ka_gochara_sky_event`, `_sky_convention`, `_physical_object`; see §12 R-2 for the registry question) | shared, heavy | `body:<Body>` × 8 (+ `convention`) | `(convention_id × body)` | `bg_ephemeris` / Swiss | sky events |
| 1 | `ka_dasha_kala` (F2 service) | service self-test | — | — | `chart_dashas` pinned | `asset_registry` self-test |
| 1 | `ka_avadhi` (F2 materialised) | light | — | `(chart × generation)` | F2, F1 attachments | `kala_avadhi` re-shaped: period rows with σ, applicability, lord condition, attached promise ids |
| 2 | `ka_yojaka` (F1) | heavy | `class:<event_class>` | `(chart × generation × class)` | L1 facts, L0 rules, L2 attachments | `kala_activation_predicates` re-shaped as the promise graph (nodes, signed edges, frames, event-class map, attachments); strangler: new columns, old columns retired after consumers migrate |
| 3 | `ka_gochara_v5` (judge) — Pravāha | heavy | `rules → convention → body:<B> → inventory:<class> → coverage:<class> → record:<class>:<path> → window:<class>:<path>` (A5.3 pins) | `(chart × generation × grain)` | sky, F1 (after R-1), `chart_dashas` pinned | contacts, records, windows, coverage, publication |
| 4 | `ka_vighnakara` (negative space) | light or `class:<event_class>` | `(chart × generation × class)` | judge records (obstruction, cancellation, exceptions), F2 applicability, judge coverage | `kala_obstruction` re-shaped: `(assertion_id, state ∈ six, what, by_what, interval, release_condition, roots)` |
| 5 | `ka_sangam` (jury) | heavy | `class:<event_class>` then `attach` | `(chart × generation × class)` | judge assertions, negative space, F1, F2, admitted schools' assertions (G-J first) | `kala_convergence` re-shaped: jury assertions, segments, `D(W)`, turning points, contests; claim attachments |
| 6 | `ka_kshetra` (forecaster) | heavy, staged | `S2/S3 → class:<c> field → null → salience → snapshot` (S0/S1 kept, evaluation-only, per B8-6) | `(chart × generation × class)` | judge + jury assertions, negative space, F2, base rates, F3 roles | compact field (`kala_field` re-shaped to segments with coefficients, masks, `∫λ`), `kala_field_null`, `kala_field_salience`, `kala_field_snapshots` |
| 7 | `ka_kalasutra` | projection | — | `(chart × generation)` | jury attachments + judge windows | `kala_activation`: per-signal intervals, recurrence ladder from judge contacts |
| 7 | `ka_kala_darshana` | projection | — | `(chart × generation)` | manifest, judge windows, jury `D`, negative space | `kala_darshana`: the published confluence view |
| 7 | `ka_taranga` | projection | — | `(chart × generation)` | forecaster `∫λ` per month, domain scope only | `kala_taranga` (event-class half retired) |
| 7 | `ka_jivana_parva` | projection | — | `(chart × generation)` | F2 hierarchy + per-period aggregates of assertions | `kala_jivana_parva` (no count from any table not in the manifest) |
| 8 | `ka_bhavishya_lekha` | registrar | — | append-only by forecast identity | jury attachments, forecaster odds (if calibrated), manifest cutoff | `issued_forecast` rows (new table or `kala_bhavishya` re-shaped); registers prospective forecasts in Samīkṣā |
| 9 | `ka_tulana`, `ka_muhurta_seva`, `ka_graha_sancara` | service self-tests | — | — | — | `asset_registry` |

Adapters (`ka_vedha_gochara`, `ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`) keep their writers and tables at level 1 (as today) and gain `method_qualification`, `coverage` and `upstream_fingerprint` columns where missing; the judge consumes them through `kala_core.overlays`.

### 4.2 The assertion row (every stage table, one shape)

```
assertion_id · chart_id · generation · stage ∈ {judge, negative_space, jury, forecaster} · method (path_id | group_id | model_id) · rule_version
subject {event_class, affected_person, objects[]} · frame · period_anchor {system, MD, AD, PD?, applicability}
interval [t0, t1) · grain ∈ {year, era, month, week, day} · resolution {computation, source_licensed, empirically_supported}
role · roots {contact_ids[], record_ids[], fact_ids[]} · derivation_parents[] · used_for_selection
source {text, locator} · provenance ∈ {verse_cited, uncited_extension} · operator_role ∈ {scored, testimony}
value fields per stage (judge: evidence_for/against, valence, severity · negative space: state, what, by_what, release ·
                        jury: D(W), segment_support · forecaster: alignment_null_p, intensity, integral, odds?)
null_reason (typed) · coverage_ref · precision {method, Δλ, Δt} · input_vector_hash
```

Invariants (oracles, §10): no L1 value restated; `generation` NOT NULL; testimony contributes zero everywhere; duplicates, aliases and relocation between stages change no result; an issued forecast is never edited.

### 4.3 Projection writer template

```python
@register("ka_kala_darshana")
class KalaDarshanaWriter(WriterBase):
    def run(self, ctx):
        gen = manifest.current_generation(ctx)            # kala_core.manifest; refuses if unpublished
        rows = ctx.db_conn.execute(DARSHANA_SQL, gen)     # pure SQL over judge/jury/negative-space tables
        return idempotency.replace_partition(ctx, "kala_darshana", ctx.config["chart_id"], gen, rows)
```

No Python in the middle. The SQL is reviewed as the projection's whole semantics. `count_sql` counts `(chart_id, generation)` with a depth-0 `chart_id = $1`. `integrity_check_sql` is written for the engine as it runs it: unparameterised, scoped to the chart by reading the running `build_runs` row, truthy first column means pass, and it claims only this writer's output. Ldgr is satisfied because every output row carries the assertion ids it joined; Dens because the projection carries the stage's tier column through.

---

## §5 · The serving plane

Finding F-L19 of the review is structural: the eight Kāla views are composites that live only in the MCP package, so the web engine and the portal cannot reach them, and their TypeScript re-implements calendar logic the core library owns.

**Change.** Each view becomes **one retrieval-registry composite capability** (the pattern `judgment_query` already uses in `register_d9_judgment.ts`), with: `density_contract` declared, `empty_reason` discipline, drill pointers, and the manifest id on every response. The MCP facades in `platform-mcp/src/tools/kala_views/` become thin aliases of the registry capability (as `register_p1_aliases.ts` already does for several tools). The Vidhi bridge then resolves `now_read`, `ahead_read`, `priority_read`, `elect_read`, `story_read`, `ritual_read`, `explain_read` by construction, because the capability's own name is the live tool name (`catalog_name_direct`).

**Rules.** A view reads stage tables and the manifest only; it never computes a primitive (the calendar primitives are read from the table F2/calendar wrote, or called through the service facade); confirmed, testimony and catalog-only rows are counted separately (§N.6); the `'3.0'`-era rows are labelled `context_only` until retired; `kala_taranga` gets a facade or is dropped from the Vidhi primitive list (today the primitive points at a tool that does not read it).

---

## §6 · Build and rebuild efficiency

### 6.1 Where the cost is today (measured or documented)

| Cost centre | Measured (W1 analysis, 2026-09) [A] | Where the time goes (code) |
|---|---|---|
| Kṣetra full build | 22,685 s = 6 h 18 m over 308 substeps and 10.5 M rows (registry estimate 237 s, 96× off); 29 failed attempts on 2026-09-10/11; "connection lost" terminal | `stage5dhara` null **15,415 s (68 %)**; `stage4` field 5,418 s (24 %); `stage8` 1,224 s for six view rows; the per-class context builds full-horizon DHARA segments on the first substep touching a class and rebuilds it after any restart; `stage8` reloads windows/boundaries/ontology per view; `prepare:replace` deletes 15 tables but first fails closed on any existing output (the Idem-failing hold) |
| Century materializer | 3,480 s (58 min) over 270 substeps (estimate 614 s, 5.7× off); held | `ClassContext.fetch` **per class × decade substep** re-reads chart-level natal, AV, sade-sati, vedha, mūrti, kakṣyā, bindu; decade slices recomputed per substep; writes both staging and production tables |
| Saṅgam + spine | ≈ 2,251 s (estimate ≈ 513 s, 4.4× off); 15-minute watchdog | each `lifetime:<i>` substep is a 100-year scan per predicate against 0° Aries; `plan_substeps` **deletes all `kala_convergence`** (destructive planning, re-invoked by the orchestrator's no-op re-probe); ledger fingerprint includes `date.today()` |
| Kalasutra | 487 s p50 (estimate 33 s, 14.8× off) | per-run daśā timeline cache; implicit `date.today()` |
| Retired sweep | ≈ 30 h per chart (per-year chunking after a decade substep exceeded 1,800 s) | daily grid × 27 classes × 100 years |
| Five overlays | 2–3 s each (estimates accurate) | small; their only cost is horizon (15 months) |
| Orchestrator | 600 s default timeout per substep; one connection, serial; `completed_keys` never passed (resume is writer-side) | grains must stay under the timeout; resume must be content-bound |

### 6.2 The efficiency design

1. **Sky once, chart-independent.** Boundary events per body per convention are geocentric and shared across every chart (Gochara spec §6.1: "one substrate per convention"). Build once; a new chart solves only its contacts against stored boundaries, `O(B log B + output)`. Moon and day tier on demand with a coverage record, never materialised.
2. **Chart preparation once per generation.** A `ChartContext` (natal facts at pinned tier, conventions, F1 graph, F2 boundaries) is built in the first substep, serialised and content-hashed as the generation's `input_vector`; every later substep binds to the hash and refuses on mismatch (A5.3 "every later substep verifies the inputs it consumes"). No per-class re-preparation (strategy P2).
3. **Three lineages, layer-wide invalidation.** The manifest records which lineage each stage consumed. On rebuild: an L2 change marks stale F1 → negative space → jury → forecaster → projections and leaves the sky and the contacts untouched; an L1 natal change marks the judge's contacts and everything after; a convention or solver change re-solves the sky once for all stages. The mechanism is the orchestrator's own edge-based staleness propagation over a **truthful** `depends_on` (review F-L4), not a writer-side skip: a writer never holds on "output exists" or "inputs unchanged" (that reads `FAIL` on Idem). What a writer *may* do within the frozen contract is the judge's rule: when its grain is marked stale, decide from the recorded input vector whether to re-solve geometry or only re-score (spec §10.1), and record which fired.
4. **Compact field instead of dense rows.** Segments are the union of knots of the terms actually in the model (clock boundaries of systems with non-zero coefficients, contact in/out instants, mask edges); coefficients and `∫λ` per segment reproduce W2's likelihood exactly. Dense rows are deleted only after a byte-equality test on sampled instants and integrals (concept §6.1). Expected order: tens of thousands of segments per class, not 343 k; the number is measured before any promise.
5. **The null once, shared.** The shift-null machinery lives in `kala_core.measure` and runs once per generation over segments, serving both the jury's `D(W)` and the forecaster's alignment surprise; no second p-value layer (concept §6.2). The DHARA sliding-window reducer is replaced by the exact blocked order-statistic reducer the strategy names (P1), with the same finite-value policy and denominators.
6. **Projections in seconds.** Eleven writers that today compute become SQL; their rebuild cost is a join. They are the cheapest part of any full-layer rebuild and never the reason a rebuild fails.
7. **Substep grains that resume.** Heavy stages plan per `class` (26 scored classes), each an idempotent delete-then-insert of its own partition inside one orchestrator transaction and under the 600 s timeout, so a lost connection loses one class, not a build. Coverage partitions are written first in the same transaction (pin 7). Resume is content-bound (same `input_vector`) through `kala_core.resume`, never positional, and **`plan_substeps` never deletes** (the orchestrator re-invokes it under a released savepoint for the no-op re-probe; Saṅgam's destructive plan is a live hazard).
7a. **One null, computed once, sized by the model.** The 68 % of Kṣetra's build spent in the DHARA shift-null (R = 1024 replicates over dense per-class segments) becomes one `kala_core.measure` pass per generation over elementary segments shared with the jury; replicates are drawn per *segment set*, not per dense row, and the reducer is the exact blocked order statistic the strategy names (P1). The replicate count is a declared parameter with its own power argument, not a constant.
8. **No learned weights, no 25-parameter fit, no composite salience at first build** (concept §9 cut list). The first generation is structurally correct and cheap; enrichment is admitted step by step with its own oracle and cost class.

### 6.3 Benchmark contract (strategy §5, adopted)

Before any speed claim: exact source/dependency/model versions, hardware, ephemeris files, workload dimensions, cache state; wall and CPU time, peak RSS, time in Swiss calls, SQL count and round trips, rows/bytes/WAL, checkpoint and recovery cost, time to first qualified consumer result; repeated matched runs with spread; cold, warm, resume, horizon-extension, upstream-correction, no-window, dense-window and rare-boundary workloads. Rehearsal database first; the canonical chart only through the orchestrator under the campaign's standing authority, with a backup before every production rebuild and a dry run before any irreversible delete (N-154). **No minutes-per-chart figure is promised by this plan.**

### 6.4 The full-layer rebuild (what Suvarṇa's layer close requires)

One orchestrator run, `action=rebuild, clear_before=false`, over the L3 asset list in level order, canonical chart. With this architecture the list is: sky (shared, skipped if its convention is unchanged) → F2 self-test, `ka_avadhi` → `ka_yojaka` → `ka_gochara_v5` → `ka_vighnakara` → `ka_sangam` → `ka_kshetra` → the five projections → `ka_bhavishya_lekha` → service self-tests. Every writer deletes and re-inserts its own `(chart × generation)` rows, which is itself the Idem proof.

---

## §7 · Certification by construction — the nine gates

Suvarṇa certifies an asset when every core gate reads `PASS` or a rule-computed `N/A`, every declared addition is certified, no open gap row remains on a gate, and a disposition is recorded; "current" means the certification still matches the writer's file hashes, the upstream certificate ids, the declarations file's hash, the registry revision and the asset's semantic fingerprint [S campaign plan §1.1; `nikasha_certify.py`; `asset_elevation_tracker.py` E6.3] [A]. Verdicts roll up worst-first (`FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS`); only `PASS` or a rule-computed `N/A` closes a gap; a reviewer's opinion is never a detector.

**Governance, kept to the minimum that is load-bearing.** The native's instruction for this plan is that governance and security stay at the essential minimum. Four rules are essential because the engine measures them and the design depends on them: (1) every writer is a frozen-contract `WriterBase` writer that deletes-then-inserts its own rows; (2) a backup precedes every production rebuild and a dry run precedes any irreversible delete, on the canonical chart only, through PRs to `main` (the campaign's current lean operating model, N-154); (3) served output is never wrong or partial without an authority switch or a disclosure (N-29), which the manifest compare-and-swap provides; (4) each asset ships one certification pack (below) so the engine's detectors can read `PASS`. Everything else in the campaign's governance is consumed as given and not discussed here. Where the engine stands [A]: no L3 asset passes every gate today, Dens and Build read mostly `FAIL`, five gates read mostly `NO_DETECTOR`, and no L3 asset has the fingerprint declaration a certificate needs; the newest detector set lives on the engine branch, not yet on `main`.

The table maps each gate to the mechanism that satisfies it in this design and to the real detector (from `asset_census.py`'s `CRITERION_REGISTRY`) that could read false.

| Gate | Meaning | Mechanism in this architecture | Detector / lint that can fail |
|---|---|---|---|
| **Ldgr** (`Ldgr.source_presence`) | every derived value traces to its facts | every stage table carries a LEDGER source column (`roots.fact_ids` resolving to `chart_facts.fact_id`, or `signal_id` resolving through `bodha_msr_signals.constituent_facts_array`); projections carry assertion ids; the `source` declaration is `LEDGER` with the resolving path; adapters with a citation column declare K1 | the detector resolves every row's ids; a placeholder or an unresolved id is `FAIL`; `citation_state` unsourced caps at `NO_DETECTOR` |
| **Idem** (`Idem.pattern`) | rebuild replaces, never accretes | `kala_core.idempotency.replace_partition` is the only write path and its `DELETE` names the asset's **own** table(s); grain = `(chart × generation × class)`; **no "output exists → hold" anywhere** (Kṣetra's `KshetraReplacementHeld` reads `FAIL` today and is removed with W7's manifest switch) | `idem_scan` follows the writer's delegation chain: a plain INSERT without a delete of its own table, an upsert without a delete, or a hold with output present → `FAIL`; a dynamic table name → `PARTIAL` |
| **Earn** (`Earn.build_record`, `Earn.service_state`) | every status has a detector that could read false | data assets declare `kind: data` (releases `service_state`); `rows_per_second`/`last_built_at` come from the orchestrator's attempt record, never written by the writer; services declare `service_probe` matching the registry `health_probe`, with a fresh self-test; every stage additionally has a `verify` substep writing a verification row (the judge's pattern) | the attempt-timing join; a stale self-test; mutation tests on the verification rows |
| **Null** (`Null.schema_default`, `Null.blank_rows`) | null, never an invented default | one `null_convention` declaration per stage table (nullable columns with meaning and scope, constants, stamp columns, allowed literals) generated from `kala_core.vocab`; a clean static writer scan (no literal fallback written to a prose column); `null_reason` typed | both criteria are **capped at `PARTIAL`** unless the declared convention verifies live or the writer scan is clean; `prose_none` only where checked |
| **Vocab** (`Vocab.identity`, `Vocab.alias`) | closed vocabularies | every stage table has a PK or UNIQUE constraint over its natural key (`(chart_id, generation, grain, assertion_id)`); `vocab_alias` declared per table (`class: planet` with `identity_only` on graha columns; `no_alias_class` only where no graha-like column exists) | identity from `pg_constraint` on a non-empty table; `no_alias_class` is refused where a `graha`/`lord` column exists |
| **Carr** (`Carr.D1`, `D2`, `D3`) | classical sources carried faithfully | each asset declares **one** carriage nature: adapters and the rule registry `transcription` (D1, locator check); stage tables `computation` with `nature: single_derivation` until a reviewed D3 method exists; `per_witness_values: false` | a mismatch between declared nature and the measured check is refused; `single_derivation` is refused where a D3 method exists |
| **Narr** (`agree`, `checkable`, `fidelity_test`, `lint`) | text restates cited facts | stage tables have **no prose** → a checked `prose_none` (closed `values` on every text column; JSON with no string leaves); views narrate at serve time from assertion fields only, with golden narration tests; `count_sql` has a depth-0 `chart_id = $1` | a bare `[]` or `null` `prose_fields` reads `NO_DETECTOR`; `fidelity_test` caps at `PARTIAL` without a declared golden test; `checkable` needs the scoped count |
| **Dens** (`Dens.served`, rev 8) | served output layered by confidence | every stage table carries a **tier column** the served SELECT reads (`operator_role`, declared in `density_tier_columns`, or the existing `verification_pass_status`); every view capability declares `density_contract` with facets; `context_only`, testimony and confirmed rows counted separately | `N/A` only if no served TypeScript module SELECTs the table; otherwise one capability with `density_contract` whose own SELECT reads a tier column, else `FAIL` (**most L3 assets read `FAIL` here today**) |
| **Build** (nine criteria) | orchestrator can dispatch; rebuild produces the right result | exactly one `@register`; `WriterBase` with `run` XOR `plan_substeps`+`run_substep` and `has_substeps` matching; no commit/close, no `asset_throughput` write; `depends_on` equal to the tables the writer's SQL actually reads (`Build.dag` parses it); non-constant chart-scoped `count_sql`; `integrity_check_sql` written for the engine as it runs it (**no parameters, truthy first column = pass; scope to the chart by reading the running `build_runs` row, the migration-1288 pattern**); `produced_tables` declared when a writer writes more than one table (`Build.completion` compares against the sum); a writer-digest entry in `nirmana-writer-digests.json` (else the wave dispatcher refuses `IMAGE_SKEW`); every dependency lit and fresh | the Build exercise: an orchestrator run on the canonical chart whose substep plan completes (D2); attempts since the last writer-digest change must not error (`Build.history`); Suvarṇa re-measures |

**The certification pack each re-shaped or new writer ships with (K8):** `kind` · `carriage` (nature + served-surface read evidence) · `source` (LEDGER or K3) · `vocab_alias` · `prose_none` or `prose_fields` + `fidelity_tests` · `null_convention` · `produced_tables` · `density_tier_columns` · a semantic-fingerprint declaration (the first for any L3 asset) · a writer-digest entry · a disposition row. Any edit to the declarations file invalidates every gate certificate, so the pack lands once per packet, not per PR.

**Three facts that shape ids and sequencing, and nothing more.** (a) With projections as SQL, each of the sixteen frozen "family readers" is certified in the same build as its stage, which collapses the reader backlog. (b) The wave tool treats any id matching `ka_gochara*` as Pravāha's family asset, so the sky substrate must not take such an id unless Pravāha owns it (§12 R-2). (c) The four services keep their self-test writers until the engine branch's service declarations reach `main`; nothing else about them changes.

---

## §8 · Asset-by-asset code dispositions

Vocabulary: **stage** (a computing writer in §4) · **projection** (SQL writer) · **adapter** (method input, table kept) · **service** · **core** (code moves into `kala_core`, asset keeps its id) · **supersede** (writer retired after migration, `superseded_by` set, data retained) · **historical**. No registry row is deleted; `is_active`, `superseded_by`, `data_disposition` carry the lifecycle (Suvarṇa I6/N-29).

| Asset | Today (lines, main module) [S] | Code disposition | What moves, what stays, what is deleted from code |
|---|---|---|---|
| `ka_gochara_v5` | 840 writer + 16,650 `gochara_kernel` | **stage (judge)** — Pravāha | untouched here; `kala_core` imports its pure modules (R-1); consumes `ka_yojaka`'s F1 for natal-fact rows after the steward's amendment (R-3) |
| `ka_gochara` | 462 writer, writes the old `_v2` table | **supersede** by `ka_gochara_v5` per Pravāha's strangler (asset id decision is Pravāha's, concept §8.6) | writer retired after the flip; `_v2` tables retained until N-29 disposition |
| `ka_gochara_v3_century_materialize` | 2,512 writer + 6,133 `gochara_v3` | **supersede** by the judge + compact evaluator; data retained | `gochara_v3/engine.py` scoring astrology: kernels already reused by the judge; `mechanisms/*` retired (their w27b/w27c inputs were never fed); `interval_solver.py` → `kala_core.sky` |
| `ka_gochara_v4_41_candidate` | 534 | **historical** once `'5.0'` lands | registry row gets `domain`/`rung`; writer deregistered |
| `ka_gochara_sweep` | retired | **historical** | nothing |
| `ka_gochara_resonance` | 1,264 writer | **core → F1** (target discovery becomes relationship-record projection) + corrections R-1…R-6 | writer kept until the judge reads F1 directly; then supersede |
| `ka_vedha_gochara` | 573 | **adapter** | add Saṅgam edge, horizon coverage, `method_qualification`; exceptions per G-9 |
| `ka_moorti_nirnaya` | 351 | **adapter, gated** (`method_contested`) | no consumer reads it directly until adjudicated |
| `ka_kota_chakra` | 206 | **adapter** (`uncited_extension`) | judge soft factor only after a primary citation |
| `ka_tithi_pravesha` | 235 | **adapter, gated** | same as moorti; NOW/AHEAD coverage reconciled |
| `ka_sudarshana_varsha` | 116 | **adapter → judge method** at enrichment step 2 | frames and nested periods via `kala_core.clocks` |
| `ka_graha_sancara` | 268 writer + 438 engine; **no caller among the L3 writers today** (the overlays import only its constants) | **service** = `kala_core.sky` facade, and the only ephemeris door for every stage | self-test unchanged; gains the arc-index/Swiss-refined solver API |
| `ka_dasha_kala` | service | **service = F2** | gains applicability per system, σ, scenarios; static fallback removed |
| `ka_avadhi` | 332 | **F2 materialised** (re-purposed, same id) | dossier = F2 period rows + F1 attachments + lord condition (BPHS 47.5–6 at step 2); the failed-build diagnosis is moot because the writer is rewritten |
| `ka_yojaka` | 1,026 | **stage (F1)** | signature-class templates retired; predicate table re-shaped to the promise graph; 0°-Aries targets gone by construction |
| `ka_sangam` | 1,168 writer + 1,812 `engine.py` | **stage (jury)**, rewritten | own ephemeris scan, symmetric aspects, Modes A–D as row producers, static prior, `confidence_*`, `independent_current_count`, `rarity_years` deleted from code; Mode fixtures kept as tests |
| `ka_vighnakara` | 997 | **stage (negative space)**, rewritten | own malefic-transit scoring and `override_score` deleted; six states from judge records |
| `ka_kshetra` | 2,637 writer + 14,069 package | **stage (forecaster)**, re-shaped | S0/S1 kept evaluation-only (B8-6); S2 → `kala_core.promise`; S3 → `kala_core.clocks` (σ fix lands there); S4 → compact evaluator; S5 null → `kala_core.measure`; S6/S6.5 salience and insights kept; S8/snapshot → `kala_core.manifest`; `uncertainty.py:268–276` defect fixed once in `clocks` |
| `ka_kalasutra` | 285 | **projection** | eight-match truncation, implicit today, all-row accumulation deleted |
| `ka_kala_darshana` | 234 | **projection** | 0.5-on-missing default and top-750 cut deleted |
| `ka_jivana_parva` | 444 | **projection** | convergence-count fields derived only from manifest-published assertions; `LIMIT 1` predicate selection deleted |
| `ka_bhavishya_lekha` | 594 | **registrar** (issued forecasts) | probability tiers, rank identity, L4 `phala_anchors` read deleted; append-only by canonical forecast identity; Samīkṣā registration |
| `ka_taranga` | 257 | **projection** (monthly `∫λ`, domain scope) | own convolution and event-class half deleted |
| `ka_tulana` | 87 writer + ranker | **service**, wired | PRIORITY calls it over jury `D(W)` + forecaster axes; I-11 fixed weights deleted |
| `ka_muhurta_seva` | 72 writer + engine | **service** = `kala_core.calendar` | election view re-based on qualified methods later |
| `gochara_grammar` (3,393) | the de-facto shared read layer of the v1/v3 generations (`resonance_map`, `dasha_data`, `event_class_scope`, `read_tier_policy`, `derived_points`) | **core** | read models move to `kala_core.{promise, clocks, ontology, rules}`; the legacy node-aspect table (`primitives.py:192`, Rāhu/Ketu cast 5/7/9) is retired in favour of the kernel's convention (N-14); the `test_aspects.py` lock on nodes = Jupiter is rewritten, not deleted silently |
| `gochara_intensity` (1,998), `gochara_v3/mechanisms` | the v1/v3 λ engines | **retire with v1/v3**; `enrich_targets`, `compute_x_t` kernels kept only if the judge's rule paths cite them | `permission` gets its own contract or retires (strategy §7) |
| `kala_trigger` (629) | signed currents composed onto Saṅgam's score | **core → negative space** | the four detectors that survive doctrine review become negative-space producers reading judge records; `compose_with_ka_sangam` deleted |
| `kala_permission` (711) | MD–AD licence gate, admission-rejected, no production consumer | **retire** (code deleted after one generation; tests archived) | the judge's `permission_per_instant` is the one permission model |
| `w2g` (2,258), `taranga_kernel` (500), `taranga_service` (806) | global arc substrate; the W2 waveform kernels | **core / retire**: `w2g` arcs and solver → `kala_core.sky` (the kernel's `arcs.py` already descends from it); `taranga_*` retired once the projection exists | `class_fingerprint` → `kala_core.manifest` |
| `ka_temporal/date_resolver` (690) | predicate → date resolution; daśā timeline loader (no tier filter) | **core → clocks** | the implicit `date.today()` becomes an explicit `as_of` |
| `pipeline/transit_search.py` (958) | daily step scanners; the backbone of v1/v3 scoring | **keep as a service for ad-hoc queries only** (`call_transit_search`), never as a stage's geometry; stage geometry is the arc-index + Swiss-refined solver | the second `orb_strength_score` formula is renamed; the ×1.2/×0.7 conventions are cited or dropped |
| `brahmagyan/kala/*` (5,577) | legacy KA-3 CLI modules with the native's daśā schedule hardcoded; **write the same tables as `ka_sangam` and `ka_vighnakara`** | **retire** (the one importer, `l5_event_chart_state_index.py`, migrates to the stage tables) | a second writer to a stage table is an Idem and Earn hazard |

---

### §8.1 · The three family plans, folded item by item

Each ruled or decided item is carried to the module or packet that owns it now. **Adopted** = unchanged; **generalised** = the same decision applied layer-wide; **superseded** = a later ruling (named) replaced it; **held** = still owned elsewhere. Items are cited from the family documents as digested this session [A] and from the concept note [S].

**Gochara family** (GOCHARA_FAMILY_ELEVATION_PLAN v2.2; ruling sheets v1.0/v2.0; native rulings 2026-09-24; Pravāha D-*/ADK-*)

| Item | Disposition here | Lands in |
|---|---|---|
| N-5 `ka_gochara` owns the served product, new generation beside `v1`/`'3.0'` | superseded by Pravāha D-41/A5.3: `ka_gochara_v5` writes `'5.0'`; id strangler is R-5 | §4.1 row 3; §12 R-5 |
| N-10 generation labels and publication manifest | **generalised** to the layer manifest | `kala_core.manifest`; §2.2 |
| N-6 / N-6a century = compact substrate with refinement projection; `is_active=false` | superseded in form: the judge's compute-once sky + the forecaster's compact evaluator are that substrate; R-9 formalises | §8 row; §12 R-9 |
| N-7 Contact object persisted (`kala_gochara_contacts`) | adopted; the judge's contact tables are the layer's geometry | §4.1 row 0 |
| N-4 / N-4a one L0-owned mean-node implementation, never a consumer copy | adopted; conflicts with Kṣetra ruling 7 (S0 decides TRUE/MEAN itself) are resolved once in `kala_core.ayanamsha`/`sky` convention; L0 asked for the column | §3.2 `ayanamsha/`; §12 (routed with R-2) |
| N-11 delete `'2.0'` rows after soak | held by Pravāha (WP10) | — |
| N-13 unqualified kakṣyā contributes no activity | adopted; one AV read for judge P5, jury and forecaster | `kala_core.rules` admission; §3.1 AV row |
| N-14 no node dṛṣṭi; `w30` leaves λ | adopted and made the **only** aspect table; the grammar's node table and its test lock retired | §3.1 aspect row; §8 `gochara_grammar` |
| M-1…M-8 method calls (orb shapes, candidate parameters) | adopted inside the frozen spec v1.4; not reopened | §4.1 row 3 |
| Resonance fixes R-1…R-6 (154 targets on negatives; 54 dangling yoga targets; false "resolved") | adopted; folded into F1 target discovery → relationship records | K2 |
| Interface packets P-1…P-4 (serving, L5, contact ledger) | adopted as the views' manifest-driven provenance | K7 |
| S-1 / S-2 directed events for Saṅgam from the post-T0-1 kernel only; `find_episodes` | adopted; the jury consumes judge assertions, never its own scan | K4; §2.2 jury "must not" |
| T-1 `kala_trigger` packet | **generalised**: surviving trigger detectors become negative-space producers | K3 |
| V-1 Saṅgam declares `ka_vedha_gochara` edge; K-1 Kṣetra declares `→ka_gochara` edge (left out of migration 1084) | adopted in the registry-truth migration | K8 |
| Instructions to Kṣetra (retire internal vedha/mūrti after one cross-check generation; contacts or evaluation-only episodes; remove `'v1'` COALESCE; J2000 axis) | adopted; B8-6 keeps episodes evaluation-only | K5; `kala_core.overlays` |
| F-0 deploy before switch; F-5 full century; D-SCOPE one chart; D-SPECS frozen with C1–C10; AM-21 part 4 PD testimony; protocol v2.1, 47 held-out | adopted verbatim; the manifest compare-and-swap is F-0 generalised | §1 principle 9; §6.2; §10 |
| Branch HOLD "for the layer-wide consolidation merge" | this plan is that consolidation; Pravāha's own `'5.0'` sequence supersedes the held branch | §9 K-packets vs Pravāha A5.3 |

**Kṣetra** (KSHETRA_ECOSYSTEM_ELEVATION_PLAN v1.17; KSHETRA_RULING_SHEET rulings 1–10; PCD-1/2; B8-4/6/7; B-2/B-4; PG349/353; enrichments E0–E8; ablation pre-registration)

| Item | Disposition here | Lands in |
|---|---|---|
| Ruling 1: the calibrated 6-class run is the product; 25-class rows are substrate (F-4 open at SS) | adopted: the forecaster's first generation is six classes; widening is an enrichment with its own gate | K5; §12 (F-4 stays with SS) |
| Ruling 2: re-scope and build fresh at W7 (F-1 open: W7 vs interim clear) | adopted: W7 **is** the layer manifest (candidate → compare-and-swap); the first compact generation is small, so no interim clear of the 8.57 M dense rows is needed before it; dense rows retire only after byte-equality, with an N-29 impact statement | `kala_core.manifest`; §6.2 item 4; §12 R-11 |
| Ruling 3: σ_T from an admitted L1 artifact, never live from `phala_rectification` | adopted and **generalised**: F2 owns σ for every stage; the upward read is deleted | K1 |
| Ruling 4: consume `ka_vedha_gochara`/`ka_moorti_nirnaya`; AV gate from the same source as Saṅgam E2 | adopted: `kala_core.overlays`; one AV read | K2, K5 |
| Ruling 5: order P6 → P2 → P1 | adopted in substance: publication (manifest) and shared context are design properties of K5; the DHARA null (P1) is replaced last, in `measure` | K5 sequencing |
| Ruling 6: enrichments E0 and E1 first | adopted: E0 "what the vighna costs" = the negative-space state + the compact field's scoped suppression term; E1 mechanism fingerprint = per-segment coefficient shares, a query | K3, K5 |
| Ruling 7: node frame disposition (b) | adopted via the single convention (see Gochara N-4a above) | `kala_core.ayanamsha` |
| Ruling 8: one shared vedha/mūrti producer, uniform admission (36 applied / 0 deferred / 6 unqualified) | adopted; adapters + `method_qualification` | `kala_core.overlays` |
| Ruling 9: G3 route-scoped suppression (Option B) + byte-equality | adopted: scoped suppression as route-specific distinctions; byte-equality on sampled instants and integrals | K5; §10 |
| Ruling 10: three-arm ablation before S1 ingestion; park if the shape earns nothing | adopted as K5's admission gate on the rehearsal DB | K5 exit; §10 |
| PCD-1 J2000 time axis (rank 0) | adopted as the axis oracle (several registry events across epochs and time zones) | §10 forecaster |
| PCD-2 inbound reconciliation; edge register both ways | adopted | K8 |
| B8-4 `group_id` content-addressed; `declared_lineage` metadata only | adopted into the assertion identity | `kala_core.assertion` |
| B8-6 Kṣetra episodes evaluation-only; knot producer stays until shared-geometry equivalence | **held** verbatim | §6.2; §11 risk 4 |
| B8-7 declared alias map; `valence` NULL; L2 demand for `event_class.valence` | adopted: `vocab_alias` declarations; the ontology loader carries the demand | `kala_core.ontology`, `vocab` |
| B-2 N/22 counts terminal assets only; B-4 shared grid, no per-class grids | adopted: compact segments per class over shared knots | K5 |
| PG349 / PG353: neither malefic scale used | adopted: negative space reads the judge's vedha records, never a scale of its own | K3 |
| E2 three-arm null | generalised: one null machinery with declared arms | `kala_core.measure` |
| E3 age-varying λ⁰ from life tables | adopted as the forecaster's base-rate axis (`population_sourced` with citation) | K5; concept §6.3 |
| E4 signed promise / bhaṅga | adopted in F1 (signed edges, cancellation keeps polarity) | K2 |
| E5 daśā × gochara interaction; E6 vighna cancellation; E7 lord condition at commencement (BPHS 47); E7b varṣa layer; E8 lattā | adopted as gated enrichments: E7 is the native's step 2; E6 is a negative-space state; E7b gates the contested adapters; E8 is a vedha-adapter row | K3, K5; §4.4 of the concept |
| Stage-3 items (G3 hoist; `baseline_is_synthetic` carried to `kala_field`; S3 σ_T; S2 sign/occurrence; S5 denominator prose; SAVEPOINT on the cohort read) | adopted and redistributed: S2 → `promise`, S3 → `clocks`, S5 → `measure`, the flag → compact field columns | K1, K2, K5 |
| `KshetraReplacementHeld` (refuse rebuild on populated chart until W7) | superseded by the manifest switch; the hold itself fails Idem and is removed | §7 Idem row |

**Saṅgam** (SANGAM_ELEVATION_FINAL v1.0; SANGAM_ALGORITHM_ELEVATION_PLAN v0.4 R-1…R-6, E1…E6; ruling sheet M-1…M-7; KALA_PIPELINE_CONCEPT_NOTE v1.1)

| Item | Disposition here | Lands in |
|---|---|---|
| R-1 target binding (every trigger carries target identity, frame, ayanāṃśa, derivation; defaulted 0° impossible) | adopted at the source: F1 carries targets; the judge solves contacts | K2; judge |
| R-2 atomic clock intersection with parent hierarchy; failed ≠ empty | adopted: F2 + the jury's elementary segments | K1, K4 |
| R-3 geometry cache key vs testimony identity, never coalesced | adopted: physical identity in `sky` (judge), assertion identity in `assertion` | K0 |
| R-4 detector/current audit; C9 and benefic dṛṣṭi assigned a method or withdrawn | superseded by the witness catalogue (G-P, G-J, G-T, G-K, G-A, contest sources); currents that survive doctrine review become declared groups | K4; concept §5.2 |
| R-5 stable contact/episode identity; immutable issued claims; generation-aware dependent map | adopted: judge contact ordinals; `issued_forecast`; manifest reachability retention | K0, K6 |
| R-6 score-kernel separation (activity / valence / applicability / availability; dignity → valence); legacy rows never pooled | adopted: the judge's three-field valence + the jury's `D(W)` + typed states; generation scoping keeps legacy rows apart | K4; `kala_core.assertion` |
| E1 method-specific contact contracts (Parāśari directed graduated; Jaimini rāśi-dṛṣṭi; Tājika) | adopted: judge S-2 events for G-P; G-J then G-T admitted sequentially, each with its own review | K4; concept §5.2 |
| E2 AV as a signed verdict from `ashtakavarga_bindu_sign`; kakṣyā deferred to L1 (G-10) | adopted in judge P5; one AV read | judge; K2 |
| E3 fast-tier refinement conditional on M-3 | superseded: the judge's Moon/day tier on demand; the jury narrows only within licensed resolution, no scored PD narrowing (AM-21 part 4) | concept §5.7 |
| E4 typed natal and clock conditioning (boundary distance per clock/level; lord condition; varga condition); annotation, never a veto | adopted: boundaries with σ in F2 now; lord condition at enrichment step 2; valence in the judge | K1; concept §4.2 |
| E5 episodes with child contacts; Taranga's aggregation unit | adopted: judge contact identity with occurrence ordinals; Taranga = monthly `∫λ` projection | judge; K6 |
| E6 modelled episode frequency with declared exposure; two-axis outcome record; `rarity_years` retired | adopted: exposure manifests in `measure`; `outcome` object (F3, L5-owned) | K4; concept §2 |
| M-3 (the Gochara stream produces directed contact events) | adopted (ruled; cited by both Gochara sheets) | K4 |
| M-1/M-1a, M-2, M-4, M-5, M-6, M-7 | folded into the jury brief as its ruling sheet; the sheet on `main` still reads `AWAITING_NATIVE_RULING` although other documents cite them as ruled (review-digest contradiction 1) — the jury brief re-presents them for one explicit ruling | K4 brief |
| Concept note dispositions: PR #2735 closes without merge; salvage identity-excluding-`peak_date` and E6 semantics as design input; Mode D retired; `confidence_*`, `independent_current_count`, `tier_basis` retired; three runtime readers of `confidence_label` (`ka_bhavishya_lekha`, `ka_kala_darshana`, `ka_tulana/ranker`) move to `D(W)` + witness signature; `register_d7_channel.ts` excluded | adopted verbatim | K4, K6, K7 |
| F-2 option 2 (Saṅgam elevated as jury; Gochara spine; Kṣetra odds/attention); F-3 = N-32; F-6 Mode D a design consequence | adopted verbatim | §2; §12 |

**What the fold changes against the family plans, stated once.** Three things, each already decided by a later ruling and only recorded here: (1) the family plans' "shared" pieces (contact events, vedha producer, AV read, clocks) stop being bilateral obligations between two assets and become `kala_core` modules every stage imports; (2) Saṅgam's and Kṣetra's own geometry and clock code is retired rather than repaired, because F-2 made the judge the spine; (3) the readers that each family plan treated as downstream consumers to be re-pointed become projections of the stages, so their re-pointing is a SQL change, not a writer migration.

## §9 · Work packets, dependencies, owners

Each packet is a separate execution brief on the asset-elevation template (stages 0–3; stage 4+ held by the campaign gates). Dependencies are on *contracts* (frozen spec, F1/F2 API), not on data; packets can be coded against fixtures before any upstream data exists (producer-ready ≠ value-proven).

| WP | Scope | Depends on | Exit | Proposed owner |
|---|---|---|---|---|
| **K0 core skeleton** | `kala_core/{assertion, vocab, idempotency, resume, ontology, ayanamsha, manifest(read side), verify(harness), measure(types)}`; declarations generator; lints (`null`, `vocab`, narration, "no `DELETE` in `plan_substeps`", "one aspect table"); regression oracles for the §11 item 8 hazards | R-1 (import direction) | package importable; 100 % of enums declared; lints green on empty stage modules; the eight-path/two-table duplication register (§3.1) has one owner per row | Track F "shared substrate" lane |
| **K1 F2 clocks** | `kala_core.clocks`; σ linearisation fix; applicability per system; `ka_dasha_kala` facade; `ka_avadhi` re-shape (strangler columns) | K0 | boundaries equal `chart_dashas` by pinned build; covariance oracle; applicability oracle; `ka_avadhi` Build exercise on rehearsal DB | F2 lane |
| **K2 F1 promise graph** | `kala_core.promise`; `ka_yojaka` re-shape; L2 attachment loader; event-class mapping; resonance target discovery folded | K0; L0 rule versions readable | removing an L2 attachment leaves the universe of promise unchanged; removing an L1 fact changes it; `missing_fact` ≠ `evaluated_empty`; zero 0°-Aries targets | F1 lane (+ Pravāha R-3 for the judge's read) |
| **K3 negative space** | `ka_vighnakara` rewrite on judge records + F2 | K0, K1; judge record contract (frozen spec §1, §5) — fixtures until `'5.0'` data exists | six states each with a positive fixture; `evaluated_silent` never becomes a negative forecast; no multiplier anywhere | negative-space lane |
| **K4 jury** | `kala_core.measure` (segments, `D(W)`, nulls, verdicts); `ka_sangam` rewrite; G-J admission as the first witness group; claim attachment | K0–K3; judge assertion contract | J1–J5 oracles with mutation tests; reused root → zero increment; universally active witness → `D ≈ 0` | jury lane (the Saṅgam session) |
| **K5 forecaster** | compact evaluator; `∫λ`; byte-equality against the dense field on sampled instants; S2/S3 moved to core; S5 → `measure`; snapshot → `manifest` | K1, K2, K4; Kṣetra rulings; B8-6 | K1–K6 oracles (concept §6.6) with four-way verdicts; segment count measured; dense rows untouched until equality passes | forecaster lane (the Kṣetra lane) |
| **K6 projections + registrar** | `ka_kalasutra`, `ka_kala_darshana`, `ka_jivana_parva`, `ka_taranga` as SQL writers; `ka_bhavishya_lekha` as registrar | K4 (K5 for taranga) | each projection rebuilds in seconds on the rehearsal DB; every row carries assertion ids; registrar never edits an issued forecast | projections lane |
| **K7 serving plane** | views → registry composites; MCP facades → aliases; density contracts; bridge regenerated; `context_only` label on `'3.0'` rows; the two serving defects (review F-L2, F-L3) | K0 (vocab); independent of data | Vidhi floor primitives resolve `catalog_name_direct`; census harness green; sentinel distinction reaches `kala_now_get` output | Paripraśna / serving owner |
| **K8 registry truth + certification packs** | one surgical migration (number allocated by Strategic Suvarṇa, N-60; the 1200–1299 range is nearly exhausted) correcting `depends_on` to the SQL actually read, stamping the two staged rows, and setting `has_substeps`/`count_sql`/`integrity_check_sql` (engine form: unparameterised, truthy first column) per re-shaped asset; the §7 certification pack per asset; the first L3 semantic-fingerprint declarations; writer-digest entries | K0; the engine branch (`suvarna/engine-100-stack-pr`) on `main` for the service classes | `Build.dag` parse agrees with declared edges; declarations validator green; a rehearsal census shows no `NO_DETECTOR` on a core gate for any K-packet asset | Suvarṇa Track E + each packet owner |
| **L0-M muhūrta parihāra extraction** (an L0 packet this plan depends on, not a Kāla packet) | extract the Muhūrta Cintāmaṇi doṣa and parihāra rules into `bg_parihara_rules` with `scope = muhurta` and exact PG locators (algorithm document 3.17, §2) | corpus custodian's count; L0 owner | the election view's residual-doṣa ledger reads cited cancellations instead of "uncancelled" | L0 owner |
| **K9 rehearsal rebuild + benchmarks** | full-layer rebuild drill on the rehearsal DB; benchmark contract runs; invalidation drill (change L2 → only F1-downstream re-runs) | K1–K8 | Idem proof; measured costs; lineage drill passes | build operator |

Parallelism: K0 first; K1, K2, K7, K8 in parallel; K3 and K4 against fixtures as soon as K0–K2 land; K5 after K4; K6 after K4/K5; K9 last. Production data flows only after Pravāha's `'5.0'` flips and the campaign's W1 physical gate opens; none of K0–K9 waits for that to be *coded and proven on the rehearsal DB*.

---

## §10 · Tests and oracles (what "proven" means per packet)

Three tiers kept separate (skill §3): computational correctness · explanatory/discriminative value · empirical outcome performance. Only the first two are claimable from code; the third waits for prospective forecasts.

| Class | Oracles (examples; each with a mutation that must fail) |
|---|---|
| **Core correctness** | F2: boundary equality with pinned `chart_dashas`; covariance of two boundaries under a birth-time shift; applicability row for Aṣṭottarī absent on this chart. F1: fact removal vs attachment removal; signed cancellation retains polarity. Sky: O-AD-1…4 aspect direction, O-RX-1 occurrence ordinals (judge oracles, reused). |
| **Evidence algebra** | same `contact_id` through two roles → one increment; P8-selected window never G-J-corroborated; relocating a computation between stages → identical `D(W)`; alias and duplicate insertion → identical outputs. |
| **Negative space** | each of six states from a planted fixture; `information_unavailable` never served as "quiet"; obstruction release date present whenever `obstruction_active`. |
| **Agreement** | `W=[0,30), A=[0,1), B=[29,30)` has no joint segment; universally active witness contributes ≈ 0; zero null variance → explicit non-informative state; `(b+1)/(R+1)` tails. |
| **Forecaster** | K4 axis oracle (several registry events across epochs and time zones; a J2000/birth-relative mixing mutant fails); K5 reproducibility (identical inputs → identical digest; each dependency mutation changes it); byte-equality field ≡ compact evaluator on sampled instants and integrals. |
| **Projections** | SQL golden tests: output rows equal a hand-built expectation over a fixture generation; rebuild twice → zero net rows. |
| **Serving** | sentinel distinction present only in the negative-space table reaches `kala_now_get` and the web engine; density census per view; narration golden tests. |
| **Build** | rehearsal full-layer rebuild; lineage drill (L2 mutation re-runs exactly F1 → projections); resume after a killed substep loses one class. |
| **Value (discriminative)** | retrodiction protocol v2.1 on the test role, judge-only vs judge+jury vs with forecaster, four-way verdicts; reported to the native, never used to flip anything automatically (concept §5.9). |

---

## §11 · Risks

1. **Import direction into a frozen kernel.** If the steward refuses R-1, `kala_core` duplicates the kernel's pure modules for one generation, with a byte-equality test between the two; the design does not change.
2. **Scope of "new assets" under Suvarṇa.** If a shared-domain sky row is out of scope, the judge's own sky tables remain the substrate and the other stages read them (R-2 fallback); cost: the sky is rebuilt with the judge's chart generation rather than once per convention.
3. **Strangler columns on live tables.** Re-shaping `kala_activation_predicates`, `kala_convergence`, `kala_obstruction`, `kala_field` in place touches L4 cascades (`phala_anchors`) and L5 binds; every re-shape is additive first, consumers migrate, old columns retire — with the N-32 wave order and transitive-footprint statement per wave.
4. **B8-6 (Kṣetra's own knots).** The forecaster keeps its continuous kinematics for evaluation until a shared-geometry equivalence is demonstrated; two solvers coexist for one generation by ruling, not by accident.
5. **Insufficient n.** Most discriminative tests will read `insufficient_evidence` for a long time; the product must say so (concept §10). The code is designed so that reads as a typed state, not a failure.
6. **One build slot.** Stage-level parallelism is not available; efficiency comes from not recomputing, not from concurrency. If the orchestrator's single-slot law changes, the grains are already independent.
7. **Coordination debt.** F1 as the judge's natal-fact source, G-E3/G-E4, the N-32 storage addition, W6 withdrawal and corpus counts close elsewhere (concept §8.5); each is a dependency of a packet above and is listed in it.
8. **Live hazards the refactor must not carry across** (code trace): Saṅgam's destructive `plan_substeps`; the legacy `brahmagyan/kala` CLI writing `kala_convergence`/`kala_obstruction`; the two `SPECIAL_DRISHTI_DEG` tables disagreeing on the nodes; the two `orb_strength_score` formulas; the century writer writing both staging and production tables; ledger fingerprints that include `date.today()`. Each gets a regression oracle in K0 so it cannot reappear.
9. **Geometry model choice.** Two numerically different models coexist: the step scanners (`transit_search`, v1/v3) and the arc-index + Swiss-refined solver (kernel, w2g, Kṣetra S0). The plan makes the solver the stage model and keeps the scanner as an ad-hoc service. If a stage's rule path needs a quantity the solver does not expose (a λ-valued extremum over time), that is a kernel amendment, not a return to scanning.

---

## §12 · Decisions routed to other owners

| ID | Decision | Owner | Why it cannot be decided here |
|---|---|---|---|
| **R-1** | `kala_core` may import `gochara_kernel`'s pure modules (substrate, knots, episodes, rule_registry read side, input_vector, ledger read side, verifiers) without modifying them | Pravāha steward | the kernel is the judge's, under a frozen spec and an implementation lock |
| **R-2** | the sky-event substrate as a shared-domain registry row (new id, **not** matching the `ka_gochara*` family pattern unless Pravāha is to own it), or the judge's tables as the layer's substrate (no new id) | native (scope) + Strategic Suvarṇa (N-12; seed + registry) + Pravāha | "new assets" are outside Suvarṇa's scope and need native approval plus a seed entry; the judge owns the tables; the wave tool auto-classifies Gochara-patterned ids as family |
| **R-3** | the judge reads natal-fact rows from F1 (`ka_yojaka` re-shaped) instead of its own projection | Pravāha steward (amendment to the frozen contract's input side) | concept note coordination item G-E1 |
| **R-4** | views move from `platform-mcp/src/tools/kala_views/` into retrieval-registry composites; facades become aliases | Paripraśna / retrieval owner | a channel-architecture change, not a Kāla writer change |
| **R-5** | asset ids: keep `ka_sangam`, `ka_kshetra`, `ka_vighnakara`, `ka_yojaka`, `ka_avadhi` with re-shaped tables (strangler), vs new ids | Strategic Suvarṇa (denominator) + native | denominator and FAMILY_ASSETS freeze |
| **R-6** | `ka_tulana`: wire into PRIORITY or retire honestly | native | a product choice about the attention view |
| **R-7** | one owner per pipeline stage plus one for projections and one for serving (today nine assets have no owner) | Strategic Suvarṇa | ownership |
| **R-8** | the two contested adapters served as `method_contested` until the corpus custodian adjudicates | native + corpus custodian | doctrine, not code |
| **R-9** | century materializer formally superseded, data retained, with its retirement row | native (hold owner) + Strategic Suvarṇa | the standing hold |
| **R-10** | housekeeping taken as given, not discussed here: migration numbers are allocated by the campaign; the three re-shapes that touch L4/L5 tables proceed additively with a footprint statement; no cross-layer cascade is reintroduced | Strategic Suvarṇa | campaign procedure |

---

## §13 · Questions for the reviewer (Astra)

1. Is the layer-wide three-lineage invalidation (§6.2 item 3) sound given that the orchestrator's staleness propagation is edge-based, or does it need a manifest-aware predicate the frozen runner cannot provide?
2. Does making every reader a pure-SQL projection lose any distinction the reader currently computes that is *not* derivable from the three stages' assertion rows? (Candidates to check: Jivana Parva's quality labels; Kalasutra's recurrence ladder; Taranga's domain waveform.)
3. Is `D-LINEAGE` (input-vector equality as a certification addition) a core-gate overlap with Build/Ldgr or a genuine addition?
4. Is keeping the five overlays as separate adapter writers (rather than folding them into the judge's rule paths now) the right first move, given that two are contested and one is uncited?
5. Does the compact field's knot set (clock boundaries of non-zero-coefficient systems + contact in/out instants + mask edges) risk under-sampling any term W2's likelihood depends on? Which byte-equality sampling is sufficient?
6. Where should `ka_bhavishya_lekha`'s issued-forecast table live: re-shaped in L3, or in L5 beside Samīkṣā, with L3 holding only a registrar?
7. Which of the ten routed decisions (§12) can be taken on the reviewer's recommendation rather than by the named owner?
8. Is making the arc-index + Swiss-refined solver the single stage geometry (retiring step scanning from stages) safe for every quantity the frozen rule paths require (P1–P6 exist in code; P7–P9 are specified but not implemented), in particular interior extrema of λ-valued forms (spec §7.2 invariant 2)?
9. The DHARA null at 68 % of build time: is "one shift-null per generation over shared elementary segments" statistically equivalent to the per-class dense-row null W2 specified, or does it change the estimand?

---

## §14 · Sources

Three read-only sub-agent digests produced this session and cited [A]: the code-architecture and duplication trace (scope: `platform/python-sidecar/services/{gochara_*, ka_*, kala_*, w2g, taranga_kernel}`, `pipeline/orchestrator/writers/ka_*.py`, `pipeline/transit_search.py`, `brahmagyan/kala/*`, the frozen `writers/__init__.py` and `asset_runner.py`; costs from `L3_W1_ANALYSIS_INDEX_v1_0.md` and `BATCH_D`); the Suvarṇa certification digest (`SUVARNA_CAMPAIGN_PLAN_v1_5.md` §1–§2, §5.3–§5.5; `ASSET_ELEVATION_TEMPLATE_v2_0.md` §4, §6; `asset_census.py` `CRITERION_REGISTRY`; `nikasha_certify.py`; `asset_elevation_tracker.py` E6.3; `asset_declarations.json` 1.19.0 on `main` and 1.36.0 on `origin/suvarna/engine-100-stack-pr`; `suvarna_level_wave.py`; the live decisions log through N-154); and the producer→consumer trace already cited in the review. As KALA_LAYER_VALUE_REVIEW_v1_0 §12, plus: `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2 (the frozen `ContextSpec` / `WriterResult` / `SubStep` / `WriterBase` definitions); `briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md` §0, §6, §10 [eea2610d0]; `briefs/nirmana/l3_autonomous/gochara_wp0_7/A5_3_REGISTERED_WRITER_BRIEF_v1_0.md` pins 1–7, delivery sequence, standing constraints [cooperative-racer]; `briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_5.md` §1, §2 [bd944059b]; `00_ARCHITECTURE/control/LEVEL_MAP.json` (frozen 2026-10-03, registry revision 16) [cooperative-racer]; `platform/scripts/manifest/web_tool_bridge_builder.ts` and `platform/src/lib/pipeline/compiled_floor_adapter.ts` (resolution kinds; `resolveLiveTool`) [cooperative-racer]; module line counts from `wc -l` on `platform/python-sidecar/services/{gochara_kernel, ka_kshetra, ka_sangam, ka_temporal, kala_trigger, kala_permission, gochara_v3, w2g}` and `pipeline/orchestrator/writers/ka_*.py` [cooperative-racer @ c751f3bd8]; `KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md` §4–§5 and `SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4.md` §3 [cooperative-racer].
