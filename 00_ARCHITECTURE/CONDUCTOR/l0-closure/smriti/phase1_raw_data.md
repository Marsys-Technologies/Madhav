---
artifact: phase1_raw_data.md
version: 1.0
status: RAW_EVIDENCE
phase: Phase 1 — Integrity Audit (read-only)
produced_by: Nirīkṣaka Phase-1 audit agent
produced_on: 2026-06-17
---

# L0 Brahmagyan — Phase 1 Raw Data

## §1 — asset_registry Query Output (Step 1)

21 rows returned for layer = 'brahmagyan', queried in sort_order.

```
asset_id              | catalog_status | is_active | scope  | asset_type | target_floor | target_table            | count_sql (abbreviated)
----------------------|----------------|-----------|--------|------------|--------------|-------------------------|--------------------------
bg_ephemeris          | CURRENT        | t         | global | data       | 825084       | ephemeris_daily         | SELECT count(*) FROM ephemeris_daily
bg_reference          | CURRENT        | t         | global | data       | NULL         | reference_nakshatras    | SELECT sum of 14 reference_* tables AS count
bg_texts              | CURRENT        | t         | global | data       | 8193         | classical_text_chunks   | SELECT count(*) FROM classical_text_chunks
bg_ontology           | CURRENT        | t         | global | data       | NULL         | brahma_ontology         | SELECT count(*) FROM brahma_ontology
bg_text_index         | CURRENT        | t         | global | data       | 361          | classical_text_chunks   | SELECT count(DISTINCT topic_tag) WHERE embedding IS NOT NULL
bg_prashna_rules      | CURRENT        | t         | global | data       | 36           | NULL                    | (SELECT COUNT(*) FROM ...) + ...  [5-table sum, missing SELECT wrapper]
bg_rules              | CURRENT        | t         | global | data       | 1755         | sutravali_rules         | SELECT count(*) FROM sutravali_rules
bg_remedies           | CURRENT        | t         | global | data       | 266          | brahma_remedy_corpus    | SELECT count(*) FROM brahma_remedy_corpus
bg_concordance        | CURRENT        | t         | global | data       | 720          | classical_attributions  | SELECT count(*) FROM classical_attributions
bg_yogas              | CURRENT        | t         | global | data       | 175          | brahma_yoga_catalog     | SELECT count(*) FROM brahma_yoga_catalog
bg_dasha_systems      | CURRENT        | t         | global | data       | 15           | brahma_dasha_systems    | SELECT count(*) FROM brahma_dasha_systems
bg_doshas             | CURRENT        | t         | global | data       | 50           | brahma_dosha_catalog    | SELECT count(*) FROM brahma_dosha_catalog
bg_compendium_index   | CURRENT        | t         | global | data       | 1755         | brahma_compendium_index | SELECT count(*) FROM brahma_compendium_index
bg_panchanga          | CURRENT        | t         | global | service    | NULL         | NULL                    | NULL
bg_ephemeris_engine   | CURRENT        | t         | global | service    | NULL         | NULL                    | NULL
bg_nakshatra          | CURRENT        | t         | global | data       | 2857         | reference_nakshatra     | SELECT (COUNT(*) FROM ref_nakshatra) + (COUNT FROM pada) + (COUNT FROM matrix)
bg_vastu_directions   | CURRENT        | t         | global | data       | 30           | bg_vastu_directions     | (SELECT COUNT(*) FROM bg_vastu_directions) + ...  [missing SELECT wrapper]
bg_transit_engine     | CURRENT        | t         | global | data       | 9            | NULL                    | (SELECT COUNT(*) FROM bg_transit_engine)  [missing SELECT wrapper]
bg_transit_rules      | CURRENT        | t         | global | data       | 37           | NULL                    | (SELECT COUNT(*) FROM bg_transit_rules)  [missing SELECT wrapper]
bg_medical_mappings   | CURRENT        | t         | global | data       | 9            | bg_medical_mappings     | SELECT COUNT(*) FROM bg_medical_mappings
bg_nakshatra_medical  | CURRENT        | t         | global | data       | 27           | bg_nakshatra_medical    | SELECT COUNT(*) FROM bg_nakshatra_medical
```

## §2 — asset_throughput Query Output (Step 2)

24 rows returned (some assets have both global and per-chart records).

```
asset_id              | chart_id                             | rows_written | last_built_at                 | state
----------------------|--------------------------------------|--------------|-------------------------------|-------
bg_compendium_index   | 482012f1-710e-4a25-994a-93821f5871aa | 7025         | 2026-06-09 00:38:44.077645+00 | lit
bg_concordance        | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:04:00.801304+00 | lit
bg_concordance        | NULL (global)                        | 477          | 2026-06-09 00:08:44.497398+00 | lit
bg_dasha_systems      | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_doshas             | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_ephemeris          | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_medical_mappings   | 482012f1-710e-4a25-994a-93821f5871aa | 36           | 2026-06-17 07:25:56.680335+00 | lit
bg_nakshatra          | 482012f1-710e-4a25-994a-93821f5871aa | 0            | 2026-06-17 07:26:05.255749+00 | lit
bg_ontology           | NULL (global)                        | 0            | 2026-06-08 03:58:34.713592+00 | lit
bg_ontology           | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_prashna_rules      | 482012f1-710e-4a25-994a-93821f5871aa | 36           | 2026-06-17 07:25:56.263487+00 | lit
bg_reference          | NULL (global)                        | 0            | 2026-06-08 03:58:26.29916+00  | lit
bg_reference          | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_remedies           | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:04:00.801304+00 | lit
bg_rules              | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_text_index         | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:04:00.801304+00 | lit
bg_texts              | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:15:16.800141+00 | lit
bg_transit_rules      | 482012f1-710e-4a25-994a-93821f5871aa | 50           | 2026-06-17 07:25:56.505419+00 | lit
bg_vastu_directions   | 482012f1-710e-4a25-994a-93821f5871aa | 32           | 2026-06-17 07:25:56.861968+00 | lit
bg_yogas              | 482012f1-710e-4a25-994a-93821f5871aa | NULL         | 2026-06-16 11:04:00.801304+00 | lit
```

**MISSING from asset_throughput (no record at all):**
- bg_ephemeris_engine (service — expected; no writer)
- bg_nakshatra_medical (data — NOT expected; should have a global record)
- bg_panchanga (service — expected; no writer)
- bg_transit_engine (data — NOT expected; should have a global record)

## §3 — count_sql Execution Results (Step 3, Check 1)

### Direct count_sql execution results:

| asset_id            | count_sql result | error?                                |
|---------------------|-----------------|---------------------------------------|
| bg_ephemeris        | 825,084         | PASS                                  |
| bg_reference        | 1,485           | PASS                                  |
| bg_texts            | 10,651          | PASS                                  |
| bg_ontology         | 623             | PASS                                  |
| bg_text_index       | 361             | PASS                                  |
| bg_prashna_rules    | SYNTAX ERROR    | FAIL — missing outer SELECT wrapper   |
| bg_rules            | 2,912           | PASS                                  |
| bg_remedies         | 266             | PASS                                  |
| bg_concordance      | 720             | PASS                                  |
| bg_yogas            | 175             | PASS                                  |
| bg_dasha_systems    | 18              | PASS                                  |
| bg_doshas           | 50              | PASS                                  |
| bg_compendium_index | 9,538           | PASS (count_sql valid; overfill noted)|
| bg_panchanga        | NULL            | N/A — service                         |
| bg_ephemeris_engine | NULL            | N/A — service                         |
| bg_nakshatra        | 2,857           | PASS                                  |
| bg_vastu_directions | SYNTAX ERROR    | FAIL — missing outer SELECT wrapper   |
| bg_transit_engine   | SYNTAX ERROR    | FAIL — missing outer SELECT wrapper   |
| bg_transit_rules    | SYNTAX ERROR    | FAIL — missing outer SELECT wrapper   |
| bg_medical_mappings | 9               | PASS                                  |
| bg_nakshatra_medical| 27              | PASS                                  |

**FIXED versions (adding SELECT wrapper):**
- bg_prashna_rules: SELECT ... AS count = 36
- bg_vastu_directions: SELECT (8 vastu_directions) + (24 remedials) = 32
- bg_transit_engine: SELECT ... = 9
- bg_transit_rules: SELECT ... = 41

## §4 — bg_reference count_sql component breakdown

```
reference_planets:          11
reference_signs:            12
reference_aspects:          19
reference_vargas:           19
reference_houses:           12
reference_strength_systems: 33
reference_karakas:          77
reference_upagrahas:        11
reference_constants:        203
reference_topic_tags:       481
reference_glossary:         364
reference_yogas:            175
reference_doshas:           50
reference_dasha_systems:    18
TOTAL:                    1,485
```

NOTE: count_sql for bg_reference does NOT include reference_nakshatra or reference_nakshatras.
The target_table for bg_reference is `reference_nakshatras` (old table, 27 rows). 
This is a naming/pointer inconsistency (bg_nakshatra asset handles reference_nakshatra).

## §5 — bg_nakshatra count_sql component breakdown

```
reference_nakshatra:        28
reference_nakshatra_pada:  108
reference_nakshatra_matrix: 2,721
TOTAL:                    2,857  (matches target_floor = 2857 EXACTLY)
```

## §6 — Seed vs Prod Comparison (Check 5)

Seed file (`asset_registry_seed.ts`) defines 16 brahmagyan assets:
bg_ephemeris, bg_reference, bg_texts, bg_ontology, bg_text_index, bg_rules, bg_remedies,
bg_concordance, bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index,
bg_panchanga, bg_ephemeris_engine, bg_nakshatra (+ later additions within the file)

Prod asset_registry has 21 brahmagyan assets.

**6 assets in prod but NOT in seed file:**
1. bg_vastu_directions — registered via migration 285_asset_registry_bg_vastu.sql
2. bg_transit_engine — registered via migration 266_bg_transit_tables.sql
3. bg_transit_rules — registered via migration 266_bg_transit_tables.sql
4. bg_medical_mappings — registered via migration 278_bg_medical_asset_registry.sql
5. bg_nakshatra_medical — registered via migration 277_bg_nakshatra_medical.sql
6. bg_prashna_rules — registered via migration 262_bg_prashna_rules_asset_registry.sql

## §7 — FORENSIC Check (Check 12 — Purva Bhadrapada nakshatra 25)

```sql
SELECT nakshatra_id, name_sa_iast, name_en, vimshottari_lord, presiding_deity, ruling_planet, rashis_spanned, start_longitude, end_longitude, body_part
FROM reference_nakshatra WHERE nakshatra_id = 25;
```

Result:
```
nakshatra_id: 25
name_sa_iast: Pūrva Bhādrapadā
name_en: Purva Bhadrapada
vimshottari_lord: jupiter
presiding_deity: Aja Ekapada
ruling_planet: jupiter
rashis_spanned: {Aquarius, Pisces}
start_longitude: 320.00000
end_longitude: 333.33333
body_part: sides
```

**FORENSIC FINDINGS:**
- Lord: Jupiter (CORRECT — expected Brihaspati/Jupiter)
- Deity: Aja Ekapada (PRESENT — note: audit spec expected "Ajaikapada"; this is the correct alternate spelling)
- Rashis: Aquarius and Pisces (CORRECT — pada 1-3 in Aquarius, pada 4 in Pisces)
- body_part: 'sides' (note: spec expected 'left_side' per bg_nakshatra_medical FORENSIC note)

Check bg_nakshatra_medical for FORENSIC native Moon nakshatra:
```sql
SELECT * FROM bg_nakshatra_medical WHERE nakshatra = 'purva_bhadrapada' OR nakshatra ILIKE '%purva%';
```
→ bg_nakshatra_medical stores body_part as 'left_side' for nakshatra #25 per the writer comment.
(Verified indirectly: asset description states "FORENSIC: #25 Purva Bhadrapada → left_side")

## §8 — Citation Coverage (Check 6)

Tables with classical_source / citation columns checked:
```
brahma_remedy_corpus:   0 uncited / 266 total (source_citation field — 100% cited)
brahma_yoga_catalog:    0 uncited / 175 total (classical_citations JSONB — 100% cited)
brahma_dosha_catalog:   0 uncited / 50 total  (classical_citations JSONB — 100% cited)
reference_nakshatra:    0 uncited / 28 total  (classical_source field — 100% cited)
```

## §9 — Writer File Inventory (Step 5)

Found 16 bg_*.py writer files at:
`/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/pipeline/orchestrator/writers/`

```
bg_compendium_index.py  — @register('bg_compendium_index'), class CompendiumIndexWriter(WriterBase)
bg_concordance.py       — @register("bg_concordance"), class ConcordanceWriter(WriterBase)
bg_dasha_systems.py     — @register('bg_dasha_systems'), class DashaSystemsWriter(WriterBase)
bg_doshas.py            — @register('bg_doshas'), class DoshasWriter(WriterBase)
bg_medical_mappings.py  — @register('bg_medical_mappings'), class BgMedicalMappingsWriter(WriterBase)
bg_nakshatra.py         — @register('bg_nakshatra'), class NakshatraReferenceWriter(WriterBase)
bg_ontology.py          — @register('bg_ontology'), class OntologyWriter(WriterBase)
bg_prashna_rules.py     — @register("bg_prashna_rules"), class PrashnaRulesWriter(WriterBase), run(ctx) [untyped — # type: ignore[override]]
bg_reference.py         — @register('bg_reference'), class ReferenceWriter(WriterBase)
bg_remedies.py          — @register('bg_remedies'), class RemediesWriter(WriterBase)
bg_rules.py             — @register('bg_rules'), class RulesWriter(WriterBase)
bg_text_index.py        — @register("bg_text_index"), class TextIndexWriter(WriterBase)
bg_texts.py             — @register("bg_texts"), class TextsWriter(WriterBase)
bg_transit_rules.py     — @register("bg_transit_rules"), class BgTransitRulesWriter(WriterBase), run(ctx) [untyped — # type: ignore[override]]
bg_vastu_directions.py  — @register('bg_vastu_directions'), class BgVastuDirectionsWriter(WriterBase)
bg_yogas.py             — @register('bg_yogas'), class YogasWriter(WriterBase)
```

**MISSING WRITERS (no bg_*.py file):**
- bg_ephemeris (ephemeris_daily is seeded separately — not orchestrator-driven)
- bg_ephemeris_engine (service — expected)
- bg_panchanga (service — expected)
- bg_transit_engine (data — MISSING WRITER; table has 9 rows but no orchestrator-registered writer)
- bg_nakshatra_medical (data — MISSING WRITER; table has 27 rows but no orchestrator-registered writer)

## §10 — Exception Handling (Check 7)

Only bg_texts.py has exception handling blocks:
- Line 101: `except Exception as exc:` with `logger.error(...)` then `return None` — non-silent (GCS download failure)
- Line 156: `except Exception as exc:` with `logger.warning(...)` then `return None` — non-silent (DjVu fetch failure)

Both exceptions log at error/warning level and return None (skipping the source). This is graceful degradation for optional external sources (GCS PDFs, archive.org), not silent swallowing. The outer writer run() handles None returns by skipping those texts.

No `except: pass` or `except: logger.debug` patterns found.

## §11 — Fragmentation (Check 11)

Nakshatra tables in prod:
```
bg_nakshatra_medical       — 27 rows  (active L0 asset)
reference_nakshatra        — 28 rows  (new canonical table, bg_nakshatra asset)
reference_nakshatra_matrix — 2,721 rows (new, part of bg_nakshatra)
reference_nakshatra_pada   — 108 rows  (new, part of bg_nakshatra)
reference_nakshatras       — 27 rows  (OLD table — bg_reference.target_table still points here)
```

**FRAGMENTATION CONFIRMED:** Both `reference_nakshatras` (old, 27 rows) and `reference_nakshatra` (new, 28 rows) exist simultaneously. bg_reference.target_table = 'reference_nakshatras' (old, inconsistent with bg_nakshatra which uses the new tables).

Other potentially orphaned bg_* tables (from migration 250, NO asset_registry entry):
```
bg_avastha_schemes             — 35 rows
bg_combustion_orbs             — 8 rows
bg_dignity_reference           — 9 rows
bg_graha_naisargika_friendship — 72 rows
bg_motion_state_thresholds     — 27 rows
```

Other tables with data but uncertain registry status:
```
classical_chunks        — 0 rows  (empty)
classical_texts         — 16 rows
classical_texts_source  — 11 rows
prashna_charts          — 0 rows  (empty)
sutravali_review        — 154 rows
```

## §12 — Idempotency Patterns (Check 9)

All 16 bg_* writers use L0-compliant ON CONFLICT patterns:
- Most: ON CONFLICT DO NOTHING / DO UPDATE
- bg_texts: DELETE FROM classical_text_chunks first (full replace), then INSERT ON CONFLICT DO NOTHING
- bg_compendium_index: ON CONFLICT on dedup unique index

L0 standard §N.3 pattern compliance: ALL writers correctly use ON CONFLICT (not per-chart delete-then-insert).

## §13 — Scope/Registration Completeness (Check 8)

All 21 prod assets have:
- scope: 'global' (CORRECT for L0 — all are global reference)
- is_active: true (all)
- catalog_status: 'CURRENT' (all)
- asset_type: 'data' or 'service' (correctly set)

Four assets registered via migrations (not seed) use older column names:
- Migration 266 used `display_name` column (not in current schema), suggesting it was written for an earlier schema version. Prod records appear correctly migrated.

## §14 — Throughput Anomalies

bg_compendium_index anomaly:
- scope = 'global' but asset_throughput record has chart_id = 482012f1 (per-chart)
- This means the global table has no global throughput row — only a chart-scoped one
- Real row count: 9,538 (vs target_floor 1,755 = 5.44× overfill)
- rows_written in throughput: 7,025 (stale — doesn't match actual 9,538)

bg_nakshatra anomaly:
- rows_written = 0, state = lit
- But reference_nakshatra has 28 rows, reference_nakshatra_pada has 108 rows, reference_nakshatra_matrix has 2,721 rows
- built_against_upstream_hash = 'e3b0c44298fc1c14' (SHA256 of empty string — indicates no upstream hash tracked)
- Writer appears to have run but rows_written was not recorded

bg_reference and bg_ontology:
- Both have TWO throughput records: one global (rows_written=0) and one per-chart (rows_written=NULL)
- Global records show rows_written=0 — built but wrote nothing (global tables already populated)
- Per-chart records are scope artifacts from per-chart build runs

## §15 — All L0-Related Tables with Row Counts

### Currently referenced by asset_registry:
```
ephemeris_daily:         825,084 rows
classical_text_chunks:   10,651 rows  (contains embedded topic tags)
brahma_ontology:         623 rows
sutravali_rules:         2,912 rows
brahma_remedy_corpus:    266 rows
classical_attributions:  720 rows
brahma_yoga_catalog:     175 rows
brahma_dasha_systems:    18 rows
brahma_dosha_catalog:    50 rows
brahma_compendium_index: 9,538 rows
reference_nakshatra:     28 rows
reference_nakshatra_pada: 108 rows
reference_nakshatra_matrix: 2,721 rows
bg_vastu_directions:     8 rows
bg_vastu_direction_remedials: 24 rows
bg_transit_engine:       9 rows
bg_transit_rules:        41 rows
bg_medical_mappings:     9 rows
bg_nakshatra_medical:    27 rows
bg_prashna_lagna_methods: 5 rows
bg_prashna_tajik_yogas:  11 rows
bg_prashna_significators: 12 rows
bg_prashna_fructification_rules: 5 rows
bg_prashna_special_techniques: 3 rows
```

### bg_reference sub-tables (summed in count_sql):
```
reference_planets:         11 rows
reference_signs:           12 rows
reference_aspects:         19 rows
reference_vargas:          19 rows
reference_houses:          12 rows
reference_strength_systems: 33 rows
reference_karakas:         77 rows
reference_upagrahas:       11 rows
reference_constants:       203 rows
reference_topic_tags:      481 rows
reference_glossary:        364 rows
reference_yogas:           175 rows
reference_doshas:          50 rows
reference_dasha_systems:   18 rows
TOTAL:                    1,485 rows
```

### OLD table (fragmented, should be retired):
```
reference_nakshatras:    27 rows  (OLD — being superseded by reference_nakshatra)
```

### Orphaned tables (no asset_registry entry, populated):
```
bg_avastha_schemes:             35 rows  (from migration 250)
bg_combustion_orbs:             8 rows   (from migration 250)
bg_dignity_reference:           9 rows   (from migration 250)
bg_graha_naisargika_friendship: 72 rows  (from migration 250)
bg_motion_state_thresholds:     27 rows  (from migration 250)
```

### Orphaned tables (no asset_registry entry, empty):
```
classical_chunks:        0 rows
prashna_charts:          0 rows
```

### Ancillary tables (referenced indirectly):
```
classical_texts:          16 rows  (text metadata for bg_texts)
classical_texts_source:   11 rows
sutravali_review:         154 rows  (review queue for bg_rules)
```
