---
canonical_id: R11C_C_S5
session_id: C-S5
title: Inline tool cards — verify ToolCallCard renders in stream order; tighten to Claude pattern
phase: R11.C
depends_on: [C-S4]
flag: MARSYS_FLAG_R11C_TOOL_CARDS (NEXT_PUBLIC, default true)
client_side: "yes — extends existing ToolCallCard.tsx"
authored: 2026-05-22
---

# C-S5 — Inline Tool Cards

## Context

`ToolCallCard.tsx` (Apr 29) and `InlineToolFlow.tsx` (R9-S4) already exist. Verify ToolCallCard renders inline in stream order in AssistantMessage; tighten visual to Claude's icon+verb pattern; map Marsys tool names to verb labels. Leave InlineToolFlow untouched. Do NOT create new InlineToolCard.tsx.

## Files in Scope

- `platform/src/components/chat/ToolCallCard.tsx` — audit + tighten visual (icon + verb label + progressive input reveal).
- `platform/src/components/chat/AssistantMessage.tsx` — verify inline ordering with `data-tool` parts.
- `platform/src/lib/chat-v2/useDataParts.ts` — confirm `data-tool` parts retain stream-position ordering.
- `platform/src/components/chat/tool_verbs.ts` (new) — Marsys tool-name → verb mapping.
- `platform/src/lib/config/feature_flags.ts` + `.github/workflows/deploy.yml` — register flag.

## Files MUST NOT Touch

- ToolCallCard.tsx (do NOT delete; extend only)
- InlineToolFlow.tsx (R9-S4; preserve)
- Stream-1 UI files
- Provider adapters

## Acceptance Criteria

1. ToolCallCard kept; InlineToolCard.tsx does NOT exist.
2. Visual: icon + verb label + progressive input reveal during streaming.
3. Stream-order interleaving verified by test (text_A → tool_X → text_B → tool_Y → text_C renders in DOM in that order).
4. Tool-verb mapping documented in tool_verbs.ts (`query_panchanga` → "Looked up panchang", etc.).
5. Marsys palette retained (gold accent, NOT coral).
6. Click-path documented.
7. Flag in deploy.yml.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
test -f src/components/chat/ToolCallCard.tsx && echo "PASS: kept"
test ! -f src/components/chat/InlineToolCard.tsx && echo "PASS: no duplicate"
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11C_TOOL_CARDS" ../.github/workflows/deploy.yml && echo "PASS: deploy.yml"
grep -n "ToolCallCard" src/components/chat/AssistantMessage.tsx && echo "PASS: wired"
npx jest --testPathPattern="ToolCallCard|C-S5" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): tighten ToolCallCard to Claude pattern + verify stream order (C-S5)
```

## Decision Log

*(Executor: paste tool_verbs mapping + before/after screenshot.)*
