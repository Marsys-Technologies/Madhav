---
canonical_id: R10_X_S11
version: 1.0
status: CURRENT
session_id: X-S11
title: Mermaid diagram rendering in chat responses
depends_on: [X-S10]
blocked_on: []
flag: MARSYS_FLAG_R10_MERMAID
flag_default: true
client_side: "yes — NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID"
authored: 2026-05-20
---

# X-S11 — Mermaid Diagram Rendering

## Context

The synthesis pipeline can emit fenced code blocks with `lang=mermaid` containing diagram definitions (flowcharts, timelines, Gantt charts for dasha periods, etc.). Currently these render as raw text code blocks. This session adds lazy-loaded `MermaidBlock` rendering via the `mermaid` npm package, with a stream-safe placeholder during streaming.

**Amendment 1 (HARD GATE):** `NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID` is a client-side flag. It MUST be added to `.github/workflows/deploy.yml` `--build-arg` block.

**Amendment 3:** FLAGGED — lazy-loads the heavy mermaid bundle (~1MB); risk-managed.

**Amendment 2:** Visible component (MermaidBlock) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/messages/MermaidBlock.tsx` (new) — lazy-loaded via `React.lazy`/`next/dynamic`
- `platform/src/components/chat-v2/messages/MarkdownContent.tsx` — code handler routes `lang=mermaid` to MermaidBlock when flag enabled
- `package.json` in `platform/` — add `mermaid` dependency
- `.github/workflows/deploy.yml` — add `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID=true`
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side pipeline code (mermaid rendering is client-only)
- Phase 4C files
- Any other MarkdownContent handlers beyond the code block handler

## Acceptance Criteria

1. **deploy.yml (Amendment 1 — HARD GATE):** `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID=true`. Session is NOT complete until present.
2. **Client-side classification (Amendment 1):** Executor confirms via grep: `grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID" platform/src --include="*.ts*"` — confirms usage in a `'use client'` component.
3. **click-path (Amendment 2):** User path: Chat V2 response containing a `\`\`\`mermaid` block → the block renders as a visual diagram (flowchart/timeline/etc.) rather than raw code text. During streaming, a placeholder (spinner or "Rendering diagram…") shows until streaming is complete. Document in commit body.
4. **Lazy loading:** `MermaidBlock` is loaded via `next/dynamic` with `{ ssr: false }` so the mermaid bundle is not included in the server-side render or the initial page bundle. This keeps the main bundle lean.
5. **Stream-safe placeholder:** While the parent message is still streaming (`isStreaming === true`), show a loading placeholder instead of attempting to render the mermaid diagram. Render the diagram only after streaming completes for that message.
6. **Error boundary:** If mermaid fails to parse/render the diagram definition, show a fallback code block (raw text) rather than a crash. No unhandled promise rejection.
7. **Flag guard:** When `NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID=false`, mermaid code blocks render as standard fenced code blocks (existing behavior).
8. **Package version pinned:** `mermaid` version is pinned in `package.json` (not `^latest`). Prefer the latest stable release at session execution time.
9. **Parent-context integration test (Amendment 2):** At least one test mounts `MarkdownContent` within its real parent message context (isStreaming=false) with a mermaid code block input and flag=true, and asserts `MermaidBlock` renders (not raw code). A streaming test asserts placeholder shows when isStreaming=true. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Amendment 1 — HARD GATE
grep "NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID" .github/workflows/deploy.yml && echo "PASS: deploy.yml has flag" || echo "FAIL: HARD GATE"

grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID" platform/src --include="*.ts*" && echo "PASS: client-side usage" || echo "FAIL"

# mermaid package installed
grep '"mermaid"' platform/package.json && echo "PASS: package present" || echo "FAIL: add mermaid to package.json"

npx jest --testPathPattern="mermaid|Mermaid|MermaidBlock" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): mermaid diagram rendering in chat responses

MermaidBlock.tsx (next/dynamic, ssr:false) renders mermaid code blocks.
Stream-safe placeholder during streaming; error boundary fallback to
code view. MarkdownContent code handler routes lang=mermaid. Guarded
by MARSYS_FLAG_R10_MERMAID=true (NEXT_PUBLIC + deploy.yml build-arg per
Amendment 1).

Click-path: response with ```mermaid block → visual diagram rendered.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
