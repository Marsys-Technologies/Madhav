---
canonical_id: R11_S_S4
version: 1.0
status: CURRENT
session_id: S-S4
title: Inline tool cards — labeled mid-stream cards for tool_use blocks
depends_on: ["S-S3"]
blocked_on: []
flag: MARSYS_FLAG_R11_TOOL_CARDS
flag_default: true
client_side: "yes — NEXT_PUBLIC, new render path inside MarkdownContent / message parts"
authored: 2026-05-21
---

# S-S4 — Inline Tool Cards

## Context

When Claude invokes a tool (web_search, web_fetch, code_execution, file_read), Claude.ai renders a labeled card inline in the message: icon + verb ("Searched the web", "Read file", "Ran code") + progressively-revealed input as `input_json_delta` partials accumulate. The card stays visible after completion as an audit trail.

Chat V2 emits `data-tool` SSE events from `/api/chat/consume/route.ts` but the rendering of inline cards mid-stream is minimal. This session adds a `<InlineToolCard />` component that renders any tool_use block as a labeled card with progressive input reveal.

## Files in Scope

- `platform/src/components/chat/InlineToolCard.tsx` (new) — props: `{ name: string, status: 'invoking'|'streaming-input'|'complete', input: object|null, result?: object|null }`. Renders icon + verb (mapped from name), input preview, status indicator.
- `platform/src/components/chat/AssistantMessage.tsx` — when rendering message parts, intersperse `<InlineToolCard />` for each `data-tool` part in stream order (not all-at-end).
- `platform/src/lib/chat-v2/useDataParts.ts` — confirm `data-tool` parts retain stream-position ordering so they can be interleaved with text parts.
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_TOOL_CARDS` (default true, NEXT_PUBLIC).
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11_TOOL_CARDS` (Amendment 1).
- `platform/tests/` — integration test.

## Files Must NOT Touch

- The SSE event shape on the server
- Synthesis prompt (no prompt change required)
- Phase 4C files

## Acceptance Criteria

1. **Flag client-side + deploy.yml (Amendment 1):** `NEXT_PUBLIC_MARSYS_FLAG_R11_TOOL_CARDS` in both `feature_flags.ts` and `deploy.yml --build-arg`. Coverage check passes.
2. **Tool-to-verb mapping:** `query_panchanga` → "Looked up panchang", `search_signals` → "Searched signals", `fetch_chunks` → "Read sources", `query_observatory_metrics` → "Pulled cost data", etc. Mapping documented in InlineToolCard.tsx comments.
3. **Progressive input reveal:** as `data-tool` part's `input` field grows (partial JSON), the card body updates progressively. On `status: complete`, full input + result preview shown.
4. **Stream-order interleaving:** if route.ts emits text_part_A → tool_part_1 → text_part_B → tool_part_2 → text_part_C, the UI renders the same vertical order. Document a test asserting this.
5. **Click-path (Amendment 2):** send a query that triggers a tool call (e.g., panchang query) → labeled tool card appears between text segments → card shows progressive input → card finalizes with result preview.
6. **Parent-context integration test (Amendment 2):** mount ConsumeChatV2, feed seeded data-parts with interleaved text+tool parts, assert vertical order matches part order.
7. **Flag guard:** with flag=false, tool parts render the way they do today (no regression).

## Pre-commit Gates

```bash
test -f platform/src/components/chat/InlineToolCard.tsx && echo "PASS"
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11_TOOL_CARDS" .github/workflows/deploy.yml && echo "PASS: deploy.yml"
grep -n "data-tool\|InlineToolCard" platform/src/components/chat/AssistantMessage.tsx
npx jest --testPathPattern="InlineToolCard|S-S4|tool-card" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): inline tool cards mid-stream

InlineToolCard renders each data-tool part as a labeled icon+verb card with
progressive input reveal and result preview. Stream-order interleaved with
text parts. Guarded by MARSYS_FLAG_R11_TOOL_CARDS=true (NEXT_PUBLIC; deploy.yml
--build-arg added).

Click-path: query triggers tool → labeled card appears between text segments.
```

## Decision Log

*(Executor: paste tool-name → verb mapping table chosen.)*
