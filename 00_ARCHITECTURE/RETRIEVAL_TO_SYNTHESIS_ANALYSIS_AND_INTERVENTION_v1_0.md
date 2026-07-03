---
artifact: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION
canonical_id: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION
version: 1.0
status: CURRENT — complete analysis + intervention plan: data → retrieval → MCP → synthesis, astrological-lens-first
created: 2026-07-02
author: Cowork (as the live LLM client over the MCP) — for native Abhisek Mohanty
classification: end-to-end analysis + layered intervention plan (handoff-grade)
instrument: live prod amjis-mcp (SHA 40a7f0d1), this Cowork connector; every claim = a real probe or the live asset catalog
governing_frame:
  - ASTROLOGICAL-MEANING FIRST — each asset = a TOPIC; each tool judged by the astrological VALUE it delivers;
    the target is meaningful, structured, correctly-weighted astrological data, not clean bytes.
  - RANKING IS THE CRUX — ranking = astrological judgment encoded (what matters). It is the highest-leverage layer.
  - 1M-CLASS MODELS, ALL FOUR FAMILIES (Gemini, Claude, GPT, DeepSeek V4 Pro) — no small-context floor; optimum =
    maximal SIGNAL at volume, served two ways: BULK (large organized briefing) + AGENTIC-LOOP (bounded + drill).
  - FOUR MEASURES per element end-to-end: VOLUME · RELEVANCE · ACCURACY · RANKING.
---

# RETRIEVAL → SYNTHESIS — COMPLETE ANALYSIS + INTERVENTION PLAN

> The question this answers: does the rich astrological data layer reach a 1M-class LLM as **meaningful,
> structured, correctly-weighted astrological information** it can synthesize into acharya-grade insight? The
> short answer: **the data layer is astrologically rich and largely correct; the retrieval + MCP + synthesis
> layers strip the meaning and the weight out on the way to the model.** Ranking is where it fails hardest.

---

## PART 1 — THE COMPLETE DATA-LAYER ASTROLOGICAL INVENTORY (every asset = a topic)

85 assets, live catalog (list_assets, 2026-07-02). Grouped by layer; for each, the astrological TOPIC and the
meaningful astrological information it holds (from the asset's fact-categories / target tables). **This is the
richness that must survive to the LLM.**

### L0 Brahmagyan — the reference/knowledge substrate (global topics)
- **bg_ontology** (Nāmasaṃgraha, 623) — the entity vocabulary: grahas, rāśis, bhāvas, nakshatras, yogas, karanas.
- **bg_reference** (Sāraṇī, 1,485) — planets, signs, aspects, vargas, houses, strength-systems, karakas,
  upagrahas, constants, glossary — the *meaning tables* for every primitive.
- **bg_rules** (Sūtravālī, 2,912) — the classical rule base (the "if-then" of Jyotish).
- **bg_texts / bg_text_index / bg_compendium_index** (10,651 / 400 / 9,538) — classical text corpus (BPHS,
  Phaladeepika…), chunked + embedded + indexed. The *citable source layer*.
- **bg_yogas** (Yoga-saṃgraha, 250) — the yoga catalog (Raja, Dhana, Arishta…) — the *named combinations*.
- **bg_doshas** (Doṣa-kośa, 50) — affliction catalog.
- **bg_dignity_reference** (Graha-avasthā, 151) — dignity, avastha schemes, combustion orbs, naisargika
  friendship, motion-state thresholds — *how strong/weak a placement is, defined*.
- **bg_dasha_systems** (18) — Vimshottari + 17 other dasha systems.
- **bg_nakshatra / bg_nakshatra_medical** (2,857 / 27) — full nakshatra reference + body-part mappings.
- **bg_remedies** (Upāya-kośa, 800) — remedy corpus (mantra/gem/charity/vrata/yantra/puja/tantric/ayurvedic/vastu/behavioral).
- **bg_concordance** (800) — rule→source attributions.
- **bg_medical_mappings, bg_prashna_rules, bg_transit_rules/engine, bg_vastu_directions** — medical, horary,
  gochara, vastu topic-rulebooks.
- **bg_ephemeris** (825,084) + **bg_ephemeris_engine / bg_panchanga** — planetary positions 1900–2150 + engines.

### L1 Gaṇita — the computed chart facts (per-chart topics; ~27,554 facts/chart)
- **ga_positions** (Graha-sthāna) — planet + Lagna positions, sign attributes (the natal spine).
- **ga_vargas** (Varga, 20,877) — ALL divisional charts (D1–D60) × grahas × ayanamshas. *This is the divisional richness.*
- **ga_strength** (Balatva, 11,936) — **shadbala (6 components) + ishta/kashta phala + vimsopaka + ashtakavarga
  (bindu/pinda/sarva) + bhava_bala + saptavargaja + per-varga strength.** *The strength/capacity topic — the raw material of ranking.*
- **ga_condition** (Graha-sthiti, 2,880) — avastha composites (baladi/deeptaadi/jagradadi/lajjitadi/sayanadi) per varga.
- **ga_structural** (Saṃracanā, 77,821) — **aspects, argala, dispositor chains, yoga_fires, dosha_fires,
  conjunctions, sambandha, parivartana, graha_yuddha, combustion, functional class, yoga_karaka flags, chart
  centrality/clusters, convergence/contradiction pairs.** *The relational-structure topic — the biggest asset.*
- **ga_nakshatra** (Nakṣatra-Paṭala, 1,802) — nakshatra joins, padas, lords, KP lords, gandanta, tara bala.
- **ga_sensitive** (Sūkṣmabindu, 8,610) — **upagrahas, sahams, arudha padas, karakamsa, swamsa, special lagnas,
  bhrigu-nadi points, KP + tajik points.** *The rare/esoteric sensitive-points topic.*
- **ga_dashas** (Daśākrama, 536,471) — Vimshottari + other dasha chains, multi-level, with lord natal condition.
- **ga_sade_sati** (11,019) — Sade Sati cycles/phases, dhaiya, kantaka/ashtama shani.
- **ga_yoga** (Yoga-nidhi) — yoga *firings* (which catalog yogas actually fire in this chart).
- **ga_tajaka** (Tājaka, 240) — annual (varshaphal) year-lords.
- **ga_transit_anchors** (45) — natal anchors for transit.
- **ga_medical, ga_vastu, ga_prashna** — per-chart medical/vastu/horary.

### L2 Bodha — the synthesis/relational layer (per-chart; the "meaning" layer)
- **bo_laksana** (Lakṣaṇa, MSR ~64,765) — the signal store: every classical observation as a signal, with
  salience, domains, tradition, constituent_facts, citation. *The interpreted-signal topic.*
- **bo_bimba / bo_karanajala** (CGM nodes 140 / edges 365) — the **causal graph** (what influences what). *The relational-reasoning organ.*
- **bo_cgm_paths / bo_cgm_motifs** — causal chains + recurring motifs.
- **bo_sangati / bo_cdlm_summary** (CDLM cells 70) — **cross-domain linkage** (how career↔character↔wealth co-activate).
- **bo_drishti** (Question Lenses, 60) — per-question-type signal projections (career/marriage/… lenses).
- **bo_upaya** (Remediation, 180) — chart-specific remedy resonances + prescriptions.
- **bo_samskara** (embeddings, ~64,765) — signal embeddings for semantic retrieval.
- **bo_anveshana** (Discovery, 500) — anomalies/discoveries (non-obvious patterns).
- **bo_samvada** (UCD) — the unified chart digest (holistic portrait).
- **bo_chart_gestalt / bo_pramana_mapa** — gestalt + synthesis-quality scorecard.

### L3 Kāla — timing/activation (per-chart + services)
- **ka_kalasutra** (Bounded Activation → kala_activation) + **ka_yojaka** (activation predicates) — **which
  signals are LIVE now** (the timing gate). *[OBSERVED EMPTY — see Part 3.]*
- **ka_sangam** (Convergence engine → kala_convergence) — windows where multiple indicators peak together.
- **ka_vighnakara** (Obstruction → kala_obstruction) — Sade Sati / malefic-dasha obstruction periods.
- **ka_bhavishya_lekha** — probabilistic forward projections.
- **ka_jivana_parva / ka_kala_darshana / ka_tulana** — life-arc chapter, display view, cross-pattern prioritization.
- **ka_gochara / ka_graha_sancara / ka_muhurta_seva / ka_dasha_kala** — transit/ephemeris/muhurta/dasha services.

### L4 Phala — prediction (per-chart)
- **ph_nimitta** (Predictive anchors → phala_anchors) — calibrated event anchors with falsifiers.
- **ph_phaladesa** (domain result declaration), **ph_pramana** (falsifiability), **ph_pratikara** (mitigation),
  **ph_muhurta** (auspicious windows), **ph_sankrama** (cross-domain spillover), **ph_sodhana/suddha_sodhana**
  (anomaly detect/cleanse), **ph_rectification** (birth-time). *[OBSERVED SCHEMA-BROKEN earlier — Wave 4.]*

### L5 Mīmāṃsā — calibration/learning + the INSIGHT surface (per-chart)
- **mi_darshana** (Darśana → **mimamsa_insight_units** + embeddings) — **the insight surface** (this is where a
  reconciled reading is *meant* to live). *[Not yet exercised via MCP — a key gap; see interventions.]*
- **mi_bhavisya** (Predictions), **mi_pramana** (Calibration/Brier), **mi_sambandha** (manifestation grammar),
  **mi_adhilepa** (learned overlay adjustments), **mi_gunanaka** (multipliers), **mi_kula** (signal families),
  **mi_jivanaghatana** (held-out LEL), **mi_pariksha** (QA), **mi_seva** (serve-time apply).

**INVENTORY VERDICT:** the astrological breadth is genuinely acharya-scale — every classical topic is present
(dignities, shadbala, all vargas, ashtakavarga, aspects, argala, dispositors, yogas, doshas, nakshatra
substructure, sahams, arudhas, upagrahas, multiple dasha systems, transits, sade-sati, causal graph, cross-domain
linkage, remedies, calibration). **The data layer is not the deficiency. The deficiency is everything downstream
of it.**

---

## PART 2 — LAYER-BY-LAYER OBSERVATIONS (astrological lens; + = strength, − = defect; all evidence-cited)

### LAYER A — DATA (L0–L5 assets)
- **+ Breadth is acharya-complete** (Part 1). Every topic an acharya uses exists as a computed asset.
- **+ Correctness at the foundation:** natal positions match the 7 FORENSIC anchors (compute_natal_positions:
  Sun Cap/Shravana H10, Moon Aq/Purva Bhadrapada H11, Lagna Aries). Dashas two-pass-verified, multi-system.
- **+ Grounding vocabulary exists:** signals carry citation_human + constituent_facts + tradition + verification status.
- **− DEFECT-001 (machine grounding broken):** constituent_facts_array → L1 fact_ids resolve at only ~8.5%
  (91.5% orphan), from the L1 SHA rebuild. Human citations read fine; the machine provenance chain is severed.
  *Astrological cost:* claims can't be traced to their computed root — untrustable at volume.
- **− Scoring degeneracy at the source:** `ga_strength`/`bo_laksana` produce salience that collapses to ~3
  constants (0.58/1.16/2.33) and remedy scores all = 0.28. *Astrological cost:* the strength/importance signal —
  the raw material of ranking — is flat where it must discriminate. (G-H fixed remedy column-selection; the
  salience collapse persists.)
- **− L3 activation empty:** kala_activation / kala_activation_predicates return 0 for the native chart
  (yoga_activation_by_dasha → 0 activated yogas). *Astrological cost:* the timing dimension — WHEN a yoga
  ripens — is absent, so nothing can be time-weighted.

### LAYER B — RETRIEVAL ENGINE (lib/retrieval registry, router, salience, bundling)
- **+ Single-source registry** consumed by both channels (the campaign's core win); capabilities are typed + contracted.
- **+ The tool CONTRACTS are astrologically literate:** assess_career promises "10th lord + Saturn kāraka + D10
  + yoga detection + activating dasha"; get_domain_reading frames by karaka/bhava/lord. The *intent* is right.
- **− RANKING IS BROKEN — THE CRUX DEFECT.** Ranking is single-dimensional (one `computed_salience`) AND
  degenerate: for a career query the top-50 signals are 96% Saturn ashtakavarga bindu-counts (sub-vargas to
  D2700), identical salience, ZERO yogas / ZERO 10th-lord / ZERO raja-yoga. `signature_tier` (meant to elevate
  defining signals) is 100% "background" — unused. *Astrological cost:* the single most important thing — WHAT
  MATTERS — is wrong. A mechanical varga tally outranks a Raja Yoga. This is the difference between data and judgment.
- **− Relevance filtering fails:** get_domain_reading self-reports "bodha_question_lenses has no domain column;
  lenses returned chart-wide" — a *career* query returns a *progeny* lens. Relevance is not enforced.
- **− No astrological structure in the output:** results are flat signal rows (UUID + salience + type), not
  organized by the acharya's reasoning chain (karaka → bhava → lord → dispositor → yoga → dasha → verdict).
- **− Semantic layer (vector_search) exists** (bo_samskara embeddings) but its astrological value untested/thin.

### LAYER C — MCP (platform-mcp: tools, payloads, transport, session)
- **+ Question-shaped tools now exist** (post connector re-add): assess_marriage/career/health/wealth,
  yoga_activation_by_dasha, get_cgm_subgraph, query_chart_facts, vector_search (53 tools). The surface finally
  maps to questions, not just tables — a real step.
- **+ Secure, multi-chart, session-aware** (M0–M8): entitlement-gated, chart-by-name, OAuth, per-model surface hooks.
- **− PAYLOADS ARE UNBOUNDED AND OVERWHELM — pervasive.** Measured live: assess_career = **6.2 MB (~1.5M
  tokens — overflows even a 1M window)**; get_positions (one chart) 63 KB; get_cgm_subgraph "convergence" mode
  53 KB; get_domain_reading pre-fix 17 MB (now 20 KB after F-021R). *Astrological cost:* even the 1M model can't
  receive the chart; and what it receives is 93.8% raw rows, not meaning.
- **− No astrological CURATION at the channel:** the MCP passes through whatever the registry returns; it does
  not shape into a bounded, topic-organized, ranked briefing. It's a pipe, not a presenter.
- **− Per-model shaping (MARO) not delivering:** response_format exists but digest returned empty on one probe;
  the bulk-vs-agentic-loop distinction isn't realized (everyone gets the same dump).
- **− Latency: improved but cache contract unmet** — served_from_cache still false on exact repeat (latency
  20→4ms, cold-start gone via min-instances=1). Enabler, not blocker.

### LAYER D — SYNTHESIS (the apex assess_* tools + the LLM's job)
- **+ The apex tools are correctly CONCEIVED** — reconciled per-domain assessments orchestrating L2+L3+contradictions.
- **− THEY DO NOT SYNTHESIZE (definitive finding).** assess_career = INGREDIENT DUMP: zero prose/verdict;
  93.8% raw signal rows; activating_dasha EMPTY (count 0); citations DEFERRED to another tool; contradictions =
  1,034 raw UUID pairs with resolution_hint null; a progeny lens inside career; 91.5% orphaned. Its own
  judgment_flag calls the output "the assembled bundle." *Astrological cost:* the apex "superlative synthesis"
  surface produces no reconciliation, no weighting, no reading — it ships the pantry, not the meal.
- **− No consumption-mode adaptation:** nothing serves a bulk model a large organized briefing vs. an
  agentic-loop model a bounded drill path. One (broken) shape for all.

---

## PART 3 — THE CRUX: RANKING (why it fails astrologically + what it must become)

Ranking is where "rich data" becomes "acharya-grade material," and it is the system's deepest failure. Today
ranking is **one degenerate scalar** (`computed_salience`) that (a) collapses to ~3 constant values so it cannot
discriminate, and (b) is dominated by one mechanical signal family (ashtakavarga varga bindu counts) so it
surfaces trivia over defining factors. `signature_tier` — the field designed to mark chart-defining signals — is
100% unused.

**Astrological ranking is inherently a COMPOSITE.** To encode judgment, the score for any factor, for a given
question, must combine at least four dimensions the data layer already has the inputs for:
1. **Topic-relevance** — is this factor a significator of the question? (karaka / bhava-lord / bhava-occupant /
   relevant varga). *Source: bg_reference karakas + ga_structural significator paths + bo_drishti lenses (once domain-correct).*
2. **Intrinsic strength** — can the factor deliver? (dignity, shadbala, avastha, vargottama). *Source: ga_strength,
   ga_condition, bg_dignity_reference — once de-degenerated.*
3. **Structural role** — is it a defining combination? (yoga_karaka, raja/dhana/arishta yoga membership,
   argala, centrality in the CGM). *Source: ga_structural yoga_fires + bg_yogas + bo_bimba centrality.*
4. **Temporal activation** — is it LIVE now? (dasha/transit activation). *Source: ka_kalasutra — once populated.*

The intervention (Part 5) is to **replace the single degenerate salience with this composite, weighted by
native-supplied class-priors** (the acharya judgment: e.g. a raja-yoga's structural weight ≫ a D2700 bindu). This
is the one change that most moves the system from warehouse to instrument. **It is native-judgment work** (the
weights are an acharya's, not a coder's default) — hence the beyond-acharya strategic track owns the weighting;
engineering owns making the composite computable + non-degenerate.

---

## PART 4 — IMPACT ANALYSIS (per consumption mode; 1M-class, all four families)

Two modes matter (context size is no longer the differentiator — all four families are 1M-class):
**BULK** (Gemini, DeepSeek V4 Pro one-shot) — wants a large, organized, ranked briefing. **AGENTIC-LOOP**
(Claude, DeepSeek V4 Pro, GPT) — wants bounded, navigable, drill-able results.

| Defect | Bulk-mode impact | Agentic-loop impact | Severity |
|---|---|---|---|
| Ranking degeneracy (Part 3) | FATAL — model gets everything equal-weighted, can't find what matters | FATAL — can't decide what to drill | ★★★★ CRUX |
| No synthesis (assess_* dump) | SEVERE — must reconstruct the reading from raw rows | SEVERE — no verdict to anchor drilling | ★★★★ |
| Unbounded payload (6.2MB) | SEVERE — overflows even 1M; noise crowds reasoning | FATAL — blows the loop's per-call budget | ★★★★ |
| Relevance leak (progeny-in-career) | HIGH — off-topic content dilutes | HIGH — wastes drill steps | ★★★ |
| Machine-grounding orphan (91.5%) | HIGH — unverifiable claims at volume | HIGH — drill-to-fact returns empty | ★★★ |
| L3 activation empty | HIGH — no time-weighting; "when" absent | HIGH — can't answer timing | ★★★ |
| No astrological structure | HIGH — model must impose structure itself | MED — more drilling to assemble | ★★★ |
| No mode adaptation | MED — bulk model under-served (dump ≠ briefing) | HIGH — loop model gets a dump not a path | ★★★ |
| Latency/cache | LOW-MED | MED (loop makes many calls) | ★★ |

**Reading of the matrix:** the top four defects (ranking, synthesis, bounding, relevance) are FATAL/SEVERE in
BOTH modes — they are not model-specific; they are foundational. Fixing ranking + synthesis + bounded structured
delivery serves every family at once. Mode-adaptation is a second-order optimization *on top of* a correct core.

---

## PART 5 — THE FOUR-LAYER INTERVENTION PLAN

Ordered by leverage. Each intervention tagged: [layer] and (mode served).

### I-1 — RANKING RE-MODEL (the crux; highest leverage) [Data + Retrieval] (both modes)
Replace single degenerate `computed_salience` with the **4-dimensional composite** (Part 3): topic-relevance ×
intrinsic-strength × structural-role × temporal-activation, weighted by **native class-priors**. Activate
`signature_tier`. De-degenerate the underlying strength/salience computation (root-cause the constant collapse).
*Acceptance:* for a career query, top signals are 10th-lord / kāraka / D10 / raja-yogas — NOT varga bindu tallies;
scores form a real distribution. **Native input required: the class-prior weighting.** This is Wave 5's spine.

### I-2 — SYNTHESIS CONTRACT (make assess_* actually reconcile) [Synthesis] (both modes)
Decide the fork: (a) tools synthesize server-side into a bounded, cited, reasoned verdict with convergences +
tensions (reconciled, not raw) + activating window + judgment_flags; OR (b) tools hand a small, ranked, resolved
ingredient set the client LLM synthesizes. Recommendation: **(a) for the verdict fields + (b) for the evidence** —
a reconciled verdict PLUS a bounded ranked evidence set, both in one response. Wire mi_darshana (the insight
surface) as the home for reconciled units. *Acceptance:* assess_career returns a career reading (prose or
structured verdict) with ranked evidence + resolving citations + a real dasha window, under a bounded size.

### I-3 — BOUNDED, TOPIC-STRUCTURED DELIVERY [Retrieval + MCP] (both modes)
Every tool returns astrologically-STRUCTURED output organized by the reasoning chain (karaka → bhava → lord →
dispositor → yoga → dasha → verdict), not flat rows — and BOUNDED by default (the F-021R discipline applied
everywhere: cap arrays, dedup, drill-pointers). Fix the domain filter (relevance). *Acceptance:* no tool exceeds
a sane default token budget; output is topic-organized; a career query returns only career-relevant structure.

### I-4 — MODE-ADAPTIVE PRESENTATION (MARO, real) [MCP] (bulk vs loop)
From the one curated core, serve two faces: **BULK** = a single large, organized, ranked chart briefing
(comprehensive, structured, still de-noised) for Gemini/DeepSeek one-shot; **AGENTIC-LOOP** = a lean orient →
drill path with excellent pointers for Claude/GPT/DeepSeek. DeepSeek reachable in both, over the plain backend
(no MCP). Driven by response_format + getMcpSurfaceSpec. *Acceptance:* the two modes return demonstrably
different shapes from the same data; each is optimal for its consumer.

### I-5 — GROUNDING REBUILD [Data] (both modes)
The MSR rebuild against current L1 so constituent_facts resolve (>80% target), restoring machine provenance.
*Acceptance:* drill-to-fact returns real chart_facts; scorecard re-scored. (Retrieval fork; request filed.)

### I-6 — TEMPORAL ACTIVATION POPULATE [Data L3] (both modes)
Populate kala_activation / predicates so yoga_activation_by_dasha and the assess_* dasha windows return live
timing — enabling the temporal dimension of ranking (I-1.4) and any prophecy. *Acceptance:* yoga_activation
returns ripening yogas with windows; assess_* dasha window is non-empty.

### I-7 — ENABLERS [MCP] — cache contract (served_from_cache true on repeat), verbosity levers real, error
envelope uniform. Lower leverage; do alongside.

### Sequencing
I-3 (bounding+structure) + I-6 (activation) + I-5 (grounding) are **prerequisites** that make I-1 (ranking) and
I-2 (synthesis) *possible and trustable*. I-1 + I-2 are the **crux + apex** (native-judgment-gated). I-4 is the
**final optimization** once the core is correct. Do: prerequisites → ranking → synthesis → mode-adaptation.

---

## PART 6 — THE ONE-LINE CONCLUSION
The data layer holds the whole of Jyotish, correctly. The path to the LLM **strips its meaning (flat rows),
loses its weight (degenerate ranking), breaks its provenance (91.5% orphan), drops its timing (empty
activation), and overwhelms the model (unbounded dumps)** — and the apex synthesis tool assembles ingredients
without cooking. **Restore meaning (structure), weight (composite ranking — the crux), provenance, timing, and
bounded mode-adaptive delivery, and a 1M-class model will synthesize acharya-grade insight from data it already
has.** Ranking is the crux; synthesis is the apex; both are native-judgment-gated and are the heart of the
beyond-acharya strategic track.

*End of RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION v1.0.*
