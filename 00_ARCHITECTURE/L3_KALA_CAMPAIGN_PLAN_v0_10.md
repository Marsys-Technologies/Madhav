---
artifact: L3_KALA_CAMPAIGN_PLAN_v0_10.md
canonical_id: L3_KALA_CAMPAIGN_PLAN
version: 0.10
status: DRAFT (holistic opening COMPLETE + asset set LOCKED with names; v0.x = pre-ratification draft series)
authored_by: Cowork 2026-06-20 (reconstructed 2026-06-21 after a file-persistence desync — see §15)
native: Abhisek Mohanty (chart_id 482012f1-710e-4a25-994a-93821f5871aa)
purpose: >
  The governing campaign plan for L3 Kāla (the TEMPORAL layer). Authored draft-first and in DETAIL
  so that facts, discussions, decisions, and nuances are RETAINED rather than lost to "fill in later"
  (native documentation-first directive). Captures the HOLISTIC OPENING (vision, convergence
  machinery, traversal infrastructure, data-vs-service boundary, supreme-product elevation, the
  activation-predicate bridge, the rigor stratum) AND the asset reconciliation (the locked ka_* set).
  Enhanced in place through v0.x until ratified to v1.0, then it spawns per-asset briefs.
read_in_order:
  - 00_ARCHITECTURE/L3_KALA_CAMPAIGN_HANDOFF_v1_0.md
  - 00_ARCHITECTURE/L3_KALA_TEMPORAL_ARCHITECTURE_v1_0.md
  - 00_ARCHITECTURE/L2_BODHA_CLOSE_v1_0.md §8
  - 00_ARCHITECTURE/LEL_TOGGLE_GOVERNING_PRINCIPLE_v1_0.md
  - CLAUDE.md §C + CURRENT_STATE + git
governing_approach:
  ratified_by_native: 2026-06-20
  steps:
    - "0. Ground-truth audit (DONE — §3)"
    - "1. Holistic opening — settle vision BEFORE touching assets (DONE — §1–§13)"
    - "2. Settle the asset set (DONE — §14, §14.5)"
    - "3. Per-asset deep review — maximal value per asset (NEXT)"
    - "4. Holistic closing review"
    - "5. Retrieval tools review"
    - "6. Clean seal + cleanup"
  documentation_discipline: >
    Document in DETAIL from the very beginning. Every decision carries its WHY; every open question is
    tracked, not dropped. (Native directive 2026-06-20.)
---

# L3 Kāla — Campaign Plan (DRAFT v0.10)

> **Status note.** DRAFT, intentionally verbose. Sections marked [VERIFIED] are code-grounded;
> [OPEN] are unresolved; [RESOLVED] carry a date + the ratifying decision. Nothing is final until
> `status` flips to RATIFIED at v1.0.

---

## §0 — How to read this document
Documentation-first: the vision is written in full BEFORE any asset is built, so reasoning,
alternatives, and small nuances survive into the build. The corpus's expensive failures are *small
correct facts nobody wrote down*. This is the retention surface. Every enhancement appends to the
changelog (§12) with WHAT changed and WHY; the discussion record (§11) is the running log.

---

## §1 — The mission
**Kāla = time.** L2 Bodha (SEALED 2026-06-20) holds what is *structurally* true about the chart —
timeless, no date. **L3 Kāla is the temporal layer: it activates L2's structural promise across time
and answers WHEN.** Canonical query: *"When does my Lakshmi yoga next fire, auspiciously?"*

**L3 also performs TEMPORAL DISCOVERY — the layer's deepest purpose (native framing).** L3
superimposes L2's structural plane on the temporal plane to identify a specific combination — of
planets, conjunctions, houses, nakshatras, dashas, and other factors — that marks the **surgical
moment to activate or deactivate an intervention** (astrological/remedial AND material). This is the
**opportunity the cosmos grants**: the window when an activity is *fruitful* because the temporal
alignment meets the structural promise. **L3 enables discovery of that intersection of the temporal
and structural planes** — the where-and-when at which acting (or refraining) bears fruit. Not
"auspicious time in general" — auspicious *for this native, for this intervention, because this
promise meets this trigger here*.

---

## §2 — The founding architectural principle (LOCKED)
**Timing is SERVICES, not DATA.** A future transit position is continuous + infinite — you cannot
pre-store the chart state at every instant. Therefore: natal/structural facts → STORED (finite,
L0/L1/L2); transit positions → COMPUTED ON DEMAND (a service); "when does condition X hold" → a
SEARCH service over the ephemeris (the hard, valuable part).

**The promise-and-manifestation principle (native framing).** The birth chart gives the **promise** —
what is destined to be possible; the promise alone carries no date. It is the **interplay of the
structural and temporal planes** that determines WHEN the promise finds its opportune time to
manifest. **L3 enables identification of that opportune window — where the right time and the right
structural alignment COINCIDE.** In one line: *L0/L1/L2 hold the promise; L3 finds when the promise
meets its hour.*

> Nuance: "services not data" has a structural consequence the pipeline wasn't built for (the
> service-asset model, §5.3). Principle locked; its DAG/cockpit implementation was the open question.

---

## §3 — VERIFIED GROUND TRUTH (the engine audit, 2026-06-20) [VERIFIED]
The handoff claims *"L3 is mostly WIRING — the engines exist."* **The audit found this materially false.**

| Engine | Handoff | Verified reality |
|---|---|---|
| `pipeline/transit_search` (find_aspect_events / find_conjunction_events — the confluence heart) | "EXISTS" | **Does not exist on ANY branch.** Only `routers/transit_search.py` exists and IMPORTS the missing module → crashes on import. A `PHASE_4D_TRANSIT_SEARCH_BRIEF` = planned, never built. **From-scratch build.** |
| `compute_transits` (`pyjhora_adapter/transits.py`) | "EXISTS" | **Stub: `return {}`.** |
| `scripts/temporal/compute_transits.py` | (unmentioned) | **REAL** pyswisseph impl. Stranded; not wired to the adapter. Dual-authority cleanup target. |
| Muhurat Finder (`muhurat/finder.py`) | "EXISTS" | **REAL** — score_muhurat/find_muhurat; tithi/nakshatra/vara/yoga; knockout; classically grounded. |
| panchang engine | "EXISTS" | Real; spread across 3 panchanga branches — needs consolidation. |
| `ga_dashas` (~536k dated rows) | "EXISTS" | **REAL** — registered writer. The dasha timeline. |

**Verdict:** L3 is **BUILD + WIRE**, not wire-only. The hardest, most valuable component — the
transit-search/confluence engine — has never been built.

### §3.1 — THE M3 TEMPORAL SUITE (a stranded prior generation) [VERIFIED]
Deeper audit (prompted by the native's "I don't see much reference to the Dasha system") found an
entire prior-generation engine under `platform/scripts/temporal/` that NEITHER governing doc mentions:
`compute_transits.py` (`get_transit_states`: sidereal positions + Sade Sati + eclipse + nakshatra —
the real impl the adapter should wrap, resolves Q6); `compute_vimshottari/yogini/chara/narayana/kp`
(**5 dasha systems**); `run_dasha_pipeline.py`; and **`signal_activator.py` — a V1 OF THE ACTIVATION
BRIDGE** (joins active Vimśottarī MD+AD × transit state × signal `entities_involved` → lit/ripening/
dormant; flat 0.6 conf; reads markdown MSR not DB; Vimśottarī-only; not orchestrator-wired).
**Reframes the campaign: L3 = MODERNIZE + INTEGRATE + EXTEND**, not build-from-scratch nor wire-only.
The native's instinct that "Dasha is under-represented" caught a real, large omission.

---

## §4 — The two planes + the coupling question [OPEN — investigation I-1]
"When does my Lakshmi yoga fire?" lives on TWO planes: STRUCTURAL (timeless — L2/L1, BUILT) and
TEMPORAL (time — L3 + services). The full answer needs both.

> **Correction (native challenge):** v0.1 called these "perpendicular axes" — an unsupported geometric
> (orthogonal=independent) claim. Honest statement: **two planes; whether orthogonal or coupled is an
> OPEN empirical question.** Already evidence of coupling: **the Vimśottarī Daśā is DERIVED FROM the
> natal Moon's nakshatra** — the temporal axis is partly *born from* the structural one. **I-1:**
> characterize the coupling (dasha-from-nakshatra is first evidence; find others, e.g. dignity-modulated
> transit). Matters because if coupled, the intersection search is not a naïve AND of independents.

---

## §5 — THE HOLISTIC OPENING (vision + layer-shaping decisions)

### §5.1 — Where the value concentrates (the thesis)
L3's value is NOT "compute a transit." **It is the ability to identify the INTERSECTION of the
structural and temporal planes conducive to — or destined for — a certain event.** That intersection
IS the product, and it is simultaneously a point in TIME and a STRUCTURAL alignment. The mechanism is
the **CONFLUENCE / INTERSECTION SEARCH**: the rare future moment where MULTIPLE conditions hold at
once. The rarity IS the value. "Find the intersection" = "find the surgical window" (§1) = "when the
promise meets its hour" (§2) — one idea. Deliverable = a located (time, structural-alignment) pair,
ranked, provenanced.

### §5.2 — The activation-predicate bridge (THE CRUX) [RESOLVED — full design §5.12]
The layer hinges on: **how does an L2 `signature_class` yield a transit/dasha condition that fires the
pattern?** RESOLVED — see §5.12: a FINITE table of signature_class → activation-rule TEMPLATE, each
bound per signal from its constituents. Taxonomy L3-owned, populated by reading sealed L2.

### §5.3 — The service-asset model [RESOLVED 2026-06-20 — A+C, both in-layer]
"Services, not data" collides with the row-store pipeline (cockpit, DAG, WriterBase, count_sql).
**Resolution: Option A (services as first-class IN-LAYER `ka_*` service-assets, service-health model,
no count_sql) + Option C (one thin `ka_*` ARTIFACT-asset storing the derived predicates + the
memoized activation windows that fill L2's NULL hooks).** Both inside L3.
> Native correction recorded: "keep the service outside the layer" was wrong wording — a service is an
> L3 asset; "outside" only meant outside the row-store DATA model.
**New infra need:** the cockpit/DAG must learn a "service asset" type (registers, shows
health/last-invoked, no row count). → **I-2** (how a service-asset registers vs. the frozen writer
contract).

### §5.4 — Eval: the COMPUTATIONAL / PREDICTIVE split [RESOLVED 2026-06-20]
Two different "evals": (1) computational correctness ("does the machine compute what it claims?" —
knowable today) and (2) predictive accuracy ("was the prediction TRUE?" — knowable only vs. the LEL,
after the fact). **Resolution (native, fully informed after debating all-to-L5): THE SPLIT.**
Computational eval STAYS in L3 as a B6-style seal gate (every prior layer self-verified its machinery;
keeps L5's later calibration interpretable — a bad prediction is then a real model failure, not a
plumbing bug). Predictive calibration GOES to L5 Mīmāṃsā. L3 makes falsifiable datable predictions;
L5 judges them.

### §5.5 — Cleanup mandate, made concrete
Branch sprawl (`feature/subsystem-transit` + 3 panchanga branches — reconcile, Q5); the crashing
router (dead import); dual `compute_transits` (consolidate to one authority, Q6); L2 carry-in:
`bo_samskara` shipped a placeholder hash not real embeddings (Q4 — native handling).

### §5.6 — THE TEMPORAL PILLARS: Daśā, Panchāṅga, subsystem leverage [native-raised, central]
**Pillar 1 — DAŚĀ is a co-equal temporal engine, not a one-liner.** The architecture doc reduced it
to "is the dasha supportive at T" — a severe under-scoping. Daśā is arguably the PRIMARY indigenous
"WHEN": the promise unfolding from within, over nested periods (MD→AD→PD→…), across multiple systems
(Vimśottarī/Yoginī/Chara/Nārāyaṇa/KP — all in the M3 suite). **Model: L3 has TWO co-equal temporal
sub-engines — Daśā (from within) + Transit (from without) — and the intersection is where BOTH meet
the structure.** → **I-3** (how elaborately L3 leverages daśā: which systems, how many levels,
cross-daśā agreement as confidence/discovery axis).

**Pillar 2 — PANCHĀṄGA qualifies time meaningfully.** Value proven in the Muhurat Finder on 3 axes:
(1) qualifying abstract time (tithi/nakshatra/vara/yoga/karaṇa); (2) **native overlay via TĀRA BALA**
(`compute_tara_bala_score` — birth nakshatra vs. day's nakshatra → auspicious *for THIS native*, its
deepest contribution); (3) the inauspicious KNOCKOUT (a safety floor). → **I-4** (deep-research:
panchāṅga's full value surface — hora, choghadiya, muhurta sub-divisions, eclipse windows).

**Pillar 3 — leverage EVERY embedded subsystem with a temporal dimension.** Already in-path:
nakshatra (Tāra Bala + transit), yoga (special-yogas), Sade Sati. NOT yet: dignity (modulating transit
force), astrovāstu/remedial (the remedial-window — serves §1 directly), the nakshatra subsystem
(`bg_nakshatra`/`ga_nakshatra`), medical, prashna. **Principle: pull every subsystem with a temporal
dimension; it arrives via L2's structural plane.** → **I-5** (subsystem × temporal-contribution
coverage matrix).

### §5.7 — THE CONVERGENCE MACHINERY [holistic core]
**§5.7.1 — Three planes, three timescales:** (1) structural/natal (timeless, fixed); (2) daśā
(from-WITHIN, nakshatra-derived, moves over YEARS, says WHAT THEME is live); (3) transit+panchāṅga
(from-WITHOUT, fast — transit weeks/months, muhūrta hours, says which point is struck + whether the
hour is fit). The timescale gap is the key to efficiency.

**§5.7.2 — The machine: a coarse→fine FUNNEL with a SOFT prior, not a hard gate [native correction].**
Daśā must be a SOFT PRIOR, because an event can fire OUTSIDE its likely daśā when another factor
(a strong transit, rare conjunction, return, eclipse) overpowers it — and those off-daśā activations
are the highest-value discoveries. A hard gate would amputate the discovery mission. → **TWO modes:**
- **MODE A (expected):** daśā prior (decade→months, cheap `ga_dashas` lookup) → transit search inside
  survivors (months→days) → panchāṅga+muhūrta refine (days→hours) → knockout vetoes.
- **MODE B (anomalous/discovery, un-gated):** sweep for rare HIGH-MAGNITUDE confluence; check (not
  gate) daśā; flag those firing DESPITE a weak daśā as high-value (the temporal twin of `bo_anveshana`).
The funnel order is also the SEMANTIC decomposition (acharya-cognition made exhaustive).

**§5.7.3 — STRENGTH coupling [native delegation].** A trigger's activation FORCE is modulated by the
dignity/shadbala of the planet involved (dignified fires strongly; debilitated weakly). The intersection
score is a *weighted convergence*, not a naïve AND. The *degree* of each factor's influence is delegated
to Cowork's domain reasoning. **Guardrail:** every weight is a stated, versioned, CITABLE judgment,
proposed→ratified→frozen ([[feedback-canonical-or-floor-rule]]). → **I-7** (the influence-weight model).

**§5.7.4 — Coverage matrix (I-5 concrete):** Daśā(stage1, cross-daśā agreement=amplifier/disagreement=
discovery) · Transit(2) · Nakshatra(2–3, Tāra Bala native overlay) · Yoga(3+1) · Panchāṅga/Muhūrta/
Horā(3) · Dignity/Shadbala(modulates 2) · Sade Sati/affliction(4 knockout) · Astrovāstu/remedial
(consumes output) · Medical(1 target+4) · Prashna(meta).

**§5.7.5 — Infrastructure preview (5 services + 1 artifact):** ephemeris-at-T service; daśā-timeline
service; transit-search service (the unbuilt heart); panchāṅga/muhūrta service (**LIVE by (date,
location)**, reads `bg_ephemeris`, applies the local sunrise-relative step live); the CONVERGENCE
engine (Mode A+B + strength + knockout → ranked intersections); the activation-artifact asset.
The **activation-predicate bridge** (Q2) is the glue: signature_class → daśā-eligibility prior + transit
trigger. `signal_activator.py` v1 is the primitive seed we generalize.

### §5.8 — WORKED TRACE: "next opportune window to activate my Lakshmi yoga?" [readiness checklist]
| Step | Asset | Exists? |
|---|---|---|
| 0 resolve target → L2 signal+signature_class | bodha_msr_signals | ✅ |
| 1 derive predicate | bridge (Q2)+bg_transit_rules | ⚠️ v1 |
| 2 daśā prior (Mode A) | daśā service / ga_dashas | ✅ data; ⚠️ wrapper |
| 3 Mode B sweep | transit-search + convergence | ❌ build |
| 4 transit search (Mode A) | transit-search + ephemeris | ❌ unbuilt; ⚠️ real impl stranded |
| 5 strength modulation | ga_strength + weights (I-7) | ✅; ⚠️ weights |
| 6 panchāṅga+muhūrta refine | Muhurat Finder | ✅ |
| 7 knockout vetoes | _in_inauspicious + affliction | ✅; ⚠️ target-affliction |
| 8 rank+store, fill NULL hooks | convergence + artifact | ❌ build |
| 9 narrate | retrieval/serve | ⚠️ later |

**Verdict:** architecture handles it cleanly; ~50% built; missing core = transit-search + convergence.
> **Governing efficiency law (native):** *"Transit is a service; we cannot keep triggering it. We
> trigger it once the window is narrowed."* The expensive ephemeris fires LAST. All §5.9 serves this.

### §5.9 — THE TRAVERSAL INFRASTRUCTURE (efficient sweep)
**§5.9.1 — Mode A: lazy pruning daśā-tree walk.** The nested tree (MD→AD→PD→Sookshma→Prāṇa ≈ 9⁵) is
never walked whole: top-down with EARLY PRUNING (prune a whole subtree if its MD is ineligible —
most of the tree dies at level 1–2); descend only into live branches to the depth the query's
precision demands; INTERVAL ALGEBRA over `ga_dashas`' precomputed intervals (no time iteration);
multi-level + multi-system (cross-daśā intersection). Output: a small ranked set of scored intervals.

**§5.9.2 — Mode B: the NON-FUNNEL engine, built THOROUGHLY [native priority].** When the supportive
daśā is past/far, Mode B is the ONLY path — so it is first-class. Four layers: (1) the extensible
**TRIGGER VOCABULARY** (conjunction/aspect/ingress/return/station-retrograde/eclipse/multi-planet/
transit-to-transit — each a generator); (2) COARSE SELF-NARROWING via the **HYBRID** (analytic
predictors PLACE & RANK a coarse grid but may only ADD/prioritize, NEVER veto; a coarse ephemeris grid
owns COMPLETENESS incl. retrograde multi-pass; precise ephemeris refines) — the coarse-to-fine answer
to the ±10yr cap (Q7); (3) MAGNITUDE scoring + threshold (I-8); (4) the shared refinement tail.
**ALWAYS-RETURN-RANKED guarantee:** never "no window" — lowers the threshold, returns the strongest
available, each labeled with magnitude/confidence.

**§5.9.3 — THE UNIFYING SPINE:** generator → interval-narrowing → ephemeris-LAST. Both modes:
GENERATORS produce candidate intervals cheaply (no ephemeris); a NARROWING pipeline scores/prunes
(still no ephemeris); the precise EPHEMERIS fires LAST inside survivors (bounded calls regardless of
horizon); a shared refinement tail. Plus an **EPHEMERIS CACHE** (I-9). Four designed-in optimizations:
the daśā-first funnel, the ephemeris-last spine, Mode B's coarse-to-fine grid, the cache.

### §5.10 — THE PRECOMPUTE / ON-DEMAND BOUNDARY [RESOLVED 2026-06-20]
**Test: precompute as a stored asset IFF finite/enumerable AND location-INDEPENDENT.**
- Daily ephemeris — location-independent → **PRECOMPUTE (`bg_ephemeris`, EXISTS, 1900–2150, ~825k). Leverage.**
- Daily **panchāṅga** — location-DEPENDENT → **SERVICE (live by date,location). NO stored asset.**
- Transit "when does X hold" — query-infinite → SERVICE.
- Daśā periods (chart-bound finite) → precomputed `ga_dashas` (read as service input).
- Activation windows (chart-bound) → memoize into the artifact-asset.

**DAILY-PANCHĀṄGA DECISION (native): NO daily-panchāṅga asset.** Panchāṅga depends on LOCATION and the
person's location CHANGES; a precomputed table bakes in one place and is silently wrong elsewhere.
> Cowork misstep corrected: Cowork proposed `ka_panchanga_daily` as "the one data-exception." Native
> caught the flaw — this STRENGTHENS the principle (panchāṅga confirms, not excepts, "timing=services").
**Cleanup (I-10):** the existing Bhubaneswar-fenced `panchanga_daily` cache is the symptom of this
problem — it is at most an internal native-home memo, NEVER a layer asset.

---

## §6 — The L2→L3 contract (VERIFIED in bo_laksana.py) [VERIFIED]
- **`signature_class`** — the matchable fingerprint the bridge keys on (stored NULL today; L3 reads it).
- **The NULL L3-fill hooks** — `active_dasha_periods_jsonb`, `activation_predicted_dates_jsonb`,
  `dasha_activation_proximity_score` (written NULL by L2 at `bo_laksana.py` ~760/~792). **L3 fills them
  in L3 artifacts referencing the L2 signal_id; L3 NEVER writes back into L2's timeless tables.**
- **`bo_anveshana` hypothesis hooks** → L3 activations become datable predictions L4/L5 validate.
- **`resonance_eligible`** patterns = L3's search targets.
> The NULL hooks being NULL is the *reserved surface*, not an oversight — never "helpfully" populate in L2.

---

## §7 — Temporal discovery = the discovery engine applied to TIME
`bo_anveshana`'s mission on the TEMPORAL axis: the rare FUTURE MOMENT when the sky activates a
consequential natal pattern — the window no acharya could compute by hand. Cross-subsystem discovery =
across disciplines; opportune-moment discovery = across time. L3's discovery output is first-class,
ranked, provenanced.

---

## §8 — The wave plan (DRAFT v0.10 — reflects the full holistic opening)
```
K0  CLEANUP + FOUNDATION (§5.5, §5.10): reconcile branch sprawl (Q5); consolidate compute_transits via
    a shim (Q6); scaffold the SERVICE-ASSET model (I-2); confirm bg_ephemeris + demote the fenced cache (I-10).
K1  EPHEMERIS + DAŚĀ SERVICES (modernize the M3 suite): ephemeris-at-T (cache I-9); daśā-timeline service
    over ga_dashas + the M3 daśā suite, multi-system; the lazy pruning tree-walk (§5.9.1).
K2  THE TRANSIT-SEARCH ENGINE (BUILD — the unbuilt heart): find_aspect/conjunction + extended vocabulary
    (ingress/return/station); continuous orb-strength (I-17); fix the crashing router.
K3  THE ACTIVATION-PREDICATE BRIDGE (§5.12): the signature_class CLASSIFIER + the class→template TABLE (I-15);
    generalize signal_activator.py v1 (DB read, not markdown).
K4  THE CONVERGENCE ENGINE — Mode A+B (the valuable core): generator→narrow→ephemeris-LAST spine; the RIGOR
    STRATUM (I-16 scoring, I-18 window profile, I-7 strength, knockouts); query_auspicious_timing(); coarse-to-fine (Q7).
K5  THE SUPREME PRODUCTS (§5.11.4, same spine run exhaustively): lifetime CATALOG (K); co-equal DANGER windows
    (D); WINDOW→INTERVENTION→TIMING loop to bo_upaya/astrovāstu (I); cross-pattern prioritization (C); daśā
    macro-narrative (L); temporal DISSONANCE (I-23); cross-subsystem convergence (I-13).
K6  THE STATISTICS + LEARNING HOOK (§5.13.B/C/D): base-rate rarity (I-19); birth-time uncertainty (I-20);
    confidence function (I-21); correlation discount (I-22); the prediction-RECORD schema (I-24); honesty vocab.
K7  RETRIEVAL + EVAL + SEAL: retrieval review; QT coverage (I-14); L3's COMPUTATIONAL eval gate (§5.4,
    predictive DEFERRED to L4/L5); L3_KALA_CLOSE + the L4 onboarding contract.
```
> Wave SHAPE, not the final plan — per-wave detail produced at the per-asset briefs. Order reflects the
> efficiency law (services+bridge → engine → products → statistics that score them).

---

## §5.11 — SUPREME ELEVATION: from timing-calculator to oracle of agency [capstone, native-directed]
*(Logically part of §5; placed here as the elevation capstone.)*

**§5.11.1 — Four things a SUPREME L3 does:** (1) answers questions the client doesn't know to ask;
(2) inverts prophecy→AGENCY (the intersection is an INSTRUCTION — when to ACT + WHAT to do); (3)
DISCOVERS unprompted across chart×all-time×all-subsystems; (4) reasons about CONSEQUENCE + RISK.

**§5.11.2 — THE CONSUMER QUESTION-SPACE (QT-1…QT-8 — the asset-coverage spec):**
| # | Family | Primary engine |
|---|---|---|
| QT-1 | forward activation | Mode A+B |
| QT-2 | window-for-purpose | Mode A+B+muhūrta |
| QT-3 | danger/avoidance | the danger engine |
| QT-4 | comparative | cross-pattern prioritization |
| QT-5 | life-arc/macro | daśā macro-narrative |
| QT-6 | diagnostic/retrodiction | reverse activation (also L5 bridge) |
| QT-7 | discovery/wonder | the lifetime confluence catalog |
| QT-8 | intervention-timing | the window→intervention loop |

**§5.11.3 — GAP REGISTER (v0.5→supreme):** A implicit-question-space→CLOSED (QT taxonomy); B no-danger-
engine→CLOSED (danger co-equal); C no-comparative→ADD (I-11); D intervention-hollow→CLOSED (the loop);
E no-life-arc→ADD (I-12); F no-discovery-catalog→CLOSED (the catalog); G cross-subsystem-convergence-not-
first-class→NAME the apex (I-13); H no-confidence-vocab→ADD (§5.11.6, the honesty layer).

**§5.11.4 — NEW FIRST-CLASS PRODUCTS (native-ratified):**
- **K — LIFETIME CONFLUENCE CATALOG:** run the discovery engine EXHAUSTIVELY over chart×lifetime×
  subsystems; store the ranked rare confluences as a standing catalog. L3's twin of `bo_anveshana`.
  Precomputable (chart-bound+finite). Serves QT-7; volunteered unprompted.
- **D — DANGER/AVOIDANCE WINDOWS (co-equal):** a first-class inverse search — when NOT to act, exposure/
  affliction periods — ranked outputs, not just knockout vetoes. Prophecy includes WARNING. QT-3.
- **I — WINDOW→INTERVENTION→TIMING LOOP (prophecy→agency, the native's core ask):** L3 wires the found
  window to the remedial layer (`bo_upaya` + astrovāstu) → window→intervention→that intervention's
  optimal timing. WHEN+WHAT+when-the-what-is-most-potent. QT-8. *(L3 owns the timing; the intervention
  CONTENT comes from L2 `bo_upaya`, referenced not restated — a JOIN, not duplication.)*
- **C — CROSS-PATTERN PRIORITIZATION:** rank across patterns/domains. QT-4.
- **L — DAŚĀ MACRO-NARRATIVE (life-arc as OUTPUT):** the next N years as CHAPTERS. QT-5. *(Daśā was only
  a search INPUT; here it becomes a product.)*

**§5.11.5 — APEX INSIGHTS (beyond a super-acharya):** (1) off-daśā anomalous activations (Mode B);
(2) **CROSS-SUBSYSTEM TEMPORAL CONVERGENCE — transit+daśā+nakshatra+yoga INDEPENDENTLY agree (the
deepest L3 insight, the temporal twin of L2 cross-domain linkage)**; (3) the lifetime catalog;
(4) window-collision/interference (constructive/destructive overlap); (5) the cost-of-omission
("won't recur for 19 years" — makes rarity actionable).

**§5.11.6 — THE HONESTY LAYER:** the LLM speaks a defined confidence vocabulary — **high** (multiple
independent currents agree), **moderate** (a strong single trigger), **speculative** (a weak/lone
trigger). Serve-time EXPRESSION of the internal magnitude scores. (Calibration vs. reality is L5;
expressing the model's own confidence is L3's duty — oracle, not fortune-teller, per the Ethical Framework.)

**§5.11.7 — Alignment (no bloat):** every new product reuses the §5.9 spine — the catalog is Mode B run
exhaustively+stored; danger windows are the same search with malefic predicates; the intervention loop
is a JOIN to `bo_upaya`; prioritization/macro-narrative/honesty are serve-time reasoning over the same
stored outputs. **Same machine, exhaustively run and well-presented — not new machinery.**

---

## §5.12 — Q2 RESOLVED: THE ACTIVATION-PREDICATE BRIDGE [native-ratified 2026-06-20]

**§5.12.1 — Two code-verified findings:** (1) `signature_class` is RESERVED but UNPOPULATED —
written `None` in the L2 seal (`bo_laksana.py` line 787), no migration defines its vocabulary. (2) the
v1 `signal_activator.py::decide_state` (daśā-lord ∈ `entities_involved` → "lit") IS the YOGA-class
daśā-eligibility rule in primitive form — generalize, don't replace.

**§5.12.2 — The mechanism (ratified): signature_class → activation-rule TEMPLATE, BOUND per signal.**
`signature_class` is the ABSTRACTION collapsing thousands of signals into ~10–15 ACTIVATION ARCHETYPES.
Two-level map: CLASSIFY each signal into a class (from existing L2 fields); MAP class → a parameterized
TEMPLATE; BIND the template's parameters (grahas/houses/signs) from the signal's own constituents.
**FINITE table of class→template (~10–15), each instantiated from the signal.** Not per-signal lookup;
not free derivation. General per class; specific per signal.

**§5.12.3 — The signature_class taxonomy (L3-OWNED; populated by reading L2 — L2 stays sealed):**
YOGA (yoga_label→opportune) · DOSHA (dosha_label→danger) · DIGNITY (ga_strength state) · DISPOSITOR/
RELATIONAL (parivartana/dispositor_chain) · SENSITIVE-POINT (arudha/karakamsa/kp_cuspal — transit over
the point) · CONJUNCTION/ASPECT (natal aspect re-triggered) · SUBSYSTEM (ga_sade_sati/ga_medical/ga_vastu).

**§5.12.4 — The template (3 parts):** (1) daśā-eligibility rule (Mode-A prior) — e.g. YOGA: eligible
when MD/AD lord ∈ {constituent lords ∪ dispositors}; (2) transit-trigger rule (Stage 2/Mode B) — events
from the §5.9.2 vocabulary parameterized by the signal's houses/lords; (3) strength-modulation +
affliction-veto hook (§5.7.3/I-7; feeds danger §5.11.4-D).

**§5.12.5 — Deterministic AND acharya-grade:** table fixed+versioned; classification+binding are
mechanical reads; predicate evaluation is pure logic — no LLM. Each template encodes a CLASSICAL
principle (a yoga fires when its lord is daśā-active+transit-supported+unafflicted), sourced from
`bg_transit_rules`, carrying a DERIVATION_LEDGER. The judgment-weights are ratified (I-7).

**§5.12.6 — Two NEW build artifacts:** (1) the signature_class CLASSIFIER (reads L2, assigns class,
references signal_id); (2) the class→template TABLE (~10–15 classical templates, versioned+cited) →
authoring item **I-15**.

**§5.12.7 — v1 generalizes** along: one class→full taxonomy; "lit NOW"→"WHEN over a horizon" (the search);
flat 0.6→strength-modulated magnitude. Salvage the v1 daśā-interval lookup + transit read; replace its
MSR-markdown parse with a DB read of `bodha_msr_signals`.

---

## §5.13 — THE RIGOR STRATUM: supreme intelligence grounded in mathematics + statistics [all nine ratified]

The native asked what aspect of SUPREME INTELLIGENCE grounded in mathematics/statistics/data-engineering
was missing. Nine gaps, all first-class — a deterministic, versioned, cited stratum UNDER the convergence
engine (same §5.9 spine, no new machinery; judgment-parameterized weights, mechanically applied).

**A — MATHEMATICS OF CONFLUENCE:** **A1/I-16** a FORMAL convergence-scoring function (multiplicative
across NECESSARY conditions — a veto if a prerequisite is absent — and additive-with-saturation across
SUPPORTING conditions, with interaction terms) — the central math object we'd skipped. **A2/I-17**
continuous ORB-STRENGTH ∈[0,1] = f(orb, speed, applying/separating) — calculus over the speed the
ephemeris already returns; applying aspects stronger than separating. **A3/I-18** WINDOW AS A
TIME-SERIES (ramp/peak/decay) with a PEAK (the surgical moment) + usable SHOULDER — "opens Mar 3, peaks
Mar 11, usable through Mar 18."

**B — STATISTICS OF RARITY + CONFIDENCE:** **B1/I-19** MEASURED base-rate rarity ("a 1-in-23-year
configuration" as a COMPUTED number — extend the sweep over a long baseline) — fortune-teller vs.
instrument. **B2/I-20** birth-time UNCERTAINTY PROPAGATION (perturb within the error band, re-run, emit a
robustness flag). **B3/I-21** a mathematically-DEFINED confidence function = f(independent-current count ×
strengths × rarity × robustness) → maps to high/moderate/speculative.

**C — INTELLIGENCE OF INDEPENDENCE + DISSONANCE:** **C1/I-22** INDEPENDENCE modeling + correlated-evidence
DISCOUNT — daśā is derived from nakshatra (I-1), so a nakshatra-overlay and a daśā "agreeing" may be ONE
piece double-counted; model the correlation + discount, or the engine overstates confidence on its
headline insight (an echo chamber). **The most intellectually serious gap.** **C2/I-23** TEMPORAL
DISSONANCE first-class — a strong opportune window for one domain coinciding with a danger window for
another; surface the tension, never average into a misleading "medium."

**D — THE LEARNING-LOOP HOOK:** **I-24** L3 emits feature-tagged, falsifiable, calibratable PREDICTION
RECORDS (triggers, magnitudes, convergence score, rarity, confidence, independent-current count) so L5 can
run reliability curves/Brier scores and feed weights BACK. An L3 DESIGN OBLIGATION, not an L5 afterthought.

> **Synthesis:** the rigor stratum converts every soft claim into a computed object — magnitude→a
> convergence FUNCTION over CONTINUOUS strengths profiled as a window time-series; "rare"→a MEASURED base
> rate; "confident"→a CONFIDENCE FUNCTION that DISCOUNTS correlated evidence, propagates uncertainty, and
> names DISSONANCE; and the whole emits CALIBRATABLE records so the instrument LEARNS. The
> mathematical/statistical soul of "supreme."

---

## §9 — Standards L3 inherits [VERIFIED against CLAUDE.md §N]
Deterministic-first (no generative LLM in the build; "improvisation" = creative latitude in SHAPING, not
loosening determinism gates); FROZEN orchestrator contract (`ka_*` writers `@register`/WriterBase, NEVER
commit/close `ctx.db_conn` — heed L2 Vimarśaka-RED, 6/10 bo_ writers remediated); anti-drift (REFERENCE
L2 signal_ids + L1/ephemeris facts, never restate; DERIVATION_LEDGER per claim); the LEL toggle
(`lel_enabled`/`lel_origin`); PROD-VERIFY (ACs vs. prod not worktree — Brahma V1.3); FORENSIC holds; only
chart `482012f1`; prefix `ka_*`, tables `kala_*`.

---

## §10 — OPEN QUESTIONS + INVESTIGATION REGISTER

| # | Question | Status |
|---|---|---|
| Q1 | Service-asset model | RESOLVED — A+C, both in-layer; cockpit gains a service-asset type |
| Q2 | Activation-predicate bridge | RESOLVED (§5.12) — class→template bound per signal; L3-owned taxonomy |
| Q3 | Eval placement | RESOLVED — THE SPLIT: computational in L3, predictive in L5 |
| Q4 | bo_samskara placeholder embeddings | OPEN — native addressing |
| Q5 | Branch reconciliation order | OPEN — Cowork judgment; lean panchāṅga-first then transit |
| Q6 | Real compute_transits vs. stub | RESOLVED — real = scripts/temporal get_transit_states; shim the adapter |
| Q7 | ±10yr search cap | OPEN-decision — Cowork view: cap threatens core value; fix = coarse-to-fine |

**Investigation/authoring items:** I-1 plane-coupling · I-2 service-asset registration · I-3 daśā depth ·
I-4 panchāṅga deep-research · I-5 subsystem coverage matrix · I-6 M3-suite salvage · I-7 influence-weight
model · I-8 Mode-B magnitude threshold · I-9 ephemeris cache/engine contract · I-10 precompute/on-demand
authority · I-11 cross-pattern prioritization · I-12 daśā macro-narrative · I-13 cross-subsystem
convergence · I-14 QT coverage spec · I-15 author the class→template table · I-16 convergence-scoring
function · I-17 orb-strength curve · I-18 window profiling · I-19 base-rate rarity · I-20 birth-time
uncertainty propagation · I-21 confidence function · I-22 subsystem correlation discount · I-23 temporal
dissonance · I-24 prediction-record schema.

---

## §11 — Discussion record (the retention log)
- **2026-06-20** — Native ratified the 6-step approach + documentation-first discipline; output =
  authored .md briefs (Cowork→Antigravity split).
- **v0.1–v0.3** — Engine audit (§3, BUILD+WIRE); the M3 suite finding (§3.1); §1 temporal-discovery +
  §2 promise-manifestation framing; "perpendicular"→coupling (§4); value thesis = the intersection (§5.1);
  service model A+C (Q1); eval split (Q3); the three pillars (§5.6); the convergence machinery (§5.7) —
  three planes, soft-prior, Mode A+B; strength delegation (I-7).
- **v0.4** — Worked trace (§5.8) + traversal infrastructure (§5.9): Mode A tree-walk; Mode B built
  thoroughly; hybrid narrowing (native-ratified); always-return-ranked; ephemeris-last spine + cache.
- **v0.5** — Precompute/on-demand boundary (§5.10): leverage bg_ephemeris; **NO daily-panchāṅga** (native
  correction — location-dependent + mobile subject).
- **v0.6** — Supreme elevation (§5.11): QT-1…QT-8; three new products (catalog/danger/intervention-loop);
  apex insights; honesty layer.
- **v0.7** — Q2 RESOLVED (§5.12): class→template bound per signal; L3-owned taxonomy; v1 salvageable.
- **v0.8** — The rigor stratum (§5.13): all nine gaps ratified; also fixed v0.x consistency defects.
- **v0.9** — Asset reconciliation (§14): code-verified the 4 registered Kāla placeholders + L4/L5 deps;
  native ratified keep-id-elevate-content + the L3/L4 boundary.
- **v0.10** — Asset set LOCKED with names (§14.5): schema-fit; R-5 subsume; 9 build-new names ratified.
- **2026-06-21** — **Persistence-desync recovery (§15):** discovered the on-disk file was only v0.3 (the
  v0.4→v0.10 Edits never flushed due to a file-tool/shell desync after a `git mv`). All decisions were
  preserved in conversation + memory; the full plan was REWRITTEN via the Write tool and read-back verified.

---

## §12 — Changelog
- v0.1–v0.3 — holistic opening through the convergence machinery.
- v0.4 — worked trace + traversal infrastructure.
- v0.5 — precompute/on-demand boundary.
- v0.6 — supreme elevation.
- v0.7 — Q2 resolved (activation bridge).
- v0.8 — rigor stratum; consistency fixes.
- v0.9 — asset reconciliation (§14).
- v0.10 — asset set locked with names (§14.5).
- **v0.10 (reconstructed 2026-06-21)** — full plan rewritten via Write after the persistence desync (§15);
  content consolidated from conversation + memory; read-back verified. No decisions changed — recovery only.

---

## §13 — State of the holistic opening
**SETTLED:** mission (§1); services-not-data + promise-manifestation (§2); engine audit + M3 suite (§3);
two-plane + coupling (§4); intersection value thesis (§5.1); service model A+C (§5.3); eval split (§5.4);
the three pillars (§5.6); convergence machinery + Mode A/B (§5.7); traversal infrastructure (§5.9);
precompute/on-demand boundary (§5.10); supreme elevation + QT + 3 products (§5.11); activation bridge
(§5.12); the rigor stratum (§5.13); asset set locked (§14, §14.5).
**STILL OPEN (§10):** Q4, Q5, Q7-decision; authoring/investigation items I-1…I-24, reconciliation items
R-1…R-4. These are *work*, not unresolved *design*.
**NEXT:** approach STEP 3 — per-asset deep review (the per-asset briefs).

---

## §14 — ASSET RECONCILIATION (approach STEP 2) [native-directed; full-alignment]

### §14.0 — CODE-VERIFIED registered reality (`asset_registry_seed.ts`)
The registry ALREADY contains **4 Kāla placeholders**, with L4/L5 assets depending on them:
| id | Sanskrit/English | Registered meaning (OLD model) | table | depends_on | Downstream |
|---|---|---|---|---|---|
| `ka_kalasutra` | Kālasūtra/Timeline | "one row per date for the life span" (STORED daily timeline) | kala_timeline | ga_dashas, bg_ephemeris | ph_muhurta, mi_bhavisya |
| `ka_sangam` | Saṅgam/Convergence | "dasha-transit convergence windows" | kala_convergence | ka_kalasutra | ph_nimitta |
| `ka_vighnakara` | Vighnakāra/Obstruction | "inauspicious/obstructed windows" | kala_obstruction | ka_kalasutra, ga_sensitive | ph_pratikara |
| `ka_transit_almanac` | Kāla-sañcara/Transit almanac | "timeline rows w/ active transits" | kala_timeline | bg_ephemeris, ka_kalasutra | — |

**Critical finding:** the placeholders embody the **OLD PRECOMPUTE-EVERYTHING model** (`ka_kalasutra` =
a stored row-per-day timeline) — exactly what §5.10 REVISED. They must be ELEVATED, not merely filled.
**Also verified — the L3/L4/L5 boundary is already drawn in the registry AND it ALIGNS with our decisions:**
L4 Phala owns `ph_nimitta` (anchors←ka_sangam), `ph_muhurta` (←ka_kalasutra+ga_panchanga), `ph_sodhana`/
`ph_suddha_sodhana` (rectification), `ph_pratikara` (mitigation←bo_upaya+ka_vighnakara); L5 Mīmāṃsā owns
`mi_bhavisya` (**predictions with confidence+falsifiers**←bo_laksana+ka_kalasutra) and `mi_pramana`
(**calibration**). **This CONFIRMS our eval-split + learning-hook were already the registered architecture.**

### §14.1 — THE BOUNDARY RULING (native-ratified)
**L3 = ENGINES + WINDOWS + rigor SCORING + prediction-RECORD emission. L4 Phala / L5 Mīmāṃsā = APPLIED
PRODUCTS that consume them.** So the WINDOW→INTERVENTION→TIMING loop (L3 computes the timing; `ph_pratikara`
applies the remedy at L4) and the uncertainty propagation (L3 computes robustness; `ph_sodhana` is the L4
rectification product) and the prediction-records (L3 emits; `mi_bhavisya`/`mi_pramana` consume at L5) all
HAND UP — they are not L3 end-products. Honors the registered DAG + layer purity.

### §14.2 — THE RECONCILED SET (keep-elevate / add)
**A. ELEVATE (registered id kept; content redefined):**
| id | Elevate to |
|---|---|
| `ka_kalasutra` | the activation-ARTIFACT (predicates + memoized windows filling L2's NULL hooks) — NOT a daily timeline |
| `ka_sangam` | the CONVERGENCE-ENGINE OUTPUT — ranked intersection windows + rigor scores (extend `kala_convergence`) |
| `ka_vighnakara` | the DANGER ENGINE — first-class ranked danger/avoidance windows (extend `kala_obstruction`) |
| `ka_transit_almanac` | → see §14.5.2 (SUBSUMED into the transit-search service) |

**B. ADD (new `ka_*`):** ephemeris service · daśā service · transit-search service · panchāṅga/muhūrta
service · activation-bridge · convergence engine (implicit) · lifetime catalog · cross-pattern
prioritization · daśā macro-narrative · prediction-record emitter. (Names locked §14.5.4.)

**C. SERVICE-ASSET TYPE (I-2)** is the enabling prerequisite for the service rows.

### §14.3 — COVERAGE CHECK (no point missed)
Every QT-1…QT-8 family AND every rigor object (A1–D) maps to an owning asset:
QT-1 bridge+convergence→ka_sangam · QT-2 convergence+panchāṅga (L4 ph_muhurta applies) · QT-3 ka_vighnakara
· QT-4 cross-pattern prioritization · QT-5 daśā macro-narrative · QT-6 convergence run backward · QT-7
lifetime catalog · QT-8 convergence window (L4 ph_pratikara applies) · rigor A1–A3 convergence engine ·
B1–B3 convergence+catalog · C1 correlation-aware aggregation · C2 convergence×danger overlap · D
prediction-record emitter→L5 · L2 NULL-hook fill ka_kalasutra · daśā/panchāṅga pillars → their services ·
subsystem leverage → bridge templates + service inputs. **No QT family and no rigor object is unowned.**

### §14.4 — Open reconciliation items (carry to per-asset briefs)
- **R-1:** rewrite the registry rows for the 4 elevated/subsumed ids (esp. `ka_kalasutra`: drop the
  row-per-day formula). Migration + seed update.
- **R-2:** choose + register the ADD-set ids (gated on the service-asset type, I-2). *(Names now in §14.5.)*
- **R-3:** audit the `kala_timeline`/`kala_convergence`/`kala_obstruction` SCHEMAS vs. the elevated content
  (`0001_brahma_baseline.sql`). *(Done §14.5.1.)*
- **R-4:** specify the L3→L4 hand-up contracts (ka_sangam→ph_nimitta/ph_muhurta; ka_vighnakara→ph_pratikara;
  prediction-emitter→mi_bhavisya).
- **R-5:** ka_transit_almanac subsume-or-keep. → **RESOLVED §14.5.2 (subsume).**

### §14.5 — THE LOCKED ASSET SET (names + R-5 + schema-fit) [native-ratified]
**§14.5.1 — Schema-fit (good-news alignment; extend not replace):** `kala_convergence` already has
`convergence_score ∈ [0,1]`, `constituent_factors` jsonb ({label,date,weight,factor_type}),
`source_citation`, a ≥3-factor rule (factor_type ∈ {dasha_transition, transit_conjunction,
signal_activation, md_ad_alignment}) → near-perfect home for elevated `ka_sangam`. `kala_obstruction`
already has `obstruction_type ∈ {malefic_transit, adverse_dasha, double_affliction}`, `severity ∈ [0,1]`,
`factors` → strong home for elevated `ka_vighnakara`. Only `kala_timeline` (the daily precompute table)
needs real rework.

**§14.5.2 — R-5 RESOLVED: SUBSUME `ka_transit_almanac` into the transit-search service (`ka_gochara`).**
The almanac was just a FILTER on `kala_timeline` (no schema of its own); since that table is reworked
away and nothing downstream depends on the almanac id, the transit-search service produces its
event-almanac output. **Elevate count 4→3.**

**§14.5.3 — Convergence engine is IMPLICIT** (the writer of `ka_sangam`, not a separate id — consistent
with the writer→asset model). Likewise the danger engine writes `ka_vighnakara`.

**§14.5.4 — LOCKED BUILD-NEW names:**
| id | Sanskrit/English | Type | Role |
|---|---|---|---|
| `ka_graha_sancara` | Graha-sañcara / Ephemeris service | SERVICE | positions-at-T (wraps M3 get_transit_states) |
| `ka_dasha_kala` | Daśā-kāla / Daśā service | SERVICE | daśā-timeline eligibility prior; the tree-walk |
| `ka_gochara` | Gochara / Transit-search service | SERVICE | events; **subsumes the almanac** |
| `ka_muhurta_seva` | Muhūrta-sevā / Panchāṅga-muhūrta service | SERVICE | live by (date,location); Tāra Bala overlay |
| `ka_yojaka` | Yojaka / Activation bridge | ARTIFACT+logic | classifier + class→template table (Q2) |
| `ka_kala_darshana` | Kāla-darśana / Lifetime confluence catalog | ARTIFACT | standing discovery product |
| `ka_tulana` | Tulanā / Cross-pattern prioritization | logic/serve | rank across patterns/domains (QT-4) |
| `ka_jivana_parva` | Jīvana-parva / Daśā macro-narrative | ARTIFACT/serve | life-arc chapters (QT-5) |
| `ka_bhavishya_lekha` | Bhaviṣya-lekhā / Prediction-record emitter | ARTIFACT (hands up) | records→L5 (pairs w/ mi_bhavisya) |

**§14.5.5 — FINAL LOCKED L3 ASSET SET.**
**ELEVATE (3):** ka_kalasutra (→activation-artifact), ka_sangam (→convergence output+rigor), ka_vighnakara
(→danger engine). **SUBSUMED (1):** ka_transit_almanac → ka_gochara. **BUILD-NEW (9):** §14.5.4.
**LEVERAGE EXISTING:** bg_ephemeris, ga_dashas, the M3 scripts/temporal suite, muhurat/finder.py,
signal_activator.py v1, L2 bodha_msr_signals, L1 strength/sensitive. **ENABLING INFRA (1):** the
service-asset type (I-2). **Tally: 3 elevate · 1 subsume · 9 build-new · ~7 leverage · 1 infra.**

---

## §15 — PERSISTENCE-DESYNC INCIDENT + RECOVERY (2026-06-21) [retained for governance]
During the v0.4→v0.10 enhancement passes, a file-tool/shell DESYNC (after an early `git mv` rename) caused
Edit-tool writes to report success while NOT flushing to the on-disk workspace file. A completeness-verify
request surfaced it: the on-disk file was still `v0.3`. **No decisions were lost** — all were preserved in
the conversation record + the memory file `project_l3_kala_engine_audit.md`. **Recovery:** the full plan was
REWRITTEN via the Write tool (which creates a fresh file, no stale handle), at the canonical filename, and
**read-back verified**. **Lesson (process):** after any bash rename of a file being edited, do NOT trust
subsequent Edit calls silently — Write the consolidated file fresh and read-back to confirm bytes on disk.

---

*End of L3_KALA_CAMPAIGN_PLAN v0.10 (DRAFT). The holistic opening is complete (vision, convergence
machinery, traversal infrastructure, data-vs-service boundary, supreme elevation, activation bridge, rigor
stratum) and the asset set is LOCKED with names (§14.5). Recovered + read-back verified after the §15
persistence incident. Next: approach STEP 3 — per-asset deep review.*
