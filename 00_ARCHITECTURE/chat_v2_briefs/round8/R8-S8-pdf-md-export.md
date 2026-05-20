---
canonical_id: CHAT_V2_R8_S8_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S8
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_EXPORT
authored: 2026-05-20
depends_on: []
---

## Context

R8-S8 adds conversation export functionality to the Chat V2 shell. Users can download a full conversation as Markdown, PDF, or JSON from an Export button added to the chat header. The feature is served via a new authenticated API route and a small dropdown UI component wired into `ChatShell.tsx`.

PDF export runs in the Node.js runtime (not the edge runtime). If the deployment environment cannot run `puppeteer` or an equivalent server-side PDF library, the route returns `501 Not Implemented` with a documented message; operators must confirm the route is set to `export const runtime = 'nodejs'` and that the PDF dependency is installed in the server environment.

The flag namespace `MARSYS_FLAG_R8_EXPORT` is reserved for any operator-level gate during rollout but is not required to be wired as a code-level feature flag for initial ship — the route and UI are always-on once deployed.

## Files in scope

- `platform/src/app/api/conversations/[id]/export/route.ts` — new file; the GET export route
- `platform/src/components/chat/ChatShell.tsx` — add Export button + dropdown to header
- `platform/src/components/chat/ExportDropdown.tsx` — new file; self-contained dropdown component (Download Markdown, Download PDF, Copy JSON)
- `platform/package.json` — add PDF generation dependency if viable (`html-pdf-node` preferred over `puppeteer` for lighter footprint; document the chosen package here)
- `platform/package-lock.json` (or `pnpm-lock.yaml` / `yarn.lock`) — lockfile update from dependency add

## Files must not touch

- `platform/src/app/api/conversations/[id]/route.ts` — existing conversation CRUD route; do not modify
- `platform/src/components/chat/ConsumeChatV2.tsx` — rendering core; no changes from this session
- `platform/src/components/consume/ConsumeChatV2.tsx` — same; do not modify
- `platform/src/lib/feature_flags.ts` — flag namespace is reserved but no code-level flag is wired in this session; do not add a flag entry unless the executor determines a hard gate is required and records the decision in the session log
- Any file under `00_ARCHITECTURE/` other than this brief itself
- Any file under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `06_LEARNING_LAYER/`
- `.geminirules`, `.gemini/project_state.md` — mirror-pair files; no changes from this session
- `platform/src/app/api/conversations/[id]/messages/` — unrelated sub-route tree

## Acceptance criteria

1. **MD export — message order.** `GET /api/conversations/<id>?format=md` returns a `text/markdown` response whose body lists every message in chronological order. User turns are prefixed `**User:** `. Assistant turns are rendered as-is (already Markdown). Consecutive messages are separated by `---` on its own line. Header line: `# Conversation <id>\n\n` before the first message.

2. **MD export — headers.** Response carries `Content-Type: text/markdown; charset=utf-8` and `Content-Disposition: attachment; filename="conversation-<id>.md"`.

3. **JSON export — structure.** `GET /api/conversations/<id>?format=json` returns `Content-Type: application/json` with body `{ "id": "<id>", "messages": [ { "role": "user"|"assistant", "content": "...", "timestamp": "<ISO-8601>" }, ... ] }`. Body must parse as valid JSON with `messages` as an array.

4. **JSON export — headers.** `Content-Disposition: attachment; filename="conversation-<id>.json"`.

5. **PDF export — happy path.** `GET /api/conversations/<id>?format=pdf` returns `Content-Type: application/pdf` with a non-empty binary body that opens as a valid PDF when saved. Route declares `export const runtime = 'nodejs'` at the top of the file.

6. **PDF export — known limitation fallback.** If PDF generation fails at runtime (dependency unavailable or runtime mismatch), the route returns HTTP 501 with body `{ "error": "PDF export requires a Node.js runtime — use the MD export instead" }`. Both outcomes (valid PDF or 501) are acceptable per this brief; the 501 path must be explicitly tested.

7. **Auth — unauthenticated.** Requests with no valid session return HTTP 401.

8. **Auth — wrong owner.** Requests with a valid session but a conversation owned by a different user return HTTP 403 (or 404 if the implementation opts for information-hiding semantics). Either status is acceptable; document the chosen behavior in a code comment.

9. **Bad format parameter.** `?format=` absent, empty, or not one of `pdf|md|json` returns HTTP 400 with body `{ "error": "format must be one of: pdf, md, json" }`.

10. **Export dropdown — render.** An Export button (`<Download />` lucide icon, visually consistent with the existing Share button) appears in the `ChatShell` header. Clicking it opens a dropdown with three items: "Download Markdown", "Download PDF", "Copy JSON". The dropdown closes on outside click or Escape key.

11. **Download Markdown / Download PDF.** Clicking either item navigates `window.location.href` to the corresponding `/api/conversations/${id}/export?format=md|pdf` URL. The browser handles the download via the `Content-Disposition: attachment` header. No custom fetch logic needed for these two items.

12. **Copy JSON.** Clicking "Copy JSON" issues a `fetch` to `/api/conversations/${id}/export?format=json`, reads the response text, writes it to `navigator.clipboard`, and displays a brief toast or inline "Copied!" label (minimum 1 500 ms visible; use the existing toast infrastructure if present, otherwise a local state toggle suffices).

13. **TypeScript clean.** `tsc --noEmit` passes with no new errors introduced by this session's changes. No `any` casts added.

14. **No console errors.** The dropdown, fetch, and clipboard flows produce no unhandled promise rejections or console errors under normal browser operation.

## Pre-commit gates

Run all of the following from `platform/` before committing. All must exit 0 (or produce no new failures relative to the pre-session baseline):

```bash
# 1. TypeScript
npx tsc --noEmit

# 2. Lint
npx eslint src/app/api/conversations/\\[id\\]/export/route.ts \
           src/components/chat/ChatShell.tsx \
           src/components/chat/ExportDropdown.tsx \
           --max-warnings 0

# 3. Unit / integration tests (if a test file is added for the route)
npx jest --testPathPattern="export" --passWithNoTests

# 4. Build check (catches import errors not caught by tsc)
npx next build --no-lint 2>&1 | tail -20
# Must not contain "Type error" or "Module not found" for files touched in this session
```

Manual smoke (document results in commit message body):

- [ ] MD download: file opens in a text editor, all messages present in correct order
- [ ] JSON download: `jq .messages` parses cleanly, role/content/timestamp fields present
- [ ] PDF: file opens in a PDF viewer OR the 501 response is returned with the documented body (record which outcome occurred)
- [ ] Auth: unauthenticated curl returns 401; wrong-owner session returns 403/404
- [ ] Dropdown renders, closes on outside click and Escape
- [ ] "Copy JSON" copies valid JSON and shows "Copied!" indicator

## Commit message template

```
feat(chat-v2/r8-s8): conversation export — MD, JSON, PDF via /api/conversations/[id]/export

Adds GET /api/conversations/[id]/export?format=md|json|pdf:
- md: text/markdown attachment, user turns prefixed with **User:**
- json: application/json attachment with messages array (role/content/timestamp)
- pdf: application/pdf via <CHOSEN_LIB> (Node.js runtime required);
       returns 501 if PDF generation is unavailable
- 400 on unknown format; 401 unauthenticated; 403/404 wrong owner

Adds Export dropdown to ChatShell header (Download MD, Download PDF, Copy JSON).

PDF outcome: [VALID_PDF | 501_RETURNED — document which]

Smoke: MD ✓ JSON ✓ PDF <outcome> Auth ✓ Dropdown ✓ Copy ✓
TypeScript: clean  ESLint: clean  Build: green

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
