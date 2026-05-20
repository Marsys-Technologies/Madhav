---
canonical_id: CHAT_V2_R8_S7_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S7
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_VISION
authored: 2026-05-20
depends_on: []
---

## Context

R8-S7 enables image attachment processing through the synthesis pipeline. When a user attaches an image in the Composer, the attachment is passed as a vision part to the underlying LLM (Gemini 2.5 Pro supports vision natively via both inline base64 and `fileUri` URL references). This session wires the full path: frontend attachment metadata → API request body → pipeline attachment check → Gemini image part injection → LLM call.

The preferred transport is `fileUri` (URL-based) when the attachment URL is publicly accessible, avoiding loading image bytes into the edge function. Inline base64 (`inlineData`) is the fallback when a public URL is unavailable.

Non-image attachments (PDF, plain text) must not enter the vision path. Unsupported MIME types must be rejected at the API boundary with HTTP 400 before reaching the LLM. No raw image bytes or base64 strings may appear in `query_trace` log output.

---

## Files in scope

### Backend

| Path | Action | Notes |
|---|---|---|
| `platform/src/lib/adapters/geminiVisionAdapter.ts` | CREATE | `GeminiVisionAdapter` — builds the image part array from `Attachment[]`; selects `fileData` (fileUri) or `inlineData` (base64) based on whether attachment carries a public URL; exports `buildImageParts(attachments: Attachment[]): GeminiImagePart[]` |
| `platform/src/lib/adapters/index.ts` | CREATE or EDIT | Re-export `GeminiVisionAdapter` and `buildImageParts` from the adapter barrel |
| `platform/src/app/api/synthesize/route.ts` | EDIT | Before constructing the LLM message array: extract `attachments` from request body; filter for `mime` starting with `image/`; call `buildImageParts`; prepend image parts to the user turn content array; reject any attachment with unsupported MIME (not `image/*`) via `return NextResponse.json({ error: 'Unsupported attachment MIME type' }, { status: 400 })` |
| `platform/src/types/attachments.ts` | CREATE or EDIT | Define (or extend) `Attachment` interface: `{ id: string; filename: string; mimeType: string; url?: string; storage_path?: string; size: number }` |

### Frontend

| Path | Action | Notes |
|---|---|---|
| `platform/src/hooks/useAttachments.ts` | EDIT | Add `mimeType: string` field to the internal attachment shape; populate from `File.type` at selection time; include `mimeType` in the payload sent to the API |
| `platform/src/components/chat/Composer.tsx` | EDIT (if needed) | Ensure file-selection handler passes `file.type` into the attachment object consumed by `useAttachments`; no UI changes required unless `mimeType` was previously omitted |

### Test

| Path | Action |
|---|---|
| `platform/tests/e2e/chat-v2/vision-smoke.spec.ts` | CREATE |

---

## Files must not touch

- `platform/src/components/consume/ConsumeChatV2.tsx` — no changes to the top-level chat shell in this session
- `platform/src/lib/pipeline/` — synthesis pipeline orchestration logic is read-only; route.ts is the injection point, not the pipeline internals
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — registry updates happen at session close only, not mid-implementation
- `01_FACTS_LAYER/**` — facts layer is out of scope for all Chat V2 sessions
- `025_HOLISTIC_SYNTHESIS/**` — synthesis corpus is out of scope
- `.geminirules` — Gemini-side mirror; not touched in this Claude-side session unless a mirror obligation is explicitly triggered
- `platform/src/app/api/synthesize/route.ts` schema validation middleware — do not remove or bypass existing request validation; add to it only

---

## Acceptance criteria

**AC-1 — Image part injection**
Attaching a JPEG (or PNG, WebP, GIF) to the Composer and sending a message causes the outgoing Gemini API call to include at least one image part (`fileData` or `inlineData`) in the user turn content array.

**AC-2 — Response references image content**
The LLM response to "What is in this image?" when a chart screenshot is attached contains text that is clearly derived from visual content, not just a reflection of the text question. Response length > 50 characters.

**AC-3 — Non-image attachments bypass vision path**
Attaching a PDF or plain-text file does not produce an image part; the PDF/text attachment is handled by the existing (or no-op) non-vision path without error.

**AC-4 — Unsupported MIME rejected at API**
Sending a request body with an attachment whose `mimeType` is not `image/*` (e.g., `application/octet-stream`, `video/mp4`) returns HTTP 400 with `{ error: 'Unsupported attachment MIME type' }` before any LLM call is made.

**AC-5 — No secrets or binary in query_trace**
`query_trace` log entries (if emitted) must not contain raw base64 image data, binary blobs, or any value longer than 512 characters derived from attachment content. Attachment presence is logged as metadata only (e.g., `{ attachments: [{ mimeType: 'image/jpeg', size: 204800 }] }`).

**AC-6 — TypeScript clean**
`tsc --noEmit` exits 0 across the platform package with all new and modified files in scope. No `any` escapes introduced in the adapter or hook changes.

**AC-7 — mimeType field present in useAttachments**
The attachment object produced by `useAttachments` carries a non-empty `mimeType` field populated from `File.type` at file-selection time and survives serialization into the API request body.

**AC-8 — fileUri preferred over inlineData**
When `attachment.url` is present and non-empty, `buildImageParts` produces a `fileData` part using `fileUri`. Only when `url` is absent does it fall back to fetching bytes and producing `inlineData`. This is verified by unit test in the adapter spec (not the E2E smoke).

---

## Pre-commit gates

Run the following in order before committing. All must pass.

```bash
# 1. TypeScript
cd platform && npx tsc --noEmit

# 2. Unit tests (adapter + hook)
cd platform && npx jest --testPathPattern="geminiVisionAdapter|useAttachments" --passWithNoTests

# 3. Lint
cd platform && npx eslint src/lib/adapters/geminiVisionAdapter.ts src/hooks/useAttachments.ts --max-warnings=0

# 4. E2E smoke (requires env vars; skip in CI if secrets absent)
if [ -n "$SMOKE_SESSION_COOKIE" ] && [ -n "$SMOKE_CHART_ID" ]; then
  cd platform && npx playwright test tests/e2e/chat-v2/vision-smoke.spec.ts --reporter=line
else
  echo "SMOKE_SESSION_COOKIE or SMOKE_CHART_ID not set — skipping vision E2E smoke"
fi
```

Gate failure policy: TypeScript and lint failures block the commit. Unit test failure blocks the commit. E2E smoke failure does not block the commit but must be recorded as a fix-forward item in the session close checklist.

---

## Commit message template

```
feat(vision): R8-S7 — wire image attachments through synthesis pipeline

- Add GeminiVisionAdapter (buildImageParts) with fileUri-first, inlineData fallback
- Inject image parts into Gemini user-turn content array in route.ts
- Extend useAttachments with mimeType field populated from File.type
- Reject unsupported MIME types with HTTP 400 before LLM call
- Add vision-smoke.spec.ts E2E gate (SMOKE_SESSION_COOKIE + SMOKE_CHART_ID guards)
- No binary/base64 data in query_trace; attachment metadata logged only

AC-1 through AC-8 satisfied. TypeScript clean. Lint 0 warnings.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
