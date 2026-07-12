---
lane: "1c"
title: "Services census + verifier"
status: CURRENT
generated: 2026-07-12
source: llm_consumption_audit / WIRE state (shards 1c-b0..b4)
chart: 482012f1-710e-4a25-994a-93821f5871aa (native Abhisek)
---

# LANE 1c — Services Census: Compute-on-Demand Reachability + Verifier

Wire probed: `:3000` MCP surgical primitives (`/api/mcp/primitives/<tool>`, the real consumer path, DB-wired) + `:8000` python-sidecar `/api/compute/*` (NOT DB-configured this env — `DATABASE_URL not set`). Compute-on-demand graded against test-spec with quoted payload. 30 services across 5 shards.

## Environment substrate (governs grades)

- `:3000` MCP surgical layer is DB-wired and is the authoritative consumer path.
- `:8000` sidecar is **DB-down** (`DATABASE_URL not set`), sinking the entire table-backed ephemeris GET family and every DB-dependent compute endpoint. Live-compute POST paths that need no DB (`/ephemeris`, `/api/compute/transit_search`) survived early probes; on 2026-07-12 re-probe `/ephemeris` REGRESSED to `500` (jhora dep absent: `No module named 'jhora'`).

## Verifier — grade tally (30 services)

| Grade | Services |
|---|---|
| PASS / GREEN (reachable + usable) | `POST /ephemeris` natal-positions (early; later regressed), `transit_search`, Vimshottari `query_dasha_periods`, Ashtottari, Kalachakra, Mudda, Naisargika, Vimshottari-KP |
| FAIL — DEAD-19 (LCA-1: whitelisted, no `TOOL_NAME_TO_URI`) | `jaimini_chara_dasha`, `jaimini_chara_dasha_full`, `query_jaimini_drishti`, `temporal`, `query_tara_balam`, `query_chandra_balam` |
| FAIL — served-only-by-down-pipeline (LCA-2: not whitelisted) | `ga_chart_service`, `get_dashas`, `query_transits_over_natal`, `prashna cast`, `recall_session` |
| FAIL — reachable-but-WRONG / DISHONEST | `query_panchanga` (date ignored), `query_varshaphala` (year inert), `query_dasha_periods system_id` (yogini/ashtottari/kalachakra→vimshottari), MCP `query_ephemeris`/`query_transit_event` (`ok:true` over sidecar 401) |
| FAIL — UNREACHABLE-BY-NONEXISTENCE (data plane empty) | Narayana dasha, Shoola dasha, Sade Sati (`sade_sati_phases` table absent), Eclipse (`eclipses` table absent), Graha Yuddha (no composed service), Active Yogas (no composed service) |
| FAIL — env / DB-down | `query_ephemeris` GET family, retrograde/station, chara-dasha compute (`M-8` refuses to fabricate — B.10-compliant) |
| EMPTY_SHELL (honest, by-design stub) | `v7_additions` (`not_implemented` pending M6) |

## Highest-severity service findings

- **CRITICAL — `query_dasha_periods` `system_id` silently ignored.** yogini, ashtottari, kalachakra ALL echo the requested system in `invocation_params` but serve VIMSHOTTARI (`facets_applied.system:"vimshottari"`, lord Mercury). **~437k rows across 7 non-vimshottari systems are UNREACHABLE** via the only dasha serving tool when addressed by the natural `system_id` key. (The `system` key DOES work — see PASS rows — so the capability is alive but discoverable only under an undocumented param name.) Class 2 WRONG + class 5 DISHONEST + class 1 UNREACHABLE.
- **HIGH — `query_panchanga` date ignored.** `date=2035` and `date=2040` both return the natal birth-day panchanga from `chart_facts`; live engine exists (muhurta path computes it) but is not wired → retrieval-plane gap. Class 2 + class 5.
- **HIGH — `query_varshaphala` year inert.** `year=2030` / `year=2045` both return identical static natal Tajika facts; no solar-return chart (no Varsha Lagna / Muntha / Varshesha / Sahams). Class 4 EMPTY SHELL + class 5.
- **HIGH — DEAD-19 cluster.** `query_tara_balam` + `query_chandra_balam` are whitelisted but error `Retrieval tool not found in registry ... TOOL_NAME_TO_URI missing`; compute exists (`panchang_engine/tara_bala.py`) but is unwired, and the `query_panchanga` fallback returns `native_context:null` even with `chart_id`. Class 1 + class 5.
- **SYSTEMIC (class 5) — MCP sidecar-proxy dishonest envelope.** DB/engine-backed primitives route to `:8000` with a bad api-key, get 401, yet the OUTER envelope reports `ok:true, confidence_band:"high", warnings:[]` wrapping INNER `{"ok":false,"error":"sidecar 401: Invalid API key","count":0}`. A consuming LLM receives high-confidence `ok:true` empties — worse than an honest error. INCONSISTENT (class 3) with direct `/api/compute/transit_search`, which returns real events. Starves every transit-dependent service (graha yuddha, active yogas).

## Anchor rediscovery (verifier confirmation)

- **LCA-1** (DEAD-19: whitelisted tool, no `TOOL_NAME_TO_URI`) independently reproduced on `jaimini_chara_dasha`, `jaimini_chara_dasha_full`, `query_jaimini_drishti`, `temporal`, `query_tara_balam`, `query_chandra_balam`.
- **LCA-2** (served-only-by-down-pipeline: `Tool not in surgical whitelist`) reproduced on `ga_chart_service`, `get_dashas`, `query_transits_over_natal`, `recall_session`, `prashna cast`.

## Bottom line

Of the consuming-LLM compute surface, only the DB-free live-compute POST paths (`transit_search`, and natal `/ephemeris` before its jhora regression) and the `query_dasha_periods {system:...}` reads are trustworthy NOW. Every DB-backed compute path is down (env), every dedicated Jaimini/Tara/Chandra tool is DEAD-19, and the MCP proxy cloaks 401s as high-confidence successes. Six named services are UNREACHABLE-BY-NONEXISTENCE (data never landed / table absent), which no amount of wiring fixes.
</content>
