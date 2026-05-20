# Chat V2 Round 10 — Sessions Log

Branch: chat-v2/round10 | Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR10
Stream type: sequential single-stream (21 sessions)
Log started: 2026-05-20

---

## X-S0 — NIM_STACK_DEGRADED Build-Arg Cleanup

**Status:** COMPLETED  
**Commit:** 2efce23  
**Completed:** 2026-05-20T08:00:00Z

Added `NEXT_PUBLIC_NIM_STACK_DEGRADED=false` to the `--build-arg` block in `.github/workflows/deploy.yml`. The client-side flag at `platform/src/components/chat/ModelStylePicker.tsx:51` was absent from deploy.yml, meaning the NIM degradation badge was unreachable by operators (client-side flags are baked at Docker build time). Added at `=false` to preserve current off-by-default behavior while making it operator-flippable. Single file changed: `.github/workflows/deploy.yml`. Acceptance check PASS. Amendment 4 satisfied.

**Amendments:** A3 (FLAGLESS — deploy.yml cleanup only) | A4 (NIM_STACK_DEGRADED entry — this IS the fix)

---

## X-S1 — Camera Capture on Mobile

**Status:** COMPLETED  
**Commit:** de0d4fd  
**Completed:** 2026-05-20T08:45:00Z

Added mobile camera capture to the Chat V2 composer. Implementation: separate hidden `<input type="file" accept="image/*" capture="environment" data-testid="v2-camera-input">` plus a mobile-only camera button (`md:hidden`, `data-testid="v2-camera-btn"`). Kept the existing general attachment input unchanged to preserve iOS Safari PDF upload compatibility (adding `capture=` to a mixed-type input restricts iOS to camera-only). Exported `AttachmentCtx` for test access. 5 new tests in `camera_capture.test.tsx` — all use `AttachmentCtx.Provider` parent context (Amendment 2 satisfied). Typecheck: PASS. New tests: 5/5 PASS. Pre-existing lint issues in ConsumeChatV2.tsx (16 errors at lines 1301+) are unchanged — zero new errors.

**Click-path:** Chat V2 → attachment area → camera button (mobile only, md:hidden on desktop) → system sheet → Take Photo.

**Amendments:** A2 (parent-context test + click-path documented) | A3 (FLAGLESS — additive)

---

## X-S2 — ArrowUp Recall Last Prompt

**Status:** COMPLETED  
**Commit:** ba85a0b  
**Completed:** 2026-05-20T09:00:00Z

Added `useLastPrompt(conversationId)` hook to `useChatPreferences.ts`. Per-conversation localStorage cache with key `marsys_chat_v2_last_prompt_<conversationId>`. Wired in `V2Composer`: `handleComposerKeyDown` handles ArrowUp (when empty) to restore last sent and Enter to save; send button's onClick also saves. 8 new tests in `recall_last_prompt.test.ts` — all pass. Typecheck: PASS.

**Click-path:** Chat V2 → send message → clear composer → ArrowUp → message restored.

**Amendments:** A2 (click-path documented, hook tests verify context chain) | A3 (FLAGLESS)

---

## X-S3 — Citation Star Persistence

**Status:** COMPLETED  
**Commit:** a7ea69d  
**Completed:** 2026-05-20T09:15:00Z

Added `useStarredCitations(conversationId)` hook backed by localStorage (`marsys_chat_v2_starred_<conversationId>`). Modified `CitationSidePanel` to accept optional `conversationId` prop and use the hook instead of ephemeral local state. Passed `conversationId` from `V2ChatRuntime`. 10 new tests in `starred_citations.test.ts` — all pass. Typecheck: PASS.

**Click-path:** Chat V2 → response with citations → open citation panel → star citation → refresh → reopen panel → star still active.

**Amendments:** A2 (click-path documented, hook tests verify persistence chain) | A3 (FLAGLESS)

---

## X-S4 — Still-Working Indicator

**Status:** COMPLETED  
**Commit:** c6be14b  
**Completed:** 2026-05-20T09:30:00Z

Created `StillWorkingIndicator.tsx` component. Shows animated dots + elapsed seconds after 25s of continuous streaming (`isStreaming && elapsed > 25s`). Auto-hides when streaming ends. `aria-live="polite"` for screen readers. Wired in `V2Message` (ConsumeChatV2) above `MessagePrimitive.Parts`. 7 new tests using `StreamingShell` parent context wrapper + fake timers — all pass.

**Click-path:** Long query → streaming > 25s → "Still working… (Ns)" indicator appears → stream ends → indicator disappears.

**Amendments:** A2 (parent-context test with StreamingShell + fake timers, click-path documented) | A3 (FLAGLESS)

---

## X-S5 — Skeleton Loaders

**Status:** COMPLETED  
**Commit:** d37a84a  
**Completed:** 2026-05-20T08:45:00Z

Created `SidebarSkeleton.tsx` (6 animate-pulse rows, aria-hidden) and `HeaderSkeleton.tsx` (two skeleton rects matching title/meta dimensions, aria-hidden). Wired `SidebarSkeleton` in `ConversationSidebarV2` replacing the "Loading…" paragraph when `loading && conversations.length === 0`. Added `onLoadingChange?: (loading: boolean) => void` prop to `ConversationSidebarV2Props` + a `useEffect` to bubble loading state changes to parent. In `ConsumeChatV2`: added `sidebarLoading` state, passed `onLoadingChange={setSidebarLoading}` to sidebar, and conditionally renders `<HeaderSkeleton />` vs the real title div based on `sidebarLoading`. 9 new tests in `skeleton_loaders.test.tsx` — all pass. Typecheck: PASS.

**Decision:** HeaderSkeleton is wired to sidebar loading state (bubbled via `onLoadingChange`), not a separate data fetch, because `chartName` is always available as a prop but the conversation list requires a fetch. The skeleton thus covers the initial network round-trip that users experience on first load.

**Click-path:** Load Chat V2 on slow/throttled network → sidebar begins fetch → SidebarSkeleton (6 pulse rows) appears in conversation list, HeaderSkeleton (shimmer rects) appears where title/meta normally render → fetch completes → real content loads in.

**Amendments:** A2 (SidebarShell + HeaderShell parent-context wrappers in tests, click-path documented) | A3 (FLAGLESS)

---

## X-S6 — Auto-Scroll Discipline

**Status:** COMPLETED  
**Commit:** 7473cdd  
**Completed:** 2026-05-20T09:07:00Z

Created `useScrollDiscipline.ts` hook with IntersectionObserver on a bottom sentinel element. Sentinel's closest `[data-testid="v2-thread-viewport"]` is used as `root`, so visibility detection is relative to the scroll container. `ScrollToBottomButton` updated with optional `unreadCount` prop — shows "N new" label and adjusts layout when count > 0. `V2ScrollDiscipline` component mounts sentinel + button inside `ThreadPrimitive.Viewport`; uses `useThreadRuntime().subscribe()` to increment unread count on each streaming batch while not at bottom. `SCROLL_DISCIPLINE_ENABLED` module-level constant guards between new (IntersectionObserver-based) and old (ThreadPrimitive.ScrollToBottom asChild) behaviors. deploy.yml updated with `NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true` (Amendment 1 HARD GATE). 8 tests — all pass.

**Click-path:** Send long query → while streaming, scroll up → auto-scroll stops → "↓ N new" button appears → click → scrolls to bottom and count resets.

**Amendments:** A1 (deploy.yml NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true — HARD GATE satisfied) | A2 (ScrollViewportShell parent-context wrapper in tests, click-path documented) | A3 (FLAGGED, default true)

---
