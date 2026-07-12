# LANE 10 — PROMISE-vs-DELIVERY — shard-6

Charter §7.5 (RATIFIED) attribution decision tree. Charts: Abhisek `482012f1-710e-4a25-994a-93821f5871aa`,
Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`. DEPLOYED channel primary (amjis-mcp Cloud Run).
DB=deployed confirmed consistent: get_projections digest `msr_signal_count 13364` = per-ayanamsha; DB
`bodha_msr_signals=66836` = 5 ayanamshas × 13367 ≈ 13364. Same DB, not divergent.

Status: COMPLETE — 7/7 assets graded.

---

## AP-043 ka_tulana (L3) — PROMISE DECLARED (brief) — VERDICT: PARTIAL / compound

Promise (brief L3_KA_TULANA:25-29): QT-4 comparative — ranks windows ACROSS patterns & life-domains
by I-11 composite; head-to-head `compare(A,B)` with dissonance-aware verdict
(proceed/defer/proceed_with_mitigation); multi-domain attention map. Pure serve-time, NO stored rows
(asset_registry: storage_type=service, count_sql=null, "no stored rows").

- **Data plane:** present-by-design (service; inputs = convergences/projections which exist). get_projections
  and kala_projections_get both return real ranked data.
- **Retrieval plane (PARTIAL):** cross-pattern RANKING is served — kala_projections_get returns
  `projections[]` with `projection_rank`, domain, probability_tier, effective_score across domains;
  get_projections returns ranked `entity_profiles[]`. BUT the promised head-to-head `compare(A,B)` with
  dissonance-aware verdict (proceed/defer/proceed_with_mitigation) has NO fronting tool — no compare tool
  exists in the 130-tool deployed list. That facet is retrieval-plane UNREACHABLE (class 1).
- **Ranking/form (DEGRADED):** get_projections top-ranked entity = `"UNATTRIBUTED"` aggregate_score
  64.556, signal_count 299; next entity `KETU` aggregate 0.497 — the multi-domain attention map collapses
  onto one UNATTRIBUTED bucket (130× the next entity). DROWNED (class 7): the "attention map" the promise
  advertises is dominated by an unattributed aggregate — rationale: an acharya reading cannot act on
  "UNATTRIBUTED" as the #1 chart-defining attention target; the 299-signal bucket buries every real graha.
- shortfall_layer = **compound** (retrieval: compare verdict facet; ranking/form: drowned attention map).

---

## AP-044 ka_vighnakara (L3) — PROMISE DECLARED (brief) — VERDICT: SHORTFALL / retrieval-plane

Promise (brief L3_KA_VIGHNAKARA:26-29): danger engine, inverse of ka_sangam; finds & RANKS danger/
avoidance windows ("when NOT to act", exposure/affliction/caution windows). Writes kala_obstruction with
severity + override_score.

- **Data plane: PRESENT.** `SELECT count(*) FROM kala_obstruction`: Abhisek **602**, Abhinandan **638**.
  Rows carry obstruction_type, severity, severity_score, override_score. Writer delivered.
- **Retrieval plane: UNREACHABLE.** kala_temporal_bundle (default) → `"obstructions": []`,
  `convergence_windows": []`, `timeline_excerpt": []`, transit_state `"sidecar unavailable"`. kala_obstruction
  has NO date columns — rows key off convergence_id/signal_id, so they only surface when convergence
  windows surface; the bundle surfaces zero convergences → zero obstructions. kala_windows_get (even with
  wide date args, which were IGNORED — filters echoed default 2026-07-12→2027-07-12) → `activations:[]`,
  `predicates:[]`. NO deployed call in the set a reasonable LLM makes returns any of the 602 danger windows.
  The tool advertises an `obstructions` field that returns [] despite 602 rows → class 4 EMPTY SHELL /
  class 1 UNREACHABLE.
- shortfall_layer = **retrieval-plane**. ranking_form = n/a (nothing served to rank).

---

## AP-045 ka_yojaka (L3) — PROMISE DECLARED (brief) — VERDICT: PARTIAL / retrieval-plane (+data-shape)

Promise (brief L3_KA_YOJAKA:28-32): activation-predicate bridge; classify each L2 signal → signature_class,
bind class template, store CONCRETE activation predicate for ka_sangam/ka_vighnakara to search.

- **Data plane: PRESENT but incomplete-shape.** kala_activation / kala_activation_predicates: Abhisek
  **66836**, Abhinandan **66747**. BUT only **110 / 66836** rows have a non-NULL `activation_start`; **0**
  fall in the default 1-year window. 66726 (99.8%) predicates are DATE-LESS. A "concrete activation
  predicate" that cannot be bound to a date cannot be searched by the date-windowed engines it was written
  for → class 6 UNUSABLE FORM at the data layer.
- **Retrieval plane: UNREACHABLE.** ka_yojaka is an internal bridge (no direct fronting tool); its fruit
  should surface through kala_yoga_activation_get / kala_windows_get. kala_yoga_activation_get →
  `activated_yogas:[]`, `total_count:0`; kala_windows_get → `predicate_count:0`. The 66836 stored predicates
  produce ZERO reachable activations via the deployed channel (partly caused by the date-less data shape
  above). Downstream serving returns nothing the consumer can use.
- shortfall_layer = **retrieval-plane** (data written but not arriving); data-shape defect noted.

---

## AP-046 lel_events (L5) — promise_quote NOT FOUND → RE-SOURCED (asset_registry) — VERDICT: SHORTFALL / retrieval-plane

Re-sourced promise (asset_registry.english_description): "Per-chart user-authored life-event corpus
(occurrence + recording dates, chart-state index). Source data … intaken via the LEL save API.
Availability-driven calibration input; never a prediction-generation source (no-leakage)."
promise_status = **re-sourced** (a real declared promise exists in asset_registry; NOT undeclared).

- **Data plane: PARTIAL (by design).** `SELECT count(*) FROM life_events`: Abhisek **57**, Abhinandan **0**.
  57 real user-authored rows for Abhisek (event_date, category, description, domain all populated);
  Abhinandan 0 is acceptable (availability-driven — no events authored).
- **Retrieval plane: UNREACHABLE.** lel_query (Abhisek, no filters, limit 100) → `"events": []`,
  `"total_count": 0`, provenance source `mimamsa.lel_intake` — serves ZERO of the 57 rows that exist in
  `life_events`. The deployed LEL reader reads an empty/other source (`lel_intake`) while the authored
  corpus sits in `life_events`. class 4 EMPTY SHELL / class 1 UNREACHABLE — the user's own 57 life events
  are unreachable via the tool named to serve them.
- shortfall_layer = **retrieval-plane**. (mimamsa_lel_query alias returned a different envelope shape —
  INCONSISTENT serving, class 3 secondary.)

---

## AP-047 mi_abhilekha (L5) — promise_quote NOT FOUND → RE-SOURCED (asset_registry) — VERDICT: SHORTFALL / compound

Re-sourced promise (asset_registry): "Journal + re-sync service: surfaces due predictions for native
feedback, ingests answers as LEL events, triggers L5-only recompute." promise_status = **re-sourced**.

- **Data plane: EMPTY (both charts).** `SELECT count(*) FROM mimamsa_journal`: Abhisek **0**, Abhinandan
  **0**. The journal has never been populated on either chart.
- **Retrieval plane: UNREACHABLE.** No deployed tool surfaces the journal / "due predictions" read side —
  no `journal` tool in the 130-tool list. record_outcome / mimamsa_outcome_record is the ingest side only.
  The "surfaces due predictions for native feedback" read capability has no fronting tool.
- Both layers fail: nothing written AND nothing servable. class 4 EMPTY SHELL. shortfall_layer =
  **compound** (data-plane empty + retrieval-plane absent). (Structurally consistent with L5 STRUCTURAL
  seal — but the promise is a live service capability, and it delivers nothing on either chart.)

---

## AP-048 mi_adhilepa (L5) — promise_quote NOT FOUND → RE-SOURCED (asset_registry) — VERDICT: PARTIAL / retrieval-plane

Re-sourced promise (asset_registry): "L5 learned-weight overlay on L1–L4 base values; 4 adjustment tables
+ load-bearing sensitivity map (G3)." promise_status = **re-sourced**.

- **Data plane: PRESENT (rich).** mimamsa_load_bearing 5/5, convergence_adjustment 500/500,
  anchor_adjustment 195/200, signal_adjustment 66836/66747, fact_adjustment 59351/59589 (Abhisek/Abhinandan).
- **Retrieval plane: PARTIAL.** mimamsa_insight_get surfaces the load-bearing sensitivity map cleanly —
  insight_type `load_bearing` present (14 hits), reachable & usable. BUT the 4 learned-weight ADJUSTMENT
  tables (126,882 rows for Abhisek) have no direct fronting tool — the raw overlays are internal-only. By
  design they adjust served values silently, but the promise names "4 adjustment tables" as a deliverable
  and none is independently retrievable → the load-bearing facet DELIVERS, the adjustment facet is
  retrieval-plane unreachable (low severity — internal overlay).
- shortfall_layer = **retrieval-plane** (adjustment-table facet). ranking_form = usable (load_bearing clean).

---

## AP-049 mi_bhavisya (L5) — promise_quote NOT FOUND → RE-SOURCED (asset_registry) — VERDICT: DELIVERS

Re-sourced promise (asset_registry): "Time-indexed prospective predictions with confidence + falsifiers."
promise_status = **re-sourced**.

- **Data plane: PRESENT.** mimamsa_predictions 195/200, mimamsa_manifestation_sets 195/200 (Abhisek/Abhinandan).
- **Retrieval plane: REACHABLE.** Prospective predictions with confidence + falsifiers arrive over the
  wire: phala_outlook → `anchors[]` (39 anchor hits, each with falsifier + confidence + query_window
  2026-07-12→2027-07-07); mimamsa_insight_get → `verdict_object` insight_units (e.g.
  `verdict_career_setback`, grade 7.2/10) carrying calibrated statements. kala_projections_get →
  time-indexed projections with explicit `falsifiability.deny_observable` + `confirm_observable` +
  evaluation_date.
- **Ranking/form: USABLE.** Anchors and verdict statements are self-describing, resolvable text with
  falsifiers. Modest promise (prospective predictions + confidence + falsifiers) is MET.
- Note (not a shortfall): mimamsa_insight_get reports `calibration_status: prior_only`, `mode: STRUCTURAL`
  — empirical calibration prior-only is the DECLARED L5 seal state (by design), not unfinished work. The
  granular 195 mimamsa_predictions rows surface in aggregated verdict/anchor form rather than 1:1, which is
  acceptable for the modest promise. shortfall_layer = **none**.

---

### Deployed-payload evidence quotes (verbatim excerpts)
- ka_vighnakara: kala_temporal_bundle → `"obstructions": []` (DB: 602/638).
- ka_yojaka: kala_yoga_activation_get → `"activated_yogas":[],"total_count":0`; kala_windows_get →
  `"predicate_count":0` (DB: 66836/66747; only 110 with activation_start).
- lel_events: lel_query → `"events": [],"total_count": 0` (DB life_events: 57/0).
- mi_abhilekha: mimamsa_journal DB 0/0; no fronting read tool.
- mi_adhilepa: mimamsa_insight_get insight_type `load_bearing` × 14.
- mi_bhavisya: phala_outlook `anchors` × 39 w/ falsifier; mimamsa_insight_get `verdict_object`.
- ka_tulana: get_projections top entity `"UNATTRIBUTED" aggregate_score 64.556 signal_count 299` vs #2 KETU 0.497.
