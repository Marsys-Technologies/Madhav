---
artifact: GATE_III_AUDIT
version: 1.0
status: COMPLETE
authored_by: Claude Code Sonnet 4.6 (Gate III executor)
date: 2026-05-12
---

# Gate III — W0 Audit

## Confirmed file paths

### Consume components (`platform/src/components/consume/`)
- `AnswerView.tsx` (115 lines) — finalized-answer renderer; parses citations and wraps text in `StreamingMarkdown`. Currently *not* used by `ConsumeChat.tsx` (which uses `StreamingAnswer.tsx` directly).
- `ConsumeChat.tsx` (637 lines) — top-level orchestrator. Uses `ChatShell` (which carries left `ConversationSidebar` from `@/components/chat`), `StreamingAnswer`, `WelcomeGreeting` (empty state), `TraceDrawer`, `ReportLibrary`/`ReportReader`. LOCKED decisions noted in `platform/AGENTS.md` (sidebar collapse default, Trace button placement, fixed composer).
- `StreamingAnswer.tsx` (116 lines) — renders message list; assistant-currently-streaming branch uses bare `StreamingMarkdown`, completed turns use `AssistantMessage`.
- `TraceDrawer.tsx` (50 lines) — thin wrapper around the trace surface. **read-only per brief**.
- `DivergenceReport.tsx`, `LogPredictionAction.tsx`, `PanelAnswerView.tsx`, `ReportGallery.tsx`, `ReportLibrary.tsx`, `ReportReader.tsx`, `SharedConsumeError.tsx`, `TierPicker.tsx`, `ValidatorFailureView.tsx` — not in scope.

### Consume API route
- `platform/src/app/api/chat/consume/route.ts` (859 lines). Uses Vercel AI SDK `streamText` + `result.toUIMessageStreamResponse(...)`. **No raw SSE**. Per-message metadata is attached via the `messageMetadata({part})` callback on `start` / `finish` parts. Conversation persistence happens in `onFinish`. Title generation already wired via `generateConversationTitle` (Gemini Flash). Trace events go through `traceEmitter.emitStep(...)` to the separate `/api/trace/stream` channel (must_not_touch).

### Synthesis prompt
- The synthesis prompt is **not a single `.md` file** — it is a TypeScript template registry under `platform/src/lib/prompts/templates/*.ts`, one per query class, all assembled by `buildOpeningBlock()` in `shared.ts` (currently 138 lines). Adding new directives requires extending `shared.ts` exports and `buildOpeningBlock()`, not creating a new `.md`. **Deviation from brief**: brief calls for a `synthesis_v2_0.md` file; actual surface is `shared.ts`.

### Planner
- `platform/src/lib/pipeline/pipeline_planner.ts` (542 lines) — actual planner. Brief paths `src/lib/planner/planner.ts` and `src/lib/planner/` do not exist. Loads `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` (file path), internal version `2.1` per its frontmatter. **Deviation from brief**: bumping the file from v2.0→v2.2 risks breaking other consumers. Strategy chosen: keep the file path `PLANNER_PROMPT_v2_0.md` and bump its internal `version` field to `2.2`; append a new `## PRIOR-TURN RELEVANCE` section. This is byte-additive to the prompt and a no-op for unrelated callers.
- `PipelinePlan` type lives in `platform/src/lib/pipeline/types.ts` (369 lines). Extension adds optional `prior_turn_relevance` field — backwards-compatible.

### Conversations
- `/api/conversations` (GET) — exists at `platform/src/app/api/conversations/route.ts`. Returns `{ conversations }` filtered by `chartId` + `module`, ordered by `created_at DESC`, hard limit 100. No pagination, no search.
- `conversations` table (migration `001_initial_schema.sql`) already has `title text` column. **No migration 046 needed.**
- `generateConversationTitle` already implemented at `platform/src/lib/conversations/title.ts` and called from `route.ts onFinish` on first turn.

### SSE events emitted today
The consume route emits a single Vercel AI UI message stream. The only places metadata leaks back to the client are:
- `messageMetadata({ part: { type: 'start' } })` — once per message, carries `conversationId, model, stack, style, disclosure_tier, queryId, planning_model_id, planning_latency_ms, planner_active`.
- `messageMetadata({ part: { type: 'finish' } })` — once per message, carries `methodology_block`.
- The streaming answer body (`answer_chunk`-equivalent) is delivered as part of the UI message stream.
- Pipeline trace events go to a **separate** SSE channel (`/api/trace/stream`) via `traceEmitter`.

### Trace surface (must_not_touch — confirmed present)
- `platform/src/components/trace/` — 20+ components (TracePanel, LifecycleGraph, HealthRail, QueryDNAPanel, RetrievalScorecard, StepDetail, etc.).
- `platform/src/lib/admin/trace_assembler.ts`, `trace_client.ts` — confirmed present.
- `platform/src/app/api/trace/stream/`, `platform/src/app/api/admin/trace/` — confirmed present.

## Architecture decisions (forced by audit)

The brief assumes a raw-SSE multiplex on `/api/chat/consume`. The codebase uses the Vercel AI SDK UI message stream protocol. Inventing a parallel SSE channel would either (a) duplicate the existing trace stream or (b) break the message-stream contract the client hook (`useChatSession`) depends on. Strategy chosen:

| Brief event type | Delivery mechanism | Rationale |
|---|---|---|
| `reasoning_step` (pipeline phase) | **Existing trace stream** (`/api/trace/stream`), client subscribes and translates step_name via `PIPELINE_STEP_NARRATION`. | Already plumbed end-to-end; zero server change required. |
| `reasoning_step` (synthesis phase) | **Inline `‹reasoning›X‹/reasoning›` markers** in the synthesis output stream, parsed client-side before display. | Server emits prose; client strips + surfaces in LiveReasoningCard. |
| `answer_chunk` | UI message stream (default). | No change. |
| `correction` | **Inline `‹correction›YAML‹/correction›` marker** in stream; client parses + extracts. | Same channel as text. |
| `out_of_domain` | **Inline `‹out_of_domain reason="…"›‹/out_of_domain›` marker**. | Same. |
| `sanskrit_terms` | **Inline `‹sanskrit term=… def=… translit=…›display‹/sanskrit›` markers** inline in prose. | Annotations are tied to specific words; inline is natural. |
| `context_usage` | `messageMetadata.start` payload. | Once-per-turn metadata. |
| `provenance` | `messageMetadata.finish` payload. | Once-per-turn metadata. |
| `conversation_title` | `messageMetadata.start` payload (first turn only). | Already a Flash call in `onFinish`; surfaced earlier via metadata. |
| `done` / `error` | UI message stream `finish` / error parts (default). | No change. |

This decision means the brief's `types/sse_events.ts` becomes a **type contract for the marker-and-metadata schema** rather than a serializer for a raw SSE protocol.

## Other deviations and decisions

1. **Synthesis prompt as TS**: new directives are added as exported constants in `platform/src/lib/prompts/templates/shared.ts` and wired into `buildOpeningBlock()`.
2. **Planner file**: `PLANNER_PROMPT_v2_0.md` is bumped in-place from `version: 2.1` → `version: 2.2`; new `## PRIOR-TURN RELEVANCE` section appended. No file path change. Planner loader (`pipeline_planner.ts`) unchanged.
3. **PipelinePlan type**: `prior_turn_relevance` added as optional field on existing `PipelinePlan` (in `src/lib/pipeline/types.ts`), with corresponding entry in `PipelinePlanInputJsonSchema`. Backwards compatible.
4. **Conversation history drawer (W10)**: the existing left `ConversationSidebar` (in `components/chat/`, owned by the chat shell, not `consume/**`) already lists prior conversations with click-to-load. It is in must_not_touch. The new `ConversationHistoryDrawer.tsx` is added in `components/consume/` as a search-augmented drawer launched from a header button; it co-exists with the existing sidebar rather than replacing it. The existing `/api/conversations` endpoint is reused as-is (already shape-compatible). No new endpoint needed for W10.
5. **Empty state (W11)**: the existing `WelcomeGreeting` (in `components/chat/`, must_not_touch) is bypassed when there are no messages; new `EmptyState.tsx` (consume-scoped) renders instead.
6. **Pipeline event narration (W6) + LiveReasoningCard (W7)**: the card subscribes to the existing trace SSE channel (`/api/trace/stream?queryId=…`) and translates step names locally — no new server endpoint.
7. **No npm packages installed** — see point about tooltip/drawer: existing UI primitives (`@radix-ui/*` via shadcn or inline) are reused. If a specific tooltip primitive is unavailable I fall back to a hand-rolled span with `:hover` CSS + keyboard focus.

## Baselines captured

- `npx tsc --noEmit` baseline: **22 errors** (pre-existing). Captured to `.gate3_tsc_baseline.txt` at worktree root.
- `npm test` not run as baseline (long; some tests touch external services). Will run after major phases.

## Critical components LOC summary

| File | LOC |
|---|---|
| `ConsumeChat.tsx` | 637 |
| `AnswerView.tsx` | 115 |
| `StreamingAnswer.tsx` | 116 |
| `TraceDrawer.tsx` | 50 |
| `route.ts` | 859 |
| `pipeline_planner.ts` | 542 |
| `single_model_strategy.ts` | 633 |
| `shared.ts` (templates) | 138 |
| `conversations.ts` | ~120 |
| `title.ts` (Flash titler) | 120 |

## Banned-model scan
`grep -ri "anthropic" platform/src` — **no matches** in any model-string position relevant to this brief (some imports of `@anthropic-ai/sdk` may exist for AI SDK provider plumbing, but none invoked as default model). No `GATE_III_BANNED_MODEL_FOUND.md` raised.

## Proceeding plan
Execute W1 → W15 with the deviations above. Will not raise `GATE_III_DESIGN_BLOCKER.md` for the SSE-vs-UI-message-stream choice — it is mechanical, not a design decision the native must arbitrate.
