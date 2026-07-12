# WIRE shard-1a4-b7 — FUSED Lane 1a (synthesizability-as-received, §7.2) + Lane 4 (receipt honesty)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Surgical wire probe, chart 482012f1-710e-4a25-994a-93821f5871aa.
Cross-refs: LCA-1 (DEAD-19 registry tools), LCA-2 (ask_madhav full-pipeline consult broken), LCA-3 (query_chart_facts fact_category/cap/ayanamsha), LCA-7 (msr_sql dishonest truncated).
Note: shared 60 RPM limit is contended by parallel lanes; probes retried with backoff. `probe.sh` was overwritten by a linter mid-run (external), forcing a second pass under a fresh filename — no data lost, all 11 probed.

## Batch B7 tools (11): probed 100%, no skips

| tool | channel | synth | receipt | note |
|---|---|---|---|---|
| query_chart_facts | reachable-surgical | PASS | DISHONEST | LCA-3: fact_category silently ignored; returned_count:100 with NO truncated/total flag vs ~5566 rows; single ayanamsha only |
| query_dasha_periods | reachable-surgical | PASS | HONEST (count) | total:200=actual 200; but 141 KB un-budgeted "compact" dump; 3-ayanamsha fanout (krishnamurti 88 / lahiri 88 / raman 24) undisclosed; lord_natal_shadbala_total NULL on all 200 rows |
| query_calibration | reachable-surgical | PASS | HONEST | qa_summary {total:141, fail_count:0}; verdict_distribution:[] + reliability_curve:[] honestly empty (L5 structural mode, prior_only, n_observations:0) — honest contrast to LCA-7 |
| query_mantras | reachable-surgical | FAIL | HONEST | empty payload: `{"planet":"all","mantras":[],"returned_count":0}` — returned_count:0 truthfully matches empty array. Class 4 EMPTY SHELL / data-plane gap |
| query_planet_position | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2) |
| query_aspects_at_time | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2) |
| phala_outlook_get | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2) |
| phala_mitigation_get | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2); NB mitigation_map IS whitelisted but this phala_* wrapper is not |
| phala_predictive_anchors_get | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2) |
| phala_rectification_get | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2) |
| prashna_undertaking_get | served-only-by-down-pipeline | not-probed | n/a | not in surgical whitelist (LCA-2) |

None of the 11 is a DEAD-19 registry tool (LCA-1 list contains none of them) — the 7 rejects carry `class:validation` "Tool not in surgical whitelist", NOT "Retrieval tool not found in registry".

## Verbatim evidence (E-6)

**query_chart_facts** (requested `fact_category:"shadbala"`) — inner meta echoed:
```
{"chart_id":"482012f1-...","ayanamsha_id":"lahiri_chitrapaksha","shape":"pivoted",
 ...,"returned_count":100,"offset":0,"grounding":{...},
 "provenance":{"table":"chart_facts","note":"fact_id references resolve to the canonical L1 chart_facts table."}}
```
returned_count=100; 22 fact_categories present (dosha_label, arudha_pada×19, midpoint×9, kp_cuspal_significators×5, karaka_chara_position, aspect_jaimini, cusp_kp_lords×12, …) — **ZERO shadbala rows**. Filter ignored. No `truncated`, no `total`; only ayanamsha `lahiri_chitrapaksha`. 119,495 bytes. `warnings:[]`.

**query_dasha_periods**:
```
"facets_applied":{"system":"vimshottari","level":"cap<=3","window":{"start":"2021-07-11","end":"2031-07-11"},"fields":"compact"} ... "total":200
```
200 rows across 3 ayanamshas; every row `"lord_natal_shadbala_total":null`; 141,672 bytes for `fields:compact`.

**query_calibration**:
```
"verdict_distribution":[],"reliability_curve":[],"multipliers":[{"weight_id":"LL1:fam_msr_signal","applied_multiplier":1.4,"n_observations":0,"promotion_status":"prior_only","gate_passed":false,"kill_switch_state":"active"}...],"qa_summary":{"total":141,"fail_count":0}
```

**query_mantras**:
```
{"ok":true,...,"results":[{"content":"{\"planet\":\"all\",\"mantras\":[],\"returned_count\":0}"}],...,"warnings":[]}
```

**7 full-pipeline-only rejects** (identical shape, `<tool>` varies):
```
{"ok":false,"trace_id":"","error":{"class":"validation","message":"Tool not in surgical whitelist: <tool>","remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are: query_chart_facts, query_signals, query_dasha_periods, ... query_mantras, mitigation_map, query_calibration"}}
```

## Determination

- **4 reachable-surgical** (query_chart_facts, query_dasha_periods, query_calibration, query_mantras) — graded on first contact.
- **7 served-only-by-down-pipeline** (query_planet_position, query_aspects_at_time, phala_outlook_get, phala_mitigation_get, phala_predictive_anchors_get, phala_rectification_get, prashna_undertaking_get) — reachable ONLY via ask_madhav (broken consult, LCA-2). Synthesizability unprobeable on surgical wire → not-probed.
- Structural finding: the **entire phala_* product surface (4 tools) + prashna undertaking + planet-position + aspects-at-time** has NO surgical primitive despite peer readers (query_dasha_periods, query_calibration, query_mantras, mitigation_map) being whitelisted. This is a RETRIEVAL-PLANE exposure asymmetry (§7.5 step 2): a whole outlook/mitigation/rectification/prashna surface is surgically un-auditable and served only through the down pipeline.
- **query_calibration is the HONEST counterpart to LCA-7's msr_sql** — where msr_sql lies (`truncated:False` on a top-50-of-13364), calibration returns honestly-empty arrays (`verdict_distribution:[]`, `reliability_curve:[]`) with a matching `qa_summary`.

## Findings

- **1a / class 5 (DISHONEST) — query_chart_facts** — receipt lies by omission & inert filter: requested `fact_category:"shadbala"` returned 100 rows of 22 OTHER categories (zero shadbala), no error/warning; `returned_count:100` carried with NO `truncated` flag and NO `total` against ~5566 chart_facts rows; single ayanamsha (`lahiri_chitrapaksha`) only, undisclosed as a filter. Cross-ref LCA-3. Synth PASS (self-describing, composable) but receipt DISHONEST. Severity: high.
- **1a / class 6 (UNUSABLE FORM) — query_dasha_periods** — 141,672-byte un-budgeted dump for a `fields:"compact"` request; undisclosed 3-ayanamsha fanout (krishnamurti/lahiri/raman) multiplies the dasha tree ~3× (uneven: raman only 24 rows) with no ayanamsha filter echoed in facets_applied; consumer must dedupe. `total:200` is honest but proportionality/DROWNED (class 7 secondary). Severity: medium-high.
- **1a / class 4 (EMPTY SHELL, depth) — query_dasha_periods** — advertised column `lord_natal_shadbala_total` is NULL on 200/200 rows: the strength facet the Mercury-standard depth doctrine (Charter §Doctrine, Depth axis) demands is present-in-schema, never-populated-over-wire. Severity: medium.
- **1a / class 4 (EMPTY SHELL) — query_mantras** — reachable & whitelisted, but first-contact realistic call returns `mantras:[], returned_count:0` for the canonical chart. Synth FAIL (empty). Receipt HONEST (count matches). Root-cause candidate: data-plane (no mantra rows written) vs default `planet:"all"` requiring a specific planet — either way empty on first contact. Severity: medium.
- **1a / class 1 (UNREACHABLE, retrieval-plane) — 7 tools** — query_planet_position, query_aspects_at_time, phala_outlook_get, phala_mitigation_get, phala_predictive_anchors_get, phala_rectification_get, prashna_undertaking_get are fronted by NO surgical primitive; reachable only via ask_madhav (LCA-2 broken). Whole phala outlook/mitigation/predictive-anchors/rectification + prashna + planet-position + aspects surface surgically un-auditable. Severity: high (surface-wide).
- **4 / receipt-honesty PASS — query_calibration** — counters/flags match payload: `qa_summary {total:141, fail_count:0}` consistent; empty `verdict_distribution`/`reliability_curve` honestly empty (prior_only, n_observations:0, gate_passed:false), not falsely populated. Positive anchor; honest contrast to LCA-7. Synth PASS.
- **4 / receipt-honesty n/a — 7 full-pipeline-only tools** — no payload received; receipt unassessable. Logged for coverage honesty (§8 criterion 4): 11/11 probed.
