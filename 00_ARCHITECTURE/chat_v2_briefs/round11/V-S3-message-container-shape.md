---
canonical_id: R11_V_S3
version: 1.0
status: CURRENT
session_id: V-S3
title: Message-container shape — bubble-less assistant, 768px column, asymmetric pattern
depends_on: ["V-S2"]
blocked_on: []
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — component styling inside .consume-shell, gated by MARSYS_FLAG_R11_CLAUDE_RENDERING"
authored: 2026-05-21
amended: 2026-05-21 — per NATIVE_RULINGS §1, all `.claude-shell` references mean "inside .consume-shell, gated by MARSYS_FLAG_R11_CLAUDE_RENDERING" — the Marsys consume-shell class is the active class; this brief layers Claude shape rules onto it via the flag.
---

# V-S3 — Message Container Shape

## Context

Claude.ai's signature visual pattern is **asymmetric**: user messages are right-aligned bubbles (`border-radius: 1rem`, `max-width: 80%`, beige bg), assistant messages are **bubble-less** (serif text directly on the canvas, full-width inside the 768px centered column). Vertical spacing between turns is ~24-32px. Action bars (copy/retry/branch) appear on hover only.

Chat V2 today renders both roles in containers; assistant has a card-like surface. This session brings the consume route's message rendering inside `.claude-shell` to the asymmetric pattern.

## Files in Scope

- `platform/src/components/chat/AssistantMessage.tsx` — when inside `.claude-shell`, remove the card chrome (no background, no border, no padding-x at the message level); rely on the parent column for max-width.
- `platform/src/components/chat/UserMessage.tsx` — when inside `.claude-shell`, ensure right-alignment with `max-width: 80%`, `border-radius: 1rem`, beige bg.
- `platform/src/components/consume/ConsumeChatV2.tsx` (or its thread viewport child) — pin the message-stream column to `max-width: 48rem` (~768px) horizontally centered, inside `.claude-shell`. Vertical gap between message turns: `gap-6` to `gap-8` (24-32px).
- `platform/src/components/chat/MessageActionBar.tsx` (or equivalent) — under `.claude-shell`, default to `opacity-0` and `group-hover:opacity-100` (Claude-style hover-only reveal). Outside `.claude-shell` behavior unchanged.

## Files Must NOT Touch

- `.consume-shell` styling (preserved)
- The `v2-user-bubble` glassmorphism path (now scoped to `.consume-shell` only after V-S2)
- Citation panel layout (separate workstream)
- Phase 4C files

## Acceptance Criteria

1. **Bubble-less assistant inside `.claude-shell`:** the assistant message element has no background, no border, no inline padding at the message-element level when rendered inside `.claude-shell`.
2. **User bubble shape:** user messages inside `.claude-shell` are right-aligned with `border-radius: 1rem`, `max-width: 80%`, `padding: 12px 14px`.
3. **Column max-width:** the message stream column is `max-width: 48rem` (768px) centered horizontally inside `.claude-shell`.
4. **Vertical rhythm:** consecutive message turns are spaced ~24-32px apart (`gap-6` to `gap-8`).
5. **Action bar reveals on hover:** copy/retry/branch icons are visually hidden until parent message is hovered (or focused for keyboard).
6. **No regression with flag=false:** `.consume-shell` message rendering byte-identical.
7. **Click-path:** consume route with flag=true → assistant text sits directly on cream canvas, user message floats right as a beige rounded rectangle.
8. **Parent-context integration test:** mount `<ConsumeChatV2>` with seeded assistant+user messages, flag=true, assert (a) assistant element has no `border` and no `background-color`, (b) user element has matched border-radius computed style, (c) parent column computed `max-width` equals 768px.

## Pre-commit Gates

```bash
# Scoped styles: assistant container has no background INSIDE .claude-shell
grep -n "\.claude-shell .*Assistant\|claude-shell.*assistant" platform/src/components/chat/AssistantMessage.tsx

# Action bar hover-reveal pattern
grep -n "opacity-0\|group-hover:opacity" platform/src/components/chat/MessageActionBar.tsx || echo "WARN: confirm hover-reveal pattern"

npx jest --testPathPattern="V-S3|message-container-shape|asymmetric-pattern" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): asymmetric message containers inside .claude-shell

Bubble-less assistant, right-aligned user-bubble, 768px centered column,
24-32px inter-turn rhythm, hover-reveal action bar. Scoped via .claude-shell
ancestor; .consume-shell unchanged. Gated by MARSYS_FLAG_R11_CLAUDE_RENDERING
(NEXT_PUBLIC; deploy.yml --build-arg already added in V-S1).

Click-path: consume route with flag=true → asymmetric message layout.
```

## Decision Log

*(Executor: paste before/after screenshots of a 3-message exchange (user/assistant/user) under flag=true.)*
