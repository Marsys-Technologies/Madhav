#!/usr/bin/env python3
"""A.L4 named read-only queries behind the numbers quoted in the briefs. SELECT only (suvarna_reader). Output: upstream_receipts.json"""
import json, datetime
from collect import q
C = "'482012f1-710e-4a25-994a-93821f5871aa'"
O = "'1c826d5a-41cb-4450-b4dc-59d440e5f75a'"
Q = {
 'upstream_rows_by_chart': ["select 'kala_convergence' t, chart_id::text c, count(*) from kala_convergence group by 2 union all select 'kala_bhavishya', chart_id::text, count(*) from kala_bhavishya group by 2 union all select 'kala_obstruction', chart_id::text, count(*) from kala_obstruction group by 2 union all select 'bodha_discoveries', chart_id::text, count(*) from bodha_discoveries group by 2 union all select 'bodha_cdlm_cells', chart_id::text, count(*) from bodha_cdlm_cells group by 2 union all select 'bodha_rm_remedy_prescriptions', chart_id::text, count(*) from bodha_rm_remedy_prescriptions group by 2 union all select 'life_events', chart_id::text, count(*) from life_events group by 2 union all select 'mimamsa_predictions', chart_id::text, count(*) from mimamsa_predictions group by 2 order by 1,2"],
 'discoveries_computed_at': [f"select min(computed_at)::text, max(computed_at)::text, count(*) from bodha_discoveries where chart_id={C}"],
 'stored_discovery_ids_still_exist': [f"select count(*) stored, count(d.discovery_id) still_exist from phala_anchors a left join bodha_discoveries d on d.discovery_id::text=a.discovery_id::text where a.chart_id={C}"],
 'predictions_resolving_to_anchors': [f"select count(*) total, count(a.anchor_id) resolves from mimamsa_predictions p left join phala_anchors a on a.anchor_id::text=p.source_pramana_id where p.chart_id={C}"],
 'nimitta_integrity_prediction_term_all_charts': ["select count(*) from mimamsa_predictions p left join phala_anchors a on a.anchor_id::text=p.source_pramana_id where p.source_pramana_id is not null and a.anchor_id is null"],
 'asset_throughput_ph': [f"select asset_id,state,rows_written,last_built_at::text from asset_throughput where chart_id={C} and asset_id like 'ph\\_%' order by 1"],
 'asset_throughput_upstream': [f"select asset_id,state,rows_written,last_built_at::text from asset_throughput where chart_id={C} and asset_id in ('ka_sangam','ka_bhavishya_lekha','ka_vighnakara','ka_kalasutra','ka_gochara','bo_upaya','bo_sangati','bo_anveshana','bo_laksana') order by 1"],
 'anchors_posterior_window': [f"select count(distinct posterior) dp, min(posterior), max(posterior), min(window_start)::text, max(window_end)::text, count(*) filter (where peak_date is null) nopeak, count(*) filter (where lift_vector_jsonb->>'promise_lift'='1.75') promise175 from phala_anchors where chart_id={C}"],
 'bhavishya_probability_tier': ["select probability_tier, count(*) from kala_bhavishya group by 1"],
 'phaladesa_vs_anchors': [f"select pd.domain, pd.anchor_count, (select count(*) from phala_anchors a where a.chart_id=pd.chart_id and lower(a.domain)=pd.domain) real_anchors, pd.top_anchor_id is not null has_top, (select count(*) from phala_anchors a where a.anchor_id=pd.top_anchor_id) top_resolves from phala_phaladesa pd where pd.chart_id={C} order by 1"],
 'phaladesa_narration_contradiction': [f"select count(*) filter (where narration_jsonb->>'text' like '%contradiction signal(s) temper%') claims, count(*) filter (where contradiction_summary_jsonb->>'contested'='false') contested_false, count(*) filter (where narration_jsonb->>'text' like '%passed clean sodhana review%') clean_claims from phala_phaladesa where chart_id={C}"],
 'muhurta_scores': [f"select action_class, count(*), round(min(composite_quality)::numeric,3) cmin, round(max(composite_quality)::numeric,3) cmax, round(min(panchanga_score)::numeric,3) pmin, round(max(panchanga_score)::numeric,3) pmax, count(*) filter (where hora_lord is distinct from personalization_graha) hora_ne_graha, count(*) filter (where linked_anchor_id is not null) linked from phala_muhurta where chart_id={C} group by 1 order by 1"],
 'muhurta_bala_source': [f"select tarabala_chandrabala_jsonb->>'source' src, window_quality_verdict, count(*) from phala_muhurta where chart_id={C} group by 1,2"],
 'sodhana_other_chart': ["select anomaly_type, anomaly_severity, count(*), count(distinct anchor_id) from phala_sodhana group by 1,2 order by 1,2"],
 'suddha_by_chart': ["select chart_id::text, cleanliness_status, count(*) from phala_suddha_sodhana group by 1,2 order by 1,2"],
 'sodhana_anchor_inputs_other_chart': [f"select count(distinct confidence_high) dch, count(distinct (dasha_consensus_count, ayanamsha_robustness)) pairs, count(*) from phala_anchors where chart_id={O}"],
 'pramana_by_chart': ["select chart_id::text, evidence_type, window_status, evidence_strength_label, count(*) from phala_pramana group by 1,2,3,4 order by 1,2,3"],
 'life_events_categories': [f"select category, count(*) from life_events where chart_id={C} group by 1 order by 2 desc"],
 'life_events_date_confidence': [f"select date_confidence, count(*) filter (where event_date<'2020-01-01') pre2020, count(*) from life_events where chart_id={C} group by 1"],
 'mitigation_facts': [f"select count(*) n, count(*) filter (where (program_jsonb->>'total_scheduled')::int=0) empty_programs, count(*) filter (where linked_anchor_id is null) no_anchor, count(*) filter (where afflicting_graha is null or afflicting_graha='') no_graha, count(distinct classical_citation) dcite, count(*) filter (where source_id is null) null_source from phala_mitigation where chart_id={C}"],
 'mitigation_obstruction_resolution': [f"select count(*) total, count(o.id) resolves from phala_mitigation m left join kala_obstruction o on o.id=m.obstruction_id and o.chart_id=m.chart_id where m.chart_id={C}"],
 'prescriptions_shape': [f"select estimated_cost_inr_range_jsonb->>'cost_tier' ct, count(*), count(*) filter (where estimated_cost_inr_range_jsonb ? 'max_inr') has_max_inr, count(*) filter (where array_length(prerequisite_prescription_ids_array,1)>0) prereq, count(*) filter (where array_length(incompatible_with_prescription_ids_array,1)>0) incompat from bodha_rm_remedy_prescriptions where chart_id={C} group by 1 order by 2 desc"],
 'prescriptions_source_ids': [f"select classical_sources_jsonb->>'source_id' sid, count(*) from bodha_rm_remedy_prescriptions where chart_id={C} group by 1"],
 'sankrama_fanout': [f"select count(*) rows, count(distinct (source_anchor_id,target_domain)) pairs, count(*) filter (where projected_window_start=source_window_start and projected_window_end=source_window_end) same_window, count(*) filter (where trajectory='stable') stable, count(*) filter (where asymmetry_score=0) asym0, count(*) filter (where cascade_depth=1) depth1 from phala_sankrama where chart_id={C}"],
 'sankrama_cell_resolution': [f"select count(*) total, count(c.cell_id) resolves from phala_sankrama s left join bodha_cdlm_cells c on c.cell_id=s.cdlm_cell_id where s.chart_id={C}"],
 'cdlm_upstream_nulls': [f"select count(*) n, count(cell_evolution_gradient_score) grad, count(asymmetry_score) asym, count(*) filter (where jsonb_array_length(coalesce(predicted_activation_dasha_windows_jsonb,'[]'::jsonb))>0) act_windows from bodha_cdlm_cells where chart_id={C}"],
 'rectification_summary': [f"select ayanamsha_id, lagna_stable, lel_fit_score::text, lel_events_matched, lel_events_tested, count(*), count(distinct offset_minutes) from phala_rectification where chart_id={C} group by 1,2,3,4,5 order by 1,2"],
 'rectification_best': [f"select offset_minutes, best_lel_fit_score::text, confidence_low::text, confidence_high::text, confidence_label, win_margin::text, lel_training_events, lel_training_matched, judgment_flags::text, auto_action, native_adopted from phala_rectification_best where chart_id={C}"],
 'rectification_sign_vs_L1': [f"select r.ayanamsha_id, r.lagna_sign = (select fact_value_text from chart_facts f where f.chart_id=r.chart_id and f.fact_subject='LAGNA' and f.fact_key='sign' limit 1) eq_L1 from phala_rectification r where r.chart_id={C} and offset_minutes=0"],
 'chart_facts_graha_subjects': [f"select fact_subject from chart_facts where chart_id={C} and ayanamsha_id='lahiri_chitrapaksha' and fact_category='graha_position' and fact_key='sign' order by 1"],
 'builder_privileges': ["select t, has_table_privilege('data_plane_builder', 'public.'||t, 'INSERT') ins, has_table_privilege('data_plane_builder', 'public.'||t, 'DELETE') del, has_table_privilege('data_plane_builder', 'public.'||t, 'SELECT') sel from unnest(array['phala_anchors','phala_muhurta','phala_sodhana','phala_mitigation','phala_suddha_sodhana','phala_sankrama','phala_pramana','phala_phaladesa','phala_rectification','phala_rectification_best','mimamsa_predictions']) t"],
 'identity_function_privilege': ["select has_function_privilege('phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text)','execute') can_execute"],
 'cascade_fks': ["select conrelid::regclass::text tbl, conname, pg_get_constraintdef(oid) def from pg_constraint where contype='f' and (confrelid='public.phala_anchors'::regclass or conrelid='public.phala_anchors'::regclass) order by 1,2"],
 'discoveries_top100_static': [f"select discovery_subsystem, count(*) from (select discovery_subsystem from bodha_discoveries where chart_id={C} order by composite_discovery_rank desc nulls last limit 100) x group by 1"],
 'ph_integrity_sql_results': None,
}
out = {'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'role': 'suvarna_reader (read-only; default_transaction_read_only=on)', 'queries': {}}
for k, v in Q.items():
    if v is None: continue
    out['queries'][k] = {'sql': v[0], 'result': q(v[0])}
reg = {}
for a in ['ph_nimitta','ph_muhurta','ph_sodhana','ph_pratikara','ph_suddha_sodhana','ph_sankrama','ph_pramana','ph_phaladesa','ph_rectification']:
    d = json.load(open(f'data/{a}.json'))
    reg[a] = d.get('integrity_check_result')
out['queries']['ph_integrity_sql_results'] = {'sql': 'asset_registry.integrity_check_sql executed as written (read-only)', 'result': reg}
json.dump(out, open('upstream_receipts.json', 'w'), indent=1, default=str)
print(len(out['queries']), 'named queries')
