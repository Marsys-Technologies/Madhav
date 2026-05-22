---
canonical_id: R11D_D_S5
session_id: D-S5
title: Cache-aware prompt layout — restructure synthesis prompt for cache-friendliness
phase: R11.D
depends_on: [D-S4]
flag: MARSYS_FLAG_R11D_PROMPT_LAYOUT (server-side, default false initially)
client_side: no
authored: 2026-05-22
---

# D-S5 — Cache-Aware Prompt Layout

## Context

Restructure the synthesis prompt assembly so cache-friendly ordering is the default: tools → static system → RAG bundle → conversation messages. Anthropic's 4 cache_control breakpoints (D-S1) place naturally at these boundaries. Other providers benefit from the same ordering even if their caching is automatic/implicit.

**Hard preservation rule (Amendment 4):** R7-S2 footnote block + Y-S4 step-marker instructions preserved byte-identical (note: R11.B B-S7 retires the footnote system in stream-1; if R11.B merges first, this brief verifies the synthesis prompt no longer contains those blocks).

## Files in Scope

- `platform/src/lib/synthesis/prompt_assembler.ts` — restructure assembly order.
- `platform/src/lib/synthesis/synthesis_prompt_v2.ts` (or equivalent) — audit + reorder.
- `platform/src/app/api/chat/consume/route.ts` — call updated assembler.
- `platform/src/lib/config/feature_flags.ts` — register flag.

## Files MUST NOT Touch

- R7-S2 footnote block (preserve until R11.B retires it)
- Y-S4 step-marker text (preserve)
- Stream-1 UI files
- Phase 4C files

## Acceptance Criteria

1. With flag=true, prompt assembled as tools → system → RAG → messages.
2. Anthropic 4 breakpoints place at the correct boundaries (verify in D-S1's gate).
3. R7-S2 footnote + Y-S4 step markers byte-identical (if not yet retired by R11.B).
4. With flag=false, prompt unchanged.
5. Server-side only.
6. Snapshot test of assembled prompt under both flag states.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -rn "NEXT_PUBLIC.*PROMPT_LAYOUT" src --include="*.ts*" && echo "FAIL" || echo "PASS"
npx jest --testPathPattern="D-S5|prompt-layout|prompt-assembler" --passWithNoTests
```

## Commit Template

```
feat(synthesis): cache-aware prompt layout (D-S5)
```

## Decision Log

*(Executor: paste before/after prompt structure; confirm preservation of R7-S2/Y-S4 blocks.)*
