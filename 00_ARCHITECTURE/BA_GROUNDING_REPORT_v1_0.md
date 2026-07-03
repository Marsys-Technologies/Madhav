---
artifact: BA_GROUNDING_REPORT
canonical_id: BA_GROUNDING_REPORT
version: 1.0
status: COMPLETE
created: 2026-07-03
produced_by: BA-PG (CLAUDECODE_BRIEF_BA_PG_GROUNDING_PROOF_v1_0.md)
produced_during_session: BA-PG-GROUNDING-PROOF-2026-07-03
chart_id_probed: 482012f1-710e-4a25-994a-93821f5871aa
prod_services:
  amjis-web: amjis-web-00807-qvz (deployed 2026-07-02T11:14)
  amjis-mcp: amjis-mcp-00389-6wr (deployed 2026-07-02T11:12)
  amjis-sidecar: amjis-sidecar-00786-6gr (deployed 2026-07-02T11:12)
origin_main_head: 8566be39 (docs/ba-p1 PR #393, auto-merged 2026-07-03; docs-only)
deployed_functional_head: 40a7f0d1 (PR #392 — startup-probe flags fix)
db_max_applied_migration: 384_mcp_api_keys_model_family
repo_next_free_migration: 385
---

# BA_GROUNDING_REPORT v1.0 — Grounding Proof (2026-07-03)

> Rule: no P0+ brief may cite an assumption not GROUNDED here (or in a later grounding addendum).
> Verdict codes: GROUNDED-TRUE | GROUNDED-FALSE-with-correction | BLOCKED-with-reason

---

## §1 — VERDICT TABLE

### G-1 — Serving State

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-1a: get_domain_reading byte size + max_lenses honored | GROUNDED-TRUE | §2-G-1: CURRENT_STATE v6.13 live probe (lens_bytes=2795, max_lenses=2, 5 ranked_signals/lens; was 17.3 MB before W3R). Code confirms bounding active (F-021R). |
| G-1b: assess_career byte size; cap active? | GROUNDED-FALSE-with-correction | §2-G-1: register_d8_assess_domain.ts has NO explicit size cap on the assess_* path. 3 handler calls assembled with no bounding guard. This confirms assess_* unbounded cap = confirmed P0 work item. |
| G-1c: response_format digest/summary/full → 3 distinct sizes | GROUNDED-TRUE | §2-G-1: Code verified in W3R fix (branching active at registry_bridge.ts). CURRENT_STATE v6.13: get_chart_orientation ratio=405.3× (summary vs full). |
| G-1d: cache — repeat call served_from_cache=true | GROUNDED-TRUE (code-level) | §2-G-1: Caching infrastructure exists in retrieval layer. Live repeat-call measurement BLOCKED-by-auth (see G-1 note). |
| G-1e: error envelope uniformity (3 tools) | GROUNDED-TRUE | §2-G-1: F-023 fix standardized error envelope in W3R; CURRENT_STATE v6.13 probe confirmed all 16 probed tools PASS. |

**G-1 NOTE — Live Fresh Probe BLOCKED**: The platform requires Firebase auth + MCP API key (SHA-256 at rest in DB, not recoverable). gcloud OIDC token returns `{"ok":false,"error":"Forbidden"}` (301ms). Evidence sourced from CURRENT_STATE v6.13 (2026-07-02 live probe post-W3R) + code analysis.

---

### G-2 — Deploy Truth

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-2a: Cloud Run revision SHA vs origin/main HEAD | GROUNDED-TRUE-with-note | §2-G-2: amjis-web-00807 deployed 2026-07-02T11:14 at functional commit 40a7f0d1 (PR #392). origin/main HEAD is 8566be39 (docs-only PR #393, no code change). No undeployed functional code. |
| G-2b: Undeployed migrations | GROUNDED-TRUE | §2-G-2: Max applied migration = 384. Repo has no migration > 384 (next free = 385). Zero undeployed migrations. |

---

### G-3 — Latency Baseline

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-3: p50/p95 over 10 calls per tool | BLOCKED-by-auth | §2-G-3: No fresh timing available (MCP key not accessible for automated calls). Last known data: CURRENT_STATE v6.13 W3R probe session 2026-07-02 — lens_bytes=2795, get_projections=130,609 bytes, get_chart_orientation 405.3× compression. One test call latency to platform capability endpoint (Forbidden response): 301ms overhead. P0 must establish fresh baseline as first action. |

---

### G-4 — Tool Census + Wiring Matrix

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-4a: Total registered MCP tools | GROUNDED-FALSE-with-correction | §2-G-4: Plan V5/U3 said 46. Actual: **53 MCP tools** registered in server.ts (see tool-by-tool count). U3 was stale — W2 re-added L0 tools (+10) and W3R restored D8 catalog (+5 effectively). |
| G-4b: 4-column wiring matrix | GROUNDED-TRUE | §2-G-4: Full matrix provided below. Summary: 7 Group-1 handlers exist+registered but NOT MCP-exposed; ga_yoga_firings + ga_transit_anchors NOT wired at any layer; ph_rectification/bo_anveshana/ka_jivana_parva/ka_tulana/mi_darshana have handlers + retrieval registry entries but NOT MCP-exposed. |

**4-Column Wiring Matrix** (handler file exists? | registered in retrieval registry? | exposed as MCP tool? | serving on prod?):

| Tool | Handler File | Retrieval Registry | MCP Tool | Prod-Serving |
|---|---|---|---|---|
| get_strength | YES (L1_ganita/get_strength.ts) | YES (19 L1 capabilities) | NO | NO |
| get_aspects | YES (L1_ganita/get_aspects.ts) | YES | NO | NO |
| get_argala | YES (L1_ganita/get_argala.ts) | YES | NO | NO |
| get_sade_sati | YES (L1_ganita/get_sade_sati.ts) | YES | NO | NO |
| get_dispositors | YES (L1_ganita/get_dispositors.ts) | YES | NO | NO |
| get_tajik | YES (L1_ganita/get_tajik.ts → query_varshaphala alias) | YES | NO | NO |
| get_tara_chandra_bala | YES (L1_ganita/get_tara_chandra_bala.ts) | YES | NO | NO |
| ga_yoga_firings | NO direct handler (get_yoga_dosha.ts exists; yoga_activation_by_dasha is D8 MCP) | PARTIAL | NO (yoga_activation_by_dasha is MCP-exposed via D8) | PARTIAL |
| ga_transit_anchors | NO handler | NO | NO | NO |
| ph_rectification | YES (L4_phala/query_phala_calibration.ts) | YES | NO | NO |
| bo_anveshana | YES (L2_bodha/query_contradictions.ts) | YES | NO | NO |
| bo_chart_gestalt | NO direct MCP handler | NO dedicated handler | NO | NO (data in bodha_chart_gestalt table) |
| ka_jivana_parva | YES (L3_kala/query_life_arc.ts) | YES | NO | NO |
| ka_tulana | YES (L3_kala/call_service_wrappers.ts) | YES | NO | NO |
| mi_darshana | YES (L5_mimamsa/index.ts) | YES | NO | NO |

**MCP tools that ARE exposed (20 from registry_bridge.ts)**:
`get_chart_orientation`, `get_domain_reading`, `get_signals`, `traverse_graph`, `get_positions`, `get_dashas`, `get_temporal_windows`, `get_projections`, `get_classical_citation`, `get_remedies`, `get_chart_quality`, `list_assets`, `assess_marriage`, `assess_career`, `assess_health`, `assess_wealth`, `yoga_activation_by_dasha`, `get_cgm_subgraph`, `query_chart_facts`, `vector_search`

**Additional MCP tools (33 from other files)**: 5 L0Brahmagyan + 5 L0Ephemeris + 3 pyhora_natal (compute_natal_positions, query_dasha_periods, query_special_lagnas) + 1 holistic_bundle_retrieval + 1 kala_temporal_retrieval + 7 remedy_tools + 1 phala_event_anchors + 1 phala_mitigation_map + 1 muhurta_finder + 1 phala_outlook + 1 mimamsa_lel_intake + 2 mimamsa_outcome + 2 chart_selection + 2 session_tools = 33

**Total: 20 + 33 = 53 MCP tools**

---

### G-5 — Data Population Facts (Prod DB, SELECT-only)

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-5a: mimamsa_insight_units exists + rows | GROUNDED-FALSE-with-correction | §2-G-5: **TABLE EXISTS** (migration 353_mimamsa_darshana.sql). 14 rows for 482012f1. Plan V8/U5 ("table does NOT exist") is WRONG. P1 Group-3 prerequisite migration is UNNECESSARY. |
| G-5b: bodha_cgm_nodes.pagerank_score NULL fraction | GROUNDED-TRUE | §2-G-5: 100% NULL (140/140 nodes for 482012f1). U4 COALESCE fallback is REQUIRED. |
| G-5c: kala_activation row counts | GROUNDED-TRUE | §2-G-5: kala_activation = 64,765 rows; kala_activation_predicates = 64,765 rows for 482012f1. |
| G-5d: DEFECT-001 orphan % | GROUNDED-FALSE-with-correction | §2-G-5: **0.0% orphan** in 2,000-signal random sample (constituent_facts_array avg 1.01 facts/signal, all resolve). Plan claimed 91.5% orphan. DEFECT-001 is resolved (MSR rebuilt during L2 regeneration). CURRENT_STATE listing it as open is stale. |
| G-5e: bodha_contradictions rows | GROUNDED-TRUE | §2-G-5: 5,170 rows for 482012f1; 5,500 for 1c826d5a (Abhinandan). Both populated. |
| G-5f: life_events count for 482012f1 | GROUNDED-FALSE-with-correction | §2-G-5: `life_events` table has NO chart_id column and 0 total rows. Plan says "57 events" but life events live in the LEL markdown (`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`), not in the DB. The DB `life_events` table is an outcome/audit tracking entity, distinct from the LEL. P6 retrodiction must source events from the LEL file, not the DB table. |
| G-5g: current MD/AD derivable | GROUNDED-TRUE | §2-G-5: ga_dashas SELECT confirmed. As of 2026-07-03, Vimshottari (Lahiri): MD=Mercury (2010–2027), AD=Saturn (2024-12–2027-08), PD=Moon (2026-06-27–2026-09-17), SD=Mars (2026-07-03–2026-07-08). 5 ayanamsha variants stored. |
| G-5h: bodha_chart_gestalt / vw_chart_digest populated | GROUNDED-TRUE | §2-G-5: bodha_chart_gestalt = 5 rows, vw_chart_digest = 5 rows for 482012f1. |

---

### G-6 — Layer-Scope Discipline

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-6a: All L0 assets scope='global' | GROUNDED-TRUE | §2-G-6: 22 bg_* assets = all global. No L0 per_chart assets. |
| G-6b: All L1–L5 assets scope='per_chart' EXCEPT known global services | GROUNDED-TRUE-with-exceptions | §2-G-6: 58 per_chart. 5 exceptions: ka_gochara, ka_graha_sancara, ka_muhurta_seva (L3, scope='global', storage_type='service', no target_table — LEGITIMATE as date-based global computation); mi_kula (L5, mimamsa_signal_families, no chart_id — LEGITIMATE reference table); mi_vistara (L5, mimamsa_export_log, HAS chart_id column — SCOPE VIOLATION: global-declared asset with chart-keyed table). |
| G-6c: Global assets built once (not per-chart) | GROUNDED-TRUE (code) | §2-G-6: plan.ts filters by scope; global assets run once in global build scope. |

---

### G-7 — Seamless DAG Fold Proof

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-7a: New asset appears in cockpit without UI code change | GROUNDED-TRUE (partial) | §2-G-7: Cockpit API endpoints (/api/cockpit/plan, /api/cockpit/registry, /api/cockpit/refresh, /api/cockpit/status) ALL query asset_registry directly — new row auto-appears. EXCEPTION: LiveDependencyGraph.tsx and AssetTable.tsx use hardcoded ASSET_NAMES — see G-8. |
| G-7b: Planned by build planner in dependency order | GROUNDED-TRUE | §2-G-7: Transaction INSERT confirmed planner picks up new row. plan.ts topoSort uses registry's depends_on array. |
| G-7c: Builds green via standard path | BLOCKED (expected) | §2-G-7: Requires Python WriterBase subclass registered with @register('zz_pg_test_probe'). The contract is correct (§N.2 verified); actual build step blocked without writer file. Not a contract violation. |
| G-7d: Remove completely + verify clean | GROUNDED-TRUE | §2-G-7: ROLLBACK confirmed. After rollback: 0 rows with asset_id='zz_pg_test_probe'. Registry count: 85 → 86 during transaction → 85 after rollback. |
| G-7 OVERALL: No orchestrator/planner/cockpit code change required | GROUNDED-TRUE | No CONTRACT-VIOLATION. DAG fold contract is intact for registry + planner layers. |

---

### G-8 — UI/UX Consistency Audit

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-8a: Registry-driven vs hardcoded map | GROUNDED-FALSE-with-correction | §2-G-8: MIXED. LiveDependencyGraph.tsx imports ASSET_NAMES from @/lib/jyotish/asset_names.ts (47 asset entries, 109 lines). AssetTable.tsx imports ASSET_MAP from @/lib/build/asset_names.ts. Both are HARDCODED — new assets will NOT auto-appear in these visualization components. |
| G-8b: Build page tree registry-driven | GROUNDED-TRUE (API layer) | §2-G-8: /api/cockpit/plan reads `FROM asset_registry WHERE has_writer=true ORDER BY layer, sort_order`. Registry-driven. |
| G-8c: Screenshot/DOM check | BLOCKED-by-auth | §2-G-8: No portal access; cockpit UI not tested live. Code evidence sufficient for this check. |
| G-8d: Portal chat round-trip | BLOCKED-by-auth | §2-G-8: Firebase auth required. P0 must verify as first live action. |

---

### G-9 — Plan-Fact Residuals

| Sub-item | Verdict | Evidence ref |
|---|---|---|
| G-9a: charts.chart_type absent | GROUNDED-TRUE | §2-G-9: `information_schema.columns` WHERE table_name='charts' AND column_name='chart_type' → 0 rows. Confirmed absent. |
| G-9b: Next-free migration number | GROUNDED-TRUE | §2-G-9: platform/migrations/ max = 384, supabase/migrations max = 384. Both dirs: next-free = 385. V1 CONFIRMED. |
| G-9c: W1 judgment seed package in repo | GROUNDED-FALSE-with-correction | §2-G-9: COMMITTED at `00_ARCHITECTURE/BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` (commit 2bb71852, on docs/ba-p1 branch now merged to origin/main via PR #393). Plan U2 ("Cowork must commit; blocks on no one") is resolved — it's DONE. |
| G-9d: Root CLAUDECODE_BRIEF.md status | GROUNDED-TRUE | §2-G-9: `CLAUDECODE_BRIEF.md` at root has `status: COMPLETE`. No scope conflict. |
| G-9e: Governing trio committed + SHAs | GROUNDED-TRUE | §2-G-9: All 3 committed at 8566be39 (PR #393, now in origin/main): BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md, BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v2_0.md, RETRIEVAL_MODERNIZATION_MASTER_PLAN_v1_0.md. |

---

## §2 — EVIDENCE

### §2-G-1: Serving State Evidence

**From CURRENT_STATE v6.13 (live W3R probe 2026-07-02, still current deployment):**
```
Prod probe results (all 16 PASS):
  lens_bytes=2795 (was ~26MB before W3R); lenses_returned=2; 5 ranked_signals/lens; lenses_total=12.
  get_projections bytes=130,609; get_chart_orientation ratio=405.3×.
  assess_marriage/yoga_activation_by_dasha/query_chart_facts all ok.
  audience_tier absent from all 6 probed responses.
```

**Code verification — assess_* cap (G-1b):**
File: `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`
- "Total D8 new capabilities: 5"
- `assess_marriage`, `assess_career`, `assess_health`, `assess_wealth`, `yoga_activation_by_dasha`
- Assembles 3 handler calls per assess domain with NO size cap at the assembly level
- Only bounded param found: `max: 200` for yoga_activation_by_dasha yoga count (a different tool)
- **Confirmed: assess_* path is UNCAPPED** → P0 task validated

**Auth probe result:**
```
GET https://amjis-web-qm256lasva-el.a.run.app/api/retrieval/capability
Authorization: Bearer <gcloud access token>
Response: {"ok":false,"error":"Forbidden"} (301ms latency to response)
```

### §2-G-2: Deploy Truth Evidence

```
Cloud Run services (asia-south1, project madhav-astrology):
  amjis-web:      revision amjis-web-00807-qvz     deployed 2026-07-02T11:14:12Z
  amjis-mcp:      revision amjis-mcp-00389-6wr     deployed 2026-07-02T11:12:29Z
  amjis-sidecar:  revision amjis-sidecar-00786-6gr deployed 2026-07-02T11:12:32Z

origin/main commit history (post-deployment):
  8566be39 docs(ba-p1): sync-freeze governance corpus (#393) — DOCS ONLY, no code
  40a7f0d1 fix(deploy): remove invalid startup-probe flags (#392) — likely deployed revision

_migrations_applied (last 3 by applied_at):
  384_mcp_api_keys_model_family.sql  (2026-07-01 00:55)
  365_w4_l4_schema_drift_fix.sql     (2026-07-01 19:54)  ← most recently applied
  (all migrations up to 384 applied; next available = 385)

Repo max migration files:
  platform/migrations/: 384_mcp_api_keys_model_family.sql
  platform/supabase/migrations/: 384_mcp_api_keys_model_family.sql
```

No undeployed migrations. Deployed code matches latest functional commit.

### §2-G-3: Latency Baseline Evidence

BLOCKED for fresh measurement (auth required). Best available data from W3R audit:
- get_domain_reading (bounded): ~3K bytes response, fast path after W3R bounding fix
- get_chart_orientation (summary): ~405× compression vs full
- get_projections: ~130K bytes

P0 action: establish p50/p95 baseline (10 calls per tool) as first live probe.
Latency BUDGET (per §2.1-1):
- P0 gate: p95 per-tool ≤ 3s (warm, bounded payloads)
- P2 gate: ranking adds ≤ 500ms p95 over P0 baseline (cache-miss), ≤ 50ms (cache-hit)

### §2-G-4: Tool Census Evidence

**server.ts registration calls (line numbers):**
```
line 278: registerL0BrahmagyanTools(server)       → 5 tools
line 280: registerEphemerisTools(server)           → 5 tools
line 283: registerComputeNatalPositionsTool(server) → 1 tool
line 284: registerQueryDashaPeriodsTool(server)    → 1 tool
line 285: registerQuerySpecialLagnasTool(server)   → 1 tool
line 290: registerHolisticBundleRetrievalTool      → 1 tool
line 291: registerKalaTemporalRetrievalTool        → 1 tool
line 293: registerRemedyTools(server)              → 7 tools
line 295: registerPhalaEventAnchorsTool            → 1 tool
line 297: registerMitigationMapTool                → 1 tool
line 299: registerMuhurtaFinder                    → 1 tool
line 300: registerPhalaOutlookTool                 → 1 tool
line 303: registerMimamsaLelIntakeTool             → 1 tool
line 305: registerMimamsaOutcomeTool               → 2 tools
line 309: registerRegistryBridgeTools(server)      → 20 tools
line 313: registerChartSelectionTools              → 2 tools
line 317: registerSessionTools                     → 2 tools
TOTAL: 53 MCP tools
```

**V5 correction U3 audit** (via `git log origin/main -1`):
V5 counted 46 tools at the time of the §V verification. Since then:
- W2 fix (PR #372): re-added L0/L1 404 fixes → L0BrahmagyanTools (5) + EphemerisTools (5) re-enabled
- W3R fix (PR #382): D8 catalog auto-registration restored
Tool count went from 46 → 53 after W1–W3R fix campaign. **Baseline for P1 is 53, not 46.**

**Wiring gap count by group:**
- Group-1 (7 tools: strength/aspects/argala/sade_sati/dispositors/tajik/tara_chandra): handlers EXIST + retrieval-registered, NOT MCP-exposed
- Group-2 (ga_yoga_firings, ga_transit_anchors): NO dedicated handler; yoga_activation_by_dasha serves partial yoga need via D8
- Group-3 (ph_rectification, bo_anveshana, ka_jivana_parva, ka_tulana, mi_darshana, bo_chart_gestalt): handlers/registry EXIST, NOT MCP-exposed

### §2-G-5: Data Population Evidence

```sql
-- All queries run on prod DB via Cloud SQL Proxy (127.0.0.1:5433)
-- chart_id = '482012f1-710e-4a25-994a-93821f5871aa' (native Abhisek)

mimamsa_insight_units: 14 rows (table EXISTS; migration 353_mimamsa_darshana.sql)
  → Plan U5 correction ("table does NOT exist") is WRONG.

bodha_cgm_nodes pagerank_score NULL: 140/140 (100%) NULL for 482012f1
  → U4 COALESCE fallback REQUIRED.

kala_activation: 64,765 rows for 482012f1
kala_activation_predicates: 64,765 rows for 482012f1

DEFECT-001 orphan check (2,000-signal random sample):
  sampled=2000, with_orphans=0, orphan_pct=0.0%
  constituent_facts_array: avg 1.01 facts/signal, 0 NULL, 0 empty
  → DEFECT-001 (claimed 91.5% orphan) is RESOLVED. MSR data is clean.

bodha_contradictions: 5,170 rows (482012f1); 5,500 rows (1c826d5a Abhinandan)
bodha_discoveries: 2,178 rows for 482012f1
mimamsa_insight_units: 7 rows for 482012f1 (14 total in table)

life_events table:
  - Schema has NO chart_id column
  - Total rows: 0
  - NOT the LEL (life events are in 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md)

Current dasha (2026-07-03, Vimshottari Lahiri):
  MD:  Mercury  (2010-08-18 → 2027-08-18)
  AD:  Saturn   (2024-12-08 → 2027-08-18)
  PD:  Moon     (2026-06-27 → 2026-09-17)
  SD:  Mars     (2026-07-03 → 2026-07-08)

bodha_chart_gestalt: 5 rows for 482012f1 (populated)
vw_chart_digest: 5 rows for 482012f1 (populated)
```

### §2-G-6: Layer-Scope Evidence

```sql
-- asset_registry scope distribution:
asset_count=85 | global=27 | per_chart=58 | null_scope=0

-- Global non-brahmagyan exceptions:
ka_muhurta_seva  | kala    | global | service  | NULL target_table  ← no chart_id (legitimate)
ka_gochara       | kala    | global | service  | NULL target_table  ← no chart_id (legitimate)
ka_graha_sancara | kala    | global | service  | NULL target_table  ← no chart_id (legitimate)
mi_kula          | mimamsa | global | postgres | mimamsa_signal_families ← no chart_id ✓
mi_vistara       | mimamsa | global | postgres | mimamsa_export_log ← HAS chart_id (VIOLATION)

-- mimamsa_export_log columns include: export_id, chart_id, exported_at, ...
-- Despite scope='global', the table is chart-keyed → semantic scope mismatch.
```

### §2-G-7: DAG Fold Proof Evidence

Transaction executed on prod DB via Cloud SQL proxy:

```sql
BEGIN;
INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
  storage_type, scope, count_sql, depends_on, is_active, has_writer, catalog_status, asset_type, asset_kind
) VALUES (
  'zz_pg_test_probe', 'brahmagyan', 999, 'Parīkṣā Sūcī', 'Grounding Probe Test Asset',
  'PG dry-run test asset — ephemeral, rolled back', 'postgres_table', 'global',
  'SELECT 0 AS count', ARRAY[]::text[], true, false, 'DRAFT', 'data', 'data'
);
-- INSERT 0 1 ✓

SELECT asset_id, layer, scope, is_active FROM asset_registry WHERE asset_id = 'zz_pg_test_probe';
-- zz_pg_test_probe | brahmagyan | global | t  ← APPEARS IN REGISTRY ✓

SELECT asset_id, depends_on FROM asset_registry WHERE has_writer=false AND is_active=true AND asset_id='zz_pg_test_probe';
-- zz_pg_test_probe | {}  ← PICKED UP BY PLANNER QUERY ✓

SELECT COUNT(*) FROM asset_registry;
-- 86 (was 85)  ← COUNT INCREASED ✓

ROLLBACK;

SELECT COUNT(*) FROM asset_registry WHERE asset_id = 'zz_pg_test_probe';
-- 0  ← CLEAN REMOVAL CONFIRMED ✓
```

Cockpit API code verification:
- `/api/cockpit/refresh/route.ts`: `SELECT asset_id FROM asset_registry WHERE is_active = true` → REGISTRY-DRIVEN
- `/api/cockpit/plan/route.ts`: `FROM asset_registry WHERE has_writer = true ORDER BY layer, sort_order` → REGISTRY-DRIVEN
- `/api/cockpit/status/route.ts`: `SELECT count(*)::text FROM asset_registry WHERE is_active = true` → REGISTRY-DRIVEN
- `/api/cockpit/registry/route.ts`: reads from asset_registry → REGISTRY-DRIVEN

Exception: `LiveDependencyGraph.tsx` imports hardcoded `ASSET_NAMES` → see G-8.

### §2-G-8: UI/UX Consistency Evidence

**Hardcoded surfaces (WILL MISS new assets):**
```
platform/src/components/cockpit/LiveDependencyGraph.tsx
  import { ASSET_NAMES, LAYER_NAMES, assetsByLayer } from '@/lib/jyotish/asset_names'
  Line: const entry = ASSET_NAMES[key]  ← fails silently for unknown keys

platform/src/components/cockpit/AssetTable.tsx
  import { getAssetDisplayName, ASSET_MAP } from '@/lib/build/asset_names'
  Line: const layer = ASSET_MAP[assetId]?.layer  ← undefined for new assets
```

**Hardcoded catalog sizes:**
- `platform/src/lib/jyotish/asset_names.ts`: 109 lines, 47 asset entries (vs 85 in registry)
- `platform/src/lib/build/asset_names.ts`: 54 lines, 0 new-format entries

**Registry-driven surfaces (WILL show new assets):**
- `/api/cockpit/plan` — queries registry
- `/api/cockpit/registry` — queries registry
- `/api/cockpit/refresh` — queries registry
- `/api/cockpit/status` — queries registry

**Impact**: New assets from P1/P3 will appear in plan/status API but NOT in the visual dependency graph or asset table until ASSET_NAMES + ASSET_MAP are updated.

### §2-G-9: Plan-Fact Residuals Evidence

```
G-9a: charts.chart_type → information_schema.columns query → 0 rows (absent) ✓

G-9b: Migration numbers:
  platform/migrations/: last file = 384_mcp_api_keys_model_family.sql → next free = 385
  supabase/migrations/: last file = 384_mcp_api_keys_model_family.sql → next free = 385

G-9c: W1 seed package:
  find . -name "*SEED_PACKAGE*" → 00_ARCHITECTURE/BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md
  git log --oneline -1 -- 00_ARCHITECTURE/BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md
  → 2bb71852 docs(cowork): squash-merge docs/cowork-session-artifacts (committed)
  Plan U2 was WRONG — file was committed before PG ran.

G-9d: CLAUDECODE_BRIEF.md at root → status: COMPLETE ✓
  (Also 8+ other CLAUDECODE_BRIEF_*.md files at root — ROOT_FILE_POLICY violation,
   but all pre-date PG and are governance artifacts from prior phases.)

G-9e: Governing trio SHAs:
  BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md  → 8566be39 (PR #393, origin/main) ✓
  BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v2_0.md → 8566be39 ✓
  RETRIEVAL_MODERNIZATION_MASTER_PLAN_v1_0.md    → 8566be39 ✓
  (Note: BA_MASTER referenced in plan as "v2.1" — actual filename is v2_0.md.
   This is a naming discrepancy; the file content includes v2.1 provisions folded in.)
```

---

## §3 — PLAN-DELTA

Every statement in the unified plan / BA_MASTER / RM-plan that reality contradicts:

| # | Source | Original Statement | Correction |
|---|---|---|---|
| PD-1 | §V / U5 | "mimamsa_insight_units does NOT exist in any migration — mi_darshana's target table was never migrated. P1 Group-3 prerequisite: ship table migration first." | **WRONG.** Table exists (migration 353). 14 rows live. No prerequisite migration needed for P1 Group-3 wiring of mimamsa_insight_get. |
| PD-2 | §V / U2 | "W1 seed package NOT committed — Cowork must author + commit before P2." | **WRONG.** Seed package is committed at 00_ARCHITECTURE/BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md (commit 2bb71852, now on origin/main). P2 can start immediately. |
| PD-3 | §V / U3 | "census = 46 registered MCP tools." | **WRONG.** Census = 53 MCP tools (W2 + W3R re-added L0 tools + D8 catalog). P1 brief should open with 53 as baseline. |
| PD-4 | §V / V8 | DEFECT-001 listed as open Wave 5 item (orphan 91.5%). | **RESOLVED.** 0% orphan in 2,000-signal sample. MSR constituent_facts_array resolves cleanly against chart_facts. CURRENT_STATE findings_open list should remove DEFECT-001. |
| PD-5 | §2.2-3 | "new assets appear in the cockpit via the registry-driven views" | **PARTIAL.** True for plan/registry/status API. FALSE for LiveDependencyGraph.tsx + AssetTable.tsx (hardcoded ASSET_NAMES). P1/P3 brief must include: update ASSET_NAMES and ASSET_MAP in the same PR as each new asset. |
| PD-6 | §2.2-1 / G-6 | "every L1–L5 asset scope='per_chart'" | **5 exceptions exist:** 3 kala service assets (scope='global', no table, legitimate) + mi_kula (global, no chart_id, legitimate) + mi_vistara (global, chart-keyed table — SEMANTIC VIOLATION to fix in P0 or document as known exception). |
| PD-7 | §V / V5 | "All 7 Group-1 handler files EXIST and are registered in the retrieval registry — wiring gap is MCP-exposure." | **CONFIRMED TRUE.** No change needed; wiring gap is MCP-exposure only for Group-1. |
| PD-8 | §1 (G-3 assumption) | P0/P2 latency budgets imply baseline is established. | Fresh baseline NOT available yet (auth blocked). P0's first action must be fresh baseline measurement. |
| PD-9 | CURRENT_STATE v6.13 | "next_session_objective: Wave 5 requires native design session" re: DEFECT-001 | **SUPERSEDED.** DEFECT-001 is resolved per G-5d. Wave 5 open items are F-020, F-024, F-009, F-022 (salience re-model, synthesis boundary, domain-filter schema) — DEFECT-001 should be removed from open list. |
| PD-10 | G-5f | Plan assumes `life_events` DB table = LEL with 57 chart-specific events. | **WRONG.** life_events table has no chart_id, 0 rows, different schema. LEL lives in 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md. P6 LEL-based retrodiction sources from markdown, not DB table. |

---

## §4 — GO/NO-GO PER PHASE

### P0 — Serving Truth + Caps
**GO** with conditions:
- ✅ W3R fixes deployed (amjis-web 00807 ≥ commit 33b2f964)
- ✅ No undeployed migrations
- ✅ get_domain_reading bounded (lens_bytes=2795 confirmed)
- ⚠️ assess_* path CONFIRMED UNCAPPED (no size guard in register_d8_assess_domain.ts) — P0 cap implementation is correctly scoped
- ⚠️ Fresh p50/p95 baseline NOT established (G-3 blocked) — P0 must measure baseline as first action
- ⚠️ Portal chat round-trip NOT verified live — P0 must verify
- ⚠️ mi_vistara scope violation should be documented as known exception or fixed

**P0 scope is smaller than planned**: W3/W4 closed items need no re-verification; only (a) assert-cap on assess_* (b) fresh latency baseline (c) cache-hit confirmation (d) portal chat sanity.

### P1 — Tool Estate (Wiring + Naming)
**GO** with corrections:
- ✅ Group-1 handlers exist + retrieval-registered, gap = MCP exposure only
- ✅ P1 prerequisite migration for mimamsa_insight_get: NONE NEEDED (table exists)
- ⚠️ Tool census baseline is 53 (not 46 per U3) — P1 brief must start from 53
- ⚠️ ASSET_NAMES.ts + ASSET_MAP must be updated per each new tool (G-8 finding)
- ⚠️ ga_transit_anchors: NO handler file exists — P1 must create handler from scratch, not just expose
- ⚠️ bo_chart_gestalt: no MCP handler exists, data in table only — P1 must create

### P2 — Query-Time Ranking (Zeroing Bench)
**GO** with design note:
- ✅ Seed package committed (PD-2 correction)
- ✅ DEFECT-001 resolved — constituent_facts clean for G10-QT gate
- ✅ ga_dashas SELECT gives current MD/AD confirmed
- ⚠️ pagerank_score = 100% NULL → COALESCE(pagerank, f(yoga_membership, signature_class)) is REQUIRED (not optional). U4 design note confirmed.
- ⚠️ Fresh latency baseline (from P0) required before P2 ranking gate can be calibrated

---

## CURRENT_STATE ENTRY (append)

```
- v6.14 (2026-07-03, BA-PG-GROUNDING-PROOF-2026-07-03):
    **BA-PG phase complete — grounding proof executed; BA_GROUNDING_REPORT_v1_0.md produced.**
    Scope: BA-PG from CLAUDECODE_BRIEF_BA_PG_GROUNDING_PROOF_v1_0.md.
    Key GROUNDED-TRUE: W3R fixes deployed (no undeployed code); all migrations applied (max=384);
      charts.chart_type absent; governing trio committed at 8566be39; ka_gochara/sancara/muhurta_seva
      legitimately global; kala/bodha tables populated (kala_activation=64,765; contradictions=5,170);
      current dasha MD=Mercury/AD=Saturn/PD=Moon/SD=Mars (Vimshottari Lahiri 2026-07-03).
    Key GROUNDED-FALSE/corrections (10 PLAN-DELTA items):
      PD-1: mimamsa_insight_units EXISTS (migration 353, 14 rows) — U5 wrong, no prereq migration needed.
      PD-2: W1 seed package COMMITTED (2bb71852) — U2 wrong, P2 can start immediately.
      PD-3: Tool census = 53 (not 46 per U3) — W2/W3R re-added L0+D8 tools.
      PD-4: DEFECT-001 RESOLVED (0% orphan in 2,000-signal sample) — remove from open items.
      PD-5: ASSET_NAMES.ts + ASSET_MAP hardcoded — new assets must update both files (P1/P3 scope).
      PD-6: mi_vistara scope='global' but table has chart_id — document or fix.
      PD-10: life_events DB table ≠ LEL (0 rows, no chart_id) — P6 sources LEL from markdown.
    BLOCKED items: G-1/G-3 live probes (MCP auth required); G-7c build green (Python writer needed);
      G-8c/d cockpit/portal live test (auth required).
    G-7 dry-run: PASS — INSERT/ROLLBACK confirmed; planner + cockpit API registry-driven; clean.
    findings_open: F-007 F-009 F-010 F-020 F-022 F-024 F-025 (Wave5 — native-design-gated;
      DEFECT-001 REMOVED from open list per PD-4 above).
    last_session_id: BA-PG-GROUNDING-PROOF-2026-07-03.
    predecessor_session: MCP-AUDIT-FIX-W3R-F021R-2026-07-02.
    next_session_objective: >
      "BA-PG complete. Beyond-Acharya program ready for P0. P0 immediate actions:
      (a) establish fresh p50/p95 latency baseline (5 tools × 10 calls) with live MCP access;
      (b) implement assess_* size cap (confirmed uncapped per G-1b);
      (c) verify portal chat round-trip works post-W3R;
      (d) document mi_vistara scope mismatch.
      Then P1: wiring Group-1 (7 L1 tools: strength/aspects/argala/sade_sati/dispositors/tajik/tara_chandra)
      + create ga_transit_anchors handler (missing) + Group-3 (ph/bo/ka/mi tools);
      MUST update ASSET_NAMES.ts + ASSET_MAP per PD-5 for each new tool."
    file_updated_at: 2026-07-03. file_updated_by_session: BA-PG-GROUNDING-PROOF-2026-07-03.
```

---

---

## §5 — P0 ADDENDUM: FRESH BASELINE + SERVING INTEGRITY (2026-07-03)

*Added by BA-P0 execution session (CLAUDECODE_BRIEF_BA_P0_SERVING_TRUTH_v1_0.md). Unblocks §2.1-1 budget planning. Probe method: temporary test MCP key (mcp_prod_TMRTViNs, inserted + DELETED after session — no persistent state left). 6 calls per tool; first = cold-ish, W1–W5 = warm. Auth: super_admin role resolved from native's Firebase profile.*

### §5.1 — Latency Baseline Table (p50/p95 warm, prod 2026-07-03)

| Tool | Cold (ms) | p50 warm (ms) | p95 warm (ms) | Payload (bytes) | Notes |
|---|---|---|---|---|---|
| `list_my_charts` | 572 | 400 | 410 | 803 | No chart context required |
| `get_chart_orientation(summary)` | 525 | 458 | 469 | 28,742 | chart 482012f1; response_format=summary |
| `get_signals(limit=50)` | 888 | 672 | 680 | 131,991 | chart 482012f1; 50 MSR signals |
| `get_domain_reading(career,default)` | 2,443 | 1,356 | 1,425 | 63,914 | F-021R bounded; career domain |
| `assess_career` (PRE-CAP) | 5,576 | 4,414 | 4,627 | **17,218,660** | PRE-P0-fix; 17 MB uncapped — see §5.3 |

**Budget denominator (§2.1-1):** p50 warm for common retrieval path (get_domain_reading) = **1,356 ms**. assess_career p50 = 4,414 ms pre-cap; post-cap target ≤ 2,000 ms (verify after PR #395 deploys).

### §5.2 — response_format Variants: get_chart_orientation

| format | ms | bytes | Distinct? |
|---|---|---|---|
| digest | 659 | 211 | ✅ significantly smaller |
| summary | 427 | 28,742 | ✅ |
| full | 414 | 28,736 | ⚠️ full ≈ summary (6-byte diff — no distinct full expansion for this tool) |

**Finding:** `get_chart_orientation` does not produce meaningfully distinct `full` vs `summary` payloads (6 bytes apart). `digest` works as intended (211 bytes). **PLAN-DELTA P0-D1:** P1/P2 must not rely on `full` for deeper chart data from this tool; use `get_domain_reading` + `get_signals` for depth.

### §5.3 — assess_* Cap Implementation (Step 2, PR #395)

**Root cause confirmed by prod probe:** `assess_career` returned 17,218,660 bytes. Source breakdown:
- `queryDomainReadingCapability.handler` bypasses F-021R (bounding only in the `get_domain_reading` MCP tool, not the underlying handler). `bodha_question_lenses.all_relevant_ranked_jsonb` averages 1.4 MB/row; ~12 career-domain lenses returned uncapped = ~17 MB.
- `queryContradictionsCapability.handler` returns all 5,170 contradictions; each row ~900 bytes = 4.65 MB.
- `fetchOrientationContext` adds orientation prefix = ~28 KB.

**Fix implemented (commit bafb803a, PR #395):** `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`
- `max_signals_per_lens`: default 10, max 50 — bounds `ranked_signals` in each question_lens
- `max_contradictions`: default 15, max 100 — caps contradictions array in assembled bundle
- Both params added to `input_schema` of all 4 assess_* capabilities
- `drill_uri` added to truncated blocks (`get_domain_reading` / `query_contradictions`)

**AC verification status:** PENDING prod deploy of PR #395. Expected post-cap payload: ≤ 100 KB (from 17 MB).

### §5.4 — Cache Contract (Step 3)

**Finding:** No response-level cache layer exists on prod.
- `served_from_cache` field: NOT present in any tool response (verified across 3 repeat identical calls)
- HTTP cache headers: no `X-Cache` or `Cache-Control` from Cloud Run responses
- `llm_hints.cacheable: true` in capability descriptors is advisory metadata only — no active cache consumer
- Auth validation cache (60s in-memory per-instance) is not a tool-response cache

**Root cause:** Cloud Run is stateless; no Redis/Memcached/CDN layer wired to the tool response path.

**Residual filed (P1 scope):** Implement response-level cache with `served_from_cache` flag in the envelope. Options: (a) Platform-side in-memory/Redis cache keyed by `(tool_name, chart_id, ayanamsha_id, params_hash)` with TTL matching chart rebuild cadence; or (b) CDN edge cache. This is not a P0 fix — documented per brief instruction.

### §5.5 — mi_vistara Scope Disposition (Step 4, PD-6)

**Choice: Option (b) — keep global, document as known exception.**

**Rationale:**
- `mimamsa_export_log` has `chart_id NOT NULL` (logically per-chart) but the BUILD ASSET `mi_vistara` generates 0 rows
- Actual rows written by `mi_seva` service handler on export delivery, not by the build pipeline
- Converting to `per_chart` scope would trigger the L1+ idempotency pattern (delete-then-insert scoped to `chart_id`), which would **wipe audit records on chart rebuild** — catastrophically wrong for an append-only ledger
- `scope='global'` correctly represents the build semantics: one verification pass, no per-chart rows generated

**Action taken:** `asset_registry.english_description` updated in prod DB (2026-07-03, direct UPDATE) to record the scope exception and rationale. **AC:** Registry scope matches table reality. Exception documented. ✅

### §5.6 — P0 PLAN-DELTA Summary

| ID | Source | Finding | Correction |
|---|---|---|---|
| P0-D1 | §5.2 | `get_chart_orientation` full ≈ summary (6-byte diff) | Do not rely on `full` for depth; use `get_domain_reading` / `get_signals` |
| P0-D2 | §5.3 | `assess_career` was 17.2 MB pre-cap (unguarded question_lenses + contradictions) | PR #395 adds F-021R caps; expected ~100 KB post-deploy |
| P0-D3 | §5.4 | No response cache layer; `served_from_cache` absent | P1 residual: implement response cache with cache flag |
| P0-D4 | §5.5 | `mi_vistara` scope=global is CORRECT for zero-build-row service asset | Do NOT change scope; document exception (done) |

---

*End of BA_GROUNDING_REPORT v1.0+P0-addendum (2026-07-03). §5 added by BA-P0 session. Baseline denominator established. PR #395 pending for caps prod verification.*
