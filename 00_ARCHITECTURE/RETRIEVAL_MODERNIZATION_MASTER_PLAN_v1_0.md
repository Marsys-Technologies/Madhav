---
canonical_id: RETRIEVAL_MODERNIZATION_MASTER_PLAN
version: 1.0
status: CURRENT — the execution-governing document for the RETRIEVAL ENGINE MODERNIZATION program
  (the "unleash the current product first" track)
created: 2026-07-03
author: Cowork (strategic workstream, Claude Fable 5) — for native Abhisek Mohanty
relationship_to_beyond_acharya: >
  STRICT SUBSET + BRIDGE of BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN v2.1 (the BA plan). This program
  modernizes the retrieval/serving plane over the EXISTING data (no L1 extensions, no L2 regeneration, no
  learning engine — those remain BA W2/W4/W5). Every interface, table, and convention here is the BA
  target-state one, so BA waves REPLACE SUBSTANCE UNDER STABLE INTERFACES (the stored-salience swap-in at
  BA-W2 is invisible to consumers). Where this document and BA v2.1 disagree, BA v2.1 wins on data-layer
  matters; THIS document wins on retrieval/serving matters until superseded.
consolidates: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION v1.0 (I-1…I-7) · RETRIEVAL_COVERAGE_MAP v1.0 ·
  RETRIEVAL_ASTRO_COVERAGE_AND_OUTPUT_QUALITY v1.0 (P1–P15, 35-topic checklist) · MCP_TOOL_NAMING_STANDARD
  v1.0 · RETRIEVAL_TOOL_BLUEPRINT v1.0 (insight-types, envelope, workflows, eval harness) ·
  BA_RATIFICATION_GUIDANCE_COVERAGE_AUDIT v1.0 (dispositions adopted)
key_design_input: ALL synthesis LLMs are 1M-context class (native directive 2026-07-03). Consequences in §1.
delegation: per native directive 2026-07-03, Cowork AUTHORS all judgment inputs (provisional class priors,
  affinity tables, golden answers) — native retains veto; provisional values carry prior_version=0.9-prov
  and are superseded by the W1 seed package on ratification.
changelog:
  - v1.0 (2026-07-03): first version.
---

# RETRIEVAL ENGINE MODERNIZATION — MASTER PLAN v1.0

## §0 — MISSION + BOUNDARY

**Mission:** with the data assets AS THEY EXIST TODAY, make a 1M-context LLM receive the complete
astrology of a chart as meaningful, structured, correctly-weighted, cited information — so that its
responses (interpretation, prediction, timing, guidance, rectification) realize the current product's
full potential BEFORE the Beyond-Acharya data-layer waves land.

**In scope:** the retrieval registry + MCP channel + serving shapes + query-time ranking + tool estate
(wiring, naming, dedup) + eval harness. **Out of scope (BA-owned):** L1 extensions (BA-W2A), the L2
regeneration incl. stored salience v2 + DEFECT-001 (BA-W2B), anchor v2 (BA-W4B), the learning engine
(BA-W5). **Bridge duty:** every scope item here must be swap-compatible with those BA deliverables.

## §1 — THE 1M-CONTEXT DESIGN CONSEQUENCE (re-frames "bounding")

With all four synthesis families at 1M tokens, the constraint is not SIZE but SIGNAL DENSITY. Re-derived
rules:

1. **Bounding = de-noising, not shrinking.** A 6.2 MB assess_career is broken not because it is big but
   because it is 93.8% unranked repetition. A 400k-token briefing that is organized, ranked, deduplicated,
   and cited is a legitimate — and now the FLAGSHIP — payload.
2. **Two consumption products, one curated core (supersedes generic "bulk vs agentic"):**
   - **PRODUCT A — the MAHĀ-BRIEF (one-shot whole-chart briefing).** A single structured document,
     100k–500k tokens by `depth` parameter, containing the ENTIRE astrological coverage of the chart
     (35 topics, §7), ranked within every section, atoms aggregated into composites with distributions,
     full head + dissent + tail digest per the attention-budget protocol, every claim cited, every row
     carrying its fact_id refs. This is the native's completeness philosophy made servable: the LLM
     genuinely holds the whole chart at once. No human-facing product like this has ever existed.
   - **PRODUCT B — the AGENTIC DRILL SURFACE.** Bounded per-call envelopes (≤25k tokens default) with
     ranked content + drill_pointers, for loop-style synthesis and follow-up questions.
   Both are projections of the same registry core; response_format selects; MARO surface-spec defaults per
   client. The Mahā-Brief is assembled FROM the same per-topic tools (Product B calls batched server-side)
   — one code path, two faces.
3. **The attention-budget protocol applies INSIDE both** (70/20/10 head/dissent/tail by section,
   registry-governed constant) — a 1M window does not repeal finite attention; it moves the budget up.

## §2 — DESIGN PRINCIPLES (binding on every tool)

1. **Rank everything, drop nothing, hunt the tail** (BA §0.1 doctrine) — salience orders, never filters;
   tail queryable; complement pass available.
2. **Reasoning-chain structure:** content organized karaka → bhava/lord → dispositor → strength → yoga →
   nakshatra → varga confirmation → temporal context → verdict — never flat rows.
3. **One envelope everywhere:** the RetrievalEnvelope (§5) — identity, query_context, structured content,
   ranking_basis, grounding, pagination, drill_pointers, judgment_flags.
4. **One primary tool per topic** (dedup rule): aliases collapse; global-corpus vs chart-scoped are
   DIFFERENT topics (ref_* vs bodha_*).
5. **Grounding always:** fact_id refs + citations + grounding_score on every payload; orphan status
   honestly flagged (DEFECT-001 is live until BA-W2B — serve `grounding.fact_ids_orphaned` truthfully).
6. **Determinism at the serving layer:** ranking, aggregation, structuring are code; the LLM only
   narrates/synthesizes on top.
7. **Astrological completeness is the acceptance frame:** the 35-topic checklist (§7) — not tool counts.

## §3 — THE TOOL ESTATE REFACTOR (census: 53 → ~66 primaries + aliases)

### §3.1 — Naming + dedup (adopt MCP_TOOL_NAMING_STANDARD Phase 1 now)

`<layer>_<topic>_<type>` with prefixes ref/ganita/bodha/kala/phala/mimamsa/synth/nav. Phase 1 aliases
(non-breaking) ship immediately; Phase 3 removal stays gated. Dedup decisions (ratified via
BA_RATIFICATION_GUIDANCE): `bodha_remedies_get` PRIMARY (chart-scoped bo_upaya); `ref_remedies_search`
retained (global corpus); `bodha_remedies_search` → alias of primary. Sweep for further duplicates at
brief time (one primary per topic; suspects: get_projections vs get_temporal_windows overlap,
query_planet_position vs compute_natal_positions — global-ephemeris vs chart topics, keep both, name
clearly).

### §3.2 — Wiring the 31 uncovered assets (the biggest single value unlock)

Grouped by treatment; each new/wired tool ships with envelope + C/A/O quality target + four-measure score.

**GROUP 1 — handler exists, not wired (P1–P9 class; highest priority, near-free):**

| New primary tool | Backing asset(s) | Astrological topic unlocked |
|---|---|---|
| `ganita_strength_get` | ga_strength | Shadbala 6-comp + ishta/kashta + vimsopaka + bhava-bala + per-varga AV (**the intrinsic-strength dimension of ranking — prerequisite for §4**) |
| `ganita_structural_get` (facet param: aspects/argala/dispositors/parivartana/yoga_fires/dosha_fires/conjunctions/sambandha/functional/graha_yuddha) | ga_structural (77,821 facts) | The relational backbone — ONE tool, facet-enumerated, replacing 6+ unwired handlers |
| `ganita_condition_get` | ga_condition | Avasthas per varga, combustion, dignity states |
| `ganita_sade_sati_get` | ga_sade_sati | Sade Sati cycles/phases, kantaka/ashtama Shani |
| `ganita_tajaka_get` | ga_tajaka | Varshaphala year-lords, muntha, annual charts |
| `ganita_nakshatra_get` | ga_nakshatra | Tara bala, chandra bala, KP lords, gandanta (extends the partial) |
| `ganita_yogas_get` | ga_yoga (firings) | Which catalog yogas FIRE in this chart + cancellation state |
| `ganita_transit_anchors_get` | ga_transit_anchors | Natal transit-sensitivity anchors |
| `phala_rectification_get` | ph_rectification | Birth-time fit table (185 candidates; the validated 10:43) |

**GROUP 2 — reference layer exposure (thin read tools over L0; makes interpretation CITED):**
`ref_rules_search` (sutravali_rules, 2,912), `ref_yogas_get` (catalog + formation/cancellation),
`ref_doshas_get`, `ref_dignity_reference_get`, `ref_dasha_systems_get`, `ref_nakshatra_get` (enriched 27
+ padas), `ref_transit_rules_get`. (bg_reference partially covered — complete it.)

**GROUP 3 — the insight surface (P15):** `mimamsa_insight_get` over mi_darshana `mimamsa_insight_units` —
becomes the HOME of the verdict object (§5); until BA-W5 populates calibration, serves structural insights
honestly flagged `calibration: prior_only`.

**GROUP 4 — consciously deferred (documented, not dark):** medical/vastu/prashna tools (P11–P13 →
their subsystem waves), mi_* internals (sambandha/adhilepa/gunanaka/kula/pariksha/vistara → BA-W5;
exception: `mimamsa_calibration_get` v2 shape lands NOW returning honest empty-with-schema), bo_chart_gestalt
/ bo_anveshana (wire cheaply in Group 1 batch if trivial — anveshana = the discovery surface, astrologically
valuable: `bodha_discoveries_get`), ka_jivana_parva/ka_tulana (life-arc chapters — wire as
`kala_life_arc_get`, cheap and unique).

### §3.3 — The synth_* apex repair (I-2 within current data limits)

assess_* tools rebuilt on the envelope: bounded, reasoning-chain structured, with a **composed verdict**
(deterministic assembly: top-k per reasoning-chain stage + contradiction pairs surfaced with both sides'
rank + activation state from ga_dashas directly [kala bypass until L3 populated] + citations resolved
inline). Full server-side prose synthesis remains BA-W3's mi_darshana wiring; HERE the verdict is
structured-not-prose but COMPLETE (claim skeleton + ranked evidence + dissent). Kills the 6.2 MB dump.

## §4 — QUERY-TIME COMPOSITE RANKING (the bridge that delivers judgment NOW)

The stored `computed_salience` is degenerate until BA-W2B. The retrieval layer does not wait: it computes
the **4-dimensional composite AT QUERY TIME** from data that already exists:

- **topic_relevance:** karaka×domain affinity table + bhava-lordship/occupancy from ga_positions/ga_structural
  + domain-conditioned varga affinity (A-A/A-D tables — Cowork-authored provisional, §9).
- **intrinsic_strength:** ga_strength (via the newly wired `ganita_strength_get` internals) + dignity from
  ga_condition — real shadbala, not the collapsed constant.
- **structural_role:** yoga_fires membership (ga_structural) + CGM centrality (bo_bimba pagerank) +
  signature class.
- **temporal_activation:** computed directly from ga_dashas (current MD/AD lords → signals whose grahas/
  lords match) + transit service — BYPASSING empty kala_activation until BA-W4A fills it properly.
- **composite** = class_prior (provisional bg_class_priors seed, §9) × the four dimensions; percentile-
  within-class computed on the fly (S-A semantics at query time).

Contract: `ranking_basis` carries all four sub-scores + composite + `class_priors_version` — so when
BA-W2B lands stored salience v2, the retrieval layer swaps its intrinsic inputs from query-time
computation to the stored columns WITHOUT interface change, and the query-time terms (activation,
karaka-congruence, varga-affinity) remain query-time forever (BA trap #18). This single section is the
highest-leverage item in the program: it moves "what matters" from degenerate to astrological using ONLY
existing data.

## §5 — THE ENVELOPE (blueprint schema ADOPTED, with the ratified amendments)

RetrievalEnvelope as specified in RETRIEVAL_TOOL_BLUEPRINT §B4, amended: (1) `content.verdict` is the
STRUCTURED verdict object `{claim, ranked_evidence[], contradictions[{side_a, side_b, weights, resolution,
status}], tradition_concordance, activation_state, ayanamsha_robustness, confidence?, falsifier?,
citations[]}` — not `string|null`; (2) new field `tail_divergence` (complement-pass memo, nullable);
(3) `ranking_basis.class_priors_version`; (4) dual tagging `insight_type` (5-set) + `query_class` (Q1–Q9,
RECTIFICATION added as Q9); (5) `judgment_flags` retains the honest self-reporting culture (degeneracy /
orphan / L3-bypass flags served truthfully until their BA fixes land).

## §6 — PRODUCTS + WORKFLOWS

1. **The MAHĀ-BRIEF** (`synth_chart_brief_get`, depth=standard|deep|complete): §1.2 Product A. Assembly
   order = the 35-topic checklist in reasoning-chain order; per topic: ranked head + dissent + tail digest
   + citations; front matter = orientation digest + promise-style domain summary (from existing bo_samvada
   UCD) + contradiction census; back matter = provenance manifest (grounding scores per section). THE
   flagship deliverable of this program.
2. **The five insight-type workflows** (blueprint §B3) wired as documented tool-chains in tool descriptions
   + MCP prompts (BULK variants feed the Mahā-Brief sections; AGENTIC variants use drill_pointers).
   PREDICTION/TIMING workflows run against current phala/kala tools with honest flags until BA-W4 upgrades
   their substance.
3. **The complement pass** (`synth_tail_divergence_get`): tail-only synthesis over any domain; also
   embedded in Mahā-Brief deep/complete depths.
4. **Session/nav:** unchanged (M2/M3 sound) + the naming aliases.

## §7 — THE 35-TOPIC ASTROLOGICAL COMPLETENESS GATE (the acceptance frame)

A birth chart's full classical coverage, every topic reachable via a named primary tool AND present as a
Mahā-Brief section: positions+lagna · vargas (all 30) · dignities · shadbala/strength · ashtakavarga ·
avasthas · aspects (3 systems) · argala/virodha · dispositor chains · parivartana · conjunctions/war ·
yogas (fired, w/ cancellation) · doshas · functional nature · nakshatra substructure (+tara/chandra bala)
· KP lords · sahams · special lagnas/upagrahas · arudha padas (graha; bhava = BA-W2A) · karakas
(chara+naisargika) · karakamsha (BA-W2A) · dashas (7 systems, 4 levels) · sade sati · tajika/varshaphala ·
transits (live) · transit anchors · panchanga+muhurta · signals (MSR ranked) · causal graph · cross-domain
linkage · contradictions · convergence windows · discoveries/anomalies · remedies (chart + corpus) · LEL
· rectification · calibration (honest-empty) · insight units. *(38 enumerated; the checklist document's 35
+ three this plan adds: discoveries, transit anchors, life-arc.)* **Gate: RM is DONE when every topic is
GREEN on the four measures (Volume/Relevance/Accuracy/Ranking) on 482012f1 AND 1c826d5a on prod.**

## §8 — EXECUTION PROGRAM (RM waves → CLAUDECODE briefs; runs inside/alongside BA-W0→W3)

| Wave | Content | Brief | Gate |
|---|---|---|---|
| **RM0** (= BA-W0 remnant + channel hygiene) | Absorb in-flight audit swarm W3/W4 (bounding live, L4 schema, kala sidecar, panchanga_daily); **assess_* 6.2 MB caps**; cache contract (served_from_cache true); error envelope; CURRENT_STATE governance sync | `RM0_SERVING_TRUTH_AND_CAPS` (extends authored BA_W0 brief) | 53 tools structured-respond ≤ budget on prod; no tool >100k tokens uncapped; repeat-call cache hit. |
| **RM1** | Tool estate: naming aliases (Phase 1) + dedup + **Group 1–3 wiring** (≈17 new primaries incl. ganita_strength_get, ganita_structural_get, mimamsa_insight_get, bodha_discoveries_get) + envelope v1 on all NEW tools | `RM1_WIRING_AND_NAMING` | 31 uncovered → ≤6 (deferred-documented only); every wired tool passes C/A/O smoke on 2 charts. |
| **RM2** | **Query-time composite ranking (§4)** + provisional seed tables (§9) + envelope v1 retrofit on the 53 existing tools + reasoning-chain restructure + synth_* apex repair (§3.3) | `RM2_QUERYTIME_RANKING_AND_ENVELOPE` | Career top-10 on 482012f1 = 10th-lord/karaka/yoga structures with ZERO sub-varga atoms (the G10 test, achieved at query time); ranking_basis on every payload; assess_career ≤ budget with structured verdict. |
| **RM3** | **Mahā-Brief** + five workflows + complement pass + attention budget + **eval harness live with Cowork-authored golden answers** (10 questions, ≥13/15 target, INTERPRETATION spearhead first) | `RM3_MAHABRIEF_AND_EVAL` | Mahā-Brief(complete) on 482012f1: all §7 topics present, ranked, cited, ≤1M tokens; INTERPRETATION golden eval ≥13/15 by blind rubric; tail_divergence non-trivial on ≥1 domain. |
| **RM4** | Bridge maintenance: swap intrinsic inputs to stored salience v2 when BA-W2B lands; L3-bypass removal when BA-W4A lands; anchor-tool substance swap at BA-W4B; calibration serving at BA-W5 | (folded into those BA briefs as interface-stability ACs) | Zero consumer-visible interface change across all four swaps. |

Sequencing: RM0 → RM1 → RM2 → RM3 strictly serial (each consumes the previous); RM1 Groups parallelizable.
BA-W1 (judgment seed ratification) can land anywhere ≥RM2 — provisional priors upgrade in place.

## §9 — COWORK-AUTHORED JUDGMENT INPUTS (under the 2026-07-03 delegation)

Authored by Cowork from classical sources in the L0 corpus, versioned `0.9-provisional`, superseded by the
ratified W1 seed package (`BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` — already authored on the BA
track; RM2's seeds are EXTRACTED from it, not re-invented): (1) provisional `bg_class_priors` seed
(signal-class × weight + varga-grain vector); (2) graha×domain affinity (A-A); (3) domain×varga affinity
(A-D); (4) the 10 golden answers (with `lel_overlap` flags; eval corpus disjoint from L5 learning corpus);
(5) attention-budget split. Native veto at any point; contested judgments encoded at the mainstream
position, flagged `contested`, left for L5 to adjudicate empirically.

## §10 — PROGRAM ACCEPTANCE (what "full value from the current product" means)

1. **Completeness:** every §7 topic GREEN on both charts on prod (the four measures).
2. **Judgment:** the G10 career test passes at query time (RM2) — before any data-layer rebuild.
3. **The Mahā-Brief exists:** a 1M-class LLM receives the whole chart in one organized, ranked, cited
   document and produces an acharya-grade interpretation from it (RM3 golden eval ≥13/15).
4. **Honesty:** every known unfixed defect (orphaned fact_ids, empty calibration, L3 bypass) is FLAGGED in
   payloads, never silently absorbed.
5. **Forward compatibility:** BA-W2/W4/W5 land as substance swaps with zero interface change (RM4).

*End of RETRIEVAL_MODERNIZATION_MASTER_PLAN v1.0. First actions: (a) author `RM0_SERVING_TRUTH_AND_CAPS`
(extends the existing BA_W0 brief); (b) Cowork begins §9 provisional seed extraction. Carry this document
+ BA v2.1 into the implementation conversation together — they interlock.*
