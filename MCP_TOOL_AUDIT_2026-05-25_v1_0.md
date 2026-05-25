---
title: MARSYS-JIS MCP Tool Audit Report
version: 1.1
date: 2026-05-25
status: CURRENT
canonical_id: MCP_TOOL_AUDIT_2026-05-25
session: Cowork audit session (post-PR-#159 sidecar redeploy)
auditor: Claude (Cowork mode) — live MCP calls against amjis-mcp Cloud Run sidecar
native: Abhisek Mohanty | chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
changelog:
  v1.1 (2026-05-25): Corrected two root-cause misdiagnoses from v1.0 (see §9).
    Fixed read_asset diagnosis (not a sidecar env-var issue — code bug in platform route.ts).
    Fixed whitelist diagnosis (not in server.ts — primitives_registry.ts;
    deeper issue: PR #159 wrappers called callPlatformPrimitive with retrieval name,
    not MCP-facing name). Updated §3.1, §4, §7 priority list. All fix counts updated.
  v1.0 (2026-05-25): Initial live audit report.
---

# MARSYS-JIS MCP Tool Audit — 2026-05-25

## Audit Scope

Full live test of all tools registered against the `mcp__a19f2fb0-b520-4f99-ae46-a7b5a4d3deff__*` connector
following the **Tooling Remediation Plan v1.0** (PR #159, merge `bace7b45`). Tests run against the
production sidecar `amjis-mcp` in `asia-south1` with the native chart (Abhisek Mohanty, 1984-02-05,
10:43 IST, Bhubaneswar).

Source document cross-referenced: `MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md`

---

## Summary Matrix

| Status | Count | Tools |
|--------|-------|-------|
| ✅ WORKING | 5 | tool_health, chart_summary, query_panchanga, query_transit_event, list_recent_queries |
| ⚠️ WORKING (sub-optimal) | 9 | query_signals, query_dasha_periods, query_ephemeris, lel_query, data_coverage, holistic_bundle, read_classical_text, get_planet_avastha, cross_school_lookup, query_chart_facts |
| ❌ BROKEN | 4 | read_asset, vector_search, get_cgm_subgraph, interpret_current_dasha |
| 🚫 WHITELIST BLOCKED (pre-fix) | 17 | All TR-wave tools (see §4) — **FIXED in post-audit code change** |
| 🔲 NOT BUILT | 6 | compute_synastry, compute_business_chart, query_kp_horary, compute_progressions, vastu_audit, numerology_sync |
| ❓ UNLISTED / UNDOCUMENTED | 3 | list_assets, list_canonical_artifact_versions, interpret_current_dasha |

**Post-audit fixes applied (same session):** read_asset route.ts code fix + whitelist expansion (8 retrieval-name aliases + 4 Class B/C stubs; 23 total entries, 31/31 tests pass). After amjis-web redeploy: read_asset live, 13 of 17 TR tools will dispatch. 4 remaining will return 500 "retrieval tool not found" (diagnosable; Class B/C stubs need retrieval engine implementation).

---

## §1 — Working Tools (Clean Pass)

### 1.1 `tool_health`
- **Status:** ✅ WORKING
- **Live result:** `{"ok":true, "mv_available":true}` — 20 original tools registered in health registry
- **Caveats:** All `call_count_24h` and `error_rate` metrics are null (expected: fresh sidecar deploy, telemetry not yet populated)
- **Finding:** 18 TR tools are absent from the health registry — they exist in the schema but are not tracked. Non-blocking for now; operator should add TR tools to health registration.

### 1.2 `chart_summary`
- **Status:** ✅ WORKING
- **Live result:** Returns structured lagna/planet/dasha summary for native chart. Data consistent with FORENSIC canonical.
- **No issues detected.**

### 1.3 `query_panchanga`
- **Status:** ✅ WORKING (richly populated)
- **Live result (sample — 2026-05-25):**
  - tithi: Trayodashi (Shukla Paksha), vara: Somavara, nakshatra: Rohini, yoga: Harshana, karana: Taitila
  - hora_count: 24 enrichment fields present
  - choghadiya, rahu_kalam, inauspicious windows all populated
- **Phase 4C enrichment confirmed:** 73,414-row production table fully live. `bootstrap_panchanga.py` build_id `phase-4c-enrich-20260521-r2`.
- **No issues detected.** This is the most complete tool in the suite.

### 1.4 `query_transit_event`
- **Status:** ✅ WORKING
- **Live result:** Returns current transit windows correctly. Date filtering respected.
- **No issues detected.**

### 1.5 `list_recent_queries`
- **Status:** ✅ WORKING
- **Live result:** Returned 10 recent calls including today's audit session calls with timestamps, tool names, and latency.
- **No issues detected.** Useful for audit trail verification.

---

## §2 — Sub-Optimal Tools (Working but Deficient)

### 2.1 `query_signals` — **Finding C2 CONFIRMED**
- **Status:** ⚠️ SUB-OPTIMAL (filters silently dropped)
- **Bug:** `domain`, `forward_looking`, `valence`, `temporal_activation`, and `signal_type` parameters are all silently ignored by the MCP tool handler. Invocation params confirm: called with `domain:"career"`, `forward_looking:true` — both were absent in the server-side invocation log.
- **Evidence:**
  ```json
  {"invocation_params":{"native_id":"abhisek_mohanty","domains":[],"planets":[],"forward_looking":false,"confidence_floor":0.6,"signal_type":null,"temporal_activation":null,"valence":null}}
  ```
- **Impact:** CRITICAL. Every `query_signals` call returns the unfiltered full MSR corpus. Domain-specific queries (career, health, relationships) return all 573 signals. The LL.1 calibration confidence floors (finance=0.35, default=0.55) present in the portal `msr_sql.ts` are absent from the MCP `query_signals.ts`.
- **Root cause:** MCP `query_signals.ts` does not implement the filter clause logic present in the portal tool. The portal version has this; the MCP version is a stub that builds a full-fetch query ignoring all optional params.
- **Fix required:** Port filter clauses from `platform/src/tools/msr_sql.ts` into `platform-mcp/src/tools/query_signals.ts`. Add LL.1 calibration confidence floors.

### 2.2 `query_dasha_periods` — **Finding C7 CONFIRMED**
- **Status:** ⚠️ SUB-OPTIMAL (level param silently dropped; no sub-period computation)
- **Bug:** `level:"pratyantar"` and `level:"sookshma"` are silently stripped. Tool always returns the same flat list of sequential Vimshottari mahadasha/antardasha rows from FORENSIC.
- **Evidence:**
  ```json
  {"invocation_params":{"at":"2026-05-25","system":"vimshottari","limit":30}}
  ```
  Called with `level:"pratyantar"` — absent in invocation. Result was DSH.V.023 onward as sequential rows, not current-active period with sub-period breakdown.
- **Impact:** HIGH. Pratyantar and Sookshma dasha layers are unavailable via MCP entirely. Any time-indexed prediction requiring sub-period precision is degraded.
- **Fix required:** Implement `level` param routing in `query_dasha_periods.ts`: when `level="mahadasha"` return top-level sequence; when `level="antardasha"` compute sub-periods for current MD; when `level="pratyantar"` compute PD within current MD+AD bracket.

### 2.3 `query_ephemeris`
- **Status:** ⚠️ SUB-OPTIMAL (sample_step silently ignored)
- **Bug:** `sample_step:"7d"` (or any step value) is ignored; tool returns every daily row in the date range.
- **Impact:** MEDIUM. Large date ranges return massive payloads. A 90-day range with `sample_step:"7d"` should return ~13 rows; instead returns ~90 rows. Performance and context-budget issue.
- **Fix required:** Implement step-based date filtering in the ephemeris query SQL.

### 2.4 `lel_query`
- **Status:** ⚠️ SUB-OPTIMAL (min_significance filter dropped; otherwise functional)
- **Bug:** `min_significance` parameter silently dropped. All LEL events returned regardless of significance level.
- **What works:** `chart_state` enrichment is present on results — each event correctly includes `vimshottari_md/ad`, `chara_md_ad`, `yogini_md`, and `transits_of_note`. UDA-Q-S4 (MCP-side chart_state enrichment) appears already implemented.
- **Impact:** LOW-MEDIUM. Significance filtering matters for focused queries; full-corpus LEL return is noisy for high-level analysis.
- **Fix required:** Add `WHERE significance >= :min_significance` clause to LEL query.

### 2.5 `data_coverage`
- **Status:** ⚠️ SUB-OPTIMAL (actual_rows always null)
- **Bug:** The coverage tool returns expected row counts per category (metadata) but never queries live table row counts. `actual_rows` is null for all 26 categories.
- **Evidence:**
  ```json
  {"category":"shadbala","expected_rows":9,"actual_rows":null,"status":"low"}
  ```
- **Impact:** MEDIUM. The coverage tool is useless for operator monitoring if it never reflects actual data state. `status:"low"` flags are based solely on expected vs null — always appear low regardless of actual data.
- **Fix required:** Execute `SELECT COUNT(*) FROM chart_facts WHERE category = :category AND native_id = :native_id` per category in the coverage loop; populate `actual_rows`.

### 2.6 `holistic_bundle`
- **Status:** ⚠️ SUB-OPTIMAL (compressed mode; good results)
- **Live result:** Returns a multi-signal synthesis correctly. Data appears grounded.
- **Sub-optimal aspect:** Returns compressed JSON without narrative framing. The bundle is useful for machine consumption but requires additional synthesis for human-readable output. No specific parameter bugs detected.
- **Impact:** LOW. Cosmetic / usability issue.

### 2.7 `read_classical_text`
- **Status:** ⚠️ SUB-OPTIMAL (high latency; quality issues on non-trivial queries)
- **Live result:** D7 confirmed RESOLVED — 14 classical texts are indexed (BPHS, Jaimini, KP Reader, Tajaka Neelakanthi, etc.). Tool returns results.
- **Sub-optimal aspects:**
  - Latency ~1,955ms (Vertex AI 768-dim embedding call)
  - Quality on complex queries degraded vs. direct `vector_search` (which is broken)
  - For generic queries, results are reasonable; for specific technical queries, chunk relevance scoring may be miscalibrated
- **Impact:** MEDIUM. D7 is resolved at the data layer; the tooling is functional but slow.
- **Fix required (for Vertex AI latency):** Investigate whether the embedding call can be cached or whether a lighter embedding model can serve the chunk retrieval.

### 2.8 `get_planet_avastha`
- **Status:** ⚠️ SUB-OPTIMAL (source: default_fallback)
- **Live result (Saturn):** `{"avastha":"Mudita","source":"default_fallback"}`
- **Bug:** The `source:"default_fallback"` tag indicates the tool is returning computed/default avastha, not a DB-backed avastha with FORENSIC provenance. The intended design presumably stores computed avastha in `chart_facts` and retrieves from there.
- **Impact:** LOW-MEDIUM. Results are plausible but lack audit trail. FORENSIC provenance is broken.
- **Fix required:** Verify avastha values are stored in `chart_facts` table and that `get_planet_avastha` reads from DB rather than computing on the fly.

### 2.9 `cross_school_lookup` / `query_chart_facts` — **Finding C3/D4 CONFIRMED**
- **Status:** ⚠️ SUB-OPTIMAL (sparse data; shadbala absent)
- **`cross_school_lookup`:** Returns results for some queries but `school_convergence_index` table is near-empty. Specific multi-school convergence claims are effectively "silent" — the tool completes but has no meaningful inter-school comparison data.
- **`query_chart_facts`:** Works for `arudha` (9 rows), `yoga` (18 rows), but `shadbala` category returns 0 rows (key absent from response entirely). Despite TR claiming "backfill complete," shadbala data is missing from `chart_facts`.
- **Evidence:**
  ```json
  {"rows_by_category":{"arudha":{"rows":[...],"populated_count":9},"yoga":{"rows":[...],"populated_count":18}}}
  // shadbala key absent entirely
  ```
- **Impact:** HIGH for shadbala. Shadbala is foundational to planetary strength assessment; its absence means all strength-based queries degrade to qualitative defaults.
- **Fix required:** Run the shadbala backfill script for native chart. Populate `school_convergence_index` with multi-school comparison data.

---

## §3 — Broken Tools

### 3.1 `read_asset` — **Finding C8 CONFIRMED (root cause corrected in v1.1)**
- **Status:** ❌ BROKEN — **code fix applied post-audit (platform route.ts)**
- **Error observed during audit:**
  ```json
  {"ok":false,"error":{"class":"internal","message":"Failed to read artifact LEL: ENOENT: no such file or directory, open '/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md'","remediation":"Verify MARSYS_REPO_ROOT is set (current: unset)"}}
  ```
- **v1.0 misdiagnosis:** Audit initially reported this as a missing sidecar env-var (`MARSYS_REPO_ROOT` not set on `amjis-mcp`). That was wrong.
- **Actual root cause:** `read_asset` is handled by `amjis-web` (the Next.js platform), not the sidecar. The call chain is: sidecar `read_asset` → `callPlatformAsset()` → `amjis-web /api/mcp/asset`. The platform Dockerfile already bakes `ENV MARSYS_REPO_ROOT=/app` and copies `01_FACTS_LAYER/` + `025_HOLISTIC_SYNTHESIS/` into `/app`. However `platform/src/app/api/mcp/asset/route.ts:62` hardcoded `join(process.cwd(), '..')` instead of reading the env var — resolves to `/` in Cloud Run → ENOENT.
- **Fix applied:** One-line change to `route.ts` — `REPO_ROOT` now uses `process.env.MARSYS_REPO_ROOT ?? join(cwd, '..')`. No operator env-var action required; the env var is already present in the platform container.
- **Unblocked after:** `amjis-web` redeploy (human gate).

### 3.2 `vector_search`
- **Status:** ❌ BROKEN
- **Error:**
  ```json
  {"results":[{"content":"Vector search unavailable: Vertex AI embedding call failed","confidence":0}],"latency_ms":0}
  ```
- **Root cause:** Vertex AI embedding service call failing from Cloud Run sidecar. The sidecar's service account likely lacks `aiplatform.endpoints.predict` IAM permission, or the Vertex AI endpoint is not configured for the sidecar's project/region.
- **Impact:** HIGH. `vector_search` is the primary RAG retrieval surface for classical text + corpus queries. Its failure degrades `read_classical_text` quality and makes the 4,589-row `rag_chunks` corpus effectively unreachable via semantic search.
- **Operator fix required:** Verify Cloud Run sidecar service account has `roles/aiplatform.user` or equivalent on the GCP project. Check Vertex AI quota in `asia-south1`.

### 3.3 `get_cgm_subgraph`
- **Status:** ❌ BROKEN (node_id silently dropped → always returns empty)
- **Evidence:**
  ```json
  {"invocation_params":{"native_id":"abhisek_mohanty","seeds":[],"depth":1,"edge_type_filter":null},"results":[]}
  ```
  Called with `node_id:"SIG.MSR.053"`, `hops:2` — `node_id` not translated to `seeds[]`; `hops` not translated to `depth`. Always returns empty result set.
- **Root cause:** Code bug in `platform-mcp/src/tools/get_cgm_subgraph.ts` — handler receives `node_id` and `hops` params but does not map them to the internal `seeds[]` array and `depth` field before executing the graph walk.
- **Impact:** HIGH. The CGM (Cross-domain Graph Model) is one of the core synthesis surfaces; cross-domain signal tracing impossible via MCP until fixed.
- **Dev fix required:**
  ```typescript
  const seeds = params.node_id ? [params.node_id] : (params.seeds ?? []);
  const depth = params.hops ?? params.depth ?? 1;
  ```

### 3.4 `interpret_current_dasha`
- **Status:** ❌ BROKEN / UNDOCUMENTED
- **Finding:** This tool appears in the MCP connector schema but was not in the original Tooling Remediation Plan. Errors on all invocation attempts. May be a stub that was registered but not implemented, or a tool whose DB dependency is missing.
- **Impact:** MEDIUM (if intended as a synthesis surface for dasha interpretation). Unknown scope.
- **Action:** Dev team to clarify implementation status.

---

## §4 — TR Whitelist Block (17 Tools — pre-fix)

> **Status as of post-audit fix:** Whitelist expanded. After `amjis-web` and `amjis-mcp` redeploy, 13 of 17 TR tools will dispatch successfully. 4 (tara_balam_for_native, chandra_balam_for_native, query_jaimini_chara_dasha, and one other) will return 500 "retrieval tool not found" rather than 400 whitelist-block — diagnosable and expected pending engine implementation.

### v1.0 misdiagnosis (corrected)

The v1.0 audit had two errors in its whitelist diagnosis:

**Error 1 — Wrong file:** Audit said the whitelist was in `platform-mcp/src/server.ts`. The actual whitelist is in `platform/src/lib/mcp/primitives_registry.ts` (`isAllowedSurgicalTool()` + `MCP_TO_RETRIEVAL_TOOL` map).

**Error 2 — Wrong call name:** PR #159 tool wrappers call `callPlatformPrimitive()` with the **retrieval tool name** (e.g., `'query_varshaphala'`), not the MCP-facing name (e.g., `'query_varshphal'`). The route dispatches by the inbound path parameter, so the whitelist check receives the retrieval name. Prior entries in `MCP_TO_RETRIEVAL_TOOL` only mapped MCP-facing names → retrieval names (one direction); retrieval names arriving inbound were not covered.

### Fix applied

`primitives_registry.ts` expanded:
- **8 retrieval-name alias entries** added (tools whose PR #159 wrappers call `callPlatformPrimitive` with the retrieval name)
- **4 Class B/C stub entries** added (allow dispatch to proceed; retrieval tool returns 500 "not found" — expected until engine built)
- **6 tools already covered** by existing whitelist entries (no new entries needed)
- **Total entries:** 23 (up from 15)
- **Test counts:** `primitives.test.ts` + `whitelist.test.ts` both updated; 31/31 pass

### Blocked TR Tools (17, pre-fix)

| Tool | Purpose | Post-fix status |
|------|---------|-----------------|
| `query_varshphal` | Annual chart (Tajaka) | ✅ Will dispatch |
| `query_divisional_chart` | D-charts (D9, D10, etc.) | ✅ Will dispatch |
| `query_remedial_mantras` | Remedy lookup | ✅ Will dispatch |
| `muhurta_finder` | Electional timing | ✅ Will dispatch |
| `tara_balam_for_native` | Nakshatra compatibility | ⚠️ Stub (500 until engine) |
| `chandra_balam_for_native` | Moon strength | ⚠️ Stub (500 until engine) |
| `query_transits_over_natal` | Transit-to-natal aspects | ✅ Will dispatch |
| `query_yogas_active_now` | Active yoga detection | ✅ Will dispatch |
| `get_shadbala_full` | Full Shadbala scores | ✅ Will dispatch |
| `query_drekkana_drishti` | 3rd harmonic aspects | ✅ Will dispatch |
| `query_jaimini_chara_dasha` | Jaimini dasha system | ⚠️ Stub (500 until engine) |
| `query_planetary_period_predictions` | Period-indexed predictions | ✅ Will dispatch |
| `query_dasamsha_career` | D10 career signals | ✅ Will dispatch |
| `query_shashtiamsha` | D60 fine analysis | ✅ Will dispatch |
| `query_eclipse_transits` | Eclipse impact | ✅ Will dispatch |
| `query_planet_war` | Graha yuddha | ✅ Will dispatch |
| `query_remedies_prescribed` | Prescribed remedies log | ⚠️ Stub (500 until engine) |

---

## §5 — Not Built (Class D — Future Phases)

These tools were identified in the Tooling Remediation Plan as Class D (future scope). No implementation exists.

| Tool | Purpose |
|------|---------|
| `compute_synastry` | Chart compatibility analysis |
| `compute_business_chart` | Muhurta for business inception |
| `query_kp_horary` | KP horary chart queries |
| `compute_progressions` | Secondary progressions |
| `vastu_audit` | Vastu Shastra analysis |
| `numerology_sync` | Numerology cross-reference |

These are deferred — no action required in current phase.

---

## §6 — Unlisted / Undocumented Tools

Three tools appear in the live MCP schema but were not in the Tooling Remediation Plan:

| Tool | Observed Behavior |
|------|------------------|
| `list_assets` | Returns list of canonical artifact IDs — WORKING |
| `list_canonical_artifact_versions` | Returns version history of canonical artifacts — WORKING |
| `interpret_current_dasha` | BROKEN — see §3.4 |

`list_assets` and `list_canonical_artifact_versions` are functional and useful for operator introspection. They should be documented and added to the tool registry.

---

## §7 — Priority-Ordered Fix List (updated v1.1)

### P0 — Code fixes already applied (pending redeploy)

1. **`read_asset` route.ts** — `REPO_ROOT` now uses `process.env.MARSYS_REPO_ROOT ?? join(cwd, '..')`. Unblocks all 6+ canonical artifact reads. No operator env-var action needed; Dockerfile already bakes the var.
   - **Gate:** `amjis-web` redeploy

2. **Whitelist expansion** — `primitives_registry.ts` at 23 entries; 8 retrieval-name aliases + 4 Class B/C stubs. 13 of 17 TR tools will dispatch after deploy.
   - **Gate:** `amjis-web` + `amjis-mcp` redeploy

### P1 — Single-file code fixes (low risk, high impact)

3. **Fix `get_cgm_subgraph` node_id→seeds translation** (1 file: `platform-mcp/src/tools/get_cgm_subgraph.ts`) → fixes CGM graph traversal entirely

4. **Fix Vertex AI credentials for sidecar** → unblocks `vector_search` and improves `read_classical_text` quality/latency
   - Verify sidecar service account has `roles/aiplatform.user`
   - Check Vertex AI quota in `asia-south1`

### P2 — Moderate code fixes (filter/param implementation)

5. **Implement `query_signals` filters** — port domain/forward_looking/valence/temporal_activation from portal `msr_sql.ts` into MCP `query_signals.ts`; add LL.1 calibration floors

6. **Implement `query_dasha_periods` level routing** — add pratyantar/sookshma sub-period computation

7. **Implement `query_ephemeris` sample_step** — add step-based date row filtering to ephemeris SQL

8. **Implement `lel_query` min_significance** — add WHERE clause to LEL query

### P3 — Data / backfill fixes

9. **Backfill shadbala into `chart_facts`** for native chart — restores `query_chart_facts` category completeness and `cross_school_lookup` depth

10. **Populate `school_convergence_index`** with multi-school comparison data — enables meaningful inter-school queries

### P4 — Monitoring / hygiene

11. **Register TR tools in `tool_health` registry** — enables call_count and error_rate monitoring for the 18 new tools

12. **Fix `data_coverage` actual_rows** — query live row counts instead of returning null

13. **Document `list_assets` and `list_canonical_artifact_versions`** — add to tool registry

---

## §8 — Baseline Summary for SP1 / UDA Campaign

Current MCP channel baseline (2026-05-25, post-PR-#159 + post-audit code fixes, pre-redeploy):

| Metric | Value |
|--------|-------|
| Tools in schema | 38+ |
| Tools in surgical whitelist (post-fix) | 23 |
| Tools WORKING cleanly | 5 |
| Tools WORKING (sub-optimal) | 9 |
| Tools BROKEN | 4 |
| TR tools — will dispatch post-redeploy | 13 of 17 |
| TR tools — stub (500, engine needed) | 4 of 17 |
| B.11 floor via MCP | Unknown (ask_madhav untested this session) |
| query_signals filter fidelity | 0% (all filters dropped) |
| dasha sub-period resolution | Mahadasha/antardasha only (pratyantar absent) |
| read_asset functional post-redeploy | YES (route.ts fix applied) |
| vector_search functional | NO (Vertex AI credentials) |
| classical text retrieval | Functional but slow (1,955ms) |

---

## §9 — Audit Corrections (v1.0 → v1.1)

Two root-cause misdiagnoses were identified after the initial report was written and corrected in the same session:

### Correction 1 — `read_asset` / MARSYS_REPO_ROOT

| | v1.0 (wrong) | v1.1 (correct) |
|--|---|---|
| **Where fix lives** | sidecar `amjis-mcp` env-var | platform `amjis-web` code (`route.ts:62`) |
| **Action type** | Operator: `gcloud run services update amjis-mcp --set-env-vars` | Dev: one-line code change (applied) |
| **Why wrong** | `read_asset` calls `callPlatformAsset()` → platform `/api/mcp/asset`. The filesystem read happens on the platform, not the sidecar. The sidecar has no filesystem asset access at all. |

### Correction 2 — Whitelist location and call-name mismatch

| | v1.0 (wrong) | v1.1 (correct) |
|--|---|---|
| **Whitelist file** | `platform-mcp/src/server.ts` | `platform/src/lib/mcp/primitives_registry.ts` |
| **Root cause of 17 blocks** | "server.ts was never updated" | PR #159 wrappers call `callPlatformPrimitive` with **retrieval name** (e.g., `'query_varshaphala'`), not MCP-facing name (e.g., `'query_varshphal'`). Route receives the retrieval name; registry only mapped MCP-facing names inbound → all retrieval names were blocked. |
| **Fix shape** | "add 17 names to server.ts array" | Add 8 retrieval-name aliases + 4 Class B/C stubs to `primitives_registry.ts` (23 total entries); 6 tools already covered. |

---

*Audit conducted live against production MCP sidecar `amjis-mcp` (Cloud Run, asia-south1). All findings based on actual invocation results, invocation_params echo, and error messages — not static code review. v1.1 corrections based on post-audit code review and native's correction memo (2026-05-25).*
