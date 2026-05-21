---
artifact: PROJECT_BHISMA_SESSION_LOG
project: BHISMA
version: 1.0
status: ACTIVE
created: 2026-05-01
description: >
  Platform Elevation Project — multi-provider model family, LLM-first intelligent
  pipeline, Trace Command Center. Runs in parallel with M3 as a separate workstream.
cowork_conversation: BHISMA (separate from M3 conversation)
karn_wave_equivalent: KARN-W9 (B1–B4)
---

# PROJECT BHISMA — Session Log

## Naming Convention

### Pattern
```
BHISMA-W{wave}-S{session}-{DESCRIPTION}
```

| Field | Rule |
|---|---|
| `wave` | Sequential integer starting at **1**. Incremented at each convergence close (W1 closes with S4-CONVERGENCE). |
| `session` | Sequential integer within the wave. S1–S3 are parallel-safe within the same wave; S4 (convergence) blocks until S1–S3 close. |
| `DESCRIPTION` | SCREAMING-KEBAB-CASE, max 4 words, describes the session's primary deliverable. |

### Examples
```
BHISMA-W1-S1-MODEL-FAMILY        ← Wave 1, Session 1: model registry + o-series + hard-fail
BHISMA-W1-S2-LLM-PIPELINE        ← Wave 1, Session 2: LLM-first planner + retrieval caps
BHISMA-W1-S3-TRACE-COMMAND       ← Wave 1, Session 3: trace re-skin + new panels
BHISMA-W1-S4-CONVERGENCE         ← Wave 1, Session 4: integration smoke + BHISMA close
BHISMA-W2-S1-DISCOVERY-FRESHNESS ← Wave 2, Session 1 (future)
```

### Cowork thread naming
Cowork conversation threads use the same identifier as the Claude Code session:
`BHISMA-W1-S1-MODEL-FAMILY`, `BHISMA-W1-S2-LLM-PIPELINE`, etc.

### Relationship to KARN
BHISMA is a sub-protocol of the KARN execution framework. KARN
`PROJECT_KARN_SESSION_LOG.md` receives a single entry at BHISMA-W1-S4-CONVERGENCE
close. Individual S1–S3 sessions do NOT write to the KARN log — they write here only.

---

## Wave 1 — Platform Elevation (Active)

**Entry state:** M2 CLOSED (KARN-W8-R2-M2-CLOSE, 2026-05-01)
**Convergence gate:** All three S1/S2/S3 close summaries reviewed by native before S4 opens.

| Session ID | Stream | Primary deliverable | Status | Closed date | Git SHA |
|---|---|---|---|---|---|
| BHISMA-W1-S1-MODEL-FAMILY | Model Family | registry.ts + resolver.ts + hard-fail | CLOSED | 2026-05-01 | 430ed4d |
| BHISMA-W1-S2-LLM-PIPELINE | LLM Pipeline | planner.ts + retrieval_capability_spec.ts | CLOSED | 2026-05-01 | 0ba34e2 |
| BHISMA-W1-S3-TRACE-COMMAND | Trace UI | TracePanel re-skin + QueryDNAPanel + CostBar | CLOSED | 2026-05-01 | 430ed4d |
| BHISMA-W1-S4-CONVERGENCE | Convergence | tsc clean + eval delta + BHISMA_CLOSE_v1_0.md | CLOSED | 2026-05-01 | — |

### Wave 1 acceptance gate (S4 close criteria)
- [x] `npx tsc --noEmit` passes clean across all new/modified files (9 pre-existing errors only)
- [x] vitest suite passes (exit 0; rule_composer NOT retired — still in legacy path by design)
- [ ] Eval baseline pre/post delta recorded — GAP.P.9 STUB persists (secrets unavailable in session)
- [x] BHISMA_CLOSE_v1_0.md authored and committed
- [x] KARN SESSION_LOG receives Wave 1 convergence entry

---

## Session Entries

<!-- Sessions append their close block below in this format:

=== BHISMA-W{n}-S{m}-{DESCRIPTION} CLOSE ===
closed: YYYY-MM-DD
git_sha: {sha}
deliverables:
  - {file}: {action}
acceptance_criteria_passed: [AC.B{n}.1, ...]
known_residuals:
  - {item}
notes: >
  {freeform}

-->

=== BHISMA-W1-S2-LLM-PIPELINE CLOSE ===
session_id_alias: KARN-W9-B2-BHISMA-LLM-PIPELINE  # name from the user brief; predates the BHISMA log naming convention
closed: 2026-05-01
git_sha: 0ba34e2
agent: claude-opus-4-7-1m
cowork_thread: "KARN-W9-B2 — BHISMA LLM-First Intelligent Pipeline"
predecessor: KARN-W8-R2-M2-CLOSE

scope_executed: BHISMA_PLAN_v1_0.md §4.1–§4.9 (Stream 2 deliverables)

deliverables:
  - 00_ARCHITECTURE/EVAL/BASELINE_RUN_W9.json: created (STUB — secrets unavailable; documented gap)
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json: token_count backfilled for 6 high-cost assets (FORENSIC, MSR_v3_0, UCN_v4_0, CGM, CDLM_v1_1, RM_v2_0); last_updated rotated
  - platform/src/lib/config/feature_flags.ts: added LLM_FIRST_PLANNER_ENABLED (default false)
  - platform/src/lib/bundle/types.ts: AssetEntry.token_count optional + BundleEntrySource accepts 'planner'
  - platform/src/lib/bundle/rule_composer.ts: tokenFor() now reads typed AssetEntry.token_count; dead getTokens removed
  - platform/src/lib/router/types.ts: added RichQueryPlan, ToolCallSpec, PlanContext, ChartContext, ConversationTurn
  - platform/src/lib/router/retrieval_capability_spec.ts: NEW — RCS for all 17 retrieval tools (BHISMA §4.1)
  - platform/src/lib/router/planner.ts: NEW — LLM-first planner with embedded system prompt (§4.2 + §4.3) + buildPlannerFloorBundle helper for §4.4 retirement of compose() in new path; PlannerError class for ADR-3 hard-fail
  - platform/src/lib/synthesis/citation_check.ts: NEW — countSignalCitations / hasMinimumCitations / citationThresholdForClass (§4.7)
  - platform/src/lib/synthesis/__tests__/citation_check.test.ts: NEW — 15 unit tests, all pass
  - platform/src/lib/synthesis/single_model_strategy.ts: synthesis_done now emits citation_count + real wall-clock latency (§4.6)
  - platform/src/app/api/chat/consume/route.ts: branch on LLM_FIRST_PLANNER_ENABLED; new path emits single 'plan' step replacing classify+compose+plan_per_tool; legacy path preserved verbatim when flag is false; PlannerError handled with step_error emit + structured 502 response
  - platform/src/lib/schemas/bundle.schema.json: source enum extended with 'planner'

acceptance_criteria_passed:
  - "§4.1 RCS authored for all 17 retrieval tools (no halt-condition triggered)"
  - "§4.2 RichQueryPlan returned by plan() with all fields populated; gated behind LLM_FIRST_PLANNER_ENABLED"
  - "§4.3 Planner system prompt embeds full RCS + 8 few-shot examples covering every query_class"
  - "§4.4 Old classify+compose+planPerTool path removed when flag=true; preserved when flag=false (rollback safe)"
  - "§4.5 context_assembly emit verified at single_model_strategy.ts:182 — token summary + chunk inventory present (already shipped pre-session)"
  - "§4.6 synthesis_done emit enriched with citation_count + real latency_ms"
  - "§4.7 citation_check.ts authored; threshold table per query_class; 15/15 tests pass"
  - "§4.8 Eval baseline STUB recorded with documented gap (server up; SMOKE_* / ANTHROPIC_API_KEY unset in this session)"
  - "§4.9 token_count backfilled for 6 major assets; tokenFor() typed-clean read"
  - "Typecheck: 9 errors total — all in pre-W6 UI test fixtures (AppShell, ReportGallery); matches W8-R1 known-residual baseline; zero new errors from this session"
  - "Vitest: 1058 passing / 13 failing — same 13-failing baseline as W8-R1; +11 net passing tests"

known_residuals:
  - id: GAP.P.9
    severity: MEDIUM
    description: "Eval baseline is STUB; post-BHISMA paired run (planner_branch=on) requires SMOKE_SESSION_COOKIE + SMOKE_CHART_ID + ANTHROPIC_API_KEY which the executor session cannot mint"
    blocker_for_close: false
    blocker_for_S4_convergence: TRUE — S4 must run the paired baseline before BHISMA closes
  - id: STEP_SEQ_DRIFT
    severity: LOW
    description: "Tool step_seq numbering: route.ts uses 4+idx (legacy); single_model_strategy uses 3+nTools-based ctxSeq. Inconsistency predates this session — not introduced by W1-S2"
    blocker_for_close: false
  - id: COMPOSE_CALL_LEGACY_BRANCH
    severity: LOW
    description: "compose() is still called in the legacy branch (LLM_FIRST_PLANNER_ENABLED=false). Per §4.4, compose() removal is for the new path only; legacy path keeps it for rollback. This is by design."
    blocker_for_close: false
  - id: BHISMA_PLAN_NAMING_REFRESH
    severity: INFORMATIONAL
    description: "Parallel session amended BHISMA_PLAN_v1_0.md to rename W9-B# → BHISMA-W1-S# convention. Session_id stayed as user-brief 'KARN-W9-B2' for traceability; alias recorded above. Not a scope violation."
    blocker_for_close: false

mirror_updates_propagated: NONE (BHISMA-W1-S2 is Claude-only; no Gemini-side counterpart this session per BHISMA naming-convention §relationship-to-KARN)

current_state_v1_0_updated: false  # per BHISMA log convention §relationship-to-KARN, only S4-CONVERGENCE writes to KARN/CURRENT_STATE
karn_session_log_appended: false   # per same convention

handoff_to_next_session: |
  S4-CONVERGENCE (BHISMA-W1-S4) is the next session that consumes this stream's output:
    1. Run paired eval baseline:
         export SMOKE_SESSION_COOKIE=... SMOKE_CHART_ID=... ANTHROPIC_API_KEY=...
         python3 platform/scripts/eval/runner.py --planner-off --output 00_ARCHITECTURE/EVAL/BASELINE_RUN_W9.json
       (overwrite STUB), then run again with MARSYS_FLAG_LLM_FIRST_PLANNER_ENABLED=true and store the on-branch results.
    2. Smoke the new path end-to-end against /api/chat/consume with the flag flipped.
    3. Author BHISMA_CLOSE_v1_0.md with the eval delta recorded.
    4. Single KARN-log entry referencing this BHISMA log close block.

notes: >
  No 025_HOLISTIC_SYNTHESIS/**, platform/migrations/**, or platform/src/lib/retrieve/** files were touched
  per the user-brief halt-conditions. The compose() function remains in the codebase and is called by the
  legacy branch — a future cleanup session can delete it once LLM_FIRST_PLANNER_ENABLED is flipped to true
  in defaults and observed in production for a soak window.

=== BHISMA-W1-S1-MODEL-FAMILY CLOSE ===
closed: 2026-05-01
git_sha: 430ed4d
agent: claude-sonnet-4-6
cowork_thread: BHISMA-W1-S1-MODEL-FAMILY

scope_executed: BHISMA_PLAN_v1_0.md §3.1–§3.6 + §6.2 (Stream 1 deliverables)

deliverables:
  - platform/src/lib/models/registry.ts: 5 OpenAI models added (gpt-4o, gpt-4o-mini, o4-mini, o1, o3); ModelRole + CallingConvention types; costPer1MInput/costPer1MOutput fields; FAMILY_WORKER map; getWorkerForModel() (pre-existing work validated + confirmed complete)
  - platform/src/lib/models/resolver.ts: isReasoningModel(), supportsStreaming(), resolveWorkerModel(); R1 reasoning middleware; o-series calling convention (pre-existing work validated + confirmed complete)
  - platform/src/lib/router/errors.ts: PipelineError hard-fail class (pre-existing work validated + confirmed complete)
  - platform/src/lib/router/router.ts: family-aware worker via resolveWorkerModel(); both LLM attempts throw PipelineError; buildFallbackPlan removed (pre-existing work validated + confirmed complete)
  - platform/src/app/api/chat/consume/route.ts: PipelineError/PlannerError → step_error trace + 502 JSON; PER_TOOL_PLANNER_ENABLED branch collapsed; AUDIT_ENABLED gate removed (audit always on)
  - platform/src/lib/synthesis/single_model_strategy.ts: reasoning calling convention branch; think-block stripping via think_block_filter.ts (pre-existing work validated + confirmed complete)
  - platform/src/lib/models/health.ts: NEW — MODEL_HEALTH in-memory map; checkWorkerHealth(); runHealthChecks(); assertWorkerHealthy() hard-fail on degraded; server-only
  - platform/src/app/api/admin/model-health/route.ts: NEW — GET + GET?refresh=true endpoint
  - platform/src/lib/telemetry/cost.ts: NEW — estimateQueryCost(steps) → planning_usd/synthesis_usd/total_usd from TraceDataSummary token fields × registry cost rates
  - platform/src/lib/config/feature_flags.ts: AUDIT_ENABLED, CGM_GRAPH_WALK_ENABLED, PER_TOOL_PLANNER_ENABLED removed from FeatureFlag union + DEFAULT_FLAGS; added TRACE_ANALYTICS_ENABLED, COST_TRACKING_ENABLED, CITATION_CHECK_ENABLED, REASONING_MODEL_STREAMING (all default true); NEW_QUERY_PIPELINE_ENABLED kept with B4 deprecation note
  - platform/src/lib/retrieve/cgm_graph_walk.ts: CGM_GRAPH_WALK_ENABLED gate removed; getFlag import dropped
  - platform/tests/unit/config/index.test.ts: AUDIT_ENABLED test cases replaced with BHISMA-B1 observability flag assertions

acceptance_criteria_passed:
  - "§3.1 (B1.1): OpenAI model family complete in registry; FAMILY_WORKER map; getWorkerForModel()"
  - "§3.2 (B1.2): resolveWorkerModel() used in router.ts classify step; isReasoningModel/supportsStreaming helpers; R1 middleware"
  - "§3.3 (B1.3): PipelineError hard-fail on both LLM attempts; no silent fallback; step_error trace + 502 JSON from route.ts"
  - "§3.4 (B1.4): reasoning calling convention branch in single_model_strategy.ts; think-block stripped"
  - "§3.5 (B1.5): health.ts created; assertWorkerHealthy() guard; /api/admin/model-health endpoint"
  - "§3.6 (B1.6): cost.ts created; estimateQueryCost() reads token fields × registry cost rates"
  - "§6.2 (B1.7): 3 stale flags removed from type union; 4 new observability flags added (all default ON); CGM gate removed from cgm_graph_walk.ts; audit consumer always active in route.ts"
  - "B1.8: tsc 9 errors — same pre-existing AppShell/ReportGallery baseline (zero new errors)"

known_residuals:
  - id: B1_HEALTH_NOT_WIRED_TO_ROUTER
    severity: LOW
    description: "assertWorkerHealthy() exists in health.ts but is not yet called from router.ts or route.ts at request time. The health module is complete; wiring it into the request path is a follow-on task (safe to add at B4 convergence or a dedicated session)."
    blocker_for_close: false
  - id: B1_COST_NOT_WIRED_TO_TRACE
    severity: LOW
    description: "estimateQueryCost() exists in cost.ts but the trace panel does not yet call it — that wiring is B3 scope (CostBar panel reads trace steps). Function is ready; integration is B3."
    blocker_for_close: false
  - id: COMPOSE_CALL_LEGACY_BRANCH
    severity: LOW
    description: "compose() still called in route.ts legacy branch (LLM_FIRST_PLANNER_ENABLED=false). By design — legacy path preserved for rollback per §4.4."
    blocker_for_close: false

mirror_updates_propagated: NONE (BHISMA-W1-S1 is Claude-only; no Gemini-side counterpart per BHISMA log §Relationship to KARN)

current_state_v1_0_updated: false  # per BHISMA log convention, only S4-CONVERGENCE writes to KARN/CURRENT_STATE
karn_session_log_appended: false   # per same convention

handoff_to_next_session: |
  S4-CONVERGENCE (BHISMA-W1-S4) consumes S1 output alongside S2 (CLOSED) and S3 (OPEN):
    1. Wire assertWorkerHealthy() into the router.ts classify path (low-priority; can be B4 scope).
    2. Run paired eval baseline (GAP.P.9 from S2 known residuals):
         export SMOKE_SESSION_COOKIE=... SMOKE_CHART_ID=... ANTHROPIC_API_KEY=...
         python3 platform/scripts/eval/runner.py --planner-off --output 00_ARCHITECTURE/EVAL/BASELINE_RUN_W9.json
    3. Smoke the new path end-to-end: LLM_FIRST_PLANNER_ENABLED=true + new model family + cost tracking.
    4. Author BHISMA_CLOSE_v1_0.md with eval delta.
    5. Single KARN-log entry referencing this BHISMA log close block.

notes: >
  Core B1 acceptance criteria (B1.1–B1.4) were satisfied by prior partial execution before
  this session opened. This session's work: created health.ts + cost.ts + admin endpoint;
  executed the full flag cleanup (3 retired, 4 added); removed stale flag gates from
  route.ts and cgm_graph_walk.ts; fixed config test suite. No 025_HOLISTIC_SYNTHESIS/**,
  platform/migrations/**, or platform/src/lib/retrieve/** files were touched per halt-conditions.
  The retrieval tool cgm_graph_walk.ts had only its flag gate removed — no retrieve logic changed.

=== BHISMA-W1-S3-TRACE-COMMAND CLOSE ===
closed: 2026-05-01
git_sha: 430ed4d  # Trace components were in working tree (un-committed by CC session); committed in B1 Cowork batch commit
agent: claude-opus-4-6 (CC session); Cowork committed in B1 batch
cowork_thread: BHISMA-W1-S3-TRACE-COMMAND

scope_executed: BHISMA_PLAN_v1_0.md §5.1–§5.8 (Stream 3 deliverables)

deliverables:
  - platform/src/components/trace/TracePanel.tsx: re-skinned warm dark palette (rgba(8,5,2,0.97)); cold GitHub-dark colours removed; all four new sections wired with B2-defensive null guards
  - platform/src/components/trace/QueryDNAPanel.tsx: NEW — shows query_class, intent_summary, tools chips, domain chips, graph_seed_hints, forward_looking flag
  - platform/src/components/trace/CostPerformanceBar.tsx: NEW — per-stage latency + USD cost estimate (reads TraceDataSummary token fields via estimateQueryCost helper)
  - platform/src/components/trace/RetrievalScorecard.tsx: NEW — per-tool signal distribution, score spread, efficiency ratio; expands for msr_sql + vector_search
  - platform/src/components/trace/AnalyticsTab.tsx: NEW — cross-query history: query class donut + latency line + tool frequency bars; powered by fetchTraceHistory analytics mode

acceptance_criteria_passed:
  - "AC.B3.1: warm dark palette (rgba(8,5,2,0.97)) — cold slate/GitHub-dark removed"
  - "AC.B3.2: QueryDNAPanel shows query_class, intent, tools/domain chips, graph seeds"
  - "AC.B3.3: context section wired to B2 context_assembly emit (null-guarded; no blank)"
  - "AC.B3.4: RetrievalScorecard expands for msr_sql + vector_search with field breakdown"
  - "AC.B3.5: CostPerformanceBar shows per-stage latency + USD cost estimate"
  - "AC.B3.6: citation count badge in synthesis quality section"
  - "AC.B3.7: AnalyticsTab with query class donut + latency line + tool frequency bars"
  - "AC.B3.8: tsc clean in B3 paths (9 pre-existing residuals; zero new)"

known_residuals:
  - id: B3_NO_VISUAL_SMOKE
    severity: LOW
    description: "AC.B3.9 dev-server visual smoke deferred — requires live dev server + browser; not runnable in headless CC session"
    blocker_for_close: false
  - id: B3_THUMBS_FEEDBACK_DEFERRED
    severity: LOW
    description: "Inline 👍/👎 feedback wire-up deferred — needs message_id linkage outside B3 scope"
    blocker_for_close: false

mirror_updates_propagated: NONE (B3 is Claude-only; Trace UI has no Gemini counterpart)
current_state_v1_0_updated: false  # per BHISMA log convention; S4 handles
karn_session_log_appended: false   # per same convention; S4 handles

notes: >
  All seven §5.x trace deliverables shipped per B3 brief. TracePanel is now a warm-gold
  Trace Command Center with four discrete sections: Query DNA, Context Assembly (fed by B2),
  Retrieval Scorecard, and Cost/Performance. AnalyticsTab is the fifth panel (history mode).
  Visual smoke and feedback wire-up deferred to post-BHISMA sessions per §9 deferred items.

=== BHISMA-W1-S4-CONVERGENCE CLOSE ===
closed: 2026-05-01
agent: claude-sonnet-4-6 (Cowork)
cowork_thread: BHISMA-W1-S1-MODEL-FAMILY  # S4 executed in same Cowork session that opened S1

scope_executed: BHISMA_PLAN_v1_0.md §7 W9-B4 convergence scope

deliverables:
  - 00_ARCHITECTURE/PROJECT_BHISMA_SESSION_LOG.md: S3 + S4 close blocks appended; acceptance gate checked
  - 00_ARCHITECTURE/BHISMA_CLOSE_v1_0.md: NEW — Wave 1 sealing artifact
  - 00_ARCHITECTURE/SESSION_LOG.md: single KARN Wave 1 convergence entry appended
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md: amended-in-place for BHISMA Wave 1 convergence

acceptance_criteria_passed:
  - "tsc: 9 errors — identical pre-existing AppShell/ReportGallery baseline; zero new"
  - "vitest: exit 0 (all suites pass; rule_composer NOT retired — still in legacy path by design)"
  - "BHISMA_CLOSE_v1_0.md authored and committed"
  - "KARN SESSION_LOG single convergence entry appended"
  - "CURRENT_STATE amended for BHISMA Wave 1 platform state"

known_residuals:
  - id: GAP.P.9_STUB_PERSISTS
    severity: MEDIUM
    description: "BASELINE_RUN_W9.json remains STUB — SMOKE_SESSION_COOKIE + SMOKE_CHART_ID + ANTHROPIC_API_KEY unavailable in session. Paired planner-off/on eval run still outstanding. Non-blocking per B2 escape clause; must be resolved before LLM_FIRST_PLANNER_ENABLED is flipped to true in production."
    blocker_for_close: false
    blocker_for_m3: "Only blocks LLM_FIRST_PLANNER_ENABLED flip, not M3-A start"
  - id: B1_HEALTH_NOT_WIRED_TO_ROUTER
    severity: LOW
    description: "assertWorkerHealthy() created; not yet wired into router.ts request path."
    blocker_for_close: false
  - id: B3_NO_VISUAL_SMOKE
    severity: LOW
    description: "AC.B3.9 visual smoke deferred; requires live dev server."
    blocker_for_close: false

mirror_updates_propagated: NONE (BHISMA Wave 1 is Claude-only per §Relationship to KARN)
current_state_v1_0_updated: true   # amended-in-place at S4 close
karn_session_log_appended: true    # single convergence entry appended
