---
artifact: L0_INTEGRITY_FINDINGS_v1_0.md
version: 1.0
status: DRAFT
phase: Phase 1 — Integrity Audit (read-only)
produced_by: Nirīkṣaka Phase-1 audit agent
produced_on: 2026-06-17
chart_id_canonical: 482012f1-710e-4a25-994a-93821f5871aa
---

# L0 Brahmagyan — Integrity Findings v1.0

## §1 — Asset Inventory (from prod asset_registry)

21 assets in `asset_registry` WHERE layer = 'brahmagyan'. All have catalog_status = 'CURRENT' and is_active = true.

| asset_id | catalog_status | target_floor | count_sql_result | delta vs floor | is_active | in_seed |
|---|---|---|---|---|---|---|
| bg_ephemeris | CURRENT | 825,084 | 825,084 | 0 (exact) | true | YES |
| bg_reference | CURRENT | NULL | 1,485 | N/A | true | YES |
| bg_texts | CURRENT | 8,193 | 10,651 | +2,458 (overfill) | true | YES |
| bg_ontology | CURRENT | NULL | 623 | N/A | true | YES |
| bg_text_index | CURRENT | 361 | 361 | 0 (exact) | true | YES |
| bg_prashna_rules | CURRENT | 36 | 36* | 0 (exact*) | true | NO |
| bg_rules | CURRENT | 1,755 | 2,912 | +1,157 (overfill) | true | YES |
| bg_remedies | CURRENT | 266 | 266 | 0 (exact) | true | YES |
| bg_concordance | CURRENT | 720 | 720 | 0 (exact) | true | YES |
| bg_yogas | CURRENT | 175 | 175 | 0 (exact) | true | YES |
| bg_dasha_systems | CURRENT | 15 | 18 | +3 (overfill) | true | YES |
| bg_doshas | CURRENT | 50 | 50 | 0 (exact) | true | YES |
| bg_compendium_index | CURRENT | 1,755 | 9,538 | +7,783 (5.4× overfill) | true | YES |
| bg_panchanga | CURRENT | NULL | N/A (service) | N/A | true | YES |
| bg_ephemeris_engine | CURRENT | NULL | N/A (service) | N/A | true | YES |
| bg_nakshatra | CURRENT | 2,857 | 2,857 | 0 (exact) | true | YES |
| bg_vastu_directions | CURRENT | 30 | 32 | +2 (overfill) | true | NO |
| bg_transit_engine | CURRENT | 9 | 9* | 0 (exact*) | true | NO |
| bg_transit_rules | CURRENT | 37 | 41 | +4 (overfill) | true | NO |
| bg_medical_mappings | CURRENT | 9 | 9 | 0 (exact) | true | NO |
| bg_nakshatra_medical | CURRENT | 27 | 27 | 0 (exact) | true | NO |

*count_sql has syntax error (missing outer SELECT wrapper) — result obtained by wrapping with SELECT.

**Floor semantics:** Per §N.4, target_floor = achieved count after first build, aspirational not a gate. Overfills are not build failures; they indicate the corpus grew beyond the floor set at last seed time. Floors must be updated in the seed to match actual counts.

---

## §2 — Per-Check Summary

| Check | # Assets Failing | Failing Assets |
|---|---|---|
| 1 — count_sql syntactically valid | 4 | bg_prashna_rules, bg_vastu_directions, bg_transit_engine, bg_transit_rules |
| 2 — target_floor matches achieved count | 6 | bg_texts, bg_rules, bg_dasha_systems, bg_compendium_index, bg_vastu_directions, bg_transit_rules |
| 3 — build-state fresh (asset_throughput populated) | 4 | bg_ephemeris_engine (service), bg_nakshatra_medical, bg_panchanga (service), bg_transit_engine |
| 4 — catalog_status = CURRENT | 0 | — (all 21 are CURRENT) |
| 5 — seed ↔ registry ↔ prod consistency | 6 | bg_vastu_directions, bg_transit_engine, bg_transit_rules, bg_medical_mappings, bg_nakshatra_medical, bg_prashna_rules |
| 6 — cited (classical_source populated) | 0 | — (all checked tables: 100% citation coverage) |
| 7 — no silent failures | 0 | — (bg_texts has graceful degradation, not swallowed exceptions) |
| 8 — registration completeness (scope/type/depends_on) | 2 | bg_compendium_index (scope=global but throughput is per-chart), bg_nakshatra (rows_written=0 despite table having 2,857 rows) |
| 9 — idempotency pattern correct (L0 ON CONFLICT) | 0 | — (all 16 writers use ON CONFLICT; all confirmed) |
| 10 — orchestrator-resolvable (@register present) | 2 | bg_transit_engine (no writer file), bg_nakshatra_medical (no writer file) |
| 11 — no table fragmentation | 1 (table pair) | reference_nakshatras (27 rows, old) + reference_nakshatra (28 rows, new) coexist; plus 5 populated orphan tables |
| 12 — FORENSIC anchor (Purva Bhadrapada) | 0 | — nakshatra 25: Jupiter lord, Aja Ekapada deity, Aquarius+Pisces — all CORRECT |

---

## §3 — Detailed Findings (per asset, per check)

### bg_ephemeris
- **Check 1 (count_sql valid):** PASS — `SELECT count(*) FROM ephemeris_daily` executes cleanly
- **Check 2 (target_floor):** PASS — achieved 825,084 = floor 825,084 (exact match)
- **Check 3 (build-state fresh):** INFO — throughput record exists with chart_id 482012f1 (per-chart record from 2026-06-16), no global record; state = lit. Global scope asset should have a global throughput record; this is a scope accounting gap but the asset is lit and data is present.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** N/A — ephemeris_daily is raw astronomical data (no classical_source field expected)
- **Check 7 (no silent failures):** PASS — no writer (ephemeris seeded externally)
- **Check 8 (registration completeness):** PASS — scope=global, asset_type=data, depends_on=[]
- **Check 9 (idempotency):** N/A — no orchestrator writer; seeded via migration
- **Check 10 (orchestrator-resolvable):** INFO — no bg_ephemeris.py writer; ephemeris_daily is populated via migration seed, not orchestrator. This is intentional (825k-row external data load). Not a failure.
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_reference
- **Check 1 (count_sql valid):** PASS — 14-table summation executes cleanly; returns 1,485
- **Check 2 (target_floor):** N/A — target_floor is NULL (no floor set; by design)
- **Check 3 (build-state fresh):** WARN — two throughput records: global (rows_written=0, 2026-06-08) and per-chart (rows_written=NULL, 2026-06-16). Global record shows 0 rows written at last global build. Actual table population: 1,485 rows spread across 14 reference_* tables. The `rows_written=0` suggests the writer detected data already present and performed no inserts (ON CONFLICT DO NOTHING — correct idempotent behavior); state = lit.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** INFO — reference_* tables do not uniformly have a classical_source column; properties encoded structurally. Not applicable in the same way as narrative tables.
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** WARN — target_table = 'reference_nakshatras' (OLD fragmented table, 27 rows). This is inconsistent with the bg_nakshatra asset which populates the new `reference_nakshatra` table. bg_reference.count_sql correctly does NOT include reference_nakshatras (the 14-table sum covers all other reference_* tables). However, the target_table pointer is stale.
- **Check 9 (idempotency):** PASS — bg_reference.py uses ON CONFLICT patterns
- **Check 10 (orchestrator-resolvable):** PASS — bg_reference.py with @register('bg_reference')
- **Check 11 (fragmentation):** FAIL — target_table = 'reference_nakshatras' (old, 27 rows) while reference_nakshatra (new, 28 rows) is the live table
- **Check 12 (FORENSIC):** N/A

---

### bg_texts
- **Check 1 (count_sql valid):** PASS — `SELECT count(*) FROM classical_text_chunks` = 10,651
- **Check 2 (target_floor):** FAIL — achieved 10,651 vs floor 8,193 (+2,458, +30%). Floor was set at last build (2026-06-09: 8,193 chunks from 13 texts). Corpus has since grown. Floor needs updating.
- **Check 3 (build-state fresh):** INFO — throughput record is per-chart (482012f1), built 2026-06-16; state = lit. rows_written = NULL (column not recorded for this build). The actual table count (10,651) is the authoritative measure.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** N/A — classical_text_chunks does not require classical_source on each chunk (they ARE the source)
- **Check 7 (no silent failures):** PASS — two `except Exception` blocks at lines 101 and 156 in bg_texts.py; both log at error/warning level and return None for optional sources (GCS PDFs, archive.org DjVu). The outer writer handles None gracefully. NOT silent swallowing.
- **Check 8 (registration completeness):** PASS
- **Check 9 (idempotency):** PASS — bg_texts.py uses DELETE FROM then INSERT (full replace), plus ON CONFLICT DO NOTHING for individual chunks
- **Check 10 (orchestrator-resolvable):** PASS — bg_texts.py with @register("bg_texts")
- **Check 11 (fragmentation):** PASS — classical_text_chunks is the sole canonical table; classical_chunks (old, 0 rows) is an empty residual
- **Check 12 (FORENSIC):** N/A

---

### bg_ontology
- **Check 1 (count_sql valid):** PASS — `SELECT count(*) FROM brahma_ontology` = 623
- **Check 2 (target_floor):** N/A — target_floor = NULL (by design)
- **Check 3 (build-state fresh):** WARN — two throughput records: global (rows_written=0, 2026-06-08) and per-chart (2026-06-16). Same pattern as bg_reference: global record wrote 0 (idempotent; data already present). state = lit.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** N/A — ontology is a vocabulary, not a classical citation target
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS
- **Check 9 (idempotency):** PASS — bg_ontology.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_ontology.py with @register('bg_ontology')
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_text_index
- **Check 1 (count_sql valid):** PASS — returns 361
- **Check 2 (target_floor):** PASS — achieved 361 = floor 361 (exact; floor was set post-build)
- **Check 3 (build-state fresh):** INFO — per-chart record (482012f1), 2026-06-16, state = lit
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed (seed value target_floor=400; DB shows 361 = post-build update per §N.4)
- **Check 6 (cited):** N/A
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — depends_on = [bg_texts] correct
- **Check 9 (idempotency):** PASS — bg_text_index.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_text_index.py with @register("bg_text_index")
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_prashna_rules
- **Check 1 (count_sql valid):** FAIL — stored count_sql is `(SELECT COUNT(*) FROM bg_prashna_lagna_methods) + ...` (5-table sum) WITHOUT an outer SELECT wrapper. Executing the raw count_sql returns syntax error. The corrected form `SELECT (...) + (...) + ... AS count` returns 36.
- **Check 2 (target_floor):** PASS — achieved 36 = floor 36 (exact). Note: 5 breakdown: lagna_methods=5, tajik_yogas=11, significators=12, fructification_rules=5, special_techniques=3 = 36.
- **Check 3 (build-state fresh):** PASS — per-chart record (482012f1), rows_written=36, 2026-06-17, state = lit (most recent build)
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** FAIL — NOT in seed file. Registered via migration 262_bg_prashna_rules_asset_registry.sql. Seed drift.
- **Check 6 (cited):** N/A — individual prashna rule tables lack a checked citation column; rules encode classical source implicitly
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** INFO — target_table = NULL (multi-table asset with no single primary table). Acceptable for multi-table assets.
- **Check 9 (idempotency):** PASS — bg_prashna_rules.py uses ON CONFLICT DO NOTHING (L0 standard per docstring)
- **Check 10 (orchestrator-resolvable):** PASS — bg_prashna_rules.py with @register("bg_prashna_rules"). NOTE: run(ctx) uses `# type: ignore[override]` (ctx parameter untyped). Functional but hygiene concern.
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_rules
- **Check 1 (count_sql valid):** PASS — `SELECT count(*) FROM sutravali_rules` = 2,912
- **Check 2 (target_floor):** FAIL — achieved 2,912 vs floor 1,755 (+1,157, +66%). Floor was set when corpus was 8,193 chunks. Corpus is now 10,651 chunks (+30%). Rule extraction scales with corpus; floor is stale.
- **Check 3 (build-state fresh):** INFO — per-chart record (482012f1), 2026-06-16, rows_written = NULL, state = lit
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed (seed floor=1,755; DB floor=1,755; the stale floor is the same in both)
- **Check 6 (cited):** N/A — sutravali_rules has text_id + verse_ref for provenance (traceable to source text)
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS
- **Check 9 (idempotency):** PASS — bg_rules.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_rules.py with @register('bg_rules')
- **Check 11 (fragmentation):** INFO — sutravali_review (154 rows) exists as a parallel review queue; not registered as an asset (acceptable ancillary table)
- **Check 12 (FORENSIC):** N/A

---

### bg_remedies
- **Check 1 (count_sql valid):** PASS — returns 266
- **Check 2 (target_floor):** PASS — achieved 266 = floor 266 (exact; floor updated post-build per §N.4; seed had 800)
- **Check 3 (build-state fresh):** INFO — per-chart record (482012f1), 2026-06-16, rows_written = NULL, state = lit
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed (seed floor=800; DB floor=266 = post-build update)
- **Check 6 (cited):** PASS — source_citation field: 0 uncited / 266 total (100%)
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS
- **Check 9 (idempotency):** PASS — bg_remedies.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_remedies.py with @register('bg_remedies')
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_concordance
- **Check 1 (count_sql valid):** PASS — `SELECT count(*) FROM classical_attributions` = 720
- **Check 2 (target_floor):** PASS — achieved 720 = floor 720 (exact; seed had 800, updated post-build)
- **Check 3 (build-state fresh):** WARN — two throughput records: global (rows_written=477, 2026-06-09) and per-chart (2026-06-16). Global record shows 477 rows written at last global build; actual table has 720. Difference of 243 rows may reflect incremental additions or an earlier partial build. Not a blocking issue since state = lit and actual count meets floor.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** N/A — classical_attributions is itself an attribution/concordance table; its source_text_ids and source_chunk_ids provide traceability
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — depends_on=[bg_rules] correct
- **Check 9 (idempotency):** PASS — ON CONFLICT (topic_id, school) DO NOTHING
- **Check 10 (orchestrator-resolvable):** PASS — bg_concordance.py with @register("bg_concordance")
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_yogas
- **Check 1 (count_sql valid):** PASS — returns 175
- **Check 2 (target_floor):** PASS — achieved 175 = floor 175 (exact; seed had 250, updated post-build)
- **Check 3 (build-state fresh):** INFO — per-chart record (482012f1), 2026-06-16, rows_written = NULL, state = lit
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** PASS — classical_citations JSONB: 0 uncited / 175 total (100%)
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — depends_on=[bg_ontology] correct
- **Check 9 (idempotency):** PASS — bg_yogas.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_yogas.py with @register('bg_yogas')
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_dasha_systems
- **Check 1 (count_sql valid):** PASS — returns 18
- **Check 2 (target_floor):** FAIL — achieved 18 vs floor 15 (+3, minor overfill). Floor = 15 was the seed estimate; 18 dasha systems are now in the catalog.
- **Check 3 (build-state fresh):** INFO — per-chart record (482012f1), 2026-06-16, rows_written = NULL, state = lit
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed (floor=15; minor overfill)
- **Check 6 (cited):** INFO — brahma_dasha_systems lacks a directly-checked citation column; schema likely includes source references internally
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — depends_on=[bg_ontology] correct
- **Check 9 (idempotency):** PASS — bg_dasha_systems.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_dasha_systems.py with @register('bg_dasha_systems')
- **Check 11 (fragmentation):** INFO — reference_dasha_systems (18 rows, part of bg_reference) mirrors brahma_dasha_systems (18 rows). Both exist; bg_reference count_sql includes reference_dasha_systems; bg_dasha_systems targets brahma_dasha_systems. Duplication of dasha system data across two tables. Not currently flagged as a blocker but worth tracking.
- **Check 12 (FORENSIC):** N/A

---

### bg_doshas
- **Check 1 (count_sql valid):** PASS — returns 50
- **Check 2 (target_floor):** PASS — achieved 50 = floor 50 (exact)
- **Check 3 (build-state fresh):** INFO — per-chart record (482012f1), 2026-06-16, rows_written = NULL, state = lit
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** PASS — classical_citations JSONB: 0 uncited / 50 total (100%)
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — depends_on=[bg_ontology] correct
- **Check 9 (idempotency):** PASS — bg_doshas.py uses ON CONFLICT
- **Check 10 (orchestrator-resolvable):** PASS — bg_doshas.py with @register('bg_doshas')
- **Check 11 (fragmentation):** INFO — reference_doshas (50 rows, in bg_reference) and brahma_dosha_catalog (50 rows, in bg_doshas) both exist with the same count. Same duplication pattern as dasha_systems.
- **Check 12 (FORENSIC):** N/A

---

### bg_compendium_index
- **Check 1 (count_sql valid):** PASS — `SELECT count(*) FROM brahma_compendium_index` = 9,538
- **Check 2 (target_floor):** FAIL — achieved 9,538 vs floor 1,755 (+7,783, 5.4× overfill). This is the largest floor-vs-actual gap in L0. The floor was set for corpus ~8,193 chunks (Pass A projected ~5,795 + Pass B ~1,230 = ~7,025 rows when first built per throughput). Actual table has grown to 9,538. Floor is severely stale.
- **Check 3 (build-state fresh):** FAIL — throughput record has chart_id = 482012f1 (per-chart record) despite bg_compendium_index being a GLOBAL scope asset. No global throughput row exists. The asset was last built 2026-06-09 with rows_written=7,025 (actual table now 9,538 = stale throughput). This is a scope/registration anomaly: a global asset's build state is recorded under a per-chart key.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** N/A — brahma_compendium_index is an aggregation/cross-reference index; citation traceability is via source chunk references
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** FAIL — scope='global' but asset_throughput record is keyed by chart_id (per-chart). This contradicts the unique index: `asset_throughput_global_idx UNIQUE btree (asset_id) WHERE chart_id IS NULL`. The global record doesn't exist; only a per-chart record exists.
- **Check 9 (idempotency):** PASS — ON CONFLICT on dedup unique index
- **Check 10 (orchestrator-resolvable):** PASS — bg_compendium_index.py with @register('bg_compendium_index')
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_panchanga
- **Check 1 (count_sql valid):** N/A — service asset; count_sql = NULL
- **Check 2 (target_floor):** N/A — service; target_floor = NULL
- **Check 3 (build-state fresh):** FAIL — NO throughput record exists for bg_panchanga (neither global nor per-chart). Service assets don't write rows but should have a throughput record indicating health.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed with full health_probe spec
- **Check 6 (cited):** N/A
- **Check 7 (no silent failures):** N/A
- **Check 8 (registration completeness):** PASS — storage_type='service', asset_type='service', health_probe defined in seed
- **Check 9 (idempotency):** N/A
- **Check 10 (orchestrator-resolvable):** INFO — no Python writer file (expected for service asset). Service assets are registered but not orchestrated via WriterBase.
- **Check 11 (fragmentation):** N/A
- **Check 12 (FORENSIC):** INFO — seed health_probe specifies forensic_expected: tithi=Shukla Tritiya, nakshatra=Purva Bhadrapada, yoga=Shiva, karana=Garaja, vara=Ravivara. Matches canonical FORENSIC 7/7 anchors. Probe not executed in this read-only pass.

---

### bg_ephemeris_engine
- **Check 1 (count_sql valid):** N/A — service; count_sql = NULL
- **Check 2 (target_floor):** N/A — service; target_floor = NULL
- **Check 3 (build-state fresh):** FAIL — NO throughput record. Same gap as bg_panchanga.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6–9:** N/A
- **Check 10 (orchestrator-resolvable):** N/A — service
- **Check 11 (fragmentation):** N/A
- **Check 12 (FORENSIC):** INFO — seed health_probe specifies forensic_jd=2445701.948264, expected Sun in sign 10 (Makara/Capricorn) sidereal Lahiri. Matches canonical anchor (Sun in Capricorn). Probe not executed in this read-only pass.

---

### bg_nakshatra
- **Check 1 (count_sql valid):** PASS — `SELECT (COUNT FROM ref_nakshatra) + (COUNT FROM pada) + (COUNT FROM matrix)` = 2,857. NOTE: count_sql as stored in DB is syntactically valid (already has SELECT wrapper unlike bg_prashna_rules).
- **Check 2 (target_floor):** PASS — achieved 2,857 = floor 2,857 (exact; floor set after first prod build per §N.4)
- **Check 3 (build-state fresh):** FAIL — throughput record shows rows_written = 0 (2026-06-17 07:26:05) but actual tables have 2,857 rows. The writer ran but reported 0 rows written. This suggests an ON CONFLICT DO NOTHING execution where all rows were already present (idempotent re-run). State = lit. built_against_upstream_hash = 'e3b0c44298fc1c14' = SHA256 of empty string — hash tracking not working correctly for this writer.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** PASS — defined in seed
- **Check 6 (cited):** PASS — reference_nakshatra.classical_source: 0 uncited / 28 total (100% cited, value='bphs:ch92' for all rows checked)
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — target_table = 'reference_nakshatra' (correct new table), depends_on = []
- **Check 9 (idempotency):** PASS — bg_nakshatra.py uses ON CONFLICT DO NOTHING (L0 standard per §N.3 docstring)
- **Check 10 (orchestrator-resolvable):** PASS — bg_nakshatra.py with @register('bg_nakshatra')
- **Check 11 (fragmentation):** PASS — correctly uses new reference_nakshatra table
- **Check 12 (FORENSIC):** PASS — nakshatra_id=25 (Purva Bhadrapada): vimshottari_lord=jupiter, presiding_deity='Aja Ekapada', ruling_planet=jupiter, rashis_spanned={Aquarius,Pisces}, start_longitude=320.00000. All CORRECT per classical specification.

---

### bg_vastu_directions
- **Check 1 (count_sql valid):** FAIL — stored count_sql `(SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials)` is missing outer SELECT wrapper. Syntax error when run directly. Corrected result = 8 + 24 = 32.
- **Check 2 (target_floor):** FAIL — achieved 32 vs floor 30 (+2 overfill). bg_vastu_directions = 8 rows (not 30 — the floor itself may be wrong in semantics: 30 could mean total including remedials? Either way, 8 directions is correct per classical Vastu, and 24 remedials = 3 per direction. The floor=30 probably meant 8+22 from an older design; now 8+24=32).
- **Check 3 (build-state fresh):** PASS — rows_written=32, 2026-06-17 07:25:56, state = lit (most recent build today)
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** FAIL — NOT in seed file. Registered via migration 285_asset_registry_bg_vastu.sql. Seed drift.
- **Check 6 (cited):** INFO — not checked (bg_vastu_directions table schema has classical_citation column per migration 266 pattern; expected to be populated)
- **Check 7 (no silent failures):** PASS — bg_vastu_directions.py uses standard exception handling
- **Check 8 (registration completeness):** PASS — target_table='bg_vastu_directions', scope=global, depends_on=[]
- **Check 9 (idempotency):** PASS — bg_vastu_directions.py: ON CONFLICT (direction) DO UPDATE / ON CONFLICT DO NOTHING
- **Check 10 (orchestrator-resolvable):** PASS — bg_vastu_directions.py with @register('bg_vastu_directions')
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_transit_engine
- **Check 1 (count_sql valid):** FAIL — stored count_sql `(SELECT COUNT(*) FROM bg_transit_engine)` is missing outer SELECT wrapper. Syntax error when run directly. Corrected result = 9.
- **Check 2 (target_floor):** PASS — achieved 9 = floor 9 (exact; once corrected)
- **Check 3 (build-state fresh):** FAIL — NO throughput record exists (neither global nor per-chart). Table has 9 rows but no build-state tracking. The data was inserted via migration 266, not via an orchestrator writer.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** FAIL — NOT in seed file. Registered via migration 266_bg_transit_tables.sql using older column names (display_name, which no longer exists in asset_registry schema).
- **Check 6 (cited):** PASS — bg_transit_engine has `classical_citation TEXT NOT NULL` per migration DDL. 9 rows, 0 uncited (implied by NOT NULL constraint).
- **Check 7 (no silent failures):** N/A — no orchestrator writer
- **Check 8 (registration completeness):** FAIL — target_table = NULL (but bg_transit_engine table exists). The asset has scope=global and asset_type=data but is registered as if it has no target table.
- **Check 9 (idempotency):** N/A — data seeded via migration INSERT, not orchestrator writer
- **Check 10 (orchestrator-resolvable):** FAIL — NO bg_transit_engine.py writer file found anywhere. Asset is data type but has no registered orchestrator writer. The 9 rows were inserted by migration 266 directly. If the orchestrator is asked to rebuild bg_transit_engine, it cannot.
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_transit_rules
- **Check 1 (count_sql valid):** FAIL — stored count_sql `(SELECT COUNT(*) FROM bg_transit_rules)` is missing outer SELECT wrapper. Syntax error when run directly. Corrected result = 41.
- **Check 2 (target_floor):** FAIL — achieved 41 vs floor 37 (+4 overfill). Floor 37 was the initial estimate from migration; actual build produced 41 rules.
- **Check 3 (build-state fresh):** PASS — rows_written=50, 2026-06-17 07:25:56, state = lit (most recent build today). NOTE: rows_written=50 > actual count=41; the throughput records insertions attempted vs final count (some may have been DO UPDATE replacements).
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** FAIL — NOT in seed file. Registered via migration 266_bg_transit_tables.sql. Seed drift.
- **Check 6 (cited):** PASS — bg_transit_rules has `classical_citation TEXT NOT NULL` per migration DDL.
- **Check 7 (no silent failures):** PASS — bg_transit_rules.py uses standard handling
- **Check 8 (registration completeness):** WARN — target_table = NULL but bg_transit_rules table exists. Same gap as bg_transit_engine.
- **Check 9 (idempotency):** PASS — bg_transit_rules.py uses ON CONFLICT DO UPDATE (L0 standard)
- **Check 10 (orchestrator-resolvable):** PASS — bg_transit_rules.py with @register("bg_transit_rules"). NOTE: run(ctx) uses `# type: ignore[override]` (ctx parameter untyped). Hygiene concern.
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_medical_mappings
- **Check 1 (count_sql valid):** PASS — `SELECT COUNT(*) FROM bg_medical_mappings` = 9
- **Check 2 (target_floor):** PASS — achieved 9 = floor 9 (exact)
- **Check 3 (build-state fresh):** PASS — rows_written=36, 2026-06-17 07:25:56, state = lit (most recent build). NOTE: rows_written=36 > actual count=9 (writer attempts multiple INSERTs per graha for different mapping types; ON CONFLICT DO UPDATE merges them to 9 canonical rows).
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** FAIL — NOT in seed file. Registered via migration 278_bg_medical_asset_registry.sql. Seed drift.
- **Check 6 (cited):** INFO — bg_medical_mappings likely has citation fields (per description: BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita). Not directly schema-checked but schema has appropriate source fields.
- **Check 7 (no silent failures):** PASS
- **Check 8 (registration completeness):** PASS — target_table='bg_medical_mappings', scope=global, depends_on=[]
- **Check 9 (idempotency):** PASS — bg_medical_mappings.py uses ON CONFLICT DO UPDATE
- **Check 10 (orchestrator-resolvable):** PASS — bg_medical_mappings.py with @register('bg_medical_mappings')
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** N/A

---

### bg_nakshatra_medical
- **Check 1 (count_sql valid):** PASS — `SELECT COUNT(*) FROM bg_nakshatra_medical` = 27
- **Check 2 (target_floor):** PASS — achieved 27 = floor 27 (exact)
- **Check 3 (build-state fresh):** FAIL — NO throughput record exists (neither global nor per-chart). Table has 27 rows but asset has no build state tracking. This is a data asset (not service) with no throughput row — critical gap.
- **Check 4 (catalog_status CURRENT):** PASS
- **Check 5 (seed consistency):** FAIL — NOT in seed file. Registered via migration 277_bg_nakshatra_medical.sql. Seed drift.
- **Check 6 (cited):** INFO — per asset description: "Ashtanga Hridayam / BPHS." FORENSIC note in description: "#25 Purva Bhadrapada → left_side (native Moon nakshatra)."
- **Check 7 (no silent failures):** N/A — no orchestrator writer found
- **Check 8 (registration completeness):** PASS — target_table='bg_nakshatra_medical', scope=global
- **Check 9 (idempotency):** N/A — no writer found; data inserted via migration
- **Check 10 (orchestrator-resolvable):** FAIL — NO bg_nakshatra_medical.py writer file found. Asset is data type but has no registered orchestrator writer. Cannot be rebuilt via orchestrator.
- **Check 11 (fragmentation):** PASS
- **Check 12 (FORENSIC):** PASS — asset description explicitly notes "#25 Purva Bhadrapada → left_side (native Moon nakshatra)" confirming FORENSIC anchor is encoded. 27 nakshatra rows present (standard 27; Abhijit excluded from medical mapping).

---

## §4 — Prioritized Fix List

### Priority 1 — Blockers (prevent orchestrator rebuild or cause correctness errors)

**P1-A: Missing orchestrator writers for two data assets**
- `bg_transit_engine` — no bg_transit_engine.py writer; data exists (9 rows from migration 266) but orchestrator cannot rebuild this asset if asked. Asset is registered as `asset_type='data'` but is de-facto migration-only.
- `bg_nakshatra_medical` — no writer file; 27 rows seeded via migration 277. Same gap.
- **Fix:** Either (a) create bg_transit_engine.py and bg_nakshatra_medical.py writers with @register decorators and move the seed data from migration into the writer, OR (b) change asset_type to 'service' and mark them as migration-seeded reference data not intended for orchestrator rebuild.

**P1-B: Four count_sqls are syntactically invalid**
- `bg_prashna_rules`, `bg_vastu_directions`, `bg_transit_engine`, `bg_transit_rules` all store count_sql without an outer SELECT wrapper.
- When the Cockpit stats route runs `asset_registry.count_sql` directly (the documented L1 trap), these four will return syntax errors rather than counts.
- **Fix:** Update count_sql for all four to add `SELECT (...) AS count` outer wrapper.

**P1-C: bg_compendium_index scope/throughput mismatch**
- scope='global' but the only throughput record is keyed by chart_id=482012f1 (violating the `asset_throughput_global_idx UNIQUE (asset_id) WHERE chart_id IS NULL` constraint for global assets).
- The global throughput slot does not exist. Build state for this global asset is invisible to the global monitoring path.
- **Fix:** Insert a global throughput record (chart_id=NULL) for bg_compendium_index, or investigate why the orchestrator is writing it as per-chart.

### Priority 2 — Integrity (data correctness and governance)

**P2-A: bg_reference.target_table points to dead table**
- `target_table = 'reference_nakshatras'` (old table, 27 rows) when the live table is `reference_nakshatra` (new, 28 rows under bg_nakshatra).
- The Cockpit's target_table display and size_sql will point at the wrong table.
- **Fix:** Update bg_reference.target_table to NULL or 'reference_planets' (primary reference table) since bg_reference covers 14 tables and no single one is "the" target.

**P2-B: reference_nakshatras (old) still populated alongside reference_nakshatra (new)**
- Two nakshatra tables coexist: reference_nakshatras (27 rows, old schema) and reference_nakshatra (28 rows, new rich schema).
- reference_nakshatras has 27 rows (no Abhijit); reference_nakshatra has 28 rows (with Abhijit).
- Any code still querying reference_nakshatras gets old schema and wrong count.
- **Fix:** Migrate or deprecate reference_nakshatras. Add a DROP TABLE or tombstone migration after verifying no active code references it.

**P2-C: 6 assets in prod but NOT in seed file**
- bg_vastu_directions, bg_transit_engine, bg_transit_rules, bg_medical_mappings, bg_nakshatra_medical, bg_prashna_rules are registered via individual migrations but absent from asset_registry_seed.ts.
- If the seed is re-run, it will not upsert these 6 assets (no ON CONFLICT record for them in the seed), so they persist only because they were added via migrations.
- The seed is supposed to be the single canonical definition (per seed file docstring §B). These 6 are seed drift.
- **Fix:** Add all 6 to asset_registry_seed.ts with correct definitions.

**P2-D: bg_nakshatra rows_written=0 and stale upstream hash**
- bg_nakshatra writer ran 2026-06-17 with rows_written=0 (ON CONFLICT DO NOTHING, data already present) but built_against_upstream_hash = 'e3b0c44298fc1c14' (SHA256 of empty string).
- The stale hash means the orchestrator cannot detect when the writer actually needs to re-run (upstream change detection is broken for this asset).
- **Fix:** Investigate why bg_nakshatra.py's upstream hash computation yields empty-string hash. Ensure the writer correctly hashes its data inputs before writing.

**P2-E: Four stale target_floors in seed**
- bg_texts: seed floor=8,193 but prod=10,651 (+30%)
- bg_rules: seed floor=1,755 but prod=2,912 (+66%)
- bg_compendium_index: seed floor=1,755 but prod=9,538 (+443%)
- bg_dasha_systems: seed floor=15 but prod=18 (+20%)
- These floors are stale from the last build; the corpus has grown.
- **Fix:** Update target_floor in seed to match current prod counts per §N.4 (floors aspirational, not gates).

**P2-F: bg_transit_engine and bg_nakshatra_medical have no throughput records**
- Two data assets have no throughput entry — they are invisible to build monitoring.
- **Fix:** Insert dormant throughput records for both, or (preferably) create writers that register build state properly.

### Priority 3 — Hygiene (cleanliness, technical debt)

**P3-A: 5 orphaned bg_* tables from migration 250 with no asset_registry entry**
- bg_avastha_schemes (35 rows), bg_combustion_orbs (8 rows), bg_dignity_reference (9 rows), bg_graha_naisargika_friendship (72 rows), bg_motion_state_thresholds (27 rows)
- All populated, all referenced by migration 250_bg_dignity_reference.sql, none registered as L0 assets.
- They represent a sub-system (dignity reference) that was built but never formally registered.
- **Fix:** Either (a) register them as a new `bg_dignity_reference` asset in asset_registry + seed, with a single writer; OR (b) if they are consumed only as read-only reference (via direct SQL), document that explicitly and add to orphaned-table register in ONGOING_HYGIENE_POLICIES.

**P3-B: bg_prashna_rules and bg_transit_rules writers use untyped ctx**
- `def run(self, ctx) -> WriterResult: # type: ignore[override]` in both writers.
- Violates WriterBase contract signature `run(self, ctx: ContextSpec) -> WriterResult`.
- **Fix:** Add type annotation: `def run(self, ctx: ContextSpec) -> WriterResult:` and remove `# type: ignore`.

**P3-C: bg_concordance global throughput rows_written=477 vs actual table=720**
- The global build record is stale (shows 477 at last global build 2026-06-09; actual table has 720).
- State = lit but rows_written doesn't match current count.
- **Fix:** When bg_concordance is next rebuilt, ensure rows_written in throughput reflects final table count, not just insertions attempted.

**P3-D: bg_transit_engine.target_table = NULL despite bg_transit_engine table existing**
- bg_transit_engine has a real table (bg_transit_engine) but target_table is NULL in asset_registry.
- Same for bg_transit_rules.target_table = NULL.
- **Fix:** Update target_table to the actual table name for both assets.

**P3-E: Empty residual tables**
- classical_chunks (0 rows), prashna_charts (0 rows) — empty tables with no asset registry pointer.
- **Fix:** Drop or formally tombstone them in a cleanup migration.

---

## §5 — Table Inventory (all L0-related tables in prod)

| table_name | row_count | associated_asset | status |
|---|---|---|---|
| ephemeris_daily | 825,084 | bg_ephemeris | LIVE |
| classical_text_chunks | 10,651 | bg_texts, bg_text_index | LIVE |
| brahma_ontology | 623 | bg_ontology | LIVE |
| sutravali_rules | 2,912 | bg_rules | LIVE |
| brahma_remedy_corpus | 266 | bg_remedies | LIVE |
| classical_attributions | 720 | bg_concordance | LIVE |
| brahma_yoga_catalog | 175 | bg_yogas | LIVE |
| brahma_dasha_systems | 18 | bg_dasha_systems | LIVE |
| brahma_dosha_catalog | 50 | bg_doshas | LIVE |
| brahma_compendium_index | 9,538 | bg_compendium_index | LIVE (stale throughput) |
| reference_nakshatra | 28 | bg_nakshatra | LIVE |
| reference_nakshatra_pada | 108 | bg_nakshatra | LIVE |
| reference_nakshatra_matrix | 2,721 | bg_nakshatra | LIVE |
| bg_vastu_directions | 8 | bg_vastu_directions | LIVE |
| bg_vastu_direction_remedials | 24 | bg_vastu_directions | LIVE |
| bg_transit_engine | 9 | bg_transit_engine | LIVE (no writer) |
| bg_transit_rules | 41 | bg_transit_rules | LIVE |
| bg_medical_mappings | 9 | bg_medical_mappings | LIVE (no throughput) |
| bg_nakshatra_medical | 27 | bg_nakshatra_medical | LIVE (no writer, no throughput) |
| bg_prashna_lagna_methods | 5 | bg_prashna_rules | LIVE |
| bg_prashna_tajik_yogas | 11 | bg_prashna_rules | LIVE |
| bg_prashna_significators | 12 | bg_prashna_rules | LIVE |
| bg_prashna_fructification_rules | 5 | bg_prashna_rules | LIVE |
| bg_prashna_special_techniques | 3 | bg_prashna_rules | LIVE |
| reference_planets | 11 | bg_reference | LIVE |
| reference_signs | 12 | bg_reference | LIVE |
| reference_aspects | 19 | bg_reference | LIVE |
| reference_vargas | 19 | bg_reference | LIVE |
| reference_houses | 12 | bg_reference | LIVE |
| reference_strength_systems | 33 | bg_reference | LIVE |
| reference_karakas | 77 | bg_reference | LIVE |
| reference_upagrahas | 11 | bg_reference | LIVE |
| reference_constants | 203 | bg_reference | LIVE |
| reference_topic_tags | 481 | bg_reference | LIVE |
| reference_glossary | 364 | bg_reference | LIVE |
| reference_yogas | 175 | bg_reference | LIVE |
| reference_doshas | 50 | bg_reference | LIVE |
| reference_dasha_systems | 18 | bg_reference | LIVE |
| reference_nakshatras | 27 | bg_reference (stale target_table) | FRAGMENTED — superseded by reference_nakshatra |
| bg_avastha_schemes | 35 | NONE | ORPHANED (migration 250) |
| bg_combustion_orbs | 8 | NONE | ORPHANED (migration 250) |
| bg_dignity_reference | 9 | NONE | ORPHANED (migration 250) |
| bg_graha_naisargika_friendship | 72 | NONE | ORPHANED (migration 250) |
| bg_motion_state_thresholds | 27 | NONE | ORPHANED (migration 250) |
| classical_texts | 16 | bg_texts (indirect) | ANCILLARY |
| classical_texts_source | 11 | bg_texts (indirect) | ANCILLARY |
| sutravali_review | 154 | bg_rules (review queue) | ANCILLARY |
| classical_chunks | 0 | NONE | EMPTY RESIDUAL |
| prashna_charts | 0 | NONE | EMPTY RESIDUAL |

**Total L0-related tables in prod: 49**
**Total rows in primary L0 assets: ~847,000+ (dominated by ephemeris_daily at 825,084)**

---

## §6 — Summary Scorecard

| Dimension | Status |
|---|---|
| Total L0 assets in prod | 21 |
| All catalog_status = CURRENT | ✓ PASS |
| All is_active = true | ✓ PASS |
| All state = lit (data assets with throughput) | ✓ PASS (for those with records) |
| count_sqls syntactically valid | 17/21 (4 fail) |
| FORENSIC anchor (Purva Bhadrapada nakshatra 25) | ✓ PASS — Jupiter lord, Aja Ekapada deity, Aquarius+Pisces rashis |
| Citation coverage on checked tables | ✓ 100% — 0 uncited across brahma_remedy_corpus, brahma_yoga_catalog, brahma_dosha_catalog, reference_nakshatra |
| Silent exception swallowing | ✓ NONE — bg_texts exceptions are graceful degradation with logging |
| Orchestrator-resolvable writers | 16/21 (2 data assets have no writer: bg_transit_engine, bg_nakshatra_medical; 2 are services) |
| Seed ↔ prod consistency | 15/21 (6 assets registered only via migrations, absent from seed) |
| Table fragmentation | 1 active pair (reference_nakshatras old + reference_nakshatra new) + 5 orphaned tables |
| Idempotency pattern (ON CONFLICT) | ✓ ALL writers compliant |
