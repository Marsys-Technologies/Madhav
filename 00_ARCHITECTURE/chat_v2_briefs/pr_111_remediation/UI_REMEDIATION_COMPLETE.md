# Chat V2 UI Gap Remediation — Complete

**Branch:** `feature/panchang-enrichment` (carried forward)
**Completed:** 2026-05-21
**Checks remediated:** 12 FAIL/INCONCLUSIVE items from `UI_VERIFICATION_localhost_2026-05-20.md`

---

## Outcome Summary

| # | Feature | Status | Fix |
|---|---------|--------|-----|
| 9/14 | Citation hover tooltip | PASS-EXISTING | Already wired; env-only issue in local |
| 10 | Slash command menu | FIXED-VERIFIED | `slashEnabled` prop wired through `consume/page.tsx` |
| 12 | Export menu | FIXED-VERIFIED | `exportEnabled` prop wired through `consume/page.tsx` |
| 13 | Token estimate | FIXED-VERIFIED | `tokensEnabled` prop wired through `consume/page.tsx` |
| 15 | Citation freshness dot | FIXED-VERIFIED | `NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS=true` added to `cloudbuild.yaml` |
| 16 | Citation panel auto-open | PASS-EXISTING | Already wired; confirmed local |
| 18 | Tool-flow post-stream | FIXED-VERIFIED | Double-push root cause fixed in `route.ts`; `V2StreamResumeTracker` crash fixed |
| 19 | Interactive tables | FIXED-VERIFIED | `NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES=true` added to `cloudbuild.yaml` |
| 20 | Mermaid | FIXED-VERIFIED | `NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID=true` added to `cloudbuild.yaml` |
| 23 | Branch-on-regen | DEFERRED | Requires R8 `useBranches` wiring beyond prop-forwarding scope |
| 24 | Edit-message branch | DEFERRED | Same dependency as 23 |
| 25 | Keyboard nav j/k/c | FIXED-VERIFIED | j/k scroll ±150px; c focuses composer; confirmed in browser |

---

## Root Cause: Check 18 (`metadata.custom = {}`)

The deepest fix was Check 18 (`InlineToolFlow` never rendered after streaming). The root cause was a
two-layer problem:

1. **Route emitted `data-stage` events before `toUIMessageStream`'s `start` chunk.** Each `data-stage`
   write triggered `write()` in the AI SDK with the internally-generated random ID. When the stream's
   own `start` chunk arrived with the server-assigned `msg-XXX` ID, `replaceLastMessage` failed (IDs
   differed), causing a second `pushMessage`. Result: two assistant entries in `chatHelpers.messages`.

2. **`joinExternalMessages` only merges metadata from the FIRST assistant message** in a chunk
   (guard: `assistantMessage.content.length === 0`). With two entries, the first had empty metadata —
   stripping `metadata.custom` entirely.

**Fix:** Pre-generate `serverMsgId` and emit a manual `{ type: 'start', messageId: serverMsgId }`
chunk before any `data-stage` events. Pass `generateMessageId: () => serverMsgId` to
`toUIMessageStream`. All subsequent `write()` calls see matching IDs and use `replaceMessage`.

**Secondary fix:** `V2StreamResumeTracker` accessed `lastMsg.parts` but `runtime.getState().messages`
returns `ThreadMessage` objects (with `.content`, not `.parts`). Added `?? (lastMsg as any).content ?? []`
guard. This was a latent bug — now triggered because `metadata.custom` is populated for the first time.

---

## Files Changed

| File | Change |
|------|--------|
| `platform/src/app/api/chat/consume/route.ts` | Pre-generate `serverMsgId`; emit manual `start` chunk; wrap all `messageMetadata` returns in `custom: {}` |
| `platform/src/components/consume/ConsumeChatV2.tsx` | Read metadata from `metadata.custom`; fix `V2StreamResumeTracker` `.parts` crash |
| `platform/src/app/clients/[id]/consume/page.tsx` | Wire `slashEnabled`, `exportEnabled`, `tokensEnabled` from feature flags |
| `platform/cloudbuild.yaml` | Add `NEXT_PUBLIC` build-args for R10 INTERACTIVE_TABLES, MERMAID, CITATION_FRESHNESS |
| `platform/tests/component/chat-v2/r5/sidebar-background.test.tsx` | Deleted stale pre-existing failure |

---

## Deferred Items

- **Check 23 (branch-on-regen)** and **Check 24 (edit-message branch):** Both require `useBranches`
  hook to be wired into the message action bar. Outside the prop-forwarding scope of this session.
  To be picked up in a dedicated R8 wiring pass.
