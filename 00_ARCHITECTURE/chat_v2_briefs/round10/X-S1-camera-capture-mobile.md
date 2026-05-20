---
canonical_id: R10_X_S1
version: 1.0
status: CURRENT
session_id: X-S1
title: Camera capture on mobile — file input capture attribute
depends_on: [X-S0]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — additive HTML attribute on existing file input"
authored: 2026-05-20
---

# X-S1 — Camera Capture on Mobile

## Context

The Chat V2 composer has a file attachment input that allows users to attach images and documents. On mobile devices, browsers support the `capture="environment"` attribute on `<input type="file" accept="image/*">` to open the camera directly instead of the file picker. This is a purely additive one-attribute change that greatly improves mobile UX.

**Amendment 3:** FLAGLESS — purely additive HTML attribute, no behavior change for non-camera flows, no backend impact.

**Amendment 2:** Visible component (file input in Composer) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/composer/Composer.tsx` (or wherever the file `<input>` lives — executor must grep to confirm exact path)
- `platform/src/hooks/chat-v2/useAttachments.ts` (or equivalent) — verify camera blob (image/jpeg from camera) is handled identically to file-picker blob; no code change expected but must be confirmed
- `platform/tests/` — new or updated integration test

## Files Must NOT Touch

- Any Phase 4C files
- Any server-side route handlers
- `.github/workflows/deploy.yml` (no flag to add)
- `platform/src/components/chat-v2/ConsumeChatV2.tsx` (unless the file input lives inside it — executor confirms)

## Acceptance Criteria

1. **click-path (Amendment 2):** The exact user path to reach this behavior is: open Chat V2 → click the attachment/paperclip icon in the composer → on a mobile browser, the system sheet offers "Take Photo / Camera" as a direct option. Document this in the commit body.
2. **`capture="environment"` added:** The file `<input>` element that accepts images in the composer has `capture="environment"` on the element rendered when `accept` includes `image/*`.
3. **Attachment hook unchanged:** Camera blobs (MIME type `image/jpeg` or `image/png` from camera) pass through `useAttachments` without errors — confirm by reading the hook; if no change needed, document "confirmed no change required".
4. **Parent-context integration test (Amendment 2):** At least one test mounts `ConsumeChatV2` (or the outermost Chat V2 shell that provides attachment context) and asserts that clicking the attachment trigger renders a file input with `capture="environment"`. Leaf-with-injected-props test alone does NOT satisfy this AC.
5. No visual regression on desktop — `capture` attribute is ignored by desktop browsers, so existing behavior is unchanged.

## Pre-commit Gates

```bash
# Verify capture attribute present in source
grep -rn 'capture="environment"' platform/src/components/chat-v2/ && echo "PASS" || echo "FAIL: capture attr missing"

# Run affected tests
npx jest --testPathPattern="composer|attachment|capture" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): camera capture on mobile via capture="environment" on file input

Mobile users can now open the camera directly from the composer attachment
button. Adds capture="environment" to the image file input — additive only,
ignored on desktop. Flagless per §M.16.

Click-path: Chat V2 → attachment icon → mobile system sheet → "Take Photo".
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
