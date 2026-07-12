# LANE 10 — PROMISE-vs-DELIVERY grading — shard-0

Charter: CHARTER.md §7.5 (RATIFIED decision tree). Grading each asset against its OWN declared intent (4 sources: build brief, asset_registry row, L1 closure doc, MCP tool description). DEPLOYED channel is primary retrieval-plane test.

Charts: Abhisek `482012f1-710e-4a25-994a-93821f5871aa` (native, natal) + Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (natal). Both natal charts.

## Data-plane (verbatim DB counts, both charts, each asset's own count_sql)

| asset | Abhisek 482012f1 | Abhinandan 1c826d5a | target_floor |
|---|---|---|---|
| ga_condition | 2880 | 2895 | 2880 |
| ga_positions | 530 | 530 | 50 |
| ga_nakshatra | 1802 | 1813 | 1802 |
| ga_dashas | 483060 | 471122 | 536471 (multi-chart aspirational) |
| ga_panchanga | 437 | 417 | 221 |
| ga_prashna | 0 | 0 | 0 (BY DESIGN — 0 for natal charts) |
| ga_medical | 45 | 45 | 45 |

## Per-asset grading

### AP-001 ga_condition — DELIVERS (promise re-sourced)
- promise_quote was "NOT FOUND"; re-sourced from asset_registry (source 2): "Unified dignity, avastha (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi), motion state, combustion, naisargika/tatkalika/panchadha friendship, graha yuddha, and a 0–1 condition score per graha per ayanamsha. Amendment 2 … adds per-varga Baladi + Deeptadi avasthas." No dedicated build brief (GA8 structural brief covers a sibling). promise_status=re-sourced.
- Data plane: 2880 (Abhisek) / 2895 (Abhinandan) — exactly meets floor.
- Retrieval (DEPLOYED `ganita_condition_get` chart_id only): returns envelope v1, facet=dignity, real rows e.g. `{"fact_id":"7c0d81772eea3bee","fact_category":"graha_dignity_per_varga","fact_subject":"D33_MOON","fact_value_text":"neutral","fact_value_jsonb":{"sign":"Gemini","house":2,"varga":"D33"...},"verification_pass_status":"two_pass_verified"}`. Self-describing, resolvable text.
- Verdict DELIVERS. shortfall_layer=none. ranking_form=usable.

### AP-002 ga_dashas — DELIVERS (declared)
- promise (brief GA7:8 + asset_registry "Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha"). Largest asset by row count.
- Data plane: 483060 / 471122.
- Retrieval (DEPLOYED `get_dashas` chart_id only): returns rows with resolvable narration, e.g. `{"lord_graha":"Mercury","lord_sign":"Capricorn","start_date":"2010-08-18","end_date":"2027-08-18","level_n":1,"lord_natal_house_d1":10,"lord_natal_nakshatra":"Uttara Ashadha","verification_pass_status":"two_pass_verified"}`. Faceted (system/level/window) with sane defaults.
- Verdict DELIVERS. shortfall_layer=none.

### AP-003 ga_medical — SHORTFALL / RETRIEVAL PLANE (promise re-sourced) ★FINDING
- promise_quote was "NOT FOUND"; re-sourced from asset_registry (source 2): "Per-chart Ayurvedic Jyotish indication summary: dosha aggravation, organ watch, body-part watch, and indication_strength derived from ga_condition condition_score joined with bg_medical_mappings. MEDICAL DISCLAIMER: indication_tier=jyotish_indication; not_diagnosis=TRUE." promise_status=re-sourced.
- Data plane: PRESENT — 45 rows both charts (=floor). Writer computed+stored.
- Retrieval plane: **NO deployed MCP tool serves ga_medical / Vaidya-phala.** Full tools/list enumerated (150+ tools); zero tools expose the ga_medical table. `assess_health`/`apex_health_assess` are L2 Bodha reconciliations (1st/6th/8th lords + Saturn), NOT the L1 ga_medical dosha-aggravation/organ-watch rows. No `ganita_medical*` tool exists (ganita_* family = strength/structural/condition/sade_sati/tajaka/nakshatra/yogas/transit_anchors only). Substring scan for medical|vaidya|ayurved|organ|dosha-aggrav|body-part hit only remedy/muhurta/nakshatra false-positives.
- 7.5 rule 2 → shortfall = RETRIEVAL PLANE, class 1 UNREACHABLE (computed but no reachable path).
- Verdict SHORTFALL. shortfall_layer=retrieval-plane. ranking_form=n/a (never served).

### AP-004 ga_nakshatra — DELIVERS (declared)
- promise (brief GA_NAKSHATRA:8 + asset_registry): "Per-chart parallel nakshatra chart: placement+attribute JOIN … KP sub-lords … per body and house cusp, nakshatra dispositor graph, gaṇḍānta severity flags, tara bala, per-chart statistics."
- Data plane: 1802 / 1813 (=floor).
- Retrieval (DEPLOYED `ganita_nakshatra_get` chart_id only): returns envelope v1 with real rows e.g. `{"fact_category":"chandra_bala_natal_baseline","fact_value_text":"favorable","citation_ref":"...eng=panchanga_engine/2.0.0-P2"}` — tara/chandra bala slice, resolvable text. Broader facets (KP sublords, dispositor graph, gaṇḍānta) reside in chart_facts, reachable via `query_chart_facts`.
- Verdict DELIVERS. shortfall_layer=none. Note (low): dedicated `ganita_nakshatra_get` surfaces only the bala slice of a broad promise; KP-sublord/dispositor/gaṇḍānta facets reachable only via the generic EAV path — a narrowness observation, not a shortfall for the core promise.

### AP-005 ga_panchanga — DELIVERS (declared)
- promise (brief GA4:8 + asset_registry): "Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha."
- Data plane: 437 / 417 (floor 221). 33 panchanga_* categories present incl. panchanga_tithi, panchanga_vara, panchanga_yoga, panchanga_karana, panchanga_nakshatra_moon (all 5 core anga + extended muhurta family).
- Retrieval: no dedicated panchanga tool, but reachable via DEPLOYED `query_chart_facts` (pivoted EAV crosstab) and core anga visible in `chart_snapshot` D1 grid. FORENSIC birth anchors (Shukla Tritiya / Ravivara / Shiva / Garaja) are in this store.
- Verdict DELIVERS (modest promise met; 7.5 rule 4). shortfall_layer=none. Note (low): only reachable path is the generic EAV crosstab dump — no panchanga-specific bundle tool.

### AP-006 ga_positions — DELIVERS (declared)
- promise (brief GA3:8 + asset_registry): "Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)" — the chart_facts spine.
- Data plane: 530 / 530 (floor 50).
- Retrieval (DEPLOYED `get_positions` chart_id only): returns rows e.g. `{"fact_category":"aprakasha_position","fact_subject":"PIDAA","fact_key":"house_d1","fact_value_num":3,"verification_pass_status":"two_pass_verified"}` with graha_position/upagraha/aprakasha categories, resolvable.
- Verdict DELIVERS. shortfall_layer=none.

### AP-007 ga_prashna — DELIVERS (promise re-sourced)
- promise_quote was "NOT FOUND"; re-sourced from asset_registry (source 2): "Per-prashna-chart horary judgment: Prashna-Lagna by each method … Tajik Ithasala/Eesarpha … fructification timing. Only computed when a prashna chart exists for the chart_id; **returns 0 rows for natal charts.**" Briefs exist (PRASHNA_EMBED_ACROSS_LAYERS, PRASHNA_F1_F2_F3_FIX). promise_status=re-sourced.
- Data plane: 0 / 0 — **matches promise exactly** (both charts natal, no prashna chart; target_floor=0). Empty-by-design, not a gap.
- Retrieval (DEPLOYED `prashna_undertaking_get` {chart_id,domain:career}): reachable, returns `{"query_class":"q4_undertaking","domain":"career","action_class":"business_start","composite_undertaking_score":0.253...}` — the fronting Q4 recipe is live.
- Verdict DELIVERS (delivers exactly its conditional promise; 7.5 rule 4). shortfall_layer=none. data_plane=empty (by design).

## Findings (Lane 10)
1. **ga_medical UNREACHABLE (class 1, HIGH)** — 45 rows computed+stored for both charts; NO deployed MCP tool serves the Vaidya-phala table. Retrieval-plane shortfall.

Status: 7/7 assets graded. 1 SHORTFALL (ga_medical), 6 DELIVERS. No undeclared-4source-empty (all three "NOT FOUND" promises re-sourced from asset_registry).
