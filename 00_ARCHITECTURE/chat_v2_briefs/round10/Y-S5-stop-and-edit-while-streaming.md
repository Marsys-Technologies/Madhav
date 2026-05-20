---
canonical_id: R10_Y_S5
version: 1.0
status: CURRENT
session_id: Y-S5
title: Stop and edit while streaming
depends_on: [Y-S4]
blocked_on: []
flag: MARSYS_FLAG_R10_EDIT_WHILE_STREAMING
flag_default: false
client_side: "yes — NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING"
authored: 2026-05-20
risk: HIGH — UX risk; default FALSE; opt-in only
---

# Y-S5 — Stop and Edit While Streaming

## Context

Currently when a synthesis response is streaming, the user can click Stop but cannot immediately edit and re-send. They must wait for the stop to register, then manually edit the query in the composer. This session adds an "Edit & Resend" affordance that appears when the user clicks Stop: the current streaming response is truncated, the user's last prompt is restored in the composer for editing, and re-sending starts a new generation.

**Risk classification:** HIGH — UX risk. Default FALSE. Must be explicitly opted in by operator. The interaction sequence (stop → edit → resend) touches the streaming abort path, composer state, and message history in sequence. Testing must be thorough.

**IMPORTANT:** Do NOT touch `preprocessCitations.ts` or any citation preprocessing logic in this session.

**Amendment 1 (HARD GATE):** `NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING` is a client-side flag. It MUST be added to `.github/workflows/deploy.yml` `--build-arg` block with value `=false` (matching the default).

**Amendment 3:** FLAGGED, default false — UX risk.

**Amendment 2:** Visible component (Edit & Resend button) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/composer/Composer.tsx` — modify Stop button to show "Stop & Edit" option when flag enabled
- `platform/src/components/chat-v2/messages/MessageActions.tsx` (or stop button location) — wire abort + edit callback
- `platform/src/hooks/chat-v2/useChatActions.ts` (or equivalent) — `stopAndEdit()` action: aborts stream, marks last assistant message as `truncated_by_user_edit=true`, restores user prompt to composer
- `platform/supabase/migrations/` or `platform/migrations/` — add `truncated_by_user_edit BOOLEAN DEFAULT FALSE` to `audit_events` table (nullable; only populated when this feature fires)
- `platform/src/lib/feature_flags.ts` — add `MARSYS_FLAG_R10_EDIT_WHILE_STREAMING` (default `false`)
- `.github/workflows/deploy.yml` — add `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING=false`
- `platform/tests/` — integration test

## Files Must NOT Touch

- `platform/src/lib/citations/preprocessCitations.ts` — HARD prohibition; do not modify
- Phase 4C files
- R7-S2 synthesis prompt footnote block

## Acceptance Criteria

1. **deploy.yml (Amendment 1 — HARD GATE):** `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING=false`. Default is `false`. Session is NOT complete until present.
2. **Client-side classification (Amendment 1):** Executor confirms via grep: `grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING" platform/src --include="*.ts*"` — usage in `'use client'` component only.
3. **click-path (Amendment 2):** User path: Chat V2 (flag=true) → send a query → while streaming, click Stop → "Edit & Resend" button appears or composer opens with original prompt restored → user edits the prompt → clicks Send → new generation starts. The truncated assistant message remains in history, visually marked as truncated. Document in commit body.
4. **preprocessCitations not touched:** `git diff platform/src/lib/citations/preprocessCitations.ts` must show zero changes. HARD gate.
5. **Migration:** New migration file adds `truncated_by_user_edit BOOLEAN DEFAULT FALSE` to `audit_events`. Migration is reversible (drops column). Filename follows project numbering convention.
6. **Abort path:** The stop action properly aborts the in-flight fetch/SSE stream. No dangling stream connections after edit.
7. **Truncated message preserved:** The partial assistant message at the time of stop is preserved in message history with a visual "truncated" indicator. It is NOT deleted from the list.
8. **Retry-of-retry guard:** The "Edit & Resend" path does not create a chain of truncated messages on successive stops. Each stop-edit-resend cycle is independent.
9. **Flag guard:** When flag=false, Stop button behaves exactly as before — no "Edit & Resend" affordance. No regression.
10. **Parent-context integration test (Amendment 2):** At least one test mounts the full streaming message flow (ConsumeChatV2 or ChatShell, flag=true) and asserts: (a) during streaming, stop+edit shows composer with prior prompt, (b) truncated message remains in list marked truncated. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Amendment 1 — HARD GATE
grep "NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING" .github/workflows/deploy.yml && echo "PASS" || echo "FAIL: HARD GATE"

# HARD gate — preprocessCitations must not be touched
git diff platform/src/lib/citations/preprocessCitations.ts | grep '.' && echo "FAIL: preprocessCitations modified" || echo "PASS: preprocessCitations clean"

# Verify migration exists
ls platform/migrations/ | grep -i "truncated\|edit_while" || ls platform/supabase/migrations/ | grep -i "truncated\|edit_while"

npx jest --testPathPattern="stopAndEdit|stop.*edit|edit.*streaming" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): stop-and-edit while streaming [default false]

Stop button gains "Edit & Resend" affordance when MARSYS_FLAG_R10_EDIT_WHILE_STREAMING
=true (default false — opt-in). Aborts stream, restores prompt to composer,
preserves truncated message in history. Migration adds truncated_by_user_edit
to audit_events. NEXT_PUBLIC + deploy.yml build-arg at =false (Amendment 1).
preprocessCitations.ts not touched.

Click-path: streaming → Stop → Edit & Resend → edit prompt → new generation.
```

## Decision Log

*(Executor: record UX edge cases discovered during testing. Flag default=false means this is opt-in — document the operator flip command here.)*
