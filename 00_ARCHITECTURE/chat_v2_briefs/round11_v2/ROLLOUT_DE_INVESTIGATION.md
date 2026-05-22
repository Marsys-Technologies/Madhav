---
artifact: ROLLOUT_DE_INVESTIGATION.md
version: "1.0"
status: COMPLETE
captured: 2026-05-23
method: Chrome DevTools live browser test + Cloud Run log analysis + source code trace
---

# R11.D Rollout — Root Cause Investigation

## Investigation summary

**D.1 and D.2 are NOT the root cause of the errors.**

The errors originate from pre-existing bugs in the adapter dispatch wiring at `route.ts:917–928`, present since commit `77205869` (dispatch wiring). These bugs would fire on any query through any provider adapter, regardless of which D.* flags are set. D.1 and D.2 are additionally confirmed to be **no-ops** in the current code (the `prompt_assembler.ts` utility they depend on is not called from `route.ts`).

## Live browser test — evidence

### Test setup
- Page: `/consume` on prod rev `amjis-web-00345-hk6` (clean baseline: only `USE_ADAPTERS=true`)
- Multi-Provider Parity: toggled ON
- Stack: Anthropic Stack (Opus 4.7)
- Query (first message, new conversation): `"What is the current Vimshottari dasha period for this native?"`

### Observed response stream (reqid=88)
```
data: {"type":"start","messageId":"msg-FzPn83oK29hp2knT"}
data: {"type":"data-stage","data":{"stage":"classify","status":"done","ms":5174}}
data: {"type":"data-stage","data":{"stage":"compose_bundle","status":"done","ms":18}}
data: {"type":"data-tool","data":{"name":"cgm_graph_walk","status":"done","ms":14}}
data: {"type":"data-tool","data":{"name":"msr_sql","status":"done","ms":269}}
data: {"type":"data-stage","data":{"stage":"tool_fetch","status":"done","ms":269}}
data: {"type":"data-stage","data":{"stage":"synthesis","status":"running"}}
data: {"type":"data-stage","data":{"stage":"synthesis","status":"done","ms":96}}
data: {"type":"data-observability","data":{...}}
data: [DONE]
```

**Synthesis: 96ms — impossible for a real Anthropic LLM call (minimum ~800ms). Zero text-delta events. Confirms silent error path.**

### UI state after query
- No assistant text rendered in message thread
- "Copy response" button disabled
- No console errors (error caught server-side)

### Cloud Run log confirmation
```
2026-05-22T20:09:45.266230Z Error [AI_InvalidPromptError]: Invalid prompt: messages must not be empty
```

## Root cause — three bugs in route.ts:917–928

### Bug A — Missing current user turn (PRIMARY, confirmed)

**File:** `platform/src/app/api/chat/consume/route.ts` lines 917–928

```typescript
// CURRENT (broken)
const adapterMessages: ChatMessage[] = trimmedConversationHistory.map(m => ({
  role: m.role as ChatMessage['role'],
  content: ...,
}))
const adapterChatReq: ChatRequest = { messages: adapterMessages, model: modelId }
```

`trimmedConversationHistory` is the **prior conversation history** — it does NOT include the current user turn (`queryText`). On the first message of any new conversation, `trimmedConversationHistory = []`, so `adapterMessages = []`.

Vercel AI SDK `streamText({ messages: [] })` → `AI_InvalidPromptError: messages must not be empty`.

**Fix:** Append `{ role: 'user', content: queryText }` after mapping history turns.

```typescript
// FIXED
const adapterMessages: ChatMessage[] = [
  ...trimmedConversationHistory.map(m => ({ ... })),
  { role: 'user' as const, content: queryText },
]
```

### Bug B — Empty string from non-text content parts (SECONDARY)

**File:** `route.ts:919–925`

```typescript
content: Array.isArray(m.content)
  ? m.content
      .map((p: unknown) => {
        const part = p as { type?: string; text?: string }
        return part.type === 'text' ? (part.text ?? '') : ''  // ← non-text → ''
      })
      .join('')   // ← if all parts are non-text: content = ''
  : ((m.content as string) ?? ''),
```

When a history message has array content where all parts are non-text (e.g., tool_result parts), `content` becomes `''` (empty string). Anthropic API rejects any message with `type: "text", text: ""` → HTTP 400 `messages: text content blocks must be non-empty`.

This explains the `AI_APICallError` from the operator's D.2 test: those queries hit an existing conversation with prior tool-result history.

**Fix:** Filter out empty-string results before joining, and skip messages that produce empty content.

```typescript
content: Array.isArray(m.content)
  ? m.content
      .map((p: unknown) => {
        const part = p as { type?: string; text?: string }
        return part.type === 'text' ? (part.text ?? '') : ''
      })
      .filter(Boolean)  // drop empty strings
      .join('\n') || '[tool result]'  // fallback if all non-text
  : ((m.content as string) ?? ''),
```

### Bug C — Missing system prompt (FUNCTIONAL — no crash, wrong output)

**File:** `route.ts:928`

```typescript
const adapterChatReq: ChatRequest = { messages: adapterMessages, model: modelId }
// Missing: system (synthesis prompt + RAG bundle)
```

The synthesis system prompt, RAG bundle (tools output), query plan, and disclosure tier are assembled into `synthContent` but never passed to `adapterChatReq`. The adapter makes a real LLM call without any astrological context — it would produce generic responses, not Madhav-calibrated answers.

**Fix:** Pass the assembled system content:
```typescript
const adapterChatReq: ChatRequest = {
  messages: adapterMessages,
  model: modelId,
  system: synthContent,  // the assembled synthesis prompt
}
```

## D.1 and D.2 flag assessment

### D.1 — MARSYS_FLAG_R11D_PROMPT_LAYOUT

**Status: NO-OP in current deployment.**

The `prompt_assembler.ts` utility (`assembleWithCacheBreakpoints`) is fully implemented in `platform/src/lib/synthesis/prompt_assembler.ts` but is **never called from `route.ts`**. The D.1 flag is declared in `feature_flags.ts` and has no code path that reads it in the synthesis or adapter dispatch layers.

**Implication:** D.1 can be re-flipped true with zero effect. It will remain a no-op until `assembleWithCacheBreakpoints` is wired into the route.

### D.2 — MARSYS_FLAG_R11D_ANTHROPIC_CACHE

**Status: NO-OP in current deployment.**

Same analysis. The `cache()` method on `AnthropicAdapter` returns a `CacheResponse` with the correct `cacheControl` config — but the route never calls `adapter.cache()`, never passes the cache config to `prompt_assembler`, and never calls `assembleWithCacheBreakpoints`. The D.2 flag has no code path that reads it.

**Implication:** D.2 can be re-flipped true with zero effect. Cache breakpoints will not be injected until the assembler wiring is complete.

## Error attribution table

| Error | Revision | Root cause | D.1/D.2 involved? |
|---|---|---|---|
| `AI_InvalidPromptError: messages must not be empty` | 00343, 00345 | Bug A — missing current user turn | No |
| `AI_APICallError: messages: text content blocks must be non-empty` | 00343 | Bug B — non-text parts → `''` | No |
| Empty 96ms synthesis response | 00345 (current test) | Bug A caught silently | No |

## Current Cloud Run state (post-investigation)

| Flag | Value | Revision |
|---|---|---|
| MARSYS_FLAG_R11V2_USE_ADAPTERS | true | 00345 |
| MARSYS_FLAG_R11D_PROMPT_LAYOUT | false | 00345 (rolled back) |
| MARSYS_FLAG_R11D_ANTHROPIC_CACHE | false | 00345 (rolled back) |
| All D.3 / E.* flags | false | 00345 |

## Fix path

All three bugs are in `platform/src/app/api/chat/consume/route.ts` lines 917–928. No other files require changes.

Bug A fix (required before any useful adapter query): ~3 lines.
Bug B fix (required for multi-turn conversations): ~3 lines.
Bug C fix (required for contextually correct answers): pass `synthContent` to `adapterChatReq.system`.

Full integration of D.1/D.2 (assembler wiring) requires additionally:
- Call `assembleWithCacheBreakpoints(sections, cacheEnabled)` to build `adapterMessages` instead of the raw history map
- Gate with `configService.getFlag('R11D_PROMPT_LAYOUT')` and `configService.getFlag('R11D_ANTHROPIC_CACHE')`

**Estimated fix scope:** 20–40 lines in `route.ts`. No schema changes. No migration. The `prompt_assembler.ts` implementation is correct and ready to be wired.

*ROLLOUT_DE_INVESTIGATION.md — authored 2026-05-23 via Chrome DevTools live test + log analysis + source trace.*
