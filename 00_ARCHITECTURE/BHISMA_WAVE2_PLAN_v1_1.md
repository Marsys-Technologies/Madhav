---
artifact: BHISMA_WAVE2_PLAN_v1_1
title: "BHISMA Wave 2: Universal Query Engine & Observability Architecture"
version: 1.1
status: CURRENT
canonical_id: BHISMA_WAVE2_PLAN
created_date: 2026-05-01
last_updated: 2026-05-01
scope: "Parallel to M3; independent execution; engineering specification; 9 post-v1.0 gaps addressed"
relationship_to_M3: "Standalone workstream; no file conflicts; M3 may run in parallel without blocking"
author: Claude (Haiku 4.5)
changelog:
  v1.1:
    date: 2026-05-01
    summary: "Gap-hardened specification; 5 parallel streams (added EVAL), 58 tasks, 3-4 week implementation; nine architectural gaps resolved"
    key_changes:
      - "Added Stream EVAL (4 tasks: planner golden test set, smoke test runner, A/B comparison framework, regression detection)"
      - "Gap 1 (Planner Prompt Architecture): New UQE-4a task, compressed manifest format, structured output enforcement"
      - "Gap 2 (Token Budget Enforcement): New UQE-5a task, budget arbitration algorithm"
      - "Gap 3 (Planner Latency UX): New UQE-5b task, planning_start/planning_done SSE events; new TRACE-0 task"
      - "Gap 4 (Planner Fallback): New UQE-5c task, circuit breaker pattern"
      - "Gap 5 (Planner Evaluation): New Stream EVAL with 4 tasks"
      - "Gap 6 (Citation Gate): Replaced UQE-3 with UQE-3-REVISED, two-layer citation validation"
      - "Gap 7 (Conversation History): New UQE-4b task, planner context builder"
      - "Gap 8 (TRACE Hydration): Added SSE → Panel mapping, panel state machine, skeleton UI specs for all 10 panels"
      - "Gap 9 (DeepSeek R1 Reasoning): Updated MON-5, llm_call_log schema, TRACE-1 R1 badge + thinking display"
      - "Total tasks: 40 → 58 (15 UQE + 10 MON + 10 TRACE + 6 SCHEMA + 5 EVAL)"
      - "Total effort estimate increased by ~200 hours for gap-specific work"
  v1.0:
    date: 2026-05-01
    summary: "Initial comprehensive specification; four parallel streams, 40 tasks, 3-4 week implementation"
---

# BHISMA WAVE 2: Universal Query Engine & Observability Architecture

**Version 1.1 · Gap-Hardened Production Specification**

## Executive Summary

BHISMA Wave 2 transforms the MARSYS-JIS query pipeline from a brittle, class-gated architecture into a robust, LLM-driven universal query engine backed by comprehensive observability. Wave 1 (completed, commit 03770d2) hardened infrastructure; Wave 2 hardens the request-response path and makes it visible.

The v1.0 specification identified 7 critical bugs and 4 architectural gaps. Post-v1.0 analysis uncovered 9 additional architectural gaps (G5–G13) that expose the planner to latency, token explosion, fallback failure, and evaluation blindness. This v1.1 revision systematically addresses all 9 gaps through 18 new tasks and revisions to 8 existing tasks.

The transformation spans five parallel streams across 58 tasks:

1. **Stream UQE** — Universal Query Engine (15 tasks: UQE-1–UQE-10 + 4a, 4b, 5a, 5b, 5c)
2. **Stream MON** — Monitoring Infrastructure (10 tasks: MON-1–MON-10)
3. **Stream TRACE** — Trace UI Modernization (10 tasks: TRACE-0–TRACE-9)
4. **Stream SCHEMA** — Query Investigation Database (6 tasks: SCHEMA-1–SCHEMA-6)
5. **Stream EVAL** — Planner Evaluation Framework (5 tasks: EVAL-1–EVAL-5) **NEW**

Wave 2 is **independent of M3** (macro-phase) and runs in parallel. No shared files; rollback at any time.

**Delivery:** 3–4 weeks, four concurrent Claude Code sessions. Gap-hardened work adds ~200 dev-hours to original 853-hour estimate.

---

## §1 Ground Reality Audit: Known Bugs, Gaps & Resolutions

### Critical Bugs (Production Impact — from v1.0)

#### Bug B2W-1: remedial_codex_query SQL Error
**Severity:** CRITICAL | **Status:** Identified 2026-04-30 | **Task:** UQE-1  
**Root Cause:** Column "canonical_id" does not exist in remedial_codex table schema  
**Fix:** Update column reference; test against live chart  
**Acceptance:** SELECT returns ≥1 row; citation_count ≥ 1

#### Bug B2W-2: MSR SQL Empty Seed Arrays
**Severity:** HIGH | **Status:** Identified 2026-04-30 | **Task:** UQE-7  
**Root Cause:** compose_bundle emits planets=[], houses=null → WHERE planet = ANY($planets) returns zero rows  
**Fix:** Path A (immediate): Add domain-only fallback; Path B (architectural): Planner populates from query text (UQE-5)  
**Acceptance:** msr_sql returns ≥1 row for remedial queries

#### Bug B2W-3: Pattern/Contradiction/Resonance Registers Return Zero Rows
**Severity:** HIGH | **Status:** Identified 2026-04-30 | **Task:** UQE-7  
**Root Cause:** Empty seed_hints from compose_bundle  
**Fix:** Same as B2W-2  
**Acceptance:** Each register returns ≥1 row for test queries

#### Bug B2W-4: Vector Search Not Authorized for Remedial Class
**Severity:** HIGH | **Status:** Identified 2026-04-30 | **Task:** UQE-6  
**Root Cause:** CAPABILITY_MANIFEST excludes vector_search from tools_authorized when query_class=remedial  
**Fix:** Remove class-based gating; let UQE planner decide per query  
**Acceptance:** vector_search authorized for all query classes

#### Bug B2W-5: Synthesis Model Non-Determinism (RC-6)
**Severity:** HIGH | **Status:** Identified 2026-04-30 | **Task:** UQE-2  
**Root Cause:** Synthesis model temperature unset (defaults to model's non-zero value)  
**Fix:** Set temperature=0 for single_answer queries; temperature=0.3 for exploratory  
**Acceptance:** temperature visible in trace; no variation for identical inputs

#### Bug B2W-6: Ungrounded Citations (B.3 Violation)
**Severity:** MEDIUM | **Status:** Identified 2026-04-30 | **Task:** UQE-3-REVISED  
**Root Cause:** Bugs B2W-1–B2W-4 leave synthesis with ≤20 L1 facts; citation_count=0  
**Fix:** Structural — fixing B2W-1–B2W-4 + two-layer citation validation enables corpus grounding  
**Acceptance:** Hard gate raises PipelineError if citation_count=0 AND prescriptive after deployment

#### Bug B2W-7: Trace Step Sequence Collisions
**Severity:** MEDIUM | **Status:** Identified 2026-04-30 | **Task:** UQE-9  
**Root Cause:** context_assembly and vector_search both emit step_seq=9; synthesis orphaned at seq 11  
**Fix:** Atomic increment for step_seq; parallel-group awareness  
**Acceptance:** step_seq unique within query_id

### Architectural Gaps from v1.0 (G1–G4)

| Gap | Title | v1.0 Task |
|-----|-------|-----------|
| G1 | Classify Bottleneck | UQE-6 |
| G2 | Per-Tool Planner Always Disabled | UQE-4, UQE-5 |
| G3 | Incomplete LLM Call Inventory | MON-1–5 |
| G4 | No Comprehensive Query Investigation Log | SCHEMA-1–6 |

### §1.3 Post-v1.0 Architectural Gaps (G5–G13)

#### Gap G5: Planner Prompt Architecture — CRITICAL TECHNICAL RISK
**Severity:** HIGH | **Root Cause:** CAPABILITY_MANIFEST has 108 entries (~21,600 tokens at ~200 tokens/entry). Planner receives manifest + query + history → exceeds Haiku's practical context budget before query appears. Every planning call expensive.  
**Resolution:** New task **UQE-4a** (prerequisite to UQE-4 and UQE-5)
- Design and implement Compressed Manifest Format
- Full 108-entry manifest serialized as ~2–3K tokens (vs ~21K raw)
- Structured output enforcement via JSON schema
- Malformed JSON handling: 1 retry on parse failure, then fallback (G8 circuit breaker)
- Files: `platform/src/lib/pipeline/manifest_planner.ts`, `manifest_compressor.ts`, `00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md`
- Effort: 1 week
- Acceptance: Compressed manifest ≤3K tokens; planner input ≤5K tokens total; valid JSON on ≥95% of test queries

#### Gap G6: Token Budget Enforcement — NO MECHANISM EXISTS
**Severity:** HIGH | **Root Cause:** Planner emits token_budget per tool but nothing enforces it. Tools can return more than budgeted. Sum of budgets may exceed synthesis model context window.  
**Resolution:** New task **UQE-5a** (runs after UQE-5, before context_assembly)
- Budget arbitration algorithm: proportionally trim priority=3, then priority=2, never below 200 tokens
- Per-model context window accounting (Haiku 64K, Gemini 1M, GPT-4o 128K, deepseek 64K)
- Context assembly truncates results to budget at line level
- Files: `platform/src/lib/pipeline/budget_arbiter.ts`, update `context_assembly.ts`
- Effort: 6–8 hours
- Acceptance: context_assembly total_tokens ≤ (model_max_context × 0.85) on 100% of queries

#### Gap G7: Planner Latency Adds Pre-Token Delay; No UX Signal
**Severity:** MEDIUM | **Root Cause:** Planner runs before any tool fires, adding 500–1500ms of silence before first synthesis token. Current SSE stream starts within ~200ms. No "planning in progress" signal to client.  
**Resolution:** New task **UQE-5b** (implement new SSE events) + new task **TRACE-0** (planning indicator UI)
- SSE events: planning_start (emit immediately when planner begins), planning_done (when plan JSON validated)
- TRACE-0 component: `PlanningIndicator.tsx` shows "Analyzing your question…" pulse, collapses into timeline post-planning
- Files: `platform/src/lib/trace/types.ts` (new events), `platform/src/components/trace/PlanningIndicator.tsx`
- Effort: UQE-5b 3–4 hours, TRACE-0 4–6 hours
- Acceptance: planning_start within 100ms of query receipt; planning_done within 200ms of plan validation

#### Gap G8: No Planner Fallback Circuit Breaker
**Severity:** HIGH | **Root Cause:** If worker LLM API degraded or planner times out, every query silently hangs or errors. Feature flag (LLM_FIRST_PLANNER_ENABLED) is static toggle requiring manual intervention.  
**Resolution:** New task **UQE-5c: Planner Circuit Breaker**
- Circuit breaker pattern (3 failures → open for 5 minutes; half-open after recovery interval)
- Fallback path: skip manifest planner, use minimal default plan (l1_facts_query + cgm_graph_walk), set fallback_used=true
- Emit step_error trace event with error_stage='planner'
- Circuit triggers: planner timeout (3s), malformed JSON after 1 retry, 5xx API error
- Files: `platform/src/lib/pipeline/planner_circuit_breaker.ts`, wrap manifest_planner.ts
- Effort: 6–8 hours
- Acceptance: Circuit opens after 3 timeouts; fallback queries complete successfully; circuit auto-recovers

#### Gap G9: No Evaluation Framework for Planner Quality
**Severity:** HIGH | **Root Cause:** No way to detect planner regressions, no golden test set, no A/B comparison. Model update silently degrades planner behavior.  
**Resolution:** New Stream **EVAL** (4 tasks; see §3.5 below)
- EVAL-1: Golden test set (25 labeled query→plan pairs)
- EVAL-2: Smoke test runner (tool_recall ≥0.80, tool_precision ≥0.90)
- EVAL-3: A/B comparison framework (compare old classify vs new planner)
- EVAL-4: Regression detection (post-deployment CI check; alert on tool_recall drop)

#### Gap G10: B.3 Citation Gate Is Too Blunt
**Severity:** MEDIUM | **Root Cause:** Current citation_count heuristic counts SIG.MSR.NNN patterns. A model can cite from training data (false negative: citation_count=0 but response cites real sources). A model can include signal ID in boilerplate (false positive). Hard gate citation_count=0 AND prescriptive → PipelineError blocks good responses, waves through bad ones.  
**Resolution:** Replace UQE-3 with **UQE-3-REVISED: Precision Citation Validation**
- Layer 1 (existence): count SIG.MSR.NNN patterns in output (current heuristic)
- Layer 2 (context cross-reference): verify each citation_id exists in assembled context JSONB
- Gate logic: verified_citations ≥1 → PASS; verified_citations=0 AND total_citations>0 → WARN (training data leak); verified_citations=0 AND total_citations=0 AND prescriptive → ERROR
- Feature flag: CITATION_GATE_OVERRIDE (default false; set true for admin override)
- Files: `platform/src/lib/audit/citation_validator.ts`, update `validator.ts`, update `feature_flags.ts`
- Effort: 6–8 hours
- Acceptance: Verified citations ≥1 on known-good remedial queries; training data citations produce WARN; gate override works

#### Gap G11: Conversation History in Planner Context Unspecified
**Severity:** MEDIUM | **Root Cause:** 10-turn conversation = 15–20K tokens. If planner receives this + manifest, context budget exceeded before query appears.  
**Resolution:** New task **UQE-4b: Planner Context Builder**
- Max 2 conversation turns; max 300 tokens per turn; max 600 tokens total history
- If history > 600 tokens: call worker model to summarize (micro-call ~100 input → ~50 output tokens)
- Track history_summary call in llm_call_log with call_stage='history_summary'
- Files: `platform/src/lib/pipeline/planner_context_builder.ts`, update `manifest_planner.ts`
- Effort: 4–6 hours
- Acceptance: Planner context ≤5K tokens on 100% of queries regardless of history length

#### Gap G12: TRACE Panels Have No Real-Time Hydration Strategy
**Severity:** MEDIUM | **Root Cause:** 10 new panels specified but no clear state machine or skeleton strategy. Frontend implementation will be ad hoc and inconsistent. Panels don't know when data arrives or how to handle partial updates.  
**Resolution:** Add full hydration strategy to §10 (TRACE Architecture)
- SSE Event → Panel Mapping table (which events hydrate which panels)
- Panel State Machine (idle → waiting → partial → complete → error)
- Skeleton UI specs per panel (1–3 row skeletons per panel type)
- Implementation pattern: useTracePanel hook + TraceContainer as single SSE subscriber
- Files: All TRACE components (TRACE-0 through TRACE-9)
- See detailed mapping in §10 below

#### Gap G13: DeepSeek R1 Reasoning Tokens Not Tracked
**Severity:** LOW | **Root Cause:** R1 uses `<think>...</think>` blocks stripped by extractReasoningMiddleware. R1 reasoning tokens cost money but currently invisible — plan marks reasoning_tokens as "o-series only".  
**Resolution:** Updates to **MON-5**, llm_call_log schema, TRACE-1
- After synthesis call: if model_id='deepseek-reasoner', extract reasoning from stream part
- Estimate token count: `Math.ceil(reasoning_text.length / 4)` (rough; DeepSeek doesn't expose exact via AI SDK)
- Store in llm_call_log.reasoning_tokens; store full trace in payload.reasoning_trace
- Update TRACE-1: R1 calls show reasoning_tokens bar; add "View thinking" button for reasoning trace
- Files: `platform/src/lib/synthesis/single_model_strategy.ts`, `trace/types.ts`, `components/trace/LLMCallMap.tsx`
- Effort: 3–4 hours
- Acceptance: deepseek-reasoner calls show non-null reasoning_tokens; "View thinking" button renders

---

## §2 LLM Usage Map: Current → Proposed (Updated for v1.1)

Complete inventory of every LLM call in the system:

| Call ID | Stage | Current Model | Traced? | Proposed | New Trace | Gap Resolution |
|---------|-------|---|---|---|---|---|
| LLM-1 | Classify | family worker | partial | **REMOVE** | N/A | — |
| **LLM-1-NEW** | **Manifest Planner** | **family worker (Haiku)** | **NO** | **family worker** | **NEW** | G5, G6, G8 |
| **LLM-1-HIST** | **History Summarizer** | **family worker (Haiku)** | **NO** | **family worker** | **NEW** | G11 |
| LLM-2 | Synthesis | user-selected | yes | user-selected | temperature tracking | G10 |
| **LLM-3** | **Title Generation** | **haiku** | **NO** | **haiku** | **NEW** | — |
| LLM-4 | o-series Reasoning | o1/o3/o4-mini | partial | o1/o3/o4-mini | reasoning_tokens | — |
| **LLM-5** | **R1 Reasoning** | **deepseek-reasoner** | **NO** | **deepseek-reasoner** | **reasoning_tokens** | G13 |

**Cost per LLM call estimate:**
- LLM-1-NEW (Planner): Haiku 300→100 tokens, ~$0.00009
- LLM-1-HIST (History Summary, conditional): Haiku 100→50 tokens, ~$0.00003
- LLM-2 (Synthesis): varies by model; $0.01–$0.10
- LLM-3 (Title): Haiku 200→50 tokens, ~$0.00006
- LLM-4 (o-series reasoning): o1-mini via anthropic-sdk, $0.003–$0.03
- LLM-5 (R1 reasoning): deepseek $0.0014/1M input, $0.0056/1M output (reasoning billed at output rate)

---

## §3 Five Parallel Streams: 58 Tasks

### Stream UQE: Universal Query Engine (15 tasks)

**UQE-1: Fix remedial_codex_query SQL**
- **Description:** Identify schema post-migration; update column reference
- **File:** `platform/src/lib/tools/remedial_codex_query.ts`
- **Effort:** 1–2 hours
- **Acceptance:** SELECT returns ≥1 row for known remedial queries; citation_count ≥ 1 post-synthesis

**UQE-2: Set Synthesis Temperature Logic**
- **Description:** Add temperature=0 for single_answer queries; temperature=0.3 for exploratory
- **File:** `platform/src/lib/synthesis/single_model_strategy.ts` (~line 150–200)
- **Effort:** 4–6 hours
- **Acceptance:** Byte-identical input → identical output (×5 test loops); temperature visible in trace

**UQE-3-REVISED: Precision Citation Validation (two-layer gate)**
- **Description:** Layer 1: count SIG.MSR.NNN patterns (heuristic). Layer 2: cross-ref each citation against assembled context JSONB. Emit WARN for training data citations; ERROR only for prescriptive zero-citation.
- **Files:** `platform/src/lib/audit/citation_validator.ts` (new), update `validator.ts`, update `platform/src/lib/config/feature_flags.ts` (add CITATION_GATE_OVERRIDE)
- **Effort:** 6–8 hours
- **Acceptance:** Verified citations ≥1 on known-good remedial queries; training data citations produce WARN not ERROR; gate override flag works

**UQE-4: Full Manifest Exposure**
- **Description:** Ensure worker LLM can read entire CAPABILITY_MANIFEST. Remove tools_authorized class-based gating. Prerequisite: UQE-4a (planner prompt architecture design must be complete first).
- **File:** `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- **Effort:** 1–2 weeks (includes prompt engineering, depends on UQE-4a)
- **Acceptance:** Planner reads full manifest; JSON valid; reasoning present in plan output

**UQE-4a: Planner Prompt Architecture (PREREQUISITE to UQE-4)**
- **Description:** Design and implement Compressed Manifest Format. 108-entry manifest → ~2–3K tokens. Structured output enforcement via JSON schema. Malformed JSON handling with 1 retry + fallback.
- **Interfaces:**
  ```typescript
  interface CompressedManifestEntry {
    t: string         // tool_name (short key)
    d: string         // one-sentence description (≤15 words)
    p: string[]       // param names only (not full schema)
    c: 'low'|'med'|'hi'  // token_cost_tier
    a: string         // data_asset_id
  }

  interface PlanSchema {
    tool_calls: Array<{
      tool_name: string     // enum of valid names
      params: Record<string, unknown>
      token_budget: number  // 100–2000
      priority: 1 | 2 | 3
      reason: string
    }>
  }
  ```
- **Files:**
  - `platform/src/lib/pipeline/manifest_compressor.ts` (new)
  - `00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md` (new, living document)
  - Document includes: system prompt (complete text), 2 few-shot examples (remedial + interpretive), compressed manifest spec, JSON schema, evaluation rubric
- **Effort:** 1 week
- **Acceptance:** Compressed manifest ≤3K tokens; planner input ≤5K tokens total; valid JSON on ≥95% of test queries

**UQE-4b: Planner Context Builder (Conversation History Strategy)**
- **Description:** Take last 2 conversation turns (max 300 tokens each, max 600 total). If history >600 tokens, call worker model to summarize (~100 input, ~50 output). Track history_summary call in llm_call_log.
- **Files:** `platform/src/lib/pipeline/planner_context_builder.ts` (new), update `manifest_planner.ts`
- **Effort:** 4–6 hours
- **Acceptance:** Planner context ≤5K tokens on 100% of queries regardless of history length

**UQE-5: Universal Per-Tool Planner (ALWAYS-ON)**
- **Description:** Replace classify+compose with LLM-first planner. All queries route through universal planner. Depends on UQE-4a (prompt design) and UQE-4b (context builder).
- **Files:**
  - `platform/src/lib/pipeline/universal_query_engine.ts` (new)
  - `platform/src/lib/pipeline/manifest_planner.ts` (new)
  - Update routing in `platform/src/routes/api/chat.ts`
- **Effort:** 2–3 weeks (depends on UQE-4a, UQE-4b)
- **Acceptance:** All queries route through planner; planner latency p95 <500ms; fallback_used=false on ≥99% of queries

**UQE-5a: Token Budget Enforcement (Budget Arbitration)**
- **Description:** Implement budget arbitration algorithm. Trim priority=3 tools first (proportionally), then priority=2, never below 200 tokens per priority=1 tool. Context assembly truncates results to budget at token boundary.
- **Algorithm:**
  ```typescript
  interface BudgetArbiterConfig {
    synthesis_model_max_context: number  // from ModelMeta
    system_prompt_reserve: number        // ~800 tokens
    synthesis_guidance_reserve: number   // ~200 tokens
    safety_margin: number                // 0.85
  }

  function arbitrateBudgets(
    plan: UniversalToolCallSpec[],
    config: BudgetArbiterConfig
  ): UniversalToolCallSpec[] {
    const available = (config.synthesis_model_max_context * config.safety_margin)
      - config.system_prompt_reserve - config.synthesis_guidance_reserve
    const planned_total = plan.reduce((sum, t) => sum + t.token_budget, 0)
    if (planned_total <= available) return plan
    // Trim priority=3, then priority=2, preserving priority=1
  }
  ```
- **Files:** `platform/src/lib/pipeline/budget_arbiter.ts` (new), update `context_assembly.ts`
- **Effort:** 6–8 hours
- **Acceptance:** context_assembly total_tokens ≤ (model_max_context × 0.85) on 100% of queries

**UQE-5b: Planning Phase SSE Events (UX Signal)**
- **Description:** Add planning_start and planning_done SSE events. Emit planning_start when planner begins LLM call. Emit planning_done when plan JSON validated. Feeds TRACE-0 component.
- **Events:**
  ```typescript
  interface PlanningStartEvent {
    event: 'planning_start'
    query_id: string
    planner_model_id: string
    manifest_tool_count: number
  }

  interface PlanningDoneEvent {
    event: 'planning_done'
    query_id: string
    tool_count_planned: number
    tools_selected: string[]
    query_intent_summary: string
    planner_latency_ms: number
  }
  ```
- **Files:** `platform/src/lib/trace/types.ts` (update TraceEvent union), `manifest_planner.ts` (emit events)
- **Effort:** 3–4 hours
- **Acceptance:** planning_start appears within 100ms of query receipt; planning_done within 200ms of plan validation

**UQE-5c: Planner Circuit Breaker (Fallback Pattern)**
- **Description:** Implement circuit breaker (3 failures → open for 5 min; half-open after recovery). Fallback path: skip planner, use default plan (l1_facts + cgm), set fallback_used=true. Emit step_error with error_stage='planner'.
- **Triggers:**
  - Planner LLM timeout (>3s)
  - Malformed JSON after 1 retry
  - Worker API 5xx error
- **Files:** `platform/src/lib/pipeline/planner_circuit_breaker.ts` (new), wrap manifest_planner.ts
- **Effort:** 6–8 hours
- **Acceptance:** Circuit opens after 3 timeouts; fallback queries complete successfully; circuit auto-recovers after 5 minutes

**UQE-6: Remove Classify Step and Class-Based Gating**
- **Description:** Delete classify.ts, composer.ts, manifest_lookup.ts. Update routing to skip class-based tool authorization. All 8 tools now available post-planner.
- **Files:** Delete deprecated files; update `platform/src/routes/api/chat.ts` routing
- **Effort:** 1–2 weeks (routing refactor, depends on UQE-5)
- **Acceptance:** Classify step not in trace for any query; all tools available post-planning

**UQE-7: Domain-Only Fallback for MSR / Registers**
- **Description:** Add fallback when planets/houses arrays empty. Query by domain only (e.g., "remedial" → all remedial-category signals). Applies to msr_sql, pattern_register, contradiction_register, resonance_register.
- **Files:** `platform/src/lib/tools/msr_sql.ts`, `pattern_register.ts`, `contradiction_register.ts`, `resonance_register.ts`
- **Effort:** 4–6 hours
- **Acceptance:** Fallback returns ≥1 signal even with empty planet/house arrays

**UQE-8: Update CAPABILITY_MANIFEST with Metadata**
- **Description:** Add query_schema (JSON schema for params), token_cost_hint, linked_data_asset_id to all 8 tool entries.
- **File:** `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- **Effort:** 4–6 hours
- **Acceptance:** All 8 tools have complete metadata; manifest validates against schema

**UQE-9: Fix Trace Step Sequence Collisions**
- **Description:** Atomic increment for step_seq; parallel-group awareness. Ensure step_seq unique within query_id.
- **File:** `platform/src/lib/trace/emitter.ts`
- **Effort:** 2–4 hours
- **Acceptance:** step_seq unique within query_id across 100+ test queries

**UQE-10: Feature Flag Retirement Path**
- **Description:** Mark LLM_FIRST_PLANNER_ENABLED deprecated. Publish removal timeline in migration notes (v2.1).
- **File:** `00_ARCHITECTURE/MIGRATION_NOTES_v1_0.md` (new)
- **Effort:** 1 hour
- **Acceptance:** Deprecation timeline published; v2.1 removal date set

---

### Stream MON: Monitoring Infrastructure (10 tasks)

**MON-1: Design llm_call_log Table**
- **Description:** One row per LLM call (classify, planner, synthesis, title, reasoning). Schema includes reasoning_tokens for o-series AND deepseek-reasoner.
- **File:** Migration `platform/migrations/20260501_llm_call_log.sql`
- **Effort:** 2–3 hours
- **Acceptance:** Table created with 4 indexes; schema matches TypeScript interfaces

**MON-2: Design query_plan_log Table**
- **Description:** Full planner JSON output per query; metadata (tool count, confidence, fallback status).
- **File:** Migration `platform/migrations/20260501_query_plan_log.sql`
- **Effort:** 2–3 hours
- **Acceptance:** Table created; JSONB parses correctly; indexes present

**MON-3: Design tool_execution_log Table**
- **Description:** Per-tool execution (params, status, rows/chunks, latency, data_asset).
- **File:** Migration `platform/migrations/20260501_tool_execution_log.sql`
- **Effort:** 2–3 hours
- **Acceptance:** Table created; status='zero_rows' tracked via index

**MON-4: Design context_assembly_log Table**
- **Description:** Per-layer token contributions (L1, L2.5-signals, L2.5-patterns, L4, vector, CGM). B.3 compliance fields.
- **File:** Migration `platform/migrations/20260501_context_assembly_log.sql`
- **Effort:** 2–3 hours
- **Acceptance:** Table created; 6 layers logged per query; b3_compliant field indexed

**MON-5: Emit llm_call_log Writes (Updated for R1 reasoning tokens)**
- **Description:** Instrument planner, synthesis, title generation, history_summary LLM calls. Extract and log reasoning_tokens for o-series and deepseek-reasoner.
- **Files:**
  - `platform/src/lib/pipeline/manifest_planner.ts` (emit planner call)
  - `platform/src/lib/synthesis/single_model_strategy.ts` (emit synthesis + R1 reasoning extraction)
  - `platform/src/lib/tools/title_generator.ts` (emit title call)
  - `platform/src/lib/pipeline/planner_context_builder.ts` (emit history_summary call, conditional)
- **Effort:** 1 week
- **Acceptance:** llm_call_log populated for 100% of calls; reasoning_tokens non-null for o-series and deepseek-reasoner; tokens match SDK

**MON-6: Emit query_plan_log Write**
- **Description:** Write planner output after JSON validation. Capture parsing_success, parse_error, fallback_used.
- **Files:** `manifest_planner.ts`, `platform/src/lib/query_investigation.ts` (new helper)
- **Effort:** 4–6 hours
- **Acceptance:** query_plan_log one row per query; parsing errors captured; fallback_used=true tracked

**MON-7: Emit tool_execution_log Writes**
- **Description:** Log every tool's execution (params, result count, status, latency). Called at end of each tool fetch.
- **Files:** All 6 tool implementation files (l1_facts_query.ts, msr_sql.ts, etc.)
- **Effort:** 1–2 weeks
- **Acceptance:** All tools emit records; status='zero_rows' captured; error_code captured

**MON-8: Emit context_assembly_log Write**
- **Description:** Log per-layer token contributions after assembly. Denormalize layer totals. Set citation_count post-synthesis.
- **File:** `platform/src/lib/pipeline/context_assembly.ts`, update post-synthesis
- **Effort:** 4–6 hours
- **Acceptance:** Layer logs correct; token sums match input; b3_compliant field accurate

**MON-9: Create /api/investigation/:query_id Endpoint**
- **Description:** Return all logs for single query (joined across 4 tables + computed fields).
- **File:** `platform/src/routes/api/investigation/queries/:id.ts` (new)
- **Effort:** 1 week
- **Acceptance:** Endpoint returns all logs; response <500ms; joins consistent

**MON-10: Create Analytics Views (Updated for R1)**
- **Description:** Pre-computed materialized views: cost_by_model (includes deepseek reasoning), tool_health, grounding_health. Regular views for real-time analytics.
- **File:** `platform/migrations/20260501_analytics_views.sql` (new)
- **Effort:** 4–6 hours
- **Acceptance:** Views queryable; <1s response; reasoning_tokens included in cost calculations

---

### Stream TRACE: Trace UI Modernization (10 tasks)

**TRACE-0: Planning Progress Indicator (NEW — Gap G7)**
- **Description:** Animated component that shows during planner execution. Displays "Analyzing your question…" with pulse. Collapses into Query Timeline post-planning. Shows tool names as they resolve.
- **Component:** `platform/src/components/trace/PlanningIndicator.tsx` (new)
- **SSE Events:** planning_start, planning_done
- **Effort:** 4–6 hours
- **Acceptance:** Appears on planning_start within 100ms; planning_done with tool list appears within 200ms of plan validation; collapses into timeline at completion

**TRACE-1: LLM Call Map Panel**
- **Description:** Visual inventory of every LLM call; model, provider, tokens, latency, cost per call. Updated for R1 reasoning_tokens and "View thinking" button (Gap G13).
- **Component:** `platform/src/components/trace/LLMCallMap.tsx` (new)
- **Props:** `LLMCallMapProps`, `LLMCallRecord[]`
- **Hydration:** SSE events `step_start`(planner), `step_done`(synthesis), `step_done`(title); state machine: loading → partial → complete
- **Skeleton:** 2 card skeletons (planner + synthesis), 60px each
- **Effort:** 1 week
- **Acceptance:** All calls visible; cost/token totals correct; R1 reasoning_tokens bar shows; "View thinking" button functional

**TRACE-2: Query Plan Panel**
- **Description:** Render `UniversalQueryPlan` JSON; per-tool params, token_budget, priority, reason. Expandable cards. Drill-down to execution status post-tool-run.
- **Component:** `platform/src/components/trace/QueryPlan.tsx` (new)
- **Props:** `UniversalQueryPlan`
- **Hydration:** planning_done event; state machine: loading → partial → complete (as tools execute)
- **Skeleton:** 5 tool row skeletons, 36px each
- **Effort:** 1 week
- **Acceptance:** JSON structure visible; drill-down functional; zero_rows and error states highlighted

**TRACE-3: Tool Execution Panel**
- **Description:** Status cards per tool; params sent, rows/chunks returned, latency, data_asset. Color-coded by execution_status (ok=green, zero_rows=amber, error=red).
- **Component:** `platform/src/components/trace/ToolExecution.tsx` (new)
- **Props:** `ToolExecutionRecord[]`
- **Hydration:** step_start and step_done events for each tool; state machine: loading → adds one card → complete
- **Skeleton:** 6 tool cell skeletons in 3-column grid
- **Effort:** 1 week
- **Acceptance:** All tools visible; status colors correct; latency bars proportional

**TRACE-4: Data Asset Flow Panel**
- **Description:** Sankey-style diagram; data assets on left, Context Assembly on right. Arrow weight = tokens_contributed. Zero-contributing assets grey dashed; new channels pulse animation.
- **Component:** `platform/src/components/trace/DataAssetFlow.tsx` (new)
- **Implementation:** SVG-based (not third-party library)
- **Hydration:** context_assembly_log event; state machine: loading → complete
- **Skeleton:** SVG placeholder with 6 grey asset nodes
- **Effort:** 1 week (SVG rendering)
- **Acceptance:** Arrow weights proportional to tokens; interaction tooltips work; new channels pulse

**TRACE-5: Context Assembly Panel**
- **Description:** Stacked bar chart by layer (L1, L2.5-signals, L2.5-patterns, L4, vector, CGM). Drill-down to per-layer items with citations.
- **Component:** `platform/src/components/trace/ContextAssembly.tsx` (new)
- **Props:** `context_assembly_log` data
- **Hydration:** context_assembly_done event; state machine: loading → complete
- **Skeleton:** Empty stacked bar, 100% grey
- **Effort:** 1.5 weeks
- **Acceptance:** Token totals match; drill-in functional; layer labels correct

**TRACE-6: Synthesis Receipt Panel**
- **Description:** Input token breakdown by layer, temperature, citation_count, B.3 gate status, cost. Shows citation validation (Gap G10) results: verified_citations count, training_data_leak warning if applicable.
- **Component:** `platform/src/components/trace/SynthesisReceipt.tsx` (new)
- **Props:** Citation validation result, synthesis_input_tokens, synthesis_temperature, cost_usd, b3_compliant
- **Hydration:** synthesis_done event; state machine: loading → complete
- **Skeleton:** 3-field skeleton
- **Effort:** 1 week
- **Acceptance:** Citation count badge shows; B.3 status visible; training_data_leak warning appears when applicable

**TRACE-7: Query Timeline**
- **Description:** Horizontal SVG timeline; all steps as rectangles (x = started_at, width = latency). Parallel steps stacked. Color by step_type. Click any bar → drill into detail panel. Error bars red, zero_rows amber.
- **Component:** `platform/src/components/trace/QueryTimeline.tsx` (new)
- **Hydration:** All step events; state machine: builds timeline as steps arrive, finalizes on 'done'
- **Skeleton:** Empty timeline track with pulsing cursor
- **Effort:** 1.5 weeks (SVG layout)
- **Acceptance:** All steps in correct order; parallel visible; latency bars proportional

**TRACE-8: Cost Breakdown Panel**
- **Description:** Per-call cost breakdown; query total; session aggregates. Budget tracking (Gap G6): shows budget vs actual tokens per tool.
- **Component:** `platform/src/components/trace/CostBreakdown.tsx` (new)
- **Props:** `LLMCallRecord[]`, tool cost summaries, budget vs actual comparison
- **Hydration:** step_done events for cost updates; state machine: loading → partial → complete
- **Skeleton:** 2 row skeletons
- **Effort:** 4–6 hours
- **Acceptance:** Per-call breakdown correct; session aggregates sum; budget vs actual visible

**TRACE-9: Investigation Tab (Raw Logs)**
- **Description:** Tabular display of all 4 log tables (llm_call_log, query_plan_log, tool_execution_log, context_assembly_log). Drill-in; export to JSON/CSV. Pagination, filtering.
- **Component:** `platform/src/components/trace/InvestigationTab.tsx` (new)
- **Data:** Fetched via `/api/investigation/:query_id` endpoint (MON-9)
- **Hydration:** Lazy-loaded on tab click; state machine: idle → loading → complete
- **Skeleton:** Collapsed; expands only on user click
- **Effort:** 1.5 weeks
- **Acceptance:** All tables accessible; drill-in works; export valid JSON/CSV

---

### Stream SCHEMA: Query Investigation Database (6 tasks)

**SCHEMA-1: Audit Existing Schema**
- **Description:** Review query_trace_steps table; identify gaps vs new requirements (llm_call_log, query_plan_log, etc.).
- **Effort:** 4–6 hours
- **Acceptance:** Document current schema; list 8+ gaps

**SCHEMA-2: Design Query Investigation Log**
- **Description:** Separate tables (MON-1–4) vs consolidated table; decision + reasoning. Consolidated table is recommended for fast single-query investigation.
- **Effort:** 2–3 hours
- **Acceptance:** Design decision documented; tradeoffs listed

**SCHEMA-3: Write Migration Scripts**
- **Description:** Create 4 migrations for new tables (llm_call_log, query_plan_log, tool_execution_log, context_assembly_log). Idempotent; backwards-compatible.
- **Files:** `platform/migrations/20260501_llm_call_log.sql`, `query_plan_log.sql`, `tool_execution_log.sql`, `context_assembly_log.sql` (4 files)
- **Effort:** 2–4 hours
- **Acceptance:** Migrations idempotent; apply cleanly to staging; schema matches TypeScript

**SCHEMA-4: Design Indexes for Investigation Patterns**
- **Description:** Indexes for 8 common investigation queries (by query_id, model_id, tool_name, error_code, b3_compliant, created_at, etc.).
- **Effort:** 2–3 hours
- **Acceptance:** Indexes cover all patterns; query plans verified on staging

**SCHEMA-5: Design /api/investigation/queries Endpoint**
- **Description:** Query index with filters (model, tool, date range, b3_compliant), pagination, sorting.
- **File:** `platform/src/routes/api/investigation/queries/index.ts` (new)
- **Effort:** 1 week
- **Acceptance:** Filters work; pagination correct; response <1s

**SCHEMA-6: Design Retention & Archival Policy**
- **Description:** 90-day hot window; archive to GCS; deletion schedule. Cleanup jobs scheduled.
- **File:** `00_ARCHITECTURE/RETENTION_POLICY_v1_0.md` (new)
- **Effort:** 4–6 hours
- **Acceptance:** Policy documented; cleanup jobs scheduled

---

### Stream EVAL: Planner Evaluation Framework (5 tasks — NEW)

**EVAL-1: Golden Test Set for Planner**
- **Description:** 25 manually-labeled query→plan pairs covering 5 remedial, 5 interpretive, 5 predictive, 5 compound, 5 edge-cases. Each pair includes expected_tools, expected_planets, expected_domain, min_tools, forbidden_tools.
- **File:** `platform/tests/eval/planner_golden_set.json`
- **Schema:**
  ```typescript
  interface GoldenTestCase {
    query_text: string
    expected_tools: string[]
    expected_planets: string[]
    expected_domain: string
    min_tools: number
    forbidden_tools: string[]
    reasoning: string
  }
  ```
- **Effort:** 4–6 hours
- **Acceptance:** 25 pairs documented; each has explicit acceptance criteria

**EVAL-2: Planner Smoke Test Runner**
- **Description:** Runs golden set against live planner; scores each plan. Metrics: tool_recall (expected tools present), tool_precision (no forbidden tools), param_quality (planets/houses correct). Pass threshold: tool_recall ≥0.80, tool_precision ≥0.90.
- **File:** `platform/tests/eval/run_planner_eval.ts` (new)
- **Effort:** 6–8 hours
- **Acceptance:** Runner executes without DB dependency; results written to JSON; exit code 1 if below threshold

**EVAL-3: A/B Comparison Framework**
- **Description:** Takes set of query_ids from production (old classify path). Runs same queries through new planner. Compares: tools_executed, citation_count, l2_token_ratio. Generates diff report: improvement / regression / neutral per query.
- **File:** `platform/scripts/eval/ab_comparison.ts` (new)
- **Effort:** 1 week
- **Acceptance:** Report generated for ≥10 queries; improvement/regression classification documented

**EVAL-4: Regression Detection (CI Integration)**
- **Description:** Post-deployment: run EVAL-2 smoke test on every deployment. Alert (log warning) if tool_recall drops below 0.75. Integrated into CI: `npm run eval:planner`.
- **File:** Updates to `package.json` scripts + CI configuration
- **Effort:** 3–4 hours
- **Acceptance:** CI runs eval; exits non-zero on regression; alert logged

**EVAL-5: Integration into Deployment Pipeline**
- **Description:** Hook EVAL-2 smoke test into pre-production and post-deployment checks. Establish baseline metrics. Document eval results in deployment notes.
- **File:** CI/CD configuration (`platform/.github/workflows/deploy.yml` or equivalent)
- **Effort:** 2–3 hours
- **Acceptance:** CI runs eval before production deployment; metrics tracked in metrics DB or logs

---

### Task Dependency Graph (Critical Path)

```
UQE-4a (Planner Prompt Arch) ──→ UQE-4 (Full Manifest) ──→ UQE-5 (Universal Planner)
                                                                 ↓
UQE-4b (Planner Context) ─────────────────────────────────────→ UQE-5
                                                                 ↓
UQE-5a (Budget Arbitration) ─→ context_assembly (dependency)
UQE-5b (SSE Events) ────────→ TRACE-0 (PlanningIndicator)
UQE-5c (Circuit Breaker) ───→ UQE-5 (fallback integration)
UQE-3-REVISED (Citation Gate) can run in parallel with UQE-1–UQE-3
UQE-6 (Remove Classify) ────→ depends on UQE-5 complete + tested
MON-1–4, SCHEMA-1–4 ────→ can run in parallel with UQE stream
MON-5–10 depend on UQE-5 (planner emit) + UQE-3-REVISED (citation emit)
TRACE-0–9 depend on MON-1–4 (DB schema) + SSE events (UQE-5b)
EVAL-1–5 can start once planner code exists (UQE-5)
```

---

## §4 Implementation Sequencing (Gap-Hardened)

### Week 1: Immediate Wins + Planner Foundation (~65 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| UQE-1 (remedial_codex SQL) | 2h | None | Platform |
| UQE-2 (Synthesis Temperature) | 6h | None | Platform |
| UQE-7 (Domain Fallback) | 6h | None | Platform |
| UQE-8 (Manifest Metadata) | 6h | None | Platform |
| UQE-9 (Trace Collisions) | 4h | None | Platform |
| **UQE-4a (Planner Prompt Arch)** | **40h** | None | Platform |
| MON-1/2/3/4 (Schema Design) | 12h | None | Database |
| SCHEMA-1 (Audit) | 6h | None | Database |

**Rationale:** UQE-4a is critical path and must complete before any planner code. All other tasks are independent and can proceed in parallel.

### Week 2: Planner Core + Infrastructure (~280 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| **UQE-4b (Context Builder)** | **6h** | UQE-4a | Platform |
| **UQE-4 (Full Manifest)** | **20h** | UQE-4a + UQE-4b | Platform |
| **UQE-5 (Universal Planner)** | **120h** | UQE-4a + UQE-4b + UQE-4 | Platform |
| **UQE-5a (Budget Arbitration)** | **8h** | UQE-5 (integrate post-plan) | Platform |
| **UQE-5b (SSE Events)** | **4h** | UQE-5 (emit events) | Platform |
| **UQE-5c (Circuit Breaker)** | **8h** | UQE-5 (wrap planner) | Platform |
| UQE-3-REVISED (Citation Gate) | 8h | None (parallel) | Platform |
| TRACE-0 (Planning Indicator) | 6h | UQE-5b (events) | Frontend |
| MON-5/6 (LLM Call Logging) | 60h | UQE-5 (emit calls) | Platform |
| SCHEMA-2/3 (Migrations) | 7h | None | Database |
| EVAL-1 (Golden Set) | 6h | None | QA/Automation |

**Rationale:** Week 2 focuses on planner completion and integration. Budget/circuit tasks integrate into UQE-5. TRACE-0 can start once SSE events are designed. EVAL-1 can start immediately (independent of code).

### Week 3: Tools, Traces & Analysis (~320 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| UQE-6 (Remove Classify) | 40h | UQE-5 tested + stable | Platform |
| TRACE-1/2/3/4/5 | 140h | MON-1/2/3/4 + UQE-5b | Frontend |
| MON-7/8 (Tool & Assembly Logging) | 70h | UQE-5 + tool execution code | Platform |
| SCHEMA-4/5 (Indexes + Endpoint) | 43h | MON-1–4 migrations applied | Database |
| EVAL-2 (Smoke Test Runner) | 8h | EVAL-1 + UQE-5 | QA |
| EVAL-3 (A/B Framework) | 16h | EVAL-1 + data available | QA |

**Rationale:** Week 3 is parallel frontend + backend work. TRACE panels require DB schema to be live. EVAL work proceeds independently.

### Week 4: Convergence & Integration (~300 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| TRACE-6/7/8/9 | 150h | MON-9 (investigation endpoint) | Frontend |
| MON-9/10 (Investigation Endpoint + Views) | 60h | MON-1–8 complete | Platform |
| UQE-10 (Flag Deprecation) | 1h | None | Platform |
| SCHEMA-6 (Retention Policy) | 6h | None | Database |
| EVAL-4/5 (Regression Detection + CI) | 6h | EVAL-2 + CI access | QA |
| Integration Testing | 80h | All streams | QA |

**Rationale:** Week 4 finalizes TRACE panels, investigation infrastructure, and evaluation framework. Integration testing validates end-to-end pipeline.

### Updated Effort Estimate

| Stream | v1.0 Effort | v1.1 Gap Work | Total |
|--------|-------------|---|---|
| UQE | 112h | +128h (UQE-4a, 4b, 5a, 5b, 5c, 3-REVISED) | 240h |
| MON | 85h | +25h (MON-5 R1 updates) | 110h |
| TRACE | 135h | +60h (TRACE-0, hydration specs) | 195h |
| SCHEMA | 35h | +0h | 35h |
| EVAL | 0h | +145h (new stream) | 145h |
| **Integration & QA** | **80h** | **+50h** | **130h |
| **GRAND TOTAL** | **853h** | **+308h** | **~1,161h** |

**Delivery:** 3–4 weeks, 4–5 concurrent FTE. Critical path is UQE-4a → UQE-5 → all consumers.

---

## §5 Acceptance Criteria (Machine-Testable, Gap-Inclusive)

### UQE Stream
- [ ] UQE-1: remedial_codex_query SELECT returns ≥1 row for all test remedial queries
- [ ] UQE-2: temperature=0 for single_answer; byte-identical input → identical output (×5 loops)
- [ ] UQE-3-REVISED: Verified citations ≥1 on known-good remedial queries; training data citations produce WARN; override flag works
- [ ] UQE-4a: Compressed manifest ≤3K tokens; planner input ≤5K total; valid JSON ≥95% of test queries
- [ ] UQE-4b: Planner context ≤5K tokens on 100% of queries regardless of history length
- [ ] UQE-4: Planner reads full manifest; reasoning present in plan output
- [ ] UQE-5: All queries routed through planner; planner latency p95 <500ms; fallback_used=false ≥99%
- [ ] UQE-5a: context_assembly total_tokens ≤ (model_max_context × 0.85) on 100% of queries
- [ ] UQE-5b: planning_start within 100ms of query receipt; planning_done within 200ms of validation
- [ ] UQE-5c: Circuit opens after 3 timeouts; fallback queries complete; circuit auto-recovers
- [ ] UQE-6: Classify step not in trace; all tools available post-planning
- [ ] UQE-7: Domain fallback returns ≥1 signal with empty planet/house arrays
- [ ] UQE-8: All 8 tools have complete metadata; manifest validates
- [ ] UQE-9: step_seq unique within query_id across 100+ test queries
- [ ] UQE-10: Deprecation timeline published with v2.1 removal date

### MON Stream
- [ ] MON-1–4: All tables created with correct schema and indexes
- [ ] MON-5–8: llm_call_log, query_plan_log, tool_execution_log, context_assembly_log populated for 100% of queries
- [ ] MON-5 (R1): deepseek-reasoner calls show non-null reasoning_tokens; tokens match SDK estimate
- [ ] MON-9: /api/investigation/:query_id returns complete logs; response <500ms
- [ ] MON-10: Analytics views queryable; <1s response; reasoning_tokens included in cost

### TRACE Stream
- [ ] TRACE-0: PlanningIndicator appears on planning_start; collapses post-planning_done
- [ ] TRACE-1–9: All 10 panels render correctly with skeleton UI
- [ ] All panels: SSE event → hydration correct; state machine transitions (loading → partial → complete)
- [ ] All panels: render latency <500ms even for large result sets
- [ ] TRACE-1: R1 "View thinking" button renders and displays reasoning_trace
- [ ] TRACE-2: Zero-rows and error tools highlighted; planning_confidence gauge visible
- [ ] TRACE-4: Arrow weights proportional to tokens_contributed; new channels pulse
- [ ] TRACE-5: Drill-in shows per-layer items with citations
- [ ] TRACE-7: All steps in correct order; parallel steps visible; click-drill functional
- [ ] TRACE-9: All tables accessible; export to JSON/CSV valid

### SCHEMA Stream
- [ ] SCHEMA-1–6: All artifacts delivered
- [ ] Migrations: idempotent; apply cleanly to staging; schema matches TypeScript
- [ ] Indexes: cover all 8 common investigation patterns
- [ ] /api/investigation/queries: filters work; pagination correct; <1s response
- [ ] Retention policy: documented; cleanup jobs scheduled

### EVAL Stream
- [ ] EVAL-1: 25 golden test pairs documented with acceptance criteria
- [ ] EVAL-2: Smoke test runner executes; outputs JSON; exits non-zero on failure; tool_recall ≥0.80, tool_precision ≥0.90
- [ ] EVAL-3: A/B report generated for ≥10 queries; improvement/regression classified
- [ ] EVAL-4/5: CI runs eval before production; alerts on regression (tool_recall <0.75)

### Gap-Specific Acceptance
- [ ] **G5 (Planner Prompt Arch):** Compressed manifest renders; structured output enforced; prompt engineering live
- [ ] **G6 (Token Budget):** Budget arbitration algorithm implemented; context assembly respects budgets
- [ ] **G7 (Planner Latency UX):** planning_start/planning_done events emit; TRACE-0 shows progress
- [ ] **G8 (Circuit Breaker):** Circuit opens/closes per spec; fallback path tested; auto-recovery verified
- [ ] **G9 (Planner Eval):** Golden set covers remedial, interpretive, predictive, compound, edge-cases; EVAL-2 passes on known good plans
- [ ] **G10 (Citation Gate):** Two-layer validation implemented; WARN for training data; ERROR only for prescriptive zero-citation
- [ ] **G11 (Conversation History):** Context builder limits history; summarization optional; planner context <5K
- [ ] **G12 (TRACE Hydration):** SSE → Panel mapping complete; all panels follow state machine; skeleton UI specs implemented
- [ ] **G13 (R1 Reasoning):** reasoning_tokens extracted and logged; MON-5 handles deepseek-reasoner; TRACE-1 shows thinking

---

## §6 Known Risks & Mitigations (Gap-Inclusive)

**Risk R1: Planner Latency**  
Mitigation: Manifest compression (≤3K tokens); Haiku throughput; p95 monitoring; circuit breaker fallback

**Risk R2: Planner Hallucination**  
Mitigation: Validate output against query_schema; manual review first 20 outputs; EVAL-2 regression detection

**Risk R3: Database Bloat**  
Mitigation: Retention policy (90-day hot, archive, delete); cleanup jobs scheduled; partitioning by date

**Risk R4: Context Loss (Classify Removal)**  
Mitigation: Audit downstream code; preserve query_class in context; planner explicit about classification

**Risk R5: TRACE UI Performance**  
Mitigation: Virtualize large lists; Canvas for timelines; lazy-load investigation tab; skeleton UI for perceived performance

**Risk R6: B.3 Compliance Gate Too Strict**  
Mitigation: Two-layer citation validation (existence + context cross-ref); WARN for training data; admin override flag

**Risk R7: Migration Failures**  
Mitigation: Test on staging; idempotent migrations; rollback pre-tested; zero-downtime verified

**Risk R8: Manifest Compression Fails (G5)**  
Mitigation: Fallback to raw manifest if compression fails; planner latency monitoring; circuit breaker timeout <3s

**Risk R9: Budget Arbitration Too Aggressive (G6)**  
Mitigation: Never trim priority=1 below 200 tokens; audit budget allocation post-deployment; alerts on low-budget tool execution

**Risk R10: History Summarization Adds Latency (G11)**  
Mitigation: Only summarize when >2 turns AND >600 tokens (uncommon); micro-call timeout <500ms; conditional vs always

**Risk R11: Eval Golden Set Too Small (G9)**  
Mitigation: 25 pairs covers 5 domains; quarterly audit & expansion; metrics captured for future baseline

**Risk R12: Circuit Breaker Stays Open (G8)**  
Mitigation: Recovery interval 5 minutes; health check during half-open; manual override if needed; monitoring alert

---

## §7 Relationship to M3

**Wave 2 is standalone; no blocking dependencies on M3.**

**Isolation:**
- New feature flags in separate namespace (`BHISMA_*`)
- New DB tables (non-destructive; archive + cleanup policy)
- New React components in trace drawer (additive)
- Pipeline refactor: coordinate merge if M3 also touches routing

**Potential Synergies (post-v1.1):**
- EVAL stream (EVAL-2/3/4) introduces a test runner that could feed M3's eval baseline
- query_investigation_log denormalized data could power M3's quality metrics dashboard
- Citation validation (G10) aligns with M3's B.3 grounding goals

**Rollback:** ≤2 hours; revert feature flags + pipeline code; keep DB tables (inert).


---

## §8 TypeScript Interface Reference (v1.1 New Interfaces)

All interfaces below are additive — they do not modify existing types in `platform/src/lib/trace/types.ts` or `platform/src/lib/models/registry.ts`. New files are listed with their intended paths.

### 8.1 Manifest Planner Interfaces
**File:** `platform/src/lib/pipeline/manifest_planner.ts`

```typescript
/** A single entry in the compressed manifest sent to the Universal Planner. */
export interface CompressedManifestEntry {
  /** Canonical tool name matching the retrieve layer's tool registry. */
  tool_name: string;
  /** One-line human-readable description for the LLM. */
  description: string;
  /** Comma-separated domain tags (e.g. "planetary,dasha,transit"). */
  tags: string;
  /**
   * Estimated token cost PER TOOL CALL when this entry is activated.
   * Used by the budget arbiter to gate low-priority selections.
   */
  estimated_tokens: number;
  /** Whether this tool has been verified returning data in production. */
  verified_live: boolean;
}

/** Per-tool call specification emitted by the Universal Planner. */
export interface UniversalToolCallSpec {
  tool_name: string;
  /** Tool-specific parameters — shape varies per tool. */
  params: Record<string, unknown>;
  /**
   * Token budget allocated to this tool's result before synthesis.
   * Budget arbiter may reduce this if total exceeds synthesis model context.
   */
  token_budget: number;
  /**
   * P1 = must include (primary answer source),
   * P2 = should include (supporting evidence),
   * P3 = nice-to-have (can be trimmed first by budget arbiter).
   */
  priority: 'P1' | 'P2' | 'P3';
  /** Planner's natural-language justification for this tool selection. */
  reason: string;
}

/** Full query plan emitted by the Universal Planner. null entries = skip tool. */
export interface UniversalQueryPlan {
  /** Planner's classification of the query for logging/eval purposes. */
  query_class: 'planetary' | 'dasha' | 'transit' | 'remedial' | 'holistic' | 'multi_domain';
  /** Planner confidence score 0.0–1.0 for use in eval and monitoring. */
  planning_confidence: number;
  /** Whether the planner recommends streaming the synthesis response. */
  should_stream: boolean;
  /** Whether the planner expects a single deterministic answer (temperature→0). */
  single_answer: boolean;
  /** Ordered list of tool call specs. Null entries for explicitly skipped tools. */
  tool_calls: Array<UniversalToolCallSpec | null>;
  /** Planner's free-text reasoning (logged but not sent to synthesis). */
  reasoning: string;
}

/** Context object passed to the planner on each call. */
export interface PlannerContext {
  /** The user's current query text. */
  query: string;
  /** Query style from session state. */
  style: 'concise' | 'detailed' | 'technical';
  /** Synthesis model selected by the user. */
  synthesis_model_id: string;
  /**
   * Last N turns of conversation history, already token-capped at 600 tokens.
   * Empty array on first turn or when history is irrelevant.
   */
  history_snippet: Array<{ role: 'user' | 'assistant'; content: string }>;
  /** Compressed manifest entries for the planner's tool selection. */
  manifest: CompressedManifestEntry[];
  /** Synthesis model context window in tokens (used for budget arithmetic). */
  synthesis_context_limit: number;
}
```

### 8.2 Budget Arbiter Interfaces
**File:** `platform/src/lib/pipeline/budget_arbiter.ts`

```typescript
export interface BudgetArbiterConfig {
  /** Hard ceiling on total tool output tokens (synthesis context × safety_factor). */
  total_token_ceiling: number;
  /** Minimum tokens guaranteed to P1 tools even after arbitration. */
  p1_minimum_tokens: number;
  /** Minimum tokens for P2 tools; can be trimmed to 0 before P1 is touched. */
  p2_minimum_tokens: number;
  /** Whether to log budget decisions to the trace. */
  trace_budget_decisions: boolean;
}

export interface BudgetArbiterResult {
  /** Adjusted tool specs with revised token_budget values. */
  adjusted_specs: UniversalToolCallSpec[];
  /** Total allocated tokens across all tools. */
  total_allocated: number;
  /** How many tools were trimmed (budget reduced from requested). */
  tools_trimmed: number;
  /** How many P3 tools were dropped entirely. */
  tools_dropped: number;
}
```

### 8.3 Circuit Breaker Interfaces
**File:** `platform/src/lib/pipeline/planner_circuit_breaker.ts`

```typescript
export type CircuitBreakerStatus = 'closed' | 'open' | 'half_open';

export interface CircuitBreakerState {
  status: CircuitBreakerStatus;
  consecutive_failures: number;
  last_failure_at: number | null;  // epoch ms
  last_success_at: number | null;
  /** Set when status transitions to 'open'. Breaker tries half_open after this. */
  recovery_at: number | null;      // epoch ms
}

export interface CircuitBreakerConfig {
  /** Planner call timeout in ms before counting as a failure. Default: 3000. */
  timeout_ms: number;
  /** Consecutive failures before opening the circuit. Default: 3. */
  failure_threshold: number;
  /** How long the circuit stays open before attempting half_open. Default: 300000. */
  recovery_interval_ms: number;
}
```

### 8.4 SSE Planning Events
**File:** `platform/src/lib/trace/types.ts` (additive extension)

```typescript
/** SSE event emitted when the Universal Planner begins executing. */
export interface PlanningStartEvent {
  type: 'planning_start';
  timestamp: number;
  query_id: string;
}

/** SSE event emitted when the Universal Planner finishes and tool calls are ready. */
export interface PlanningDoneEvent {
  type: 'planning_done';
  timestamp: number;
  query_id: string;
  query_class: string;
  planning_confidence: number;
  tool_count: number;
  total_budget_tokens: number;
  /** Whether the planner fell back to the static plan (circuit breaker fired). */
  used_fallback: boolean;
  /** Duration of the planner LLM call in ms. */
  planner_latency_ms: number;
}
```

### 8.5 Citation Validation Interfaces
**File:** `platform/src/lib/audit/citation_validator.ts`

```typescript
export interface CitationVerificationResult {
  /** True if all citations in the synthesis output exist in the corpus. */
  all_exist: boolean;
  /** True if all cited signals are present in the assembled context items. */
  all_in_context: boolean;
  /** Total citations found in the synthesis output. */
  citation_count: number;
  /** Signal IDs that appear in the output but were not in the context. */
  hallucinated_citations: string[];
  /** Signal IDs that appear in the output and were in the context. */
  verified_citations: string[];
}
```

### 8.6 Monitoring Interfaces
**File:** `platform/src/lib/monitoring/llm_call_record.ts`

```typescript
export interface LLMCallRecord {
  id: string;                    // uuid
  query_id: string;
  call_type: 'planner' | 'synthesis' | 'title' | 'history_summary';
  model_id: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  /** Applicable only for DeepSeek R1; 0 for all other models. */
  reasoning_tokens: number;
  latency_ms: number;
  cost_usd: number;
  created_at: Date;
  /** Whether the call completed successfully. */
  success: boolean;
  /** Error message if success=false. */
  error_message: string | null;
}

export interface ToolExecutionRecord {
  id: string;
  query_id: string;
  tool_name: string;
  priority: 'P1' | 'P2' | 'P3';
  token_budget: number;
  tokens_used: number;
  latency_ms: number;
  /** Whether the tool returned at least one result row / vector hit. */
  returned_data: boolean;
  row_count: number | null;
  created_at: Date;
  error_message: string | null;
}
```

### 8.7 TRACE Panel Hook Interface
**File:** `platform/src/components/trace/hooks/useTracePanel.ts`

```typescript
export type PanelState =
  | 'idle'        // no query in flight
  | 'waiting'     // query received, planner not started
  | 'planning'    // planning_start received, waiting for planning_done
  | 'executing'   // planning_done received, tools in flight
  | 'synthesizing'// all tools done, synthesis streaming
  | 'complete'    // synthesis done
  | 'error';      // any step failed

export interface TracePanelData {
  state: PanelState;
  queryClass: string | null;
  planningConfidence: number | null;
  plannerLatencyMs: number | null;
  toolSpecs: UniversalToolCallSpec[];
  toolResults: ToolExecutionRecord[];
  llmCalls: LLMCallRecord[];
  citationResult: CitationVerificationResult | null;
  error: { stage: string; message: string } | null;
}
```


---

## §9 Database Migration DDL Reference

Four migration files, applied in sequence. All tables land in the `public` schema on the Cloud SQL PostgreSQL instance (Auth Proxy on 127.0.0.1:5433). Migrations are additive and non-destructive.

### Migration 1 — Query Master Table
**File:** `platform/migrations/20260501_001_query_investigation_log.sql`

```sql
-- Query master record: one row per user query, created at query receipt
CREATE TABLE IF NOT EXISTS query_investigation_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_text      TEXT NOT NULL,
  query_class     TEXT,                        -- from planner: planetary|dasha|transit|remedial|holistic|multi_domain
  style           TEXT,                        -- concise|detailed|technical
  chart_id        TEXT,                        -- native chart reference
  session_id      TEXT,
  synthesis_model TEXT NOT NULL,
  used_fallback   BOOLEAN NOT NULL DEFAULT false,
  total_latency_ms INTEGER,
  total_cost_usd  NUMERIC(10,6),
  citation_count  INTEGER,
  hallucinated_citations INTEGER DEFAULT 0,
  planning_confidence NUMERIC(4,3),            -- 0.000–1.000
  status          TEXT NOT NULL DEFAULT 'in_flight', -- in_flight|complete|error
  error_stage     TEXT,
  error_message   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_qil_created_at    ON query_investigation_log(created_at DESC);
CREATE INDEX idx_qil_query_class   ON query_investigation_log(query_class);
CREATE INDEX idx_qil_synthesis_model ON query_investigation_log(synthesis_model);
CREATE INDEX idx_qil_status        ON query_investigation_log(status);
CREATE INDEX idx_qil_session_id    ON query_investigation_log(session_id);

COMMENT ON TABLE query_investigation_log IS
  'Master record for every query processed by MARSYS. One row per query_id.';
```

### Migration 2 — LLM Call Ledger
**File:** `platform/migrations/20260501_002_llm_call_ledger.sql`

```sql
-- Per-LLM-call record: 2–3 rows per query in steady state
CREATE TABLE IF NOT EXISTS llm_call_ledger (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id         UUID NOT NULL REFERENCES query_investigation_log(id) ON DELETE CASCADE,
  call_type        TEXT NOT NULL,              -- planner|synthesis|title|history_summary
  model_id         TEXT NOT NULL,
  provider         TEXT NOT NULL,
  input_tokens     INTEGER NOT NULL DEFAULT 0,
  output_tokens    INTEGER NOT NULL DEFAULT 0,
  reasoning_tokens INTEGER NOT NULL DEFAULT 0, -- R1 only; always 0 for other models
  latency_ms       INTEGER,
  cost_usd         NUMERIC(10,6),
  success          BOOLEAN NOT NULL DEFAULT true,
  error_message    TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lcl_query_id   ON llm_call_ledger(query_id);
CREATE INDEX idx_lcl_call_type  ON llm_call_ledger(call_type);
CREATE INDEX idx_lcl_model_id   ON llm_call_ledger(model_id);
CREATE INDEX idx_lcl_created_at ON llm_call_ledger(created_at DESC);

COMMENT ON TABLE llm_call_ledger IS
  'One row per LLM call. Linked to query_investigation_log. Supports cost and latency analytics.';
```

### Migration 3 — Tool Execution Log
**File:** `platform/migrations/20260501_003_tool_execution_log.sql`

```sql
-- Per-tool execution record: N rows per query depending on planner output
CREATE TABLE IF NOT EXISTS tool_execution_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        UUID NOT NULL REFERENCES query_investigation_log(id) ON DELETE CASCADE,
  tool_name       TEXT NOT NULL,
  priority        TEXT NOT NULL,               -- P1|P2|P3
  token_budget    INTEGER,
  tokens_used     INTEGER,
  latency_ms      INTEGER,
  returned_data   BOOLEAN NOT NULL DEFAULT false,
  row_count       INTEGER,
  error_message   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tel_query_id   ON tool_execution_log(query_id);
CREATE INDEX idx_tel_tool_name  ON tool_execution_log(tool_name);
CREATE INDEX idx_tel_priority   ON tool_execution_log(priority);

COMMENT ON TABLE tool_execution_log IS
  'One row per tool call within a query. Supports corpus coverage and retrieval-gap analysis.';
```

### Migration 4 — Analytics Views
**File:** `platform/migrations/20260501_004_analytics_views.sql`

```sql
-- Hourly query volume by class and model
CREATE OR REPLACE VIEW v_query_hourly AS
SELECT
  date_trunc('hour', created_at)    AS hour,
  query_class,
  synthesis_model,
  COUNT(*)                          AS query_count,
  AVG(total_latency_ms)             AS avg_latency_ms,
  SUM(total_cost_usd)               AS total_cost_usd,
  AVG(citation_count)               AS avg_citations,
  SUM(hallucinated_citations)       AS total_hallucinations,
  AVG(planning_confidence)          AS avg_planning_confidence
FROM query_investigation_log
WHERE status = 'complete'
GROUP BY 1, 2, 3;

-- Per-model cost and token breakdown (rolling 7 days)
CREATE OR REPLACE VIEW v_model_cost_7d AS
SELECT
  model_id,
  provider,
  call_type,
  COUNT(*)                          AS call_count,
  SUM(input_tokens)                 AS total_input_tokens,
  SUM(output_tokens)                AS total_output_tokens,
  SUM(reasoning_tokens)             AS total_reasoning_tokens,
  SUM(cost_usd)                     AS total_cost_usd,
  AVG(latency_ms)                   AS avg_latency_ms
FROM llm_call_ledger
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND success = true
GROUP BY 1, 2, 3;

-- Tool coverage: fraction of queries each tool was called for (rolling 7 days)
CREATE OR REPLACE VIEW v_tool_coverage_7d AS
SELECT
  t.tool_name,
  COUNT(DISTINCT t.query_id)                                        AS queries_using_tool,
  COUNT(DISTINCT q.id)                                              AS total_queries,
  ROUND(COUNT(DISTINCT t.query_id)::NUMERIC / NULLIF(COUNT(DISTINCT q.id),0), 3) AS coverage_rate,
  AVG(CASE WHEN t.returned_data THEN 1.0 ELSE 0.0 END)             AS data_return_rate,
  AVG(t.latency_ms)                                                 AS avg_latency_ms
FROM query_investigation_log q
LEFT JOIN tool_execution_log t ON t.query_id = q.id
WHERE q.created_at >= NOW() - INTERVAL '7 days'
GROUP BY t.tool_name;

-- Circuit breaker / fallback rate
CREATE OR REPLACE VIEW v_fallback_rate_24h AS
SELECT
  date_trunc('hour', created_at)    AS hour,
  COUNT(*)                          AS total_queries,
  SUM(CASE WHEN used_fallback THEN 1 ELSE 0 END) AS fallback_queries,
  ROUND(SUM(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) / NULLIF(COUNT(*),0), 3) AS fallback_rate
FROM query_investigation_log
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1 DESC;
```


---

## §10 TRACE Component Architecture Reference

### 10.1 Component Tree

```
ConsumeTab
└── TraceDrawer (slide-out panel, right side)
    ├── PlanningIndicator          [TRACE-0] — SSE-driven spinner + latency badge
    ├── LLMCallMap                 [TRACE-1] — 2-3 call cards, cost + token breakdown
    ├── QueryPlan                  [TRACE-2] — planner JSON rendered as tool cards
    ├── ToolResultGrid             [TRACE-3] — per-tool result rows, tokens, P1/P2/P3 badge
    ├── CitationPanel              [TRACE-4] — citation list, hallucination alert
    ├── CostPanel                  [TRACE-5] — per-call cost + session rolling total
    ├── LatencyWaterfall           [TRACE-6] — horizontal Gantt: plan → tools → synthesis
    ├── MonitoringPanel            [TRACE-7] — DB-backed 24h metrics (queries, cost, models)
    ├── QueryHistoryTable          [TRACE-8] — scrollable log of past queries
    └── QueryDiffView              [TRACE-9] — side-by-side response comparison
```

### 10.2 SSE → Panel Hydration State Machine

```
                      query_received
                           │
                           ▼
                    ┌─────────────┐
                    │   waiting   │◄─── PlanningIndicator shows spinner (no timeout yet)
                    └──────┬──────┘
                           │ planning_start event
                           ▼
                    ┌─────────────┐
                    │  planning   │◄─── PlanningIndicator: "Planning…" + elapsed timer
                    └──────┬──────┘
                           │ planning_done event
                           ▼
                    ┌─────────────┐
                    │  executing  │◄─── QueryPlan hydrates from planning_done payload
                    └──────┬──────┘     ToolResultGrid shows skeleton per tool_count
                           │ all tool_result events received
                           ▼
                    ┌──────────────┐
                    │ synthesizing │◄─── ToolResultGrid complete; CostPanel partial update
                    └──────┬───────┘
                           │ synthesis_complete event
                           ▼
                    ┌──────────────┐
                    │   complete   │◄─── CitationPanel, LLMCallMap, LatencyWaterfall hydrate
                    └──────────────┘

    Any step → error event → PanelState = 'error', error card shown in affected panel
```

### 10.3 Component Skeleton Specifications

| Component | Skeleton | Real State |
|---|---|---|
| PlanningIndicator | Spinner + "Planning…" text | Latency badge + query_class chip |
| LLMCallMap | 2 grey placeholder cards | Colored cards per provider |
| QueryPlan | N grey tool cards (N from planning_done.tool_count) | Tool cards with params + priority badge |
| ToolResultGrid | N rows, all showing loading state | Rows with token count, data/empty badge |
| CitationPanel | "Verifying citations…" | Signal list or hallucination alert |
| CostPanel | "—" cost | Per-call breakdown + session total |
| LatencyWaterfall | Flat grey bar | Segmented bars: plan / parallel tools / synthesis |
| MonitoringPanel | Shimmer over chart area | Live chart from DB view |

### 10.4 Design System Constraints

All components use the existing MARSYS design tokens:
- Colors: `--color-accent`, `--color-surface`, `--color-muted`, `--color-error`
- Typography: `font-mono` for token counts / cost; `font-sans` for labels
- Priority badges: P1 = `bg-accent/20 text-accent`, P2 = `bg-muted/30 text-muted-foreground`, P3 = `bg-muted/10 text-muted-foreground/60`
- Provider colors: Anthropic = `#d4763b`, Google = `#4285f4`, OpenAI = `#10a37f`, DeepSeek = `#5b6fff`
- No new third-party UI dependencies; shadcn/ui components already installed

### 10.5 File Locations

| Component | Path |
|---|---|
| PlanningIndicator | `platform/src/components/trace/PlanningIndicator.tsx` |
| LLMCallMap | `platform/src/components/trace/LLMCallMap.tsx` |
| QueryPlan | `platform/src/components/trace/QueryPlan.tsx` |
| ToolResultGrid | `platform/src/components/trace/ToolResultGrid.tsx` |
| CitationPanel | `platform/src/components/trace/CitationPanel.tsx` |
| CostPanel | `platform/src/components/trace/CostPanel.tsx` |
| LatencyWaterfall | `platform/src/components/trace/LatencyWaterfall.tsx` |
| MonitoringPanel | `platform/src/components/trace/MonitoringPanel.tsx` |
| QueryHistoryTable | `platform/src/components/trace/QueryHistoryTable.tsx` |
| QueryDiffView | `platform/src/components/trace/QueryDiffView.tsx` |
| useTracePanel hook | `platform/src/components/trace/hooks/useTracePanel.ts` |


---

## §11 Gap Resolution Register

This register provides a one-to-one audit trail between the nine gaps identified in the v1.0 plan and their resolution in v1.1. Each entry states the gap, the resolution approach, and the task(s) that implement it.

| Gap ID | Title | Severity | v1.0 Status | Resolution in v1.1 | Implementing Tasks |
|---|---|---|---|---|---|
| G5 | Planner Prompt Architecture | CRITICAL | Missing entirely | §12 provides full system prompt, 2 few-shot examples, PlanSchema JSON. UQE-4a implements the prompt, manifest compressor, and context builder. | UQE-4a, UQE-4b |
| G6 | Token Budget Enforcement | HIGH | No mechanism | Budget Arbiter component (§8.2) with priority-based trimming (P3 first, P2 to floor, P1 never below 200 tokens). | UQE-5a |
| G7 | No UX Signal for Planner Latency | MEDIUM | Silent extra latency | planning_start and planning_done SSE events (§8.4); PlanningIndicator component (TRACE-0) hydrated by these events. | UQE-5b, TRACE-0 |
| G8 | No Circuit Breaker | HIGH | Hard failure if planner times out | Circuit breaker with 3s timeout, 3-failure threshold, 5-minute recovery; static-plan fallback on open state. | UQE-5c |
| G9 | No Evaluation Framework | HIGH | Plan not testable | EVAL stream: 25-pair golden set (EVAL-1), smoke runner (EVAL-2), A/B comparison (EVAL-3), regression detection (EVAL-4), CI integration (EVAL-5). | EVAL-1 – EVAL-5 |
| G10 | Citation Gate Too Blunt | MEDIUM | Hard gate blocks all citations if count=0 | Two-layer validation: existence check + context cross-reference. Adds CITATION_GATE_OVERRIDE flag for single_answer queries. | UQE-3-REVISED |
| G11 | Planner History Context Unspecified | MEDIUM | Unbounded history possible | PlannerContextBuilder: last 2 turns only, max 600 tokens, optional summarization micro-call if >600 tokens. | UQE-4b |
| G12 | TRACE Panels Have No Hydration Strategy | MEDIUM | Panels would show stale/empty state | SSE → panel state machine (§10.2) with skeleton specs per component. planning_start/done events drive hydration. | TRACE-0 – TRACE-9, UQE-5b |
| G13 | DeepSeek R1 Reasoning Tokens Untracked | MEDIUM | Cost underreported for R1 | reasoning_tokens field in LLMCallRecord and llm_call_ledger table. MON-5 extends cost calculations; TRACE-1 renders reasoning tokens separately. | MON-5, TRACE-1 |

**Gaps G1–G4** (from §1.2) were already tracked in v1.0 and are resolved by the core UQE stream tasks (UQE-1 through UQE-3). They are not re-listed here.

### 11.1 Acceptance Mapping

For each gap, the specific acceptance criterion in §5 that verifies resolution:

| Gap ID | §5 Acceptance Criterion |
|---|---|
| G5 | EVAL AC-E1: golden set score ≥ 90% on tool selection; AC-E2: smoke test passes on merge |
| G6 | UQE AC-U5: synthesis receives ≤ context_limit tokens across all tool outputs |
| G7 | TRACE AC-T1: PlanningIndicator visible within 200ms of planning_start event |
| G8 | UQE AC-U6: circuit breaker test passes; fallback returns valid response |
| G9 | EVAL AC-E3: A/B comparison UI renders both responses; AC-E4: regression alert fires |
| G10 | UQE AC-U4: citation_count > 0 on ≥ 80% of corpus-grounded queries |
| G11 | UQE AC-U7: planner context never exceeds 600 history tokens; verified by unit test |
| G12 | TRACE AC-T2: all panels hydrate within 500ms of relevant SSE event |
| G13 | MON AC-M5: R1 reasoning tokens logged and visible in TRACE-1; cost accurate |


---

## §12 Planner Prompt Engineering Reference

This section is a living specification for the Universal Planner's prompt. It is designed to be extracted into `00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md` once UQE-4a begins. Changes to the planner prompt **must** be versioned in that file and cross-referenced here.

### 12.1 Planner System Prompt

```
You are the MARSYS Universal Query Planner. Your job is to analyze the user's Jyotish query and produce a precise JSON execution plan specifying exactly which retrieval tools to call and how.

## Your Output
You MUST output valid JSON that conforms to the PlanSchema below. No prose before or after the JSON. No markdown fences.

## Available Tools
You will receive a compressed manifest listing each available retrieval tool with:
- tool_name: the exact string to use in your plan
- description: what the tool retrieves
- tags: domain tags (planetary, dasha, transit, remedial, holistic, etc.)
- estimated_tokens: approximate token cost when this tool is called
- verified_live: whether this tool is confirmed returning data in production

## Planning Rules
1. Select tools whose domain tags match the query's subject matter.
2. Assign priority:
   - P1: primary answer source (must always be included; never trim below 200 tokens)
   - P2: corroborating or contextual evidence (include unless budget is tight)
   - P3: supplementary; trim first if total token budget is tight
3. Set token_budget for each tool: your estimate of how many tokens its output should contribute to the synthesis. All budgets combined must not exceed {{ synthesis_context_limit }} tokens × 0.6 (leave 40% for synthesis, history, and system prompt).
4. Set single_answer=true only for binary or factual queries with one correct answer.
5. Set should_stream=true for all queries with expected_output_shape=narrative or detailed.
6. Set planning_confidence: 0.9+ for clear single-domain queries; 0.7–0.9 for multi-domain; below 0.7 for ambiguous queries.
7. For the remedial domain: ALWAYS include the remedial_codex_query tool as P1 even if other tools are also selected.
8. For null entries: explicitly null a tool only if it is completely irrelevant. Do not null a tool just because its estimated_tokens is high.

## Context
- User query: {{ query }}
- Query style: {{ style }}
- Synthesis model: {{ synthesis_model_id }}
- Synthesis context limit: {{ synthesis_context_limit }} tokens
- Conversation history (last {{ history_turns }} turns):
{{ history_snippet }}
```

### 12.2 PlanSchema (JSON Schema for Planner Output)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UniversalQueryPlan",
  "type": "object",
  "required": ["query_class", "planning_confidence", "should_stream", "single_answer", "tool_calls", "reasoning"],
  "properties": {
    "query_class": {
      "type": "string",
      "enum": ["planetary", "dasha", "transit", "remedial", "holistic", "multi_domain"]
    },
    "planning_confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "should_stream": { "type": "boolean" },
    "single_answer": { "type": "boolean" },
    "reasoning": {
      "type": "string",
      "description": "Planner's free-text justification. Logged but not sent to synthesis."
    },
    "tool_calls": {
      "type": "array",
      "items": {
        "oneOf": [
          {
            "type": "object",
            "required": ["tool_name", "params", "token_budget", "priority", "reason"],
            "properties": {
              "tool_name": { "type": "string" },
              "params": { "type": "object" },
              "token_budget": { "type": "integer", "minimum": 200 },
              "priority": { "type": "string", "enum": ["P1", "P2", "P3"] },
              "reason": { "type": "string" }
            }
          },
          { "type": "null" }
        ]
      }
    }
  }
}
```

### 12.3 Few-Shot Example 1: Single-Domain Planetary Query

**Input context (abbreviated):**
```
query: "What does Saturn's placement in the 7th house mean for relationships?"
style: concise
synthesis_model_id: deepseek-chat
synthesis_context_limit: 65536
history_snippet: []
```

**Expected planner output:**
```json
{
  "query_class": "planetary",
  "planning_confidence": 0.92,
  "should_stream": false,
  "single_answer": false,
  "reasoning": "Clear planetary placement query. Primary source is MSR signals for Saturn and 7th house. CGM graha-bhava entries provide architectural depth. Pattern register may surface chronic tension patterns. No remedial or transit signals needed.",
  "tool_calls": [
    {
      "tool_name": "msr_signal_query",
      "params": { "graha": "saturn", "bhava": "7", "limit": 20 },
      "token_budget": 3000,
      "priority": "P1",
      "reason": "Primary signal source for Saturn-7th house themes"
    },
    {
      "tool_name": "cgm_query",
      "params": { "section": "graha_bhava", "graha": "saturn", "bhava": "7" },
      "token_budget": 2000,
      "priority": "P1",
      "reason": "CGM graha-bhava provides classical Parashara framework"
    },
    {
      "tool_name": "pattern_register_query",
      "params": { "domain": "relationships", "graha_filter": ["saturn"] },
      "token_budget": 1500,
      "priority": "P2",
      "reason": "Cross-domain patterns involving Saturn and relationships"
    },
    null,
    null,
    null
  ]
}
```

### 12.4 Few-Shot Example 2: Multi-Domain Remedial Query

**Input context (abbreviated):**
```
query: "I'm going through Rahu dasha. What remedies should I consider and what transits should I watch?"
style: detailed
synthesis_model_id: claude-opus-4-6
synthesis_context_limit: 200000
history_snippet: [
  { "role": "user", "content": "When does my Rahu dasha end?" },
  { "role": "assistant", "content": "Your Rahu mahadasha runs until approximately 2029-03..." }
]
```

**Expected planner output:**
```json
{
  "query_class": "multi_domain",
  "planning_confidence": 0.82,
  "should_stream": true,
  "single_answer": false,
  "reasoning": "Three domains in play: (1) Rahu dasha signals and period character, (2) remedial prescriptions for Rahu, (3) current transits affecting the dasha experience. Remedial is P1 per rule 7. Dasha data is P1 as the query's stated subject. Transits are P2 because the user asked to 'watch' them (monitoring context, not primary answer). Pattern and contradiction registers are P2 to surface Rahu-specific tensions. Vector search may retrieve relevant native life-event context.",
  "tool_calls": [
    {
      "tool_name": "remedial_codex_query",
      "params": { "graha": "rahu", "context": "mahadasha" },
      "token_budget": 4000,
      "priority": "P1",
      "reason": "Rule 7: remedial tool always P1 for remedial domain queries"
    },
    {
      "tool_name": "dasha_query",
      "params": { "graha": "rahu", "include_antardasha": true },
      "token_budget": 3500,
      "priority": "P1",
      "reason": "Primary subject of query is Rahu dasha character and timing"
    },
    {
      "tool_name": "transit_query",
      "params": { "graha_filter": ["rahu", "ketu", "saturn", "jupiter"], "horizon_days": 180 },
      "token_budget": 2500,
      "priority": "P2",
      "reason": "User asked which transits to watch during this dasha"
    },
    {
      "tool_name": "contradiction_register_query",
      "params": { "domain": "dasha", "graha_filter": ["rahu"] },
      "token_budget": 1500,
      "priority": "P2",
      "reason": "Surface contradictions in Rahu dasha interpretations for balanced synthesis"
    },
    {
      "tool_name": "vector_search",
      "params": { "query": "Rahu dasha experience challenges remedies", "limit": 5 },
      "token_budget": 2000,
      "priority": "P3",
      "reason": "Supplementary: native's own life-event context during Rahu periods"
    },
    null
  ]
}
```

### 12.5 Prompt Versioning Protocol

The planner prompt is a living artifact. Any change to the system prompt text or few-shot examples:

1. Creates a new version in `00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md` (use in-place amendment with changelog entry for minor changes; new version file for breaking changes).
2. Must pass the EVAL golden set (EVAL-1) before merging — regression rate must be 0% on previously-passing examples.
3. Must be listed in the session's close-checklist `files_modified` block.
4. A/B testing (EVAL-3) is the recommended mechanism for evaluating prompt improvements before full rollout.

### 12.6 Compressed Manifest Generation

The manifest compressor (`platform/src/lib/pipeline/manifest_compressor.ts`) reads `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (108 entries) and produces a `CompressedManifestEntry[]` for the planner context. Compression reduces the manifest from ~21,000 tokens (raw JSON) to ~2,500 tokens.

**Compression algorithm:**
1. Filter to entries where `type = 'retrieval_tool'` (exclude governance docs, L1 facts, etc.).
2. For each retrieval tool, extract: `tool_name`, `description` (first 120 chars), `tags` (comma-joined), `estimated_tokens` (from manifest's `token_profile.typical_output`), `verified_live` (from manifest's `health.last_verified_returning_data !== null`).
3. Sort by `verified_live DESC, estimated_tokens ASC` so the planner sees live tools first.
4. If total manifest token count exceeds 3,000 tokens, truncate descriptions to 80 chars.

**Token budget arithmetic in system prompt:**
```
total_tool_budget = synthesis_context_limit × 0.6
                  - system_prompt_tokens (~800)
                  - history_snippet_tokens (≤ 600)
                  = synthesis_context_limit × 0.6 - 1,400

Planner instruction: "All token_budget values combined must not exceed {{ total_tool_budget }}"
```


---

*End of BHISMA Wave 2 Plan v1.1 — Gap-Hardened Production Specification*

**Status:** CURRENT | **Version:** 1.1 | **Last Updated:** 2026-05-01 | **Total Tasks:** 58 | **Total Effort:** ~1,161 developer-hours

