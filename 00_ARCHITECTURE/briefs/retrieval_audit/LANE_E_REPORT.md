---
artifact: LANE_E_REPORT.md
lane: E — Data-plane & service coverage reality
audit_subject: RETRIEVAL_STRATEGY_v1_0.md §5.2/§5.3 census + RETRIEVAL_PLANE_ELEVATION_PLAN §8 R-1.5
authored_by: Claude (opus, high effort), 2026-07-19, Lane E of the retrieval audit swarm
governing_brief: 00_ARCHITECTURE/briefs/RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §E Lane E
dsn_status: UNVERIFIABLE-NO-DSN — no live/dev Postgres DSN in env or any non-example .env;
  all row-count claims marked UNVERIFIABLE-NO-DSN. Physical inventory done from migration DDL.
constraints_honored: READ-ONLY on platform/** and platform-mcp/**; no DB writes; no source edits.
---

# Lane E — Data-plane & Service Coverage Reality

## 0. Method & the two structural caveats that condition every count

**Serving surface is NOT one directory.** The strategy census method ("migration
inventory × retrieval-source grep") appears to have grepped `platform/src/lib/retrieval/`
only. The live served surface is actually **three parallel paths**, all wired into the
MCP server (`platform-mcp/src/server.ts`):
1. the registry layers `platform/src/lib/retrieval/registry/layers/L{0..5}_*` bridged by
   `registerRegistryBridgeTools` (server.ts:348) + `registerP1{Ganita,Reference,Synthesis,Alias}Tools`
   (server.ts:353-357, all four imported & called — verified);
2. hand-registered MCP tools `platform-mcp/src/tools/register_p1_*.ts` and standalone tools;
3. the older `platform/src/lib/tools/brahma/*` layer, reachable through `tool_name_bridge.ts`.
**A single-directory grep produces false-dark classifications** — this is the root cause of
several stale §5.2 claims below.

**Two disjoint migration histories.** `platform/migrations/` (142 files, max #453 — the
authoritative set per the `create-migration` skill) and `platform/supabase/migrations/`
(186 files, max #434) share only 23 sequence numbers and have entirely disjoint filenames.
A table CREATEd in either exists in the DB, so physical inventory = the UNION. Exact per-layer
counts depend on reconciling retirement (DROP) history against the live DB — **UNVERIFIABLE-NO-DSN**.

---

## 1. Census re-verification (strategy §5.2 physical inventory)

Union of `CREATE TABLE` across both migration dirs, deduped by table name = **261 unique tables**.
Per-layer physical inventory (union; drop-then-recreate staging noise not netted out):

| Layer | Prefix | Union CREATE count | platform/migrations | supabase/migrations | Strategy §5.2 claim | Verdict |
|---|---|---|---|---|---|---|
| L0 | `bg_` + `reference_` | 21 + 18 = 39 | 17+5 | 4+13 | "13 tables" (catalog stratum) | **STALE — undercount**; physical L0 catalog ≈ 39 (bg_ 21, reference_ 18) |
| L1 | `chart_` + `ga_` | 9 + 7 | 4+7 | 6+0 | (not itemized) | inventoried |
| L2 | `bodha_` | 36 | 36 | 32 | **"34 tables behind 14 assets"** | **CONFIRMED-APPROX** (32–36 band; 34 sits inside it) |
| L3 | `kala_` | 11 | 4 | 12 | (not itemized) | inventoried |
| L4 | `phala_` | 11 | 5 | 15 | (not itemized) | inventoried |
| L5 | `mimamsa_` | 28 | 29 | 11 | **"27 tables behind 12 assets"** | **CONFIRMED-APPROX** (27–29 band; 27 sits inside it) |

- **L2 = 34 behind 14 assets → CONFIRMED-APPROX.** Physical `bodha_` = 32 (supabase) to 36
  (platform/migrations union). The delta from 34 is retired/staging tables (`bodha_graph`,
  `bodha_graph_edges`, `bodha_graph_staging`, `bodha_signals`, `bodha_signal_embeddings`,
  `bodha_remediation`, `bodha_remediation_staging`, `bodha_resonance`, `bodha_domain_links`
  — all in the DROP-TABLE set, legacy pre-rebuild L2). Exact live count = UNVERIFIABLE-NO-DSN.
- **L5 = 27 behind 12 → CONFIRMED-APPROX.** Physical `mimamsa_` = 28 union / 29 in
  platform/migrations. Within tolerance; the extra is staging/dropped (`mimamsa_export_log_staging`,
  dropped-and-recreated `mimamsa_calibration`/`_multipliers`/`_predictions`/`_qa_eval`).
- **L0 "13 tables" → STALE (undercount).** The L0 catalog stratum is physically ~39 tables
  (21 `bg_` + 18 `reference_`), not 13. The "13" likely counted only the served/notable subset.

---

## 2. The dark set (a)–(e) — per-claim verdicts

Serving-reference counts from `rg` over `platform/src` + `platform-mcp/src` (tests excluded),
then each nonzero ref hand-classified as **live-serving** vs **incidental** (cockpit
`assetClearSpec.ts` DELETEs, migrations, comments).

### (a) L0 `reference_*` / `bg_*` catalog stratum — **STALE / PARTIALLY WRONG**
Claim: "the entire L0 catalog stratum (13 tables) dark." Reality is a **mix**:

| Table | serving refs | Disposition | Evidence |
|---|---|---|---|
| `reference_aspects/signs/planets/nakshatras/vargas` | **0** | **DARK → RETIRED candidate** | 0 refs anywhere; L0 serving uses `bg_*` equivalents instead — these 5 are legacy/superseded |
| `bg_dignity_reference` | live | **SERVED** | `register_p1_reference.ts:290 FROM bg_dignity_reference` → `ref_dignity_reference_get` (registerP1ReferenceTools LIVE) |
| `bg_sign_medical` | live | **SERVED** | `L0_brahmagyan/query_sign_medical.ts` + alias `ref_sign_medical_get` (register_p1_aliases.ts:616) |
| `bg_nakshatra`, `bg_dasha_systems`, `bg_yoga_catalog`, `bg_dosha_catalog`, `bg_transit_rules`, `bg_classical_texts` | live | **SERVED** | queried in register_p1_reference.ts (FROM/ref_* tools) |
| `bg_prashna_rules`, `bg_vastu_directions`, `bg_medical_mappings`, `bg_nakshatra_medical`, `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_shashtiamsha_deities` | **0** | **DARK** | 0 serving refs — genuine dark data |

Verdict: the sweeping "entire stratum dark" is **WRONG**; the true dark L0 set is narrower
(the 6–7 `bg_*` above + the 5 legacy `reference_*` that are retirement candidates, not
wire-up candidates). The dignity/aspect *definitions* the strategy worried the LLM "cannot
cite" — dignity IS citable (`bg_dignity_reference` served); aspect-catalog is not.

### (b) L5 `mimamsa_*` substantive read candidates — **CONFIRMED dark** (with one correction)
| Table | serving refs | Disposition | Evidence |
|---|---|---|---|
| `mimamsa_signal_adjustment` (~66.8k rows/chart) | assetClearSpec only | **DARK** | only ref = `cockpit/assetClearSpec.ts:157` DELETE (teardown, not serving) |
| `mimamsa_manifestation_sets` | assetClearSpec only | **DARK** | assetClearSpec.ts:120 DELETE only |
| `mimamsa_discoveries` | assetClearSpec only | **DARK** | assetClearSpec.ts:141 DELETE only |
| `mimamsa_insight_embeddings` | assetClearSpec only | **DARK** | assetClearSpec.ts:145 DELETE only |
| `mimamsa_insight_units` | **live** | **SERVED** (correction) | `register_p1_synthesis.ts:649 FROM mimamsa_insight_units` + `L5_mimamsa/query_insights.ts` — strategy did not list it as dark; confirmed served |

Verdict on (b): **CONFIRMED** — the four named substantive tables are dark (their only code
reference is the cockpit clear-spec, which is NOT a retrieval path).

### (c) L2 rollup tiers — **CONFIRMED dark**
| Table | serving refs | Disposition | Evidence |
|---|---|---|---|
| `bodha_rm_dasha_windowed_prescriptions` (time-targeted remedy) | assetClearSpec only | **DARK** | assetClearSpec.ts:98 DELETE only |
| `bodha_cdlm_domain_rollups` | **0** | **DARK** | 0 refs |
| `bodha_cdlm_evolution_gradients` | **0** | **DARK** | 0 refs |
| `bodha_cdlm_pattern_clusters` | **0** | **DARK** | 0 refs |
| `bodha_triangulation` | assetClearSpec only | **DARK** | assetClearSpec.ts:93 DELETE only |
| `bodha_cgm_sub_graphs` | **0** | **DARK** | 0 refs |

Verdict: **CONFIRMED**. All six are dark. (Served L2 CDLM/CGM/RM surfaces use `bodha_cdlm_cells`,
`bodha_cgm_edges/nodes`, `bodha_rm_resonances/remedy_prescriptions` — the rollup/gradient/cluster
*tiers* above them are not read.)

### (d) `kala_timeline` / `chart_panchanga` / `chart_ayanamsha_reports` — **MIXED (2 of 3 STALE)**
| Table | Disposition | Evidence |
|---|---|---|
| `chart_panchanga` | **SERVED** (STALE claim) | `tool_name_bridge.ts` maps `query_panchanga → marsys://tool/L1/get_panchanga`; handler `get_panchanga.ts` (L1 registry) + `brahma/l1/query_panchanga.ts FROM chart_panchanga`. **Not dark.** |
| `kala_timeline` | **DARK (orphaned handler)** — see New Finding #1 | A complete MCP handler exists (`platform-mcp/src/tools/kala_timeline.ts`, `registerKalaTimeline`, `server.registerTool`) but `registerKalaTimeline` is **never imported in server.ts** — exported-but-unwired. Functionally dark; 0 registry refs. |
| `chart_ayanamsha_reports` | **DARK** | 0 serving refs anywhere |

Verdict: `chart_panchanga` claim is **STALE** (served via get_panchanga). `kala_timeline` is
dark but for a different reason than "never built" — it is **built-but-unwired**.
`chart_ayanamsha_reports` **CONFIRMED dark**.

### (e) Open register rows S-3 / SC-2 / SC-3..5 / G-1 — **CONFIRMED all OPEN**
Cross-referenced `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (not duplicated):
- **S-3** bhava_arudha computed-unserved — OPEN (register:82). Nuance in-register: `address_resolver.ts:417`
  consumes it *internally* for arudha re-basing → "zero serving, not zero refs."
- **SC-2** graha speed/retro/combustion states unserved — OPEN (register:406).
- **SC-3** D1 parivartana_pairs category-split orphan — OPEN (register:407).
- **SC-4** ashtakavarga refinement set (shodhana/kakshya/per-varga bindu) unserved — OPEN (register:408).
- **SC-5** karaka_per_varga + nakshatra_cross_ayanamsha unserved; coverage-matrix stuck 158 vs 187 — OPEN (register:409).
- **G-1** CGM has no graha→bhava lordship/occupancy edges (every house chain fails) — OPEN, CRITICAL (register:194).
Verdict: **CONFIRMED** — every cited row is live-OPEN.

---

## 3. Recently-remediated set (LCA-19 / LCA-4) — **CONFIRMED serving works**

Claim: "18 of 23 computed-but-unserved assets now served (2026-07-13); `register_p1_ganita.ts`
closed most of the old NOT-REACHABLE L1 list." Traced to live registry, not just wiring:
- L1_ganita registry carries **31 live handler files** (`platform/src/lib/retrieval/registry/layers/L1_ganita/*.ts`),
  including the previously-dark set: `get_vastu_directions.ts`, `get_medical_indications.ts`,
  `get_sade_sati.ts`, `get_ayurdaya.ts`, `get_tajik.ts` (tajaka), `get_panchanga.ts`,
  `get_sensitive_degrees.ts`, `get_transit_anchors.ts`, `get_eclipse_flags.ts`, `get_graha_yuddha.ts`.
- `registerP1GanitaTools` is imported & invoked at `server.ts:353` → these are on the LIVE surface.
Verdict: **CONFIRMED** — remediated assets are wired to the live registry (not orphaned).
This is the same wiring that makes `chart_panchanga` served, refuting §5.2(d).

---

## 4. Single cross-layer join claim — **CONFIRMED (one relationship, ~4 sites)**

Claim (strategy §5, §5.1): "today only ONE real cross-layer join exists
(`bodha_msr_signals ↔ kala_activation`)." Grepped all `JOIN <layer-prefix>` in serving SQL:

| Site | Join | Layers |
|---|---|---|
| `register_d8_assess_domain.ts:1120` | `JOIN kala_activation ka ON ka.signal_id = m.signal_id` | L2↔L3 |
| `L3_kala/call_service_wrappers.ts:509` | `JOIN kala_activation a ON m.signal_id = a.signal_id` | L2↔L3 |
| `L3_kala/query_temporal_activation.ts:158,183` | correlated `bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id` | L2↔L3 |
| `L2_bodha/query_remedies.ts:226` | `bodha_rm_resonances JOIN bodha_cdlm_cells` | L2↔L2 (within-layer) |
| `L2_bodha/traverse_chart_graph.ts:529,696` | `JOIN bodha_cgm_edges` | L2↔L2 (within-layer) |

Verdict: **CONFIRMED.** Exactly **one cross-*layer* join relationship** exists —
`bodha_msr_signals.signal_id ↔ kala_activation.signal_id` (L2↔L3) — instantiated at ~4 query
sites. **No** phala↔anything, mimamsa↔bodha, or bodha↔phala joins exist. Everything else is
within-layer or to `chart_*` (L1). The strategy's horizontal-disconnection diagnosis holds.

---

## 5. Service-asset inventory (the census's blind spot) — strategy §5.3

Real-time compute surfaces and their retrieval reachability + provenance markers.
`computed_at` appears **39×** across serving source → computed responses do carry provenance
(the §5.3 `computed_at`/engine-version discipline is partially present, not absent).

| Service asset | Compute surface | Reachable? | Provenance | Evidence |
|---|---|---|---|---|
| natal positions | `ga_chart_service` / `/ephemeris` router | **SERVED** | birth-param derived | `registerComputeNatalPositionsTool` (server.ts:317) |
| L0 ephemeris (positions 1900–2150) | Python sidecar `brahmagyan/ephemeris_routes.py` via `PYTHON_SIDECAR_URL`/`PLATFORM_URL`; pyswisseph DE441; table `ephemeris_daily` | **SERVED** | engine=pyswisseph DE441 | `l0_ephemeris.ts` — 6 capabilities |
| panchanga | stored `chart_panchanga` (written by `panchanga_writer.py`) | **SERVED** | build_id (stored) | `get_panchanga.ts` / `brama/l1/query_panchanga.ts` |
| graha yuddha (winner) | compute-at-serve from ephemeris + birth date | **SERVED** | computed-at-serve, cited JL-027 | `registry_bridge.ts` get_graha_yuddha overlay |
| transit event search | `ka_gochara` service | **SERVED (wired)** | sidecar | `call_service_wrappers.ts:133 fetch(${sidecarUrl}/api/compute/transit_search)` |
| **arbitrary-datetime ephemeris** | `ka_graha_sancara` service | **DARK — NOT WIRED** | n/a | `call_service_wrappers.ts:200-208`: "not yet wired to a compute sidecar endpoint … needs_decision: wire `/api/compute/ephemeris_at_t`". See New Finding #2 |
| dasha eligibility windows | `ka_dasha_kala` service | wrapper present; endpoint wiring UNVERIFIED | sidecar | `call_service_wrappers.ts` (call_dasha_eligibility) |
| muhurta scoring | `ka_muhurta_seva` service | wrapper present; endpoint wiring UNVERIFIED | sidecar | `call_service_wrappers.ts` (call_muhurta_score) |
| priority ranking | `ka_tulana` service | wrapper present; endpoint wiring UNVERIFIED | sidecar | `call_service_wrappers.ts` (call_priority_ranking) |
| mimamsa calibration / outcome | Python sidecar `/api/mimamsa/query_calibration`, `/api/mimamsa/record_outcome` | **SERVED** (confirmed live 2026-07-16, chart 482012f1) | source_citation, ISO datetime | `mimamsa_outcome.ts` (callSidecar) |

`ka_graha_sancara`/`ka_dasha_kala`/`ka_muhurta_seva`/`ka_tulana`: `asset_registry.target_table = null`
(compute services). Their wrappers exist as registry descriptors, but only `transit_search` has a
confirmed `fetch()` to a live `/api/compute/*` endpoint; `ephemeris_at_t` is explicitly unwired;
the other three's sidecar endpoints are **UNVERIFIABLE-NO-DSN** (cannot exercise without a running sidecar).

---

## 6. SERVED / INTERNAL-BY-DESIGN / RETIRED disposition draft

Legend: **[declared]** = disposition already stated in code/register; **[proposed]** = Lane E judgment.
This is the R-1.5 input register. Every "proposed" row is a proposal for native/R-1.5 ratification,
not a settled disposition.

### Tables — SERVED (verified live handler + registration)
- L1: `chart_facts`, `chart_dashas`, `chart_divisionals`, `chart_panchanga` **[proposed→confirm]**, all `ga_*`-fed get_* handlers (positions, strength, dignity, dashas, sade_sati, ayurdaya, tajik, vastu, medical, sensitive_degrees, transit_anchors, yoga_firings, ashtakavarga, etc.)
- L0: `bg_dignity_reference`, `bg_sign_medical`, `bg_nakshatra`, `bg_dasha_systems`, `bg_yoga_catalog`, `bg_dosha_catalog`, `bg_transit_rules`, `bg_classical_texts`, `ephemeris_daily`
- L2: `bodha_msr_signals`, `bodha_cgm_edges`, `bodha_cgm_nodes`, `bodha_cdlm_cells`, `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`, `bodha_chart_gestalt`, `bodha_contradictions`, `bodha_convergence`
- L3: `kala_activation`, `kala_windows`/projections (via registry L3 handlers)
- L5: `mimamsa_insight_units`, `mimamsa_calibration` (sidecar), `mimamsa_reliability`

### Services — SERVED
- `ga_chart_service`/natal compute, L0 ephemeris sidecar (6 caps), panchanga, graha-yuddha compute-at-serve, `ka_gochara` transit_search, mimamsa calibration/outcome sidecar.

### Tables — DARK today (defect class; disposition proposed)
- **Wire-up candidates (substantive, should be SERVED)** **[proposed]**: `bodha_rm_dasha_windowed_prescriptions`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_evolution_gradients`, `bodha_cdlm_pattern_clusters`, `bodha_triangulation`, `bodha_cgm_sub_graphs`, `mimamsa_signal_adjustment`, `mimamsa_manifestation_sets`, `mimamsa_discoveries`, `mimamsa_insight_embeddings`, `chart_ayanamsha_reports`, `bg_prashna_rules`, `bg_vastu_directions`. Plus register-tracked: S-3 `bhava_arudha`, SC-2 graha-states, SC-3/4/5, G-1 CGM edges.
- **Built-but-unwired (wiring fix, not build)** **[proposed]**: `kala_timeline` (orphaned `registerKalaTimeline`).

### Tables — RETIRED / RETIRE candidate (dark AND superseded)
- **[proposed]** `reference_aspects`, `reference_signs`, `reference_planets`, `reference_nakshatras`, `reference_vargas` — 0 serving refs, superseded by `bg_*` equivalents. Recommend explicit RETIRED disposition (not wire-up).
- **[declared]** DROP-set legacy L2: `bodha_graph`, `bodha_graph_edges`, `bodha_graph_staging`, `bodha_signals`, `bodha_signal_embeddings`, `bodha_remediation`, `bodha_remediation_staging`, `bodha_resonance`, `bodha_domain_links` (pre-rebuild, in DROP TABLE migrations).

### Tables — INTERNAL-BY-DESIGN (proposed)
- **[proposed]** Most `mimamsa_*` ledgers (adjudication_log, event_provenance, negative_controls, snapshot_cosign, journal, preferences, export_log, multipliers, load_bearing, attribution, reliability internals) — L5 calibration substrate, legitimately internal per the strategy's own "most legitimately internal" note. `mimamsa_signal_adjustment` etc. flagged as read-candidates are the exceptions.
- **[proposed]** `bg_*` low-level threshold/orb tables (`bg_combustion_orbs`, `bg_motion_state_thresholds`, `bg_avastha_schemes`) — internal to L1 compute, not caller-facing.

### Services — DARK / not wired
- **[declared, in code]** `ka_graha_sancara` (arbitrary-datetime ephemeris) — no sidecar endpoint.
- **[proposed/UNVERIFIABLE]** `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana` — wrappers exist, endpoint reachability UNVERIFIABLE-NO-DSN.

---

## 7. Gaps found (NEW — not in plan or strategy)

1. **`kala_timeline` is built-but-unwired, not unbuilt.** A complete MCP handler
   (`platform-mcp/src/tools/kala_timeline.ts`, `registerKalaTimeline`, uses `server.registerTool`
   + `callPlatformPrimitive('kala_timeline')`) exists but `registerKalaTimeline` is **never imported
   into `server.ts`**. The strategy lists `kala_timeline` as generic "dark"; it is actually a
   one-line wiring fix (add the import + call), materially cheaper than the CDLM/mimamsa build items
   it's grouped with. R-1.5 should split "dark-unbuilt" from "dark-unwired."

2. **`ka_graha_sancara` (arbitrary-datetime ephemeris) is a live-in-code dark SERVICE.** This is the
   §5.3 "computable-but-unreachable service = dark data" case in the wild:
   `call_service_wrappers.ts:200-208` returns `error: 'call_ephemeris_at_t is not yet wired to a
   compute sidecar endpoint'` with a `needs_decision` to wire `/api/compute/ephemeris_at_t`. Neither
   plan nor strategy names it. It blocks all date-parameterized "positions at time T" retrieval —
   the exact futures-query the §5.3 service doctrine exists to enable.

3. **Census single-directory blind spot causes false-dark.** Grepping only
   `platform/src/lib/retrieval/` misses the `register_p1_*.ts` hand-tools and the `brahma/*` layer,
   which is why `bg_dignity_reference`, `bg_sign_medical`, and `chart_panchanga` were classed dark
   when they are served. The R-1.5 census harness must grep all three serving paths (registry +
   register_p1_* + brahma via tool_name_bridge) or it will keep mis-dispositioning L0/L1 tables.

4. **`reference_*` vs `bg_*` supersession is unrecognized.** The strategy treats the "L0 catalog
   stratum dark" as a wire-up gap. In fact 5 `reference_*` tables are dead-superseded by `bg_*`
   (served) equivalents — they are RETIRE candidates, not SERVE candidates. Conflating the two would
   have R-1.5 wire up dead tables.

5. **Physical inventory is unpinnable without DB reconciliation.** Two disjoint migration histories
   (platform/migrations #453 vs supabase/migrations #434) plus unresolved DROP-then-recreate noise
   mean the exact "34/27" table counts cannot be settled from DDL alone. The census should state its
   counts as "physical DDL union, net of live-DB retirement (pending)" and pin them against
   `SELECT count(*) FROM information_schema.tables` once a DSN exists.

---

## 8. Model / effort ledger

- **Model:** opus (opus-4-8[1m]); **effort:** high (judgment lane — disposition calls).
- **DSN availability:** NONE. No `DATABASE_URL`/`POSTGRES*`/`PG*` in env; only `.env.example` /
  `.env.rag.example` / `platform/.env*.example` carry placeholder DSNs. All row-count and
  live-endpoint-reachability items → **UNVERIFIABLE-NO-DSN**. No connection attempted (per brief:
  connect only if trivially available; it was not).
- **Source touched (read-only greps/reads):** `platform/migrations/*.sql`,
  `platform/supabase/migrations/*.sql`, `platform/src/lib/retrieval/registry/**`,
  `platform/src/lib/retrieval/registry/layers/{L0_brahmagyan,L1_ganita,L3_kala,L2_bodha}/**`,
  `platform/src/lib/retrieval/registry/{catalog.ts,tool_name_bridge.ts}`,
  `platform-mcp/src/server.ts`, `platform-mcp/src/tools/{register_p1_reference,register_p1_synthesis,register_p1_aliases,register_p1_ganita,kala_timeline,l0_ephemeris,mimamsa_outcome,registry_bridge}.ts`,
  `platform/src/lib/retrieval/registry/layers/L3_kala/{call_service_wrappers,query_temporal_activation}.ts`,
  `platform/src/lib/cockpit/assetClearSpec.ts`, `platform/src/lib/tools/brahma/l1/query_panchanga.ts`,
  `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (S/SC/G rows).
- **No production source modified.** One new file written: this report.
- **Display caveat:** the claude-mem observation hook substituted some tokens in grep *output*
  (e.g. `panchanga`→`n`, `sidecar`/`PLATFORM_URL`→`ln`); verified against clean `Read` of source
  where load-bearing (tool_name_bridge, call_service_wrappers). Underlying source is intact.

*End Lane E report.*
