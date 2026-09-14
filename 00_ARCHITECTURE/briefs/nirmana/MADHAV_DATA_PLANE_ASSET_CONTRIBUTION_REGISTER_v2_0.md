---
artifact: MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER
version: "2.0"
status: PROPOSED
produced_on: 2026-09-13
session_id: MADHAV-DATA-PLANE-V2-20260913
parent_plan: MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md
source_revision: 45120d72dd4e968234d5e77cc1d665e74bc595d6
role: "Complete known identity-level contribution register with provisional component dispositions; not a field-complete, runtime or empirical asset certification."
changelog:
  - "2.0: Maps 123 writer identities and six non-writer identities, plus additional service/answer authorities, to preserved value, exact delta investigations and receiving contracts."
---

# Data-plane asset contribution and preservation register

## 1. How to use this register

This is the asset-level companion to the [master plan](MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md). Every named asset has a consumer contribution, preserved kernel and provisional delta. Exact source findings and their limits are in the [review record](MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md).

**Coverage:** 123 writer identities from `platform/src/generated/nirmana-writer-digests.json` plus six non-writer identities from `platform/src/generated/nirmana-analysis-layer-pins.json` = **129 distinct identities**. Supporting `bo_grounding` is outside the frozen formal L2 count of 22, so this does not change the campaign's frozen 128-member receipt denominator. Additional services/answer authorities in §8 have no invented writer membership.

This is an identity-level contribution review plus selected deep producer/consumer traces. It is not an audit of every field, every caller or live population. Every row's runtime, served-effect and empirical-value status remains **not assessed here**. Existing acceptance evidence is preserved, not negated. No row is an authorized implementation or reopening instruction.

Disposition codes: **P** preserve useful kernel; **I** integrate existing depth; **E** enrich/correct the named part; **Q** qualify semantics/authority; **C** investigate consolidation of a kernel after caller/value proof; **H** retain historical/research/restricted scope. A code does not certify that the rest of an asset needs no changes. No whole-asset retirement is newly recommended; unknown use remains unresolved.

The DP contracts and V consumer journeys are defined in the master. Source prefixes, all relative to this worktree:

- **W** = `platform/python-sidecar/pipeline/orchestrator/writers/`
- **B** = `platform/python-sidecar/brahmagyan/`
- **G** = `platform/python-sidecar/ga_writers/`
- **S** = `platform/python-sidecar/services/`

The source column is the owning implementation or selected entry point, not proof that every output is populated or that the method is doctrinally complete. Grouped/shared writers and shared tables are legitimate and are explicitly preserved. Layer membership and physical/global scope do not determine epistemic type.

## 2. L0 — Brahmagyan: 36 writers and four non-writers

| Asset | Preserve: contribution to the story | Provisional delta and receiving contract | Source anchor |
|---|---|---|---|
| `bg_ontology` | Stable entities, aliases and semantic relations make questions and computations refer to the same thing. | P/I/E: qualify authority, generate adapters, resolve unknowns; preserve physical variants separately. Every normalizer, DP01/10. | B/l0_ontology.py |
| `bg_reference` | Graha/rāśi/bhāva/varga/kāraka/aspect/glossary reference meaning. | P/I/Q: bind meaning to ontology; preserve disabled legacy nakshatra seeding rather than revive a duplicate authority. All calculation/interpretation, DP01/02. | B/l0_reference.py:1336 |
| `bg_nakshatra` | Nakshatra/pada geometry, attributes and relationships. | P/Q/I: retain 27/28 systems, source and scope; chart joins use authoritative static attributes. `ga_nakshatra`, DP01/03. | B/l0_nakshatra.py |
| `bg_dignity_reference` | Dignity, friendship, avasthā and combustion reference kernels. | P/Q/I: reconcile ordinary/deep orb and retrograde-note semantics before uniform reuse; L1 condition and L2/L4 judgments, DP02/04. | W/bg_dignity_reference.py:318 |
| `bg_formula_constants` | Named formula constants, classes, consumer lists and ratification context. | P/Q/E: reconcile different dignity scales and orb meanings; retain named legitimate variants, no blind value unification. DP01/04. | B/l0_formula_constants.py:28,80 |
| `bg_dasha_systems` | System catalog, sequence, applicability and method meaning. | P/Q/I: catalog presence versus executable/chart-applicable distinct; L1 and Kāla system selection, DP02/07. | B/l0_dasha_systems.py |
| `bg_kp_sublord_division` | Global sign-cut sublord geometry. | P/Q/I: retain sidereal-circle grain; explicit chart/cusp convention projection, DP03/07. | B/l0_kp_sublord_division.py |
| `bg_texts` | Original corpus/chunks and retrieval representation. | P/E/Q: edition/rights/context and extraction lineage; scholarly access and rule witnesses, V08/DP02/10. | W/bg_texts.py |
| `bg_text_index` | Keyword/topic discovery over the corpus. | P/I/Q: discovery aid, not doctrinal support; hydrate actual passages. DP02/10. | W/bg_text_index.py |
| `bg_compendium_index` | Chapter/topic navigation and mechanical synopses. | P/I/Q: retain navigation; summaries do not replace passages or executable clauses. V08/DP10. | W/bg_compendium_index.py |
| `bg_rules` | Extracted antecedents, predicates, predictions and source links. | P/E/Q: separate extraction quality, executable qualification, exceptions and predictive evidence. L1–L4 and inquiry, DP02. | B/l0_rules.py:1445 |
| `bg_yogas` | Formation, strength and cancellation definitions. | P/E/Q: clause-level prerequisites/partial states and source variants; firing and structural mechanisms, DP02/05. | B/l0_yogas.py |
| `bg_doshas` | Attributed configuration and mitigation rules. | P/E/Q: preserve exceptions and critical interpretation; not fear labels or inevitable harm. DP02/05. | B/l0_doshas.py |
| `bg_concordance` | Topic × school × text navigation and associated rules. | P/E/Q: current text-level rule aggregates/empty chunk IDs are not passage-level agreement. Source-learning and qualification, DP02/10. | W/bg_concordance.py:186,231,256 |
| `bg_remedies` | Attributed static/corpus-derived practice catalog and review states. | P/Q/I: retain source, applicability, burden and contraindications; no efficacy upgrade. L2/L4 permitted practice, DP02/09. | W/bg_remedies.py; B/l0_remedy_corpus.py |
| `bg_ghatana` | Shared event/state/activity concepts and point/interval/chain shape. | P/E/I: outcome-specific definitions for hypotheses and observations; not private event storage. L2–L5, DP01/09/13. | B/l0_ghatana.py |
| `bg_ephemeris` | Global daily celestial reference samples. | P/Q/I: retain sample resolution versus exact instant; precise engines refine only where needed. L1/L3, DP03/07. | B/l0_ephemeris.py |
| `bg_gochara_arcs` | Unwrapped monotone longitude arcs for efficient search. | P/Q/I: retain interpolation/search bounds and source generation; exact contact consumers, DP07. | W/bg_gochara_arcs.py |
| `bg_sky_calendar` | Ingress/station/eclipse timing and conjunction geometry. | P/Q/I: observer visibility and personal significance require qualified joins. Calendar and Kāla, DP07/08. | W/bg_sky_calendar.py |
| `bg_muhurta_lattice` | Reusable temporal factor families with per-factor provenance/status feeding the separate census. | P/E/Q: global scope is not location-free; reference-location and midpoint approximation explicit; real undertaking/place consumers, DP07/09. | W/bg_muhurta_lattice.py:38–79 |
| `bg_parihara_rules` | Cancellation/activity rules and computed/absent-factor distinctions. | P/E/Q/I: source-qualified exceptions and full required factor coverage; personalized election, DP02/09. | W/bg_parihara_rules.py |
| `bg_transit_engine` | Mean-motion and period-reference substrate. | P/Q/I: shared writer with transit rules is not redundancy; average motion is not precise observation. DP02/07. | W/bg_transit_rules.py; B/l0_transit.py |
| `bg_transit_rules` | Attributed gochara and mūrti rules. | P/Q/I: preserve method/native reference and condition scope; chart-specific activation, DP02/08. | W/bg_transit_rules.py; B/l0_transit.py |
| `bg_kota_chakra_rings` | Ring geometry and attributed partitions. | P/Q/I: preserve school scope; Kota consumer must use actual geometry, DP02/08. | B/l0_kota_chakra_rings.py |
| `bg_vedha_malefic_scale` | Source-attributed obstruction scale. | P/Q/I: keep separate from contact geometry/probability; avoid repeated attenuation of one obstruction, DP02/08. | W/bg_phaladeepika_vedha.py; B/l0_phaladeepika_vedha.py |
| `bg_phaladeepika_latta` | Distinct latta rules within shared vedha seeding implementation. | P/Q/I: retain exact rule family and source identity, not generic adverse vote. DP02/08. | W/bg_phaladeepika_vedha.py; B/l0_phaladeepika_vedha.py |
| `bg_prashna_rules` | Method-specific lagna, significator, yoga and fructification rules. | P/Q/I: qualify full method prerequisites and limits; not every question uses Praśna. DP02/09. | B/l0_prashna.py |
| `bg_vastu_directions` | Attributed directional/spatial doctrine. | P/Q/H: retain study capital; actual spatial service needs its own inputs and horizon approval. DP02/09. | B/l0_vastu_directions.py |
| `bg_medical_mappings` | Traditional graha/body/doṣa correspondences. | P/Q/H: shared seeding writer, distinct subtable; scholarship does not enable individual illness forecasts. V12/DP02. | W/bg_medical_mappings.py:25; B/l0_medical.py |
| `bg_nakshatra_medical` | Attributed nakshatra/body correspondence. | P/Q/H: preserve source-specific meaning and exclusions, not clinical fact. V12/DP02. | W/bg_medical_mappings.py; B/l0_medical.py |
| `bg_sign_medical` | Attributed rāśi/body correspondence. | P/Q/H: same safety and source qualification; no diagnosis or medical timing. V12/DP02. | W/bg_medical_mappings.py; B/l0_medical.py |
| `bg_class_priors` | Shared signal/method/tradition/domain prior coordinates. | P/Q/I: structural/classical/model prior types explicit; not individual empirical probability. DP02/18. | B/l0_class_priors.py |
| `bg_class_lifetime_counts` | Separately tagged count/incidence priors in shared table. | P/Q/I: population/source/horizon units preserved; a shared table does not merge semantic authority. DP02/18. | B/l0_class_lifetime_counts.py |
| `bg_cohort` | Synthetic coordinate/lagna sampling and mahādaśā chains. | P/Q/E: retain engineering reference population; not observed humans or predictive validation. DP17/18. | W/bg_cohort.py |
| `bg_vidhi_primitives` | Existing tool/argument/fallback/known-gap evidence primitives. | P/I/E: keep registry mirror/parity mechanism; scope-aware concepts and discoverability. DP10/11. | W/bg_vidhi_primitives.py; platform/src/lib/vidhi/registry_data.ts |
| `bg_vidhi_floors` | Intent-specific mandatory evidence floors. | P/I/E: floors are minimums; expandable independent omission challenge, not completeness ceiling. DP10/11. | W/bg_vidhi_floors.py |
| `bg_ephemeris_engine` | Numerical service for arbitrary instants. | P/Q/I: backend/frame/node/instant provenance; sign-level probe is limited proof. DP03/07. | platform/python-sidecar/pipeline/orchestrator/service_probes.py:256; routers/ephemeris.py under python-sidecar |
| `bg_panchanga` | Date/place pañcāṅga service. | P/E/Q/I: location/timezone/sunrise convention; distinct from natal `ga_panchanga`. V05/DP07. | platform/python-sidecar/panchang_engine/; platform/python-sidecar/routers/panchang.py |
| `bg_gochara_citation_resolution` | Migration-owned citation-to-verse/chunk resolver. | P/E/Q: retain unresolved cases; citation resolution is not rule qualification. DP02/10. | platform/supabase/migrations/565_bg_gochara_citation_resolution.sql |
| `bg_sarvatobhadra_grid` | School/version-keyed geometry substrate. | P/Q: historical admission intentionally empty; verify actual source/population before claiming either current emptiness or availability. DP02/08. | platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql:17; S/ka_vedha_gochara/writer.py:115 |

## 3. L1 — Gaṇita: 19 writers

| Asset | Preserve: contribution to the story | Provisional delta and receiving contract | Source anchor |
|---|---|---|---|
| `ga_positions` | Canonical longitude, sign, house, nakshatra and pada facts. | P/Q/I: exact subject/frame/node/build/instant qualification; authoritative downstream references. DP03. | G/ga_positions_writer.py |
| `ga_panchanga` | Birth-instant almanac and qualified invariant factors. | P/Q/I: distinguish natal instant from arbitrary-day/place context; preserve per-factor invariance. DP03/07. | G/ga_panchanga_writer.py |
| `ga_strength` | Decomposed ṣaḍbala/bhāvabala, sign-keyed AV grids/reductions/piṇḍas and kakṣyā boundaries. | P/E/I/Q: consume existing richness; contributor prastāra separately computed-but-discarded, not already persisted. Raw/reduced, sign/house and total/component distinctions. DP04/07. | G/ga_strength_writer.py:971–1079; platform/python-sidecar/pyjhora_adapter/strength.py:209–232 |
| `ga_condition` | Dignity, avasthā, motion, combustion/friendship and condition decomposition. | P/I/Q/E: reconcile scale and orb contracts, retain explicit variants; normalized judgment distinct from categorical calculation. DP04. | G/ga_condition_writer.py:53,347,386 |
| `ga_vargas` | Rich divisional positions, own-lagna houses, dignity, deities and variant formulas. | P/E/Q: preserve engine; do not publish fallback Aries/0° as ordinary fact after numerical failure. Preserve input sensitivity and degree semantics. DP03/17. | G/ga_vargas_writer.py:871–1011,2903–2957 |
| `ga_structural` | Aspects/conjunctions, chains, exchange, argalā, lordship and constituent references across divisions. | P/E/I: retain actor/target roles, method and topology into Bodha; no label-only flattening. DP03/06. | G/ga_structural_writer.py |
| `ga_yoga` | Actual formation and cancellation detection. | P/E/Q/I: preserve reusable detector and formed/partial/not-formed distinctions; timing consumes whole configurations. DP05. | G/ga_yoga_writer.py |
| `ga_sensitive_degree` | Point/firing evidence and shared sensitive/yoga-related detectors. | P/Q/I: preserve explicit declination approximation where latitude absent; proximity is not manifestation. DP03/05/07. | G/ga_sensitive_degree_writer.py |
| `ga_sensitive` | Sensitive points, formulas, tolerances and declared unsupported prerequisites. | P/Q/I: honest uncomputed state, point-specific convention and uncertainty. DP03/07. | G/ga_sensitive_writer.py |
| `ga_nakshatra` | KP/star/sub chains, tara, boundary proximity and dispositor cycles joined to L0. | P/E/I/Q: reuse static authority; method-native prerequisites and roles retained downstream. DP03/06. | W/ga_nakshatra.py; G/ga_nakshatra_compute.py; G/ga_nakshatra_emitters.py |
| `ga_dashas` | Nested qualified clock systems, actual applicability and precise ISO boundaries. | P/Q/I: do not reduce precision to date pairs or mistake scope-cap records for real periods. DP07. | G/ga_dashas_writer.py:1005–1078 |
| `ga_sade_sati` | Cycle/phase/quarter structure and method-specific modifiers. | P/Q/I: existing L1 temporal/rule-derived product; separate occurrence, condition and interpretation. DP07/08. | G/ga_sade_sati_writer.py |
| `ga_tajaka` | Annual return, year-lord/Munthā and annual yoga kernels. | P/Q/I: preserve method/year/frame and prerequisites; coherent use alongside other clocks. DP07/08. | G/ga_tajaka_writer.py |
| `ga_transit_anchors` | Natal geometry projected for chart-relative contact joins. | P/I/Q: useful projection, not independent evidence or transit significance. DP03/07. | W/ga_transit_anchors.py |
| `ga_vichara` | Explicitly judged structure, valence, ratification/divergence and leverage. | P/I/Q: maintain epistemic type and adapters for two consumer vocabularies; L1 membership does not make every judgment astronomical fact. DP04/06. | G/ga_vichara_writer.py:2,38–43 |
| `ga_prashna` | Horary-specific eligibility, querent/quesited and qualified fructification structures. | P/E/Q/I: natal zero-output is intentional; average-motion versus exact application/separation must be qualified. DP02/03/09. | G/ga_prashna_writer.py |
| `ga_medical` | Chart-conditioned traditional correspondence computation. | P/Q/H: retain source and unknowns; no individual illness/clinical output admission. V12. | G/ga_medical_writer.py |
| `ga_vastu` | Planetary-direction indications under actual inputs. | P/Q/H: not a complete building/spatial assessment; preserve horizon qualification. DP03/09. | G/ga_vastu_writer.py |
| `ga_ayurdaya` | Attributed method calculations, applicability and explicitly omitted reductions. | P/Q/H: scholarly restricted capital; no mortality/lifespan consumer predictions or fabricated completeness. V12. | G/ga_ayurdaya_writer.py |

## 4. L2 — Bodha: 23 writers including support

| Asset | Preserve: contribution to the story | Provisional delta and receiving contract | Source anchor |
|---|---|---|---|
| `bo_laksana` | L1-referenced structured signals, configuration and condition evidence. | P/I/Q/E: qualify heuristics/NULL hooks; expose all relevant domains/participants/conditions to temporal and inquiry consumers. DP05/06. | W/bo_laksana.py:2186–2565 |
| `bo_laksana_rerank` | UPDATE-only enrichment, structural role/valence and synthesis rollups. | P/I/Q: retain as enrichment of same evidence, not another independent vote. DP06/10. | W/bo_laksana.py:3915–3960 |
| `bo_bimba` | Entity/configuration nodes, membership and chart context. | P/I: identity substrate for mechanisms and search, not rival verdict authority. DP05/06. | W/bo_bimba.py:461–513 |
| `bo_karanajala` | Typed signed graph edges, relationship basis and source membership. | P/E/I/Q: preserve sign/cancellation and all references in consumers; cancellation-reason payload currently NULL is an enrichment gap. DP06/08. | W/bo_karanajala.py:65–110,907 |
| `bo_cgm_paths` | Deterministic dispositor paths, endpoints and cycles. | P/I/Q: hydrate path evidence; topology alone is not an activation prerequisite. DP06/08. | W/bo_cgm_paths.py:1–21,96 |
| `bo_cgm_motifs` | Motif/subgraph candidates and edge lineage. | P/I/Q: discovery hypothesis/navigation, not proven significance from motif presence. DP06/11. | W/bo_cgm_motifs.py:1–17,87 |
| `bo_yantra_mechanism` | Valenced chain/circuit/subgraph objects. | P/I/Q: reusable mechanism representation; preserve typed relationships without physical-causality claim. DP06/08. | W/bo_yantra_mechanism.py:584–630 |
| `bo_sangati` | Complete domain pairs, shared signals and positive/negative linkage. | P/E/I/Q: qualify doṣa-based negative construction; preserve counterpart and underlying drivers, not only net weight. DP06/08. | W/bo_sangati.py:223–323 |
| `bo_cdlm_summary` | Whole-chart cross-domain navigation/statistics. | P/I/Q: hydrate underlying pairs; alphabetical inbound/outbound is not causal direction. DP06/10. | W/bo_cdlm_summary.py:265–291 |
| `bo_pratijna` | v4 occurrence/condition axes and factor/denial ledgers. | P/I/Q: condition[0,10] means affliction magnitude; legacy grade does not replace both axes. Actual v4 lineage, no fabricated MSR refs. DP04/06/08. | W/bo_pratijna.py:107–146,342–410 |
| `bo_arudha` | Qualified perception/standing/domain perspective grounded in L1. | P/I/Q: retain distinct frame, not redundant with natal-house interpretation. DP06/09. | W/bo_arudha.py:1–14,134 |
| `bo_special_lagna` | Distinct Indu/Sree/Ghati/Hora roles and domain salience. | P/I/Q: reference-specific contribution with facts and scope, not universal wealth score. DP06/09. | W/bo_special_lagna.py:1–15,104 |
| `bo_sudarshana` | Static Lagna/Moon/Sun relative-house synthesis. | P/I/Q: preserve separately from temporal annual wheel; one input's views are correlated. DP06/08. | W/bo_sudarshana.py:1–23,166 |
| `bo_vargottama_dhana` | Qualified vargottama/2nd–11th-axis interpretation. | P/I/Q: constituent evidence and scope retained; repetition not independent support. DP05/06/09. | W/bo_vargottama_dhana.py:1–15,114 |
| `bo_nakshatra_semantic` | Star identity, dispositors, tara and boundary-related evidence. | P/I/Q: connect meaningful roles to mechanisms; symbolic/relationship types stay distinct. DP06/08. | W/bo_nakshatra_semantic.py:1–19,109 |
| `bo_upaya` | Condition-to-attributed-practice mapping and source links. | P/I/Q: eligibility constrains permitted action; priority is neither strength nor efficacy. DP02/09. | W/bo_upaya.py:1–25,2155 |
| `bo_samskara` | Semantic retrieval embeddings and versioned text. | P/I/Q: retrieve/hydrate source signals; embeddings not independent evidence or confidence. DP10/11. | W/bo_samskara.py:1–15,189 |
| `bo_anveshana` | Anomaly/broker/discovery candidates with references. | P/I/Q/E: confidence derived from consequence/fixed fragility needs qualification; discovery is a hypothesis. DP06/11. | W/bo_anveshana.py:380–431 |
| `bo_drishti` | Question lenses and wildcard graph traversal. | P/I/E/Q: inquiry entry points, not complete concept coverage or a finished reading. DP10/11. | W/bo_drishti.py:1–13,284 |
| `bo_chart_gestalt` | Zoom spine, pointers and contested-area navigation. | P/I/Q: whole-chart orientation followed by evidence hydration, not summary-only judgment. DP10/11. | W/bo_chart_gestalt.py:1–25,658 |
| `bo_samvada` | Corrected digest view and context-aware navigation. | P/I/Q: preserve real L1 strength/remedy distinction; query-time digest timestamp is not build freshness. DP10/16. | W/bo_samvada.py:60–135 |
| `bo_pramana_mapa` | Actual orphan-reference/quality detectors. | P/I/Q: preserve reachable checks; state only what each detector proves, not all-domain validity. DP03/06/16. | W/bo_pramana_mapa.py:569–645 |
| `bo_grounding` | Supporting source matcher and explicit target classes. | P/I/Q: source-grounding qualification, not empirical or complete interpretive validation. DP02/06. | W/bo_grounding.py:107–170 |

## 5. L3 — Kāla: 22 writers and one retained non-writer

| Asset | Preserve: contribution to the story | Provisional delta and receiving contract | Source anchor |
|---|---|---|---|
| `ka_graha_sancara` | Position/motion service. | P/I/Q: arbitrary instant/frame provenance; self-test is bounded service proof. DP07. | S/ka_graha_sancara/engine.py; W/ka_graha_sancara.py |
| `ka_dasha_kala` | Clock retrieval, ancestry and system traversal. | P/E/I/Q: precise ISO intervals, actual overlap and applicability/failed-system coverage; label approximate subdivisions. DP07/08. | S/ka_dasha_kala/tree_walk.py:45–164; service.py:76–211 |
| `ka_gochara_resonance` | Event-target assembly and provenance. | P/I/Q/C: reconcile structural compilation with Yojaka/Kshetra, preserving unique roles rather than rival promise definitions. DP06/08. | S/ka_gochara_resonance/writer.py:329 |
| `ka_gochara` | Contact/search numerics and generation-bearing materialization. | P/I/Q: separate service/writer/coverage from interpretive conclusion; preserve protected data contracts. DP07/08. | W/ka_gochara.py:180 |
| `ka_gochara_v3_century_materialize` | Numerical refinement, resumability and wide-horizon coverage. | P/Q/H: existing hold remains; eager century-wide work is not itself required user value. No rematerialization here. DP07/16. | W/ka_gochara_v3_century_materialize.py |
| `ka_gochara_sweep` | Protected historical sweep corpus and retired shim. | P/H: preserve current retired registration status; no resurrection or deletion. DP07/16. | W/ka_gochara_sweep.py:6–45 |
| `ka_kota_chakra` | Ring/run primitives and method-specific posture. | P/I/Q: actual source geometry and scope; not an independent adverse vote by default. DP02/08. | S/ka_kota_chakra/logic.py; writer.py |
| `ka_moorti_nirnaya` | Run detection and truncated-ingress safeguards. | P/I/Q: source-adjudicate implemented 27-nakshatra convention before broader authority. DP02/08. | S/ka_moorti_nirnaya/logic.py:1–55 |
| `ka_vedha_gochara` | Typed obstruction and disclosed approximations. | P/I/Q: target-specific role and dependence; avoid duplicate attenuation. DP02/08. | S/ka_vedha_gochara/logic.py:1–72 |
| `ka_sudarshana_varsha` | Annual three-reference wheel. | P/I/Q: preserve actual annual scope; not static `bo_sudarshana` duplication or proof of full sub-daśā. DP07/08. | S/ka_sudarshana_varsha/logic.py:1–43 |
| `ka_tithi_pravesha` | Return bracketing, annual-chart and numerical search kernels. | P/Q/E: named method/equation needs source adjudication; current Moon-longitude return is not accepted merely from name. DP02/07. | S/ka_tithi_pravesha/writer.py:130–193 |
| `ka_yojaka` | Typed activation predicates and fired-yoga participant lookup. | P/E/I/Q/C: full mechanism compiler; preserve paired CDLM signals/roles and method key, not net domain average. DP05/06/08. | W/ka_yojaka.py:479–510 |
| `ka_sangam` | Targeted/exploratory convergence and contact search. | P/E/I/Q: consume full configuration/domains/conditions, not first domain or missing-dignity 0.5. DP06/08. | W/ka_sangam.py:331–377 |
| `ka_kalasutra` | Deterministic interval resolution and recurrence. | P/E/I/Q/C: shared interval kernel with exact peak/horizon/truncation semantics; best-score selection is not nearest search. DP07/08. | W/ka_kalasutra.py:66–116; S/ka_temporal/date_resolver.py:417–588 |
| `ka_vighnakara` | Explicit counter-indicator interface and astronomical calls. | P/I/Q: qualify detector, target and interval; distinguish one underlying obstruction from repeated representation. DP08. | W/ka_vighnakara.py:144 |
| `ka_kshetra` | Typed stages, integration/search, provenance and uncertainty/selection machinery. | P/E/I/Q: retain engineering; preserve signed edges, complete lineage, occurrence/condition and qualified clock jurisdiction before expanding model authority. DP06/07/08. | S/ka_kshetra/stage2_promise.py:317–526; stage3_clocks.py:550–586 |
| `ka_taranga` | Coarse multiresolution trend projection. | P/I/Q/C: candidate projection of common qualified evidence; current grade/convergence averaging is not event probability. DP08/10. | W/ka_taranga.py:120–170 |
| `ka_avadhi` | Period dossiers with L1 references. | P/E/I: enrich qualified participant/condition context and share with chapters. DP08/10. | W/ka_avadhi.py:176 |
| `ka_jivana_parva` | Chapter hierarchy, birth clipping and references. | P/E/I/Q: current fine-period scope is running AD; enrich mechanisms rather than generic keywords; disclose coverage. DP08/10. | W/ka_jivana_parva.py:53 |
| `ka_kala_darshana` | Convergence/obstruction presentation join. | P/I/Q/C: qualify independent net-score authority; global top-750 and NULL→0.5 are not complete personalized search. DP08/10/12. | W/ka_kala_darshana.py:21–33,85–102 |
| `ka_bhavishya_lekha` | Forward packaging and historical outcome references. | P/I/Q/C: shared qualified selection/claim boundary; top-100/five-year filter is not exhaustive future coverage; historical purpose isolated. DP08/12/15. | W/ka_bhavishya_lekha.py:24–115 |
| `ka_tulana` | Comparison service and factor breakdown. | P/I/Q: compare named outcomes/criteria, nearest/strongest/robust separately; self-test not consumer-value proof. DP08/17. | S/ka_tulana/writer.py; service.py |
| `ka_muhurta_seva` | Calendar/action-time computation and search service. | P/I/Q: calendar correctness, personal suitability and outcome are distinct; real undertaking constraints and scope. DP07/09. | S/ka_muhurta_seva/writer.py; service.py |

## 6. L4 — Phala: nine writers

| Asset | Preserve: contribution to the story | Provisional delta and receiving contract | Source anchor |
|---|---|---|---|
| `ph_nimitta` | Rich manifestation anchors with mechanisms, contradictions, precedent and falsifiers. | P/E/I/Q: proposition/event-class-specific joins instead of unordered first class per domain; include method key. Structural confidence not probability. DP09. | W/ph_nimitta.py:452–505 |
| `ph_muhurta` | Personalized election windows using calendar, natal Moon/condition and obstruction. | P/I/Q/E: preserve actual tāra/candra and lord resolution; deferred transit factor 0.5 and 400-anchor cap must be explicit. DP07/09. | W/ph_muhurta.py |
| `ph_pratikara` | Sequenced, conflict-aware mitigation programs. | P/I/Q: L2 owns prescriptions; retain topological/conflict feasibility while binding actual obstruction/domain/window; no efficacy proof from source. DP09. | S/ph_pratikara/engine.py |
| `ph_sankrama` | Cross-domain spillover and competing effects via CDLM paths/windows. | P/I/Q: source-window fallback not independent timing; preserve uncovered-domain/missing-gradient states. DP06/08/09. | S/ph_sankrama/engine.py:215 |
| `ph_sodhana` | Real detectors for inflated confidence, absent falsifiers/derivation and declared contamination. | P/I/Q: preserve build-halt checks; a clean label alone does not prove all upstream lineage. DP09/15. | S/ph_sodhana/engine.py:414 |
| `ph_suddha_sodhana` | Usable/caveated/revision-staged anchor disposition. | P/I/Q: preserve D43 no-auto-approval; corrections bind immutable consumed revisions, no silent issued-claim repair. DP09/16. | S/ph_suddha_sodhana/engine.py |
| `ph_rectification` | Staged birth-time candidates and discrimination gate, no automatic chart mutation. | P/E/Q/H: preserve original event precision rather than fixed month-exact; exposure/history-conditioned hypotheses cannot silently drive event-free forecast. DP14/17. | W/ph_rectification/__init__.py:175 |
| `ph_pramana` | Observable criteria/falsifiers, window states and historical evidence links. | P/E/I/Q: retain hard no-scoring; subject-scope event lookup and separate criteria from event matching. Domain history is not complete observation coverage. DP09/14/15. | W/ph_pramana.py:160–193 |
| `ph_phaladesa` | Per-domain overview of top anchor, contradictions, spillovers and action availability. | P/I/Q: preserve overview; hydrate complete material evidence; event-informed fields require purpose-aware serving. DP09/10/12. | W/ph_phaladesa.py:94,375–386 |

## 7. L5 — Mīmāṃsā: 14 writers and one source asset

| Asset / semantic ownership | Preserve: contribution to the story | Provisional delta and receiving contract | Source anchor |
|---|---|---|---|
| `lel_events` — chart-scoped source | Original admitted observations; intentionally no writer. | P/E/I/Q: reconcile intake, revisions, provenance/precision/purpose and testimony identity. DP13/16. | platform/migrations/691_nirmana_l5_w3_integrity_contracts.sql:100 |
| `mi_jivanaghatana` — chart | Qualified observation provenance, admissibility and chronology projection. | P/E/I/Q: remove unscoped legacy fallback; retain unknown/empty; knowledge time must be claim/revision-specific. DP13/14/15. | W/mi_jivanaghatana.py:184–219 |
| `mi_bhavisya` — chart | Rebuildable generated prediction candidates and manifestation assignments. | P/I/Q: not frozen issued-claim authority; content-complete issuance snapshot and claim linkage. DP09/15/16. | W/mi_bhavisya.py:30–33,222–230 |
| `mi_abhilekha` — global service/chart updates | Journal-to-prediction lifecycle reconciliation. | P/E/I/Q: structured explicit adjudication instead of substring outcomes; unknown/partial/disputed/unobserved retained. DP15. | W/mi_abhilekha.py:28 |
| `mi_pramana` — chart | Actual match/falsifier kernels and dimensional reporting. | P/E/I/Q: match-score-derived verdict is not independent forecast calibration; frozen probability, outcomes and denominator contract. DP15/18. | W/mi_pramana.py:329–359,480–550 |
| `mi_kula` — global catalog | Evidence-family IDs, classical priors/bindings and controls. | P/I/Q: preserve global ownership; family membership/version is not validation or personal truth. DP01/15/18. | W/mi_kula.py:286 |
| `mi_gunanaka` — chart/proposal snapshots | Shrinkage, divergence bounds and candidate learned-weight mathematics. | P/Q/H: retain proposal snapshots; sample count/not_assessed input does not qualify serving or held-out validity. DP18. | W/mi_gunanaka.py:87,125–155 |
| `mi_adhilepa` — chart | Non-destructive overlays and dependency explanation. | P/I/Q/H: approved immutable snapshot/model admission required; mutable multipliers/kill-switch not enough. Ranked multiplier is not ablation proof. DP16/18. | W/mi_adhilepa.py:139–177 |
| `mi_pariksha` — chart | Historical probes, attribution/controls/ablation/discovery harness. | P/E/Q/H: enforce actual declared cutoffs before blind claims; structural labels preserved; no autonomous research activation. DP14/17/18. | W/mi_pariksha.py |
| `mi_sambandha` — chart | Manifestation-channel grammar and prior/assignment/observed distinction. | P/I/Q: retain NULL for unmeasured attribution; qualify coverage and frozen channel definitions, not automatic tuning. DP09/15/18. | W/mi_sambandha.py:110 |
| `mi_darshana` — chart | Provenance-rich insight units, including negative/historical knowledge. | P/I/Q: purpose/exposure partition before common retrieval; no embeddings claimed from this writer. DP10/14/18. | W/mi_darshana.py |
| `mi_seva` — global service verifier | Intended serve-time service infrastructure. | P/E/Q: current four-table existence check proves only that; require actual authorized service and consumer-effect proof later. DP10/18. | W/mi_seva.py:25 |
| `mi_vistara` — global service/export ledger | Append-only export/disclosure receipts and reproducible package infrastructure. | P/E/I/Q: verify exporter wiring, payload identity/scope and delivered artifact; no artificial chart build rows. DP12/16. | W/mi_vistara.py |
| `mi_bhara` — chart evaluation/shared model infrastructure | As-built field skill/GOF, forward-chaining/shrinkage library and model-version pinning. | P/Q/H: current orchestrator explicitly does not refit while basis columns pending; preserve research kernel, no claim of active personal tuning. DP15/18. | W/mi_bhara.py:227–245 |
| `mi_sankalpa` — chart intervention ledger | Elected action/performance/event linkage and status-preserving attestations. | P/I/Q/H: retain explicit-filing FK/native attestation; observational arms are not randomized or causal-efficacy proof. DP13/15/18. | W/mi_sankalpa.py |

## 8. Additional capital outside the 129-identity denominator

| Responsibility / representative source | Preserve and align | Required proof / owner boundary |
|---|---|---|
| `ga_chart_service`; `brahmagyan/ganita/engine.py`, `pyjhora_adapter/compute.py`, `routers/pyhora.py`, `routers/ephemeris.py` under python-sidecar | P/I/Q: numerical on-demand service, preserve kernels and current routes. | Resolve historical service ID to callable implementation, frame/node variants and stored-fact parity; no claim all historical tools are reachable. DP03/07. |
| Capability catalog, `platform/src/lib/retrieval/registry/types.ts` and `catalog.ts`; Vidhi source/parity checker | P/E/I: extend existing discovery/purpose/field contracts. | Specific concept/field → exact access path → relevant computation → finding; not tool-count coverage. DP10/11. |
| L2 signal query `registry/layers/L2_bodha/query_signals.ts` | P/I/E: preserve explicit projection whitelist and pagination; hydrate complete relevant records. | Fields available outside default projection must survive intended consumer/synthesis path. DP06/12. |
| D8 assessment, D9 judgment, D10 pact in `registry/layers/register_d*.ts` | P/Q/E/C: retain staged evidence/flags and useful deterministic narration. | Qualify composite→denial and partial bhaṅga coverage; one shared operator may replace rival judgment kernels only after comparison. DP09/11. |
| Synergy, aggregation and spine bundles in retrieval registry | P/I/Q/C: efficient composition and whole-chart orientation. | Do not invent independent evidence from repeated bundles or drop contradictions and secondary domains. DP06/10/12. |
| Paripraśna adaptive pipeline, `pipeline/synthesis_stage.ts`, `pipeline/reading_parts.ts` | P/E/I: existing multi-pass engine, block state, snapshots and persistence. | Expandable obligation and omission checks; complete material findings; incomplete/resumable on limits, not endless calls. DP11/12/16. |
| MCP managed inquiry/status and raw tool/resource/prompt registrations; `platform-mcp/src/lib/response_budget.ts` | P/I/E: preserve tool discovery, managed jobs, honesty fields and protected payload parts. | Managed evidence/reading parity; raw-client narrower guarantee; actual full delivery beyond summary/cap. DP10/12. |
| L4 `query_domain_result.ts`; L5 discovery/insight/retrodiction retrieval | P/I/E/Q: preserve drillable summaries and qualified research access. | Rich narration/ledger hydration; indirect historical lineage cannot be laundered through `lel_capable:false`. DP10/12/14/18. |
| MCP `lel_event_writer.ts`, admin `api/lel`, `lel/writer.ts`, timeline/creation/chat intake | P/E/I/Q: preserve usable subject-scoped upserts and original testimony. | Resolve canonical intake; revision-known timestamps, legacy file path, all subject/purpose boundaries. DP13/16. |
| `brahma_prospective_ledger` / `lib/lel/prospective_ledger.ts` | P/I: retain explicit-filing ledger and intervention linkage. | Distinct issuance family, not interchangeable with generated candidates or Samīkṣā detection. DP15. |
| `brahma_mimamsa_prediction_ledger` / `lib/pariprashna/samiksha/schema.ts` | P/I/Q: retain detected/confirmed lifecycle and copied provenance. | Original model probability, operator band and full consumed content retain correct freeze points; no duplicate scoring across ledgers. DP15. |
| Model registries/pins, proposed snapshots, scorecard/qualification services | P/Q/H: useful shared evaluation capital. | Actual admission, immutable version and purpose/cutoff rules; dormant service/table existence not authorized model use. DP18. |
| Calendar/profile/source-reader/export/share/operator consumers | P/I/E: retain useful routes/components and existing qualified data. | Same meaning and context through selection, drill, save/replay/export; operator completion not consumer or astrological validity. DP10/12/16. |

## 9. Candidate consolidation and enrichment choices

These are **investigations**, not deletion recommendations:

| Candidate responsibility | Existing useful parts | Decision test |
|---|---|---|
| Structural target compiler | Yojaka, resonance target mapping, Kshetra promise graph | One qualified participant/condition compiler with preserved specialized adapters versus several independent premise definitions. Compare complete mechanism semantics and callers. |
| Temporal interval/search kernel | Daśā service, Sangam, Kalasutra/date resolver, Kshetra clocks/contact engines | Reuse exact computations and scoped materializations; separate nearest/strongest/horizon selectors. Similar outputs are not proof of same method. |
| Temporal views | Taranga, Kāla Darshana, Avadhi, Jivana Parva, Bhavishya Lekha | Retain useful trend/chapter/window views over common evidence; retire only unjustified independent scoring after value/consumer comparison. |
| Manifestation publication | Nimitta, Phaladesa, Sankrama, Sodhana, Suddha Sodhana, Pramana | Preserve distinct anchor, cascade, quality, staged-correction, criteria and overview roles; consolidate only duplicated judgment kernels. |
| Source navigation and authority | Text/index/compendium/concordance/rules | Navigation may share indexing; passage support and rule qualification stay different responsibilities. |
| Priors and model overlays | L0 class/count priors; L5 family, multiplier, overlay and field-fit artifacts | Shared physical tables do not collapse classical, engineered and empirical authority; no automatic model-serving path. |

New value candidates should begin as exact contract gaps: contributor-level AV where it discriminates a relevant question; source-qualified missing condition/cancellation reasons; scoped method-native return equations; richer manifestation bridges; complete historical revision chronology; and actual controlled comparisons. Each needs a consumer, source/computation basis, cost and test. No new writer is assumed necessary.

## 10. Next layer-plan obligations

The responsible layer analyst converts each provisional row into a field-level input-use contract, proving producer semantics, actual direct/transitive consumers, present population/generation where needed and the unique contribution. Inspect dormant, service, dynamic, audit and historical callers before considering retirement. Carry unresolved use explicitly.

A recommendation of **preserve fully** is earned only after the relevant unchanged kernel/interface passes the desired contract; it cannot be inferred solely from this identity-level pass. Conversely, a finding in one projection does not justify discarding its producer. The objective is maximum useful preservation with no compromise on the product's needed distinctions.
