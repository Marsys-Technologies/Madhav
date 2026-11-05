#!/usr/bin/env python3
"""A.L5 read-only fact queries (suvarna_reader, read-only session via q.sh). Output: facts.json {id: {sql, rows}}."""
import json, subprocess, re
C = '482012f1-710e-4a25-994a-93821f5871aa'
A = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
Q = '/Users/Dev/suvarna-evidence/A_L5/q.sh'
def q(sql):
    r = subprocess.run([Q, sql], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().split('\n')
    if out and out[0].startswith('ERROR'): return {'error': '\n'.join(out)[:300]}
    if len(out) < 2: return []
    hdr = out[0].split('|'); res = []
    for ln in out[1:]:
        if re.match(r'^\(\d+ rows?\)$', ln): continue
        res.append(dict(zip(hdr, ln.split('|'))))
    return res
QS = {}
def add(i, s): QS[i] = s
# LEL
add('le_basic', f"select count(*) n, min(recorded_at) rec_min, max(recorded_at) rec_max, count(*) filter (where recorded_at <= '2000-01-01') at_sentinel, count(*) filter (where recorded_at > '2026-08-13 01:16:29+00') after_emission, count(*) filter (where outcome_observed is true) outcome_true, count(*) filter (where outcome_observed is null) outcome_null, count(*) filter (where pool_consent) consent, count(distinct event_id) ids from life_events where chart_id='{C}'")
add('le_by_chart', "select chart_id::text, count(*) from life_events group by 1 order by 2 desc")
add('le_dates', f"select count(*) filter (where event_date is null) nodate, max(event_date) latest_event_date, count(*) filter (where event_date > current_date) future from life_events where chart_id='{C}'")
add('le_recorded_hist', f"select date_trunc('month', recorded_at)::date m, count(*) from life_events where chart_id='{C}' group by 1 order by 1")
add('le_missing_cols', "select count(*) from information_schema.columns where table_name='life_events' and column_name in ('shaped_predictor','shaped_predictor_refs','disclosure_timing','disclosure_type','disclosure_date','event_magnitude','magnitude','subcategory','attestation_source','event_class')")
# provenance
add('prov', f"select count(*) n, count(*) filter (where admissible_clean) clean, count(*) filter (where held_out) held, count(*) filter (where held_out and admissible_clean) held_clean, count(distinct admissibility_reason) reasons, min(admissibility_reason) reason, count(*) filter (where event_class_id is not null) cls, count(*) filter (where event_magnitude is not null) mag from mimamsa_event_provenance where chart_id='{C}'")
add('prov_heldout_chrono', f"select e.held_out, count(*) n, max(e.event_date) latest_event_date, count(*) filter (where e.event_date < (select max(x.event_date) from mimamsa_event_provenance x where x.chart_id=e.chart_id and not x.held_out)) earlier_than_latest_training from mimamsa_event_provenance e where chart_id='{C}' group by 1")
add('prov_vs_le_ids', f"select (select count(*) from mimamsa_event_provenance p where p.chart_id='{C}') prov, (select count(*) from life_events l where l.chart_id='{C}') le, (select count(*) from mimamsa_event_provenance p where p.chart_id='{C}' and not exists (select 1 from life_events l where l.chart_id=p.chart_id and l.event_id=p.event_id)) prov_without_le, (select count(*) from life_events l where l.chart_id='{C}' and not exists (select 1 from mimamsa_event_provenance p where p.chart_id=l.chart_id and p.event_id=l.event_id)) le_without_prov")
add('prov_domain', f"select domain_primary, count(*) from mimamsa_event_provenance where chart_id='{C}' group by 1 order by 2 desc")
# kula
add('fam', "select family_id, evidence_tier, calibration_status, default_state, prior_weight, is_active from mimamsa_signal_families order by 1")
add('ctrl', "select control_id, expected_score, tolerance from mimamsa_negative_controls order by 1")
add('priors', "select signal_type_class, source_subsystem, class_prior, prior_version from brahma_class_priors where prior_version='1.0' and signal_tradition='*' and fact_kind='*' order by 1,2")
# bhavisya
add('pred_summary', f"select count(*) n, count(distinct prediction_id) pid, min(emitted_at) e_min, max(emitted_at) e_max, count(*) filter (where lifecycle_status='pending') pending, count(*) filter (where chart_context_stale_at is not null) stale from mimamsa_predictions where chart_id='{C}'")
add('pred_window', f"select count(*) filter (where upper(observation_window) <= emitted_at::date) window_ended_before_emit, count(*) filter (where lower(observation_window) <= emitted_at::date and upper(observation_window) > emitted_at::date) straddles_emission, count(*) filter (where lower(observation_window) > emitted_at::date) fully_future, min(lower(observation_window)) w_min, max(upper(observation_window)) w_max from mimamsa_predictions where chart_id='{C}'")
add('pred_live_anchor', f"select count(*) preds, count(*) filter (where exists (select 1 from phala_anchors a where a.chart_id=p.chart_id and a.anchor_id::text=p.source_pramana_id)) with_live_anchor from mimamsa_predictions p where chart_id='{C}'")
add('pred_driving_live', f"with d as (select p.prediction_id, (x->>'signal_id') sid from mimamsa_predictions p, jsonb_array_elements(p.driving_signals) x where p.chart_id='{C}') select count(*) refs, count(distinct sid) distinct_sids, count(*) filter (where exists (select 1 from bodha_msr_signals s where s.chart_id='{C}' and s.signal_id::text=d.sid)) resolving from d")
add('pred_bundle_hash', f"select count(*) n, count(distinct frozen_bundle_hash) h, count(*) filter (where bundle_formula_version is null) nov from mimamsa_predictions where chart_id='{C}'")
add('pred_conf_gen', f"select count(*) filter (where confidence_band='[0.4,0.7)') default_band, count(distinct confidence_band::text) distinct_bands from mimamsa_predictions where chart_id='{C}'")
add('pred_cols_missing', "select column_name from information_schema.columns where table_name='mimamsa_predictions' order by ordinal_position")
add('mset', f"select count(*), count(distinct channel_id), min(source), max(source) from mimamsa_manifestation_sets where chart_id='{C}'")
add('mset_channels', f"select channel_id, count(*) from mimamsa_manifestation_sets where chart_id='{C}' group by 1 order by 2 desc")
# pramana
add('cal_summary', f"select count(*) n, count(distinct prediction_id) preds, count(distinct event_id) events, min(scored_at) s_min, max(scored_at) s_max, count(*) filter (where leakage_status='clean') clean_lk, count(*) filter (where base_rate is not null) base_nn, count(distinct base_rate) base_d, count(*) filter (where manifestation_channel is not null) chan_nn from mimamsa_calibration where chart_id='{C}'")
add('cal_retro', f"select count(*) joined, count(*) filter (where e.event_date < p.emitted_at::date) event_date_before_emit, count(*) filter (where l.recorded_at < p.emitted_at) recorded_before_emit, count(*) filter (where e.event_date >= p.emitted_at::date) event_date_on_or_after_emit from mimamsa_calibration c join mimamsa_predictions p on p.chart_id=c.chart_id and p.prediction_id=c.prediction_id join mimamsa_event_provenance e on e.chart_id=c.chart_id and e.event_id=c.event_id left join life_events l on l.chart_id=e.chart_id and l.event_id=e.event_id where c.chart_id='{C}'")
add('cal_domain_pair', f"select p.domain pred_domain, e.domain_primary ev_domain, count(*) n from mimamsa_calibration c join mimamsa_predictions p on p.chart_id=c.chart_id and p.prediction_id=c.prediction_id join mimamsa_event_provenance e on e.chart_id=c.chart_id and e.event_id=c.event_id where c.chart_id='{C}' group by 1,2 order by 3 desc")
add('cal_verdict', f"select composite_verdict, count(*), min(composite_score), max(composite_score), round(avg(score_timing)::numeric,3) t, min(score_magnitude) magmin, max(score_magnitude) magmax, min(score_falsifier) fmin, max(score_falsifier) fmax from mimamsa_calibration where chart_id='{C}' group by 1 order by 1")
add('cal_orphan_event', f"select count(*) from mimamsa_calibration c where c.chart_id='{C}' and not exists (select 1 from mimamsa_event_provenance e where e.chart_id=c.chart_id and e.event_id=c.event_id)")
add('rel', f"select stratum_key, n, observed_rate, held_out_validity, evidence_grade, ece, ci_low from mimamsa_reliability where chart_id='{C}' order by 1")
# gunanaka
add('mult', f"select weight_id, target_ref, n_observations, held_out_validity, promotion_status, gate_passed, confidence_high, neg_control_clear, kill_switch_state, raw_multiplier, applied_multiplier, divergence_from_classical from mimamsa_multipliers where chart_id='{C}' order by 1")
add('snap', f"select snapshot_id, publication_status, two_key_complete, proposing_executor, created_at from mimamsa_calibration_snapshot where chart_id='{C}' order by created_at")
# adhilepa
add('adh_counts', f"select (select count(*) from mimamsa_signal_adjustment where chart_id='{C}') sig, (select count(*) from mimamsa_fact_adjustment where chart_id='{C}') fact, (select count(*) from mimamsa_convergence_adjustment where chart_id='{C}') conv, (select count(*) from mimamsa_anchor_adjustment where chart_id='{C}') anc, (select count(*) from mimamsa_load_bearing where chart_id='{C}') lb")
add('adh_sig_live', f"select count(*) rows, count(*) filter (where exists (select 1 from bodha_msr_signals s where s.chart_id=a.chart_id and s.signal_id::text=a.origin_id)) resolving, count(distinct weight_id) weights, count(*) filter (where applies_to_reading) applies, count(*) filter (where evidence_n=0) n0, count(*) filter (where leakage_status='not_assessed') lk_na from mimamsa_signal_adjustment a where chart_id='{C}'")
add('adh_fact_live', f"select count(*) rows, count(*) filter (where exists (select 1 from chart_facts f where f.chart_id=a.chart_id and f.fact_id::text=a.origin_id)) resolving, count(distinct weight_id) weights from mimamsa_fact_adjustment a where chart_id='{C}'")
add('adh_conv_live', f"select count(*) rows, count(*) filter (where exists (select 1 from kala_convergence k where k.chart_id=a.chart_id and k.convergence_id::text=a.origin_id)) resolving, (select count(*) from kala_convergence where chart_id='{C}') live_conv from mimamsa_convergence_adjustment a where chart_id='{C}'")
add('adh_anc_live', f"select count(*) rows, count(*) filter (where exists (select 1 from phala_anchors k where k.chart_id=a.chart_id and k.anchor_id::text=a.origin_id)) resolving from mimamsa_anchor_adjustment a where chart_id='{C}'")
add('adh_lb', f"select conclusion_id, signal_id, sensitivity, role from mimamsa_load_bearing where chart_id='{C}' order by sensitivity desc")
add('adh_w', f"select weight_id, multiplier, evidence_n, count(*) from mimamsa_signal_adjustment where chart_id='{C}' group by 1,2,3 order by 4 desc")
add('msr_now', f"select count(*), max(computed_at) from bodha_msr_signals where chart_id='{C}'")
add('facts_now', f"select count(*) from chart_facts where chart_id='{C}'")
# pariksha
add('qa', f"select check_type, status, count(*) from mimamsa_qa_eval where chart_id='{C}' group by 1,2 order by 1,2")
add('attr', f"select count(*) n, count(distinct match_id) matches, count(distinct signal_id) sigs, count(distinct family_id) fams, min(credit_blame), max(credit_blame) from mimamsa_attribution where chart_id='{C}'")
add('attr_sig_live', f"select count(distinct signal_id) sigs, count(distinct signal_id) filter (where exists (select 1 from bodha_msr_signals s where s.chart_id='{C}' and s.signal_id::text=a.signal_id)) resolving from mimamsa_attribution a where chart_id='{C}'")
add('disc', f"select discovery_class, activation_status, count(*), min(n_support), max(n_support), min(strength), max(strength) from mimamsa_discoveries where chart_id='{C}' group by 1,2")
add('disc_scored', f"select count(*) filter (where (evidence_refs->>'n_scored_matches')::int > 0) with_scored, max((evidence_refs->>'n_scored_matches')::int) max_scored from mimamsa_discoveries where chart_id='{C}' and discovery_class='emergent_law'")
add('disc_retro', f"select count(*) n, count(*) filter (where n_support=0) zero_anchor, count(*) filter (where (evidence_refs->>'cutoff_enforced') = 'false') cutoff_false from mimamsa_discoveries where chart_id='{C}' and discovery_class='retrodiction'")
# sambandha
add('gram', f"select evidence_grade, count(*), sum(opportunity_count) opp, sum(scored_count) scored, sum(fire_count) fire, count(channel_propensity) prop_nn from mimamsa_manifestation_grammar where chart_id='{C}' group by 1")
add('gram_prior', f"select channel_id, domain, prior_propensity, opportunity_count, scored_count, evidence_grade from mimamsa_manifestation_grammar where chart_id='{C}' order by opportunity_count desc, channel_id limit 12")
add('gram_prior_dist', f"select prior_propensity, count(*) from mimamsa_manifestation_grammar where chart_id='{C}' group by 1 order by 2 desc")
add('mset_vs_opp', f"select (select count(*) from mimamsa_manifestation_sets where chart_id='{C}') sets, (select coalesce(sum(opportunity_count),0) from mimamsa_manifestation_grammar where chart_id='{C}') opp_sum")
# darshana
add('ins', f"select insight_type, evidence_grade, leakage_status, count(*), min(rank_consequence), max(rank_consequence) from mimamsa_insight_units where chart_id='{C}' group by 1,2,3 order by 1,2")
add('ins_emb', f"select (select count(*) from mimamsa_insight_embeddings where chart_id='{C}') emb, (select count(*) from mimamsa_insight_units where chart_id='{C}') units")
add('views', "select table_name from information_schema.views where table_name like 'vw_mimamsa%' order by 1")
add('ins_lb', f"select statement from mimamsa_insight_units where chart_id='{C}' and insight_type='load_bearing' limit 2")
add('ins_cal', f"select statement, evidence_grade from mimamsa_insight_units where chart_id='{C}' and insight_type='calibrated_outlook' order by insight_id limit 3")
# services
add('exp', "select count(*) from mimamsa_export_log")
add('pref', "select count(*) from mimamsa_preferences")
add('jrn', "select count(*), count(distinct chart_id) from mimamsa_journal")
add('ledger', "select count(*), count(distinct chart_id) from mimamsa_intervention_ledger")
add('ledger_cols', "select column_name from information_schema.columns where table_name='mimamsa_intervention_ledger' order by ordinal_position")
# bhara
add('skill', f"select event_class, n_events, n_prospective, n_backfill, skill_score, skill_state, skill_prospective, null_replicates from kala_field_skill where chart_id='{C}' order by 1")
add('gof', f"select event_class, n, gof_state, ks_p from kala_field_gof where chart_id='{C}' order by 1")
add('wv', "select version_id, status, scope, fitted_from_chart_id::text, activated_at from kala_field_weight_versions")
add('kfw', f"select count(*) from kala_field_weights where chart_id='{C}'")
add('kins', f"select count(*), count(*) filter (where lel_derived) lel_derived from kala_insights where chart_id='{C}'")
add('kfield', f"select (select count(*) from kala_field where chart_id='{C}') kala_field_rows")
# ledgers
add('pl', f"select lifecycle_status, count(*) from brahma_prospective_ledger where chart_id='{C}' group by 1")
add('mpl', f"select lifecycle_status, count(*) from brahma_mimamsa_prediction_ledger where chart_id='{C}' group by 1")
add('pl_cols', "select column_name from information_schema.columns where table_name='brahma_prospective_ledger' order by ordinal_position")
# other charts
add('other_charts', f"select 'predictions' t, chart_id::text, count(*) from mimamsa_predictions group by 2 union all select 'calibration', chart_id::text, count(*) from mimamsa_calibration group by 2 union all select 'provenance', chart_id::text, count(*) from mimamsa_event_provenance group by 2 union all select 'insight_units', chart_id::text, count(*) from mimamsa_insight_units group by 2 order by 1,3 desc")
# throughput + runs
add('tp', f"select asset_id, state, rows_written, last_built_at, left(coalesce(last_error,''),90) err, built_against_writer_hash from asset_throughput where chart_id='{C}' and (asset_id like 'mi\\_%' or asset_id='lel_events') order by 1")
add('runs', "select asset_id, state, count(*) from build_run_assets where asset_id like 'mi\\_%' group by 1,2 order by 1,2")
add('lastrun', f"select distinct on (b.asset_id) b.asset_id, b.state, b.started_at, left(coalesce(b.error,''),130) err from build_run_assets b join build_runs r on r.id=b.run_id where b.asset_id like 'mi\\_%' and r.chart_id='{C}' and b.state in ('complete','error','aborted') order by b.asset_id, b.started_at desc nulls last")
add('regrow', "select asset_id, storage_type, catalog_status, has_substeps, writer_timeout_seconds, data_disposition, natural_key_partition, left(count_sql,160) count_sql, left(coalesce(integrity_check_sql,''),200) integrity, service_health from asset_registry where layer='mimamsa' order by 1")
add('blast', "select u as upstream, array_agg(asset_id order by asset_id) downstream from (select asset_id, unnest(depends_on) u from asset_registry where is_active) x where u like 'mi\\_%' or u='lel_events' group by 1 order by 1")
out = {}
for k, s in QS.items():
    out[k] = {'sql': s, 'rows': q(s)}
json.dump(out, open('/Users/Dev/suvarna-evidence/A_L5/facts.json', 'w'), indent=1, default=str)
print('queries', len(out), 'errors', [k for k, v in out.items() if isinstance(v['rows'], dict)])
