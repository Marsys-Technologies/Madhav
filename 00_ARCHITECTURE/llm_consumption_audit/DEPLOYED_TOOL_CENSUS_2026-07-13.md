---
artifact: DEPLOYED_TOOL_CENSUS_2026-07-13
type: FIRST-CONTACT CENSUS (deployed MCP connector; consumer seat = Cowork/Fable 5)
version: 1.0
status: COMPLETE
method: 4 parallel sub-agents; every non-write tool called once with minimal valid args;
  chart 1c826d5a (Abhinandan); write tools classified without calling; post-rebuild
  (build 762de6e8, priors 1.1). Complements Lane 1a (which censused the LOCAL surgical
  wire); this is the DEPLOYED connector the real consumer uses.
totals:
  tested: 126
  working: 95        # PASS 88 + PASS-OVERSIZE 7 (75%)
  empty: 21          # succeeds, zero rows — mix of honest-empty and data gaps (17%)
  error: 9           # (7%)
  skipped_write: 2   # mimamsa_outcome_record, record_outcome
  retired_aliases: 4 # apex_*_assess (announced disconnected; WP-1.3(i) retirement)
---

# Deployed-Channel Tool Census — 2026-07-13

## ERRORS (9) — register candidates

| Tool | Error | Class |
|---|---|---|
| asset_registry_all / asset_registry_l0 | cockpit registry GET → 401 | auth wiring (system-inventory tools dead to consumer) |
| ref_aspects_at_time_get | sidecar 401 Invalid API key | LCA-13 family CONFIRMED ON DEPLOYED |
| ref_planet_transit_get | sidecar 401 Invalid API key | LCA-13 family |
| ref_retrograde_periods_get | sidecar 401 Invalid API key | LCA-13 family |
| ref_planet_position_get | sidecar 500 — passes literal "undefined" as date | param-mapping bug (alias layer) |
| ref_ephemeris_year_get | 404 Unknown capability URI marsys://resource/ephemeris-cache/year/2026 | unregistered URI (LCA-12 family) |
| ref_transit_rules_get | platform DB query 400 | query bug |
| traverse_graph | "Could not parse address expression: 'l'" — `about` DSL string TRUNCATED TO FIRST CHARACTER | **NEW: the graph's flagship consumer tool is broken at the param layer** (bodha_graph_traverse_get, the alias, WORKS — so the bug is in traverse_graph's own arg handling) |

Interesting: the non-alias twins mostly work (query_aspects_at_time PASS, query_planet_transit
PASS, query_retrograde_periods PASS, bodha_graph_traverse_get PASS) — the breakage
concentrates in the ref_*/legacy alias layer, i.e. registry/param plumbing, not engines.

## EMPTY (21) — split honest vs gap

Honest-empty (correct behavior, good empty_reason): get_temporal_windows & kala_windows_get
(4,568 dated rows exist outside the tested H2-2026 range — engine healthy), lel_query +
mimamsa_lel_query (no LEL corpus for this chart — known), query_calibration +
mimamsa calibration surfaces (STRUCTURAL mode — by design), kala_temporal_bundle
(honest "sidecar unavailable; native data removed by D7 remediation" note).

Data/serving gaps (register-relevant):
- bodha_remedies_get + get_remedies: bo_upaya resonance rows absent for wealth (LCA-5 family)
- phala_predictive_anchors_get: 0 wealth anchors (other domains have rows) — L4 wealth gap
- yoga_activation_by_dasha + kala_yoga_activation_get: 0 activated yogas even over a 3-YEAR
  window — yoga→dasha activation join likely broken (new finding candidate)
- query_mantras / ref_mantras_get: 0 for Venus; ref_remedies_by_planet_get("venus") returns 25
  → **case-sensitivity + backend split**: "Venus" empty vs "venus" 25 rows (filter bug)
- query_remedies / ref_remedies_get: planet filter silently IGNORED (returns jupiter rows for Venus)
- ganita_positions_get: planet="Venus" → 0 rows while unfiltered returns rows (filter vocab)
- list_remedies_by_category("gemstones"), ref_remedies_by_category_list("mantra"),
  query_tantric_remedies / ref_tantric_remedies_get (Venus), ref_yogas_get(wealth): all 0 rows,
  no empty_reason — honest-empty discipline missing on this family
- get_projections: kala_bhavishya empty for wealth/5y

## OVERSIZE (7) — budget-discipline confirmations (R-40/LCA-3 class, live on deployed)

assess_career **748KB** · bodha_domain_reading_get **898KB** · ephemeris_cache_year **815KB**
· assess_marriage 537KB · assess_wealth 163KB · get_cgm_subgraph ~100KB · assess_health 96KB
— plus phala_outlook/outlook_get/anchors/mitigation ~26–35KB and synth_chart_brief ~13KB
(borderline). phala_outlook_get's trim_report cites recover_via "unknown_tool" (alias bug).

## HEALTHY HIGHLIGHTS

- Post-rebuild quality surfaces: bodha_quality/get_chart_quality report 84.15% two-pass,
  **DEFECT-001 RESOLVED (0/68,224 orphans)**.
- The temporal engine serves dated windows (R-45 fix live); kala_projections_get returns
  tier-1 projections peaking 2027-10-20 with falsifiability blocks.
- Graph consumption works via bodha_graph_subgraph_get (hub=Moon, 62 nodes/146 edges,
  motifs) and bodha_graph_traverse_get (path narration).
- muhurta_finder + kala_muhurta_get return ranked, BPHS-cited election windows (T-15 class
  fixed in behavior; 89-day range accepted).
- ganita_special_lagnas_get / query_special_lagnas PASS — **caveat: tested with the
  NATIVE'S (Abhisek's) birth params** since the tool is birth-keyed, not chart-keyed;
  mechanism proven, Abhinandan values still unobtainable without his birth data (the
  chart-id-keying gap stands).
- compute_natal_positions/ganita_natal_positions_compute reproduce FORENSIC anchors.
- holistic_bundle_chart_facts: completes but 5 of its sub-tools error internally (partial).
- intent_classify/util_intent_classify return a classifier PROMPT rather than a
  classification — works-as-built, but note the design: classification is delegated to
  the consuming LLM.

## Full per-tool TSV (as returned by test agents)

### Slice A
assess_career	PASS	748KB bundle; envelope schema present
assess_health	PASS	96KB bundle
assess_marriage	PASS	537KB bundle
assess_wealth	PASS	163KB bundle
asset_registry_all	ERROR	cockpit GET /api/cockpit/registry → 401
asset_registry_l0	ERROR	cockpit GET ?layer=brahmagyan → 401
bodha_chart_digest_get	PASS	9427 signals, Venus top entity, 6 domains
bodha_discoveries_get	PASS	1/1036 discoveries; bo_anveshana v1.0
bodha_domain_reading_get	PASS	898KB wealth reading (oversize)
bodha_graph_subgraph_get	PASS	hub Moon pagerank .0708, 62n/146e, motif
bodha_graph_traverse_get	PASS	10L Saturn→Moon 5 paths narrated
bodha_quality_get	PASS	84.15% two-pass; DEFECT-001 RESOLVED
bodha_remedies_get	EMPTY	0 wealth resonance rows; bo_upaya gap note
bodha_remedies_search	PASS	saturn→resonance .438 + BPHS mantra
bodha_signals_get	PASS	1/1591 wealth signals, 0 orphans
catalog_assets_all	PASS	2/95 assets w/ count_sql + DAG deps
catalog_assets_l0	PASS	2/26 L0 assets
catalog_assets_list	PASS	layer map works
chart_snapshot	PASS	D1 grid, 258B within budget
compute_natal_positions	PASS	PyJHora; matches FORENSIC anchors
event_anchors	PASS	1/2 anchors w/ falsifier
ephemeris_cache_year	PASS	815KB year 2026, 9 bodies (oversize)

### Slice B
ganita_chart_facts_get	PASS	1/5566 facts, more_available honest
ganita_condition_get	PASS	dignity facet serves
ganita_dasha_periods_get	PASS	Saturn MD row as_of honored
ganita_dashas_get	PASS	alias consistent
ganita_nakshatra_get	PASS	chandra bala rows
ganita_natal_positions_compute	PASS	FORENSIC anchors reproduced
ganita_positions_get	PASS*	unfiltered ok; planet="Venus" filter → 0 (vocab bug)
ganita_sade_sati_get	PASS	cycle rows + 15 categories
ganita_special_lagnas_get	PASS*	works w/ native's birth params (not chart-keyed)
ganita_strength_get	PASS	21 strength categories
ganita_structural_get	PASS	aspect facets page
ganita_tajaka_get	PASS	varsha years + hadda lords
ganita_transit_anchors_get	PASS	venus anchor w/ house-from-Moon
ganita_yogas_get	PASS	32 rows
get_cgm_subgraph	PASS-OVERSIZE	~100KB
get_chart_orientation	PASS	digest healthy, 0% unattributed
get_chart_quality	PASS	same as bodha_quality
get_classical_citation	PASS	dhana yoga → uttara_kalamrita
get_dashas	PASS	compact rows
get_domain_reading	PASS	20 ranked signals + CDLM cells + lenses
get_graha_yuddha	PASS	VEN v MAR 0.68° winner VEN, 5 ayanamshas
get_positions	EMPTY	planet filter vocab (unfiltered alias works)
get_projections	EMPTY	kala_bhavishya empty for wealth/5y
get_remedies	EMPTY	bo_upaya gap (honest empty_reason)
get_signals	PASS	ranked, 0 orphans
get_temporal_windows	EMPTY	honest: 4568 dated rows outside tested range

### Slice C
graha_portrait	PASS	v3 envelope, grounding 1.0
holistic_bundle_chart_facts	PASS*	completes; 5 sub-tools error internally
intent_classify	PASS*	returns classifier prompt (design note)
judgment_query	PASS	convergent_moderate wealth; >12KB flag
kala_life_arc_get	PASS	2 parvas
kala_muhurta_get	PASS	7 windows, BPHS ch.46
kala_projections_get	PASS	tier-1 peak 2027-10-20, falsifiable
kala_temporal_bundle	EMPTY	honest sidecar-unavailable note
kala_windows_get	EMPTY	honest out-of-range note
kala_yoga_activation_get	EMPTY	0 in 6-month window
lel_query	EMPTY	no LEL corpus (expected)
list_assets	PASS	3/95 w/ DAG deps
list_entities	PASS	planet entities + cursor
list_my_charts	PASS	4 charts
list_my_sessions	PASS	session pin visible
list_remedies_by_category	EMPTY	gemstones → 0, no empty_reason
mimamsa_calibration_get	PASS	prior_only multipliers, QA 0 fail
mimamsa_insight_get	PASS	2 wealth verdicts, STRUCTURAL
mimamsa_lel_query	EMPTY	no corpus
mimamsa_outcome_record	SKIPPED-WRITE	—
mitigation_map	PASS	2/618 w/ BPHS citations
muhurta_finder	PASS	ranked windows, citation-compliant
pact_query	PASS	chain_pending_activation, window 2053+
phala_anchors_get	PASS-OVERSIZE	~26KB, 100→12 trim
phala_mitigation_get	PASS-OVERSIZE	~30KB
phala_outlook	PASS-OVERSIZE	~28KB
phala_outlook_get	PASS-OVERSIZE	~35KB; trim recover_via "unknown_tool" bug
phala_predictive_anchors_get	EMPTY	0 wealth anchors (others have rows)
phala_rectification_get	PASS	185 candidates, D43 note
prashna_undertaking_get	PASS	honest placeholder notes

### Slice D
query_aspects_at_time	PASS	2 aspects, BG provenance
query_calibration	EMPTY	structural mode
query_chart_facts	PASS	LAGNA pivot w/ fact_ids
query_dasha_periods	PASS	two_pass rows
query_mantras	EMPTY	Venus → 0 (backend split w/ ref_remedies_by_planet)
query_planet_position	PASS	pyswisseph DE441
query_planet_transit	PASS	daily rows
query_remedies	PASS*	planet filter IGNORED (jupiter rows for Venus)
query_remedies_by_planet	EMPTY*	case-sensitive: "Venus" 0 / "venus" 25
query_remedies_for_chart	PASS	wealth → jupiter mantra
query_retrograde_periods	PASS	Venus stations Oct–Nov 2026
query_special_lagnas	PASS*	native birth params (see caveat)
query_tantric_remedies	EMPTY	0 rows, no empty_reason
read_remedy	PASS	full record + BPHS ref
recall_session	PASS	pin visible
record_outcome	SKIPPED-WRITE	—
ref_aspects_at_time_get	ERROR	sidecar 401
ref_classical_citation_get	PASS	dhana row
ref_dasha_systems_get	PASS	functional (low relevance)
ref_dignity_reference_get	PASS	hybrid row
ref_doshas_get	PASS	kala sarpa catalog row
ref_entities_list	PASS	cursor ok
ref_entity_resolve	PASS	Venus→Shukra
ref_ephemeris_year_get	ERROR	404 capability URI
ref_mantras_get	EMPTY	Venus → 0
ref_nakshatra_get	PASS	functional (not revati-specific)
ref_planet_position_get	ERROR	"undefined" date mapping
ref_planet_transit_get	ERROR	sidecar 401
ref_remedies_by_category_list	EMPTY	mantra → 0
ref_remedies_by_planet_get	PASS	25 venus remedies
ref_remedies_chart_get	PASS	wealth mantra
ref_remedies_get	PASS*	planet filter ignored
ref_remedies_search	PASS	wealth row
ref_remedy_get	PASS	identical to read_remedy
ref_retrograde_periods_get	ERROR	sidecar 401
ref_rules_search	PASS	BPHS HIGH row
ref_tantric_remedies_get	EMPTY	0
ref_transit_rules_get	ERROR	DB 400
ref_vector_search	PASS	hybrid ok
ref_yogas_get	EMPTY	wealth → 0
resolve_entity	PASS	epistemics envelope
select_chart	PASS	pin ok
synth_chart_brief_get	PASS-OVERSIZE	~13KB, 30 topics/22 verdicts
synth_tail_divergence_get	PASS	tail row
traverse_graph	ERROR	about-DSL truncated to 1st char
util_intent_classify	PASS*	prompt-returning design
vector_search	PASS	hybrid ok
yoga_activation_by_dasha	EMPTY	0 over 3 YEARS (join suspect)

*qualified pass — see notes above.
