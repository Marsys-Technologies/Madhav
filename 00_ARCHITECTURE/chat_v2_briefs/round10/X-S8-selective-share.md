---
canonical_id: R10_X_S8
version: 1.0
status: CURRENT
session_id: X-S8
title: Selective share — hide reasoning and methodology from shared link
depends_on: [X-S7]
blocked_on: []
flag: MARSYS_FLAG_R10_SELECTIVE_SHARE
flag_default: true
client_side: "no — server-side flag; touches share render route + schema migration"
authored: 2026-05-20
---

# X-S8 — Selective Share

## Context

When users share a conversation link, they may not want to expose the reasoning trace or methodology sections — these contain Jyotish analytical detail that may be sensitive or just noise for the recipient. This session adds checkboxes to the ShareButton flow: "Include reasoning" and "Include methodology" (both checked by default). The settings are stored in `conversation_shares` and consulted by the share renderer.

**Amendment 3:** FLAGGED — schema-touching (database migration), gated rollout desired.

**Amendment 1:** Server-side flag only (read in share render route/server component). No `NEXT_PUBLIC_` prefix needed. Flag is `MARSYS_FLAG_R10_SELECTIVE_SHARE`. No deploy.yml build-arg required (server env var sufficient).

**Amendment 2:** Visible component (ShareButton checkboxes) → click-path and parent-context test required.

## Files in Scope

- Database migration file under `platform/migrations/` or `platform/supabase/migrations/` — add `hide_reasoning BOOLEAN DEFAULT FALSE` and `hide_methodology BOOLEAN DEFAULT FALSE` to `conversation_shares` table
- `platform/src/components/chat-v2/share/ShareButton.tsx` — add checkboxes
- `platform/src/app/share/[slug]/page.tsx` (or share renderer) — consult `hide_reasoning`/`hide_methodology` fields when rendering
- `platform/src/lib/share/` or equivalent — share creation function passes new fields
- `platform/tests/` — integration test

## Files Must NOT Touch

- `platform/src/components/chat-v2/messages/MarkdownContent.tsx`
- Phase 4C files
- `.github/workflows/deploy.yml` (server-side flag, no build-arg needed)

## Acceptance Criteria

1. **Flag is server-side (Amendment 1 confirmation):** `MARSYS_FLAG_R10_SELECTIVE_SHARE` is read only in server components or API route handlers — NOT in any `'use client'` component or file. Executor must grep to confirm: `grep -rn "MARSYS_FLAG_R10_SELECTIVE_SHARE" platform/src --include="*.ts*"` — no result should appear in client components.
2. **Migration:** New migration file adds `hide_reasoning BOOLEAN DEFAULT FALSE NOT NULL` and `hide_methodology BOOLEAN DEFAULT FALSE NOT NULL` to `conversation_shares`. Migration is reversible (rollback drops the columns safely if no data). Migration filename follows project convention (numbered prefix).
3. **click-path (Amendment 2):** User path: Chat V2 conversation → click Share → share modal appears with two checkboxes "Show reasoning" and "Show methodology" (both checked by default) → uncheck "Show reasoning" → click "Create Link" → recipient opens the link → reasoning section is absent from the shared view. Document in commit body.
4. **Default behavior preserved:** When both checkboxes are checked (default), shared conversation renders identically to current behavior. No regression for existing shares (legacy shares without the fields render as if both = false = show everything, since DEFAULT FALSE means "do not hide").
5. **Share renderer:** When `hide_reasoning = TRUE`, omit reasoning/think sections from the rendered share page. When `hide_methodology = TRUE`, omit methodology sections. Use the flag guard: when `MARSYS_FLAG_R10_SELECTIVE_SHARE` is disabled, ignore hide fields and render everything.
6. **Parent-context integration test (Amendment 2):** At least one test mounts `ShareButton` within the real ChatShell/provider chain (providing conversationId) and asserts: (a) modal opens with checkboxes, (b) unchecking "reasoning" and submitting passes `hide_reasoning: true` to the share creation function. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Verify flag is server-side only (no NEXT_PUBLIC prefix)
grep -rn "MARSYS_FLAG_R10_SELECTIVE_SHARE" platform/src --include="*.ts*"
# Should NOT appear in 'use client' files — executor confirms manually

# Verify migration file exists
ls platform/migrations/ | grep -i "selective_share\|hide_reason" || ls platform/supabase/migrations/ | grep -i "selective\|hide"

npx jest --testPathPattern="share|Share|SelectiveShare" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): selective share — hide reasoning/methodology from shared links

Migration: conversation_shares gains hide_reasoning + hide_methodology BOOL
DEFAULT FALSE. ShareButton checkboxes (both checked by default). Share
renderer omits sections per flags. Guarded by MARSYS_FLAG_R10_SELECTIVE_SHARE
(server-side, default true).

Click-path: Share → uncheck "Show reasoning" → Create Link → recipient sees response only.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
