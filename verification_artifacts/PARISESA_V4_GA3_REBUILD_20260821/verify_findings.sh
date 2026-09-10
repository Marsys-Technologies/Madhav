#!/usr/bin/env bash
# PARIŚEṢA-V4 GA-3 — each finding's own live reproducer, with the PASS condition
# stated as a predicate the query itself evaluates. Run identically before and after.
set -uo pipefail
CHART=482012f1-710e-4a25-994a-93821f5871aa
export PGPASSWORD=$(cat /tmp/.pgpw)
Q() { psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -P pager=off -tAc "$1"; }

echo "=============== $(date -u +%Y-%m-%dT%H:%M:%SZ) — chart $CHART ==============="

echo
echo "--- F-104  mi_darshana leakage_status: PASS iff 0 rows read 'clean' ---"
Q "select 'clean='||count(*) filter (where leakage_status='clean')
        ||'  not_assessed='||count(*) filter (where leakage_status='not_assessed')
        ||'  total='||count(*)
        ||'  => '||case when count(*) filter (where leakage_status='clean')=0
                       then 'PASS' else 'FAIL' end
     from mimamsa_insight_units where chart_id='$CHART'"

echo
echo "--- F-35  scored_count gate: PASS iff 0 rows are 'empirical' with scored_count<5 ---"
Q "select 'empirical='||count(*) filter (where evidence_grade='empirical')
        ||'  assignment_only='||count(*) filter (where evidence_grade='assignment_only')
        ||'  prior_only='||count(*) filter (where evidence_grade='prior_only')
        ||'  unearned_empirical='||count(*) filter (where evidence_grade='empirical' and coalesce(scored_count,0)<5)
        ||'  => '||case when count(*) filter (where evidence_grade='empirical' and coalesce(scored_count,0)<5)=0
                       then 'PASS' else 'FAIL' end
     from mimamsa_manifestation_grammar where chart_id='$CHART'"

echo
echo "--- F-116  bo_upaya preamble strip: PASS iff every row carries the flag AND 0 labels retain 'For ...:' ---"
Q "select 'total='||count(*)
        ||'  with_flag='||count(*) filter (where prescription_detail_jsonb ? 'preamble_stripped')
        ||'  still_preambled='||count(*) filter (where remedy_label_human like 'For %:%')
        ||'  => '||case when count(*) filter (where prescription_detail_jsonb ? 'preamble_stripped')=count(*)
                         and count(*) filter (where remedy_label_human like 'For %:%')=0
                       then 'PASS' else 'FAIL' end
     from bodha_rm_remedy_prescriptions where chart_id='$CHART'"

echo
echo "--- F-71  mi_bhara: PASS iff state<>'error' and no TypeError remains ---"
Q "select 'state='||state||'  rows='||coalesce(rows_written,0)
        ||'  err='||case when coalesce(last_error,'')='' then '(none)'
                        else left(replace(last_error,chr(10),'|'),80) end
        ||'  => '||case when state<>'error' and coalesce(last_error,'')=''
                       then 'PASS' else 'FAIL' end
     from asset_throughput where chart_id='$CHART' and asset_id='mi_bhara'"
echo "    (crash precondition, independent of build state — expect 0)"
Q "select 'open_predictions_with_empty_window='||count(*)
     from mimamsa_predictions
    where chart_id='$CHART' and lifecycle_status='open'
      and observation_window is not null and isempty(observation_window)"

echo
echo "--- F-63  ga_panchanga special-yoga key: PASS iff 0 rows read 'unknown' (PARKED — expect FAIL) ---"
Q "select 'unknown_rows='||count(*)
        ||'  => '||case when count(*)=0 then 'PASS' else 'FAIL (packet parked, expected)' end
     from chart_facts
    where chart_id='$CHART' and fact_key='combination_name' and fact_value_text='unknown'"

echo
echo "--- F-143 (NOT fixed by this rebuild; recorded so the ledger is accurate either way) ---"
echo "    discoveries with n_support>=5 that mi_darshana.py:226 grades 'empirical' unearned:"
Q "select 'n_support_ge_5='||count(*) filter (where coalesce(n_support,0)>=5)||' of '||count(*)
     from mimamsa_discoveries where chart_id='$CHART'"
Q "select 'insight_units_empirical='||count(*) filter (where evidence_grade='empirical')||' of '||count(*)
     from mimamsa_insight_units where chart_id='$CHART'"

echo
echo "--- build-state snapshot for the four in-scope assets ---"
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -P pager=off -c \
 "select asset_id, state, rows_written, last_built_at
    from asset_throughput
   where chart_id='$CHART'
     and asset_id in ('mi_sambandha','mi_darshana','mi_bhara','bo_upaya','ga_panchanga')
   order by asset_id"
