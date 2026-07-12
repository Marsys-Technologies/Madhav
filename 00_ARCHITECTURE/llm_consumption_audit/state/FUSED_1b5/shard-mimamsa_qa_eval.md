# FUSED Lane 1b+5 shard — mimamsa_qa_eval (12 families)

Channel (path-level): served-only-by-down-pipeline. No surgical MCP tool (0 manifest mappings; 0 route.ts refs; absent from ALIVE + DEAD-19 lists). QA-eval results are internal L5 verifier output; served only via the L5 compute/full-pipeline path, never as a per-chart surgical retrieval.
DB truth: `SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id=<A>`=141 (Abhisek), `<B>`=6 (Abhinandan). Populated. Columns: chart_id, check_id, check_type, target, result_score, status, detail, checked_at.
Wire probe: NONE possible — no surgical tool. Lane 5 four failure modes un-testable (no wire value to diff).
Derivation: path-grade(exemplar=result_score[VF-2456]) + member-confirmation (all 12 families — 8 columns + 4 check_type value-partitions — share identical channel; same absent-surgical-tool condition). heterogeneity_escalated=false.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| chart_id (VF-2452) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated (141/6) | N/A — no wire path; diff un-exercisable | path-grade(exemplar=result_score) + member-confirmation |
| check_id (VF-2453) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| check_type (VF-2454) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| target (VF-2455) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| result_score (VF-2456) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade(exemplar) + member-confirmation |
| status (VF-2457) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| detail (VF-2458) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| checked_at (VF-2459) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| check_type=tail_only (VF-2940) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; present both charts | N/A — no wire path | path-grade + member-confirmation |
| check_type=degenerate_distribution (VF-2941) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; present both charts | N/A — no wire path | path-grade + member-confirmation |
| check_type=negative_control (VF-2942) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; present both charts | N/A — no wire path | path-grade + member-confirmation |
| check_type=control_window (VF-2943) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; Abhisek-only | N/A — no wire path | path-grade + member-confirmation |
