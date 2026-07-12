# FUSED Lane 1b + Lane 5 shard — mimamsa_export_log

channel: truly-UNREACHABLE
families_total: 12
exemplar_family: export_id
heterogeneity_escalated: false (all families are columns/value-partitions of ONE table sharing ONE retrieval path; path-grade valid)
members_sampled: 8

retrievability_verdict (Lane 1b): UNREACHABLE + DATA-PLANE-EMPTY: table has 0 rows for ALL charts; NO retrieval tool serves it. Operational export-audit log (write-side); empty because no export flow has run for these charts (likely by-design-empty, not a consumption surface).

fidelity_verdict (Lane 5): NOT-TESTABLE (0 rows + no tool). SELECT count(*)=0 globally.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| export_id (VF-2307) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade EXEMPLAR(export_id) |
| chart_id (VF-2308) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| exported_at (VF-2309) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| export_format (VF-2310) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| recipient_ref (VF-2311) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| included_insight_ids (VF-2312) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| contribution_state (VF-2313) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| calibration_mode (VF-2314) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| disclosures_attached (VF-2315) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| payload_hash (VF-2316) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| lel_version (VF-2317) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
| export_formula_version (VF-2318) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=export_id) + member-confirmation |
