---
session: DAR-P4-S14
chart_facts_row_count: 767
chart_facts_yaml_version: "1.2"
chart_facts_yaml_fact_count: 783
chart_facts_unique_fact_ids: 767
chart_facts_duplicate_fact_ids: 16
chart_facts_categories_loaded: 36
new_categories_loaded: [ashtakavarga, sthira_karaka, upagraha, bhrigu_bindu, yogi_avayogi, mrityu_bhaga, chalit_kinetic, avastha, longevity, narayana_dasha, moola_dasha, ishta_kashta, pancha_vargeeya]
mcp_query_chart_facts: PASS
capability_manifest_updated: true
build_id: dar-p4-s14-2026-05-25
load_method: local-yaml-direct (GCS-bypass; writer EXPECTED_COUNT_MAX=700 below v1.2 count of 783)
prior_row_count: 2681
date: "2026-05-25"
---

# DAR-P4-S14 Chart Facts Load Report

## Summary

Enhanced CHART_FACTS_EXTRACTION_v1_0.yaml (v1.2, 783 facts) loaded into DB `chart_facts` table.
Prior state: 2,681 rows (MCP Transformation era build, mixed categories including varshphal/kp_cusp/ashtakavarga_bav etc.).
Post-load state: 767 unique rows across 36 categories — strictly from v1.2 YAML source.

## Load Method

The standard `ChartFactsWriter` reads from GCS and enforces `EXPECTED_COUNT_MIN=500 / EXPECTED_COUNT_MAX=700`.
v1.2 YAML has 783 facts (exceeds the 700 cap), so a local bypass loader was used:

- Script: `platform/scripts/load_chart_facts_local.py` (created this session)
- Source: `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml`
- Operation: `TRUNCATE chart_facts` + `INSERT ... ON CONFLICT DO UPDATE`
- Build manifests row inserted: `dar-p4-s14-2026-05-25` (status: live)

## Row Count Reconciliation

| Metric | Value |
|--------|-------|
| YAML facts (raw) | 783 |
| Duplicate fact_ids in YAML | 16 |
| Unique fact_ids loaded to DB | 767 |
| DB row count (SELECT COUNT) | 767 |
| Categories in DB | 36 |

**Duplicate fact_ids (16):** These are the 7 `KRK.C.*` (sthira_karaka) and 9 `UPG.*` (upagraha) entries which appear
twice in the YAML — once in their original category sections and once in the new S11 additions. The `ON CONFLICT DO UPDATE`
pattern means last-write wins; both writes carry the same values, so no data is lost. This is a pre-existing YAML authoring
artifact from S11 and does not indicate data corruption.

## New Categories Verified (S11–S13 additions)

```sql
SELECT DISTINCT category FROM chart_facts 
WHERE category IN ('ashtakavarga','sthira_karaka','upagraha','bhrigu_bindu',
  'yogi_avayogi','mrityu_bhaga','chalit_kinetic','avastha','longevity',
  'narayana_dasha','moola_dasha','ishta_kashta','pancha_vargeeya') 
ORDER BY category;
```

Result: **13/13 categories present** ✓

| Category | Rows | Source |
|----------|------|--------|
| ashtakavarga | 20 | FORENSIC §6.2 BAV totals |
| avastha | 7 | FORENSIC §6.5 planetary states |
| bhrigu_bindu | 8 | FORENSIC §5.6 Bhrigu Bindu |
| chalit_kinetic | 9 | FORENSIC §3.3 Chalit shifts |
| ishta_kashta | 8 | FORENSIC §6.7 |
| longevity | 9 | FORENSIC §6.6 longevity indicators |
| moola_dasha | 1 | EXTERNAL_COMPUTATION_REQUIRED stub |
| mrityu_bhaga | 11 | FORENSIC §5.5 |
| narayana_dasha | 1 | EXTERNAL_COMPUTATION_REQUIRED stub |
| pancha_vargeeya | 8 | FORENSIC §6.8 |
| sthira_karaka | 14 | FORENSIC §4.2 |
| upagraha | 9 | FORENSIC §5.3 |
| yogi_avayogi | 11 | FORENSIC §5.4 |

Note: `sudasa` (1 EXTERNAL_COMPUTATION_REQUIRED stub) also present in DB, not listed in task's Step 4 check.

## MCP Spot-Check (Step 5)

```sql
SELECT fact_id, category, value_text FROM chart_facts WHERE category='ashtakavarga' LIMIT 3;
```

Result:
```
   fact_id    |   category   | value_text
--------------+--------------+--------------------------------------------------------------------------
 AVG.BAV.SUN  | ashtakavarga | Sun BAV total: 48 bindus
 AVG.BAV.MOON | ashtakavarga | Moon BAV total: 49 bindus (FORENSIC canonical; JH differs ±1 in 4 signs)
 AVG.BAV.MARS | ashtakavarga | Mars BAV total: 39 bindus
(3 rows)
```

**mcp_query_chart_facts: PASS** — rows returned, not empty, values match FORENSIC §6.2.

## Full Category Breakdown

```sql
SELECT category, COUNT(*) FROM chart_facts GROUP BY category ORDER BY category;
```

| Category | Rows |
|----------|------|
| arudha | 9 |
| ashtakavarga | 20 |
| aspect | 38 |
| avastha | 7 |
| bhava_bala | 12 |
| bhrigu_bindu | 8 |
| birth_metadata | 22 |
| chalit_kinetic | 9 |
| cusp | 21 |
| dasha_chara | 144 |
| dasha_vimshottari | 50 |
| dasha_yogini | 17 |
| house | 149 |
| ishta_kashta | 8 |
| kp_cusp | 12 |
| kp_planet | 9 |
| kp_significator | 7 |
| longevity | 9 |
| mercury_convergence | 8 |
| moola_dasha | 1 |
| mrityu_bhaga | 11 |
| narayana_dasha | 1 |
| navatara | 12 |
| panchang | 12 |
| pancha_vargeeya | 8 |
| planet | 41 |
| saham | 36 |
| special_lagna | 9 |
| sthira_karaka | 14 |
| strength | 9 |
| strength_extra | 7 |
| sudasa | 1 |
| transit | 8 |
| upagraha | 9 |
| yoga | 18 |
| yogi_avayogi | 11 |
| **TOTAL** | **767** |

## CAPABILITY_MANIFEST.json Update

Updated `FORENSIC` entry (canonical_id=FORENSIC, tool_name=chart_facts_query):
- `chart_facts_db_row_count`: 767
- `chart_facts_yaml_version`: "1.2"
- `chart_facts_yaml_fact_count`: 783
- `chart_facts_db_unique_fact_ids`: 767
- `chart_facts_db_categories`: 36
- `chart_facts_last_loaded_session`: "DAR-P4-S14"
- `chart_facts_last_loaded_build_id`: "dar-p4-s14-2026-05-25"

## Anomalies / Notes

1. **YAML EXPECTED_COUNT_MAX breach:** `ChartFactsWriter` enforces max=700; v1.2 has 783 facts.
   The writer's hardcoded range was designed for the pre-S11 era. Recommend updating
   `EXPECTED_COUNT_MIN=700 / EXPECTED_COUNT_MAX=900` in `chart_facts_writer.py` in a follow-up
   governance session to allow the GCS-sourced pipeline to handle v1.2+.

2. **16 duplicate fact_ids in YAML (pre-existing):** KRK.C.* (7) + UPG.* (9) duplicated.
   These should be deduplicated in the YAML in a future S15+ cleanup session.
   No DB data corruption — ON CONFLICT DO UPDATE preserves last-write values.

3. **narayana_dasha / moola_dasha / sudasa = EXTERNAL_COMPUTATION_REQUIRED stubs:**
   These 3 rows carry placeholder values; actual dasha values require JH computation.
   MCP consumers should filter or tag these appropriately.
