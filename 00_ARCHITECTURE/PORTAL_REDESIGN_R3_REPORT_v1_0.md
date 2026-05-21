---
artifact: PORTAL_REDESIGN_R3_REPORT_v1_0
artifact_id: PORTAL_REDESIGN_R3_REPORT
version: 1.0
status: COMPLETE
phase: R3
authored_at: 2026-04-30T00:00:00Z
authored_by: Claude Code (Sonnet 4.6)
session_id: redesign-r3-build-upgrade-2026-04-30
branch: redesign/r3-build-upgrade
commits: [cf2bedd, 5d6567d, c593114, 03d0b25, be9491e]
---

# Portal Redesign R3 — Closure Report

## 1. Audit verdict

**Verdict B — Thin adapter (76 lines, ceiling 80).** Three gaps found between the hook stack and /api/chat/build: (1) useChatSession hardcodes /api/chat/consume — no endpoint param; (2) build route returned toTextStreamResponse() instead of toUIMessageStreamResponse() — blocking incompatibility; (3) build route did not persist conversations, so useFeedback would always 404. useBranches and useFeedback were hook-agnostic and needed no changes.

All three gaps resolved by a 76-line adapter (useBuildChatAdapter.ts) plus three bounded route changes. Full audit at 00_ARCHITECTURE/PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT_v1_0.md.

## 2. Adapter line count

76 lines. Spec ceiling: 80 lines. File: platform/src/hooks/useBuildChatAdapter.ts.

## 3. Session structure

R3 shipped in one session. Verdict B allowed R3b to proceed immediately within the same session as R3a.

## 4. Scope expansion

platform/src/app/api/chat/build/route.ts added to may_touch — three bounded changes: stream format (toTextStreamResponse → toUIMessageStreamResponse), conversation persistence (insertConversationWithId + replaceConversationMessages), conversationId in stream metadata. Route grep-verified as having BuildChat.tsx as its only consumer. Scope expansion approved during R3a review and documented in EXEC_BRIEF §1.4.

## 5. Test baseline preserved

Before R3: 13 failed files, 10 failed tests, 918 total.
After R3: 14 failed files, 10 failed tests, 936 total.
+1 failed file = build-mode.spec.ts (Playwright spec, same pattern as all other E2E specs — not a regression).
+18 tests = 8 BuildChat unit tests + 10 BuildRightPane unit tests, all passing.

## 6. Deliverables

- 00_ARCHITECTURE/PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT_v1_0.md — COMPLETE
- platform/src/hooks/useBuildChatAdapter.ts — COMPLETE (76 lines)
- platform/src/components/build/BuildChat.tsx — COMPLETE (replaced v1 shell with ChatShell composition)
- platform/src/components/build/BuildRightPane.tsx — COMPLETE (new: 5-widget right pane)
- platform/src/app/clients/[id]/build/page.tsx — COMPLETE (updated: loads build state + conversations)
- platform/src/app/clients/[id]/build/layout.tsx — COMPLETE (new: ZoneRoot zone=vellum)
- platform/src/app/clients/[id]/build/[conversationId]/page.tsx — COMPLETE (new: conversation resume route)
- platform/src/app/api/chat/build/route.ts — COMPLETE (3 bounded changes)
- tests/components/BuildChat.test.tsx — COMPLETE (8 passing tests)
- tests/components/BuildRightPane.test.tsx — COMPLETE (10 passing tests)
- tests/e2e/portal/build-mode.spec.ts — COMPLETE (Playwright spec)

## 7. Deferred polish items for R7

1. Accessibility pass on the new ChatShell instance in Build mode (ARIA, keyboard nav, focus)
2. Mobile layout pass — three-pane on small screens, sidebar drawer, right-pane collapse
3. InsightCards data source — currently derived from completed pyramid layers; a richer source would improve signal quality
4. ConversationSidebar rename/delete visual confirmation dialogs (Build-specific polish)

## 8. R7 coordination

R7 deferred Build-mode polish pending R3 closure. R3 PRs first; R7 picks up items 1–4 above as a small follow-up commit on redesign/r7-polish before its PR opens.

---

*End of PORTAL_REDESIGN_R3_REPORT_v1_0.md*
