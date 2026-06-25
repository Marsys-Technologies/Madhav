---
artifact: LAYER_CLEAR_PARTIAL_DELETE_BRIEF_v1_0.md
canonical_id: LAYER_CLEAR_PARTIAL_DELETE_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Fix the cockpit LAYER CLEAR so it actually deletes ALL of a layer's data. Observed on chart
  Abhinandan Mohanty (1c826d5a-41cb-4450-b4dc-59d440e5f75a): clearing L1 Gaṇita leaves many assets
  still LIVE with row counts (Graha-sthāna 50, Varga 794, Daśākrama 538,707, Balatva 1,330, etc.).
  Root cause is a table-centric clear over a fact_category-partitioned shared-table data model.
audience: Claude Code executor
constraints: prod data plane via proxy :5433; L0 untouched; FROZEN orchestrator contract; main only.
---

# Layer Clear — Partial Delete Bug (L1 Gaṇita assets survive a layer clear)

## §SYMPTOM (confirmed live)
On the Nirmāṇa tracker for chart 1c826d5a, after a LAYER clear of Gaṇita, the layer still shows
17 assets / 540,881 rows and several assets remain LIVE with counts (Graha-sthāna, Varga,
Daśākrama, Balatva…). The clear reports success but deletes only a subset.

## §ROOT CAUSE (confirmed in code: platform/src/app/api/cockpit/clear/execute/route.ts)
The clear is TABLE-CENTRIC but the L1 data model is FACT_CATEGORY-PARTITIONED in shared tables.
1. **Line 104:** `const clearableAssets = scopeAssets.filter(r => r.target_table)` — any asset whose
   `asset_registry.target_table` is NULL is SILENTLY DROPPED from the clear. It is not deleted and
   does NOT appear in `failed_tables`, so the response still looks successful.
2. **Lines 127-128:** delete loop dedupes by `target_table` (`seen.has(asset.target_table)`), then
   **Lines 138-141:** deletes the WHOLE table for the chart (`DELETE FROM <target_table> WHERE
   chart_id=$1`). There is NO `fact_category` (or other natural-key) scoping.
3. **The data reality (from registry seed migrations + writers):** most L1 assets write into the
   SHARED `chart_facts` table, partitioned by `fact_category`:
   - ga_positions  → chart_facts (graha_position / graha_sign_attributes)
   - ga_panchanga  → chart_facts (panchanga_* family)   [chart_panchanga table is EMPTY/legacy]
   - ga_condition  → chart_facts (graha_avastha_*_per_varga) + ga_condition_composite
   - ga_strength, ga_sensitive, ga_structural, ga_nakshatra … → chart_facts categories
   - ga_dashas     → chart_dashas   [ganita_dashas is EMPTY/legacy]
   - ga_vargas     → chart_divisionals
   The writers DELETE with fact_category precision (`replace_prior_chart_facts` deletes
   `WHERE chart_id AND fact_category = ANY(...)`). The CLEAR does not — it has no category model.
   So an asset whose registry target_table is NULL (because its data is a *category within*
   chart_facts, not a table it owns) is skipped; and assets sharing chart_facts are only as
   deleted as the one row that happened to carry `target_table='chart_facts'`.

## §GATE 0 — confirm the exact registry state (operator / prod DB :5433). Do FIRST.
The fix depends on which ga_ assets have NULL vs shared target_table. Run:
```sql
SELECT asset_id, layer, scope, target_table, (count_sql IS NOT NULL) AS has_count
FROM asset_registry WHERE asset_id LIKE 'ga_%' ORDER BY sort_order;
```
Expected pattern to CONFIRM: several ga_ rows with target_table NULL or with target_table=chart_facts
shared across many. Also dump the live row distribution so the fix can be verified against truth:
```sql
SELECT fact_category, count(*) FROM chart_facts
WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a' GROUP BY 1 ORDER BY 2 DESC;
SELECT count(*) FROM chart_dashas      WHERE chart_id='1c826d5a-...';
SELECT count(*) FROM chart_divisionals WHERE chart_id='1c826d5a-...';
```
Report the registry table + the live distribution. This is the ground truth the fix targets.

## §FIX — make the clear delete by the SAME natural key the writers use
The clear must mirror the writers' idempotency model (delete-then-insert scoped to
chart_id × natural-key), not delete whole tables by name. Options, recommend (A):

**(A) Reuse the writers' clear contract (preferred — single source of truth).**
The ga_writers already have `_idempotency.py` with `replace_prior_chart_facts/_dashas/_divisionals`
and `clear_table_for_chart`. The DELETE half of each is the authoritative "how to remove this
asset's data" logic, including the `fact_category = ANY(...)` scoping. Drive the clear from the SAME
per-asset clear definition the writer uses, so clear and rebuild can never disagree. Concretely:
give each asset a declarative clear spec (target_table + optional fact_category filter) in the
registry (or a shared map), and have BOTH the writer idempotency and the clear route read it. NULL
target_table must NOT mean "skip" — it must mean "resolve this asset's category filter on chart_facts".

**(B) Minimal fix if (A) is too large now:** in clear/execute, replace the whole-table delete with
a category-aware delete:
  - For assets whose data is a chart_facts category, DELETE FROM chart_facts WHERE chart_id=$1 AND
    fact_category = ANY($2) using the asset's category list (from the writer/registry).
  - Keep whole-table delete ONLY for assets that genuinely own a dedicated table (chart_dashas,
    chart_divisionals).
  - Remove the silent `filter(r => r.target_table)` skip — an asset with no resolvable clear target
    must surface as a FAILURE in `failed_tables`, never be silently dropped.

**Either way, two non-negotiables:**
1. **No silent skips.** Every scope asset must be either cleared or reported in `failed_tables`.
   The response's `cleared.assets` count must reflect actual deletion, not just "rows we attempted".
2. **The cockpit count after clear must be the TRUTH.** Tie this to the stats route — after a clear,
   the layer's real row count (live count_sql) must drop to 0 for the cleared categories. If the
   tracker still shows old counts, distinguish stale asset_throughput (the known class) from
   genuinely-undeleted rows by checking the live tables, not throughput.

## §VERIFY (Claude Code, without needing the operator to re-run the UI)
- Unit/integration test: a LAYER clear of ganita on a seeded chart deletes ALL ga_ categories from
  chart_facts + chart_dashas + chart_divisionals → live counts go to 0; NO asset silently skipped;
  any unresolved asset appears in failed_tables.
- Regression test: an asset with NULL target_table is NOT dropped — it either clears (via its
  category filter) or is reported failed.
- Cross-check: clear-then-rebuild round-trips cleanly (the clear removes exactly what the writer
  would replace — same natural key).
- Report a before/after row-distribution for chart 1c826d5a proving the cleared categories hit 0.

## §HARD CONSTRAINTS
- L0 (Brahmagyan) untouched — the clear's L0 typed-confirmation guard must remain.
- Prod data plane (:5433). The fix's verification deletes data ONLY on the non-native test chart
  1c826d5a (safe — no downstream native citations). Do NOT run destructive verification on 482012f1.
- FROZEN orchestrator contract — the clear is an API route, not a writer; keep the writer contract
  intact. Prefer making clear READ the writers' clear definition over duplicating delete logic.
- No silent success: the bug was a silent partial delete; the fix's headline property is that it
  can no longer silently skip an asset.
```
