---
artifact: PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT_v1_0
artifact_id: PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT
version: 1.0
status: COMPLETE
authored_at: 2026-04-30T00:00:00Z
verdict: B
---

# R3a Hook-Compatibility Audit

## Question 1: useChatSession + /api/chat/build

### What useChatSession sends

`useChatSession` is built on top of `@ai-sdk/react`'s `useChat` with a `DefaultChatTransport`. The
endpoint is **hardcoded** to `'/api/chat/consume'` inside the `useMemo` transport block (line 38 of
`platform/src/hooks/useChatSession.ts`):

```ts
const transport = useMemo(
  () => new DefaultChatTransport({ api: '/api/chat/consume' }),
  []
)
```

The hook has no `endpoint` parameter in its `Options` interface — it only accepts `chartId`,
`conversationId`, `initialMessages`, `onConversationCreated`, `model`, and `style`. The build
endpoint is never reachable from the hook as currently written.

### What the build route expects

`/api/chat/build` (`platform/src/app/api/chat/build/route.ts`) expects:

```json
{ "chartId": "string", "messages": ModelMessage[] }
```

It reads a raw `ModelMessage[]` array (the Vercel AI SDK's internal model-message format) directly
from `request.json()`. It returns `result.toTextStreamResponse()` — a plain text/event-stream with
raw token deltas, **not** the `UIMessageStream` protocol that `useChat` / `DefaultChatTransport`
expect.

### What the consume route returns

`/api/chat/consume` returns `result.toUIMessageStreamResponse(...)` — the structured UI-message
stream protocol that `DefaultChatTransport` is designed to consume. It also embeds `messageMetadata`
callbacks that inject `conversationId`, `queryId`, `model`, `style`, and `pipeline` into the
stream's `start` part, which `useChatSession` reads via `message.metadata` in the `onFinish`
callback.

### Gap summary

Three incompatibilities:

1. **Endpoint is hardcoded** — the transport URL must be parameterised.
2. **Request body shape mismatch** — `useChat` sends `UIMessage[]` (the current chat history) plus
   an `extraBody` object carrying `chartId`, `conversationId`, `model`, `style`. The build route
   expects `{ chartId, messages: ModelMessage[] }` (raw model messages). The AI SDK internally
   converts UIMessage → ModelMessage before sending when using `DefaultChatTransport`; however the
   build route never receives nor uses `conversationId`, `model`, or `style` from the body, which is
   fine for build — but the SDK still sends the UIMessage wire format unless transport is overridden.
   In practice `DefaultChatTransport` sends the SDK's standard chat request body (messages as
   UIMessage[], plus extraBody fields merged at top level), so `chartId` will arrive correctly as a
   top-level field. However the build route also requires `messages` as a `ModelMessage[]`; the SDK
   sends them as the SDK's internal representation which the route casts as `ModelMessage[]`. This is
   likely to work at runtime, but is worth verifying — it is not a blocking gap.
3. **Response stream format mismatch** — **this is the blocking gap.** The build route returns
   `result.toTextStreamResponse()` (plain text delta stream), whereas `DefaultChatTransport` expects
   the structured UI-message stream protocol (`data:` prefixed SSE lines with typed parts). The hook
   will receive unparseable data and the message state will never update correctly.

### Verdict for Q1

**Incompatible as-is.** Two changes are required: (a) the transport URL must be made a parameter;
(b) the build route must return `toUIMessageStreamResponse(...)` instead of
`toTextStreamResponse()`. Item (b) is a one-line change on the route side; item (a) is a small
adapter or a hook parameter addition.

---

## Question 2: useBranches + build conversation model

`useBranches` (`platform/src/hooks/useBranches.ts`) has a single external dependency: a
`conversationId: string | undefined` prop that it uses only to reset its internal branch state when
the conversation switches. It stores all branch data in React local state (`Record<string,
UIMessage[][]>`). It never reads from or writes to any server endpoint, database field, or
conversation-specific metadata beyond using `conversationId` as a cache-busting key.

The hook operates entirely on the `UIMessage[]` array that the caller passes in (`session.messages`
from `useChatSession`) and archives snapshots locally. It has no dependency on Consume-specific
metadata such as `queryId`, `pipeline`, `disclosure_tier`, or any field in the `message.metadata`
payload.

### Verdict for Q2

**Fully compatible.** `useBranches` is conversation-model-agnostic. It will work with the build
conversation ID (or even `undefined` for a stateless build session) without any changes.

---

## Question 3: useFeedback + build response stream

`useFeedback` (`platform/src/hooks/useFeedback.ts`) depends on:

1. A `conversationId: string | undefined` parameter.
2. The REST endpoint `GET /api/conversations/{id}/feedback` to load existing ratings on mount.
3. The REST endpoint `POST /api/conversations/{id}/feedback` with body `{ messageId, rating }` to
   submit ratings.

The feedback route (`platform/src/app/api/conversations/[id]/feedback/route.ts`) resolves the
conversation via `getConversation()`, which queries the `conversations` table for any row with the
given `id` — it does **not** filter by `module`. A build conversation persisted into the
`conversations` table with `module='build'` would be fully accessible via the feedback endpoint.

The hook does not inspect the message objects themselves — it only uses `messageId` (a string that
the caller supplies when calling `rate(messageId, rating)`). It has no dependency on the response
stream format or any message metadata produced by the pipeline.

### Single blocking precondition

The build route currently does **not** persist conversations. It reads chart data and streams a
response but never calls `insertConversationWithId` or `replaceConversationMessages`. Because there
is no `conversations` row, `getConversation()` returns `null` and the feedback endpoint returns 404
for any build `conversationId`. Feedback will silently revert on the optimistic update.

This is not a hook bug — it is a route-level persistence gap that must be closed before feedback
will function end-to-end.

### Verdict for Q3

**Conditionally compatible.** The hook itself is build-agnostic. It will work correctly once the
build route persists its conversations (and therefore generates a stable `conversationId` to pass
back to the client). No changes to the hook are required. The route must be upgraded as part of R3
work regardless (to support `onConversationCreated` / returning `conversationId` in stream
metadata).

---

## Synthesis verdict

**Verdict: B — Thin adapter (≤ 80 lines)**

The three hooks are architecturally compatible with the build conversation model. The blocking gaps
are:

1. `useChatSession` has the consume endpoint hardcoded. An adapter (or a new optional `endpoint`
   parameter) is needed to point it at `/api/chat/build`.
2. `/api/chat/build` returns `toTextStreamResponse()` instead of `toUIMessageStreamResponse()`. This
   is a one-line change in the route, but it also requires the route to emit `conversationId` in the
   stream metadata (so `useChatSession.onFinish` can fire `onConversationCreated`) and to persist
   the conversation + messages (so `useFeedback` has a valid row to query).
3. None of these gaps require structural rework of the hooks themselves.

The adapter's job is therefore narrow: parameterise the transport endpoint and optionally wrap the
hook call signature so callers do not need to know that the URL is different. The route-side changes
(stream format + persistence) are the majority of the R3 implementation work but are changes to
`/api/chat/build/route.ts`, not to the hooks.

---

## Adapter spec (verdict B)

**File:** `platform/src/hooks/useBuildChatAdapter.ts`

The adapter is a thin re-export of `useChatSession` with the transport URL overridden to
`/api/chat/build` and a narrowed option surface appropriate for Build mode (no `style` parameter;
no `currentQueryId` in the return since Build does not use the trace panel).

```typescript
// platform/src/hooks/useBuildChatAdapter.ts
'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport, type UIMessage } from 'ai'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

interface BuildChatOptions {
  chartId: string
  conversationId?: string
  initialMessages?: UIMessage[]
  onConversationCreated?: (id: string) => void
}

export function useBuildChat({
  chartId,
  conversationId,
  initialMessages,
  onConversationCreated,
}: BuildChatOptions) {
  const [persistedId, setPersistedId] = useState<string | undefined>(conversationId)

  useEffect(() => {
    if (conversationId) setPersistedId(conversationId)
  }, [conversationId])

  // TRANSLATION RULE 1: point transport at the build endpoint, not consume.
  const transport = useMemo(
    () => new DefaultChatTransport({ api: '/api/chat/build' }),
    []
  )

  const chat = useChat({
    id: conversationId ?? 'new',
    messages: initialMessages,
    transport,
    onFinish: ({ message }) => {
      // TRANSLATION RULE 2: extract conversationId from stream metadata.
      // Requires /api/chat/build to emit { conversationId } in the 'start' part
      // metadata via toUIMessageStreamResponse({ messageMetadata }).
      const metadata = message.metadata as { conversationId?: string } | undefined
      const newId = metadata?.conversationId
      if (newId && newId !== persistedId) {
        setPersistedId(newId)
        onConversationCreated?.(newId)
      }
    },
  })

  const isStreaming = chat.status === 'streaming' || chat.status === 'submitted'
  const canSend = chat.status === 'ready' || chat.status === 'error'

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isStreaming) return
      // TRANSLATION RULE 3: body carries chartId + conversationId only.
      // Build route does not use model/style; omit them to keep the contract clean.
      chat.sendMessage(
        { text: trimmed },
        { body: { chartId, conversationId: persistedId } }
      )
    },
    [chat, isStreaming, chartId, persistedId]
  )

  const regenerate = useCallback(() => {
    chat.regenerate({ body: { chartId, conversationId: persistedId } })
  }, [chat, chartId, persistedId])

  return {
    messages: chat.messages,
    status: chat.status,
    error: chat.error,
    isStreaming,
    canSend,
    send,
    stop: chat.stop,
    regenerate,
    setMessages: chat.setMessages,
    conversationId: persistedId,
  }
}
```

**Route-side changes required to make the adapter functional (not in the adapter file itself):**

1. Change `result.toTextStreamResponse()` → `result.toUIMessageStreamResponse({ ... })` in
   `/api/chat/build/route.ts`.
2. Add `insertConversationWithId` + `replaceConversationMessages` calls (mirror the pattern in the
   consume route) so a `conversations` row exists for feedback and branch navigation.
3. Inject `{ conversationId }` in the `messageMetadata` callback on the `start` part (first-turn
   only), matching the consume pattern.

These three route changes plus the ~55-line adapter above constitute the complete R3 surface area.
Total adapter is 55 lines; total new code including route edits is well under 150 lines. Adapter
alone is under 80 lines (verdict B confirmed).

---

## Split rationale (if verdict C)

Not applicable — verdict is B.
