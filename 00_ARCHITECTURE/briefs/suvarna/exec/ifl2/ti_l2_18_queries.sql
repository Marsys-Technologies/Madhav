-- TI-L2-18 trace queries (reader-only SELECT; chart 482012f1-710e-4a25-994a-93821f5871aa)
-- Q1: rows carrying a count, with the distinct-text count derived from the row's own citations
with d as (
  select signal_id, signal_type_class, signal_type_id, source_corroboration_count_by_text c,
         salience_formula_version v, producer_asset_id,
         (select count(distinct split_part(x,':',1))
            from jsonb_array_elements_text(coalesce(classical_sources_jsonb->'citations','[]'::jsonb)) x) ncit,
         (select count(distinct split_part(x,'_pg',1))
            from jsonb_array_elements_text(coalesce(classical_sources_jsonb->'text_chunk_ids','[]'::jsonb)) x) nchunk,
         classical_sources_jsonb is null as nosrc
    from bodha_msr_signals
   where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and source_corroboration_count_by_text is not null)
select signal_type_class, left(signal_type_id,40) sid, producer_asset_id, c, v, ncit, nchunk, nosrc, count(*)
  from d group by 1,2,3,4,5,6,7,8 order by 1,2,4;
-- Q2: which producers store a count at all
select producer_asset_id,
       count(*) filter (where source_corroboration_count_by_text is null) nulls,
       count(*) filter (where source_corroboration_count_by_text is not null) nn, count(*)
  from bodha_msr_signals where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1 order by 1;
-- Q3: the 14 rows, with their citations
select signal_id, signal_type_id, source_corroboration_count_by_text c, classical_sources_jsonb::text
  from bodha_msr_signals
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and signal_type_class='yoga'
   and signal_type_id='yoga_label:yoga_name' and source_corroboration_count_by_text=2 order by 4;
-- Q4: signal classes of the chart (the amplifier class is absent)
select signal_type_class, count(*), count(*) filter (where source_corroboration_count_by_text is not null) nn
  from bodha_msr_signals where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1 order by 2 desc;
