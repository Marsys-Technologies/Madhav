# bg_yogas: Citation Pass 2 (decision OS-2026-10-05-CITATIONS)

Branch `suvarna/engine-citation-yogas`. Migration **1322**. Queued after S-L2.

## What changes
One catalog row, `brahma_yoga_catalog.canonical_id = kala_sarpa_yoga`: `classical_citations` = one K2 object (modern practice / project judgment, ratified OS-2026-10-05-CITATIONS; note: duplicate authority, not fired by ga_yoga_writer, R6A.2); `school` = `modern`; `cancellation_conditions` gains a `notes` string. 233 / 233 / 233 rows before and after; no other row or column changes. The ontology projection of the row still carries the classical-lineage label (not decided; listed in `E5.7/CITATION_AMBIGUOUS.md`). The K2 object shape and the `notes` key are choices listed there too.

## RUNBOOK GATE for migration 1322 (read before merging, and again after the rebuild)
1322 derives the new catalog pin IN SQL from the live table, because the catalog pin covers corpus-extracted rows that cannot be derived offline. A state it cannot classify is NOT overwritten: it raises a WARNING and changes nothing, and `migrate.ts` still records the migration as applied, so it never re-runs; only a new migration would repair a stale pin.
- **BEFORE the deploy that carries 1322**, confirm read-only that the live catalog hashes to the old pin:
  `SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class)::text, E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') FROM brahma_yoga_catalog;`
  Expect `4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8`. If it differs, STOP and ask.
- **AFTER the governed rebuild**, REQUIRE the stored integrity check to return `t`: `SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_yogas' \gexec`. A FALSE means the migration skipped (look for the WARNING in the deploy log) or the rebuild differs from the decided change; it is loud by design, never silently disabled.
- An empty L0 catalog (no kala_sarpa_yoga row) is a NOTICE and a no-op, never a blocked deploy.

## Migration 1322
Guarded replace of the catalog pin inside `integrity_check_sql`; only runs while the live catalog hashes to the sealed pin (or already equals the decided post-state). `SET LOCAL lock_timeout = '5s'`. SERVING EFFECT: the UPDATE fires `nirmana_registry_receipt_invalidation` (migration 596) and stales bg_yogas' freshness rows. **Order:** apply 1322, then the governed rebuild (expected-change mode, `expected_change_bg_yogas.json`: row count 1292 as of the 2026-10-05 census, set to the plan's pre count if bg_ontology was rebuilt first; no fingerprint declared: the unit holds corpus-extracted rows). Between them the stored check reads FALSE by design.

## Readers
`routers/yoga_formation_band._citations` skips an entry without `text_id` (tested: a K2-only column lists no classical citation); `ga_yoga_writer` does not branch on the citation text and does not fire this relation.

## Tests run
`platform/python-sidecar/tests/l0/test_citation_pass2_yogas.py` (10, disposable Postgres): row pins, Ldgr predicate, the pin the migration writes equals the hash after the REAL seeder runs with the new row, catch-up when the catalog was rebuilt first, skip with a WARNING on an unclassifiable state, empty catalog notice, readers.
