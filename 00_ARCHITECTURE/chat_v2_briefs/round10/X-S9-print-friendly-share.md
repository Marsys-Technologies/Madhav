---
canonical_id: R10_X_S9
version: 1.0
status: CURRENT
session_id: X-S9
title: Print-friendly share page via @media print CSS
depends_on: [X-S8]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "no — server-rendered CSS; purely additive @media print rules"
authored: 2026-05-20
---

# X-S9 — Print-Friendly Share

## Context

The shared conversation page (`/app/share/[slug]/page.tsx`) renders a full Chat V2 conversation view. When a user prints this page (or uses "Save as PDF"), the output includes navigation chrome, floating buttons, sidebars, and other UI elements that are irrelevant on paper. Adding `@media print` CSS rules hides non-content elements and formats the conversation for clean printing.

**Amendment 3:** FLAGLESS — additive CSS only, zero behavior change, zero JavaScript change.

## Files in Scope

- `platform/src/app/share/[slug]/page.tsx` or the layout/styles imported by it — add `@media print` CSS (inline via Tailwind's `print:hidden` utilities or a scoped stylesheet)
- Potentially `platform/src/styles/` if a global or module CSS file is the right home

## Files Must NOT Touch

- Any React component logic
- Any server-side API routes
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **Print behavior:** `@media print` rules hide: sidebar/navigation, header action buttons (Share, Copy, etc.), floating UI overlays, any sticky headers/footers not part of the conversation content. The printed/PDF output shows: conversation title, messages in readable order, citations as inline references.
2. **Tailwind print utilities:** Use Tailwind's `print:hidden` class on non-print elements rather than a separate `.css` file, unless the project's style architecture makes a CSS module more appropriate (executor chooses the cleaner approach).
3. **No visible change on screen:** `@media print` rules are invisible in browser rendering. Running the app and viewing the share page shows zero visual difference.
4. **Typography:** Ensure body font-size in print context is ≥12pt (browser default usually handles this; verify no override shrinks it).
5. **Single-file change:** If using Tailwind utilities, changes are confined to the share page template only. No global CSS file is modified unless no other option exists.

## Pre-commit Gates

```bash
# Verify print:hidden or @media print appears in share page
grep -rn "print:hidden\|@media print\|media print" platform/src/app/share/ && echo "PASS" || echo "FAIL: no print CSS found"

# Only share page changed
git diff --stat HEAD | grep -v 'share' | grep '|' && echo "WARN: unexpected files" || echo "PASS: only share files"
```

## Commit Template

```
feat(chat-v2): print-friendly share page via @media print CSS

Adds print:hidden Tailwind utilities (or @media print rules) to
/share/[slug] page to hide navigation chrome, buttons, and overlays
on print/PDF. Zero behavior change on screen. Flagless per §M.16.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
