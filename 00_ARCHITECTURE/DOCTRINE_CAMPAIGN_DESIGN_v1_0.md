---
artifact: DOCTRINE_CAMPAIGN_DESIGN_v1_0
canonical_id: DOCTRINE_CAMPAIGN_DESIGN
type: DESIGN SPEC (post-W4 doctrine campaign; the resolution map for POST_REMEDIATION_CONSUMPTION_REGISTER)
version: 1.0
status: DRAFT — native-approved design (Cowork 2026-07-13); pending spec-review loop + native read
supersedes_stubs: REMEDIATION_PLAN_v3_0 §"Doctrine campaign (post-W4): P-1..P-9, P-13"
source_session: Cowork 2026-07-13 — beyond-acharya consumption brainstorm (Fable 5 + Opus 4.8, native Abhisek).
  Anchors: POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md (CR-1..CR-89), two Explore code-reviews
  (combinatorial-sweep inventory; MSR/CGM/convergence deep review), chart 482012f1 wealth reading as
  the type specimen throughout.
governing_principles: CLAUDE.md §B (facts/interpretation separation), §N (build standards, +§N.6 new),
  §I B.3 (derivation ledger), B.10 (no fabricated computation), B.11 (whole-chart-read); MACRO_PLAN
  §Ethical Framework (probabilistic/calibrated/auditable), §IS (system-integrity substrate).
---

# The Doctrine Campaign — Demand-Driven, Beyond-Acharya Consumption

## §0 — Purpose and one-paragraph thesis

The instrument is a superb **fact store** and a failing **judgment engine**. L1 retrieval is fast, grounded, and correct; the L2+ surfaces that are supposed to *rank, time, and calibrate* run on inert priors, keyword heuristics, and a timing engine that has been severed from the chart's own judged structure. This campaign closes that gap along one spine:

```
question → scope tuple → compiled contract (vidhi) → two-pass retrieval over
build-time-JUDGED, density-disciplined surfaces → synthesis + completeness receipt →
prediction log → LEL retrodiction → calibration → sharper priors for the next contract
```

The differentiator is deliberate: **deterministic computation and single-chart statistics beyond human cognition** — the exhaustive combinatorial band and the temporal-convolution band that no acharya can hold in working memory. Population/multi-chart statistics are **explicitly out of scope** (native decision — we do not build a capability we cannot yet use).

## §1 — Scope

**In scope:** the five components (§3–§7), the three-asset elevation (§10–§12), the Three-Lock activation model (§13), the register resolution map (§9). All single-chart. Modular-monolith + registered-plugin + sidecar architecture (§2). Nothing modifies the FROZEN orchestrator contract.

**Out of scope (native-directed):** population/rarity/multi-chart statistics (the "class A" band of the §5 brainstorm — cross-chart rarity context; NOT a register Class number); KP sub-lord *engine* build (CR-75, deferred-explicit — but KP significator serving/wiring is in); microservices decomposition (modular monolith is the ceiling for this nascent stage); tantric-corpus content authoring (CR-52). Note: CR-87's "Abhinandan must score differently from Abhisek" is a **2-chart correctness regression guard**, not population statistics — in scope.

## §2 — Architecture stance: modular monolith + registered plugins + sidecar compute

The system already contains its own modularity doctrine — the FROZEN orchestrator + `@register('<asset_id>')` `WriterBase` plugin pattern (ORCHESTRATOR_CONVERGENCE_CLOSE §2). This campaign **generalizes that one proven pattern to five planes**, so every future addition is plug-and-play and no change is monolithic-breaking:

| Plane | Today | Plug-and-play form |
|---|---|---|
| **Detectors** (yoga/dosha/NBRY/dhana/raja…) | hardcoded in one writer | **Detector registry** — each family a registered module: declarative rule + citation + cancellation-check + test fixtures. Adding Lakṣmī Yoga = one module, zero core change |
| **Signal classes** | fixed set in MSR writer | **Signal-class registry** — varga-divergence, nakshatra-semantic, arudha, special-lagna each a plugin folding into MSR |
| **Vidhis** (evidence contracts) | none | **Data, not code** — primitives + floors as versioned registry rows; new question types = configuration |
| **Compute services** | PyJHora sidecar (precedent) | **Uniform sidecar contract** — stateless, versioned API, results written back as L1 facts w/ citation refs. Kāla Taraṅga is the 2nd instance |
| **Serving envelope** | per-tool ad hoc | **One shared envelope library** every tool imports (v3 universal) |

**Explicitly NOT microservices.** A modular monolith + sidecar compute services gives every plug-and-play property (registries, frozen interfaces, versioned schemas, independent testability) without a service-mesh operational tax. When scale later demands extraction, a registered module lifts into a service cleanly *because its interface was already frozen*. That is the adaptability guarantee.

**Fold-vs-build rule (governs every new capability):** *enumeration enriches in place; judgment lands as new registered assets; capabilities with a distinct lifecycle become sidecars.*

| New capability | Disposition |
|---|---|
| Valence pass, varga-ratification matrix, varga-consistency index | **New sibling L1 asset `ga_vichara`** ("judged structure") — consumes `ga_structural`, feeds MSR |
| Detector families (dhana/raja/NBRY-per-varga…) | **Registered modules inside the existing yoga writer** — asset unchanged, internals become plugins |
| New signal classes (varga-divergence, nakshatra-semantic, arudha, special-lagna) | **Fold into MSR** via the signal-class registry (MSR *is* the aggregation surface) |
| Kāla Taraṅga (temporal convolution) | **Sidecar service** + evidence write-through |
| Convergence elevation | **Extracted shared kernel** — the ka_sangam engine becomes a library used by BOTH the Taraṅga sidecar (live) and ka_* writers (materialized) |

## §3 — Component 1: the Vidhi Engine (demand-driven retrieval)

**Problem (register CR-27, CR-36):** the LLM plans from tool-familiarity, stale tool memory, and generic priors — supply-driven. It doesn't know what a complete answer requires, so it improvises (chain missed until native pointed; nakshatras omitted; special lagnas never touched despite being computed).

**The three-band contract.** "Sufficient input for an AI supercomputer beyond acharya grade" is not the acharya checklist — it has a band no human vidhi contains:

1. **Acharya floor** — the classical checklist per intent class. Non-skippable, versioned, auditable. Skipping any floor item forces a disclosure.
2. **Machine band** — what only computation supplies: full lord-pair matrix, varga-ratification across all vargas, dasha×transit convolution, statistical rarity *within the chart*, LEL-calibrated priors. **This band is the differentiator, defined inside the contract** so it is systematic, not opportunistic.
3. **Question-specific extension** — what *this* question uniquely needs beyond both (LLM-owned).

**Ownership split (settles the native's question):** the **server owns bands 1 + 2** — deterministic, versioned, auditable, and *model-independent* (Fable/Opus/Gemini must all get the same floor, or completeness varies by model and is never measurable). The **LLM owns band 3** and the classification of the question into a scope tuple. The server defines *sufficiency*; the LLM pursues *beyond-sufficiency*.

**Vidhi = grammar + compiler, NOT a fixed checklist** (native correction — a fixed vidhi cannot serve "show me my D1" and "unleash my financial potential" alike):

- **Primitives (~30 atoms):** fixed, versioned definitions (`bhava_condition`, `varga_ratification`, `special_lagna_read`, `chara_karaka_read`, `dasha_spine`, `taranga_curve`, `mechanism_read`, `statistical_context`, `lel_retrodiction`, `intervention_synthesis`…). Each maps to a live tool + args + fallback face + **`known_gap` annotation sourced from the CR register** (the register becomes machine-readable planner input).
- **Compiler:** `question → scope_tuple(intent, domains, width, depth, horizon, intervention?, entitlement) → contract = floor(intent) + machine_band(depth) + LLM_extensions`. Deterministic given the tuple → identical questions yield identical contracts (reproducibility survives dynamism). The four canonical examples compile to visibly different contracts (retrieval-only / structure-read / panoramic-breadth / deep-dive+intervention).
- **Delivery:** vidhi registry as an **MCP resource**; compiled plans as an **MCP prompt** (primary) + `plan_retrieval` meta-tool (fallback for clients without prompt support). One registry, two faces.
- **The scope tuple is shown to the native for correction before execution** ("the plan on the screen").
- **The acharya-floor content is itself a D-2 deliverable** (data in the vidhi registry, one floor per intent class), not prose in this spec — but it must be *enumerated* to be buildable. Worked example, `floor(wealth_deepdive)`: `bhava_condition(2)` · `bhavesha_condition(2)` · `karaka_condition(Jupiter)` · `from_moon_view` · `varga_ratification(D2,D9,D11)` · `special_lagna_read(Indu,Sree)` · `chara_karaka_read(AmK)` · `dhana_yoga_scan` · `nbry_scan(per-varga)` · `wealth_loss_mechanism_scan` · `dasha_spine + lord_capability` · `taranga_curve(wealth)` · `lel_retrodiction(wealth)` · `intervention_synthesis(leverage_ranked)`. Each atom is a §3 primitive with a live-tool mapping + `known_gap`. The registry ships every intent class's floor as versioned rows; the master test (§8) is the acceptance gate on floor *sufficiency*.
- **Completeness receipt:** every synthesis ends with the scored checklist (`served / empty / dark`) against the compiled floor; each `dark` item cites its CR-row. This makes Gate-1 question-sufficiency measurable per reading AND turns every dark line into a standing demand-vote for remediation priority.
- **Staleness kill:** every response already carries build_id; add `capability_version` + emit MCP `tools/list_changed` on deploy; the served consumption protocol instructs re-fetch when cached understanding predates the version.

## §4 — Component 2: the judgment substrate (build-time; the B-deltas)

**Verified reality (Explore inventory):** the enumeration exists (28 karaka-pairs × 30 vargas, full aspect/lord/house matrices × 30 vargas, dispositor chains, graph metrics, ashtakavarga, parivartana, kala-sarpa per varga). The *judgment on top of it* does not. Four deltas, all build-time (per §8's build/runtime split):

1. **Valence pass** — every sweep row gains polarity from **actor's functional lordship × target's class** (corrected CR-54: the 4-way `link_type` already exists on `bhava_significance_link` but grades the *target house's class*, never the *acting lord's functional nature* — an 8L-Mars→2H aspect reads "neutral" because H2 is neither kendra/trikona/dusthana). Karaka-web gains strength/orb; `effective_dignity` fixed to the file's own Parāśari aspect model + functional status (today it uses a foreign 15° longitude orb, D1-only).
2. **Cross-varga joins** — the single biggest absence (every builder treats each varga in isolation): the **varga-ratification matrix** (D1 promise vs D2/D9/D11 delivery per bhāveśa/kāraka — CR-57), a continuous **varga-consistency index** over the 9×30 graha-varga matrix (vargottama generalized to a score), multi-varga-weighted convergence. **Per-varga NBRY** (CR-59) lands here as a detector-registry module.
3. **Graph completion** — finish CGM's own specced centrality (eigenvector/betweenness/harmonic currently silently 0), consequence semantics on edges (LCA-9a), chain/circuit-signal class (G-6/CR-24).
4. **Materialized per-domain ranked views** at build; runtime = lookup + question-scoped projection + light re-rank, `as_of`-stamped.

Detector families (dhana / raja / Budha-Āditya / Sarasvatī / Lakṣmī / Vipareeta — CR-56) ship as registry modules with mandatory cancellation-checks (fixes the CR-72/73 "no negative-condition check" class at the doctrine level).

## §5 — Component 3: Kāla Taraṅga — temporal convolution as a stateless service

**Value produced** (converts "which period" → "how much, when exactly, rising/fading, helped/opposed by what"): graded event windows; **interference semantics** (why promised periods don't deliver — destructive interference, impossible in today's additive model); momentum (curve derivative → act-now vs wait); **mechanism-specific danger windows** (the 8L-Mars→2H curve — validated against the May-2025 fraud); LEL-retrodiction calibration fuel; window ranking by area not height; cross-domain simultaneity; slow-transit texture (triple-crossing sade-sati as three peaks); dasha-sandhi troughs; the instantaneous "now" vector.

**Shape — stateless on-demand service** (native reframe, correct: nothing stored means nothing stale):

- **API:** `activation(chart, domain|mechanism, t)` and `curve(chart, domain|mechanism, [t₁,t₂], resolution)`. Any point, any range, computed live, always valid.
- **Split:** chart-static substrate at build (natal sensitivity map w/ valence + weights from §4, dasha tree already to level-4, graha capability); time-varying kernel on demand (ephemeris-cached transits — `ephemeris_cache_year` exists; cos² orb, applying ×1.0 / separating ×0.7; superposition). Cost: a point eval is sub-ms after ephemeris lookup; a 5-yr daily curve ~1,800 evals < 1s; full 120-yr life-arc ~44k evals in seconds worst-case. **CR-41's forward-horizon defect dissolves by construction** — there is no writer horizon.
- **Staged kernel (native-approved):** v1 = dasha-capability step-functions + slow-planet transit pulses + SAV potency (3 sources). Each further current admitted **only on demonstrated LEL-retrodiction improvement** — the kernel grows on evidence, not doctrine; each current's weight is earned against this chart's lived history.
- **Acceptance gates (falsifiable, with numeric thresholds):**
  - *Peak-proximity:* the 8L-Mars→2H mechanism curve must show a local maximum within **±45 days** of the May-2025 `loss/financial_deception` event, at an intensity in the **top decile** of that mechanism's own 5-year curve.
  - *Windfall:* the wealth-domain curve must show a peak within **±45 days** of the 2010-07 `finance/family_windfall` event, top-decile.
  - *Blind battery:* across all scorable LEL events (see count note below), **≥50% hit-rate** at the ±45-day / top-tercile threshold, with the hit-rate **statistically above** the shuffled-birth negative control (the §7 control, once implemented). Lead/lag distribution reported (not gated in v1).
  These thresholds are v1 gates and are themselves subject to revision as the staged kernel matures.
- **LEL event-count note (reconciles the numbers used across this doc):** 482012f1's LEL holds **57 total events**; PH-4-3's leakage firewall uses **36 as the pre-2020 training split** (post-2020 + enrichment held out); the §7 backfill flips `n_observations` from 0 to **~40 scorable outcome records per chart** (events with a resolvable mechanism). Same corpus, three different filtered counts.
- **Evidence-grade write-through (B.3):** results cited in a reading or consumed by L5 persist with `formula_version + inputs + as_of`; everything else evaporates. Retrodiction backfill is a one-time job, not a store.

## §6 — Component 4: channel elevation (density + two-pass + support)

**§N.6 Serving Density Principle (new ground standard — ratified into CLAUDE.md §N + ONGOING_HYGIENE):** binding on every current and future asset/service — *(i)* family-collapse + dedup **at the writer**; *(ii)* projection facets honored **or rejected loudly** (kills the CR-42 silent-wrong-answer class forever); *(iii)* layered envelope (verdict ≤1KB → digest ≤4KB → paginated rows) as the only response shape; *(iv)* a per-tool **density contract** in the capability map enforced by the census harness in CI. A new asset that violates density fails its gate — exactly as a writer that commits its own transaction fails the orchestrator contract today.

**Two-pass retrieval (dissolves the 12KB-starves / 900KB-drowns dilemma):** Pass-1 SCAN = ultra-dense subject-bearing index lines (~60 bytes/row, hundreds of rows in ~8KB — requires the CR-45 subject-in-headline fix as enabler); Pass-2 FETCH by the IDs the LLM selects *for this question*. Width lives in Pass-1, depth in Pass-2; neither breaches budget. The LLM is the best relevance classifier — but only if Pass-1 carries enough metadata per row to choose.

**Support surface (MCP as senior colleague, not filing cabinet):** capability map + vidhis + **per-chart reading-notes (CR-38/71/80) as MCP resources** (kills "the LLM forgot what we learned about this chart"); errors that teach (return the corrected call — CR-7 class); description-vs-payload contract audit in CI (CR-44 class); question-aware drill_pointers ("Venus debilitated in D9 → check NBRY grounds: call X"). Consider deprecating the twin-alias supply surface from the LLM-visible list (129 read tools → ~30 canonical faces the vidhis reference; CR-30/51).

## §7 — Component 5: calibration ignition (L5 finally fed)

**Diagnosis (CR-79, CR-47, CR-68):** the machinery is well-designed and **has never been fed** — all multipliers `prior_only`, `n_observations: 0`, kill-switches active; 141 QA checks nearly all scoring 0.5; gain and loss both "denied 1.7/10" on identical evidence. Three blockages, in causal order:

1. **Over-firewalled LEL.** The no-leakage rule (correct for prediction *generation*) is implemented as total quarantine. Re-scope: firewall sits between LEL→prediction-inputs, **not** LEL→outcome-scoring.
2. **Nothing pumps the outcome loop.** `mimamsa_outcome_record` has never been called. **Retrodiction backfill:** score all 57 LEL events against their Kāla-Taraṅga mechanism curves; batch-write outcome records under PH-4-3's existing train/test leakage discipline. One run flips `n_observations` 0→~40/chart and lets promotion gates evaluate.
3. **Degenerate matcher + verdict function.** Fix the shared LEL↔candidate matcher once (CR-47's root, reused by rectification + calibration); make evidence sets **event-class-specific** (gain ≠ loss — kills CR-79's degeneracy); implement the `not_implemented` negative controls (shuffled-birth, antiphase) so calibration claims are falsifiable.

**Forced dependency:** calibration learns *weights over evidence*. If the evidence layer serves 95.7% noise (CR-65) and can't see dhana yogas (CR-56), calibration learns the weights of noise. So the sequence is: judgment layer (§4) → mechanism-retrodiction surface → backfill → open gates → live loop (every reading logs falsifier-bearing predictions per its vidhi; every LEL append triggers outcome matching; multipliers update; the *next* contract retrieves with calibrated priors).

## §8 — Phasing, dependencies, master acceptance test

Build-time / runtime split (native point 3, confirmed correct — the broken half of ranking is the *build* half): **push everything question-independent to build** (valence, yoga/NBRY detection, varga-ratification matrix, leverage index, dasha-lord capability, family-collapse, per-domain materialized views); **nightly batch** for slowly-drifting temporal refresh; **serve time = lookup + question-scoped projection + light re-rank only**. Runtime gets faster *and* deterministic (essential for calibration reproducibility); `as_of` stamps disclose vintage.

| Phase | Delivers | Depends on |
|---|---|---|
| **D-1** | Judgment substrate §4 (`ga_vichara` + detector registry + valence + varga-ratification matrix + **leverage_index**) + §N.6 density ratified + MSR elevation §11 | — |
| **D-2** | Vidhi Engine §3 + two-pass shape §6 + CGM elevation + **Mechanism object** §12 (retires the CR-78 discovery engine) | D-1 (contracts reference judged surfaces; CGM/mechanism needs valence) |
| **D-3** | Kāla Taraṅga v1 §5 + Three-Lock convergence §13 + retrodiction gates | **D-1** (sensitivity map needs valence/weights) **+ D-2** (mechanism-keyed curves + PROMISE-lock "mechanism graph-weight" require the §12 Mechanism object); INFRA-PREREQ CR-40/CR-8 (sidecar) |
| **D-4** | Calibration ignition §7 + kernel staging loop | D-3 |

`leverage_index` (D-1 deliverable, absorbs CR-69) is defined as **`domain_load_bearing_weight ÷ capability(shadbala_percentile, dignity, varga_ratification)`, forward-weighted by dasha runway** — the number remedy and intervention-timing rank on (a graha that is load-bearing, weak, and about to run a long MD is the highest-leverage target, and the window is the years *before* its dasha opens).

**Master acceptance test (regression suite, per release):** a fresh LLM, given only served surfaces + the compiled vidhi, must reach the **six load-bearing wealth conclusions enumerated in `POST_REMEDIATION_CONSUMPTION_REGISTER §G.0` on chart 482012f1 without hand-derivation** — plus census battery green + the two named retrodictions (§5) passing. *Operationalizing "without hand-derivation":* each of the six conclusions must be traceable to a **served signal/verdict whose `computed_salience` places it in the top-15 of its domain surface** (i.e. the engine *surfaced* it, the LLM did not reconstruct it from raw longitudes) — the harness asserts presence-in-top-K per conclusion, pass/fail per conclusion, 6/6 required. That single test *operationalizes* "beyond-acharya input" — it is the executable definition.

## §9 — Register absorption map (POST_REMEDIATION_CONSUMPTION_REGISTER, CR-1..CR-89)

**Rule:** every CR row receives exactly one disposition — `ABSORBED(phase)` / `AMENDED` / `INFRA-PREREQ` / `DEFERRED-EXPLICIT` / `BASELINE`. No row remains undispositioned. **This §9 table is the authoritative disposition map for CR-1..CR-89**; the register (v1.4) carries inline disposition annotations on its newest rows (§I, CR-81..89) and points to this table for the rest via its §I disposition-index footer. The register stays the living intake, this doc is its resolution map; the two are kept in sync at every edit. (A future register pass may back-fill a per-row `disposition` column from this table; until then, this table governs.)

| Disposition | Rows | Rationale |
|---|---|---|
| **ABSORBED → D-1** (judgment substrate, MSR, density) | CR-54*(amended)*, CR-55, CR-56, CR-57, CR-59, CR-22/34/35, CR-65, CR-24, CR-25, CR-26/64, CR-61, CR-58, CR-60, CR-69, CR-72, CR-73, CR-74, CR-33/43, CR-76*(amended)*, CR-77*(amended)*, CR-17, CR-18, CR-10/42, CR-11, CR-13/49, CR-45, CR-46, CR-50, CR-81, CR-82, CR-83, CR-86 | Fixed *by construction* of the valence pass, cross-varga joins, detector/signal-class registries, §N.6 density — not one-off patches |
| **ABSORBED → D-2** (vidhi + channel + CGM + mechanism/discovery) | CR-9, CR-14/39, CR-15, CR-16, CR-27, CR-28*(ratified as scope-tuple classifier)*, CR-30/51, CR-36, CR-44, CR-62, CR-78, CR-84, CR-85 | Capability map gets a live source; twin-aliases → one declared face; descriptions become CI-audited contracts; CGM dead-links closed; **CR-78 — the degenerate `bo_anveshana` discovery engine is replaced by the first-class Mechanism object (§12): genuine cross-subsystem synthesis is what the mechanism graph *is*, so the univariate-z-score engine is retired, not tuned** |
| **ABSORBED → D-3** (Kāla Taraṅga + Three-Lock) | CR-1, CR-2, CR-3, CR-4/29, CR-5, CR-6, CR-12, CR-19/66, CR-37, CR-41*(dissolved by construction)*, CR-48, CR-63, CR-87, CR-88, CR-89 | The temporal-blackout cluster is **superseded, not patched** — broken L3 join/writer fixes abandoned in favor of the service + Three-Lock kernel. CR-2 (`varga_confirmation.rows` hollow) is populated by the §4 varga-ratification matrix feeding the Three-Lock PROMISE lock; CR-3 (`bearing_yogas` regression) by the D-1 detector family surfaced through the elevated timing_hooks |
| **ABSORBED → D-4** (calibration) | CR-20/67, CR-47, CR-68, CR-79 | Backfill, matcher, event-class evidence, remedy-leverage join |
| **INFRA-PREREQ** | CR-8 + CR-40*(sidecar auth/keys — hard prereq for D-3 transit kernel)*, CR-7*(retest first per CR-53)* | Gate conditions on the phase that needs them |
| **DEFERRED-EXPLICIT** (native decision) | CR-75*(KP engine — separate build)*, CR-21*(vedha completion)*, CR-52*(tantric content)*, CR-23*(NB doctrine ruling — governance gate in D-1, needs native ruling not code)* | Deferral is a disposition, not an omission |
| **BASELINE / carried** | CR-31, CR-32, CR-38, CR-53, CR-70, CR-71, CR-80 | Verified-positives → regression baseline; reading-notes (CR-32/38/71/80 — chart knowledge for 1c826d5a + 482012f1) → per-chart MCP resources (operationalized, not archived) |

*Completeness proof: the buckets above name all of CR-1..CR-89 exactly once. Verified by enumeration in the spec-review loop (2026-07-13) — CR-32 and CR-78 were caught missing in the first pass and placed here (BASELINE and D-2 respectively).*

## §10 — Asset elevation: `ga_structural`

**Scope today:** ~6,372 lines, ~30 fact families × 30 vargas — vast enumeration, zero judgment, one internal inconsistency (`effective_dignity` uses a 15° longitude orb foreign to the file's own Parāśari model, D1-only, fixed benefic/malefic sets ignoring functional status computed elsewhere in the same file).

**Elevate:** (a) split internally into **registered sub-builders** (one per family) behind the unchanged asset contract — modularity, no DAG change; (b) keep it **enumeration-pure** — all new judgment goes to `ga_vichara`; (c) fix the `effective_dignity` inconsistency; (d) CR-50 default-ordering (lead with the nine grahas + lagna, upagrahas behind a facet) + §N.6 density. Scope is right; shape and downstream consumption need work.

## §11 — Asset elevation: MSR (`bo_laksana` → `bodha_msr_signals`)

**Why it under-delivers (five located mechanics, not vague tuning):**

1. **The class-prior term is dead** — `class_prior=1.0` passed as a literal; `brahma_class_priors` is *never queried* (`bo_laksana.py:1305`). The first factor of the ranking formula is inert.
2. **The 95.7%-supporting mush has a mechanical cause** — a blanket **tier ceiling** force-caps any `*_per_varga` or non-D1 fact at `supporting` (`:556-569`). The varga layer — where the chart's whole story lives — is *structurally forbidden* from ranking high.
3. **Valence is a keyword-substring heuristic** (`:269-282`), not judgment (CR-54's true root).
4. **Ingested-then-starved, NOT dropped (corrects CR-76/77 fix-direction):** special-lagna / chara-karaka / arudha / KP / tajaka facts *are* all ingested — but position-class facts carry no graha/house resolution, so they get default shadbala (1.0), default dignity (0.5), default bindus, hit the varga ceiling, and sink to `background`. Fix = **subject resolution + un-capping**, not ingestion.
5. **Subject-anonymous headlines by design** (`_build_headline_text` excludes `fact_subject`, `:510-519`) — CR-45 one-line-class fix.

**Elevate:** activate class-priors as data; valence from the §4 functional-lordship pass; **tiers from percentile distribution** (chart_defining ≈ top 1–2%) with the varga ceiling replaced by **ratification-aware weighting**; subject-bearing headlines; graha/house resolution for position-class facts; CGM metrics feeding the `structural_role` term (§12). MSR then becomes the single judged, ranked corpus every surface trusts.

**`ratification-aware weighting` (defined):** replace the flat "cap any non-D1 fact at `supporting`" rule with a multiplier `ratification_factor ∈ [0.6, 1.4]` applied to a per-varga fact's salience, `= 1.0 + 0.2 × (agreeing_operative_vargas − opposing_operative_vargas)` over the domain's operative varga set (e.g. wealth = {D1,D2,D9,D11}), clamped. A 2nd-lord dignity that holds across D1+D2+D9+D11 is *amplified* (approaches 1.4 and may reach `major`/`chart_defining`); one that flips sign between vargas is *damped* toward 0.6 and additionally emits a **`varga_ratification_divergence` signal** (CR-57) — the divergence itself becomes rankable evidence, which is exactly the promise/ripening gap the reading needs. Constants (0.2 step, [0.6,1.4] clamp, operative-varga sets) are registry data, not literals.

## §12 — Asset elevation: CGM + the Mechanism object

**Under-leveraged, precisely:** (1) no arudha / special-lagna nodes; (2) edge strengths mostly **hardcoded literals** — `weight_formula_version:"edge_weight_v1.0"` is a label with no formula behind it; (3) temporal hooks partial (dasha activation on 4 edge types only, Vimśottarī-only; a declared `sade_sati` edge type has **no builder** — dead); (4) **dead links both directions** — CGM never feeds MSR (bo_laksana runs first, reads no graph table), and `ka_yojaka`'s `cgm_centrality_weight` stamp is **never read by the convergence engine**; (5) only pagerank computed.

**Elevate — promote MECHANISM to a first-class object (the unifying idea of the campaign):** a mechanism = a named, valenced CGM subgraph (the 8L-Mars→2H wealth-loss circuit; the Saturn→Venus→Jupiter cash cascade; the 10→8→12→10 circuit of CR-24). Then one object threads all five layers:

```
CGM defines mechanisms → MSR ranks them (structural_role from real graph metrics)
→ Kāla Taraṅga computes each mechanism's activation curve → LEL retrodiction scores it
→ L5 calibrates it
```

Plus: real edge-strength formula from the valence pass; arudha / special-lagna nodes; chain/circuit motifs; completed centralities (eigenvector/betweenness/harmonic); and **close the two dead links** (CGM→MSR structural_role; centrality→convergence engine).

## §13 — Convergence elevation: the Three-Lock Activation Model

**Current model, precisely:** `score = Π(dignity, orb, vedha) × [1 − Π(1 − wᵢsᵢ)]` over 12 additive currents. Three confirmed limitations + one critical bug:

- **The promise side is severed** — the *only* structural input is `dignity_score` (defaulting to 0.5 when NULL). **Salience, valence, varga-ratification, signature-tier, dasha-lord shadbala — all ignored.** The two richest MSR outputs never reach timing. Convergence times *the sky* almost independently of the chart's judged structure.
- **No suppression model** — all 12 currents are positive, the sum monotone-increasing; only vedha (×0.3) damps, on the gate side. **Destructive interference is mathematically impossible** — "strong dasha, adverse sky, nothing happened" cannot be modeled.
- **Inert / stub currents** — `school_consensus` always scores 0.0 (`school_consensus_by_domain` left empty); ~90% of predicates are non-functional template stubs.
- **CRITICAL BUG (→ register CR-87):** this chart's natal constants are **hardcoded into shared engine code** — janma-nakshatra index 24 (Purva Bhadrapada), sade-sati signs (Cap/Aqu/Pis for Aquarius Moon), Bhubaneswar lat/long for panchanga (`engine.py:253, :1146-1149`; `ka_sangam.py:35-39`). **Tara-bala, sade-sati, and panchanga currents are computed against 482012f1 for every chart** — Abhinandan's activation scores are silently wrong today.

**The Three-Lock model** (classical delivery doctrine, finally computed) — each lock a **signed** superposition, run through the shared kernel that Taraṅga serves live and ka_sangam materializes at build:

```
Activation(t) = PROMISE × PERMISSION(t) × TRIGGER(t)
```

- **PROMISE (structural lock):** salience × functional valence × **varga-ratification** × **NBRY-deferral semantics** (a cancelled debility does not weaken the promise — it *re-times* it into the canceller's periods: the Venus-via-Mercury story, computable) × mechanism graph-weight.
- **PERMISSION (dasha lock):** Vimśottarī spine + **multi-system concordance elevated from a 0.12 counter to a real gate multiplier** (7 systems already computed, barely used) + **period-lord relational algebra** (AD-lord's kendra/trikoṇa/dusthāna + tāra relation *from the MD-lord* — the classical delivery rule, absent today) + **dasha-lord capability** (CR-60).
- **TRIGGER (transit lock):** the 12 currents + **signed suppressive currents** (malefic transits over the mechanism, papa-kartari of the window — *enables destructive interference*) + the **Guru-Śani double-transit rule** (Jupiter AND Saturn jointly aspecting the bhāva/lord — the famous accuracy technique; grep confirms it exists nowhere) + **saham currents** (sahams already computed as facts, zero currents today — the Dhana-saham for wealth timing sits unused) + **de-hardcoded per-chart constants**.

Staged-admission (native-approved) governs every new current: it stays only if LEL retrodiction improves. School-consensus and the stub predicates are repaired or retired under the same test.

## §14 — Register updates carried by this design (landed in register v1.4 §I)

The following rows and amendments were authored by this design and are **already committed to the register at v1.4 §I / §I.1** (this section is the design-side index of them):

- **CR-81** — MSR class-prior term inert (`class_prior=1.0` literal; `brahma_class_priors` never queried). Class 5, HIGH.
- **CR-82** — MSR tier-ceiling force-caps all varga/non-D1 facts at `supporting` → mechanical root of the 95.7%-supporting mush (CR-65). Class 7, HIGH.
- **CR-83** — MSR valence is keyword-substring heuristic, not functional-lordship judgment (deepens CR-54). Class 2, HIGH.
- **CR-84** — CGM→MSR link absent (bo_laksana reads no graph table); graph influence on ranking is zero by wiring. Class 8, HIGH.
- **CR-85** — CGM `cgm_centrality_weight` stamped onto predicates but never read by the convergence engine (dead passenger field). Class 8, MED-HIGH.
- **CR-86** — CGM edge strengths are hardcoded literals; `weight_formula_version` is a label with no formula; `sade_sati` edge type declared but has no builder. Class 5, MED-HIGH.
- **CR-87** — **CRITICAL:** one native's natal constants (janma-nakshatra, sade-sati signs, birth location) hardcoded into shared convergence-engine code → tara/sade-sati/panchanga currents wrong for every non-482012f1 chart. Class 1+4, **CRIT**.
- **CR-88** — Convergence promise-side severance: salience/valence/varga-ratification/signature-tier/dasha-lord-shadbala all ignored; only dignity_score (0.5-defaulted) feeds timing. Class 7, **CRIT**.
- **CR-89** — Convergence has no suppression model (additive-saturating; destructive interference impossible) + missing double-transit / saham / period-lord-relational currents + inert school_consensus + ~90% stub predicates. Class 7, HIGH.
- **Amendments:** CR-54 fix-direction → "valence from actor's functional lordship, not link vocabulary (4-way link_type already exists)"; CR-76/77 → "ingested-then-starved (subject-resolution + un-capping), not dropped"; CR-41 → "superseded by Kāla Taraṅga service, not patched."

---

*Changelog: v1.0 (2026-07-13) — initial design from the Cowork beyond-acharya consumption brainstorm; §0–§14; native-approved section-by-section; supersedes the deferred P-1..P-13 doctrine-campaign stub in REMEDIATION_PLAN_v3_0. Pending spec-review loop + native read before writing-plans.*
