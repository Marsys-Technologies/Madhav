---
canonical_id: RED_TEAM_PLATFORM_MOD
version: 1.0
status: CURRENT
sealed_at: 2026-05-28
red_team_pass_for: PLATFORM_MODERNIZATION (Batches 1–5)
class_1_findings: 0
class_2_findings: 3
class_3_findings: 4
---

# Platform Modernization — Adversarial Red-Team Pass

Per IS.8(b) cadence: macro-phase close requires a red-team pass with
0 class-1 findings before sealing. This is the Wave-4 (Batch 5) red-team
covering the cumulative Platform Modernization arc (Batches 1–5).

## Class-1 attack surfaces (anything that could ship a wrong answer or leak data)

| # | Surface | Verdict | Evidence |
|---|---|---|---|
| 1 | **Authz coverage (owner / grant / super_admin)** | PASS | 2c `authorizeChartAccess.ts` + 6/6 tests; RLS on `charts.owner_id` + `chart_grants`; 4.build_trigger gates `/api/build/start` via the same module; 0b.3 mirror-retirement keeps no privileged-mirror back door. |
| 2 | **Constant-offset ayanamsha invariant (jh_true_chitra canonical)** | PASS | 1.2 three-ayanamsha registry; 2a `assert_no_native_literal.sh` exits 0; 2d Command Center hard-guards canonical-ayanamsha selection; G6_tool_coverage asserts 0 ayanamsha mismatches across 77 tools × 19 assets. |
| 3 | **B.11 floor forced-first on every gateway path** | PASS | 3.gateway_pipeline_isolation `b11_floor.ts` + gateway 8-step chokepoint enforces B.11 before any tool dispatch; primitives tagged `surgical:true`. Both single_pass + agentic share the same `pipelines/shared/b11_floor_inject.ts`. |
| 4 | **No tier path reachable** | PASS | 3.tier_excision deleted `lib/disclosure/` + `TierPicker.tsx` + `house_rules_variants/public_redacted.md` + `tier_catalog.ts`; migration 090 dropped `mcp_api_keys.audience_tier`; planner-auto-by-query-class is the only depth selector. |
| 5 | **No `NATIVE_CHART_ID` / `DEFAULT_CHART_ID` literals in retrieve path** | PASS | 2a `assert_no_native_literal.sh` exits 0; `chart_context.ts` resolver threads chart_id explicitly through 4 retrieval tools; G4_no_native_lit GREEN. |
| 6 | **No LEL in build / churn** | PASS | LEL is a panel input only (per 4.learning_loop wiring: calibration stamp logs regardless of LEL toggle; LEL_CONTEXT_ENABLED affects panel reads only); build path (`/api/build/*`) does not import LEL modules — verified by grep. |
| 7 | **Prediction-log determinism** | PASS | 4.learning_loop calibration stamp keyed on (chart_id, ayanamsha_id, query_hash, salience_formula_version); ON CONFLICT DO NOTHING idempotency; query_hash via SHA-256 truncated 16-char hex. |
| 8 | **Kill-switch wiring (budget + error-rate)** | PASS | 4.observability `budget_guard.ts` writes `gate_status` + flips `BUDGET_KILL_SWITCH_ENABLED` via `setGate` at ≥100%; multi-window alert policies (latency_burn / error_rate_burn at 14.4x/6x) wired in `infra/monitoring/alerts/*.json`. |
| 9 | **MCP IAM (no public reach)** | PASS | 4.edge_and_infra_hygiene flipped `amjis-mcp` to `--no-allow-unauthenticated`; `platform-mcp/src/client.ts` uses `GoogleAuth.getIdTokenClient(PLATFORM_URL)` for bearer-token outbound calls; 3/3 IAM-bearer tests GREEN. |
| 10 | **Secret hygiene** | PASS | 0b.2 secret remediation closed the leaked-DB-password incident in HEAD; 4.edge `infra/secrets/secret_inventory.yaml` enumerates 12 secrets; `:latest` pins flagged (1 WARN, non-fatal). Rotation policy in `infra/secrets/rotation_policy.md`. |

**Class-1 verdict: 0 findings.** All 10 attack surfaces PASS.

## Class-2 findings (non-blocking; dispositioned)

| ID | Finding | Disposition |
|---|---|---|
| RT.2.1 | `tools/program-tracker/` is an ephemeral support service (`lifecycle: ephemeral`); per brief AC.2 it must be removed at macro-phase close. | RESOLVED in this batch (commit 2/3 of red_team_seal). |
| RT.2.2 | `:latest` image pins flagged in `infra/secrets/secret_inventory.yaml` for Cloud Run image references — non-fatal per 4.edge design (WAF/Armor protect; rotation policy in place). | DEFERRED to next quarterly hygiene pass per `ONGOING_HYGIENE_POLICIES §H`. |
| RT.2.3 | answer:eval post-cutover baseline shipped STUBBED (commit 4.learning_loop 2/2) — operator must re-run with live creds to populate v1.1. | DEFERRED to operator queue (documented in `answer_eval_baseline_post_cutover_v1_0_notes.md §Operator runbook`). |

## Class-3 findings (advisory)

| ID | Finding | Disposition |
|---|---|---|
| RT.3.1 | Memorystore Redis HA mode = standard tier (not HA) per `infra/memorystore/main.tf`; OK for single-region staging-grade traffic; HA tier upgrade is a §9 deferred call. | DEFERRED per master plan §9 "incremental call" — upgrade when traffic warrants. |
| RT.3.2 | `MARSYS_FLAG_BUILD_TRIGGER_ENABLED` defaults FALSE (kill-switch); operator must flip to true post-smoke to enable Build action. | DEFERRED to operator queue. |
| RT.3.3 | Cloud Trace + Cloud Monitoring IaC codified but `terraform apply` not executed from autonomous session — operator runs `infra/monitoring/apply.sh` + `infra/edge/apply.sh` + `infra/iam/apply.sh` + `infra/scheduler/apply.sh` + `infra/memorystore/apply.sh` + `infra/cloud_tasks/apply.sh` to materialize. | DEFERRED to operator queue. |
| RT.3.4 | Migration 119 (calibration-stamp columns) and migration 118 (build_events) not yet applied to staging/prod — additive + idempotent. | DEFERRED to operator queue. |

## Open-decisions disposition (per brief)

| Decision | Status |
|---|---|
| Depth-selector default (planner-auto-by-query-class) | LOCKED per 3.tier_excision; native review pending but operating as-default. |
| Anthropic-cost call | RESOLVED — observatory cost-reconciliation surface tracks per-model spend; budget guard kill-switch wired (4.observability 4/4); per-stack pricing in `model_pricing.ts`. |
| Macro-phase number assigned | RESOLVED — Platform Modernization is a concurrent workstream that ran during M5-active time; sealed as `PLATFORM_MODERNIZATION_CLOSE_v1_0.md`. No new M-number assigned (the M-arc is the macro-arc; Platform Modernization is an arc inside M5). |
| Layer-vocabulary canonicalization | RESOLVED — L1 (facts) / L2.5 (synthesis) / L4 (RAG corpus) usage is consistent across the codebase post-2a; no L2 (deleted phase 14F) references in active code. |
| §9 open decisions (HA, partition, SQL upgrade) | DEFERRED per master plan §9 explicit "incremental call" rationale; not a sealing blocker. |

## Conclusion

**0 class-1 findings.** The Platform Modernization arc is safe to seal. The 3 class-2 + 4 class-3 findings are dispositioned with explicit operator-queue items or quarterly-hygiene defers. No native review required pre-seal.
