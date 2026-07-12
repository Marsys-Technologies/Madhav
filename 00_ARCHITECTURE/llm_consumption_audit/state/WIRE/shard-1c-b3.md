# Lane 1c SERVICES-census — shard-1c-b3

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Chart: 482012f1-710e-4a25-994a-93821f5871aa (native).
Wire: MCP surgical POST :3000/api/mcp/primitives/<tool>; compute :8000. status: COMPLETE (6/6 services).

| # | Service | compute_reachable | grade | path invoked |
|---|---|---|---|---|
| 1 | Naisargika dasha | YES | GREEN | query_dasha_periods system=naisargika |
| 2 | Vimshottari-KP sub-period dasha | YES | GREEN | query_dasha_periods system=vimshottari_kp |
| 3 | Jaimini Chara Dasha (sidecar) | NO | RED | MCP jaimini_chara_dasha + :8000 GET /jaimini_drishti/chara_dasha |
| 4 | Jaimini drishti (special aspect) | NO | RED | MCP query_jaimini_drishti + :8000 POST /jaimini_drishti |
| 5 | Sade Sati phase | NO | RED | MCP temporal + :8000 POST /sade_sati |
| 6 | Eclipse proximity/query | NO | RED | :8000 /eclipse_transits (404); no MCP tool |

## 1 — Naisargika dasha — GREEN
- Note: test_spec named `get_dashas` → NOT in surgical whitelist ("Tool not in surgical whitelist: get_dashas"). Live surgical tool is `query_dasha_periods` (system param). Capability alive; naming/discoverability note (class 9 low).
- `query_dasha_periods {system:"naisargika"}` → ok:true, 150 rows (window 2021-07-11..2031-07-11, cap<=3). L1 lord Venus 2016-02-05→2036-02-05 (20yr, natural-order consistent), two_pass_verified, citation_ref present.
- DB ground truth: chart_dashas system_id=naisargika = 21,945 rows. Reachable + usable.

## 2 — Vimshottari-KP sub-period dasha — GREEN
- `query_dasha_periods {system:"vimshottari_kp"}` → ok:true. Row level_n=2 Rahu, lord_natal_sign Taurus, dignity=exalted, natal_house 2, two_pass_verified.
- DB: distinct system_id `vimshottari_kp` = 5,760 rows, separate from `vimshottari` (45,882). Confirms V-12 namespace split (previously conflated). Reachable + usable.

## 3 — Jaimini Chara Dasha (dedicated sidecar) — RED (compute NOT reachable)
- MCP `jaimini_chara_dasha` (IS in whitelist) → ok:false "Retrieval tool not found in registry: jaimini_chara_dasha" = **DEAD-19 / LCA-1** (class 1 UNREACHABLE).
- Sidecar :8000 GET /jaimini_drishti/chara_dasha → HTTP-level EXTERNAL_COMPUTATION_REQUIRED: "[jaimini_router] DATABASE_URL not set. Refusing to substitute fallback longitudes (M-8 fix)." Compute refuses (class 4 EMPTY SHELL / broken compute, high).
- Data plane: chart_dashas has NO rashi-based chara-dasha system_id (only `chara_karaka` = chara KARAKAS, a different concept; 155,135 rows). No table-read fallback exists. Rashi Chara Dasha = UNREACHABLE by both MCP and compute.

## 4 — Jaimini drishti (special aspect) — RED
- MCP `query_jaimini_drishti` (whitelisted) → ok:false "Retrieval tool not found in registry" = **DEAD-19 / LCA-1** (class 1).
- Sidecar :8000 POST /jaimini_drishti → {"status":"deprecated","message":"Use GET /jaimini_drishti/chara_dasha ..."} — redirects to a DASHA endpoint (not drishti-pairs) which is itself broken (see #3). No endpoint returns special-aspect pairs. UNREACHABLE (class 1) + no drishti stage served (class 4).
- test_spec expected a 'stub — not_implemented until M6' response; got a deprecation redirect instead — self-description drift (class 5 low).

## 5 — Sade Sati phase query — RED
- MCP `temporal` (whitelisted) → ok:false "Retrieval tool not found in registry: temporal" = **DEAD-19 / LCA-1** (class 1).
- Sidecar :8000 POST /sade_sati → {"status":"not_implemented","message":"sade_sati: endpoint not yet implemented"} (class 4 EMPTY SHELL).
- Data plane: **sade_sati_phases table does NOT exist** (information_schema: no %sade% table). test_spec's "backed by sade_sati_phases table" claim is false → UNREACHABLE-BY-NONEXISTENCE (data plane). No phase (rising/peak/setting) served by any path.

## 6 — Eclipse proximity/query — RED
- :8000 /eclipse_transits → HTTP 404 (POST and GET); endpoint absent from openapi.json.
- No eclipse MCP tool in surgical whitelist; no query_transit_event eclipse facet exposed.
- Data plane: **eclipses table does NOT exist** (no %eclipse% table). Full UNREACHABLE-BY-NONEXISTENCE (class 1, data plane) — nothing computed, nothing served.

## Calibration-anchor touch
- LCA-1 (DEAD-19 "Retrieval tool not found in registry") rediscovered on 3 whitelisted tools: jaimini_chara_dasha, query_jaimini_drishti, temporal.
- LCA-2 (served-only-by-down-pipeline "not in surgical whitelist") rediscovered on get_dashas.
