-- 369_count_sql_batch2.sql
-- Fix count_sql for bg_reference, bg_yogas, bg_texts, mi_adhilepa.
--
-- bg_reference: current count_sql (set by migration 179, trimmed by 239) includes
--   reference_yogas, reference_doshas, reference_dasha_systems — tables written by
--   bg_yogas, bg_doshas, and bg_dasha_systems respectively, NOT by bg_reference.
--   bg_reference delegates to l0_reference.seed_reference() which writes only:
--     reference_planets, reference_signs, reference_aspects, reference_vargas,
--     reference_houses, reference_strength_systems, reference_karakas,
--     reference_upagrahas, reference_constants, reference_topic_tags, reference_glossary
--   Remove the 3 cross-asset tables from the sum.
--
-- bg_yogas: current count_sql = SELECT count(*) FROM brahma_yoga_catalog
--   Writer (bg_yogas.py → l0_yogas.seed_yogas) also inserts into:
--     brahma_ontology (entity_class='yoga') and reference_yogas
--   Extend count_sql to include all three tables.
--
-- bg_texts: current count_sql = SELECT count(*) FROM classical_text_chunks
--   Writer (bg_texts.py) also upserts into classical_texts (one row per text,
--   18 rows = every TEXTS entry). classical_texts registry rows are entirely
--   uncounted. Add classical_texts to the sum.
--
-- mi_adhilepa: current count_sql (set by migration 364) counts 3 tables:
--   mimamsa_load_bearing, mimamsa_convergence_adjustment, mimamsa_anchor_adjustment.
--   Writer also inserts into mimamsa_signal_adjustment (signal overlays from
--   bodha_msr_signals — high-volume, can be hundreds of rows per chart) and
--   mimamsa_fact_adjustment (fact overlays from chart_facts). Both are cleared in
--   the idempotency DELETE block (mi_adhilepa.py lines 147-154) but were absent
--   from count_sql. Fix extends the sum to all 5 tables the writer writes.
--   EXPLICIT_CLEAR_OPS in assetClearSpec.ts is updated separately (see that file).
--
-- All changes are idempotent UPDATEs.

-- ── bg_reference ──────────────────────────────────────────────────────────────
-- Remove reference_yogas, reference_doshas, reference_dasha_systems.
-- Authority for those tables: bg_yogas, bg_doshas, bg_dasha_systems respectively.
UPDATE asset_registry
SET count_sql = $sql$SELECT
  (SELECT count(*) FROM reference_planets) +
  (SELECT count(*) FROM reference_signs) +
  (SELECT count(*) FROM reference_aspects) +
  (SELECT count(*) FROM reference_vargas) +
  (SELECT count(*) FROM reference_houses) +
  (SELECT count(*) FROM reference_strength_systems) +
  (SELECT count(*) FROM reference_karakas) +
  (SELECT count(*) FROM reference_upagrahas) +
  (SELECT count(*) FROM reference_constants) +
  (SELECT count(*) FROM reference_topic_tags) +
  (SELECT count(*) FROM reference_glossary) AS count$sql$
WHERE asset_id = 'bg_reference';

-- ── bg_yogas ──────────────────────────────────────────────────────────────────
-- Add brahma_ontology (yoga rows) + reference_yogas to the sum.
-- brahma_ontology is a global shared table; we count only yoga entity_class rows
-- so the cockpit number reflects exactly what bg_yogas writes.
UPDATE asset_registry
SET count_sql = $sql$SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_yogas) AS count$sql$
WHERE asset_id = 'bg_yogas';

-- ── bg_texts ──────────────────────────────────────────────────────────────────
-- Add classical_texts (18 registry rows, one per corpus text) to the count.
-- The existing count_sql counts classical_text_chunks (chunks + embeddings);
-- the 18-row classical_texts registry table was entirely uncounted.
UPDATE asset_registry
SET count_sql = $sql$SELECT
  (SELECT count(*) FROM classical_texts) +
  (SELECT count(*) FROM classical_text_chunks) AS count$sql$
WHERE asset_id = 'bg_texts';

-- ── mi_adhilepa ───────────────────────────────────────────────────────────────
-- Extend count to all 5 tables the writer emits.
-- mimamsa_signal_adjustment and mimamsa_fact_adjustment were written and cleared
-- by the writer but absent from the count_sql.
-- EXPLICIT_CLEAR_OPS in assetClearSpec.ts updated to add both tables.
UPDATE asset_registry
SET count_sql = $sql$SELECT
  (SELECT count(*) FROM mimamsa_load_bearing           WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_convergence_adjustment WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_anchor_adjustment      WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_signal_adjustment      WHERE chart_id = $1) +
  (SELECT count(*) FROM mimamsa_fact_adjustment        WHERE chart_id = $1) AS count$sql$
WHERE asset_id = 'mi_adhilepa';
