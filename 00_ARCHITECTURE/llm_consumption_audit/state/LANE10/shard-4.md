# LANE 10 — PROMISE-vs-DELIVERY — shard-4

Charter §7.5 (RATIFIED). Grading each asset against its OWN declared intent (4 sources:
build brief, asset_registry row, layer closure, MCP tool description). DEPLOYED channel
(amjis-mcp) primary. Charts: 482012f1 (Abhisek, primary) + 1c826d5a (Abhinandan).

Deployed tool inventory relevant to shard: bodha_chart_digest_get, bodha_domain_reading_get,
bodha_remedies_get/_search, kala_projections_get, kala_windows_get, kala_yoga_activation_get
(=yoga_activation_by_dasha), kala_life_arc_get, query_planet_transit (=ref_planet_transit_get),
get_dashas, kala_temporal_bundle.

---

## AP-029 bo_samvada (L2) — UCD / gestalt + navigable spine — VERDICT: PARTIAL (ranking-form)
Promise (brief:28-33): "the LLM's FIRST retrieval ... whole chart's skeleton ... the chart's
GESTALT ... AND the navigable spine of the whole judgment substrate."
- DATA PLANE: present. `vw_chart_digest` = 5 rows on BOTH charts (482012f1=5, 1c826d5a=5).
- RETRIEVAL PLANE: reachable-deployed. `bodha_chart_digest_get` returns a usable header skeleton:
  `digest`={msr_signal_count 13364, yoga_count 15, dosha_count 22, avg_salience 0.6592,
  max_salience 2.99, contradiction_count 0, weakest_graha Mercury, top_priority_class medium}.
  Header skeleton = DELIVERED cleanly.
- RANKING/FORM: degraded (class 7 DROWNED). The `entity_profiles` spine's #1 entity is
  `entity=UNATTRIBUTED, entity_type=unattributed, signal_count=299, aggregate_score=64.557` vs the
  next real entity `KETU aggregate_score=0.497`. The navigable-spine's top node is a 299-signal
  unattributed bucket (R-44 anchor pattern resurfacing in the gestalt). Entity navigation still
  works below it (grahas + top_signals carry headlines + ids), so PARTIAL not SHORTFALL.
- Finding: class 7 DROWNED, med — the "navigable spine" ranks an UNATTRIBUTED(299) bucket first.

## AP-030 bo_sangati (L2) — the DOMAIN EVIDENCE LEDGER (Move 1) — VERDICT: SHORTFALL (data-plane)
Promise (brief:32-36): "the weight-of-evidence engine: per domain, the full EVIDENCE LEDGER
(support / oppose / independent-weight / cross-tradition / net-verdict / confidence / dissents)."
Brief §4 is explicit: centerpiece stored on `bodha_cdlm_domain_rollups` or `bodha_domain_evidence_ledger`
with columns supporting_signal_ids[], independent_support_count, verdict_class, confidence, dissents_jsonb.
- DATA PLANE: EMPTY for the graded promise. `bodha_domain_evidence_ledger` table DOES NOT EXIST.
  `bodha_cdlm_domain_rollups` columns = {rollup_id, ..., total_inbound_linkage, total_outbound_linkage,
  diagonal_density, signal_count_for_domain, top_3_linked_domains_jsonb, contradiction_density,
  pattern_markers_for_domain_array, ...} — NO supporting/opposing signal lists, NO independent_support_count,
  NO verdict_class, NO confidence, NO dissents_jsonb. The promised evidence-ledger facets were never
  computed/written. (The CDLM *linkage matrix* `bodha_cdlm_cells`=70 rows both charts IS built — but that
  satisfies the registry's "Domain links (CDLM)" line, NOT the graded promise_quote evidence ledger.)
- RETRIEVAL PLANE: unreachable (moot). No deployed tool serves a support/oppose/verdict/confidence/dissents
  ledger. `bodha_domain_reading_get(domain=career)` returns `question_lenses` whose
  `template_element_ids_jsonb.signal_ids` is a bare wall of ~70+ signal UUIDs with no text (class 6 UNUSABLE
  FORM, secondary) — not an evidence ledger.
- Findings: (a) class 4 EMPTY SHELL / class-1-by-nonexistence, HIGH — promised weight-of-evidence engine
  (net-verdict/confidence/dissents/independence-dedup) never built at data plane. (b) class 6, low —
  domain_reading emits unresolved signal-UUID wall.

## AP-031 bo_upaya (L2) — Remediation Map (RM) — VERDICT: DELIVERS
Promise (brief:41-46): "(a) the RESONANCE map ... (b) per-tradition × per-category PRESCRIPTIONS grounded to
L0 brahma_remedy_corpus (every remedy CITED, never invented) ... the instrument's 'what can be DONE' surface."
- DATA PLANE: present. `bodha_rm_resonances`=45 both charts; `bodha_rm_remedy_prescriptions`=135 both charts.
- RETRIEVAL PLANE: reachable-deployed. `bodha_remedies_get` returns resonances(9)+prescriptions(27); each
  prescription carries {tradition, sub_tradition, remedy_category, remedy_label_human, classical_citation,
  classical_strength_rating, feasibility_score}. Sample citation grounded to G27 corpus:
  citation_human="G27 remedy mercury_matrix_mantra for Mercury" — cited, not invented. (a)+(b) both met.
- RANKING/FORM: usable. Self-declared `data_gap_note`: `associated_doshas_array` and
  `estimated_cost_inr_range_jsonb` are 100% NULL every chart (honestly disclosed, derived substitutes given).
- Finding: class 6-adjacent partial, LOW — two ancillary facets (formal dosha tagging, INR cost) NULL;
  NOT in promise_quote and honestly flagged. Core promise fully delivered → DELIVERS.

## AP-032 ka_avadhi (L3) — Period Dossiers — VERDICT: SHORTFALL (retrieval-plane); promise RE-SOURCED
promise_quote was "NOT FOUND"; re-source hit source #2 (asset_registry.english_description):
"Per-dasha-period dossiers: ... lord condition (refs to chart_facts), activated promise-register IDs (from
bodha_pratijna), and sublord modulation. Powers 'how will my Ketu dasha be' readings." → promise DECLARED.
- DATA PLANE: present. `kala_avadhi` = 1571 rows (482012f1), 1585 rows (1c826d5a). Fully computed.
- RETRIEVAL PLANE: UNREACHABLE. NO deployed tool reads `kala_avadhi`. grep of platform/src/lib/retrieval +
  all platform retrieval/mcp/registry source for `kala_avadhi` = ZERO hits (only asset_registry_seed.ts).
  `kala_life_arc_get` serves `kala_jivana_parva` (a DIFFERENT asset), not kala_avadhi. The "how will my Ketu
  dasha be" dossiers (1571 rows) cannot reach any consuming LLM.
- Finding: class 1 UNREACHABLE, HIGH — 1571/1585 dossier rows computed+stored, zero serving path.

## AP-033 ka_bhavishya_lekha (L3) — forward projections / prediction records — VERDICT: DELIVERS
Promise (brief:28-32): "the prediction-record emitter — the L3→L5 LEARNING HOOK ... feature-tagged,
falsifiable, calibratable PREDICTION RECORD."
- DATA PLANE: present. `kala_bhavishya` = 95 rows (482012f1), 100 rows (1c826d5a).
- RETRIEVAL PLANE: reachable-deployed. `kala_projections_get` returns projections carrying probability_tier
  (tier_1_high), domain, effective_score, peak/window dates, `narrative`{headline, probability_statement,
  caveat}, and `falsifiability`{deny_observable, evaluation_date} — feature-tagged + falsifiable + calibratable.
- RANKING/FORM: usable. Delivered form matches the promised falsifiable prediction record.
- Finding: class 3 INCONSISTENT (promise-record), LOW — brief §3.1 names the table `kala_prediction_records`
  but the built/served table is `kala_bhavishya` (kala_prediction_records DOES NOT EXIST in DB). Cross-source
  promise disagreement per §7.5 rule 6; delivery unaffected → DELIVERS.

## AP-034 ka_dasha_kala (L3) — Daśā-eligibility SERVICE — VERDICT: SHORTFALL (retrieval-plane)
Promise (brief:26-29): "given a target structural signature and a time horizon, it returns the scored set of
time-intervals during which the daśā plane makes that signature LIKELY to fire." asset_kind=service, no table.
- DATA PLANE: n/a (service; underlying chart_dashas exist, reachable via get_dashas — but that is raw chains,
  not scored eligibility).
- RETRIEVAL PLANE: UNREACHABLE as promised. NO deployed tool exposes "scored eligibility for a target
  structural signature over a horizon." Nearest surface `yoga_activation_by_dasha` (kala_yoga_activation_get)
  returns EMPTY: with dasha_period=Saturn → `activated_yogas:[], total_count:0`; default window likewise
  `activated_yogas:[]` (class 4 EMPTY SHELL). No signature→scored-interval service is callable over the wire.
- Findings: (a) class 1 UNREACHABLE, MED-HIGH — scored dasha-eligibility service has no deployed front.
  (b) class 4 EMPTY SHELL, MED — the adjacent yoga-activation surface returns zero on both default + scoped.

## AP-035 ka_gochara (L3) — transit-EVENT-search SERVICE — VERDICT: SHORTFALL (compound)
Promise (brief:27-31 + registry): "the transit-search SERVICE: given a trigger condition ... live-computes
WHEN that condition holds ... Finds aspect crossings, conjunctions, ingresses, returns, stations, eclipse
proximity, multi-planet confluence, and transit-to-transit events ... Lahiri sidereal throughout."
- DATA PLANE: n/a (live-compute service).
- RETRIEVAL PLANE: mostly UNREACHABLE. The only deployed transit tool `query_planet_transit`
  (=ref_planet_transit_get) returns a RAW DAILY LONGITUDE SERIES (rows of {date, tropical_longitude,
  sign_number, degree_in_sign, nakshatra_number, is_retrograde, speed_dps}). It performs NO event search:
  no aspect-crossing / conjunction / return / station / eclipse-proximity / multi-planet-confluence finder is
  callable. A consuming LLM must hand-derive every promised event type from a daily series (ungoverned).
- RANKING/FORM: WRONG frame (class 2). The served series is TROPICAL ("tropical_longitude", "tropical sign
  number") whereas the promise is "Lahiri sidereal throughout." e.g. Jupiter 2026-01-01 tropical_longitude
  111.292281, sign_number 4 — tropical, not the promised sidereal frame.
- Findings: (a) class 1 UNREACHABLE, HIGH — promised event-search engine ("the engine the audit found was
  never built") has no deployed search path; only raw ephemeris series. (b) class 2 WRONG, MED — deployed
  transit series is tropical, contradicting the sidereal promise → shortfall_layer=compound.

---
Shard-4 complete. 7/7 assets graded. DELIVERS=2 (bo_upaya, ka_bhavishya_lekha),
PARTIAL=1 (bo_samvada), SHORTFALL=4 (bo_sangati data-plane, ka_avadhi retrieval,
ka_dasha_kala retrieval, ka_gochara compound). Re-sourced promises=1 (ka_avadhi).
