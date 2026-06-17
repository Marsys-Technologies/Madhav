# Phase 2 Fix Log — L0 Brahmagyan Closure Pass
**Date:** 2026-06-17
**Branch:** fix/l0-closure-integrity
**Agent:** Claude Sonnet 4.6 repair agent

---

## Migrations Applied

| Migration | Finding | Description | Result |
|-----------|---------|-------------|--------|
| 295_fix_count_sql_syntax.sql | P1-B BLOCKER | Fix 4 invalid count_sqls (missing SELECT wrapper) | PASS — all 4 count_sqls now valid SQL statements |
| 296_fix_target_floors.sql | P2-E | Update 6 stale target_floors to match actual row counts | PASS — bg_texts=10651, bg_rules=2912, bg_compendium_index=9538, bg_dasha_systems=18, bg_vastu_directions=32, bg_transit_rules=41 |
| 297_fix_bg_reference_target_table.sql | P2-A | Fix bg_reference.target_table stale pointer | PASS — changed from 'reference_nakshatras' to 'reference_planets' |
| 298_register_bg_dignity_reference.sql | P3-A | Register bg_dignity_reference in asset_registry + throughput | PASS — INSERT 0 1 for both registry and throughput |
| 299_fix_compendium_index_throughput.sql | P1-C | Insert missing global throughput for bg_compendium_index | PASS — global record (chart_id IS NULL) inserted, state=lit, rows_written=9538 |
| 300_fix_missing_throughput_records.sql | P2-F + P1-A | Insert dormant throughput for bg_transit_engine and bg_nakshatra_medical | PASS — both inserted, state=lit |
| 301_fix_transit_target_tables.sql | P3-D | Fix NULL target_table for bg_transit_engine and bg_transit_rules | PASS — both set to matching table name |
| 302_deprecate_reference_nakshatras.sql | P2-B | Deprecate reference_nakshatras table | PARTIAL — COMMENT ON TABLE applied; DROP deferred (live writer still inserts) |
| 303_comment_residual_tables.sql | P3-E | Mark classical_chunks and prashna_charts as deprecated/placeholder | PARTIAL — COMMENT ON TABLE applied; DROP deferred (live code queries both) |

---

## Seed File Changes
File: `platform/scripts/seed/asset_registry_seed.ts`

| Asset | Change | Value |
|-------|--------|-------|
| bg_texts | target_floor updated | 8193 → 10651 |
| bg_rules | target_floor updated | 1755 → 2912 |
| bg_compendium_index | target_floor updated | 1755 → 9538 |
| bg_dasha_systems | target_floor updated | 15 → 18 |
| bg_prashna_rules | NEW ENTRY added | sort_order=55, target_floor=36 |
| bg_vastu_directions | NEW ENTRY added | sort_order=56, target_floor=32 |
| bg_transit_engine | NEW ENTRY added | sort_order=61, target_floor=9 |
| bg_transit_rules | NEW ENTRY added | sort_order=62, target_floor=41 |
| bg_medical_mappings | NEW ENTRY added | sort_order=64, target_floor=9 |
| bg_nakshatra_medical | NEW ENTRY added | sort_order=65, target_floor=27 |
| bg_dignity_reference | NEW ENTRY added | sort_order=66, target_floor=151 |

---

## Writer File Changes
File: `platform/python-sidecar/pipeline/orchestrator/writers/bg_prashna_rules.py`
- Added `ContextSpec` to import
- Changed `def run(self, ctx) -> WriterResult:  # type: ignore[override]` → `def run(self, ctx: ContextSpec) -> WriterResult:`

File: `platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py`
- Added `ContextSpec` to import
- Changed `def run(self, ctx) -> WriterResult:  # type: ignore[override]` → `def run(self, ctx: ContextSpec) -> WriterResult:`

---

## Verification Results

| Fix | Status | Notes |
|-----|--------|-------|
| FIX 1 — P1-B count_sql syntax | PASS | All 4 count_sqls execute successfully and return counts |
| FIX 2 — P2-E target_floors | PASS | All 6 target_floors updated in DB; 4 updated in seed file |
| FIX 3 — P2-A bg_reference target_table | PASS | target_table = 'reference_planets' confirmed |
| FIX 4 — P2-C 6 missing seed entries | PASS | All 6 assets added to seed file with correct values from DB |
| FIX 5 — P3-A bg_dignity_reference registration | PASS | asset_registry + asset_throughput records inserted |
| FIX 6 — P1-C bg_compendium_index throughput | PASS | Global throughput record inserted, state=lit, rows_written=9538 |
| FIX 7 — P2-F/P1-A transit/medical throughput | PASS | Both throughput records inserted, state=lit |
| FIX 8 — P3-D transit target_tables | PASS | Both target_tables set to matching table name |
| FIX 9 — P2-B reference_nakshatras | PARTIAL | Deprecation comment applied; DROP deferred (live writer) |
| FIX 10 — P3-B type annotations | PASS | ContextSpec added to both writers; type: ignore removed |
| FIX 11 — P3-E empty residual tables | PARTIAL | Comments applied; DROP deferred (live code queries both) |

---

## Deferred Items
See `phase2_deferred_items.md` for full detail on:
- bg_transit_engine writer (P1-A)
- bg_nakshatra_medical writer (P1-A)
- Drop reference_nakshatras (P2-B) — after bg_reference writer refactor
- Drop classical_chunks and prashna_charts (P3-E) — after live code refactors
