-- TI-L2-40 trace queries (reader-only SELECT; chart 482012f1-710e-4a25-994a-93821f5871aa)
select edge_type, relationship_class, cancelled_flag, valence, count(*)
  from bodha_cgm_edges where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and (edge_type='argala' or relationship_class ilike '%argala%') group by 1,2,3,4 order by 1,2,3,4;
select edge_type, count(*), count(*) filter (where cancelled_flag) cancelled
  from bodha_cgm_edges where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1 order by 2 desc;
select count(*) from bodha_cgm_edges where chart_id='482012f1-710e-4a25-994a-93821f5871aa';
