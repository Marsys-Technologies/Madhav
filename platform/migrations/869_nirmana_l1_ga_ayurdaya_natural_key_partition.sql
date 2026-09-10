-- 869_nirmana_l1_ga_ayurdaya_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Second of seven natural_key_partition backfills authorized by the
-- Conductor's ruling on adjudication #2180 (2026-09-07). `chart_facts` is
-- shared by seven L1 writers; each needs its own declared partition or
-- the DEP-ASSERT gate reads `freshness_state='unknown'` forever. First
-- (`ga_positions`) shipped in migration 868 (PR #2205); this is the
-- second.
--
-- `ga_ayurdaya`'s ownership is the simplest of the seven: a single
-- hardcoded constant, `FACT_CATEGORY = "ayurdaya"`
-- (ga_ayurdaya_writer.py:57) -- the writer emits nothing else into
-- `chart_facts`. Confirmed no overlap: grepped all six sibling writers
-- (`ga_positions_writer.py`, `ga_nakshatra_emitters.py`,
-- `ga_kp_significators.py`, `ga_panchanga_writer.py`,
-- `ga_sade_sati_writer.py`, `ga_sensitive_writer.py`,
-- `ga_sensitive_degree_writer.py`) for the literal string `"ayurdaya"`,
-- zero hits.

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category = ayurdaya'
 WHERE asset_id = 'ga_ayurdaya'
   AND natural_key_partition IS NULL;
