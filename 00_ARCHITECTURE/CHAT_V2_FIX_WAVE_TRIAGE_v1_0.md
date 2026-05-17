---
id: CHAT_V2_FIX_WAVE_TRIAGE
version: 1.0
status: CURRENT
created: 2026-05-17
---

# Chat V2 Chrome Parity — Fix Wave Triage

_Triaged from 5 parallel subagent sessions + code verification. Source of truth for implementation order._

## Summary

5 W-case failures from the 2026-05-17 F.1 incident. Root causes identified per case below.
Fix priority order: W3 → W10 → W5 → W4+W8 bundle.

---

## W3 — Details drawer: model/tokens/cost never populated

**Test duration when failing:** 27.3 minutes (900s timeout exhausted)

**Root cause (CONFIRMED):**
`PerMessageDetailsDrawer` reads data parts from `message.content` (lines 91-97 of
`platform/src/components/chat/PerMessageDetailsDrawer.tsx`), expecting format
`{ type: 'data', name: 'cost', data: {...} }`.

In the assistant-ui runtime used by ConsumeChatV2 (`useChatRuntime` + `DefaultChatTransport`),
ALL streaming data parts land in `message.metadata.unstable_data` as
`{ type: 'data-cost', data: {...} }` — NOT in `message.content`.

Evidence: `V2Message` reads identically-structured data parts from `message.metadata.unstable_data`
(line 429 of `ConsumeChatV2.tsx`) for stage, tool, prediction-candidate. `PerMessageDetailsDrawer`
was written with a different assumption about the message format.

**Route emission (confirmed correct):**
`platform/src/app/api/chat/consume/route.ts` lines 1045-1067: emits `data-cost` correctly in
`onFinish`. Not the break point.

**Fix location:**
`platform/src/components/chat/PerMessageDetailsDrawer.tsx` lines 85-97.

**Fix:** Replace `message.content` extraction with `message.metadata.unstable_data` extraction,
normalizing `type: 'data-{name}'` → `name = type.slice(5)`:

```diff
-  type NamedDataPart = { type: 'data'; name: string; data: Record<string, unknown> }
-  const namedDataParts = ((message.content ?? []) as ReadonlyArray<unknown>).filter(
-    (p): p is NamedDataPart =>
-      typeof p === 'object' &&
-      p !== null &&
-      (p as Record<string, unknown>).type === 'data' &&
-      typeof (p as Record<string, unknown>).name === 'string',
-  )
+  // In assistant-ui, data parts from streaming land in metadata.unstable_data
+  // as { type: 'data-{name}', data: {...} }, NOT in message.content.
+  type RawDataPart = { type: string; data: Record<string, unknown> }
+  type NamedDataPart = { name: string; data: Record<string, unknown> }
+  const rawUnstable = (message.metadata?.unstable_data ?? []) as ReadonlyArray<unknown>
+  const namedDataParts: NamedDataPart[] = rawUnstable
+    .filter((p): p is RawDataPart =>
+      typeof p === 'object' && p !== null &&
+      typeof (p as Record<string, unknown>).type === 'string' &&
+      ((p as Record<string, unknown>).type as string).startsWith('data-') &&
+      typeof (p as Record<string, unknown>).data === 'object',
+    )
+    .map(p => ({ name: p.type.slice(5), data: p.data }))
```

Downstream `costEntry`, `gateEntry`, `obsEntry` lookups unchanged.

---

## W10 — Citation chips: [N] badges never appeared

**Test duration when failing:** 15.5 minutes (test or upstream stream hung)

**Root cause (CONFIRMED):**
`V2AssistantText` (line 331 of `ConsumeChatV2.tsx`) gates citation chip rendering with `!isStreaming`:
```tsx
{citationChips.length > 0 && !isStreaming && (
  <div className="mt-2 flex flex-wrap gap-1.5" data-testid="v2-citation-chips">
```

`isStreaming = message.status?.type === 'running'`. The assistant-ui runtime may keep the
message in `running` state during `onFinish` data-part emission (citations arrive post-synthesis).
Once the response stream closes (all data parts processed), `isStreaming` transitions to false —
but the Playwright test's `waitForStreamComplete` gates on `v2-abort-btn` disappearing which
may fire before citation chips render if there's a brief re-render lag.

The `!isStreaming` guard was defensive (avoid flash during live typing) but prevents chips from
appearing in the final frame.

**Fix location:**
`platform/src/components/consume/ConsumeChatV2.tsx` line 331.

**Fix:**
```diff
-      {citationChips.length > 0 && !isStreaming && (
+      {citationChips.length > 0 && (
```

Citation chips only populate once text contains `SIG.MSR.NNN` patterns (extracted by
`renderWithCitations`). Removing the `!isStreaming` guard is safe — chips won't flash during
streaming because they don't exist in `citationChips` until the full signal ID text is present.

---

## W5 — Regenerate: old assistant turn not removed

**Test duration when failing:** 15.3 minutes (re-generation stream timed out)

**Root cause (CONFIRMED):**
`V2RegenerateButton` (lines 375-412 of `ConsumeChatV2.tsx`) uses `ActionBarPrimitive.Reload asChild`
with a fire-and-forget fetch to `/api/chat/consume/regenerate`:

```typescript
void fetch('/api/chat/consume/regenerate', {
  method: 'POST',
  body: JSON.stringify({ conversation_id: conversationId, parent_message_id: parentId }),
}).catch(() => {})
```

The `ActionBarPrimitive.Reload` handler fires IMMEDIATELY (before truncation completes),
triggering a new synthesis against the UNTRUNCATED conversation. The old assistant turn
persists in the database. The new synthesis re-uses the full message history including the
stale assistant turn.

The `/api/chat/consume/regenerate` endpoint EXISTS and is correct (deletes conversation_messages
after parent). The race condition is between the DB truncation (async, fire-and-forget) and
the assistant-ui Reload (synchronous, fires immediately on button click).

**Fix location:**
`platform/src/components/consume/ConsumeChatV2.tsx` lines 375-412 (`V2RegenerateButton`).

**Fix:** Replace fire-and-forget + ActionBarPrimitive.Reload with: await truncation, then
call `runtime.reload()` explicitly. Remove `ActionBarPrimitive.Reload asChild` wrapper.

```diff
 function V2RegenerateButton() {
   const message = useMessage()
   const runtime = useThreadRuntime()
   const conversationId = useContext(ConversationIdCtx)

-  const handleClick = useCallback(() => {
+  const handleClick = useCallback(async () => {
     if (!conversationId) return
     const messages = runtime.getState().messages
     const myIndex = messages.findIndex((m) => m.id === message.id)
     const parentId = myIndex > 0 ? messages[myIndex - 1].id : null
     if (!parentId) return
-    void fetch('/api/chat/consume/regenerate', {
-      method: 'POST',
-      headers: { 'Content-Type': 'application/json' },
-      body: JSON.stringify({ conversation_id: conversationId, parent_message_id: parentId }),
-    }).catch(() => {})
+    try {
+      await fetch('/api/chat/consume/regenerate', {
+        method: 'POST',
+        headers: { 'Content-Type': 'application/json' },
+        body: JSON.stringify({ conversation_id: conversationId, parent_message_id: parentId }),
+      })
+      runtime.reload()
+    } catch {
+      // Truncation failed — don't reload; UI stays in current state
+    }
   }, [message.id, runtime, conversationId])

   return (
-    <ActionBarPrimitive.Reload asChild>
-      <button
-        type="button"
-        onClick={handleClick}
-        ...
-        data-testid="v2-regenerate-btn"
-      >
-        ...
-      </button>
-    </ActionBarPrimitive.Reload>
+    <button
+      type="button"
+      onClick={handleClick}
+      ...
+      data-testid="v2-regenerate-btn"
+    >
+      ...
+    </button>
   )
 }
```

---

## W4 — Panel mode toggle: v2-panel-mode-toggle not visible within 10s

**Test duration when failing:** 30.1s (10s toBeVisible timeout + ~20s page load)

**Root cause (PROBABLE):**
`PanelModeToggle` component exists at
`platform/src/components/chat-v2/PanelModeToggle.tsx` with `data-testid="v2-panel-mode-toggle"`.
It renders unconditionally inside `V2Composer` → `ComposerPrimitive.Root`.

The 30.1s failure (10s timeout + 20s page load) suggests the element is in the DOM but
a JavaScript crash caused by other W-case bugs (W3/W5/W10) rendered the React tree into an
error boundary, replacing the composer UI. After fixing W3/W5/W10, W4 should pass.

If W4 still fails after the other fixes: the element is visible but `ComposerPrimitive.Root`
may have an async hydration delay. Fix: add `data-testid="v2-composer-options"` wrapper
visibility as a proxy check, or confirm element is outside any conditional rendering gate.

**Current element location:** `ConsumeChatV2.tsx:1066` inside `div[data-testid="v2-composer-options"]`.
**Testid:** `v2-panel-mode-toggle` (PanelModeToggle.tsx:30). Test uses same testid — correct.

**Fix:** No code change needed. Verify after W3/W5/W10 fixes. If still failing, investigate
ComposerPrimitive.Root rendering conditions.

---

## W8 — Trace button: v2-details-btn / v2-trace-btn not found

**Test duration when failing:** 11.3s

**Root cause (PROBABLE):**
The W8 test (`walkthrough-comprehensive.spec.ts:318`) is a SOFT test — it checks
`v2-trace-btn` visibility via `isVisible()` and annotates rather than hard-asserting.
The test CANNOT hard-fail on button absence.

The 11.3s failure was most likely a side-effect: the V2 UI crashed (React error from W3/W5/W10
bugs) causing page navigation or unhandled promise, which made the test fail at the
`waitForStreamComplete` step or at a subsequent assertion.

Both `v2-trace-btn` (`ConsumeChatV2.tsx:1471`) and `v2-details-btn` (`ConsumeChatV2.tsx:654`)
exist in the current codebase. The `v2-trace-btn` is conditional on `audienceTier === 'super_admin'`.

**Fix:** No code change needed. W8 should pass after W3/W5/W10 fixes resolve V2 stability.
Confirm via Playwright W8 test run with auth (super_admin session).

---

## Implementation Order

| Priority | Fix ID | File | Change | Gate |
|----------|--------|------|--------|------|
| 1 | F-W3 | PerMessageDetailsDrawer.tsx | Read from unstable_data | W3 Playwright PASS |
| 2 | F-W10 | ConsumeChatV2.tsx:331 | Remove `!isStreaming` | W10 Playwright PASS |
| 3 | F-W5 | ConsumeChatV2.tsx:375-412 | Await truncation + runtime.reload() | W5 Playwright PASS |
| 4 | F-W4W8 | — | Verify (likely auto-fixed) | W4+W8 Playwright PASS |
