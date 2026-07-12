# FUSED Lane 1b+5 shard — mimamsa_reliability (15 families)

Channel (path-level): served-only-by-down-pipeline. No surgical MCP tool (0 manifest mappings; 0 route.ts refs; absent from ALIVE + DEAD-19). Calibration-reliability table; served only via L5 compute path.
DB truth: `SELECT count(*) FROM mimamsa_reliability WHERE chart_id=<A>`=0, `<B>`=0. EMPTY on BOTH charts. Per CLAUDE.md §E, L5 sealed in STRUCTURAL mode — empirical calibration (reliability/Brier/ECE/observed_rate) fills in as prediction→outcome data accrues. Empty is BY DESIGN, not unfinished. Columns: chart_id, stratum_key, predicted_prob_bin, observed_rate, n, ci_low, ci_high, brier_score, log_loss, ece, hit_rate_by_tier, held_out_validity, evidence_grade, calibration_formula_ver, computed_at.
Wire probe: NONE possible — no surgical tool AND no rows. Lane 5 four failure modes un-testable.
Derivation: path-grade(exemplar=observed_rate[VF-2463]) + member-confirmation (all 15 families identical channel; same empty-by-design data-plane state). heterogeneity_escalated=false.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| chart_id (VF-2460) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY 0/0 (STRUCTURAL-seal by design) | N/A — no wire path; no rows | path-grade(exemplar=observed_rate) + member-confirmation |
| stratum_key (VF-2461) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| predicted_prob_bin (VF-2462) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| observed_rate (VF-2463) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade(exemplar) + member-confirmation |
| n (VF-2464) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| ci_low (VF-2465) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| ci_high (VF-2466) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| brier_score (VF-2467) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| log_loss (VF-2468) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| ece (VF-2469) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| hit_rate_by_tier (VF-2470) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| held_out_validity (VF-2471) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| evidence_grade (VF-2472) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| calibration_formula_ver (VF-2473) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
| computed_at (VF-2474) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; EMPTY 0/0 by design | N/A — no wire path | path-grade + member-confirmation |
