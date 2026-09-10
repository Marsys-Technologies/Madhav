-- 870_nirmana_l1_ga_sensitive_degree_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Third of seven natural_key_partition backfills authorized by the
-- Conductor's ruling on adjudication #2180 (2026-09-07). First
-- (`ga_positions`) shipped in migration 868 (PR #2205); second
-- (`ga_ayurdaya`) in migration 869 (PR #2208); this is the third.
--
-- `ga_sensitive_degree`'s ownership was already established during this
-- session's own F-B32 audit (cycle 152) and re-confirmed directly against
-- `ga_sensitive_degree_writer.py` for this migration: the file's own
-- header (line 5) states "Table: chart_facts (fact_category =
-- 'sensitive_degree_check')", and `build_yogi_points_rows()` (~line 483)
-- additionally emits `fact_category='sensitive_point_yogi'` for a ninth
-- facet, both scoped by the same `replace_prior_chart_facts` idempotency
-- call (lines 57-61). `ga_sensitive_writer.py` mentions `sensitive_point_
-- yogi` too, but only in a cross-referencing DOCSTRING comment (lines
-- 802-816) explaining its own DIFFERENT category (`esoteric_point_yogi`)
-- computes the same classical construction independently -- it does not
-- write `sensitive_point_yogi` itself. Confirmed no genuine overlap:
-- grepped all six sibling writers for both literal category strings;
-- only this comment, no real write, anywhere else.

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category IN (sensitive_degree_check, sensitive_point_yogi)'
 WHERE asset_id = 'ga_sensitive_degree'
   AND natural_key_partition IS NULL;
