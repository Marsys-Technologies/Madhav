# Lane 1c SERVICES-census — shard-1c-b0

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Chart: 482012f1-710e-4a25-994a-93821f5871aa (native Abhisek).
Wire: :8000 compute endpoints (openapi) + :3000 MCP surgical primitives. Rider 2: compute-on-demand graded against E-6 with quoted payload.

## Service results (6/6)

### S1 — ga_chart_service (L1 on-demand recompute)  → FAIL / UNREACHABLE (class 1)
- MCP `ga_chart_service` → `{"ok":false,"error":{"class":"validation","message":"Tool not in surgical whitelist: ga_chart_service"}}` (full-pipeline-only, LCA-2 consult broken).
- `/api/compute/brahma/holistic_bundle` (candidate chart-facts front) → `Internal Server Error` (500).
- No consuming-LLM path recomputes L1 facts on demand. compute_reachable=FALSE. Matches L1_GANITA_CLOSURE "service; no direct table" — by design, but a retrieval-plane gap for any LLM wanting fresh L1.

### S2 — natal-positions compute (`POST /ephemeris`)  → PASS
- Live swisseph compute from birth params (no DB dependency). Payload self-describing.
- Excerpt: `{"jd":2445735.717...,"positions":[{"planet":"Sun","longitude":291.9568,"sign":"Capricorn","nakshatra":"Shravana","pada":4,"retrograde":false,"speed":1.014217},{"planet":"Moon","longitude":327.055,"sign":"Aquarius","nakshatra":"Purva Bhadrapada","pada":3,...}]}`
- Sun Cap 21.95 / Moon PBhadra pada3 consistent with 7 FORENSIC anchors. compute_reachable=TRUE, usable=TRUE.

### S3 — ephemeris service query_ephemeris (`GET /brahmagyan/ephemeris/planet_position`)  → FAIL / UNREACHABLE (class 1, env)
- Future date `2030-06-15` and near date `2026-07-12`, planet=Saturn → both `500 {"detail":"DATABASE_URL not set"}`.
- Endpoint is table-backed (ephemeris_daily) and gates on DB BEFORE any live-swe fallthrough — so for a date not in the table it cannot compute; it errors first. Whole GET ephemeris family (planet_position/retrograde_periods/all_bodies_range/aspects/planet_transit) is DB-gated and DOWN in this env. compute_reachable=FALSE.
- Note: live ephemeris compute IS reachable via `POST /ephemeris` (S2) for birth-based positions — but there is NO reachable path for an arbitrary calendar-date planet longitude.

### S4 — retrograde / station-detection service  → FAIL / EMPTY-SHELL + UNREACHABLE (class 4 + 1)
- Claimed "sidecar POST /transit_search station branch" DOES NOT EXIST: `transit_search.event_type` enum = only `'aspect'|'conjunction'`; `event_type:"station"` → `422 Input should be 'aspect' or 'conjunction'`.
- Fallback `GET /brahmagyan/ephemeris/retrograde_periods?planet=Mercury...` → `500 DATABASE_URL not set`.
- No compute path serves retrograde stations to a consumer. compute_reachable=FALSE.

### S5 — transit search / transit-to-natal aspect (`POST /api/compute/transit_search`)  → PASS
- Live swe compute (no DB). Well-formed self-describing events.
- Excerpt (Saturn aspect to natal Moon lon 326.5, 2025-2028, orb 2.0): `[{"event_type":"aspect","event_datetime_ist":"2025-03-01T09:26:18","transit_planet":"Saturn","exact_longitude_deg":326.5,"orb_at_event_deg":0.0,"sign":"Aquarius","nakshatra":"Purva Bhadrapada","extra":{"aspect_deg":0}}, {...,"orb_at_event_deg":180.0,"extra":{"aspect_deg":180}}]`
- compute_reachable=TRUE, usable=TRUE. Two form caveats: (a) empty `[]` returned with NO envelope/receipt when 0 hits (window 2026-07-12+ → `[]`; searched-but-found-0 indistinguishable from failure — mild class-5/6); (b) the 180° row is emitted at `exact_longitude_deg:326.5` (the conjunction point) with `orb_at_event_deg:180.0` — the opposition is mislabeled as a hit at the conjunction longitude (possible class-2/6 form quirk). Minor; primary grade PASS.

### S6 — query_transits_over_natal (`POST /transits_over_natal`)  → FAIL / DEAD-ENDPOINT (class 1)
- `POST /transits_over_natal` → `404`. Endpoint absent from :8000 openapi (only `/brahmagyan/ephemeris/planet_transit` and `/api/compute/transit_search` exist). No MCP variant.
- The named "all-9-grahas over natal today" service is not served by any single path; would require N per-planet `transit_search` calls (undocumented composition → class-9 candidate). compute_reachable=FALSE.

## Summary
PASS: S2, S5. FAIL/UNREACHABLE: S1, S3, S4, S6. DB-down (:8000 has no DATABASE_URL) sinks the entire table-backed ephemeris GET family (S3/S4). Live-compute POST paths (/ephemeris, /transit_search) are healthy.

---

## ADDENDUM — re-probe 2026-07-12 (env regression + MCP-layer coverage)

The prior checkpoint above ran against a healthier :8000. On re-probe the compute env has DEGRADED, and I additionally exercised the MCP :3000 surgical layer (untested above). Reconciliation:

- **S2 natal-positions REGRESSED to DOWN.** `POST /ephemeris` now → `500 Internal Server Error` (2/2 retries); `POST /api/pyhora/compute` → `{"detail":"PyJHora not available: No module named 'jhora'"}`; `GET /api/pyhora/smoke` → `{"status":"error","error":"No module named 'jhora'","ephe_path":"/app/ephe"}`. The live natal-compute path that PASSED above is currently unreachable. Suspected layer: deployment/env (jhora dep absent, DATABASE_URL unset) — the whole pyjhora + DB-backed surface is down, not just S3/S4. compute_reachable NOW = FALSE.
- **S5 transit_search still PASS (confirmed this run).** conjunction Saturn↔Moon → real events e.g. `{"event_datetime_ist":"2025-04-25T08:23:33","exact_longitude_deg":333.0272,"orb_at_event_deg":0.0008,"sign":"Pisces","nakshatra":"Purva Bhadrapada"}`; aspect branch proven live (target 350°, 0°, 2026-28 → 2 events at Revati). This backend needs no DB/jhora, so it survives the regression.
- **NEW — MCP :3000 sidecar-proxy is DISHONEST (class 5), systemic.** The prior shard tested :8000 direct only. Via MCP the DB/engine-backed surgical primitives route to :8000 with a bad/absent api-key and get 401, yet the OUTER envelope lies:
  - `query_ephemeris` (2027-03-15 Mars): OUTER `ok:true, epistemics.confidence_band:"high", warnings:[]`; INNER `{"ok":false,"error":"sidecar 401: {\"detail\":\"Invalid API key\"}","count":0,"positions":[]}`.
  - `query_transit_event` (Saturn↔Moon conjunction): OUTER `ok:true, confidence_band:"high"`; INNER `{"ok":false,"error":"sidecar 401: Invalid API key","count":0,"rows":[]}`. This is INCONSISTENT (class 3) with the direct `/api/compute/transit_search` which returns real events for the equivalent query.
  A consuming LLM receives high-confidence ok:true empties — worse than an honest error. Suspected layer: MCP contract / sidecar auth.
- **S1 confirmed** full-pipeline-only (`Tool not in surgical whitelist: ga_chart_service`), consult broken per LCA-2.
- **S6 confirmed** `query_transits_over_natal` → `Tool not in surgical whitelist` (full-pipeline-only); direct `/transits_over_natal` + `/api/compute/transits_over_natal` → 404.

Current-wire grade (what a consuming LLM gets NOW): PASS = S5 only. All DB/pyjhora-backed compute (S1/S2/S3/S4/S6) unreachable; MCP-fronted ephemeris/transit primitives return dishonest ok:true empties.
