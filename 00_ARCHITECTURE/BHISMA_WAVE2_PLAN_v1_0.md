---
artifact: BHISMA_WAVE2_PLAN_v1_0
title: "BHISMA Wave 2: Universal Query Engine & Observability Architecture"
version: 1.0
status: CURRENT
canonical_id: BHISMA_WAVE2_PLAN
created_date: 2026-05-01
last_updated: 2026-05-01
scope: "Parallel to M3; independent execution; engineering specification"
relationship_to_M3: "Standalone workstream; no file conflicts; M3 may run in parallel without blocking"
author: Claude (Haiku 4.5)
changelog:
  v1.0:
    date: 2026-05-01
    summary: "Initial comprehensive specification; four parallel streams, 40 tasks, 3-4 week implementation"
---

# BHISMA WAVE 2: Universal Query Engine & Observability Architecture

**Version 1.0 · Production Specification**

## Executive Summary

BHISMA Wave 2 transforms the MARSYS-JIS query pipeline from a brittle, class-gated architecture into a robust, LLM-driven universal query engine backed by comprehensive observability. Wave 1 (completed, commit 03770d2) hardened infrastructure; Wave 2 hardens the request-response path and makes it visible.

The transformation fixes 7 identified bugs and closes 4 architectural gaps across four parallel streams:

1. **Stream UQE** — Universal Query Engine: replace class-based tool gating with LLM-driven per-tool planning
2. **Stream MON** — Monitoring Infrastructure: complete LLM call inventory + per-tool execution logging
3. **Stream TRACE** — Trace UI Modernization: nine new panels providing end-to-end query visibility
4. **Stream SCHEMA** — Query Investigation Database: comprehensive per-query audit trail persistence

Wave 2 is **independent of M3** (macro-phase) and runs in parallel. No shared files; rollback at any time.

**Delivery:** 3–4 weeks, four concurrent Claude Code sessions.

---

## §1 Ground Reality Audit: Known Bugs & Gaps

### Critical Bugs (Production Impact)

#### Bug B2W-1: remedial_codex_query SQL Error
**Severity:** CRITICAL — blocks entire L4 Remedial Codex channel  
**Status:** Identified 2026-04-30  
**Root Cause:** Column "canonical_id" does not exist in the remedial_codex table schema after migration  
**Evidence:** Silent failure — synthesis proceeds with zero L4 prescriptive data  
**File:** `platform/src/lib/tools/remedial_codex_query.ts`  
**Impact:** Every remedial query returns model priors only; corpus grounding lost for primary prescriptive channel  
**Fix Approach:** Update column reference to current schema; test against live chart  
**Acceptance:** SELECT returns ≥1 row for known remedial queries; citation_count ≥ 1 post-synthesis  

#### Bug B2W-2: MSR SQL Empty Seed Arrays
**Severity:** HIGH — MSR signal retrieval fails for 80% of queries  
**Status:** Identified 2026-04-30  
**Root Cause:** compose_bundle emits `planets=[]`, `houses=null` for remedial queries → WHERE planet = ANY($planets) returns zero rows  
**Evidence:** 499 MSR signals exist; msr_sql query returns 0 rows on remedial class  
**Files:**  
  - `platform/src/lib/bundle/composer.ts` (compose_bundle)  
  - `platform/src/lib/tools/msr_sql.ts` (query predicate)  
**Impact:** L2.5 signal layer unavailable; synthesis runs on L1 facts + model priors only  
**Fix Approaches:**
  - **Path A (immediate):** Add domain-only fallback when planets/houses arrays empty
  - **Path B (architectural):** Planner populates arrays from query text (requires UQE-5)
**Acceptance:** msr_sql returns ≥ 1 row for remedial queries  

#### Bug B2W-3: Pattern/Contradiction/Resonance Registers Return Zero Rows
**Severity:** HIGH — registers (L2.5-patterns) inaccessible  
**Status:** Identified 2026-04-30  
**Root Cause:** Same cascade as B2W-2; empty seed_hints from compose_bundle  
**Files:**  
  - `platform/src/lib/tools/pattern_register.ts`  
  - `platform/src/lib/tools/contradiction_register.ts`  
  - `platform/src/lib/tools/resonance_register.ts`  
**Impact:** Pattern synthesis blocked; contradiction detection unavailable  
**Fix:** Same as B2W-2  
**Acceptance:** Each register returns ≥ 1 row for test queries  

#### Bug B2W-4: Vector Search Not Authorized for Remedial Class
**Severity:** HIGH — semantic retrieval channel entirely bypassed  
**Status:** Identified 2026-04-30  
**Root Cause:** CAPABILITY_MANIFEST excludes vector_search from tools_authorized when query_class=remedial  
**Files:**  
  - `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (tools_authorized gating)  
  - `platform/src/lib/pipeline/manifest_lookup.ts` (authorization logic)  
**Impact:** Embedding index unused for remedial queries; vector retrieval zero chunks  
**Fix:** Remove class-based tools_authorized gating; let UQE planner decide per query  
**Acceptance:** vector_search authorized for all query classes  

#### Bug B2W-5: Synthesis Model Non-Determinism (RC-6)
**Severity:** HIGH — produces contradictory prescriptions  
**Status:** Identified 2026-04-30  
**Root Cause:** Synthesis model (e.g., claude-sonnet-4-6) temperature unset (defaults to model's non-zero value)  
**Evidence:** Byte-identical input → opposite outputs observed  
**Files:** `platform/src/lib/synthesis/single_model_strategy.ts`  
**Impact:** Unreliable prescriptions  
**Fix:** Set temperature=0 for single_answer queries; temperature=0.3 for exploratory  
**Acceptance:** temperature visible in trace; no variation for identical inputs  

#### Bug B2W-6: Ungrounded Citations (B.3 Violation)
**Severity:** MEDIUM  
**Status:** Identified 2026-04-30; blocks PipelineError gate  
**Root Cause:** Bugs B2W-1 through B2W-4 leave synthesis with ≤20 L1 facts; citation_count=0  
**Evidence:** Every remedial response cites Phaladīpikā / BPHS from model training, not corpus  
**Files:** All synthesis output paths  
**Impact:** Violates B.3 (derivation-ledger mandate)  
**Fix:** Structural — fixing B2W-1–B2W-4 enables corpus grounding  
**Acceptance:** Hard gate raises PipelineError if citation_count=0 AND prescriptive after deployment  

#### Bug B2W-7: Trace Step Sequence Collisions
**Severity:** MEDIUM — observability broken  
**Status:** Identified 2026-04-30  
**Root Cause:** context_assembly and vector_search both emit step_seq=9; synthesis orphaned at seq 11  
**Files:** `platform/src/lib/trace/emitter.ts`  
**Impact:** Trace analysis tools cannot reconstruct correct pipeline order  
**Acceptance:** step_seq unique within query_id  

### Architectural Gaps (Design Limitations)

#### Gap G1: Classify Bottleneck
Complex queries forced into one class; entire tool authorization gated on single bucket.

#### Gap G2: Per-Tool Planner Always Disabled
Planner mechanism exists (LLM_FIRST_PLANNER_ENABLED) but forced OFF on every query.

#### Gap G3: Incomplete LLM Call Inventory
Current trace captures synthesis only; missing worker, planner, title generation, cost breakdown.

#### Gap G4: No Comprehensive Query Investigation Log
Cannot debug failed queries or verify B.3 compliance post-hoc; no per-tool execution log.

---

## §2 LLM Usage Map: Current → Proposed

Complete inventory of every LLM call in the system:

| Call ID | Stage | Current Model | Traced? | Proposed | New Trace |
|---------|-------|---|---|---|---|
| LLM-1 | Classify | family worker | partial | **REMOVE** | N/A |
| **LLM-1-NEW** | **Manifest Planner** | **family worker** | **NO** | **family worker** | **NEW** |
| LLM-2 | Synthesis | user-selected | yes | user-selected | temperature tracking |
| **LLM-3** | **Title Generation** | **haiku** | **NO** | **haiku** | **NEW** |
| LLM-4 | o-series Reasoning | o1/o3/o4-mini | partial | o1/o3/o4-mini | reasoning_tokens |

---

## §3 Four Parallel Streams: 40 Tasks

### Stream UQE: Universal Query Engine (10 tasks)

**UQE-1: Fix remedial_codex_query SQL**
- Identify schema; update column reference
- File: `platform/src/lib/tools/remedial_codex_query.ts`
- Effort: 1–2 hours
- Acceptance: SELECT returns ≥1 row; citation_count ≥ 1

**UQE-2: Set Synthesis Temperature Logic**
- Add temperature=0 for single_answer; 0.3 for exploratory
- File: `platform/src/lib/synthesis/single_model_strategy.ts` (~line 150–200)
- Effort: 4–6 hours
- Acceptance: Byte-identical input → identical output (×5 test loops)

**UQE-3: Hard Gate on Citation Count Zero**
- Add PipelineError if citation_count=0 AND prescriptive
- File: `platform/src/lib/audit/validator.ts`
- Effort: 2–3 hours
- Acceptance: Gate triggers; error message surfaces investigation link

**UQE-4: Full Manifest Exposure**
- Worker LLM reads entire CAPABILITY_MANIFEST
- File: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- Effort: 1–2 weeks (includes prompt engineering)
- Acceptance: Planner reads full manifest; JSON valid; reasoning present

**UQE-5: Universal Per-Tool Planner (ALWAYS-ON)**
- Replace classify+compose with LLM-first planner
- Files: `platform/src/lib/pipeline/universal_query_engine.ts` (new), `manifest_planner.ts` (new)
- Effort: 2–3 weeks
- Acceptance: All queries route through planner; planner latency p95 < 500ms

**UQE-6: Remove Classify Step and Class-Based Gating**
- Delete classify.ts, composer.ts, manifest_lookup.ts
- File changes: `platform/src/routes/api/chat.ts`
- Effort: 1–2 weeks (routing refactor)
- Acceptance: Classify step not in trace; all tools available

**UQE-7: Domain-Only Fallback for MSR / Registers**
- Add fallback when planets/houses empty
- Files: msr_sql.ts, pattern_register.ts, contradiction_register.ts, resonance_register.ts
- Effort: 4–6 hours
- Acceptance: Fallback returns ≥1 signal

**UQE-8: Update CAPABILITY_MANIFEST with Metadata**
- Add query_schema, token_cost_hint, linked_data_asset_id
- File: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- Effort: 4–6 hours
- Acceptance: All 8 tools have complete schema; validates

**UQE-9: Fix Trace Step Sequence Collisions**
- Atomic increment for step_seq; parallel-group awareness
- File: `platform/src/lib/trace/emitter.ts`
- Effort: 2–4 hours
- Acceptance: step_seq unique within query_id

**UQE-10: Feature Flag Retirement Path**
- Mark LLM_FIRST_PLANNER_ENABLED deprecated
- File: `00_ARCHITECTURE/MIGRATION_NOTES_v1_0.md` (new)
- Effort: 1 hour
- Acceptance: Timeline published; v2.1 removal date set

---

### Stream MON: Monitoring Infrastructure (10 tasks)

**MON-1: Design llm_call_log Table**
- One row per LLM call (classify, planner, synthesis, title, reasoning)
- Schema: query_id, call_sequence, call_stage, model_id, provider, temperature, tokens, latency, cost_usd
- Effort: 2–3 hours
- Acceptance: Table created; 4 indexes; schema matches TypeScript

**MON-2: Design query_plan_log Table**
- Full planner JSON output per query
- Schema: query_id, plan_output_json JSONB, tool_count, tools_enabled, parsing_success
- Effort: 2–3 hours
- Acceptance: Table created; JSONB parses correctly

**MON-3: Design tool_execution_log Table**
- Per-tool execution (params, status, rows/chunks, latency, data_asset)
- Schema: query_id, tool_name, params_sent, execution_status, rows_returned, data_asset_id
- Effort: 2–3 hours
- Acceptance: Table created; status='zero_rows' tracked

**MON-4: Design context_assembly_log Table**
- Per-layer token contributions (L1, L2.5-signals, L2.5-patterns, L4, vector, CGM)
- Schema: query_id, layer_name, item_count, token_estimate, items_json
- Effort: 2–3 hours
- Acceptance: Table created; 6 layers logged per query

**MON-5: Emit llm_call_log Writes**
- Instrument planner, synthesis, title generation LLM calls
- Files: manifest_planner.ts (new), single_model_strategy.ts, title_generator.ts
- Effort: 1 week
- Acceptance: llm_call_log populated for 100% of calls; tokens match SDK

**MON-6: Emit query_plan_log Write**
- Write planner output after planner generates JSON
- Files: manifest_planner.ts, query_investigation.ts (new helper)
- Effort: 4–6 hours
- Acceptance: query_plan_log one row per query; parsing errors captured

**MON-7: Emit tool_execution_log Writes**
- Log every tool's execution (params, result count, status, latency)
- Files: All 6 tool files
- Effort: 1–2 weeks
- Acceptance: All tools emit records; status='zero_rows' captured

**MON-8: Emit context_assembly_log Write**
- Log per-layer token contributions after assembly
- File: context_assembly.ts
- Effort: 4–6 hours
- Acceptance: Layer logs correct; token sums match input

**MON-9: Create /api/investigation/:query_id Endpoint**
- Return all logs for single query (joined across 4 tables)
- File: `platform/src/routes/api/investigation/queries/:id.ts` (new)
- Effort: 1 week
- Acceptance: Endpoint returns all logs; response < 500ms

**MON-10: Create Analytics Views**
- Pre-computed views: cost_by_model, latency_by_stage, tool_data_by_class
- File: `platform/migrations/20260501_analytics_views.sql` (new)
- Effort: 4–6 hours
- Acceptance: Views queryable; < 1s response

---

### Stream TRACE: Trace UI Modernization (9 tasks)

**TRACE-1: LLM Call Map Panel**
- Visual inventory of every LLM call; model, tokens, latency, cost per call
- Component: `platform/src/components/trace/LLMCallMap.tsx` (new)
- Effort: 1 week
- Acceptance: All calls visible; cost/token totals correct

**TRACE-2: Query Plan Panel**
- Render planner JSON; per-tool params, token budget, reasoning
- Component: `platform/src/components/trace/QueryPlan.tsx` (new)
- Effort: 1 week
- Acceptance: JSON structure visible; drill-down to execution

**TRACE-3: Tool Execution Panel**
- Status cards per tool; params sent, rows/chunks returned, latency, data asset
- Component: `platform/src/components/trace/ToolExecution.tsx` (new)
- Effort: 1 week
- Acceptance: All tools visible; status colors correct

**TRACE-4: Data Asset Flow Panel**
- Sankey diagram; assets → synthesis model; arrow weight = tokens
- Component: `platform/src/components/trace/DataAssetFlow.tsx` (new)
- Effort: 1 week (SVG/Canvas rendering)
- Acceptance: Arrow weights proportional; interaction works

**TRACE-5: Context Assembly Panel**
- Stacked bar by layer; drill-down to per-layer items
- Component: `platform/src/components/trace/ContextAssembly.tsx` (new)
- Effort: 1.5 weeks
- Acceptance: Token totals match; drill-in functional

**TRACE-6: Synthesis Receipt Panel**
- Input token breakdown, temperature, citation readiness, B.3 gate status, cost
- Component: `platform/src/components/trace/SynthesisReceipt.tsx` (new)
- Effort: 1 week
- Acceptance: Citation count badge; B.3 status visible

**TRACE-7: Query Timeline**
- Horizontal timeline; parallel steps on same band; latency bars
- Component: `platform/src/components/trace/QueryTimeline.tsx` (new)
- Effort: 1.5 weeks (SVG layout)
- Acceptance: All steps in correct order; parallel visible

**TRACE-8: Cost Breakdown Panel**
- Per-call cost; query total; session aggregates; budget tracking
- Component: `platform/src/components/trace/CostBreakdown.tsx` (new)
- Effort: 4–6 hours
- Acceptance: Per-call breakdown correct; session aggregates sum

**TRACE-9: Investigation Tab (Raw Logs)**
- Tabular display of all log tables; drill-in; export to JSON/CSV
- Component: `platform/src/components/trace/InvestigationTab.tsx` (new)
- Effort: 1.5 weeks
- Acceptance: All tables accessible; export valid

---

### Stream SCHEMA: Query Investigation Database (6 tasks)

**SCHEMA-1: Audit Existing Schema**
- Review query_trace_steps; identify 8+ gaps
- Effort: 4–6 hours
- Acceptance: Document current schema; list gaps

**SCHEMA-2: Design Query Investigation Log**
- Separate tables (MON-1–4) vs. consolidated table; decision + reasoning
- Effort: 2–3 hours
- Acceptance: Design decision documented

**SCHEMA-3: Write Migration Scripts**
- Create 4 migrations for new tables
- Files: `platform/migrations/20260501_*.sql` (4 files)
- Effort: 2–4 hours
- Acceptance: Migrations idempotent; schema matches TypeScript

**SCHEMA-4: Design Indexes for Investigation Patterns**
- Indexes for 8 common investigation queries
- Effort: 2–3 hours
- Acceptance: Indexes cover all patterns; query plans verified

**SCHEMA-5: Design /api/investigation/queries Endpoint**
- Query index with filters, pagination, sorting
- File: `platform/src/routes/api/investigation/queries/index.ts` (new)
- Effort: 1 week
- Acceptance: Filters work; pagination correct; response < 1s

**SCHEMA-6: Design Retention & Archival Policy**
- 90-day hot window; archive to GCS; deletion schedule
- File: `00_ARCHITECTURE/RETENTION_POLICY_v1_0.md` (new)
- Effort: 4–6 hours
- Acceptance: Policy documented; cleanup jobs scheduled

---

## §4 Implementation Sequencing

### Week 1: Immediate Wins (~45 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| UQE-1 | 2h | None | Platform |
| UQE-2 | 6h | None | Platform |
| UQE-3 | 3h | None | Platform |
| UQE-7 | 6h | None | Platform |
| UQE-8 | 6h | None | Platform |
| UQE-9 | 4h | None | Platform |
| MON-1/2/3/4 | 12h | None | Database |
| SCHEMA-1 | 6h | None | Database |

### Week 2: Core Planner (~227 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| UQE-4/5 | 80h | None | Platform |
| TRACE-1/2 | 80h | None | Frontend |
| MON-5/6 | 60h | UQE-5 | Platform |
| SCHEMA-2/3 | 7h | None | Database |

### Week 3: Tools & Traces (~293 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| UQE-6 | 40h | UQE-5 | Platform |
| TRACE-3/4/5 | 140h | MON-3/4 | Frontend |
| MON-7/8 | 70h | None | Platform |
| SCHEMA-4/5 | 43h | None | Database |

### Week 4: Convergence (~288 hours)

| Task | Effort | Blockers | Owner |
|------|--------|----------|-------|
| TRACE-6/7/8/9 | 145h | MON-9 | Frontend |
| MON-9/10 | 55h | None | Platform |
| UQE-10 | 2h | None | Platform |
| SCHEMA-6 | 6h | None | Database |
| Integration testing | 80h | All streams | QA |

**Grand Total:** ~853 developer-hours (3–4 concurrent FTE over 4 weeks)

---

## §5 Acceptance Criteria (Machine-Testable)

**UQE Stream:**
- [ ] UQE-1: remedial_codex_query SELECT returns ≥1 row
- [ ] UQE-2: temperature=0 for single_answer; byte-identical input → identical output (×5 loops)
- [ ] UQE-3: PipelineError raised if citation_count=0 AND prescriptive
- [ ] UQE-4: Manifest includes query_schema for all 8 tools
- [ ] UQE-5: Planner routed on 100% of queries; latency p95 < 500ms
- [ ] UQE-6: Classify step not in trace; all tools available
- [ ] UQE-7: Domain fallback returns ≥1 signal
- [ ] UQE-8: Manifest entries validated
- [ ] UQE-9: step_seq unique within query_id
- [ ] UQE-10: Deprecation timeline published

**MON Stream:**
- [ ] MON-1–4: All tables created and indexed
- [ ] MON-5–8: llm_call_log, query_plan_log, tool_execution_log, context_assembly_log populated
- [ ] MON-9: /api/investigation/:query_id returns complete logs; response < 500ms
- [ ] MON-10: Analytics views queryable

**TRACE Stream:**
- [ ] TRACE-1–9: All 9 panels render correctly
- [ ] All panels show correct token/cost/latency data
- [ ] Drill-down interactions functional
- [ ] Render latency < 500ms

**SCHEMA Stream:**
- [ ] SCHEMA-1–6: All artifacts delivered
- [ ] Migrations idempotent; apply cleanly to staging
- [ ] Retention policy enforced
- [ ] Zero-downtime migration verified

---

## §6 Known Risks & Mitigations

**Risk R1: Planner Latency**  
Mitigation: Cache manifest; use Haiku; measure p95 < 500ms

**Risk R2: Planner Hallucination**  
Mitigation: Validate output against query_schema; manual review first 20 outputs

**Risk R3: Database Bloat**  
Mitigation: Retention policy (90-day hot, archive, delete); cleanup jobs

**Risk R4: Context Loss (Classify Removal)**  
Mitigation: Audit downstream code; preserve query_class in context

**Risk R5: TRACE UI Performance**  
Mitigation: Virtualize large lists; use Canvas for timelines; lazy-load investigation tab

**Risk R6: B.3 Compliance Gate Too Strict**  
Mitigation: Gate only prescriptive queries; allow admin override; track false positives

**Risk R7: Migration Failures**  
Mitigation: Test on staging; idempotent migrations; rollback pre-tested

---

## §7 Relationship to M3

**Wave 2 is standalone; no blocking dependencies on M3.**

**Isolation:**
- New feature flags (separate namespace)
- New DB tables (non-destructive)
- New React components (additive)
- Pipeline refactor: coordinate merge if M3 also touches routing

**Rollback:** ≤ 2 hours; revert flags + pipeline code; keep DB tables.

---

*End of BHISMA Wave 2 Plan v1.0*

---

## §8 Technical Appendix: Database Schema (PostgreSQL DDL)

All tables created in the `public` schema, compatible with Cloud SQL (PostgreSQL 14+) via Auth Proxy on `127.0.0.1:5433`.

### A. llm_call_log

Tracks every individual LLM call across the pipeline. One row per call, regardless of model or stage.

```sql
CREATE TABLE llm_call_log (
  id                  BIGSERIAL PRIMARY KEY,
  query_id            UUID        NOT NULL,
  conversation_id     UUID,
  call_seq            SMALLINT    NOT NULL,        -- ordering within a query (1=planner, 2=synthesis, 3=title)
  call_stage          TEXT        NOT NULL,        -- 'planner' | 'synthesis' | 'title' | 'reasoning'
  model_id            TEXT        NOT NULL,        -- matches registry id, e.g. 'claude-haiku-4-5'
  provider            TEXT        NOT NULL,        -- 'anthropic' | 'google' | 'deepseek' | 'openai'
  calling_convention  TEXT        NOT NULL DEFAULT 'standard', -- 'standard' | 'reasoning'
  temperature         NUMERIC(4,2),                -- null = model default (bug), 0 = deterministic
  input_tokens        INTEGER,
  output_tokens       INTEGER,
  reasoning_tokens    INTEGER,                     -- o-series only
  latency_ms          INTEGER,
  cost_usd            NUMERIC(10,6),               -- input_tokens/1M * costPer1MInput + output_tokens/1M * costPer1MOutput
  prompt_preview      TEXT,                        -- first 500 chars of prompt for debugging
  completion_preview  TEXT,                        -- first 500 chars of completion
  error_code          TEXT,                        -- null on success
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX llm_call_log_query_id      ON llm_call_log (query_id);
CREATE INDEX llm_call_log_model_id      ON llm_call_log (model_id);
CREATE INDEX llm_call_log_call_stage    ON llm_call_log (call_stage);
CREATE INDEX llm_call_log_created_at    ON llm_call_log (created_at);
CREATE INDEX llm_call_log_cost          ON llm_call_log (cost_usd);
-- Composite for analytics: cost by model by day
CREATE INDEX llm_call_log_model_day     ON llm_call_log (model_id, DATE_TRUNC('day', created_at));
```

### B. query_plan_log

Stores the full JSON plan emitted by the Universal Per-Tool Planner for every query.

```sql
CREATE TABLE query_plan_log (
  id                    BIGSERIAL PRIMARY KEY,
  query_id              UUID        NOT NULL UNIQUE,  -- one plan per query
  conversation_id       UUID,
  planner_model_id      TEXT        NOT NULL,         -- worker model used
  planner_latency_ms    INTEGER,
  tool_count_total      SMALLINT    NOT NULL,         -- tools in manifest shown to planner
  tool_count_planned    SMALLINT    NOT NULL,         -- tools planner chose to call
  tool_count_skipped    SMALLINT    NOT NULL,         -- tools planner explicitly skipped
  plan_json             JSONB       NOT NULL,         -- full [{tool_name, params, token_budget, reason}] array
  query_intent_summary  TEXT,                        -- planner's one-line intent extraction
  planning_rationale    TEXT,                        -- planner's reasoning
  synthesis_guidance    TEXT,                        -- planner's hint to synthesis model
  planning_confidence   NUMERIC(3,2),               -- 0.0–1.0
  parse_success         BOOLEAN     NOT NULL DEFAULT TRUE,
  parse_error           TEXT,                        -- if plan JSON was malformed
  fallback_used         BOOLEAN     NOT NULL DEFAULT FALSE, -- true if planner failed and old path was used
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX query_plan_log_query_id       ON query_plan_log (query_id);
CREATE INDEX query_plan_log_created_at     ON query_plan_log (created_at);
CREATE INDEX query_plan_log_confidence     ON query_plan_log (planning_confidence);
CREATE INDEX query_plan_log_fallback       ON query_plan_log (fallback_used) WHERE fallback_used = TRUE;
-- GIN index for JSONB querying (e.g. find all queries that planned vector_search)
CREATE INDEX query_plan_log_plan_gin       ON query_plan_log USING GIN (plan_json);
```

### C. tool_execution_log

One row per tool execution per query. Covers all parallel tool calls.

```sql
CREATE TABLE tool_execution_log (
  id                  BIGSERIAL PRIMARY KEY,
  query_id            UUID        NOT NULL,
  tool_name           TEXT        NOT NULL,         -- 'l1_facts_query' | 'msr_sql' | 'vector_search' | etc.
  parallel_group      TEXT,                         -- e.g. 'tool_fetch' — matches trace parallel_group
  execution_status    TEXT        NOT NULL,         -- 'ok' | 'zero_rows' | 'error' | 'skipped'
  params_sent         JSONB,                        -- exact params the planner specified
  rows_returned       INTEGER,                      -- for sql tools
  chunks_returned     INTEGER,                      -- for vector tools
  top_score           NUMERIC(5,4),                 -- vector_search: best similarity score
  tokens_contributed  INTEGER,                      -- tokens this tool's results added to context
  latency_ms          INTEGER,
  data_asset_id       TEXT,                         -- e.g. 'FORENSIC' | 'MSR' | 'CGM' | 'REMEDIAL_CODEX'
  error_message       TEXT,                         -- null on success
  error_code          TEXT,                         -- machine-readable: 'SQL_ERROR' | 'TIMEOUT' | 'EMPTY_PARAMS'
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX tool_exec_query_id         ON tool_execution_log (query_id);
CREATE INDEX tool_exec_tool_name        ON tool_execution_log (tool_name);
CREATE INDEX tool_exec_status           ON tool_execution_log (execution_status);
CREATE INDEX tool_exec_zero_rows        ON tool_execution_log (tool_name, execution_status)
  WHERE execution_status = 'zero_rows';
CREATE INDEX tool_exec_errors           ON tool_execution_log (tool_name, error_code)
  WHERE execution_status = 'error';
CREATE INDEX tool_exec_created_at       ON tool_execution_log (created_at);
-- Composite for tool success rate analytics
CREATE INDEX tool_exec_tool_day_status  ON tool_execution_log (tool_name, DATE_TRUNC('day', created_at), execution_status);
```

### D. context_assembly_log

Per-layer token breakdown at context assembly. Enables the TRACE-5 stacked bar chart.

```sql
CREATE TABLE context_assembly_log (
  id                  BIGSERIAL PRIMARY KEY,
  query_id            UUID        NOT NULL UNIQUE,  -- one assembly per query
  total_tokens        INTEGER     NOT NULL,
  l1_tokens           INTEGER     NOT NULL DEFAULT 0,
  l1_item_count       INTEGER     NOT NULL DEFAULT 0,
  cgm_tokens          INTEGER     NOT NULL DEFAULT 0,
  cgm_node_count      INTEGER     NOT NULL DEFAULT 0,
  msr_tokens          INTEGER     NOT NULL DEFAULT 0,
  msr_signal_count    INTEGER     NOT NULL DEFAULT 0,
  pattern_tokens      INTEGER     NOT NULL DEFAULT 0,
  pattern_item_count  INTEGER     NOT NULL DEFAULT 0,
  vector_tokens       INTEGER     NOT NULL DEFAULT 0,
  vector_chunk_count  INTEGER     NOT NULL DEFAULT 0,
  l4_tokens           INTEGER     NOT NULL DEFAULT 0,
  l4_item_count       INTEGER     NOT NULL DEFAULT 0,
  system_tokens       INTEGER     NOT NULL DEFAULT 0,
  -- B.3 compliance fields
  citation_count      INTEGER,                      -- citations detected in synthesis output (set post-synthesis)
  b3_compliant        BOOLEAN,                      -- citation_count > 0 for prescriptive query
  expected_output_shape TEXT,                       -- 'single_answer' | 'narrative' | 'table' | etc.
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ctx_assembly_query_id      ON context_assembly_log (query_id);
CREATE INDEX ctx_assembly_created_at    ON context_assembly_log (created_at);
CREATE INDEX ctx_assembly_b3            ON context_assembly_log (b3_compliant)
  WHERE b3_compliant = FALSE;
CREATE INDEX ctx_assembly_total_tokens  ON context_assembly_log (total_tokens);
```

### E. query_investigation_log (master record)

Consolidated per-query record joining all the above. Written at query completion. Enables fast single-query investigation without JOIN-ing 4 tables.

```sql
CREATE TABLE query_investigation_log (
  query_id              UUID        PRIMARY KEY,
  conversation_id       UUID,
  chart_id              TEXT        NOT NULL,
  query_text            TEXT,
  query_text_hash       TEXT,                       -- SHA-256 for deduplication analysis
  -- Model selection
  synthesis_model_id    TEXT        NOT NULL,
  worker_model_id       TEXT        NOT NULL,
  synthesis_provider    TEXT        NOT NULL,
  -- Pipeline outcome
  pipeline_status       TEXT        NOT NULL,       -- 'success' | 'error' | 'partial'
  error_stage           TEXT,                       -- which stage failed
  error_code            TEXT,
  -- Planner
  planner_tool_count    SMALLINT,
  planner_latency_ms    INTEGER,
  planning_confidence   NUMERIC(3,2),
  fallback_to_classify  BOOLEAN     NOT NULL DEFAULT FALSE,
  -- Tool execution summary (denormalised for fast filtering)
  tools_executed        TEXT[],                     -- ['l1_facts_query','msr_sql',...]
  tools_zero_rows       TEXT[],                     -- tools that returned 0 rows
  tools_errored         TEXT[],                     -- tools that errored
  -- Context assembly
  total_context_tokens  INTEGER,
  l2_token_ratio        NUMERIC(5,4),               -- l2_tokens / total_tokens (0 = no corpus grounding)
  -- Synthesis
  synthesis_temperature NUMERIC(4,2),
  synthesis_input_tokens  INTEGER,
  synthesis_output_tokens INTEGER,
  citation_count        INTEGER,
  b3_compliant          BOOLEAN,
  expected_output_shape TEXT,
  -- Cost
  planning_cost_usd     NUMERIC(10,6),
  synthesis_cost_usd    NUMERIC(10,6),
  title_cost_usd        NUMERIC(10,6),
  total_cost_usd        NUMERIC(10,6),
  -- Latency
  total_latency_ms      INTEGER,
  plan_latency_ms       INTEGER,
  tool_fetch_latency_ms INTEGER,
  assembly_latency_ms   INTEGER,
  synthesis_latency_ms  INTEGER,
  -- Metadata
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX qil_conversation_id       ON query_investigation_log (conversation_id);
CREATE INDEX qil_chart_id              ON query_investigation_log (chart_id);
CREATE INDEX qil_created_at            ON query_investigation_log (created_at DESC);
CREATE INDEX qil_synthesis_model       ON query_investigation_log (synthesis_model_id);
CREATE INDEX qil_pipeline_status       ON query_investigation_log (pipeline_status);
CREATE INDEX qil_citation_count        ON query_investigation_log (citation_count);
CREATE INDEX qil_b3_non_compliant      ON query_investigation_log (created_at DESC)
  WHERE b3_compliant = FALSE;
CREATE INDEX qil_zero_token_ratio      ON query_investigation_log (l2_token_ratio)
  WHERE l2_token_ratio < 0.05;           -- catches effectively-empty-corpus queries
CREATE INDEX qil_high_cost             ON query_investigation_log (total_cost_usd DESC);
CREATE INDEX qil_text_hash             ON query_investigation_log (query_text_hash); -- for RC-6 analysis
-- GIN indexes for array fields (investigation: "find all queries where vector_search errored")
CREATE INDEX qil_tools_executed_gin    ON query_investigation_log USING GIN (tools_executed);
CREATE INDEX qil_tools_errored_gin     ON query_investigation_log USING GIN (tools_errored);
CREATE INDEX qil_tools_zero_gin        ON query_investigation_log USING GIN (tools_zero_rows);
```

### F. Analytics Views

Pre-computed for the TRACE-8 Cost panel and the /api/investigation/queries analytics endpoint.

```sql
-- Daily cost by model
CREATE MATERIALIZED VIEW mv_daily_cost_by_model AS
SELECT
  DATE_TRUNC('day', created_at)::DATE AS day,
  model_id,
  provider,
  call_stage,
  COUNT(*)                            AS call_count,
  SUM(input_tokens)                   AS total_input_tokens,
  SUM(output_tokens)                  AS total_output_tokens,
  SUM(cost_usd)                       AS total_cost_usd,
  AVG(latency_ms)                     AS avg_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms
FROM llm_call_log
GROUP BY 1, 2, 3, 4
WITH DATA;

CREATE UNIQUE INDEX mv_daily_cost_pk ON mv_daily_cost_by_model (day, model_id, call_stage);
-- Refresh daily via pg_cron or a scheduled task
-- SELECT cron.schedule('0 1 * * *', $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_cost_by_model$$);

-- Tool health by day
CREATE MATERIALIZED VIEW mv_daily_tool_health AS
SELECT
  DATE_TRUNC('day', created_at)::DATE   AS day,
  tool_name,
  COUNT(*)                              AS total_executions,
  SUM(CASE WHEN execution_status = 'ok'        THEN 1 ELSE 0 END) AS ok_count,
  SUM(CASE WHEN execution_status = 'zero_rows' THEN 1 ELSE 0 END) AS zero_rows_count,
  SUM(CASE WHEN execution_status = 'error'     THEN 1 ELSE 0 END) AS error_count,
  SUM(CASE WHEN execution_status = 'skipped'   THEN 1 ELSE 0 END) AS skipped_count,
  AVG(latency_ms)                       AS avg_latency_ms,
  AVG(rows_returned)                    AS avg_rows_returned
FROM tool_execution_log
GROUP BY 1, 2
WITH DATA;

CREATE UNIQUE INDEX mv_tool_health_pk ON mv_daily_tool_health (day, tool_name);

-- Corpus grounding rate by day
CREATE VIEW v_daily_grounding_health AS
SELECT
  DATE_TRUNC('day', created_at)::DATE       AS day,
  COUNT(*)                                  AS total_queries,
  AVG(l2_token_ratio)                       AS avg_l2_token_ratio,
  SUM(CASE WHEN b3_compliant THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) AS b3_compliance_rate,
  SUM(CASE WHEN citation_count = 0 THEN 1 ELSE 0 END) AS zero_citation_queries,
  AVG(total_cost_usd)                       AS avg_cost_per_query,
  SUM(total_cost_usd)                       AS total_cost
FROM query_investigation_log
GROUP BY 1;
```

---

## §9 Technical Appendix: TypeScript Interfaces (new / extended)

### A. Extended TraceDataSummary (trace/types.ts additions)

```typescript
// ── BHISMA-B2W additive fields (all optional) ────────────────────────────────
// Appended to the existing TraceDataSummary interface in trace/types.ts

/** planner step: model_id of the worker LLM that ran the planner */
planner_model_id?: string
/** planner step: number of tools in the manifest shown to the planner */
manifest_tool_count?: number
/** planner step: number of tools the planner chose to call */
planned_tool_count?: number
/** planner step: number of tools the planner explicitly skipped */
skipped_tool_count?: number
/** planner step: true if planner output was malformed and fallback was used */
fallback_used?: boolean
/** tool execution step: name of the data asset queried */
data_asset_id?: string
/** tool execution step: execution_status code */
execution_status?: 'ok' | 'zero_rows' | 'error' | 'skipped'
/** synthesis step: temperature actually used (not just configured) */
temperature_used?: number
/** synthesis step: ratio of L2 tokens to total context tokens (0 = no corpus) */
l2_token_ratio?: number
/** llm_call step: total cost in USD for this LLM call */
call_cost_usd?: number
/** title_generation step: model used for title */
title_model_id?: string
```

### B. New TraceStep types for Wave 2

```typescript
// New step_name values emitted by the UQE pipeline:
type W2StepName =
  | 'manifest_exposure'    // worker LLM reads full manifest
  | 'universal_planner'    // worker LLM emits per-tool JSON plan
  | 'tool_fetch'           // parallel tool execution (existing, step_name per tool)
  | 'context_assembly'     // existing
  | 'synthesis'            // existing
  | 'title_generation'     // NEW: now separately traced
  | 'llm_call'             // generic LLM call wrapper (for future calls)
  | 'step_error'           // existing
```

### C. UniversalQueryPlan (new, replaces QueryPlan for UQE pipeline)

```typescript
/** Emitted by the universal_planner step, stored in TracePayload.query_plan */
export interface UniversalQueryPlan {
  plan_id: string                        // UUID, also written to query_plan_log.query_id
  planner_model_id: string               // worker model that generated this plan
  planner_latency_ms: number
  query_intent_summary: string           // LLM's one-line extraction of query intent
  planning_rationale: string             // LLM's reasoning for tool selection
  synthesis_guidance?: string            // hints for synthesis model
  planning_confidence: number            // 0.0 – 1.0
  tool_calls: UniversalToolCallSpec[]    // ordered by priority
  manifest_version: string              // CAPABILITY_MANIFEST fingerprint at plan time
}

export interface UniversalToolCallSpec {
  tool_name: string
  params: Record<string, unknown>       // typed against the tool's query_schema
  token_budget: number                  // max tokens this tool should contribute
  priority: 1 | 2 | 3                  // 1 = must-have, 2 = important, 3 = nice-to-have
  reason: string                        // LLM's reason for including this tool
  data_asset_id: string                 // which corpus asset this tool reads from
}
```

### D. LLMCallMap component data shape (TRACE-1 panel)

```typescript
/** Consumed by platform/src/components/trace/LLMCallMap.tsx */
export interface LLMCallRecord {
  call_seq: number
  call_stage: 'planner' | 'synthesis' | 'title' | 'reasoning'
  model_id: string
  provider: Provider
  calling_convention: CallingConvention
  temperature: number | null            // null = was not set (bug indicator)
  input_tokens: number
  output_tokens: number
  reasoning_tokens?: number
  latency_ms: number
  cost_usd: number
  prompt_preview?: string
  is_worker: boolean                    // true for planner + title calls
  is_synthesis: boolean
}

/** Consumed by the parent TracePanel to build the LLMCallMap */
export interface LLMCallMapProps {
  calls: LLMCallRecord[]
  total_cost_usd: number
  // derived in component:
  // - planning_cost = sum of is_worker calls
  // - synthesis_cost = sum of is_synthesis calls
}
```

### E. ToolExecutionPanel data shape (TRACE-3 panel)

```typescript
/** Consumed by platform/src/components/trace/ToolExecution.tsx */
export interface ToolExecutionRecord {
  tool_name: string
  data_asset_id: string
  data_asset_label: string              // e.g. 'L1 FORENSIC' | 'L2.5 MSR' | 'L4 Remedial Codex'
  execution_status: 'ok' | 'zero_rows' | 'error' | 'skipped'
  params_sent: Record<string, unknown>
  rows_returned?: number
  chunks_returned?: number
  top_score?: number
  tokens_contributed: number
  latency_ms: number
  error_message?: string
  // visual props
  is_new_channel: boolean               // true for channels absent in old arch (vector, codex, msr for remedial)
}
```

---

## §10 Technical Appendix: TRACE Component Architecture

All new trace components live under `platform/src/components/trace/`. They consume data from:
1. The existing SSE stream of `TraceEvent` objects (real-time)
2. The new `/api/investigation/:query_id` endpoint (retrospective drill-in)

The design system used throughout:

```css
/* Color tokens — identical to existing Trace Command Center */
--bg-primary:        #0f1117;
--bg-surface:        #181b25;
--bg-surface-raised: #1e2130;
--border:            #2a2d3e;
--text-primary:      #e8eaf0;
--text-muted:        #6b7280;

/* Semantic accents */
--color-ok:          #2a9d5c;  /* working channels, ok status */
--color-error:       #d94f4f;  /* broken, error status */
--color-warn:        #e8873a;  /* degraded, zero-rows, warn */
--color-llm:         #7c5cbf;  /* any LLM call indicator */
--color-worker:      #5c6bc0;  /* worker model calls (planner, title) */
--color-synthesis:   #2a9d5c;  /* synthesis model call */
--color-data:        #3a7bd5;  /* data asset / L1 layer */
--color-l25:         #7c5cbf;  /* L2.5 layer */
--color-l4:          #d4a017;  /* L4 prescriptive layer */
--color-vector:      #2a9d5c;  /* vector store */
```

### Panel layout within the Consume module trace drawer

```
┌─────────────────────────────────────────────────┐
│  Query Timeline (TRACE-7) — full width, top     │
│  All pipeline steps as latency bars             │
├──────────────┬──────────────┬───────────────────┤
│ LLM Call Map │ Query Plan   │ Cost Breakdown    │
│ (TRACE-1)    │ (TRACE-2)    │ (TRACE-8)         │
├──────────────┴──────────────┴───────────────────┤
│  Tool Execution + Data Asset Flow               │
│  (TRACE-3 + TRACE-4) — side by side             │
├─────────────────────────────────────────────────┤
│  Context Assembly (TRACE-5) — stacked bar       │
├──────────────────────────┬──────────────────────┤
│  Synthesis Receipt        │ Investigation Tab    │
│  (TRACE-6)               │ (TRACE-9)            │
└──────────────────────────┴──────────────────────┘
```

### TRACE-1 LLM Call Map — key interactions
- Each call shown as a card: model badge (colour-coded by provider), calling_convention chip, token pill, latency bar, cost
- Worker calls (planner, title) shown with `--color-worker` left border
- Synthesis call shown with `--color-synthesis` left border
- o-series calls show reasoning_tokens as a secondary bar in `--color-llm`
- `temperature = null` shows an orange warning chip: "temp unset — nondeterministic"
- Click any card → expand to show prompt_preview + completion_preview (first 500 chars each)

### TRACE-2 Query Plan — key interactions
- Renders `UniversalQueryPlan.tool_calls[]` as expandable cards
- Collapsed: tool_name + priority badge + token_budget bar + one-line reason
- Expanded: full params as key:value chips, data_asset_id badge, full reason text
- Tools with `execution_status = 'zero_rows'` are highlighted orange post-execution
- Tools with `execution_status = 'error'` are highlighted red
- planning_confidence shown as a gauge (0.0–1.0) in the panel header

### TRACE-4 Data Asset Flow — key design
- SVG-based, not a third-party library (keeps bundle small)
- Six data asset nodes on the left, "Context Assembly" node on the right
- Arrow weight (stroke-width 1–8px) proportional to tokens_contributed
- Zero-contributing assets: grey dashed border, no arrow
- New channels (first time ever contributing): animated pulse on arrow
- Hover asset → shows data_asset_label, item_count, token_count tooltip

### TRACE-7 Query Timeline — key design
- Horizontal SVG timeline, 0ms → total_latency_ms
- Each TraceStep as a rectangle: x = started_at offset, width = latency_ms
- Parallel steps (same parallel_group) stacked on the same row
- Color by step_type: deterministic=blue, llm=purple, sql=green, vector=teal
- Click any bar → slides in the relevant detail panel (TRACE-1 for LLM, TRACE-3 for tools, etc.)
- Error steps shown in red; zero-row steps shown in amber

---

*End of BHISMA Wave 2 Plan v1.0 — Technical Appendix appended 2026-05-01*
