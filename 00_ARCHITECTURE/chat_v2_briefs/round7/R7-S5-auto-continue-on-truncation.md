---
canonical_id: CHAT_V2_R7_S5_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S5
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_CONTINUE
authored: 2026-05-20
depends_on: []
---

## Context

R7-S5 adds a "Continue" affordance to the assistant message component so that users can recover gracefully when the synthesis LLM is cut off mid-response. The Chat V2 Big Bang (§M.17, COMPLETE 2026-05-18, sealing-merge `6c431f9`) shipped `ConsumeChatV2.tsx` as the unconditional code path; there is no legacy fallback. This session extends that file and adds one new API route. No new DB tables are required — the continuation is a fresh synthesis call with a tailored system instruction prepended.

The truncation signal is detected from the message's data parts stream. A `data-truncated` part (type `'data-truncated'`, data `{ reason: string }`) is the primary source. A heuristic fallback fires when no `data-truncated` part is present but the accumulated text does not end with sentence-terminating punctuation (`[.!?…]`) AND the `context_usage` data part indicates token consumption >= 90 % of the model's context limit.

The "Continue" button is rendered inside `V2Message()` in `ConsumeChatV2.tsx`, below the `<MessagePrimitive.Parts />` block and above the citation-gate soft-fail chip, gated on `MessagePrimitive.If assistant`. The button is only shown after streaming completes (`message.status?.type !== 'running'`) to avoid confusing users during live output.

The new API route (`/api/chat/consume/continue`) is intentionally thin: it authenticates the caller, loads the conversation, appends a continuation system instruction, and delegates to the same synthesis pipeline entry point used by the main `route.ts`. The response is streamed using the same `createUIMessageStreamResponse` pattern already established in the main consume route.

## Files in scope

Primary implementation targets:

- `platform/src/components/consume/ConsumeChatV2.tsx` — add `TruncationContinueBanner` component and wire it inside `V2Message()` after `<MessagePrimitive.Parts />`.
- `platform/src/app/api/chat/consume/continue/route.ts` — **new file**; POST handler that streams a continuation synthesis response.

Supporting reads (do not modify unless a type fix is mandatory):

- `platform/src/app/api/chat/consume/route.ts` — reference for request body shape, auth pattern, pipeline invocation, and streaming response construction.
- `platform/src/app/api/chat/consume/regenerate/route.ts` — reference for the minimal auth + DB lookup pattern used in thin consume-adjacent routes.
- `platform/src/lib/streams/data_parts.ts` — to confirm whether a `data-truncated` part helper already exists; add one if not.
- `platform/src/types/sse_events.ts` — to check whether `TruncatedEvent` is already declared; add if not.

## Files must not touch

- `platform/src/components/consume/ConsumeChat.tsx` — LOCKED decisions (sidebar default, Trace button placement); do not touch.
- `platform/src/components/chat/Composer.tsx` — LOCKED decision (fixed-size textarea); do not touch.
- `platform/src/app/api/chat/consume/route.ts` — read for reference only; do not modify the main consume route.
- `platform/src/app/api/chat/consume/regenerate/route.ts` — read for reference only; do not modify.
- `platform/src/app/api/chat/consume/resume/` — unrelated workstream; do not touch.
- `00_ARCHITECTURE/**` — governance artifacts; do not touch except to update this brief's `status` field to `COMPLETE` on successful close.
- `01_FACTS_LAYER/**` — L1 facts layer; never touch during platform sessions.
- `025_HOLISTIC_SYNTHESIS/**` — synthesis artifacts; never touch during platform sessions.

## Acceptance criteria

### AC-1 — Truncation detection

The `TruncationContinueBanner` component detects a truncated message through either of two signals (evaluated in order; first match wins):

1. **Data-part signal:** a `data-truncated` part (type `'data-truncated'`) exists in the message's `dataParts`.
2. **Heuristic signal:** no `data-truncated` part is present AND the last non-whitespace character of the accumulated text content is not in `[.!?…]` AND the `context_usage` data part (type `'data-context-usage'`) reports `tokens_used / tokens_limit >= 0.90`.

The banner is **not** shown while `message.status?.type === 'running'` (streaming in progress).

### AC-2 — Continue button UI states

The "Continue" button inside the truncation banner cycles through three states:

| State | Label | Visual |
|---|---|---|
| `idle` | "Continue" | Outline button, normal weight |
| `loading` | (spinner) | Disabled outline button with 16px Lucide `Loader2` icon animating `animate-spin` |
| `done` | "Continued" | Disabled outline button, muted color |

Button class baseline: `variant="outline"` semantics using Tailwind (`border border-zinc-600 text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 rounded px-2.5 py-1 text-xs font-medium`). Do not introduce a new UI library component — use a plain `<button>`.

### AC-3 — Click handler

On click the button:

1. Transitions to `loading` state.
2. POSTs to `/api/chat/consume/continue` with JSON body `{ conversation_id: string, last_message_id: string }`.
   - `conversation_id` is read from `ConversationIdCtx` (already threaded through the component tree per B.3 comment in the file).
   - `last_message_id` is read from `message.id` (the current assistant message's ID as stored by `assistant-ui`).
3. On HTTP 2xx: the streaming response is consumed and rendered as a new assistant message appended to the thread. The button transitions to `done` state.
4. On HTTP 4xx/5xx or network error: the button transitions back to `idle` state and a brief error toast is shown (`console.error` is acceptable if no toast infrastructure is available in scope; prefer existing toast/sonner patterns in the file if present).

The new message approach (append a fresh assistant message) is preferred over mutating the existing message's content in place.

### AC-4 — API route: happy path

`POST /api/chat/consume/continue` with a valid authenticated request body:

- Loads the conversation via `getConversation(conversation_id)`.
- Prepends the continuation system instruction to the synthesis call:
  > "Continue exactly from where the previous response was cut off. Do not repeat any content. Begin mid-sentence if needed."
- Calls the synthesis pipeline with the same model stack as the conversation's last turn (fall back to `DEFAULT_STACK_ID` if not determinable).
- Streams the response back to the client using `createUIMessageStreamResponse` with the same data-part shape as the main route.

### AC-5 — API route: error cases

- Missing `conversation_id` or `last_message_id` in body → 400 `{ error: 'conversation_id and last_message_id are required' }`.
- `getConversation` returns null → 404 `{ error: 'conversation not found' }`.
- Unauthenticated caller → 401 (via existing `getServerUser()` pattern — return `res.unauthenticated()` or equivalent `NextResponse` with status 401).

### AC-6 — Typecheck

`npm run typecheck` (run from `platform/`) exits 0 with no new errors introduced. All new code is fully typed; no `any` without an inline `// eslint-disable-line` justification.

### AC-7 — No regression on existing smoke tests

The existing R6 smoke spec at `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` must not be modified by this session. If it imports from files touched here, verify no import paths are broken.

## Pre-commit gates

Run from `platform/` unless otherwise noted. All gates must pass before the commit is created.

```
# 1. Typecheck
npm run typecheck

# 2. Lint (if configured; non-fatal if lint script absent)
npm run lint --if-present

# 3. Confirm the new route file exists
ls platform/src/app/api/chat/consume/continue/route.ts

# 4. Confirm TruncationContinueBanner is exported or used inside V2Message
grep -n "TruncationContinueBanner\|truncation-continue" \
  platform/src/components/consume/ConsumeChatV2.tsx

# 5. Confirm data-truncated part helper exists
grep -n "data-truncated\|truncatedPart" \
  platform/src/lib/streams/data_parts.ts

# 6. No modifications to locked files
git diff --name-only HEAD | grep -E \
  "ConsumeChat\.tsx$|Composer\.tsx$|consume/route\.ts$|regenerate/route\.ts$" \
  && echo "LOCKED FILE MODIFIED — abort" && exit 1 || echo "Locked files clean"
```

## Commit message template

```
feat(chat-v2/r7-s5): add Continue button for truncated assistant messages

- TruncationContinueBanner detects truncation via data-truncated part or
  heuristic (last char not sentence-ending + token usage >= 90 %)
- Button states: idle → loading (spinner) → done; error reverts to idle
- POST /api/chat/consume/continue: thin route that loads conversation,
  prepends continuation system instruction, delegates to synthesis pipeline
- Route returns 400 (missing params), 401 (unauth), 404 (no conversation)
- npm run typecheck passes; no locked files modified

R7-S5 | CHAT_V2_R7_S5_BRIEF v1.0 | branch: chat-v2/round7-polish
```
