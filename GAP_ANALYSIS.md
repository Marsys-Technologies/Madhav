---
work_item: W1
authored: 2026-05-12
author: Gate II executor (Claude Code Sonnet 4.6, autonomous)
status: COMPLETE
purpose: Inventory every mismatch between what the trace UI consumes and what the new pipeline emits today.
---

# Gate II — W1 — Trace ↔ Pipeline Gap Analysis

## Executive summary

The repo runs **two parallel trace systems** simultaneously, and the trace UI is split across both with no shared schema:

| System | Storage | Schema | Consumer |
|---|---|---|---|
| **NEW (Phase 11B emitter)** | `query_trace_steps` table | `lib/trace/types.ts` — `TraceEvent`, `TraceStep`, `TraceQueryPlan`, `TraceDataSummary`, `TracePayload`, `TraceHistoryRow` | `TracePanel.tsx`, `PipelineLifecycleView.tsx`, `QueryDNAPanel.tsx`, `RetrievalScorecard.tsx`, `/api/trace/stream/[queryId]` (SSE) |
| **OLD (pre-rebuild parallel)** | `llm_call_log`, `tool_execution_log`, `plan_alternatives_log`, `context_assembly_item_log`, `synthesis_quality_scorecard`, `query_plan_log` | `lib/admin/trace_assembler.ts` — `TraceDocument` | `TraceModal.tsx`, `LifecycleGraph.tsx`, `lifecycle/*Node.tsx`, `step_detail/*Detail.tsx`, `HealthRail.tsx`, `QueryHeaderStrip.tsx`, `TimingRibbon.tsx`, `StepDetail.tsx`, `/api/admin/trace/[query_id]` |

This W1 documents that bifurcation, the additional emitter↔renderer drift inside each system, the orphan step variants per D7, the supporting-component findings (§F), and an autonomous resolution plan (§I) that consolidates everything onto `lib/trace/types.ts` while keeping renderers tolerant to the actual emit shape (§4.5 R2).

---

## §A — Stage vocabulary

Stage names hard-coded in renderers vs. stage names actually emitted by the new pipeline.

### Emitted by the new pipeline (per `app/api/chat/consume/route.ts` + `single_model_strategy.ts`)

| `step_name` | `step_type` | parallel_group | Status | Notes |
|---|---|---|---|---|
| `classify` | `llm` | — | CURRENT, **misleading name** | Per `route.ts:393` comment: "step_name 'classify' preserved for trace UI compat". This is actually the PLANNER step — emits `payload.query_plan` (RichQueryPlan), `payload.tool_calls`, `data_summary.query_class`. The legacy classifier no longer exists. **Per D3, this is the canonical Planner stage.** |
| `compose_bundle` | `deterministic` | — | CURRENT, NEW | Manifest-driven bundle hydration (asset count, floor_enforced). Not anticipated by brief. |
| `<tool_name>` (any of ~20 tools) | `sql` / `vector` / `gcs` / `llm` (per `toolStepType()`) | `tool_fetch` | CURRENT | The "Retrieval" stage per D5, but emitted as **many parallel sibling steps** keyed by the tool's manifest name. See §J.1 for the divergence from D5's stated 4 sub-tools. |
| `context_assembly` | `deterministic` | — | CURRENT, **vestigial** | Emitted from `single_model_strategy.ts:213`. Per CLAUDE.md §F: "ContextAssembly was removed entirely" in Pipeline-Transform-S1. What survives is a **short-circuit marker**: `data_summary.short_circuited`, `data_summary.total_token_estimate`, `data_summary.threshold`. Not a true assembly stage. |
| `synthesis` | `llm` | — | CURRENT | Single-model synthesis. Emits `data_summary.model`, `input_tokens`, `output_tokens`, `citation_count`, `temperature`, `output_shape_compliant`, `provider`, `reasoning_path`. |
| `synthesis_done` | `llm` | — | CURRENT (alt) | Some emit paths use `synthesis_done`. `PipelineLifecycleView` already treats both as the synthesize stage. |
| `citation_warn` | `deterministic` | — | CURRENT | Post-stream citation gate result. Not a top-level stage; render as Audit sub-item. |
| `citation_error` | `deterministic` | — | CURRENT | Post-stream citation gate HARD_BLOCK. Same as above. |
| `step_error` (status='error' on any step) | various | — | CURRENT | Generic error pathway, payload carries `error_message`, `error_stage`. |
| `history_summary` (LLM call_stage only, not a trace step) | — | — | LLM-only | Conversation-history summarization. Not a trace step. |

### Expected by D5/D1 (brief)

| Stage (brief) | Status | Disposition |
|---|---|---|
| `planner` | RENAMED | Emit site uses `classify`. Renderer maps `classify` → canonical `planner` stage. Per R2: don't modify emitter. |
| `retrieval` (grouped) | NEW (composite) | Aggregate all `parallel_group === 'tool_fetch'` steps under one container node. |
| `synthesis` | CURRENT | Matches `step_name === 'synthesis'` or `'synthesis_done'`. |
| `audit` | **NOT EMITTED AS A TRACE STEP** | Pipeline writes to `audit_events` table directly via `createAuditConsumer` (route.ts:616) and does NOT emit a trace step. See §J.2. |
| `checkpoint_4_5` | NOT EMITTED | All three checkpoints exist as modules under `lib/checkpoints/` but emit no trace steps. Feature flags `CHECKPOINT_4_5_ENABLED` / `_5_5_ENABLED` / `_8_5_ENABLED` are all `false` by default per `feature_flags.ts:83-89`. |
| `checkpoint_5_5` | NOT EMITTED | Same. |
| `checkpoint_8_5` | NOT EMITTED | Same. |

### Hard-coded by renderers

| Source | Hard-coded stage list | Decision |
|---|---|---|
| `LifecycleGraph.tsx` (old, TraceDocument-based) | `classify`, `plan`, `<fetches>`, `context_assembly`, `synthesis` | Rewrite per D5/D1 in W3. |
| `PipelineLifecycleView.tsx` (new, TraceStep-based) | `Classify`, `Plan`, `Retrieve`, `Assemble`, `Synthesize` | Rewrite per D5/D1 in W3. Note: it currently looks for `step_name === 'plan'` (never emitted) AND `step_name === 'classify'` (the actual planner). The "Plan" stage in the UI is therefore always blank. |
| `trace_assembler.ts` (old) | `classify`, `planner`, `synthesis` (call_stage discriminants) | Rewrite in W7 to read `query_trace_steps`. |
| `TraceModal.tsx` `buildStepOrder()` | Sequence from old TraceDocument | Rewire when assembler is rewired. |

### Stages classified

| Stage name (canonical) | CURRENT / RETIRED / RENAMED / NEW |
|---|---|
| `planner` | **RENAMED** from emitter's `classify` |
| `retrieval` (group) | **NEW** (composite over `parallel_group === 'tool_fetch'`) |
| `compose_bundle` | **NEW**, surface as sub-item of Planner stage |
| `context_assembly` | **RETIRED stage**, kept as **short-circuit metadata** only (do not render as a top-level stage; surface in Synthesis step-detail if needed) |
| `synthesis` | **CURRENT** |
| `audit` | **NEW shape** — must be sourced from `audit_events` table, not from `query_trace_steps`. Phase deferred (§J.2). |
| `checkpoint_4_5`, `_5_5`, `_8_5` | **NEW (zero-emit)** — render dimmed per D1; surface "0 of 3 ran" in the collapsible group. |

---

## §B — Step type discriminants

| Surface | Discriminant field | Values consumed | Values produced |
|---|---|---|---|
| **New (TraceStep)** | `step_type` | `'deterministic' \| 'llm' \| 'sql' \| 'vector' \| 'gcs'` (per `lib/trace/types.ts:11`) | Same — all five appear in `route.ts` (`toolStepType()`) and `single_model_strategy.ts`. ✅ |
| **New (TraceStep)** | `step_name` | Anything emitted; PipelineLifecycleView pattern-matches `'classify' \| 'plan' \| 'context_assembly' \| 'synthesis' \| 'synthesis_done'` | Emitter writes `'classify'`, `'compose_bundle'`, `<tool_name>`, `'context_assembly'`, `'synthesis'`, `'citation_warn'`, `'citation_error'`. `'plan'` is **never emitted** — the Plan stage card in PipelineLifecycleView never fires. |
| **New (TraceStep)** | `status` | `'pending' \| 'running' \| 'done' \| 'error'` | All four used. ✅ |
| **Old (TraceDocument)** | `call_stage` (LLM rows) | `'classifier' \| 'classify' \| 'planner' \| 'synthesis'` | trace_assembler reads `call_stage` from `llm_call_log`. Pipeline writes: see `pipeline_planner.ts:264,307,350` use `'planner'`; `single_model_strategy.ts:502` uses `'synthesis'`. NO emit site writes `'classifier'` or `'classify'` — those discriminants are dead-letter values. |
| **Old (TraceDocument)** | `tool_name` (ToolExec rows) | Any string | The `tool_execution_log` table is not currently populated by the new pipeline — pipeline writes to `query_trace_steps` only. **Old trace_assembler returns empty `fetches[]` for all new-pipeline queries.** |

---

## §C — Metadata field reconciliation

Per stage: fields read by renderer vs. fields written by emitter; ⚠ flag = mismatch.

### Planner (emitter `step_name='classify'`)

| Renderer reads | Emitter writes | Match? |
|---|---|---|
| `data_summary.query_class` | yes (route.ts:410) | ✅ |
| `data_summary.confidence` | yes (1.0 hard-coded, route.ts:411) | ✅ |
| `data_summary.planning_confidence` | yes (route.ts:412) | ✅ |
| `payload.query_plan` (full RichQueryPlan) | yes (route.ts:415) | ✅ |
| `payload.tool_calls` | yes (route.ts:423) | ✅ |
| `data_summary.model` | NOT WRITTEN here (only on `synthesis` step) | ⚠ Planner LLM model id is in `payload.query_plan.planning_model_id`, not `data_summary.model`. `PipelineLifecycleView.tsx:152` reads `data_summary.model` for the Plan card — always blank. |
| `data_summary.tools_authorized` | NOT WRITTEN — it's nested under `payload.query_plan.tools_authorized` and `payload.tool_calls[].tool_name` | renderers reach into `payload.query_plan.tools_authorized` correctly (`PipelineLifecycleView.tsx:96`). ✅ |
| `payload.query_plan.planning_rationale` | yes (route.ts:418) | ✅ |
| `payload.query_plan.synthesis_guidance` | yes (route.ts:419) | ✅ |
| `payload.query_plan.query_intent_summary` | yes (route.ts:417) | ✅ |

### Retrieval (per-tool steps, `parallel_group='tool_fetch'`)

| Renderer reads | Emitter writes | Match? |
|---|---|---|
| `step_name` (= tool name) | yes | ✅ |
| `step_type` | yes (sql/vector/gcs/llm) | ✅ |
| `data_summary.rows_returned` | yes (`buildToolSummary`) — for SQL/structured tools | ✅ |
| `data_summary.chunks_returned` | yes — for vector_search | ✅ |
| `data_summary.token_estimate` | yes | ✅ |
| `data_summary.top_score` | yes — vector only | ✅ |
| `data_summary.tool_name` | yes (when tool emits it) | ✅ |
| `payload.items[]` (TraceChunkItem) | yes — full retrieved chunk content | ✅ |
| **Per-sub-tool hit-rate** (brief mentions) | NOT WRITTEN | ⚠ Brief's W4 names "rows-fetched, latency, hit-rate, top-score". Hit-rate is not emitted; derive it client-side as `kept / raw` or omit. |
| `error_class` per fetch (TraceDocument.fetches[].error_class) | OLD ONLY — `tool_execution_log.error_class`. New pipeline emits `step_error` events instead. | ⚠ trace_assembler-mode (old) reads it; new mode does not write. |

### Synthesis (`step_name='synthesis'`)

| Renderer reads | Emitter writes | Match? |
|---|---|---|
| `data_summary.model` | yes (route.ts:568, `data_summary: { model: modelId }`) | ✅ |
| `data_summary.input_tokens`, `output_tokens` | yes (on synthesis_done) | ✅ |
| `data_summary.temperature` | yes (BHISMA-B3 additive) | ✅ |
| `data_summary.citation_count` | yes | ✅ |
| `data_summary.output_shape_compliant` | yes | ✅ |
| `data_summary.provider` | yes | ✅ |
| `data_summary.reasoning_path` | yes | ✅ |
| `payload.prompt_preview` | yes | ✅ |
| `payload.reasoning_trace` | yes — DeepSeek R1 only | ✅ |
| **Panel mode discriminant** | NOT WRITTEN | ⚠ Brief D6 expects `mode: 'single_model' \| 'panel'`. No emit site sets it. Per R1: default render to single_model; document. See §J.4. |
| **Panelist rows + aggregator row metadata** | NOT WRITTEN | ⚠ The panel orchestrator under `lib/synthesis/panel/` doesn't appear to emit per-panelist `TraceStep` rows. Per R2: render single Synthesis node with discriminated variant; if no panel data, fall through to single_model branch. |

### Audit

| Renderer reads | Emitter writes | Match? |
|---|---|---|
| _(no current Audit step-detail renderer)_ | `audit_events` table (consumer.ts:60, `audit_event_version: 1`) — NOT a `query_trace_steps` row | ⚠⚠ See §J.2. The brief's AuditStepDetail expects `validator verdict, disclosure tier, B.10/B.11 compliance flags, audit-event id`. None are in the trace step stream — must be fetched separately from `audit_events`. |

### Checkpoints (4.5 / 5.5 / 8.5)

All disabled by default; no emit sites under `lib/checkpoints/` call `traceEmitter.emitStep`. Per D1: render dimmed group with "0 of 3 ran". When (future) checkpoints enable + emit, the renderer must tolerate either shape.

---

## §D — Orphan references (per D7)

`grep -rn` results for retired stage names:

### `ClassifyStepDetail` / `ClassifyDetail`
- `platform/src/components/trace/step_detail/ClassifyDetail.tsx` — **DELETE** per D7
- `platform/src/components/trace/StepDetail.tsx:13,32,77` — imports + variant registry → remove
- `platform/src/components/trace/TraceModal.tsx:20,31` — `buildStepOrder` references "classify" string → keep as the **Planner** stage id (mapped via assembler) but rename the variant component
- `platform/src/components/trace/lifecycle/ClassifyNode.tsx` — **DELETE** (D7 spirit: classify stage retired; renderer node is part of the same orphan family)
- `platform/src/components/trace/LifecycleGraph.tsx:4,37,45-49` — remove ClassifyNode import + render block

### `ContextAssemblyStepDetail` / `ContextAssemblyDetail`
- `platform/src/components/trace/step_detail/ContextAssemblyDetail.tsx` — **DELETE** per D7
- `platform/src/components/trace/StepDetail.tsx:14,33,78` — imports + variant registry → remove
- `platform/src/components/trace/TraceModal.tsx:20` — `buildStepOrder` references "context_assembly" → drop from order
- `platform/src/components/trace/lifecycle/ContextAssemblyNode.tsx` — **DELETE**
- `platform/src/components/trace/LifecycleGraph.tsx:7,39,86-92` — remove ContextAssemblyNode import + render
- `platform/src/components/trace/ContextAssembly.tsx` — also an old top-level component used by TracePanel. **Mark for deletion** if grep shows no remaining consumers in TracePanel after W5.

### `context_assembly` as stage name
- Still EMITTED by `single_model_strategy.ts:213` (vestigial short-circuit marker). **Do NOT delete the emit site (must_not_touch).** Renderers should consume the short-circuit metadata into the Synthesis step-detail's Notes area or ignore it; per §A it is not a top-level stage.
- `PipelineLifecycleView.tsx:84,112-115` Assemble stage card relies on this. Will be retired in W3 (Assemble stage card removed).

### `classify` as stage name in DB
- DB rows in `query_trace_steps` keep `step_name='classify'`. Per R2: assembler maps `classify` → canonical `planner`. Do not require a DB migration.

---

## §E — Schema source (D4 resolution)

A schema file **exists** at:

```
platform/src/lib/trace/types.ts   (schema_version: 1.1, since BHISMA-B3 2026-05-01)
```

Exports: `StepType`, `StepStatus`, `TraceChunkItem`, `TraceToolCallSpec`, `TraceQueryPlan`, `TraceDataSummary`, `TracePayload`, `TraceStep`, `PlanningStartEvent`, `PlanningDoneEvent`, `TraceEvent`, `TraceHistoryRow`.

**Decision (per R8 + D4):** keep this file. Do NOT author a new `lib/admin/trace_schema.ts`. W2 extends this file in place with:

- `PipelineStage` enum — canonical stage names: `'planner' \| 'retrieval' \| 'synthesis' \| 'audit' \| 'checkpoint_4_5' \| 'checkpoint_5_5' \| 'checkpoint_8_5'`
- `STAGE_FROM_STEP_NAME: Record<string, PipelineStage>` mapping (`classify → planner`, `compose_bundle → planner` sub-item, `context_assembly → synthesis` sub-item, `<tool_name with parallel_group=tool_fetch> → retrieval`, `synthesis|synthesis_done → synthesis`, `citation_* → audit`)
- `RetrievalSubToolRun` — `{ tool_name: string; step_type: StepType; status: StepStatus; latency_ms: number | null; data_summary: TraceDataSummary; payload: TracePayload }` (NOT a 4-enum literal — see §J.1)
- `PlannerStepMetadata`, `SynthesisStepMetadata` (discriminated union `mode: 'single_model' | 'panel'` with brief-defined shape), `AuditStepMetadata`, `CheckpointStepMetadata`
- `AssembledTrace` — `{ query_id, total_latency_ms, query_plan: TraceQueryPlan | null, steps: TraceStep[], grouped: { planner; retrieval: RetrievalSubToolRun[]; synthesis; audit; checkpoints: CheckpointStepMetadata[] }, partial: boolean }`
- `interface QueryPlan extends TraceQueryPlan {}` — type alias keeping the brief's name; do NOT duplicate fields

**Old `lib/admin/trace_assembler.ts:TraceDocument`** stays exported for one realignment cycle, but `assembleTrace` is rewritten to (a) read from `query_trace_steps` first, then (b) compose `AssembledTrace`, then (c) project into `TraceDocument` for the legacy consumer set (`HealthRail`, `TraceModal`, etc.) until those are migrated. Marked `@deprecated`.

---

## §F — Supporting-component findings (D8)

### HealthRail (`platform/src/components/trace/HealthRail.tsx`)

- Imports `TraceDocument` (old). Reads `trace.query.health`, `trace.query.total_ms`, `trace.query.total_cost_usd`, `trace.baselines`, `trace.anomalies`, `trace.partial`.
- Action: realign to consume `AssembledTrace` (new). Project equivalent fields via the assembler's `derive*` helpers. Detectors named for retired stages (e.g., `'context_assembly'` anomaly) need updating; grep finds 1 such (assembler line 205).
- Top-of-file comment to add: `// Realigned for new pipeline 2026-05-12 (Gate II W6).`

### QueryDNAPanel (`platform/src/components/trace/QueryDNAPanel.tsx`)

- Imports `TraceStep, TraceQueryPlan, TraceToolCallSpec` from `@/lib/trace/types`. Already on the new schema.
- Spot-check expected: render is fine. Verify no `step_name === 'plan'` reads (which never fire).
- Likely no realignment needed; confirm in W6 read-pass.

### RetrievalScorecard (`platform/src/components/trace/RetrievalScorecard.tsx`)

- Imports `TraceStep, TraceChunkItem` from `@/lib/trace/types`. Already on the new schema.
- Brief requires per-sub-tool variance visible (4-tool breakdown). Reality: many tools (~20). Render full per-tool breakdown — not an aggregate. Verify in W6.

---

## §G — SSE event payload audit

| Event type | Emitter writes | Client expects (`useTraceStream`) | Match? |
|---|---|---|---|
| `step_start` | yes — step row with status='running' | yes (status check) | ✅ |
| `step_done` | yes — step row with status='done' | yes | ✅ |
| `step_error` | yes — step row with status='error' | yes | ✅ |
| `done` | yes — sentinel, no step | yes (terminates) | ✅ |
| `planning_start` | declared in types.ts:164 + TraceEvent union, but **NOT emitted by route.ts** | likely no-op handler — verify | ⚠ Declared, never fired. Renderers should not depend on it. |
| `planning_done` | declared in types.ts:171 + TraceEvent union, **NOT emitted by route.ts** | likely no-op | ⚠ Same. |

`stream/[queryId]/route.ts` replays historical steps then subscribes to the in-process emitter. The replay loop synthesizes `step_done` for every persisted step (line 53, 90). Live mode forwards whatever the emitter yields. There is no `audit` SSE event type — Audit data is not on the stream at all (§J.2).

**W7 hardening:** add `satisfies TraceEvent` in the stream encoder; add `satisfies AssembledTrace` in the admin endpoint return. Both are currently untyped through `JSON.stringify` / `NextResponse.json` calls — drift would not be caught at compile time.

---

## §H — Recommended migration 045 disposition: **NO**

W1 finds zero database schema changes required for trace alignment.

- All renderer realignments are TypeScript-only — they consume the existing `query_trace_steps` rows via a new projection in `trace_assembler.ts`.
- The legacy tables (`llm_call_log`, `tool_execution_log`, etc.) remain populated by some emitters (e.g., `pipeline_planner.ts` writes to both `llm_call_log` and `query_trace_steps`); we do not need to drop them.
- No enum value rename is required at the DB layer; `classify → planner` is a renderer-side projection.
- No new columns are required: `query_trace_steps.payload` is `jsonb` and already accommodates the planner/audit/checkpoint shapes via the `TracePayload` type.

**Migration slot 045 is reserved-unused for Gate II.** Per W9 + §4.5 R4, the slot stays empty; no `.sql` file authored. Rationale documented in W9 commit.

If Gate IV or a follow-up needs schema-level work for Audit (§J.2) or checkpoint emission, that work uses slot 047+ (Gate II's reservation is single-slot).

---

## §I — Open questions / autonomous resolutions

| # | Ambiguity | §4.5 rule | Resolution applied in W2–W9 |
|---|---|---|---|
| I.1 | Brief's D5 names 4 sub-tools (`vector_search`, `cgm_graph_walk`, `structured_sql`, `hybrid_rank`); reality emits ~20 named tools and no `structured_sql` / `hybrid_rank` literals. | R2 (emitter behavior differs from brief) | `RetrievalSubToolRun[]` typed as `string` tool_name, not a 4-literal enum. Renderer shows all tools that fired. |
| I.2 | Brief's D6 names a `mode: 'single_model' \| 'panel'` discriminant on synthesis; emitter writes no such field. | R1 (ambiguous synthesis mode discriminant → default `single_model`) | Detect from presence of `panel_opt_in` in message metadata or absence of panelist rows; default `single_model`. |
| I.3 | Audit data lives in `audit_events`, not `query_trace_steps`; trace stream has no audit event type. | R2 | Renderer renders Audit node as **placeholder** with `status: 'pending'` + an inline note `audit data lives in audit_events; surface deferred`. Document in §J.2 for native review. |
| I.4 | Checkpoints emit no trace steps at all. | D1 (always-visible) + R1 | Render `Checkpoints · 0 of 3 ran` dimmed; each checkpoint inside the group shows `disabled` badge keyed off `CHECKPOINT_*_ENABLED` flag (read server-side once and surfaced via a future field in AssembledTrace; for now, hard-code dimmed). |
| I.5 | `step_name === 'classify'` is the actual planner step but legacy renderers treat it as classifier. | R1 (partially-renamed type) | `STAGE_FROM_STEP_NAME['classify'] = 'planner'`. Add `@deprecated` JSDoc on the literal-string alias. |
| I.6 | `step_name === 'plan'` is referenced by PipelineLifecycleView but never emitted. | R1 | Drop the dead branch in W3 rewrite. |
| I.7 | `compose_bundle` is a deterministic step not in D1–D8. | R2 | Render as a chip inside the Planner step-detail (Bundle summary), not a standalone lifecycle node. |
| I.8 | `context_assembly` step still emitted but is now a short-circuit marker. | R1 (preserve current renderer behavior; log warning) | Renderer does not render a top-level node. Short-circuit metadata surfaces in Synthesis step-detail under "Context assembly" subsection. Console warns once if `short_circuited !== true`. |
| I.9 | `citation_warn` / `citation_error` are emitted but have no D-decision. | R2 | Render as Audit step-detail sub-items (validator verdict + reason). |
| I.10 | OLD trace_assembler.ts has its own anomaly detectors (5 of them) keyed off retired stage names. | R1 | Rewritten in W7. Detectors operate on `AssembledTrace.grouped.*`; the `context_assembly` detector is dropped. |

---

## §J — Emitter assumptions flagged for native confirmation (§12)

### J.1 — Tool universe wider than brief assumed

Brief D5 names 4 retrieval sub-tools. The pipeline currently emits any subset of the ~20 tools registered in `CAPABILITY_MANIFEST.json`. The Retrieval grouped node will display whichever tools the planner selected for the query, not a hard-coded 4. **Confirm that this generalization is acceptable** for the trace UI; if the native wants a curated 4-tool fixed grid, a follow-up gate will be needed.

### J.2 — Audit data is not on the trace stream

`createAuditConsumer` writes to `audit_events` table directly. No `audit` step is emitted to `query_trace_steps`. The brief's W4 AuditStepDetail expects validator verdict, disclosure tier, B.10/B.11 flags, audit-event id — none of which the SSE stream carries today. **Two options:**

1. Render an Audit node placeholder this gate, with a follow-up gate to either (a) emit an `audit` trace step from `route.ts` (touches must_not_touch — likely follow-up Gate scope) or (b) extend `/api/admin/trace/[query_id]` to JOIN `audit_events` into the assembled trace.
2. Choose option (b) inside Gate II's may_touch envelope (`trace_assembler.ts` is touchable). Assembler reads `audit_events` for the query_id and includes the row in `AssembledTrace.grouped.audit`.

**Decision (autonomous, R2 + R7):** apply **option (b)** in W7 — assembler reads `audit_events` (read-only SELECT) and projects into `AuditStepMetadata`. Keep the Audit lifecycle node always-visible.

### J.3 — Checkpoints never emit

All three checkpoint modules under `lib/checkpoints/` exist as gated infrastructure (default OFF). They emit no trace steps. Per D1, render as a collapsible group with `0 of 3 ran` and dimmed treatment for each. **Confirm** that this surface is the right shape for the eventual M5+ checkpoint-on path.

### J.4 — Panel-mode synthesis has no first-class trace shape

The panel orchestrator under `lib/synthesis/panel/` emits a single `synthesis` step like single-model. There is no per-panelist `TraceStep` row in the stream. Brief D6 expects N panelist rows + an aggregator row. **The renderer cannot meet D6 without emitter changes** (panel emit is in must_not_touch territory).

**Decision (autonomous, R1 + R2):** SynthesisStepDetail discriminates on `audience_tier` / `panel_opt_in` metadata derivable from query-message metadata (`pipeline: 'v2'` payload). For panel mode it shows a single LLM-call row with an inline note "Panel-mode trace shape pending follow-up gate; per-panelist rows not yet emitted". For single_model it shows the full LLM-call row per D6.

### J.5 — Backwards compatibility note

The legacy admin trace endpoint (`/api/admin/trace/[query_id]`) and `TraceModal.tsx` are essentially DEAD CODE — TracePanel doesn't use them, only the admin page at `/admin/trace/[query_id]` does, and that page is reachable only by super_admin URL-typing. **W7 still wires the endpoint to the new AssembledTrace return shape** for completeness, but the consumer can be deleted in a follow-up gate without user-visible impact. Flag noted; no action this session.

---

## Files in scope and not-in-scope (W1 lock)

### Files to modify (W2–W9)

| File | Work item | Verb |
|---|---|---|
| `platform/src/lib/trace/types.ts` | W2 | Extend (add `PipelineStage`, `AssembledTrace`, metadata interfaces, `STAGE_FROM_STEP_NAME`) |
| `platform/src/lib/admin/trace_assembler.ts` | W7 | Rewrite to read `query_trace_steps` + `audit_events`; return `AssembledTrace`; keep deprecated `TraceDocument` projection |
| `platform/src/lib/admin/trace_client.ts` | W7 | Update return type to `AssembledTrace` |
| `platform/src/app/api/admin/trace/[query_id]/route.ts` | W7 | Add `satisfies AssembledTrace` |
| `platform/src/app/api/trace/stream/[queryId]/route.ts` | W7 | Add `satisfies TraceEvent` in encoder |
| `platform/src/components/trace/LifecycleGraph.tsx` | W3 | Rewrite per D5 + D1 |
| `platform/src/components/trace/PipelineLifecycleView.tsx` | W3 | Rewrite per D5 + D1 (Planner → Retrieval grouped → Synthesis → Audit → Checkpoints group) |
| `platform/src/components/trace/lifecycle/ClassifyNode.tsx` | W4 | **DELETE** |
| `platform/src/components/trace/lifecycle/ContextAssemblyNode.tsx` | W4 | **DELETE** |
| `platform/src/components/trace/lifecycle/PlanNode.tsx` | W4 | Rename → `PlannerNode.tsx`; render full Planner stage |
| `platform/src/components/trace/lifecycle/FetchNode.tsx` | W4 | Replace with `RetrievalGroupNode.tsx` (D5) |
| `platform/src/components/trace/lifecycle/SynthesisNode.tsx` | W4 | Update (D2: no inline latency; metadata in detail panel) |
| `platform/src/components/trace/lifecycle/AuditNode.tsx` | W4 | **NEW** |
| `platform/src/components/trace/lifecycle/CheckpointGroupNode.tsx` | W4 | **NEW** (D1) |
| `platform/src/components/trace/step_detail/ClassifyDetail.tsx` | W4 | **DELETE** |
| `platform/src/components/trace/step_detail/ContextAssemblyDetail.tsx` | W4 | **DELETE** |
| `platform/src/components/trace/step_detail/PlanDetail.tsx` | W4 | Rename → `PlannerDetail.tsx`; render full QueryPlan |
| `platform/src/components/trace/step_detail/FetchVectorDetail.tsx` | W4 | Generalize → `RetrievalDetail.tsx` (per-tool blocks via D5) |
| `platform/src/components/trace/step_detail/FetchSqlDetail.tsx` | W4 | Subsumed by `RetrievalDetail.tsx`; delete |
| `platform/src/components/trace/step_detail/FetchGcsDetail.tsx` | W4 | Subsumed; delete |
| `platform/src/components/trace/step_detail/SynthesisDetail.tsx` | W4 | Add D6 discriminated union (single_model vs panel) |
| `platform/src/components/trace/step_detail/AuditDetail.tsx` | W4 | **NEW** |
| `platform/src/components/trace/step_detail/CheckpointDetail.tsx` | W4 | **NEW** |
| `platform/src/components/trace/StepDetail.tsx` | W4 | Update registry: drop ClassifyDetail/ContextAssemblyDetail; add Audit/Checkpoint/Planner |
| `platform/src/components/trace/TracePanel.tsx` | W5 | Drawer header + QueryPlan banner per D2 + D3 |
| `platform/src/components/trace/QueryHeaderStrip.tsx` | W5 | Migrate to AssembledTrace, render total-latency pill |
| `platform/src/components/trace/HealthRail.tsx` | W6 | Realign to AssembledTrace |
| `platform/src/components/trace/QueryDNAPanel.tsx` | W6 | Spot-fix any stale references (likely no-op) |
| `platform/src/components/trace/RetrievalScorecard.tsx` | W6 | Spot-fix; ensure per-tool variance visible |
| `platform/src/components/trace/TraceModal.tsx` | W6 | Adapt to AssembledTrace |
| `platform/src/components/trace/TimingRibbon.tsx` | W6 | Adapt to AssembledTrace |
| `platform/src/components/trace/ContextAssembly.tsx` | W6 | Likely candidate for deletion — confirm no remaining consumers |
| `platform/src/components/consume/TraceDrawer.tsx` | W5 | Shell only — pass-through any new prop |
| tests under `platform/src/__tests__/lib/admin/*` and `platform/src/components/trace/__tests__/*` | W8 | New + updated |
| `platform/tests/fixtures/gate_ii_smoke_trace.json` | W8 | New (synthetic E2E fixture) |
| `platform/tests/integration/trace_pipeline_e2e.test.ts` | W8 | New |

### Files explicitly NOT modified (must_not_touch)

Per §2 scope. Confirmed read-only:

- `platform/src/components/consume/ConsumeChat.tsx`
- `platform/src/app/api/chat/consume/route.ts` (emitter — read to learn shape only)
- `platform/src/lib/synthesis/single_model_strategy.ts` (emitter)
- `platform/src/lib/pipeline/pipeline_planner.ts` (emitter)
- `platform/src/lib/checkpoints/*` (emitter modules)
- `platform/src/lib/audit/*` (audit emitter; assembler reads its output via SELECT, does not write)

---

*End of GAP_ANALYSIS — proceeding directly to W2 per brief §4.*
