---
session_id: DAR-P7-S23
phase: 7
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P3-S10, DAR-P4-S14, DAR-P5-S20, DAR-P6-S22]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md  # create
must_not_touch:
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
---

# DAR-P7-S23: MCP tool layer comprehensive test — all 21 tools

## Context

All data layers are now loaded. This session stress-tests the MCP tool layer against the
reconciled data state. All 21 MCP tools must return correct data. Key counts: 573 signals,
57 LEL events, 4,011 school_signal_coverage rows, MEAN_NODE Rahu.

## Steps

1. For each of the 21 MCP tools, run a representative query and record the result.
   Use direct DB queries or the MCP sidecar endpoint (amjis-mcp).

   Core asset reads:
   - `read_asset(MSR)` → verify returns MSR_v5_0.md content (573-signal file), source = MSR_v5_0
   - `read_asset(LEL)` → verify returns LEL v1.7 content (57 events)
   - `read_asset(CGM)` → verify returns CGM file
   - `read_asset(UCN)` → verify returns UCN file

   Signal queries:
   - `query_signals(domain='lagna')` → verify non-empty, signals have derivation_ledger
   - `query_signals(count=true)` → verify total count = 573

   Chart facts:
   - `query_chart_facts(category='ashtakavarga')` → verify non-empty (new category from S11)
   - `query_chart_facts(category='sthira_karaka')` → non-empty

   Ephemeris:
   - `query_ephemeris(date='1984-02-05', planet='Rahu')` → verify nakshatra matches FORENSIC

   Holistic bundle:
   - `holistic_bundle()` → verify returns data from MSR + UCN + CDLM + CGM + RM

   School convergence:
   - `multi_school_bundle(signal_id='SIG.MSR.001')` → verify 7 school rows returned

   LEL:
   - `query_lel()` → verify returns 57 events

2. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md`:
   ```yaml
   # MCP Tool Layer Test Report — Phase 7 S23
   # Generated: [timestamp]

   read_asset_MSR: PASS
   read_asset_LEL: PASS
   read_asset_CGM: PASS
   read_asset_UCN: PASS
   query_signals_count: 573
   query_chart_facts: PASS
   query_ephemeris_rahu: PASS
   holistic_bundle: PASS
   multi_school_bundle: PASS
   lel_count: 57
   tools_pass: 21
   tools_fail: 0
   ```

3. Commit:
   ```
   dar: P7-S23 MCP tool comprehensive test — all 21 PASS; signals=573, lel=57
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md` → TRUE
- `grep 'read_asset_MSR: PASS' MCP_TEST_REPORT.md` → match
- `grep 'query_signals_count: 573' MCP_TEST_REPORT.md` → match
- `grep 'holistic_bundle: PASS' MCP_TEST_REPORT.md` → match
- `grep 'query_chart_facts: PASS' MCP_TEST_REPORT.md` → match
- `grep 'query_ephemeris_rahu: PASS' MCP_TEST_REPORT.md` → match
- `grep 'lel_count: 57' MCP_TEST_REPORT.md` → match
- `grep 'tools_pass: 21' MCP_TEST_REPORT.md` → match
