---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_B_v1_0.md
stream: B — Ephemeris Bulk Build + Capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-B
branch: feature/l0fr-stream-b-ephemeris
budget_cap_usd: 150
tier3_escalation_usd: 5000
---

# Stream B — Ephemeris

## §0-§0.5
Same discipline as Stream A. Master plan, source data, Vimarśaka specs are required reading.

## §1 — Mission
Compute 1900-2150 × 9 bodies ephemeris (~822k rows) using pyswisseph + bundled `.se1` files. Register 6 ephemeris capabilities in unified registry.

## §2 — Dependencies
Blocks on `state.yaml: gates.vimarsaka_a.status = pass`. Poll every 60 sec; start when condition met.

## §3 — Scope
1. **Rewrite** `platform/python-sidecar/brahmagyan/l0_ephemeris.py`:
   - Date range: 1900-01-01 to 2150-12-31 (91,313 days)
   - Bodies: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu (mean), Ketu (mean)
   - Columns: date, body, longitude_tropical, latitude, speed_dps, is_retrograde, computed_at
   - Use `COPY FROM stdin` for bulk insert
   - VOLUME_FLOOR constant = 821,250 (not 29,200)
2. Run the writer; complete in ~15-30 min
3. JPL Horizons sanity check (one date): Sun's longitude 2000-01-01 00:00 UT, tolerance ≤2 arcsec
4. Spot checks against native chart (per source data §7):
   - 1984-02-05 Sun → ~291.8° tropical = Capricorn 21°48' (Lahiri-corrected at consumption)
   - 2050-01-01 Saturn → Pisces ~27°
5. **Capability registrations** (per master plan §8 Stream B):
   - Tools: `query_planet_position`, `query_planet_transit`, `query_aspects_at_time`, `query_retrograde_periods`
   - Resources: `marsys://resource/ephemeris-cache/year/<yyyy>`, `marsys://resource/ephemeris-cache/native-lifetime`
6. Each capability authored at `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/`
7. MCP mirror at `platform-mcp/src/tools/`
8. Each capability invoked through all 4 adapter modes; agentic/bulk_context/openai_function_calling/hybrid all return Capricorn 21°48' for native birth

## §4 — Capability registrations
6 capabilities. Mark `expose_mcp=true`, `expose_consume_chat=true`.

## §5 — Acceptance criteria (programmatic)
- `SELECT count(*) FROM ephemeris_daily ≥ 820,000`
- `SELECT longitude_tropical FROM ephemeris_daily WHERE date='1984-02-05' AND body='Sun'` returns ~291.8°
- 4-adapter smoke test all pass
- parity_check still passes (6 new capabilities mirrored)
- JPL Horizons cross-check within 2 arcsec

## §6 — Budget
Tier-3 cap $150. Pure compute + minor LLM in smoke tests.

## §7 — Pre-Vimarśaka readiness
Same protocol as Stream A.

## §8 — Final summary
```yaml
---FINAL_SUMMARY---
stream: B
status: READY_FOR_REVIEW
ephemeris_row_count: <N>
spot_checks_passed: <N>/3
capabilities_registered: 6/6
adapter_smoke_results: { agentic: pass, bulk_context: pass, openai: pass, hybrid: pass }
budget_spent_usd: <N>
---END_FINAL_SUMMARY---
```
