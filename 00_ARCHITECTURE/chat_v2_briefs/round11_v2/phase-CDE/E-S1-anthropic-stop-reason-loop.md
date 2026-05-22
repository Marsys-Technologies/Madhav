---
canonical_id: R11E_E_S1
session_id: E-S1
title: Anthropic agentic loop — while (stop_reason === 'tool_use')
phase: R11.E
depends_on: [E-S0]
flag: MARSYS_FLAG_R11E_ANTHROPIC_LOOP (server-side, default false — HIGH risk)
client_side: no
authored: 2026-05-22
---

# E-S1 — Anthropic stop_reason Loop

## Context

**Biggest behavioral change in the arc.** Replace today's single-shot pipeline (when Anthropic is active) with the canonical agentic loop:

```typescript
while (response.stop_reason === 'tool_use') {
  const toolBlocks = response.content.filter(b => b.type === 'tool_use');
  const toolResults = await Promise.all(toolBlocks.map(execute));
  messages.push({ role: 'assistant', content: response.content });
  messages.push({ role: 'user', content: toolResults });
  response = await anthropic.messages.create({...});
}
```

8-iteration cap. Default false until verified.

## Files in Scope

- `platform/src/lib/providers/anthropic/adapter.ts` — implement `tools()` method returning agentic loop topology.
- `platform/src/lib/synthesis/agentic_loop.ts` (new) — generic loop engine; Anthropic adapter feeds Anthropic-specific iteration.
- `platform/src/app/api/chat/consume/route.ts` — when active stack is Anthropic + flag=true, dispatch via loop instead of single-shot.
- `platform/src/lib/config/feature_flags.ts` — register flag.

## Files MUST NOT Touch

- Tool implementations themselves (preserve `lib/retrieve/*`)
- Stream-1 UI files
- Other providers' loop work (E-S2..E-S5)
- `.github/workflows/deploy.yml` (server-side flag)

## Acceptance Criteria

1. With flag=true + Anthropic active: loop dispatches tools by stop_reason; up to 8 iterations.
2. With flag=false: single-shot pipeline preserved.
3. Integration test: multi-tool query triggers ≥2 loop iterations.
4. Token accounting: sum per-iteration usage to total Observatory cost.
5. Server-side only.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -rn "NEXT_PUBLIC.*ANTHROPIC_LOOP" src --include="*.ts*" && echo "FAIL" || echo "PASS"
grep -n "stop_reason.*tool_use\|while.*tool_use" src/lib/synthesis/agentic_loop.ts src/lib/providers/anthropic/adapter.ts && echo "PASS"
npx jest --testPathPattern="E-S1|anthropic.*loop" --passWithNoTests
```

## Commit Template

```
feat(synthesis): Anthropic stop_reason agentic loop (E-S1, HIGH RISK)
```

## Decision Log

*(Executor: paste sample multi-tool trace; iteration count; cost per turn.)*
