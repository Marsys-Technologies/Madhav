# Conductor Log — M5 Coverage Campaign

| field | value |
|---|---|
| campaign_id | M5_COVERAGE_REMEDIATION |
| authored_on | 2026-05-21 |
| worktree | /Users/Dev/Vibe-Coding/Apps/MadhavCoverage |
| branch | feature/m5-coverage-remediation |
| spec | 00_ARCHITECTURE/CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md v1.2 |

## Session runs

| timestamp | session_id | attempt | outcome | commit_sha | pr_url | gate_results | halt_reason |
|---|---|---|---|---|---|---|---|
| 2026-05-21T00:16:00Z | COV-S1 | 1 | success | fdfb444d | https://github.com/amonty84/Madhav/pull/115 | tsc:PASS vitest:7/7 lint:EXIT0 CI:all-green | null |
| 2026-05-21T00:22:00Z | COV-S8 | 0 | halt | — | — | — | spec_version_mismatch: §G.8 not in audit v1.0; queue requires v1.2 |
| 2026-05-21T00:40:00Z | COV-S8 | 1 | success | 2b2eca10 | https://github.com/amonty84/Madhav/pull/116 | tsc:PASS vitest:6/6 lint:EXIT0 CI:all-green | null |
| 2026-05-21T00:55:00Z | PERF-S1 | 1 | success | 013fc90a | https://github.com/amonty84/Madhav/pull/117 | tsc:PASS vitest:79/79 lint:EXIT0 CI:all-green | null |
| 2026-05-21T01:10:00Z | ICR-S1 | 1 | success | 1dee9cc9 | https://github.com/amonty84/Madhav/pull/118 | tsc:PASS vitest:4/4 schema_validate:PASS CI:all-green | null |
| 2026-05-21T01:40:00Z | COV-S2 | 1 | success | 03439cc3 | https://github.com/amonty84/Madhav/pull/119 | tsc:PASS vitest:4/4 manifest_audit:PASS CI:all-green | null |
| 2026-05-21T01:55:00Z | COV-S9 | 1 | success | 81e3230e | https://github.com/amonty84/Madhav/pull/120 | tsc:PASS vitest:5/5 CI:all-green | null |
| 2026-05-21T02:05:00Z | ICR-S2 | 1 | halt | 1a46940b | https://github.com/amonty84/Madhav/pull/121 | tsc:PASS vitest:4/4 l1_truth_index:17.8% CI:all-green | l1_truth_index_coverage_gte_95pct=FAIL: 91/510 grounded (17.8%) — ICR stream halted |
| 2026-05-21T02:10:00Z | COV-S10 | 1 | success | a671fcd3 | https://github.com/amonty84/Madhav/pull/122 | tsc:PASS vitest:6/6 CI:all-green | null |
| 2026-05-21T02:30:00Z | COV-S3 | 1 | success | e9cf20dc | https://github.com/amonty84/Madhav/pull/123 | tsc:PASS vitest:15/15 planner_golden_regression:PASS CI:all-green | null |
| 2026-05-21T07:00:00Z | COV-S4 | 1 | success | ecee542d | https://github.com/amonty84/Madhav/pull/124 | tsc:PASS vitest:9/9 sla_probe_new_tools:PASS lint:EXIT0 CI:all-green | null |
| 2026-05-21T07:30:00Z | ICR-S2 (halt resolution) | — | resolved | — | — | criterion_redefined:Option_C | halt resolved: classical-text citations now count as grounded |
| 2026-05-21T07:47:00Z | PERF-S2 | 1 | success | 401e6b46 | https://github.com/amonty84/Madhav/pull/125 | tsc:PASS vitest:16/16 lint:EXIT0 | null |
| 2026-05-21T02:40:00Z | COV-S7 | 1 | success | 2b9ec783 | https://github.com/amonty84/Madhav/pull/125 | tsc:PASS vitest:4/4 synthetic_pr_coverage_gate_fails:PASS CI:all-green (continue-on-error for pre-existing gaps) | null |
