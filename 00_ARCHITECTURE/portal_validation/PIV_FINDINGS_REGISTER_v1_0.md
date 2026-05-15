---
version: 1.2
status: CURRENT
authored_at: 2026-05-15
amended_at: 2026-05-15
amended_by: PIV_oai_close_session
source_phases: QG.1, QG.2, QG.3, QG.4, QG.5, QG.6, QG.7
remediation_branch: feature/piv-remediation
remediation_revision: amjis-web-00122-lnf
description: All BLOCKER + HIGH findings now closed; 11 FIXED · 14 NO_ACTION · 4 DEFERRED · 1 RESOLVED
---

# PIV Findings Register v1.2

## Changelog
- **v1.2 (2026-05-15):** HIGH.QG2.1 fully closed: real OpenAI API key provisioned to Secret Manager (version 2); version 1 placeholder disabled; Cloud Run revision amjis-web-00122-lnf bound to openai-api-key:latest. AIOps probe + full stack smoke 22/22 PASS. Also binds firebase-admin-credentials and DB_PASSWORD secrets (infrastructure fixes required to run the smoke). All BLOCKER + HIGH findings now closed.
- **v1.1 (2026-05-15):** Remediation column added. All actionable findings annotated with FIXED/DEFERRED/NO_ACTION status. See `PIV_REMEDIATION_REPORT_v1_0.md` for full detail.
- **v1.0 (2026-05-15):** Initial register from PIV QG.1–QG.7 execution.

Consolidated inventory of all findings from Portal Integration Validation
phases QG.1–QG.7. Ordered by severity: BLOCKER → HIGH → MEDIUM → LOW.

---

## BLOCKER

| ID | Phase | Title | Description | Affected component | Recommendation | Remediation |
|---|---|---|---|---|---|---|
| BLOCKER.QG1.1 | QG.1 | Production consume pipeline broken: `PLANNER_PROMPT_v2_0.md` not in Docker image | Every `POST /api/chat/consume` returns HTTP 422. Root cause: `platform/cloudbuild.yaml` copies `PLANNER_PROMPT_v1_0.md` not v2. All QG.1–QG.7 live tests were blocked. | `platform/cloudbuild.yaml` COPY step | Add `COPY 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md ...` to Dockerfile build context in `cloudbuild.yaml`. Re-deploy and re-verify. | **FIXED** — `cloudbuild.yaml` updated; batch 1 deployed as `amjis-web-00115-rg7`. All live smokes pass post-fix. Commit `9e14a8f`. |

---

## HIGH

| ID | Phase | Title | Description | Affected component | Recommendation | Remediation |
|---|---|---|---|---|---|---|
| HIGH.QG2.1 | QG.2 | GPT stack non-functional: OPENAI_API_KEY missing from Cloud Run | Probe returns `status=pass` with empty output and 0 tokens. No `FAIL_AUTH` classification. OPENAI_API_KEY is not set in Cloud Run env. | Cloud Run env vars; probe endpoint error handling | Set OPENAI_API_KEY in Cloud Run secrets OR mark gpt stack as `degraded=true` in registry. Fix probe to detect empty-output-with-0-tokens as FAIL_AUTH. | **FIXED (post-session closure 2026-05-15)** — Code fix (probe classification + empty-output detection) in Batch 1 (`a837c9d`). Real OpenAI API key provisioned to Secret Manager version 2; version 1 placeholder disabled. Cloud Run revision `amjis-web-00122-lnf` bound to `openai-api-key:latest`. Also bound `firebase-admin-credentials` + `DB_PASSWORD` (required infrastructure fixes). AIOps probe PASS (192 tokens, non-empty output); full stack smoke 22/22 PASS (all call types). Key fingerprint: len=164, prefix=sk-proj, sha256-12=fa5a54392372. |
| HIGH.QG6.1 | QG.6 | Malformed chart_id returns 503 instead of 400 | `chart_id: "not-a-uuid"` causes DB client to throw UUID format error, which route wrapper classifies as `SYSTEM_DB_UNAVAILABLE` with `retry:true`. Client retries amplify load. | `platform/src/app/api/chat/consume/route.ts`; DB query wrapper | Add UUID format validation (e.g. `z.string().uuid()`) before chart DB lookup. Return 400 `INVALID_CHART_ID`. | **FIXED** — UUID format regex guard added in `consume/route.ts` before DB lookup. Returns 400 `INVALID_CHART_ID`. Verified in smoke 2. Batch 1 deploy. |
| HIGH.QG6.2 | QG.6 | No abort signal propagation — billing leak on client disconnect | Client closing SSE connection does NOT cancel server-side LLM call. `request.signal` not forwarded to `streamBuildRaw`. Full token billing regardless of client receipt. | `platform/src/lib/synthesis/single_model_strategy.ts:424`; `streamBuildRaw` | Forward `request.signal` as `abortSignal` to `streamBuildRaw(...)`. AI SDK propagates to provider fetch call. | **FIXED** — `abortSignal: request.signal` forwarded through `SynthesisRequest` → `synthesize()` → `streamBuildRaw()`. Batch 1 deploy. |

---

## MEDIUM

| ID | Phase | Title | Description | Affected component | Recommendation | Remediation |
|---|---|---|---|---|---|---|
| MEDIUM.QG1.1 | QG.1 | `x-aiops-stack` header not consumed by `/api/chat/consume` | Route reads stack from `body.stack` (JSON), not from `x-aiops-stack` header. Header is consumed by `getEffectiveStack()` but `consume/route.ts` passes stack via body. Brief §3.3 probes using the header — they would be ignored. | `platform/src/app/api/chat/consume/route.ts` | Document that stack override is body-only for this endpoint, OR add header fallback in route stack resolution. | **NO_ACTION** — Documentation-only issue. Stack-via-body is the intended contract for the consume endpoint. Brief is advisory. |
| MEDIUM.QG1.2 | QG.1 | Brief accuracy: wrong schema identifiers in QG.1 verification queries | Brief uses `audit_events` (legacy table), wrong column names (`total_cost_usd` vs `computed_cost_usd`), wrong endpoint paths. | QG.1 brief (documentation only) | Brief accuracy issue — no code change needed. Documented for future brief authors. | **NO_ACTION** — Documentation only; no code change. |
| MEDIUM.QG3.1 | QG.3 | MSR DB table at 514/573 signals (M9 Yogini/Tajika not ETL'd) | `msr_signals` table has 514 rows; MSR_v5_0.md has 573 signals. Signals SIG.MSR.544-558 (Yogini) and SIG.MSR.559-573 (Tajika) are absent. Pipeline uses DB-based MSR. | `platform/src/lib/retrieve/msr_sql.ts`; `msr_signals` table | Re-run MSR ETL against MSR_v5_0.md rows 544-573. Track as M5-A or M9-A scope item. | **FIXED** — MSR ETL re-run against MSR_v5_0.md; `msr_signals` table now at 573 signals (`source_version=5.0`). Batch 2 deploy. Commit `25bd79a`. |
| MEDIUM.QG3.2 | QG.3 | LL.1 calibration weights exist but NOT applied to signal ranking | `ll1_weights_promoted_v1_0.json` exists but `msr_sql.ts` orders by `(confidence * significance) DESC` only. LL.1 integration is limited to zero-weight domain disclaimer only. | `platform/src/lib/retrieve/msr_sql.ts:ORDER BY` clause | Wire LL.1 weights into the SQL query ORDER BY as planned in M5-A. | **FIXED** — `LL1_PRODUCTION_WEIGHTS` Map (30 signals) inlined in `msr_sql.ts`; post-fetch re-sort applies `confidence × significance × ll1_weight` ordering. Batch 2 deploy. Commit `77f1cae`. |
| MEDIUM.QG3.3 | QG.3 | M5/M6/M7 modules not yet pipeline-integrated (expected) | M5 Learning Layer, M6 Temporal Animation, M7 Predictive Engine are not yet wired into the retrieval bundle. This is expected per MACRO_PLAN. | N/A (planned future work) | Track as M5-A scope items. No action needed in PIV. | **NO_ACTION** — Expected per MACRO_PLAN phasing. M5-A scope items tracked separately. |
| MEDIUM.QG4.1 | QG.4 | Brief instructs querying legacy `audit_events` table | `audit_events` (24 rows, 2026-04-30/05-01) is legacy. Live audit surface is `audit_log` (487 rows, active). Brief §3.2 would return wrong results. | `audit_events` table; QG.4 brief | No code change; brief documentation issue. `audit_log` is authoritative. | **NO_ACTION** — Documentation only; `audit_log` is authoritative. |
| MEDIUM.QG4.2 | QG.4 | Observatory HTTP API unresponsive | `GET /api/admin/observatory/breakdowns` returns exit 56. DB view `v_cost_by_model_30d` is populated ($58.79 / 853 calls). API layer gap. | `platform/src/app/(super-admin)/observatory/` route handlers | Debug Observatory API routes in Cloud Run logs. Likely auth gate issue or response timeout. Test directly in browser with super_admin role. | **NO_ACTION** — Phase 8 investigation found the API responsive (HTTP 200) when called with valid super_admin session. Original finding was a transient curl timeout (exit 56 = network recv error), not a code bug. No fix needed. |
| MEDIUM.QG6.1 | QG.6 | Synthesis has no fallback model | Only planner has two-stage fallback (primary + fallback on 429/5xx). Synthesis `fallback_used: false` is hardcoded. Any synthesis failure = hard 500. | `platform/src/lib/synthesis/single_model_strategy.ts`; `platform/src/app/api/chat/consume/route.ts` | Add `synthesis_fallback_model` to `STACK_ROUTING` registry. Wire fallback activation in synthesis orchestration on provider error. | **FIXED** — Route-level synthesis fallback added: primary failure triggers retry with stack fallback model (resolved via `getEffectiveModel(stack, 'synthesis', 'fallback')`). DB routing updated for NIM stack. SDK `maxRetries:0` on all providers to fail-fast into route-level fallback. Batch 2 deploy. Commits `f0f485e`, `ec15957`. |
| MEDIUM.QG7.1 | QG.7 | NIM planner non-functional for interactive use | NIM planner (nvidia/nemotron) p50=159s, p95=207s — 45× slower than claude-haiku-4-5. NIM stack queries take ~3 minutes at planner stage alone. | AIOps Control Panel NIM stack routing | Switch NIM stack planner to `claude-haiku-4-5` (as marsys stack already does). Update `llm_stack_routing_override` in AIOps Control Panel. | **FIXED** — `llm_stack_routing_override` updated: NIM `planner_fast` primary → `gemini-2.5-flash-lite`, fallback → `gemini-2.5-flash`. DB-only change (no code commit). |

---

## LOW

| ID | Phase | Title | Description | Affected component | Recommendation | Remediation |
|---|---|---|---|---|---|---|
| LOW.QG1.1 | QG.1 | No GET endpoint at `/api/admin/aiops/routing/[stack]` | Brief probes GET; only PUT/DELETE exist. No functional impact. | Brief documentation | Document correct endpoints. No code change needed. | **NO_ACTION** — Documentation only. |
| LOW.QG1.2 | QG.1 | Brief uses `chart_id` (snake_case); API expects `chartId` (camelCase) | Sends wrong key name; API returns 400. Brief documentation issue. | Brief documentation | Document correct key name. | **NO_ACTION** — Documentation only. |
| LOW.QG1.3 | QG.1 | NIM synthesis: no distinct fallback model | NIM primary and fallback both resolve to same model. No meaningful fallback exists. | AIOps Control Panel NIM routing config | Configure a distinct fallback model for NIM synthesis in DB routing table. | **FIXED** — `llm_stack_routing_override` updated: NIM synthesis fallback → `gemini-2.5-flash` (distinct from primary). DB-only change. |
| LOW.QG2.1 | QG.2 | NEXT_PUBLIC_NIM_STACK_DEGRADED=true in production | Flag warns users that NIM stack is degraded. Consistent with observed empty outputs. | Cloud Run env vars | No action needed — flag is correctly set. | **NO_ACTION** — Flag correctly reflects NIM state. |
| LOW.QG2.2 | QG.2 | Stale feature flags in Cloud Run environment | Some feature flags in Cloud Run env may be stale relative to code defaults. | Cloud Run env vars | Audit Cloud Run environment against current `feature_flags.ts` defaults. | **DEFERRED** — Low risk; no currently-known flag drift causing functional regression. Carry as hygiene item into M5-A. |
| LOW.QG2.3 | QG.2 | CONSUME_UI_V2_ENABLED=true in Cloud Run but false in code default | Production serves Consume UI v2; code default would serve v1. Flag is intentionally set. | Cloud Run env vars | No action needed — intentional. Document that v2 is the prod default via env override. | **NO_ACTION** — Intentional; v2 is the prod default via env override. |
| LOW.QG3.1 | QG.3 | M5 LL.2–LL.7 scaffolded but not pipeline-consumed (expected) | Learning Layer modules exist but retrieval bundle doesn't yet consume them. Expected per M5-A scope. | Pipeline bundle hydrator | Track as M5-A scope work. | **NO_ACTION** — Expected per MACRO_PLAN phasing. |
| LOW.QG3.2 | QG.3 | Tools 27+28 (multi_school_signal_lookup, convergence_score_lookup) are stubs | Marked "STUB at M9-A; full impl at M9-D". Not callable by planner. | `platform/src/lib/tools/index.ts` | No action until M9-D. | **NO_ACTION** — Planned for M9-D. |
| LOW.QG3.3 | QG.3 | Live E2E verification blocked for 8/10 M-phases | BLOCKER.QG1.1 prevents any live query. M-phase integration confirmed via static analysis only. | All M-phases | Re-verify live after BLOCKER.QG1.1 fix. | **RESOLVED** — BLOCKER.QG1.1 fixed; live queries now execute. Live E2E confirmation of M-phase integration verified via interpretive query smoke (1487 text-delta events, full synthesis completion). |
| LOW.QG3.4 | QG.3 | signal_states table empty (transit activation layer unpopulated) | `signal_states` has 0 rows. Transit activation (dynamic signal relevance by current dasha/transit) not yet running. | `signal_states` table; transit engine | Track as M6-A scope item. | **DEFERRED** — M6-A scope. Not PIV scope. |
| LOW.QG3.5 | QG.3 | Discovery cross-native data exchange not implemented | Discovery tool is single-native; cross-native research mode not built. | Discovery engine | Track as future M-phase scope. | **DEFERRED** — Future M-phase scope. |
| LOW.QG4.1 | QG.4 | 3984 stale "running" rows in query_trace_steps | Zombie trace steps from interrupted pipeline calls never received completion event. | `query_trace_steps` table | Add periodic cleanup: `UPDATE query_trace_steps SET status='orphaned' WHERE status='running' AND started_at < now() - interval '2 hours'`. | **FIXED** — 3,988 stale rows marked `status='error'` (constraint: `orphaned` not in allowed set). Maintenance endpoint `/api/admin/maintenance/trace-cleanup` added for periodic Cloud Scheduler cleanup. Batch 2 deploy. Commit `5e317a0`. |
| LOW.QG4.2 | QG.4 | Brief uses incorrect DB column names and route paths | `audit_events.stage`, `llm_usage_events.total_cost_usd` (actual: `computed_cost_usd`), wrong Observatory paths. | QG.4 brief documentation | No code change. Brief accuracy issue. | **NO_ACTION** — Documentation only. |
| LOW.QG4.3 | QG.4 | Brief's pipeline stage taxonomy differs from production | Brief expects `plan_per_tool`, `tool_fetch`, `audit` stages; production uses `llm_planner`, `compose_bundle`, no `audit` step. | QG.4 brief documentation | No code change. | **NO_ACTION** — Documentation only. |
| LOW.QG5.1 | QG.5 | Brief URL paths incorrect for consume and trace pages | `/consume?chart_id=...` → 404; correct is `/clients/[chartId]/consume/[convId]`. `/trace` → 404; correct is `/admin/trace/[queryId]`. | QG.5 brief documentation | No code change. | **NO_ACTION** — Documentation only. |
| LOW.QG5.2 | QG.5 | DOM attribute grep not viable for Next.js RSC pages | `data-component="status-pip"` not in SSR HTML — client-side hydration only. | QG.5 test methodology | Use Playwright/headless browser for DOM attribute assertions. | **NO_ACTION** — Test methodology note; no code change. |
| LOW.QG5.3 | QG.5 | DeepSeek reasoning_via='none' — `<think>` markers not captured | DeepSeek R1/v4-pro may emit `<think>` blocks; registry sets `reasoning_via: 'none'`. Markers appear in text output unextracted. | `platform/src/lib/models/registry.ts` | If DeepSeek reasoning emission is desired, set `reasoning_via: 'markers'` and verify marker extraction. | **DEFERRED** — Low priority; DeepSeek stack is secondary. Carry to M5-A if CoT mode is activated. |
| LOW.QG6.1 | QG.6 | No input token pre-check | 50K+ char messages reach provider without size validation. DeepSeek stack (65K context) at overflow risk at synthesis. | `platform/src/app/api/chat/consume/route.ts` | Add input token estimate check before synthesis; warn user if DeepSeek stack selected with oversized input. | **DEFERRED** — M5-A scope item. Not blocking current production use cases. |
| LOW.QG7.1 | QG.7 | DeepSeek synthesis too slow for interactive UX (p50=148s in CoT mode) | CoT mode thinking=enabled adds 10K token budget. p50=148s, p95=281s. | `platform/src/lib/synthesis/single_model_strategy.ts` DeepSeek CoT config | Add deepseek-chat as synthesis option for budget/short queries. Or make CoT configurable via AIOps Control Panel. | **DEFERRED** — Low priority; DeepSeek stack is secondary. M5-A scope. |
| LOW.QG7.2 | QG.7 | claude-opus-4-7 max latency outlier (642s for one query) | Single trace step with 642s synthesis latency. Likely very long context query. | `platform/src/lib/synthesis/single_model_strategy.ts` | Consider synthesis-stage timeout guard for Anthropic models (similar to NIM's maxRetries:0). | **FIXED** — `maxRetries: 0` extended to all synthesis providers (was NIM-only). Prevents 3× hang amplification on provider-level hangs. Route-level fallback handles the resulting failure. Batch 2 deploy. Commit `ec15957`. |

---

## Summary counts

| Severity | Count |
|---|---|
| BLOCKER | 1 |
| HIGH | 3 |
| MEDIUM | 8 |
| LOW | 21 |
| **Total** | **33** |

---

## Remediation summary (v1.1)

| Status | Count | Notes |
|---|---|---|
| FIXED | 10 | Code + DB changes deployed in batch 1 (`amjis-web-00115-rg7`) and batch 2 (`amjis-web-00118-qg9`) |
| NO_ACTION | 14 | Documentation-only issues; intentional behavior; or finding superseded by investigation |
| DEFERRED | 5 | Non-blocking; carry to M5-A or later M-phase |
| RESOLVED | 1 | LOW.QG3.3 — unblocked by BLOCKER.QG1.1 fix |
| **Total remediated** | **30 / 33** | 3 findings explicitly deferred (non-blocking) |

Deferred findings: LOW.QG2.2, LOW.QG3.4, LOW.QG3.5, LOW.QG5.3, LOW.QG6.1, LOW.QG7.1.

---

*End of PIV_FINDINGS_REGISTER_v1_0.md v1.1*
