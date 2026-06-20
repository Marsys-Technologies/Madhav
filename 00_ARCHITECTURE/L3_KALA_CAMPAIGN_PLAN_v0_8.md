---
artifact: L3_KALA_CAMPAIGN_PLAN_v0_3.md
canonical_id: L3_KALA_CAMPAIGN_PLAN
version: 0.3
status: DRAFT (holistic opening — to be ENHANCED iteratively, not rewritten; v0.x = pre-ratification draft series)
authored_by: Cowork 2026-06-20
native: Abhisek Mohanty (chart_id 482012f1-710e-4a25-994a-93821f5871aa)
supersedes_on_ratification: nothing yet — this is the first L3 campaign-plan artifact
purpose: >
  The governing campaign plan for L3 Kāla (the TEMPORAL layer). Authored draft-first and in
  DETAIL from the very beginning so that facts, discussions, decisions, and nuances are RETAINED
  rather than lost to "fill in later" — per native directive 2026-06-20 (documentation-first
  discipline). This v0.1 captures the HOLISTIC OPENING: the layer vision, the verified ground
  truth (the engine audit), the open design questions, and the discussion record. It will be
  enhanced through v0.x until ratified to v1.0, then it spawns per-asset briefs for the
  Cowork→Antigravity build.
read_in_order:
  - 00_ARCHITECTURE/L3_KALA_CAMPAIGN_HANDOFF_v1_0.md          # the entry brief (mission, principle, wave shape)
  - 00_ARCHITECTURE/L3_KALA_TEMPORAL_ARCHITECTURE_v1_0.md     # the design (the two-axis decomposition, the bridge)
  - 00_ARCHITECTURE/L2_BODHA_CLOSE_v1_0.md §8                 # the L2→L3 onboarding contract
  - 00_ARCHITECTURE/LEL_TOGGLE_GOVERNING_PRINCIPLE_v1_0.md    # L3 honors lel_enabled
  - CLAUDE.md §C + CURRENT_STATE + git                        # always — verify live state
governing_approach:
  ratified_by_native: 2026-06-20
  steps:
    - "0. Ground-truth audit (DONE — §3 of this doc)"
    - "1. Holistic opening — treat the whole layer as one improvisation opportunity; settle vision BEFORE touching assets (this doc)"
    - "2. Settle the asset set — update/define which assets comprise the layer"
    - "3. Per-asset deep review — maximal value out of each asset"
    - "4. Holistic closing review — re-evaluate the whole layer for the value it delivers"
    - "5. Retrieval tools — review how L3 is served/queried"
    - "6. Clean seal — close out cleanly; clean up the mess (branch sprawl etc.)"
  documentation_discipline: >
    Document in DETAIL from the very beginning. Facts, discussions, activities, and nuances —
    even small ones — are RETAINED in-artifact, because critical aspects are routinely lost when
    a plan is thin and "filled in later." Every decision carries its WHY. Every open question is
    tracked, not dropped. (Native directive 2026-06-20.)
---

# L3 Kāla — Campaign Plan (DRAFT v0.1, Holistic Opening)

> **Status note.** This is a DRAFT. It is intentionally verbose. Nothing here is final until the
> frontmatter `status` flips to RATIFIED and the version reaches v1.0. Sections marked **[OPEN]**
> are unresolved design questions awaiting native decision; sections marked **[VERIFIED]** are
> code-grounded facts; sections marked **[CLAIM — UNVERIFIED]** are inherited from the handoff
> and NOT yet independently confirmed. The distinction is deliberate and load-bearing.

---

## §0 — How to read this document (and why it exists in this form)

This plan is authored **documentation-first**: the holistic vision is written down in full BEFORE
any asset is built, so that the reasoning, the alternatives considered, and the small nuances
survive into the build sessions. The MARSYS-JIS corpus has repeatedly shown that the expensive
failures are not big wrong decisions — they are *small correct facts that nobody wrote down*
(e.g. the L1 trap, the MSR drift, the Vimarśaka-RED commit violation, and — freshly — today's
finding that the L3 transit-search engine was never built despite the handoff claiming it exists).
This document is the antidote: a retention surface.

Each subsequent enhancement appends to the changelog with WHAT changed and WHY, so the document
is also its own discussion record.

---

## §1 — The mission (the one paragraph)

**Kāla = time.** L2 Bodha (SEALED 2026-06-20) holds what is *structurally* true about the chart —
signals, judgment, discoveries — with **no date attached** (timeless). **L3 Kāla is the temporal
layer: it activates L2's timeless structural promise across time and answers WHEN.** The canonical
query: *"When does my Lakshmi yoga next fire, auspiciously?"* — L2 says what the yoga IS and why it
matters; L3 says WHEN the transiting sky activates it.

**L3 also performs TEMPORAL DISCOVERY — the layer's deepest purpose (native framing, 2026-06-20).**
L3 superimposes L2's structural plane on the temporal plane to identify a *specific combination* —
of planets, conjunctions, houses, nakshatras, dashas, and other astrological factors — that marks
the **surgical moment to activate or deactivate an intervention** (astrological/remedial AND
material). This is the **opportunity the cosmos itself grants**: the window when a chosen activity
would be *fruitful* because the temporal alignment meets the structural promise. **L3 Kāla enables
the discovery of that appropriate intersection of the temporal and structural planes** — the
precise where-and-when at which acting (or refraining) is destined to bear fruit. The surgical
window is not merely "auspicious time in general"; it is auspicious *for this native, for this
specific intervention, because this structural promise meets this temporal trigger here*.

---

## §2 — The founding architectural principle (native-reasoned, LOCKED)

**Timing is SERVICES, not DATA.** A future transit position is continuous and infinite — you
cannot pre-store the chart state at every future instant. Therefore:

- **Natal / structural facts → STORED (finite).** L0 / L1 / L2. Done.
- **Transit positions at a future moment → COMPUTED ON DEMAND (a service).** The ephemeris.
- **"When does condition X hold in the future" → a SEARCH service over the ephemeris.** The hard,
  valuable part.

This is the architectural spine. Get it right and the rest follows. The native reasoned to exactly
the right architecture; this plan does not relitigate it.

**The promise-and-manifestation principle (native framing, 2026-06-20).** The natal/birth chart
gives you the **promise** — what is destined to be possible for this native. The *promise alone*
carries no date. It is the **interplay of the structural and temporal planes** that determines WHEN
that promise finds its **most suitable, opportune time to manifest**. **L3 Kāla enables
identification of that opportune window — the moment where the right time and the right structural
alignment COINCIDE at the same point** — so that interventions made there are fruitful. In one line:
*L0/L1/L2 hold the promise; L3 finds when the promise meets its hour.*

> **Nuance retained:** "services, not data" has a structural consequence the rest of the pipeline
> was NOT built for — see §5 (the service-asset model question). The principle is locked; its
> *implementation in the DAG/cockpit/orchestrator* is the open question.

---

## §3 — VERIFIED GROUND TRUTH (the engine audit, 2026-06-20) [VERIFIED]

The handoff and temporal-architecture docs claim *"L3 is mostly WIRING — the engines exist."*
**The audit found this is materially false.** This section is the corrected, code-grounded reality.
It is the most important section of this draft, because the entire wave plan depends on it.

| Engine | Handoff claim | **Verified reality (2026-06-20)** | Consequence |
|---|---|---|---|
| `pipeline/transit_search` — `find_aspect_events` / `find_conjunction_events` (the confluence-search heart) | "EXISTS ✓" | **Does not exist on ANY branch** (checked: main, feature/subsystem-transit, feature/panchanga-service-registry, feature/panchanga-rich-output). Only `routers/transit_search.py` exists, and it IMPORTS the missing module → would crash on import. A `PHASE_4D_TRANSIT_SEARCH_BRIEF` exists = **planned, never built**. | The single most valuable engine is a **from-scratch build**, not a wire-up. |
| `compute_transits` — `pyjhora_adapter/transits.py` (ephemeris-at-T) | "EXISTS ✓" | **Stub: `return {}`.** Same stub on feature/subsystem-transit. | The adapter the router/services expect is **empty**. |
| `scripts/temporal/compute_transits.py` | (not mentioned) | **REAL** — proper pyswisseph implementation (planet codes, sidereal, EXTERNAL_COMPUTATION_REQUIRED guard if pyswisseph absent). | The capability EXISTS as a standalone script but is **not wired into the adapter**. Dual-`compute_transits` authority ambiguity → a cleanup target. |
| Muhurat Finder — `muhurat/finder.py` | "EXISTS ✓" | **REAL ✓** — `score_muhurat`, `find_muhurat`, `find_muhurat_from_cache`; weighted tithi/nakshatra/vara/yoga; knockout for inauspicious; classically grounded (MC/BS/MMP/DP). | The auspiciousness-ranking layer is genuinely ready. |
| panchang engine — `panchang_engine/*` + `routers/panchang.py` | "EXISTS ✓, future-capable" | Real; BUT spread across **3 panchanga branches** (`-service-registry`, `-rich-output`, `l0fr-stream-e-panchanga-service`) — needs consolidation. | Real, but branch-sprawled → reconcile before building on it. |
| `ga_dashas` (the dated dasha timeline, ~536k rows) | "EXISTS ✓" | **REAL ✓** — registered writer (`@register('ga_dashas')`), writes rows. | The dasha-timeline temporal input is ready to be ACTIVATED. |

**Audit verdict:** L3 is **BUILD + WIRE**, not wire-only. Roughly half the named "existing"
machinery is real (muhurat, panchang, ga_dashas); the other half is brief-only (transit_search) or
stubbed (compute_transits adapter). **The hardest, most valuable component — the transit-search /
confluence engine — has never been built.** Any wave plan that scopes L3 as "wiring" is wrong.

### §3.1 — THE M3 TEMPORAL SUITE (a stranded prior generation the handoff never mentioned) [VERIFIED]
Deeper audit (2026-06-20, prompted by the native's "I don't see much reference to the Dasha
system") found an **entire prior-generation temporal engine** under `platform/scripts/temporal/`
that NEITHER the handoff NOR the temporal-architecture doc mentions:

| Script | What it is |
|---|---|
| `compute_transits.py` (`get_transit_states`) | **REAL** sidereal transit engine — positions of all 9 planets + **Sade Sati** state + eclipse-point proximity + nakshatra decomposition. (This is the real impl the adapter stub should wrap — resolves Q6.) |
| `compute_vimshottari.py` | **Vimśottarī** daśā computation |
| `compute_yogini.py` | **Yoginī** daśā |
| `compute_chara.py` | **Chara** (Jaimini) daśā |
| `compute_narayana.py` | **Nārāyaṇa** daśā |
| `compute_kp.py` | **KP** (Krishnamurti Paddhati) |
| `compute_shadbala.py`, `compute_varshaphala.py` | strength + annual (Varṣaphala) |
| `run_dasha_pipeline.py` | the daśā pipeline orchestrator (Vimśottarī + Yoginī live; Chara/Nārāyaṇa gated on a tradition-fork verdict) |
| **`signal_activator.py`** | **A V1 OF THE ACTIVATION BRIDGE ITSELF.** Joins (active Vimśottarī MD+AD at query_date) × (transit state) × (each signal's `entities_involved`) → emits **lit / ripening / dormant** per signal. "lit" = active MD or AD lord ∈ entities_involved; "ripening" = next AD lord within 90 days OR a transit planet in an involved sign; flat 0.6 confidence (uncalibrated, deterministic). |
| `bulk_signal_activator.py` | batch form of the above |

**This reframes the whole campaign.** The activation bridge the architecture doc calls "the core
MISSING piece" is **not missing — there is a working v1** (`signal_activator.py`). Its limitations:
(a) reads MSR from **markdown (MSR_v3_0.md)**, not the DB (so it predates the L1/L2 DB-native
rebuild); (b) **Vimśottarī-only**; (c) **flat 0.6 confidence**, uncalibrated; (d) **not wired to the
orchestrator** or the L2 `signature_class`/NULL hooks. So L3 is precisely: **MODERNIZE + INTEGRATE +
EXTEND** a stranded prior generation — neither "build from scratch" nor "just wire."

> **Why this was hidden:** these scripts are M3-era (per their own docstrings: "M3-W2-B2
> deliverable", `PHASE_M3_PLAN_v1_0.md` references). The L1/L2 rebuild superseded the data plane but
> **left this temporal work stranded** — and the L3 handoff/architecture docs were authored without
> auditing `scripts/temporal/`. The native's instinct that "Dasha is under-represented" caught a
> real, large omission. **Cleanup/integration item: decide what of the M3 suite is salvageable vs.
> rebuilt** (it reads stale markdown MSR and uses pre-DB conventions, but the *astronomical*
> computation — swisseph daśā/transit math — is likely sound and reusable).

> **Why this matters for the approach:** the native's instinct to AUDIT FIRST is exactly what
> caught this. Had the holistic opening proceeded on "just wire it," the campaign would have
> under-scoped the layer by its single most important engine.

---

## §4 — The two planes (the query decomposed) — and the coupling question [OPEN — investigation]

"When is the next auspicious moment my Lakshmi yoga fires?" lives on TWO planes:

- **STRUCTURAL (timeless):** what IS Lakshmi yoga in this chart — constituents, strength, state,
  what "firing" means. → **L2 Bodha (+ L1). BUILT ✓.**
- **TEMPORAL (time):** at what future DATE do transiting planets / the active dasha reach the
  activating positions. → **L3 Kāla + temporal services.** Partially built (see §3).

The full answer needs BOTH planes together. This is the L2↔L3 seam the project deliberately
protected: L2 stayed timeless, and reserved the L3 attachment points. §6 is where they pay off.

> **Correction from v0.1 (native challenge, 2026-06-20).** v0.1 called these "two perpendicular
> axes." That asserted a geometric (orthogonal = independent) relationship I cannot support. The
> honest statement: **they are two planes; whether they are orthogonal/independent or have a real
> coupling is an OPEN empirical question (investigation item).** There is already reason to suspect
> they are NOT independent: **the Vimśottarī Daśā sequence is DERIVED FROM the natal Moon's
> nakshatra** — a structural fact. So the temporal axis is partly *born from* the structural one;
> the planes share a root. That is a coupling, not orthogonality. **Investigation item I-1:**
> characterize the coupling between the structural and temporal planes (the dasha-from-nakshatra
> derivation is the first concrete evidence of non-independence; are there others — e.g. transit
> effects modulated by natal dignity?). This matters because if the planes are coupled, the
> intersection search (§5.1) is not a naïve AND of two independent conditions — the structure may
> *shape* which temporal triggers are even eligible.

---

## §5 — THE HOLISTIC OPENING: where L3's value concentrates, and the layer-shaping decisions

This is the heart of the holistic phase: before defining assets, decide what the layer is FOR and
what shape it must take. Five layer-shaping questions, each with the current thinking and an
explicit OPEN flag where a native decision is required.

### §5.1 — Where the value concentrates (the thesis — sharpened by the native, 2026-06-20)
L3's value is NOT "compute a transit." Anyone can do that. **L3's value is the ability to identify
the INTERSECTION of the structural plane and the temporal plane that is conducive to — or destined
for — a certain event.** That intersection IS the product. And the intersection is, by its nature,
**simultaneously a specific point in TIME and a specific STRUCTURAL alignment** — you find it
precisely by locating where a temporal trigger coincides with a structural promise. The mechanism
that finds it is the **CONFLUENCE / INTERSECTION SEARCH**: the rare future moment where MULTIPLE
conditions hold AT ONCE — yoga-lord transit + supportive dasha + auspicious panchanga + no
affliction + (any other coupled subsystem condition). The rarity IS the value: no human can scan
decades across all conditions simultaneously. Everything else in the layer (the ephemeris service,
the dasha engine, the event vocabulary, the subsystem reads) exists to FEED this intersection
search. **The plan invests hardest here, exactly as L2 invested hardest in the graph.**

> **Framing nuance retained:** "find the intersection" and "find the surgical opportune window"
> (§1) and "when the promise meets its hour" (§2) are THREE statements of ONE idea. The deliverable
> is a *located intersection point* — a (time, structural-alignment) pair, ranked, provenanced, with
> its structural reasoning (L2) and its temporal proof (the computed alignment).

### §5.2 — The activation-predicate bridge (THE CRUX) [OPEN — load-bearing]
The whole layer hinges on one deterministic question: **how does an L2 `signature_class` yield a
transit/dasha condition that "fires" the pattern?** Example target behavior: *"Lakshmi yoga fires
when its lord transits a kendra/trikona during a supportive dasha, free of affliction."* The bridge
reads the L2 `signature_class` + the L0 classical transit/dasha rules (`bg_transit_rules`) → derives
the predicate → hands it to the (to-be-built) transit-search engine.
- **Open question:** is the mapping `signature_class → predicate` a finite lookup table (one rule
  per signature_class, authored from classical sources), a parameterized rule template, or a
  derivation? Determinism is mandatory (no LLM in the build), so it must be one of the first two.
- **Decision needed before K1.** This is the single most important design artifact of the layer.

### §5.3 — The service-asset model [RESOLVED 2026-06-20 — native ratified A+C, both in-layer]
"Services, not data" collides with the existing pipeline, which assumes **stored row-assets**
(cockpit, radial-constellation DAG, orchestrator `WriterBase`, idempotency delete-then-insert,
`count_sql` on `asset_registry`). A service (callable, no rows) has no row count and no stored
output.

**RESOLUTION (native, 2026-06-20): Option A as the spine + Option C's artifact — BOTH inside L3.**
A service is an **independent, first-class asset WITHIN the layer** (this is how prior layers
already treated the panchanga and transit services — services as in-layer assets, not external
plumbing). It is simply NOT a data-storage asset. Concretely:
- **The services** (transit-search, the ephemeris-at-T service, the confluence search, the dasha
  engine) register as first-class **`ka_*` SERVICE-assets within L3.** They have **no `count_sql` /
  no row store.** The cockpit renders them with a **SERVICE HEALTH model** (registered /
  last-invoked / self-test pass) instead of a row count.
- **Plus one thin `ka_*` ARTIFACT-asset** (Option C) that DOES store rows: the derived activation
  predicates (one per matchable `signature_class`) and the **memoized activation windows that fill
  L2's reserved NULL hooks** for the native chart. This is the "asset that has leveraged the
  service" the native intuited — a stored asset *fed by* the services.

**Net:** not A-vs-C — **A for the services, C for the one artifact they produce; everything stays
inside L3.**

> **Native's clarifying correction (recorded):** Cowork's v0.1 phrase "keep the service outside the
> layer" was wrong/ambiguous. A service is unambiguously an **L3 asset** and stays IN L3. "Outside"
> only ever meant *outside the row-store DATA model* — i.e. a service-type asset, not a
> table-with-rows asset. The native is right; this is corrected.

**New infra need (the one genuinely new piece):** the cockpit/DAG must learn a **"service asset"
type** — a node that registers and shows a health/last-invoked/self-test status but has no row
count and no `count_sql`. This is a small, real design addition (flag for the cockpit brief). It
does NOT change the FROZEN orchestrator contract for the artifact-asset (that one is a normal
`WriterBase`); the service-assets may need a parallel lightweight "service registration" path —
**investigation item I-2: define how a service-asset registers vs. the orchestrator's writer
contract** (does a service get a no-op writer that self-tests, or a separate registry?).

### §5.4 — Eval: the COMPUTATIONAL/PREDICTIVE split [RESOLVED 2026-06-20 — native ratified the split]
"Eval" bundles two different questions that the native and Cowork separated explicitly:

1. **Computational correctness** — *"Does the machine compute what it claims?"* Did the transit
   engine put the planet where it actually was? Does the activation predicate fire on a kendra
   transit and not misfire? Knowable TODAY, no reference to the native's life; verified by
   reproducing known ephemeris positions + checking predicate logic against classical rules.
2. **Predictive accuracy against reality** — *"Was the prediction TRUE?"* Did the opportune window
   L3 named correspond to a fruitful event in the native's life? Knowable only by calibration
   against **lived reality (the LEL)**, often only after the predicted time passes.

**RESOLUTION (native, 2026-06-20, made with full information after debating "all-to-L5"):**
- **Computational correctness (#1) → STAYS IN L3** as a B6-style **seal gate**, parallel to L1
  FORENSIC 7/7 and L2 B6 35/35. *Rationale:* every prior layer self-verified its own machinery
  before sealing; a bug caught at the layer that produced it is cheap, three layers downstream it
  is expensive and ambiguous. Critically — **this keeps L5's later calibration interpretable:** when
  L5 sees a bad prediction, the L3 gate guarantees it's a real MODEL failure, not a plumbing bug.
  Without it, L5 cannot tell "wrong astrology" from "off-by-one transit engine," and its learning
  becomes uninterpretable.
- **Predictive accuracy (#2) → GOES TO L5 Mīmāṃsā.** L3 MAKES falsifiable, datable predictions; L5
  JUDGES them against the LEL and calibrates confidence. This honors the make/validate separation
  (B.1): producers produce, the validator validates *truth-in-the-world*.

> **Decision record:** the native initially chose "ALL eval to L5" (layer-purity instinct — keep
> all judging in the validation layer). On a second pass, Cowork distinguished the two eval types
> and presented the strongest case for the split AND for all-to-L5. The native, now fully informed,
> ratified **THE SPLIT** (computational in L3, predictive in L5). The layer-purity concern is
> honored because L3's gate is about *its own machinery*, not about *truth* — truth stays L5's.

**Design consequence (let it pull the build):** L3 must carry a **computational eval gate** — the
activation predicate is testable by reproducing KNOWN PAST activations (e.g. a dated LEL event whose
structural pattern + transit/dasha at that date should make the predicate fire). This forces the
bridge to be *constructed testably* from day one. The eval criteria are sketched now, in the
holistic phase, so they shape the design rather than being retrofit at seal.

### §5.5 — Cleanup mandate, made concrete [OPEN — scope]
The native's "clean up the mess" applies to specific, audited debris:
- **Branch sprawl** — `feature/subsystem-transit` + 3 panchanga branches carry overlapping
  temporal work. Reconcile/consolidate BEFORE L3 builds on them, or L3 forks the mess.
- **The crashing router** — `routers/transit_search.py` imports a non-existent module; it is
  dead/broken on main-line branches right now. L3 either builds the module or removes the router.
- **Dual `compute_transits`** — real script (`scripts/temporal/`) vs. stub adapter
  (`pyjhora_adapter/`). Consolidate to one authority (the corpus warns against exactly this kind
  of authority ambiguity).
- **L2 carry-in:** `bo_samskara` shipped a **placeholder hash, not real Vertex embeddings** —
  semantic retrieval quality is unverified. If L3's retrieval review (step 5) leans on semantic
  search, this is a hidden dependency. Decide: inherit as known-gap, or fix.

### §5.6 — THE TEMPORAL PILLARS: Daśā, Panchāṅga, and embedded-subsystem leverage [native-raised, central]
The native raised three concerns (2026-06-20) that the audit confirms are first-order, not
footnotes. The architecture docs under-scoped all three. This section promotes them to **design
pillars.**

**Pillar 1 — DAŚĀ is a co-equal temporal engine, not a one-liner.**
The architecture doc reduced daśā to *"is the dasha supportive at moment T."* That is a severe
under-scoping. **The daśā system is arguably the PRIMARY indigenous "WHEN" of Jyotish** — the
unfolding of the natal promise *from within*, over named periods (Mahādaśā → Antardaśā →
Pratyantardaśā → …), across MULTIPLE systems (Vimśottarī, Yoginī, Chara, Nārāyaṇa, KP — all already
computed in the M3 suite, §3.1). The right model:

> **L3 has TWO temporal sub-engines, co-equal:**
> - **DAŚĀ** — activation *from within* (the promise unfolds on its own clock; nakshatra-derived).
> - **TRANSIT** — activation *from without* (the moving sky triggers the natal pattern).
> The intersection/confluence (§5.1) is where **BOTH temporal engines meet the structural plane.**

How elaborately L3 leverages daśā is itself a deep design question (investigation item **I-3**):
which daśā systems; how many nested levels (MD/AD/PD/…); how daśā-lord ↔ signal-entity matching
generalizes beyond `signal_activator.py`'s v1; whether multiple daśā systems must *agree* for high
confidence (a cross-daśā confluence — a discovery axis in itself). `ga_dashas` (536k dated rows)
already holds the timeline; the M3 `compute_*` scripts already compute the systems. **The build is
to ELEVATE daśā to a pillar, integrate it DB-native, and make daśā↔structure matching rich.**

**Pillar 2 — PANCHĀṄGA qualifies time in astrologically meaningful ways (research item).**
The native asked to *deeply research how Panchāṅga adds value, or not.* The audit shows its value is
**already proven in code** (Muhurat Finder), on at least three distinct axes:
1. **Qualifying abstract time astrologically** — tithi / nakshatra / vara / yoga / karaṇa turn a
   bare date into an astrologically-typed moment (auspicious/inauspicious for an activity-class).
2. **Native-specific overlay via TĀRA BALA** — `score_muhurat` overlays the *native's* birth
   nakshatra against the day's nakshatra (`compute_tara_bala_score`). This is the bridge from
   "auspicious in general" to "auspicious **for THIS native**" — exactly the §1 surgical-window
   idea. **This is panchāṅga's deepest contribution to L3.**
3. **The inauspicious KNOCKOUT** — `_in_inauspicious` zeroes a window regardless of other scores
   (e.g. a compound-inauspicious combination vetoes the moment). A safety floor on "do not act here."
**Research item I-4 (the native's ask):** a dedicated deep-research pass on panchāṅga's full value
surface for L3 — beyond the three above (e.g. hora, choghadiya, the muhurta sub-divisions, eclipse
windows) — and which belong in the confluence score vs. as knockouts vs. as native-overlay.

**Pillar 3 — L3 must systematically leverage EVERY embedded subsystem with a temporal dimension.**
The native's assumption — *"the Kāla layer leverages the subsystems we embedded (nakshatra, vastu,
…); if we're not, we're missing an important factor"* — is correct and partially realized:
- **Already in the temporal path:** nakshatra (via Tāra Bala + transit nakshatra decomposition),
  yoga (via panchāṅga special-yogas), Sade Sati (computed in the transit engine).
- **NOT yet in the temporal path (the gap the native sensed):** the **dignity** subsystem (does
  transit effect get modulated by natal/transit dignity?), **astrovāstu/remedial** (the surgical
  window for a *remedial/vāstu* intervention — directly serves §1's "activate/deactivate
  interventions"), the embedded **nakshatra subsystem** (`bg_nakshatra`/`ga_nakshatra`) as a
  first-class L3 input, **medical** (timing of health-domain interventions), and **prashna**
  (chart-type, if a temporal query is itself a prashna).
> **Design principle (ratified intent):** **L3 pulls every embedded subsystem that has a temporal
> dimension — not only the ones the M3 scripts happened to wire.** Where a subsystem reaches L3,
> it arrives through L2's structural plane (the subsystem facts are already in L1/L2). Investigation
> item **I-5:** enumerate, per embedded subsystem, its temporal contribution to the intersection
> search (a coverage matrix: subsystem × {confluence-condition / native-overlay / knockout / none}).

### §5.7 — THE CONVERGENCE MACHINERY (how we leverage daśā + panchāṅga + subsystems to find the intersection) [holistic core, native-shaped 2026-06-20]

This section answers the native's direct question — *how do we actually leverage Daśā, Panchāṅga,
and the other subsystems to surgically find the intersection, and what infrastructure makes that
discovery efficient?* It is the holistic heart of L3.

#### §5.7.1 — Three planes, not two (the corrected model)
The intersection is a convergence of **THREE** planes operating at **three different timescales** —
and the timescale difference is the key to efficiency:
1. **Natal / structural plane (timeless)** — the promise. L2 holds it. *Fixed.*
2. **Daśā plane (temporal-from-WITHIN)** — which part of the promise is "switched on." *Derived from
   the natal Moon's nakshatra (hence coupled to structure, I-1); moves over YEARS; tells you WHAT
   THEME is live.*
3. **Transit + panchāṅga plane (temporal-from-WITHOUT)** — the moving sky. *Fast (transit:
   weeks–months; panchāṅga/muhūrta/horā: hours); transit says which natal point is struck NOW,
   panchāṅga says whether this hour is FIT to act.*

So L3 has **two co-equal temporal sub-engines** — **Daśā (from within)** and **Transit+Panchāṅga
(from without)** — and the intersection is where **both** meet the **structural** promise.

#### §5.7.2 — The machine: a coarse→fine FUNNEL, but with a SOFT prior, not a hard gate [native correction]
The planes move at different speeds, so the efficient machine uses the SLOW planes to focus the
FAST ones. But — **critical native correction (2026-06-20)** — daśā must be a **SOFT PRIOR, not a
HARD GATE**, because *an event can fire OUTSIDE its likely daśā when another factor (an exceptionally
strong transit, a rare conjunction, a return, an eclipse on a sensitive point) overpowers the
missing daśā support — and THOSE off-daśā activations are exactly the high-value intersection points
we most want to discover.* A hard gate would silently amputate the discovery mission. Therefore the
machine runs **TWO search modes together:**

**MODE A — EXPECTED intersections (daśā-prior funnel; cheap; the "likely" windows):**
- **Stage 1 — Daśā prior (coarse, decade→months).** From an L2 signal's `signature_class`, ask the
  daśā timeline (`ga_dashas`, already computed): which periods make this promise *eligible / likely*
  to fire? Collapses decades → a few month-to-year windows. A cheap lookup, no ephemeris scan. *This
  is why daśā is the primary engine — it does the brutal first cut.*
- **Stage 2 — Transit search (medium, within each window; months→days).** Only inside surviving
  windows, run transit-search: when does the activating planet reach the trigger (aspect /
  conjunction / ingress / return / station)? Narrows months → candidate days.
- **Stage 3 — Panchāṅga + muhūrta refine (fine, within each day; days→hours).** Score the day's
  panchāṅga (tithi/nakshatra/vara/yoga/karaṇa), apply the **Tāra Bala native overlay** (favorable
  *for THIS native*), find the muhūrta/horā — the auspicious hours. Narrows days → the surgical hour.
- **Stage 4 — Knockout / affliction veto (any stage).** Veto candidates hitting a hard inauspicious
  condition (muhūrta knockout, affliction to the relevant house/lord, eclipse, malefic over trigger).

**MODE B — ANOMALOUS intersections (the DISCOVERY engine; un-gated by daśā):**
- A coarse sweep for **rare, HIGH-MAGNITUDE** transit/conjunction/return/eclipse confluence — NOT
  filtered by daśā. For each hit, it then *checks* daśā (rather than being gated by it) and **flags
  the ones that cross the activation threshold DESPITE a dormant/unsupportive daśā** as high-value
  discoveries (high non-obviousness — the temporal twin of L2 `bo_anveshana` anomalies).
- **Stays tractable** because Mode B searches only for *rare high-magnitude* configurations (a coarse
  magnitude threshold), not every hour. So we keep efficiency AND we never blind the machine to the
  off-daśā discoveries that are its highest purpose.

> **Why the funnel order is the MACHINERY, not just an optimization:** the slowest plane carries the
> most meaning about *whether*; the fastest about *exactly when*. Daśā = "is this your season for the
> thing?"; transit = "which week does the trigger land?"; muhūrta = "which hour to act?". The funnel
> mirrors how a real acharya reasons — acharya-cognition made exhaustive. Mode B is what an acharya
> *cannot* do by hand: scan decades for the anomalous overpowering confluence.

#### §5.7.3 — STRENGTH coupling (structure modulates the temporal trigger's FORCE) [native delegation]
Per the native (2026-06-20): the *degree* to which each factor influences an activation — and
specifically how **dignity / shadbala** scales a trigger — is delegated to **Cowork's astrological
domain reasoning** as the LLM, not pre-specified by the native. The model: **a trigger's activation
FORCE is modulated by the dignity/strength of the planet involved** — a dignified/strong trigger
fires strongly; a debilitated/weak one fires weakly (and may need Mode-B-level magnitude to register
at all). This IS the structure×time coupling (§4): the intersection score is not a naïve AND of
binary conditions; it is a *weighted convergence* where structural strength scales temporal triggers.
- **Guardrail (corpus discipline, [[feedback-canonical-or-floor-rule]]):** every influence-weight
  Cowork assigns is a **stated, versioned, CITABLE judgment** (classical reasoning + source), proposed
  to the native, ratified, then frozen as a versioned formula parameter. *Weights are judgments; their
  APPLICATION is deterministic.* No silent magic numbers. (The "normalize, never re-pick; halt for
  sign-off" rule.) → investigation/authoring item **I-7: the influence-weight model** (per factor:
  classical rationale, source, proposed weight, normalization).

#### §5.7.4 — Where every subsystem plugs in (the coverage matrix, I-5 made concrete)
| Subsystem | Stage | Role |
|---|---|---|
| **Daśā** (Vimśottarī / Yoginī / Chara / Nārāyaṇa / KP) | 1 | The coarse PRIOR. **Cross-daśā agreement** (multiple systems concur a period is live) = confidence amplifier; **cross-daśā disagreement / single-system-only** = a discovery flag. |
| **Transit** (graha gochara) | 2 | The medium trigger search. |
| **Nakshatra** | 2–3 | Transit-nakshatra trigger (2) + **Tāra Bala native overlay** (3) — makes the window native-SPECIFIC. |
| **Yoga** (panchāṅga + chart yogas) | 3 + 1 | Panchāṅga special-yogas score the day; chart-yoga promises are Stage-1 targets. |
| **Panchāṅga / Muhūrta / Horā** | 3 | The fine sieve — qualifies the hour. |
| **Dignity / Shadbala** | modulates 2 | Scales trigger FORCE (§5.7.3) — the structure×time coupling. |
| **Sade Sati / transit-affliction** | 4 | Knockout / dampener. |
| **Astrovāstu / remedial** | consumes output | Says WHAT intervention to do in the found window (§1 activate/deactivate). |
| **Medical** | 1 target + 4 | Health-domain promises as targets; health-affliction windows as vetoes. |
| **Prashna** | meta | If the query is itself a prashna, the asking-moment becomes an input chart. |

#### §5.7.5 — The infrastructure this implies (the asset reconciliation preview)
The machinery = **five service-assets + one artifact-asset** (the §5.3 A+C model). This is the
preview of the asset reconciliation (approach step 2); detailed per-asset later.
1. **Ephemeris-at-T service** — positions at any moment (modernize M3 `get_transit_states`).
2. **Daśā-timeline service** — "which periods are live/likely for signature X" (the coarse prior;
   wraps the M3 daśā suite + `ga_dashas`; multi-system).
3. **Transit-search service** — "when does trigger condition hold" (the unbuilt heart — BUILD;
   event vocabulary aspect/conjunction/ingress/return/station; serves Mode A and Mode B).
4. **Panchāṅga / muhūrta service** — "score this day/hour for THIS native" (modernize the real
   Muhurat Finder; Tāra Bala overlay).
5. **The CONVERGENCE engine** — the FUNNEL orchestrator running Mode A (daśā-prior cascade) + Mode B
   (anomaly sweep) with strength-modulation + knockout vetoes → ranked intersection points. **The
   new valuable core.**
6. **The activation-artifact asset** — stores the derived predicates (per `signature_class`) + the
   memoized intersection windows that fill L2's NULL hooks. *(The one stored asset.)*

The **activation-predicate bridge** (Q2) is the glue from L2 to stages 1–2: it reads a
`signature_class` and emits BOTH the daśā-eligibility prior (stage 1) AND the transit-trigger
condition (stage 2). `signal_activator.py` v1 already does a primitive form (daśā-lord ∈
`entities_involved` → "lit") — we generalize it and add the strength modulation + Mode B.

The two-plane discipline maintained throughout L2 is exactly what makes L3 clean. Verified in the
actual writer code (`bo_laksana.py`):

- **`signature_class`** on natal patterns — the matchable fingerprint L3's activation predicate
  keys on. *(Stored NULL today; populated by L2; the bridge reads it.)*
- **The NULL L3-fill hooks** — `active_dasha_periods_jsonb`, `activation_predicted_dates_jsonb`,
  `dasha_activation_proximity_score`. Written NULL by L2 (confirmed at `bo_laksana.py` lines ~760,
  ~792); **L3 fills them** — in L3 artifacts that REFERENCE the L2 `signal_id`. **L3 NEVER writes
  back into L2's timeless tables.**
- **The `bo_anveshana` falsifiable-hypothesis hooks** — L3 activations become datable predictions
  that L4 Phala / L5 Mīmāṃsā validate.
- **`resonance_eligible` patterns** — the yogas/configs that CAN be transit-activated = L3's search
  targets.

> **Nuance retained:** the NULL hooks being NULL is not an oversight — it is the *reserved surface*.
> A future session must not "helpfully" populate them in L2; that would collapse the two planes.

---

## §7 — Temporal discovery = the discovery engine applied to TIME (the deep connection)

"Discover rare opportune moments" = `bo_anveshana`'s discovery mission projected onto the TEMPORAL
axis. Structural discovery (L2) finds the consequential pattern in the static chart no acharya sees;
**temporal discovery (L3) finds the rare FUTURE MOMENT when the transiting sky activates a
consequential natal pattern** — the opportune window no acharya could compute by hand. Cross-subsystem
discovery = discovery ACROSS disciplines; opportune-moment discovery = discovery ACROSS time. Both
find the confluence a human cannot hold. L3's discovery output should be **first-class, ranked, and
provenanced**, exactly as L2's discoveries are.

---

## §8 — The wave plan (DRAFT — revised from the handoff's K0–K5 to reflect the audit)

The handoff proposed K0–K5 assuming "wiring." The audit forces a build-inclusive revision. This is
a DRAFT shape, to be detailed per-wave after the §5 OPEN questions are resolved.

```
K0  CLEANUP + WIRE-UP FOUNDATION
    - Reconcile the transit/panchanga branch sprawl (§5.5) into a clean base.
    - Consolidate compute_transits: promote the real scripts/temporal impl into the adapter;
      remove or quarantine the stub. One authority.
    - Decide + scaffold the service-asset model (§5.3) so later waves have a home.

K1  THE TRANSIT-SEARCH ENGINE  (BUILD — not wire; the audit's correction)
    - Build pipeline/transit_search: find_aspect_events + find_conjunction_events over the
      (now-real) ephemeris service. The PHASE_4D brief is the starting spec.
    - Make routers/transit_search.py actually importable (close the crashing-router debt).

K2  THE ACTIVATION-PREDICATE BRIDGE  (BUILD — the crux, §5.2)
    - L2 signature_class + L0 transit/dasha rules → activation predicate.
    - The signature_class→predicate mapping (lookup table vs. template — §5.2 decision).

K3  EVENT VOCABULARY + DASHA-TIMELINE ACTIVATION
    - Extend beyond aspect/conjunction: ingress, dasha-boundary, return, transit-over-natal-point,
      station/retrograde.
    - Wire the ga_dashas dated timeline as a temporal input ("is the dasha supportive at moment T").

K4  THE CONFLUENCE SEARCH  (BUILD — the valuable heart, §5.1)
    - AND over event searches + muhurat score → rare opportune moments.
    - query_auspicious_timing(chart, target_pattern, window) → ranked moments, each with its
      STRUCTURAL reasoning (L2) + TEMPORAL proof (the transit calc).

K5  TEMPORAL DISCOVERY  (§7)
    - The discovery engine applied to time: opportune moments as first-class, ranked, provenanced.

K6  RETRIEVAL + EVAL + SEAL
    - Retrieval tools review (step 5 of the approach).
    - The timing-query eval corpus (§5.4), falsifiable vs. LEL when enabled.
    - L3_KALA_CLOSE + the L4 Phala onboarding contract. Clean seal.
```

> **Changed from handoff:** the handoff's K0–K5 folded the transit-search engine into "wiring."
> This draft splits out **K0 cleanup** and **K1 build the engine** as distinct, real work, because
> the audit proved the engine does not exist. The confluence search (handoff K3) is preserved as
> the valuable heart (here K4).

> **v0.2 wave-plan caveats (to be detailed once §10 investigation items close):**
> - The §3.1 finding (the M3 temporal suite + `signal_activator.py` v1) means K1/K2 are
>   **MODERNIZE+INTEGRATE+EXTEND**, not pure build — start from the M3 swisseph math, port DB-native.
> - **DAŚĀ is a co-equal pillar (§5.6 P1):** the wave plan needs an explicit daśā-engine track
>   (integrate the M3 `compute_*` daśā scripts DB-native; elevate daśā↔structure matching) running
>   alongside the transit track — the confluence (K4) consumes BOTH.
> - **The eval gate (split, §5.4):** K6 carries L3's COMPUTATIONAL eval gate (reproduce known past
>   activations); predictive calibration is explicitly DEFERRED to L4/L5, not built here.
> - **Coarse-to-fine search (Q7):** K4 must not inherit the ±10yr cap as a hard wall.

---

## §9 — Standards L3 inherits (same as every layer) [VERIFIED against CLAUDE.md §N]

- **Deterministic-first** — ephemeris + search + muhurat are deterministic; **no generative LLM in
  the build.** "Improvisation" (native's word) = creative latitude in SHAPING the layer, NOT
  loosening the determinism gates.
- **FROZEN orchestrator contract** — `ka_*` writers are `@register` `WriterBase` subclasses, run on
  `ctx.db_conn` and **NEVER commit/close it** (heed the L2 Vimarśaka-RED lesson: 6 of 10 bo_ writers
  had to be remediated for exactly this — see L2_BODHA_CLOSE §10). For service-assets, the contract's
  applicability is part of the §5.3 decision.
- **Anti-drift** — L3 artifacts REFERENCE L2 `signal_id`s + L1/ephemeris facts; never restate. Every
  L3 claim carries a `DERIVATION_LEDGER` entry (B.3).
- **The LEL toggle** — L3 honors `lel_enabled` + `lel_origin`; timing is calibrated by LEL only when
  enabled (see LEL_TOGGLE_GOVERNING_PRINCIPLE).
- **PROD-VERIFY** — ACs verify against PROD, not a worktree DB (the Brahma V1.3 lesson). FORENSIC
  holds. Only chart `482012f1`.
- **Naming** — prefix `ka_*`; tables `kala_*`.

---

## §10 — OPEN QUESTIONS REGISTER (tracked, not dropped)

| # | Question | Where | Owner | Status |
|---|---|---|---|---|
| Q1 | Service-asset model | §5.3 | native | **RESOLVED 2026-06-20 — A+C, both in-layer; cockpit gains a service-asset type** |
| Q2 | `signature_class → predicate` mapping: lookup table vs. template vs. derivation? | §5.2 | native + design | OPEN — but `signal_activator.py` v1 gives a working precedent (daśā-lord ∈ entities_involved) |
| Q3 | Eval placement & criteria | §5.4 | native | **RESOLVED 2026-06-20 — THE SPLIT: computational eval (B6-style gate) in L3; predictive calibration vs. LEL in L5** |
| Q4 | `bo_samskara` placeholder embeddings — inherit as known-gap or fix in L3? | §5.5 | native | OPEN — native is addressing (update pending) |
| Q5 | Branch reconciliation order — which of the temporal branches is the clean base? | §5.5, K0 | Cowork judgment | OPEN — Cowork to determine after fuller branch-content audit; lean: panchāṅga branches consolidate first (most-real, most-depended-on), then transit |
| Q6 | Real `compute_transits` vs. adapter stub | §3.1, K0 | design | **RESOLVED 2026-06-20 — real impl is `scripts/temporal/compute_transits.py:get_transit_states`; the `pyjhora_adapter` stub must wrap/replace it. A SHIM is needed: signatures differ (`get_transit_states(birth_dt, query_date)` vs. `compute_transits(jd_ut, …)`)** |
| Q7 | Search-window cap (the ±10yr latency guard) | §8 K4 | native | OPEN — **impact clarified (see below); Cowork view: the cap THREATENS the core value** |

**Q7 explained (the native asked for the question + its impact).** The existing transit-search
router hard-caps any search window at **±10 years** — a *latency guard*, because scanning the
ephemeris day-by-day over a longer span is slow. **The impact:** confluence/intersection moments
(the rare alignments that are L3's *entire value*, §5.1) may be **decades apart**. With a 10-year
cap, L3 **structurally cannot find a once-in-30-years opportune window** — the product's most
valuable output is silently excluded by a performance guardrail. **Cowork's view:** the cap is a
real threat to the core value; the fix is not a bigger number but a **coarse-to-fine search** (scan
decades cheaply at low resolution to find candidate regions, then refine each hit to exact
precision), so rarity is never capped away. **Native decision needed:** accept coarse-to-fine as
the K4 design constraint?

### Investigation items (Cowork-owned, feed later draft passes)
| # | Item | Where |
|---|---|---|
| I-1 | Characterize the COUPLING between structural & temporal planes (daśā-from-nakshatra is first evidence of non-independence; find others, e.g. dignity-modulated transit) | §4 |
| I-2 | Define how a SERVICE-asset registers vs. the FROZEN orchestrator writer contract (no-op self-testing writer, or separate service registry?) | §5.3 |
| I-3 | How elaborately L3 leverages DAŚĀ — which systems, how many nested levels, cross-daśā agreement as a confidence/discovery axis | §5.6 P1 |
| I-4 | DEEP RESEARCH: panchāṅga's full value surface for L3 (hora, choghadiya, muhurta sub-divisions, eclipse windows) — confluence-score vs. knockout vs. native-overlay | §5.6 P2 |
| I-5 | Subsystem × temporal-contribution COVERAGE MATRIX (nakshatra/dignity/vāstu/medical/prashna/yoga × {confluence / native-overlay / knockout / none}) | §5.6 P3 |
| I-6 | Salvage assessment of the M3 `scripts/temporal/` suite (which is reusable DB-native vs. rebuilt) | §3.1 |
| I-7 | The INFLUENCE-WEIGHT model — per factor (daśā/transit/dignity/panchāṅga/…): classical rationale + source + proposed weight + normalization; Cowork proposes, native ratifies, frozen as versioned formula params | §5.7.3 |
| I-8 | The Mode-B ANOMALY magnitude threshold — what counts as a "rare high-magnitude" configuration worth an un-gated sweep (keeps Mode B tractable AND catches off-daśā discoveries) | §5.7.2 |

---

## §11 — Discussion record (the retention log)

- **2026-06-20** — Native ratified the 6-step approach (audit → holistic → asset set → per-asset →
  holistic close → retrieval → clean seal) and the documentation-first discipline ("document in
  detail from the very beginning … nuances could be critical in nature"). Output mode = authored
  .md artifacts/briefs (Cowork→Antigravity split).
- **2026-06-20** — Cowork ran the ground-truth engine audit (§3). Finding: handoff's "engines exist,
  just wire" is materially false; transit-search never built, compute_transits adapter stubbed.
  L3 reclassified as BUILD + WIRE.
- **2026-06-20** — This draft (v0.1) authored as the holistic opening.
- **2026-06-20 (v0.2 session)** — Native enhancement pass. Native added the temporal-discovery /
  surgical-intervention-window framing (§1), the promise-and-manifestation principle (§2),
  challenged "perpendicular" (§4 → coupling investigation), and sharpened the value thesis to "the
  structural×temporal INTERSECTION point" (§5.1). Native corrected the service-model wording (a
  service is an IN-LAYER asset) → Q1 resolved A+C. Native raised the **Daśā/Panchāṅga/subsystem
  under-representation** concern → Cowork audited `scripts/temporal/` and found the **M3 temporal
  suite + `signal_activator.py` v1** (§3.1); the three concerns promoted to **pillars** (§5.6).
  Eval debate: native first chose all-to-L5, then (fully informed, after Cowork distinguished
  computational vs. predictive eval) ratified **THE SPLIT** (§5.4). Q6 resolved (real
  compute_transits found). Q7 (window cap) explained + impact flagged. Investigation items I-1…I-6
  registered.
- **2026-06-20 (v0.3 session)** — The CONVERGENCE MACHINERY (§5.7), in answer to the native's "how
  do we leverage Daśā/Panchāṅga/subsystems to find the intersection, efficiently?" Native's brain
  dump (three planes' factors must converge; need efficient discovery infrastructure) reflected +
  refined to a **THREE-plane model** (structural / daśā-from-within / transit+panchāṅga-from-without
  at three timescales). Cowork proposed the **coarse→fine FUNNEL** (slow planes focus fast ones).
  **Native's key correction:** daśā must be a **SOFT PRIOR, not a HARD GATE** — events fire OUTSIDE
  likely daśā when another factor overpowers it, and those off-daśā activations are the highest-value
  discoveries. → adopted **TWO search modes**: Mode A (daśā-prior funnel, expected) + Mode B
  (un-gated anomaly sweep, the discovery engine). **Native delegated STRENGTH-coupling weighting** to
  Cowork's astrological domain reasoning (dignity/shadbala scales trigger FORCE), under the
  versioned-citable-judgment guardrail → I-7. Coverage matrix (I-5) made concrete. Infrastructure
  preview: 5 service-assets + 1 artifact-asset. I-7, I-8 registered.

---

## §12 — Changelog

- **v0.1 (2026-06-20)** — Initial DRAFT. Holistic opening: mission, services-not-data principle,
  the VERIFIED engine audit, two axes, value thesis + 5 layer-shaping decisions, L2→L3 contract,
  temporal discovery, audit-revised wave plan, inherited standards, open-questions register,
  discussion record. Sections flagged [VERIFIED] / [OPEN] / [CLAIM — UNVERIFIED].
- **v0.2 (2026-06-20)** — Native enhancement pass. **§1** temporal-discovery + surgical-intervention
  framing. **§2** promise-and-manifestation principle. **§3.1** NEW — the M3 temporal suite +
  `signal_activator.py` v1 (reframes L3 as MODERNIZE+INTEGRATE+EXTEND). **§4** dropped "perpendicular";
  added plane-coupling investigation (I-1). **§5.1** value thesis recast as the structural×temporal
  INTERSECTION point. **§5.3** RESOLVED — A+C service-asset model, both in-layer (Q1). **§5.4**
  RESOLVED — the computational/predictive eval SPLIT (Q3). **§5.6** NEW — the three temporal pillars
  (Daśā co-equal engine; Panchāṅga value-research; systematic subsystem leverage). **§8** wave-plan
  caveats for the M3 suite, the daśā pillar, the eval split, coarse-to-fine search. **§10** Q1/Q3/Q6
  resolved; Q7 explained; investigation items I-1…I-6 added. Open: Q2, Q4, Q5, Q7-decision, I-1…I-6.
- **v0.3 (2026-06-20)** — **§5.7 NEW — THE CONVERGENCE MACHINERY.** The three-plane model (structural
  / daśā-from-within / transit+panchāṅga-from-without, three timescales); the coarse→fine FUNNEL as
  both efficiency mechanism and acharya-cognition decomposition; the native's correction that daśā is
  a **SOFT PRIOR not a HARD GATE** → **Mode A (expected) + Mode B (anomalous/discovery)** dual search;
  strength-coupling delegated to Cowork's domain reasoning under the versioned-citable-judgment
  guardrail; the subsystem coverage matrix; the 5-service + 1-artifact infrastructure preview. **§10**
  I-7 (influence-weight model) + I-8 (Mode-B magnitude threshold) added. Open: Q2, Q4, Q5,
  Q7-decision, I-1…I-8.

---

*End of L3_KALA_CAMPAIGN_PLAN v0.3 (DRAFT). This pass built the holistic CONVERGENCE MACHINERY: a
three-plane, two-search-mode funnel that uses the slow daśā plane as a SOFT PRIOR (not a gate) to
focus the fast transit/panchāṅga planes for EXPECTED intersections (Mode A), while an un-gated
anomaly sweep (Mode B) discovers the off-daśā activations that are L3's highest-value finds — with
structural strength modulating temporal trigger force. Next pass: the load-bearing Q2
(activation-predicate mapping, building on the `signal_activator.py` precedent) and the
authoring/investigation items — especially I-3 (daśā depth), I-4 (panchāṅga deep-research, the
native's explicit ask), and I-7 (the influence-weight model Cowork owns). This document is a
retention surface: enhanced in place, every change logged, every decision carrying its WHY.*
