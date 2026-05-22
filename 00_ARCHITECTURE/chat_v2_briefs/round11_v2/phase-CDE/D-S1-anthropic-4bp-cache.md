---
canonical_id: R11D_D_S1
session_id: D-S1
title: Anthropic 4-breakpoint cache_control — canonical layout
phase: R11.D
depends_on: [D-S0]
flag: MARSYS_FLAG_R11D_ANTHROPIC_CACHE (server-side, default false initially)
client_side: no
authored: 2026-05-22
---

# D-S1 — Anthropic 4-Breakpoint Cache

## Context

Wire `cache_control: { type: 'ephemeral' }` at 4 canonical positions per NATIVE_RULINGS §4: end-of-tools, end-of-system, end-of-RAG-bundle, last-assistant-turn. 5-min TTL. Capture `usage.cache_creation_input_tokens` + `usage.cache_read_input_tokens` for Observatory.

## Files in Scope

- `platform/src/lib/providers/anthropic/adapter.ts` — implement `cache()` method returning 4-breakpoint config.
- `platform/src/lib/synthesis/prompt_assembler.ts` (new or extended) — placement logic.
- `platform/src/app/api/chat/consume/route.ts` — emit cache-token usage to Observatory.
- `platform/src/lib/observatory/cache_metrics.ts` (new) — log per-request hit/miss.
- `platform/src/lib/config/feature_flags.ts` — register flag.

## Files MUST NOT Touch

- `.github/workflows/deploy.yml` (server-side flag)
- Stream-1 UI files
- Other providers' cache wiring (later sessions)

## Acceptance Criteria

1. With flag=true, Anthropic requests include exactly 4 `cache_control` markers at canonical positions.
2. Cache token usage emitted to Observatory.
3. With flag=false, no cache_control in requests.
4. Cost gate: with warm cache, input cost drops ≥60% on representative query set.
5. Server-side only.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -rn "NEXT_PUBLIC.*ANTHROPIC_CACHE" src --include="*.ts*" && echo "FAIL" || echo "PASS"
grep -n "cache_control" src/lib/providers/anthropic/adapter.ts src/lib/synthesis/prompt_assembler.ts && echo "PASS"
npx jest --testPathPattern="D-S1|anthropic.*cache" --passWithNoTests
```

## Commit Template

```
feat(synthesis): Anthropic 4-breakpoint cache_control (D-S1)
```

## Decision Log

*(Executor: paste measured hit rate after 20 sample turns; cost-per-turn delta.)*
