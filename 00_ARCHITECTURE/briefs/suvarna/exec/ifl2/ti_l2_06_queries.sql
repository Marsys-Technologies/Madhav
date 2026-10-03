-- TI-L2-06 trace queries (reader-only SELECT)
-- Q1: identity coverage by chart
select f.chart_id, count(*) facts,
       count(*) filter (where exists (select 1 from chart_fact_identity i where i.fact_id=f.fact_id)) with_identity
  from chart_facts f where f.chart_id in ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
 group by 1;
-- Q2: identity rows by kind
select chart_id, entity_kind, count(*), count(varga_id) with_varga from chart_fact_identity group by 1,2 order by 1,2;
-- Q3: identity build vs facts builds (canonical)
select build_id, count(*), min(computed_at)::date, max(computed_at)::date from chart_fact_identity
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1;
select count(distinct build_id), min(computed_at)::date, max(computed_at)::date from chart_facts
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- Q4: the FK that cascades
select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid='chart_fact_identity'::regclass and contype='f';
-- Q5: what bodha_pratijna's provenance cites, per chart
select p.chart_id, f.fact_category, f.fact_key, count(*)
  from bodha_pratijna p, jsonb_array_elements(p.derivation->'provenance') e
  join chart_facts f on f.fact_id::text = e->>'id'
 where e->>'id_kind'='fact_id' and p.chart_id in ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
 group by 1,2,3 order by 1,4 desc;
-- Q6: the table the docstring names
select to_regclass('public.brahma_reference_planets') as docstring_table, to_regclass('public.reference_planets') as real_table;
-- Q7: registry rows
select asset_id, depends_on from asset_registry where asset_id in ('bo_pratijna','bg_reference','ga_vargas','ga_positions','ga_structural','ga_sensitive');
