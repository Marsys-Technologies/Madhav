-- 868_nirmana_l1_ga_positions_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors ga_positions' natural_key_partition -- fix 1/2 of the Conductor's
-- ruling on adjudication #2180 (2026-09-07). `chart_facts` is shared by
-- seven L1 writers (ga_positions, ga_ayurdaya, ga_nakshatra, ga_panchanga,
-- ga_sade_sati, ga_sensitive, ga_sensitive_degree); provenance.py's
-- `has_cowriters` check is true for all seven, so each needs its own
-- `natural_key_partition` describing the slice it actually owns, or the
-- DEP-ASSERT gate reads `freshness_state='unknown'` (reason:
-- `partition_undeclared`) forever, regardless of a successful rebuild.
--
-- ga_positions' own `fact_category` ownership, verified directly against
-- `ga_positions_writer.py`'s actual row-construction call sites (not
-- assumed from the coverage_matrix.ts serving-tool mapping, which records
-- who SERVES a category, not who WRITES it): `_build_position_rows`
-- (lines ~299-368) emits `graha_position` and `graha_sign_attributes`;
-- `_build_chalit_rows`/`_chalit_row` (lines ~403-507) emits `bhava_cusps`
-- and `house_chalit`. Confirmed no overlap: grepped all six sibling
-- writers for these four literal strings, zero hits in any of them.
--
-- This is L1's own domain knowledge to author, not a value to guess or
-- fabricate (per the ruling's own framing, mirroring adjudication #1888's
-- "you know the writer, pick the correct key" instruction for an
-- analogous case). Scoped to exactly what this session verified live in
-- the writer's own source, nothing more.
--
-- Only ga_positions is authored here. The other six chart_facts
-- co-writers this same ruling authorizes are NOT included -- each needs
-- its own equally careful verification of what it actually writes (one,
-- ga_sensitive, turned out to own a much larger and more diverse category
-- set than initially assumed while investigating this migration), and
-- rushing all seven in one migration risks the exact "collapsing several
-- writers' provenance into one guess" failure mode the ruling explicitly
-- warned against. Left for follow-up migrations.

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category IN (graha_position, graha_sign_attributes, bhava_cusps, house_chalit)'
 WHERE asset_id = 'ga_positions'
   AND natural_key_partition IS NULL;
