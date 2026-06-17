# Phase 2 Deferred Items — L0 Brahmagyan Closure Pass

## P1-A: bg_transit_engine Writer
**Status:** Deferred
**Reason:** The bg_transit_engine table has 9 seeded rows (transit engine motion parameters) but no WriterBase subclass. A global throughput record has been inserted (migration 300, state=lit) to make it visible in build monitoring. Full writer creation deferred pending L2 Bodha campaign.
**Throughput:** state=lit, rows_written=9 (migration 300_fix_missing_throughput_records.sql)

## P1-A: bg_nakshatra_medical Writer
**Status:** Deferred
**Reason:** The bg_nakshatra_medical table has 27 seeded rows (nakshatra body-part mappings) but no WriterBase subclass. A global throughput record has been inserted (migration 300, state=lit) to make it visible in build monitoring. Full writer creation deferred pending L2 Bodha campaign.
**Throughput:** state=lit, rows_written=27 (migration 300_fix_missing_throughput_records.sql)

## P2-B: Drop reference_nakshatras
**Status:** Deferred (deprecation comment applied in migration 302)
**Reason:** reference_nakshatras has live INSERT code in l0_reference.py (~line 1342) and is referenced in bg_reference writer and governance scripts. A COMMENT ON TABLE deprecation marker was applied. Full drop requires:
1. Update bg_reference writer (l0_reference.py) to stop writing to reference_nakshatras
2. Update governance scripts (v13_production_gate.py, vimarsaka_beta.py) to remove reference
3. Apply DROP TABLE migration

## P3-E: Drop classical_chunks and prashna_charts
**Status:** Deferred (deprecation/placeholder comments applied in migration 303)
**Reason:**
- classical_chunks: Empty, but live code in l0_text_index.py._search_classical_chunks() queries it
- prashna_charts: Empty, but live code in ga_prashna_writer.py Step 1 queries it
Both require live code refactors before they can be safely dropped.

## bg_prashna_rules target_table
**Status:** Remains NULL (correct — asset spans 5 tables; no single primary table)
**Reason:** bg_prashna_rules writes to bg_prashna_lagna_methods, bg_prashna_tajik_yogas, bg_prashna_significators, bg_prashna_fructification_rules, bg_prashna_special_techniques. NULL target_table is appropriate for multi-table assets without a canonical primary.
