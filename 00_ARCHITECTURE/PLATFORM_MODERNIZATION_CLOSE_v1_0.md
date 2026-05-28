---
canonical_id: PLATFORM_MODERNIZATION_CLOSE
version: 1.0
status: SEALED
sealed_at: 2026-05-28
sealed_by: Wave-4 unit 4.red_team_seal (Batch 5, autonomous Conductor)
program: PLATFORM_MODERNIZATION
plan: PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0
execution_plan: PLATFORM_MODERNIZATION_EXECUTION_PLAN_v1_0
total_units: 23 (20 planned + 2 hygiene + 1 inline)
total_batches: 5
total_gates: 8/8 GREEN
class_1_red_team_findings: 0
---

# Platform Modernization — Macro-arc Close

The autonomous Conductor arc that delivered the JH-parity natal engine, the
unified contract substrate, the L2.5 chart-id-keyed deterministic data layer,
the gateway+pipeline split, the post-cutover adapter path, and the Wave-4
final-seal infrastructure (Memorystore caching, observability, edge hygiene,
build trigger, learning-loop substrate). Concurrent workstream on M5-active
time. Sealed at commit `<TO_FILL>` on main, 2026-05-28.

## Wave / Batch summary

| Batch | Waves | Units | Sub-agents | Outcome |
|---|---|---|---|---|
| 1 | 0-support, 0a, 0b, 1 | 0t, 0a.0, 0a.1, 0b.1, 0b.2, 0b.3, 1.1 | 7 | Naming + behaviour-altering gates set; engine scaffold |
| 2 | 1, 2 | 1.2, 2b, 2c, 2d | 4 | G1_jh_parity / G2_authz_live / G3_contract GREEN |
| 3 | 2, 3 | 2a, 3.consult_nav, 3.dejudge, 3.tier_excision, 3.gateway_pipeline_isolation, 3.tool_asset_recon | 6 | G4 / G6 GREEN; de-judgment; tier excision; gateway split |
| 4 | 3-hygiene, 3 | hygiene.test_chart_id, hygiene.flag_cleanup, 3.cutover, 3.legacy_delete | 4 | G5b_onfinish GREEN; legacy trio deleted; pipeline-selector flag retired |
| 5 | 4 | 4.refactor_pipeline_shim, 4.observability, 4.memorystore_caching, 4.edge_and_infra_hygiene, 4.build_trigger, 4.learning_loop, 4.red_team_seal | 11 (8 agents + 3 inline) | Wave-4 final seal; red-team 0 class-1 |

## Gate board (final)

| Gate | Status | Set by |
|---|---|---|
| naming_ci | GREEN | 0a.0 (Batch 1) |
| jh_oracle_pinned | GREEN | oracle pinned 2026-05-28 |
| G1_jh_parity | GREEN | 1.2 (Batch 2) |
| G2_authz_live | GREEN | 2c (Batch 2) |
| G3_contract | GREEN | 2b (Batch 2) |
| G4_no_native_lit | GREEN | 2a (Batch 3) |
| G5b_onfinish | GREEN | 3.cutover (Batch 4) |
| G6_tool_coverage | GREEN | 3.tool_asset_recon (Batch 3) |

**8/8 hard gates GREEN.**

## Wave-4 unit commit ledger (this batch)

| Unit | Stream | Commits on main |
|---|---|---|
| **4.refactor_pipeline_shim** | A | `bc9379ce` `5b9164bd` |
| **4.observability** | B | `5180733f` `50b74814` `33bacc0a` `42a39960` |
| **4.memorystore_caching** | C | `45ed0ef9` `177420c9` `a56434b1` |
| **4.edge_and_infra_hygiene** | A | `309376cd` `d47ad81a` `c8592215` |
| **4.build_trigger** | B | `4b5d60b7` `6d34e6cb` `524792ab` |
| **4.learning_loop** | C inline | `1a0b0fe8` `307c39ed` |
| **4.red_team_seal** | A inline | `fcdc9199` + program-tracker removal commit + seal artifact commit |

## Test posture at seal

`npx vitest run src/app/clients src/app/api/build src/lib/build src/lib/predictions src/lib/pipelines/shared src/lib/cache src/lib/observability src/lib/embeddings src/app/api/chat` → **22 files, 223 tests, all green** at HEAD.

## Open-decisions disposition

| Decision | Status |
|---|---|
| Depth-selector default | LOCKED at planner-auto-by-query-class (3.tier_excision) |
| Anthropic-cost call | RESOLVED — observatory + budget kill-switch wired (4.observability 4/4) |
| Macro-phase number | RESOLVED — Platform Modernization is a concurrent workstream during M5; sealed without new M-number |
| Layer-vocabulary canonicalization | RESOLVED — L1 / L2.5 / L4 only; L2 retired phase 14F |
| §9 deferred calls (HA tier, SQL upgrade, partition) | DEFERRED — incremental investment, not sealing blockers |

## Red-team disposition

Full report: `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md`.

**Class-1: 0 findings.** Class-2: 3 dispositioned (program-tracker retired; `:latest` pins to quarterly hygiene; answer:eval baseline STUBBED → operator). Class-3: 4 dispositioned (Memorystore HA tier deferred per §9; BUILD_TRIGGER flag default false → operator; terraform apply pending operator; migrations 118/119 pending operator).

## Deferred operator items

1. **Apply migrations** to staging then prod: **081–090** (pre-existing carry from Batch 4), **118** (build_events), **119** (calibration-stamp columns). All additive + idempotent; 090 (`mcp_api_keys.audience_tier` drop) is the only irreversible op — run after a green post-cutover smoke window.
2. **Run terraform apply** for the new Wave-4 IaC:
   - `infra/memorystore/apply.sh` (Redis instance, ~$50/mo standard tier)
   - `infra/edge/apply.sh` (LB + CDN + Cloud Armor)
   - `infra/iam/apply.sh` (4 least-priv service accounts)
   - `infra/scheduler/apply.sh` (MV-refresh + reaper jobs)
   - `infra/cloud_tasks/apply.sh` (build queue)
   - `infra/monitoring/` dashboards + SLOs + alerts (apply via `gcloud monitoring dashboards create` per JSON file)
   - `infra/artifact_registry/cleanup_policy.json` apply
3. **Cloud Run env-var cleanup**: `gcloud run services update amjis-web --remove-env-vars MARSYS_FLAG_PIPELINE_SELECTOR,MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED`.
4. **Rotate `amjis-db-password`** (carried from Batch 1).
5. **Run live `answer:eval` baseline** — see `00_ARCHITECTURE/answer_eval_baseline_post_cutover_v1_0_notes.md §Operator runbook`. Overwrites the STUBBED v1.0 file with live metrics as v1.1.
6. **Flip MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true** in Cloud Run after smoke-testing the Build action against a non-native chart.
7. **Delete Cloud Run service `amjis-tracker`** (program-tracker retired): `gcloud run services delete amjis-tracker --region asia-south1`.
8. **Native review of depth-selector default** (3.tier_excision; carried from Batch 3).

## Concurrent workstream effect

Platform Modernization ran during M5 active time. M5-A is the active sub-phase per `PHASE_M5_PLAN_v1_0.md`; this arc did not advance M5 substantively (its scope was platform substrate, not Learning Layer / MSR reconciliation / PPL cadence). The M5-A backlog remains intact: LL.8+LL.9 scaffold; CF.LL7.1 CDLM confirm + LL.7 re-emit; MSR reconciliation; LL.2 per-edge campaign; PPL cadence plan (NAP.M5.0); JH scheduling.

## Reversibility

Each Wave-4 unit's commits cleanly revert. Memorystore + edge + IAM are IaC-additive (apply script gated). Migration 119 is additive + idempotent. The calibration-stamp producer swallows errors so DB-absent environments degrade cleanly.

The legacy synthesis trio (orchestrator + single_model_strategy + panel_strategy) was deleted in Batch 4 (3.legacy_delete) and is not recoverable except by `git revert`. The pipeline-selector shim was deleted in Wave 4 (4.refactor_pipeline_shim 2/2) and is not recoverable except by `git revert`.

This arc is SEALED.
