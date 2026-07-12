# FUSED Lane 1b + Lane 5 shard — mimamsa_insight_units

channel: served-only-by-down-pipeline
families_total: 58
exemplar_family: insight_id
heterogeneity_escalated: false (all families are columns/value-partitions of ONE table sharing ONE retrieval path; path-grade valid)
members_sampled: 8

retrievability_verdict (Lane 1b): REACHABLE-VIA-FULL-PIPELINE-ONLY (query_insights built + reads this table but EXCLUDED from surgical whitelist; wire 200 rejects with class:validation "Tool not in surgical whitelist: query_insights" -> ask_madhav full-pipeline only). Data present: 74 rows Abhisek / 30 Abhinandan.

fidelity_verdict (Lane 5): NOT-TESTABLE (no surgical wire value obtainable; surgical channel blocked). DB-truth captured: verdict_object rows e.g. verdict_marriage rank_consequence=0.092 confidence_band=[0.09,0.29). Fidelity via ask_madhav is LLM-synthesis, not a deterministic value diff -> deferred.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| chart_id (VF-2338) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| insight_id (VF-2339) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade EXEMPLAR(insight_id) |
| insight_type (VF-2340) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain (VF-2341) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| horizon (VF-2342) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens (VF-2343) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| statement (VF-2344) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| rank_consequence (VF-2345) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| confidence_band (VF-2346) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| n_support (VF-2347) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| leakage_status (VF-2348) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| evidence_grade (VF-2349) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| freshness_lel_version (VF-2350) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| last_calibrated_at (VF-2351) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| provenance_chain (VF-2352) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| is_negative_knowledge (VF-2353) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| surface_formula_version (VF-2354) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| updated_at (VF-2355) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=family (VF-2880) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=health (VF-2881) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=career (VF-2882) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=wealth (VF-2883) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=progeny (VF-2884) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=spirituality (VF-2885) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=residence (VF-2886) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=education (VF-2887) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=travel (VF-2888) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=transition (VF-2889) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| domain=relationship (VF-2890) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| evidence_grade=structural (VF-2891) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| evidence_grade=empirical (VF-2892) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| evidence_grade=prior_only (VF-2893) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| insight_type=retrodiction (VF-2894) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| insight_type=manifestation_grammar (VF-2895) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| insight_type=verdict_object (VF-2896) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| insight_type=load_bearing (VF-2897) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=property_acquisition (VF-2898) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=chronic_onset (VF-2899) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=illness_acute (VF-2900) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=career_advancement (VF-2901) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=surgery (VF-2902) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=exam_outcome (VF-2903) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=major_loss (VF-2904) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=business_launch (VF-2905) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=major_gain (VF-2906) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=career_entry (VF-2907) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=career_change (VF-2908) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=foreign_settlement (VF-2909) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=spiritual_turn (VF-2910) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=career_setback (VF-2911) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=parental_event (VF-2912) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=education_milestone (VF-2913) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=relocation (VF-2914) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=marriage (VF-2915) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=separation (VF-2916) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=childbirth (VF-2917) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=bereavement (VF-2918) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
| question_lens=romantic_start (VF-2919) | served-only-by-down-pipeline | REACHABLE-FULL-PIPELINE-ONLY | NOT-TESTABLE | path-grade(exemplar=insight_id) + member-confirmation |
