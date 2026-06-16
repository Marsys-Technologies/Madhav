---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_E_v1_0.md
stream: E — Pañcāṅga Service + Capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-E
branch: feature/l0fr-stream-e-panchanga-service
budget_cap_usd: 250
---

# Stream E — Pañcāṅga On-Demand Service

## §1 — Mission
Replace location-locked panchanga_daily with on-demand compute service. 5 retrieval capabilities. Migrate Phase 4C Bhubaneswar data into chart_panchanga_cache for native.

## §2 — Dependencies
Blocks on `state.yaml: gates.vimarsaka_a.status = pass`.

## §3 — Scope
1. Author `platform/python-sidecar/panchanga/panchanga_engine.py`:
   - `compute_panchanga(chart_id, lat, lon, date, tz_offset_hours) -> dict`
   - Uses pyswisseph (`.se1` bundled per Stream A)
   - tithi = (moon_long - sun_long) / 12 → lunar day at sunrise
   - vara = weekday at sunrise (location-dependent)
   - nakshatra = floor(moon_long / 13.333°) at sunrise
   - yoga = (sun_long + moon_long) / 13.333 mod 27
   - karaṇa = half-tithi
   - Sunrise/sunset via pyswisseph rsmi calculation for lat/lon
   - Returns: { tithi, vara, nakshatra, yoga, karana, sunrise_utc, sunset_utc, auspicious_windows: { choghadiya, hora, inauspicious } }
2. Author `/api/panchanga/compute` route in Madhav cockpit:
   - GET with { chart_id, date, lat?, lon? }
   - Lookup chart's lat/lon if not provided
   - Cache miss → invoke python-sidecar; cache hit → return from chart_panchanga_cache
3. **Migrate** existing Phase 4C 73,414 panchanga_daily rows (Bhubaneswar) into chart_panchanga_cache for native's chart_id; preserve Phase 4C work
4. Drop `panchanga_daily` table after migration
5. Capability registrations:
   - Tools: `query_panchanga`, `query_panchanga_range`, `query_muhurta`, `query_choghadiya`, `query_hora`
   - Resource: `marsys://resource/panchanga/native-lifetime`
6. Smoke tests:
   - Native birth 1984-02-05 Bhubaneswar → tithi=Shukla Tritiya, vara=Ravivara, nakshatra=Purva Bhadrapada
   - Mumbai same date → tithi can shift (proves location-awareness)

## §5 — Acceptance criteria
- panchanga_engine.compute() returns correct five limbs for native birth
- Mumbai vs Bhubaneswar return different sunrises (proving location-awareness)
- chart_panchanga_cache populated for native (73,414 rows migrated)
- 6 capabilities registered; parity_check passes
- 4-adapter smoke tests

## §6 — Budget $250.

## §7-§8 — Final summary
Standard format.
