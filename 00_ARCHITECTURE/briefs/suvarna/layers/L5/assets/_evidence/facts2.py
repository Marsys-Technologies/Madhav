#!/usr/bin/env python3
"""A.L5 follow-up read-only fact queries (join formulations that avoid correlated casts). Output: facts2.json."""
import json, subprocess, re
C = '482012f1-710e-4a25-994a-93821f5871aa'
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
QS = {
 'adh_sig_live': f"select count(*) rows_total, count(s.signal_id) resolving from mimamsa_signal_adjustment a left join bodha_msr_signals s on s.chart_id=a.chart_id and s.signal_id::text = a.origin_id where a.chart_id='{C}'",
 'adh_fact_live': f"select count(*) rows_total, count(f.fact_id) resolving from mimamsa_fact_adjustment a left join chart_facts f on f.chart_id=a.chart_id and f.fact_id::text = a.origin_id where a.chart_id='{C}'",
 'adh_conv_live': f"select count(*) rows_total, (select count(*) from kala_convergence where chart_id='{C}') live_convergence_rows, count(k.convergence_id) resolving from mimamsa_convergence_adjustment a left join kala_convergence k on k.chart_id=a.chart_id and k.convergence_id::text = a.origin_id where a.chart_id='{C}'",
 'adh_anc_live': f"select count(*) rows_total, count(k.anchor_id) resolving from mimamsa_anchor_adjustment a left join phala_anchors k on k.chart_id=a.chart_id and k.anchor_id::text = a.origin_id where a.chart_id='{C}'",
 'attr_sig_live': f"select count(distinct a.signal_id) sigs, count(distinct s.signal_id) resolving from mimamsa_attribution a left join bodha_msr_signals s on s.chart_id=a.chart_id and s.signal_id::text = a.signal_id where a.chart_id='{C}'",
 'pred_driving_live': f"with d as (select (x->>'signal_id') sid from mimamsa_predictions p, jsonb_array_elements(p.driving_signals) x where p.chart_id='{C}') select count(*) refs, count(distinct d.sid) distinct_sids, count(s.signal_id) resolving from d left join bodha_msr_signals s on s.chart_id='{C}' and s.signal_id::text=d.sid",
 'gun_n': f"select x->>'family_id' fam, count(*) pairs, count(distinct c.match_id) matches, count(distinct c.prediction_id) preds, count(distinct c.event_id) events from mimamsa_calibration c join mimamsa_predictions p on p.chart_id=c.chart_id and p.prediction_id=c.prediction_id and p.chart_context_stale_at is null, jsonb_array_elements(p.driving_signals) x where c.chart_id='{C}' group by 1 order by 2 desc",
 'cal_leaked': f"select count(*) from mimamsa_calibration where chart_id='{C}' and leakage_status='leaked'",
 'snap': f"select snapshot_id, publication_status, two_key_complete, proposing_executor from mimamsa_calibration_snapshot where chart_id='{C}' order by snapshot_id",
 'rel_ok': f"select stratum_key, n, observed_rate, held_out_validity, evidence_grade, brier_score from mimamsa_reliability where chart_id='{C}' order by predicted_prob_bin::text",
 'disc_versions': f"select discovery_formula_ver, discovery_class, count(*), count(evidence_refs->'n_scored_matches') has_scored, count(evidence_refs->'cutoff_enforced') has_cutoff from mimamsa_discoveries where chart_id='{C}' group by 1,2",
 'ins_versions': f"select insight_type, evidence_grade, surface_formula_version, count(*), count(provenance_chain->'grade_basis') has_basis from mimamsa_insight_units where chart_id='{C}' group by 1,2,3 order by 1,2",
 'retro_statements': f"select count(*) filter (where statement ilike 'Blind retrodiction%') blind_claim, count(*) from mimamsa_discoveries where chart_id='{C}' and discovery_class='retrodiction'",
 'gram_empirical': f"select channel_id, fire_count, opportunity_count, scored_count, channel_propensity, prior_propensity, evidence_grade from mimamsa_manifestation_grammar where chart_id='{C}' and evidence_grade='empirical' order by channel_id",
 'gram_opp_vs_sets': f"select (select count(*) from mimamsa_manifestation_sets where chart_id='{C}') sets, (select sum(opportunity_count) from mimamsa_manifestation_grammar where chart_id='{C}') opp_sum",
 'cal_retro': f"select count(*) joined, count(*) filter (where e.event_date < p.emitted_at::date) event_date_before_emit, count(*) filter (where l.recorded_at < p.emitted_at) recorded_before_emit from mimamsa_calibration c join mimamsa_predictions p on p.chart_id=c.chart_id and p.prediction_id=c.prediction_id join mimamsa_event_provenance e on e.chart_id=c.chart_id and e.event_id=c.event_id left join life_events l on l.chart_id=e.chart_id and l.event_id=e.event_id where c.chart_id='{C}'",
 'unresolved_in_bins': f"select count(*) filter (where composite_verdict='UNRESOLVED') unresolved, count(*) total from mimamsa_calibration where chart_id='{C}'",
 'pred_live_anchor': f"select count(*) preds, count(a.anchor_id) with_live_anchor from mimamsa_predictions p left join phala_anchors a on a.chart_id=p.chart_id and a.anchor_id::text=p.source_pramana_id where p.chart_id='{C}'",
 'anchors_now': f"select count(*), min(computed_at) from phala_anchors where chart_id='{C}'",
 'msr_ids_now': f"select count(*), max(computed_at) from bodha_msr_signals where chart_id='{C}'",
 'kfw_cols': "select count(*) from kala_field_weights",
 'cal_controls_cols': "select count(*) filter (where last_harness_score is not null) harness_scored from mimamsa_negative_controls",
 'le_corr_8': f"select count(*) from life_events where chart_id='{C}' and date_tightened_at is not null",
 'journal_all': "select count(*) rows_all, count(distinct chart_id) charts from mimamsa_journal",
 'prospective_ledger': f"select lifecycle_status, count(*) from brahma_prospective_ledger where chart_id='{C}' group by 1",
 'activation_basis': f"select count(*) total_matches, count(*) filter (where composite_verdict in ('CONFIRMED','PARTIAL','REFUTED')) adjudicated, count(distinct prediction_id) distinct_predictions from mimamsa_calibration where chart_id='{C}'",
}
out = {k: {'sql': s, 'rows': q(s)} for k, s in QS.items()}
json.dump(out, open('/Users/Dev/suvarna-evidence/A_L5/facts2.json', 'w'), indent=1, default=str)
print('queries', len(out), 'errors', [k for k, v in out.items() if isinstance(v['rows'], dict)])
