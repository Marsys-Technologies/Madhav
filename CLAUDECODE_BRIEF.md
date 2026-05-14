---
status: HALTED
session_id: AIOPS_AD_4
phase: AD.4
phase_name: "Call-site migration + legacy-path preservation + flag-off equivalence"
next_session: AIOPS_AD_4
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
bail_out:
  phase: AD.4
  reason: >
    AC.AD4.2 (zero streamText/generateText outside adapters) is not achievable
    with the current adapter architecture. Two classes of call sites block migration:
    (1) single_model_strategy.ts and panel_strategy.ts use streamText with
    stopWhen: stepCountIs(5) + smoothStream — multi-step tool use that the adapter
    layer (a single-call streamText wrapper) does not support.
    (2) consume/route.ts (971 lines) pipes StreamTextResult.toUIMessageStreamResponse()
    directly to the HTTP SSE response — the adapter returns ReadableStream<ModelInteractionEvent>
    which is architecturally incompatible without a new SSE bridge.
  last_completed_step: "AD.3 committed (f92f898); AD.4 inventory produced; bail triggered before any migration work"
  attempted_remediations:
    - "Reviewed single_model_strategy.ts lines 395-465: confirmed stepCountIs(5) + smoothStream in use"
    - "Reviewed consume/route.ts size (971 lines): toUIMessageStreamResponse() piping confirmed"
    - "Bail triggered per brief §7 trigger: 'A call site requires deep refactoring that pulls in >5 unrelated files'"
  suggested_native_action: >
    Before re-triggering AD.4, the brief must be revised to:
    (a) Narrow AC.AD4.2 to exclude the SSE-streaming synthesis path and consumer route
        (these are Phase 3 territory or require a separate architectural decision),
        OR
    (b) Extend the adapter layer in a new AD.3.5 sub-phase to support:
        - Multi-step tool use (passthrough of stopWhen / stepCountIs from QueryRequest)
        - A StreamTextResult-compatible return type for consume/route.ts SSE piping,
        OR
    (c) Split AD.4 into two parts: AD.4a (scripts + probe + checkpoints — simple generateText
        callers) and AD.4b (synthesis + consume SSE path — requires architecture decision).
    The simplest path is (c): AD.4a targets the ~8 simple generateText call sites
    (probe/runner.ts, eval scripts, checkpoint files, title.ts, health.ts) and leaves
    the synthesis streaming path for a native-scoped AD.4b.
  stack_trace_or_logs: |
    Inventory of blocking call sites:
    - src/lib/synthesis/single_model_strategy.ts:412 — streamText with stopWhen:stepCountIs(5), smoothStream, onFinish audit
    - src/app/api/chat/consume/route.ts:2 — streamText piped via toUIMessageStreamResponse() SSE
    - src/lib/synthesis/panel_strategy.ts:120 — streamText passthrough for panel verbatim output
    - src/lib/synthesis/panel/member_runner.ts:120 — generateText for panel members
    - src/lib/synthesis/panel/adjudicator.ts:88 — generateText for adjudication
    - src/lib/pipeline/pipeline_planner.ts:226 — generateText with tool-choice
    - src/lib/pipeline/planner_context_builder.ts:85 — generateText for context
    - src/app/api/chat/build/route.ts:91 — streamText for build route (separate product)
    Simpler sites (safe to migrate once brief is revised):
    - src/lib/aiops/probe/runner.ts:56 — generateText (single call, no tools)
    - src/lib/checkpoints/checkpoint_4_5.ts:69 — generateText
    - src/lib/checkpoints/checkpoint_5_5.ts:92 — generateText
    - src/lib/checkpoints/checkpoint_8_5.ts:83 — generateText
    - src/lib/conversations/title.ts:43 — generateText (title generation)
    - src/lib/models/health.ts:66 — generateText (health check ping)
    - scripts/retrieval/test_classify.ts:47 — generateText (test utility)
---

# CLAUDECODE_BRIEF — AIOPS_AD_4 (HALTED)

See `bail_out` block above. Resume after native revises the brief.

*End of PHASE_AD_4_BRIEF.md (HALTED)*
