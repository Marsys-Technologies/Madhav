# FUSED Lane 1b + Lane 5 shard — mimamsa_journal

channel: truly-UNREACHABLE
families_total: 9
exemplar_family: journal_id
heterogeneity_escalated: false (all families are columns/value-partitions of ONE table sharing ONE retrieval path; path-grade valid)
members_sampled: 8

retrievability_verdict (Lane 1b): UNREACHABLE + DATA-PLANE-EMPTY: 0 rows for ALL charts; no retrieval tool serves it. Native prediction->answer feedback journal (write-side); empty because no journaling has occurred (by-design-empty).

fidelity_verdict (Lane 5): NOT-TESTABLE (0 rows + no tool). SELECT count(*)=0 globally.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| chart_id (VF-2356) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| journal_id (VF-2357) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade EXEMPLAR(journal_id) |
| prediction_id (VF-2358) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| prompt_shown (VF-2359) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| native_answer (VF-2360) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| answered_at (VF-2361) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| resulting_event_id (VF-2362) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| provenance_tag (VF-2363) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
| created_at (VF-2364) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=journal_id) + member-confirmation |
