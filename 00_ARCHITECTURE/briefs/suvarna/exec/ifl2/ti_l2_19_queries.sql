-- TI-L2-19 review queries (reader-only SELECT; chart 482012f1-710e-4a25-994a-93821f5871aa)
-- Q1: yoga/dosha signals by type, per ayanamsha
select signal_type_class, signal_type_id, ayanamsha_id, count(*) from bodha_msr_signals
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and signal_type_class in ('yoga','dosha') group by 1,2,3 order by 1,2,3;
-- Q2: live yoga/dosha nodes per ayanamsha, with degrees
select ayanamsha_id, node_type, node_subject, degree_in, degree_out from bodha_cgm_nodes
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and node_type in ('yoga','dosha') order by 1,2,3;
-- Q3: no membership edges on the chart
select edge_type, count(*) from bodha_cgm_edges where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1 order by 2 desc;
-- Q4: kendradhipati signals: per graha, active flag, doctrine status
select ayanamsha_id, configuration_jsonb->>'planet' planet, configuration_jsonb->>'kendradhipati_active' active,
       configuration_jsonb->>'doctrine_status' doctrine, configuration_jsonb->>'fact_value_text' vtext
  from bodha_msr_signals where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and signal_type_id='kendradhipati_dosha:doshas_kendradhipati' order by 1,2;
-- Q5: the identity function
select pg_get_functiondef('public.bodha_cgm_node_identity'::regproc);
