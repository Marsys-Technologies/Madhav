---
session_id: DAR-P4-S14
phase: 4
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P4-S11, DAR-P4-S12, DAR-P4-S13]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md  # create
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
must_not_touch:
  - 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml  # finalized in S11-S13
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - platform/migrations/
---

# DAR-P4-S14: Load enhanced chart_facts to DB + update CAPABILITY_MANIFEST + verify MCP

## Context

Sessions S11–S13 have enhanced `CHART_FACTS_EXTRACTION_v1_0.yaml` to v1.2 with 15 new
categories. This session loads the updated YAML into the `chart_facts` DB table, updates
CAPABILITY_MANIFEST.json to reflect the new row count, and verifies MCP `query_chart_facts`
returns the new categories.

## Steps

1. Truncate and reload `chart_facts` from the enhanced YAML:
   ```bash
   cd platform/python-sidecar
   python3 -m pipeline.writers.chart_facts_writer \
     --source ../../01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml \
     --truncate
   ```
   If the writer doesn't support truncate flag:
   ```bash
   psql "$DATABASE_URL" -c "TRUNCATE TABLE chart_facts;"
   python3 -m pipeline.writers.chart_facts_writer \
     --source ../../01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
   ```

2. Verify row count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM chart_facts;"
   psql "$DATABASE_URL" -c "SELECT category, COUNT(*) FROM chart_facts GROUP BY category ORDER BY category;"
   ```
   Record total row count (should be > 2,717 — the MCP Transformation baseline).

3. Verify new categories are present:
   ```bash
   psql "$DATABASE_URL" -c "SELECT DISTINCT category FROM chart_facts WHERE category IN ('ashtakavarga','sthira_karaka','upagraha','bhrigu_bindu','yogi_avayogi','mrityu_bhaga','chalit_kinetic','avastha','longevity','narayana_dasha','moola_dasha','ishta_kashta','pancha_vargeeya') ORDER BY category;"
   ```

4. MCP spot-check — query via the MCP tool layer:
   ```bash
   # Use the amjis-mcp sidecar or direct DB query to simulate MCP query_chart_facts
   psql "$DATABASE_URL" -c "SELECT * FROM chart_facts WHERE category='ashtakavarga' LIMIT 3;"
   ```
   Expected: rows returned (not empty).

5. Update `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — find the `chart_facts` entry,
   update `row_count` to the actual count, update `version` if present.

6. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md`:
   ```yaml
   # chart_facts Load Report — Phase 4 S14
   # Generated: [timestamp]

   chart_facts_row_count: <N>
   new_categories_loaded: [ashtakavarga, sthira_karaka, upagraha, bhrigu_bindu, yogi_avayogi, mrityu_bhaga, chalit_kinetic, avastha, longevity, narayana_dasha, moola_dasha, ishta_kashta, pancha_vargeeya]
   mcp_query_chart_facts: PASS
   capability_manifest_updated: true
   ```

7. Commit:
   ```
   dar: P4-S14 load enhanced chart_facts v1.2 to DB; update CAPABILITY_MANIFEST; MCP verify PASS
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md` → TRUE
- `grep 'chart_facts_row_count:' CHART_FACTS_LOAD_REPORT.md` → match
- `grep 'mcp_query_chart_facts: PASS' CHART_FACTS_LOAD_REPORT.md` → match
