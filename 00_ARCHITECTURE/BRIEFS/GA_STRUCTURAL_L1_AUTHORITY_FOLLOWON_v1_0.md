---
canonical_id: GA_STRUCTURAL_L1_AUTHORITY_FOLLOWON
version: 1.0
status: OPEN
created: 2026-06-19
blocker_for: L2 Bodha (reads vimsopaka totals and nakshatra-relationship categories)
parent_brief: CLAUDECODE_BRIEF_GA_STRUCTURAL_COMPLETENESS_REBUILD_v2_0.md
---

# GA8 L1-Authority Follow-on Gate Items

Two items flagged during GA_STRUCTURAL_REBUILD_VERIFY_v2_0.md (approved, build 5d11969e).
NOT blockers for PR #301 merge. Gate items before L2 reads the relevant categories.

---

## Item 1 — vimsopaka constituent refs: join_key → fact_id

**Category:** `vimsopaka_bala_per_graha` (35 rows/ayanamsha, 175 total in new build)

**Current state:**  
`fact_value_jsonb` stores a logical reference:
```json
{
  "source_table": "chart_divisionals",
  "source_category": "varga_vimsopaka_contribution",
  "join_key": "chart_id=…,ayanamsha_id=…,graha=JUP"
}
```
No resolvable `fact_id` pointer. L1 authority is asserted by join_key, not verifiable via fact_id resolution.

**Required fix before L2 reads vimsopaka totals:**  
Migrate to `fact_value_jsonb.constituent_fact_ids` pointing at the actual `chart_divisionals` row IDs for the 16 varga-vimsopaka-contribution rows that sum to this total. The `chart_divisionals` table's primary key structure needs to be confirmed first (it may not have a UUID `fact_id` — if row IDs are composite keys, document the correct reference pattern instead).

**Scope:** `_build_vimsopaka_ext_rows` in `ga_structural_writer.py`.

---

## Item 2 — silent-drop class not fully closed

**Root cause recap:**  
`chart_facts` has no `constituent_facts_array` column. `_base_row(constituent_facts_array=...)` puts the ref in the Python row dict, but `_CF_INSERT_COLS` excludes it → silently dropped at INSERT. Fixed for `nakshatra_dispositor_chain` (now uses `fact_value_jsonb.constituent_fact_ids`).

**Remaining broken-path callers (both currently produce 0 rows):**

### 2a — `_build_nakshatra_relationship_rows`

Produces: `nakshatra_lord_relationship`, `tara_bala`, `nakshatra_co_tenancy`  
Current row count: **0** (builder called but returns empty)

**Double bug:**
1. Nakshatra name lookup queries `graha_nakshatra_join` for `fact_key = 'nakshatra'` — that key does NOT exist in `graha_nakshatra_join`. Nakshatra names live in `graha_position.nakshatra`. All `data.get("nakshatra", "")` return empty → no rows produced.
2. When fixed, `constituent_facts_array=fids` uses broken _base_row path → needs migration to jsonb.

**Fix sequence:**  
a) Change query to join `graha_position` for nakshatra names (same fix pattern as `_build_nakshatra_dispositor_chain_rows`).  
b) Migrate `constituent_facts_array` refs to `fact_value_jsonb.constituent_fact_ids`.  
c) Rebuild and verify all 3 categories appear with correct row counts.

### 2b — `_build_bhava_chalit_divergence_rows`

Produces: `bhava_chalit_divergence`  
Current row count: **0** (builder called but returns empty)

**Bug:** Unknown — needs investigation. The function exists and is called in `build_ga_structural_substep` (line 5729). May be producing 0 rows because no bhava-chalit divergences exist for this chart, or because an upstream dependency is missing.

**Action:** Investigate why 0 rows, fix if a bug, then migrate `constituent_facts_array` to jsonb if rows are produced.

---

## Audit confirmation

Grep result confirming all `_base_row(constituent_facts_array=...)` call sites:
```
line 5306  _build_nakshatra_relationship_rows  → nakshatra_co_tenancy
line 5325  _build_nakshatra_relationship_rows  → nakshatra_lord_relationship
line 5345  _build_nakshatra_relationship_rows  → tara_bala
line 5517  _build_bhava_chalit_divergence_rows → bhava_chalit_divergence
```

Categories using `value_jsonb` dict directly (NOT the broken path — never silently dropped):
- `yoga_label`: `fact_value_jsonb.constituent_facts_array` ✅
- `dosha_label`: `fact_value_jsonb.constituent_facts_array` ✅

**The silent-drop class is fully enumerated.** No live category in the current build (build 5d11969e, 106,014 rows) has silently-dropped L1 refs. The 4 remaining broken-path calls all produce 0 rows currently.
