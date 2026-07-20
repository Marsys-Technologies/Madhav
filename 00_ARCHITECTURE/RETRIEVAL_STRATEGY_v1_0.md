---
artifact: RETRIEVAL_STRATEGY_v1_0.md
canonical_id: RETRIEVAL_STRATEGY
version: 1.3
status: CURRENT — §F gate ruling absorbed 2026-07-19/20; W1 addendum doc correction 2026-07-20
authored_by: Claude (Cowork, Fable 5) 2026-07-19
parent_documents:
  - 00_ARCHITECTURE/RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md (v1.2 absorbs §9)
  - 00_ARCHITECTURE/RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md
  - 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
purpose: >
  The retrieval strategy written from the END GOAL backwards: an LLM — in a
  client chat over MCP or inside Paripraśna — must operate at highest
  capability, efficiency and productivity to produce deep, thorough,
  complete, wide insights, interpretations, predictions, and consultations.
  Defines the strategy areas, the tool-design architecture from the LLM's
  seat, the layering ruling, the demand-driven serving doctrine, the
  channel-variation capability set, the per-tool review rubric, and the
  data-plane coverage doctrine (grounded in the 2026-07-19 coverage census).
changelog:
  - v1.3 (2026-07-20, W1 addendum, §F gate ruling item 6): §5.2 corrected —
    `chart_ayanamsha_reports` flagged as stale/aspirational naming (no such
    table exists in the live DB); footnote added pointing to the actual
    coverage (`chart_facts_query`'s `ayanamsha_id` filter) and to the
    `DARK_SET_WIRING_PLAN_v1_0.md` finding. Doc-only correction, no
    disposition or table semantics changed.
  - v1.2 (2026-07-19/20, §F human gate ruling, RS-2 authority exercised): §5.2
    disposition taxonomy amended — DARK abolished as a terminal state,
    replaced with SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED / RETIRED,
    default bias SERVE (burden of proof on withholding). GATED requires a
    doctrine-grounded reason (A-19 NO-LEAKAGE / L5 structural seal / D-14
    register safety), a named served aggregate, and a written revisit
    condition — not an ad hoc rationale. Full ruling text:
    `briefs/retrieval_impl/RULINGS_ADOPTED.md` §F gate ruling.
  - v1.1 (2026-07-19): native review absorbed — §3.5 distillation boundary
    (librarian/scholar split, tail protection, dissent quota), §3.6
    proportionality principle + B.11 carve-out (ruling RS-4), §5.3 service-
    asset coverage (data_source: stored|computed|hybrid; census A6 extended).
  - v1.0 (2026-07-19): initial draft.
---

# Retrieval Strategy — From the Consuming LLM's Seat

## §0 — The vantage point

Both scenarios impose the SAME requirements, because the consumer is the
same kind of mind with the same goal:

> An LLM holds a question about a chart. Its objective is an acharya-grade
> answer: deep (every claim grounded to facts), thorough (nothing material
> missed), complete (it can *prove* it is done), wide (cross-domain
> patterns surfaced, contradictions held honestly), time-indexed
> (predictions with windows and confidence), and calibrated (it knows how
> sure it is). It has a finite context window, a finite number of calls it
> can afford, and — on the MCP path — no memory beyond the session pin.

Everything below derives from one question: **what does that mind need
from the plane at each moment of its work?** The channels differ only in
who runs the loop and what state persists; the retrieval requirements are
identical. That identity is the design invariant (it is why the engine is
door-agnostic, handoff §4.1).

**The efficiency law.** For an LLM, retrieval cost = calls × tokens ×
stitching effort. Capability = what it *can* reach; productivity = how much
verified insight per unit context. The plane's job is to maximize insight
density per token and minimize the number of calls the LLM must invent for
itself. Every strategic choice below is an application of this law.

## §1 — The eight areas of the retrieval strategy

The strategy decomposes into eight areas. Tool design (S-2) is one of
them; the native asked what the others are — this is the complete set:

| # | Area | The LLM's question it answers |
|---|---|---|
| **S-1** | **Orientation & discovery** | "Where am I, what exists, where do I start?" |
| **S-2** | **Tool design architecture (the ACI)** | "What actions can I take, and do they match my cognitive moves?" |
| **S-3** | **Coverage & fidelity (data-plane contract)** | "Can I reach everything that is true, and only what is true?" |
| **S-4** | **Demand-shaping (query & ranking semantics)** | "Will the plane give me what *my question* needs, or what the table happens to hold?" |
| **S-5** | **Synthesis support (width machinery)** | "How do I see across domains/layers without N² exploration?" |
| **S-6** | **Temporal & predictive spine** | "How do I anchor every claim in time and grade every prediction?" |
| **S-7** | **Epistemic governance** | "How sure am I, and can I prove where each claim came from?" |
| **S-8** | **Adaptivity & channel absorption** | "Does the plane meet me as I am — my model family, my loop, my budget, my entitlement?" |

The elevation plan v1.1 already carries most of S-7 and S-8 and the
mechanics of S-2. What this strategy adds is the *doctrine* for S-1, S-3,
S-4, S-5, S-6 — and the per-tool review that enforces all eight.

### S-1 — Orientation & discovery

The LLM's first 2,000 tokens decide the quality of everything after. It
must never start blind or waste calls discovering the terrain.

- **One entry call.** A single orientation capability returns: chart
  frame (the v3 `chart_header`), the chart's most load-bearing structural
  facts, what is *notable* about this chart (top gestalt findings), the
  active dasha context, and a map of where to go next (category inventory
  + drill pointers). Today `get_chart_orientation` approximates this;
  the strategy makes it the designed front door of every session.
- **Self-describing catalog.** `marsys://resource/catalog` (plan R-1.2)
  lets any client model learn the surface without a human; the category
  inventory line rides in every projection (vendor-consult row 8).
- **The plan as a retrieval artifact.** `plan_retrieval`/`vidhi_plan`
  gives the LLM the acharya floor for its intent *before* it starts —
  orientation not just in space (what exists) but in method (what a
  complete investigation looks like).

### S-2 — Tool design architecture (deep-dived in §2)

### S-3 — Coverage & fidelity (deep-dived in §5)

### S-4 — Demand-shaping (deep-dived in §3)

### S-5 — Synthesis support: width machinery

Width is not "more rows"; it is *relations served as data*. An LLM
composing a wide reading needs the plane to have pre-computed what no
single-call mind can hold:

- **Convergence surfaces** — where independent techniques agree
  (`kala_convergence`, judgment composites) served verdict-first.
- **Contradiction surfaces** — where they disagree (`bodha_contradictions`,
  `synth_tail_divergence`) served with both poles + the dissent held open,
  never averaged away. A wide reading that hides tension is a narrow
  reading with good manners.
- **Linkage** — cross-domain cell structure (CDLM), graph motifs/paths
  (CGM), domain links: the "career question with a marriage mechanism"
  case must be one drill away, not a lucky guess.
- **Cross-layer stitched bundles** (new; census §4 finding): today only ONE
  real cross-layer join exists (`bodha_msr_signals ↔ kala_activation`);
  everything else the LLM must stitch manually across 3–5 calls. The
  strategy adds **spine bundles** as first-class capabilities: 
  `signal → its activation windows → its phala anchors → its calibration`
  served as one pre-joined chain for a given domain/scope. This is the
  single biggest *productivity* upgrade available: it converts the LLM's
  most expensive stitching work into one call.

### S-6 — Temporal & predictive spine

Readings are time-indexed claims. The plane must make "when" as cheap as
"what":

- Every signal-bearing response carries timing hooks (dasha context, next
  activation window) or an honest `timing_anchored: false` flag — never
  silence (§N.6 rule 3 generalized).
- Prediction-grade output is a distinct shape: claim + window + mechanism
  + confidence + calibration lineage (`phala_anchors` × `mimamsa_calibration`),
  ready to enter the prediction ledger without transformation. The ledger
  is channel-agnostic (handoff §7.3); therefore this shape is too.
- The current-date context (`now_context_date` in the pin) governs all
  "current/upcoming" semantics so both channels resolve time identically.

## §2 — Tool design architecture, from the LLM's seat

**The organizing principle: tools mirror the acharya's cognitive loop, not
the database schema.** An acharya reading a chart performs recognizable
moves. Each move is a tool archetype; the surface is complete when every
move has its tool and no tool exists that serves no move:

| Move | The acharya act | Tool archetype | Today's exemplars |
|---|---|---|---|
| **ORIENT** | Take in the chart's frame and gestalt | entry umbrella | `get_chart_orientation`, chart digest |
| **PLAN** | Decide what a complete read requires | plan compiler | `plan_retrieval` / `vidhi_plan` |
| **SCAN** | Sweep a domain/technique for what fires | faceted umbrella | `get_signals`, `ganita_yoga_firings_get` |
| **CONVERGE** | Find agreement/tension across techniques | synthesis surface | judgment composites, contradictions, CDLM |
| **JUDGE** | Weigh evidence into a verdict | verdict tool | `judgment_query`, `assess_*` |
| **TIME** | Anchor findings in dasha/transit windows | temporal spine | `kala_windows_get`, activation, convergence |
| **PREDICT** | Commit to claims with windows + confidence | prediction shape | `phala_anchors`, outlook |
| **REMEDIATE** | Map findings to interventions | remedy surface | `bodha_remedies_*`, mitigation |
| **VERIFY** | Check grounding, coverage, calibration | epistemic tools | coverage stamps, `mimamsa_calibration`, LEL |
| **DRILL** | Descend from any claim to its facts | leaf + pointers | `ganita_*` leaves via `drill_pointers` |

Design rules that follow:

1. **Question-shaped, not table-shaped.** A tool's signature is the LLM's
   *intent* (`assess domain X at depth Y for horizon Z`), never "SELECT
   from my table with these columns." Table-shaped tools survive only as
   DRILL leaves under umbrellas.
2. **Every umbrella answers three things at once:** the verdict layer
   (what is true), the grounding layer (why), and the navigation layer
   (where to go deeper) — the v3 envelope IS this triple; §N.6 orders it.
3. **Every claim is drillable to L1 in ≤2 hops.** Fable-grade depth means
   the chain reading → signal → fact_id is mechanically walkable.
4. **No dead ends.** A response that exhausts its budget, hits an empty
   family, or reaches a coverage boundary says so AND points somewhere
   (trim `recover_via`, `empty_reason`, drill pointers). Dead ends make
   the LLM guess; guessing is where hallucination enters.
5. **Symmetric effort.** The same move costs the same shape of call in
   every domain (career scan ≡ marriage scan). Asymmetry taxes the LLM's
   planning; today's thin non-wealth floors are an asymmetry defect.
6. **The loop is the unit of design.** Tools are judged not in isolation
   but by how the 10 moves compose under an 8-iteration internal loop or
   a client loop of unknown discipline. Target: a standard deepdive
   consultation completes inside ≤10 umbrella calls + drills.

## §3 — Demand-driven, not supply-driven (S-4 doctrine)

**Definitions.** A response is *supply-driven* when its content is
determined by what the table holds (dump rows, static ranking, fixed
shape). It is *demand-driven* when determined by what the question needs
(scope-conditioned selection, question-relevant ranking, verdict-first
assembly). Today's plane is mostly supply-driven with demand-driven
islands (`judgment_query`'s domain-bearing sort is the exemplar).

The five mechanics that convert the plane:

1. **The scope tuple is the demand contract.** Every umbrella accepts the
   unified scope tuple (plan R-3.1): intent, domains, width, depth,
   horizon, intervention, entitlement. No umbrella serves a default dump
   when a tuple is absent — it serves the orientation slice + a flag.
2. **Question-conditioned ranking.** Rows rank by *relevance to the
   demand*: domain-bearing before domain-adjacent, horizon-relevant
   windows before distant ones, contested-but-material before
   confirmed-but-trivial. Static salience becomes the tiebreaker, never
   the ordering. (This is the generalization of `judgment_query`'s
   bearing-sort to every umbrella; descriptor field `demand_ranking`
   declares each tool's ranking basis so it is auditable data, §N.6-4.)
3. **Progressive disclosure as the default shape.** Verdict → grounding →
   drill. Depth is *pulled* by the LLM (drill pointers, `verbosity` knob,
   facets), never *pushed* by the handler. The budget trimmer protects
   the demanded layer (`hardFloor` on the verdict/bearing sections).
4. **Completeness receipts close the loop.** Demand-driven is only safe if
   the LLM can see what the demand *required* vs what was served: the
   Vidhi floor receipt (served/empty/dark per item) rides with every
   planned investigation, so "thorough" and "complete" are checkable
   properties, not vibes. This is how the LLM knows it is done — or knows
   exactly what remains dark and why (CR-cited).
5. **Width on demand.** The linkage/convergence/contradiction surfaces
   (S-5) are the demand-driven form of width: the LLM asks "what else
   bears on this?" and gets relations, not a second supply dump.

**Anti-patterns, named and banned:** row dumps without ranking basis;
static top-N that ignores the question; empty sections without
`empty_reason`; "complete" claims without a receipt; depth pushed into
context the demand never asked for (the 909KB response of D-1.5b history).

### §3.5 — The distillation boundary (native ruling, 2026-07-19)

A retrieval tool's product is **relevant information, not raw computed
data** — but distillation has a precise boundary:

- **The tool is the librarian; the LLM is the scholar.** The tool performs
  *deterministic relevance work*: select, rank, group, label, account
  (demand-conditioned filtering, density layering, receipts). The LLM
  performs *meaning-making*: weighing, synthesis, narrative. 
- **Tools never summarize generatively.** Paraphrasing rows into prose
  injects interpretation below the B.1 boundary, invisibly. Distillation
  is structural (which rows, what order, what labels), never rhetorical.
- **Trim is lossy in context, lossless in reachability.** Nothing trimmed
  is destroyed: every cut is declared (trim_report + `recover_via` +
  coverage stamp) and everything cut remains one drill call away. The LLM
  always retains the power to decide the tail mattered.
- **Tail/middle protection is structural, not abstentional:** (a) rank by
  bearing-on-the-question, not magnitude — magnitude-ranked trimming is
  what eats the meaningful middle (the D-1.5a `bearing_yogas` zeroing is
  the canonical precedent); (b) a **dissent quota** — reserved,
  `hardFloor`-protected slots for contradictions, anomalies, and
  low-confidence-high-impact rows in every trimmed response (§N.6 rule 1
  made mechanical); (c) the receipt tells the LLM what was not served, so
  "go get the tail" is an informed choice, never a blind spot.

### §3.6 — The proportionality principle (native ruling, 2026-07-19)

**Response effort is proportional to question scope.** A pinpointed
factual inquiry needs a fact, not an investigation:

- The scope tuple is the mechanism: `depth: retrieval` compiles a minimal
  floor (structural primitives, no machine band) and routes to DRILL
  leaves — one call, one fact, grounded, done.
- **B.11 carve-out (ruling RS-4):** B.11's whole-chart-read discipline
  governs *interpretive* queries. Factual lookups satisfy it via the
  frame check every response already carries (chart_header + session
  pin), not a full L2 synthesis pass.
- **Escalation valve, not escalation default:** if a pinpoint lookup
  touches material context (the fact participates in an active
  contradiction, firing yoga, or open prediction window), the response
  flags it in one line with a drill pointer — it never balloons the
  answer. Relevance cuts both ways: no unrequested depth, no silence
  where depth is warranted.
- On the MCP raw path, proportionality is inherent (the client picks the
  leaf); on planned paths (Paripraśna, `prashna_ask`) the classifier and
  floor bands own it.

## §4 — Channel-variation capabilities (S-8)

The variations the plane must absorb, and the capability that absorbs each:

| Variation axis | Portal (Paripraśna) | MCP client | Absorbing capability |
|---|---|---|---|
| Who plans | our planner | client LLM (or `prashna_ask`) | same Vidhi plan surface on both (R-3); plan_retrieval for clients |
| Loop discipline | 8-iteration, gated | unknown, possibly loop-prone | self-contained envelopes; circuit breakers (v1.1 §7-11) |
| State | conversation + summaries | session pin only | pin as the universal minimum; no tool assumes transcript |
| Model family | ModelPlane tiers A/B/C | any (Claude/GPT/Gemini/DeepSeek) | per-family projections + schema dialects (v1.1 §7-1) |
| Token budget | budget arbiter | client's context, unknown | density_contract + verbosity knob + honest trim |
| Register | linted prose (D-14) | envelope-only defense | register block in envelope (R-2.3) |
| Entitlement | portal session | OAuth scope/profile | one entitlement brain, profile = scope (OT-10) |
| Synthesis quality | our gates | ungateable | epistemic grades + reading_contract header (R-2.3b) |

The invariant restated: **capability differences between channels are
absorbed at the edge; the plane itself never branches on the door.**

## §5 — The data-plane contract: layering ruling + coverage doctrine (S-3)

### §5.1 The layering ruling: layered data, flat access, guided navigation

The native asked: layer it up, or flatten? The answer is both, at
different strata — and the census data settles it empirically:

- **The DATA stays layered** (L0…L5). The layering *is* the epistemology
  (B.1: facts ≠ derivations ≠ interpretations); flattening it would
  destroy the provenance chain that makes readings auditable and is the
  project's core differentiator. Non-negotiable.
- **ACCESS is flat.** Any capability is directly callable without walking
  a hierarchy; an expert LLM that knows it wants `kala_convergence` pays
  one call, not a descent ritual. (Already true; preserved.)
- **NAVIGATION is guided.** The layer structure reaches the LLM as
  *semantics on the envelope* (`grounds_to`, epistemic grades, drill
  pointers pointing DOWN the layers), and as the umbrella→drill topology
  — never as a maze it must traverse blind. The cognitive-loop taxonomy
  (§2), not the storage layers, organizes the surface the LLM sees.
- **The flattening that IS needed is horizontal, not vertical:** the spine
  bundles of S-5 (pre-joined signal→window→anchor→calibration chains).
  The census shows the plane is vertically well-layered but horizontally
  disconnected — one real cross-layer join in the entire surface. Bundles
  fix that without collapsing the layers.

### §5.2 Coverage doctrine

**AMENDED v1.2 (§F human gate ruling, RS-2 authority exercised, 2026-07-19/20).** DARK is
abolished as a terminal state. Every substantive table resolves to exactly one of:

- **SERVED-DIRECT** — a capability serves this table's concepts directly.
- **SERVED-VIA** — concepts fully covered by a *named* other serving surface (per-concept cover
  recorded in the `concept_ledger`, CI-verified — not merely asserted in prose).
- **OPERATIONAL** — the table carries no astrological concept (bookkeeping, journaling, export,
  cosign ledgers, embedding-store infrastructure); declared, not a coverage gap.
- **GATED** — an astrological concept is deliberately withheld, with (a) a cited reason already
  grounded in standing doctrine (A-19 NO-LEAKAGE / the L5 structural seal / D-14 register
  safety — never an ad hoc rationale invented at disposition time), (b) a named served aggregate
  that stands in for the withheld detail, and (c) a written revisit condition.
- **RETIRED** — dead/superseded, no live consumer.

**Default bias is SERVE: the burden of proof sits on withholding, not on serving.** A table with
no discovered serving route is not "dark" pending investigation — it is evidence-checked against
the reachability matrix + a live probe (per the mechanical resolution procedure,
`briefs/retrieval_impl/RULINGS_ADOPTED.md` §F gate ruling item 2) and assigned the state the
evidence dictates. Only a table whose evidence points to a genuinely NEW gate reason — not
already covered by A-19/L5-seal/D-14 — escalates to the native; nothing sits at an unresolved
"needs owner" state as a terminal outcome. Dark-by-accident (a table with no route AND no
doctrine-grounded gate reason) remains a defect class (extends §N.6 to the data plane), but its
disposition is SERVE-it, not label-and-park-it.

~~Prior v1.0/1.1 rule: every substantive table is either SERVED, INTERNAL-BY-DESIGN (declared,
with rationale), or RETIRED. Dark-by-accident is a defect class.~~ Superseded by the five-state
taxonomy above — INTERNAL-BY-DESIGN's single catch-all bucket conflated "no concept here"
(now OPERATIONAL) with "concept withheld for a reason" (now GATED, which additionally requires
the doctrine citation + named aggregate + revisit condition INTERNAL-BY-DESIGN never demanded).

Census (2026-07-19, full map in
session record; method: migration inventory × retrieval-source grep):

- Physical inventory far exceeds the asset counts: L2 has 34 tables
  behind 14 assets; L5 has 27 behind 12.
- **Dark today:** (a) the entire L0 `reference_*`/`bg_*` catalog stratum
  (13 tables — dignities, aspects, vargas, prashna, medical/vastu
  reference); (b) 18 L5 `mimamsa_*` ledgers (most legitimately internal,
  but `mimamsa_signal_adjustment` ~66.8k rows/chart,
  `mimamsa_manifestation_sets`, `mimamsa_discoveries`,
  `mimamsa_insight_embeddings` are substantive read candidates); (c) L2
  rollup tiers (`bodha_rm_dasha_windowed_prescriptions` — the
  time-targeted remedy slice! — `bodha_cdlm_{domain_rollups,
  evolution_gradients,pattern_clusters}`, `bodha_triangulation`,
  `bodha_cgm_sub_graphs`); (d) `kala_timeline`, `chart_panchanga`,
  `chart_ayanamsha_reports`¹; (e) still-open register rows S-3
  (bhava_arudha), SC-2 (graha speed/retro/combustion), SC-3..5
  (ashtakavarga refinements), G-1 (CGM bhava edge-orphans).

  ¹ **Correction (W1 addendum, 2026-07-20; §F gate ruling item 6; corrected 2026-07-20,
  independent verification):** `chart_ayanamsha_reports` does not exist in the live DB —
  confirmed against the W1b harvest's full live-table scan (zero match, no close variant).
  It WAS a real, once-created table, not stale/aspirational naming: `platform/migrations/
  _archive/130_chart_ayanamsha_reports.sql` created it (cross-ayanamsha divergence scoring),
  and it was explicitly retired during the legacy teardown — listed in
  `LEGACY_TEARDOWN_KILL_LIST_v1_0.md` / `LEGACY_TEARDOWN_CLOSE_v1_0.md` §4's build-orchestration
  kill set and dropped via `infra/teardown/01_drop_tables.sql:142`
  (`DROP TABLE IF EXISTS public.chart_ayanamsha_reports CASCADE`). This doc's dark-set mention
  of it is simply stale — it references a table that no longer exists post-teardown, not one
  that never existed. The closest live equivalents are `concordance_ayanamsha_flags` (2 rows) /
  `concordance_ayanamsha_flags_staging` (0 rows) — neither is what this bullet meant. The
  concept this bullet intended (per-ayanamsha divergence reporting) is otherwise already served
  without a dedicated table: `chart_facts_query`'s `ayanamsha_id` filter
  plus the 6 stored ayanamshas on `chart_facts` cover ayanamsha-scoped
  fact lookup directly; no dedicated divergence-report surface exists or is
  being wired. See `briefs/retrieval_impl/DARK_SET_WIRING_PLAN_v1_0.md`
  (table-does-not-exist finding) and `briefs/retrieval_impl/RULINGS_ADOPTED.md`
  §F gate ruling item 6 for the adopted disposition.
- **Recently remediated, verify-don't-redo:** LCA-19/LCA-4 (18 of 23
  computed-but-unserved assets now served, 2026-07-13);
  `register_p1_ganita.ts` closed most of the old "NOT REACHABLE" L1 list.
  `RETRIEVAL_COVERAGE_MAP_v1_0.md` (53-tool era) is stale — supersede it.

### §5.3 — Service-asset coverage (native ruling, 2026-07-19)

Coverage is **stored assets + service assets**. The plane's second data
source is real-time computation — `ga_chart_service`, the panchanga
service, the ephemeris/python sidecars (arbitrary-date transits, tajaka,
muhurta, prashna). These answer what stored data structurally cannot:
date-parameterized futures and "now" queries. Doctrine:

- Every capability descriptor declares `data_source: stored | computed |
  hybrid`; census axis A6 audits service reachability exactly as it
  audits tables (a computable-but-unreachable service result is dark data).
- Computed responses carry their own provenance honesty: `computed_at`,
  engine/ephemeris version — the real-time analogue of `build_id` (they
  cannot carry one).
- Hybrid tools declare which fields are stored vs computed so the LLM
  never mistakes a live transit for a sealed build fact (B.1 applied to
  time).

Reading-impact priorities from the dark set: dasha-windowed remedies (the
REMEDIATE move is time-blind without it), CDLM rollups/evolution gradients
(width machinery, §S-5), the L0 dignity/aspect catalog (the LLM cannot
cite canonical definitions), triangulation, and the G-1 graph repair
(JUDGE-move chains through bhavas are structurally broken).

## §6 — The per-tool review (every tool, one rubric)

Every capability is scored on eight axes, each 0–2 (0 absent, 1 partial,
2 conformant). The review is executed as a generated scorecard — machine
where possible (axes 2,3,4,8 are statically checkable), Fable-5-judged
where semantic (axes 1,5,6,7):

| Axis | Question | Strategy section |
|---|---|---|
| A1 Cognitive fit | Which §2 move does it serve? (0 = none → retire/merge) | §2 |
| A2 Demand-shaping | Accepts scope/facets; declares `demand_ranking`; no default dump | §3 |
| A3 Envelope conformance | v3, header, grades, coverage, flags-enum, register labels | plan R-2 |
| A4 Density & budget | density_contract populated + enforced; trim with recovery | §N.6 |
| A5 Drill topology | Correct position (umbrella/drill/leaf); ≤2 hops to L1; no dead ends | §2 |
| A6 Data coverage | Serves its tables completely; no accidental facet-only slice | §5.2 |
| A7 Description quality | Display fields per authoring standard; no native leakage; portable schema | plan R-1 |
| A8 Cross-channel | Stateless-safe; entitlement-gated; family-projectable | §4 |

Output: `RETRIEVAL_TOOL_CENSUS_v1_0.md` — one scored row per capability
(123 + additions), each defect mapped to the phase that fixes it, plus the
table-disposition register from §5.2. The census is re-generated (not
re-authored) after every phase gate — it is the running proof that the
strategy is landing.

## §7 — What "highest capability, efficiency, productivity" cashes out to

Measurable end-state targets (extending plan §6):

1. **Capability:** 100% of substantive tables SERVED or declared; every §2
   move has its tool; spine bundles live; zero dead ends in a full
   crawl of drill pointers.
2. **Efficiency:** standard deepdive ≤10 umbrella calls; orientation
   ≤2,000 tokens; median umbrella response ≤25KB with verdict layer
   intact under trim; readback battery ≥ target across all four families.
3. **Productivity:** completeness-receipt coverage on 100% of planned
   investigations; question→floor round-trip works for every intent;
   time-to-first-verdict (calls until a grounded verdict exists) ≤3 for
   every domain.
4. **Depth/width proof:** every served claim drills to fact_ids in ≤2
   hops; contradiction and linkage surfaces appear in ≥ the floor-mandated
   rate of deepdive readings (no silently-narrow readings).

## §8 — Feed into the elevation plan (absorbed as v1.2)

- **New phase R-1.5 — Tool Census & Coverage Closure** (after R-1
  metadata exists, before R-2 envelope migration): run the §6 rubric over
  all capabilities; disposition every dark table per §5.2; wire the
  substantive dark set (dasha-windowed remedies, CDLM rollups,
  triangulation, L0 catalog stratum, panchanga, mimamsa read candidates);
  repair G-1; supersede the stale coverage map.
- **R-2 additions:** `demand_ranking` descriptor field + question-
  conditioned ranking on every umbrella; timing hooks or
  `timing_anchored:false` on every signal-bearing response; prediction
  shape standardized (claim+window+mechanism+confidence+lineage).
- **R-3 additions:** scope tuple accepted by every umbrella (not only
  plan surfaces); completeness receipts served on both channels;
  orientation redesigned as the S-1 front door.
- **R-4 additions:** spine-bundle capabilities (signal→window→anchor→
  calibration) as first-class tools on all profiles; §7 metrics wired
  into the battery as tracked numbers.
- **New ruling rows:** RS-1 — approve the layering ruling (§5.1);
  RS-2 — approve the coverage doctrine + dark-table disposition authority
  (§5.2); RS-3 — approve the ≤10-call / ≤3-to-verdict efficiency targets
  as gate criteria (§7); **RS-4 — RULED: AUTHORIZED by native 2026-07-19**
  (§3.6 proportionality carve-out). Executed same day: `CLAUDE.md` v6.4
  (§I B.11 bullet + frontmatter/footer/changelog) and
  `PROJECT_ARCHITECTURE_v2_2.md` §B.11 + §H.4 amended in place with a
  dated changelog entry.
- **§3.5/§3.6/§5.3 execution notes for the plan:** dissent quota →
  R-2 trim discipline; `data_source` field → R-1 descriptor amendment;
  proportionality flags (escalation valve) → R-2 envelope; service-asset
  audit → R-1.5 census scope.

---

*End of RETRIEVAL_STRATEGY v1.0 (2026-07-19). The elevation plan remains
the execution vehicle; this document is its WHY and its acceptance
criteria, written from the seat of the mind the plane exists to serve.*
