---
canonical_id: CHAT_V2_R9_S4_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R9
session_id: R9-S4
owner: chat-v2/round9-elevation worktree
branch: chat-v2/round9-elevation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR9
flag_namespace: MARSYS_FLAG_R9_TOOL_FLOW
authored: 2026-05-20
depends_on: []
---

## Context

R9-S4 surfaces the planner-stages + tool-fetch visualization that currently lives only on the `/audit/[query_id]` admin page, and inlines it directly inside each `AssistantMessage` in the chat UI. The disclosure is collapsed by default so it adds zero visual noise for normal reading; super-admin and admin users can expand it to see the full query execution timeline without leaving the chat.

The data source is `query_trace_steps` (already populated by the pipeline and exposed on the audit page). R9-S4 adds a thin API wrapper at `GET /api/audit/[queryId]/trace` if one does not already exist, a new `InlineToolFlow` component, and a single integration point in `AssistantMessage.tsx`. The whole surface is gated behind `MARSYS_FLAG_R9_TOOL_FLOW`.

---

## Files in scope

### New files
- `platform/src/components/chat/InlineToolFlow.tsx`
  - Props: `{ queryId: string | null; isAdmin: boolean }`
  - Renders nothing when `queryId` is null, `isAdmin` is false, or `MARSYS_FLAG_R9_TOOL_FLOW` is false
  - Collapsed by default: shows a small "View tool flow ▸" disclosure button below the assistant message content area
  - On expand: fetches `GET /api/audit/[queryId]/trace` and renders a compact vertical timeline
    - Each step row: icon (tool emoji or stage icon) + stage name + duration (ms) + status indicator (✓ / ✗ / ⏳)
    - Final synthesizer step shown in full with its model name + token counts
  - Trace data memoized per `queryId`; does not re-fetch on expand/collapse toggle

- `platform/src/app/api/audit/[queryId]/trace/route.ts` (create if absent)
  - Thin GET handler: reads `queryId` from path param, queries `query_trace_steps` filtered by `query_id`, returns ordered rows as JSON
  - Returns 404 when no rows found for the given `queryId`
  - Auth-gated: requires admin or super-admin session; returns 403 otherwise

### Modified files
- `platform/src/components/consume/AssistantMessage.tsx`
  - Import `InlineToolFlow`
  - Extract `queryId` from `message.metadata?.queryId` (or equivalent `query_trace_id` field on the message data part — inspect actual shape and use whichever is present)
  - Derive `isAdmin` from the user session using the same pattern already employed by other admin-gated UI in this file or its siblings
  - After the message content area (below citations / action bar), render:
    `<InlineToolFlow queryId={queryId ?? null} isAdmin={isAdmin} />`

- `platform/src/lib/feature_flags.ts` (or equivalent flag registry)
  - Add `MARSYS_FLAG_R9_TOOL_FLOW` with default rule: ON for `role === 'super-admin'`, ON for `role === 'admin'` viewing their own chart, OFF for all other roles / client-facing users

- `platform/src/components/consume/ConsumeChatV2.tsx` (only if `isAdmin` is not already threaded into `AssistantMessage` props — touch minimally)

---

## Files must not touch

- `platform/src/app/audit/**` — the existing audit page and its sub-routes; do not modify them
- `platform/src/components/consume/ConsumeChatLegacy.tsx` — deleted in §M.16; must not be recreated
- `platform/src/lib/pipeline/**` — pipeline internals; read only if needed to understand `query_trace_steps` schema
- `06_LEARNING_LAYER/**`
- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `00_ARCHITECTURE/**` (this brief file is already written; no further governance edits in this session)
- Any file outside `platform/src/` except `platform/src/app/api/audit/[queryId]/trace/route.ts`

---

## Acceptance criteria

1. **Super-admin disclosure visible.** When the logged-in user is super-admin and `MARSYS_FLAG_R9_TOOL_FLOW` is on, every `AssistantMessage` that carries a non-null `queryId` renders a "View tool flow ▸" disclosure button below the message content.

2. **Expand shows correct timeline.** Clicking the disclosure fetches `/api/audit/[queryId]/trace` and renders a vertical list of stage rows matching the order and data shown on `/audit/[queryId]` — same stage names, same durations, same status values.

3. **Collapsed by default.** On initial render the disclosure button is visible but the timeline panel is hidden. Expanding and re-collapsing returns to the collapsed state.

4. **Non-admin renders nothing.** For any user whose `isAdmin` resolves to false, `InlineToolFlow` renders null — no disclosure button, no DOM nodes, no network request.

5. **Flag off renders nothing.** When `MARSYS_FLAG_R9_TOOL_FLOW` is false (e.g. client-facing deployment), `InlineToolFlow` renders null even for admin users.

6. **Trace memoized per queryId.** Opening the disclosure for the same message a second time does not issue a second network request. The cached trace is used immediately.

7. **Synthesizer step detail.** The final synthesizer row in the expanded timeline displays the model name and input + output token counts in addition to stage name, duration, and status.

8. **TypeScript clean.** `tsc --noEmit` passes with zero new errors on all new and modified files.

9. **No regressions on existing messages.** AssistantMessage renders without error for messages that carry no `queryId` (e.g. legacy messages); the component simply omits the disclosure button.

10. **API auth gate.** Calling `GET /api/audit/[queryId]/trace` without an admin session returns HTTP 403; calling it with a valid admin session and a known `queryId` returns HTTP 200 with a JSON array of trace steps.

---

## Pre-commit gates

Run all of the following from the `platform/` directory; every command must exit 0 before committing:

```bash
# 1. TypeScript
npx tsc --noEmit

# 2. Lint
npx eslint src/components/chat/InlineToolFlow.tsx \
           src/components/consume/AssistantMessage.tsx \
           src/app/api/audit/\[queryId\]/trace/route.ts \
           --max-warnings 0

# 3. Unit / component smoke (if a test file is added — encouraged but not required for R9-S4)
npx jest --testPathPattern="InlineToolFlow" --passWithNoTests

# 4. Build
npx next build 2>&1 | tail -20
```

No gate may be skipped. If `next build` fails, the commit does not land.

---

## Commit message template

```
feat(chat-v2/r9-s4): inline tool-flow timeline disclosure in AssistantMessage

- Add InlineToolFlow component (collapsed by default, admin-only)
- Add GET /api/audit/[queryId]/trace thin wrapper over query_trace_steps
- Integrate <InlineToolFlow> into AssistantMessage after content area
- Gate behind MARSYS_FLAG_R9_TOOL_FLOW (on for admin/super-admin, off for clients)
- Trace data memoized per queryId; no re-fetch on expand/collapse

Acceptance criteria: R9-S4 §AC 1–10 all green.
Brief: 00_ARCHITECTURE/chat_v2_briefs/round9/R9-S4-inline-tool-flow-timeline.md
```
