---
canonical_id: R11_O_S2
version: 1.0
status: CURRENT
session_id: O-S2
title: Prompt-cache breakpoints — 4 cache_control markers per Anthropic docs
depends_on: ["O-S1"]
blocked_on: ["O-S1 (V2 layout must land first so breakpoint positions are stable)"]
amended: 2026-05-21 — Open Item #4 LOCKED per NATIVE_RULINGS §4: ship canonical Anthropic 4-breakpoint layout EXACTLY (end-of-tools, end-of-system, end-of-RAG-bundle, last-assistant-turn). No experimental variants. 5-min ephemeral TTL.
flag: MARSYS_FLAG_R11_PROMPT_CACHE_V2
flag_default: false
client_side: "no — server-side request shaping"
authored: 2026-05-21
---

# O-S2 — Prompt-Cache Breakpoints

## Context

Anthropic supports up to **4 `cache_control` breakpoints** per request, lookback window 20 blocks. Cache hits charge ~10% of base input price (Sonnet 4.6: $3/M → $0.30/M cache-hit). With ~10-30K tokens of context (tool defs + system + MSR RAG bundle), a single warm cache turn saves 80-90% of input cost AND ~half a second of TTFB.

This session adds the canonical 4-breakpoint layout (end of tools, end of system, end of RAG bundle, last assistant turn) and a **measurement harness** to verify cache hit rate after rollout before flipping default true.

Per master-plan Open Item #4, the native rules on whether to keep this exact breakpoint layout or move the RAG-bundle marker.

## Files in Scope

- `platform/src/lib/synthesis/prompt_assembler.ts` (introduced in O-S1) — add `cache_control: { type: "ephemeral" }` (or 1h TTL as documented) on the four breakpoint positions when flag=true.
- `platform/src/app/api/chat/consume/route.ts` — capture `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` from the API response and emit them on the existing cost-events SSE part (Observatory integration).
- `platform/src/lib/observatory/cache_metrics.ts` (new) — log cache hit/miss to the Observatory pipeline.
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_PROMPT_CACHE_V2` (default false, server-side).

## Files Must NOT Touch

- `.github/workflows/deploy.yml` (server-side flag)
- Observatory dashboard (separate workstream; only the metric-emit point is added here)
- Phase 4C files

## Acceptance Criteria

1. **Four breakpoints declared:** with flag=true, the API request includes exactly 4 `cache_control` markers at the positions: end of tools, end of system, end of RAG bundle, last assistant turn.
2. **Breakpoint placement matches Open Item #4 ruling:** Decision Log records the native's ruling and the implementation matches.
3. **Cache metrics captured:** `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` are read from the Anthropic response and emitted to Observatory.
4. **Measurement harness:** a script or admin route that summarizes cache hit rate over the last N turns; executor runs it after 20 sample turns and pastes hit rate in Decision Log.
5. **Cost gate:** with flag=true and a warm cache, observed input cost per turn drops by ≥60% vs flag=false on a representative query set.
6. **Flag guard:** with flag=false, no `cache_control` markers in the request; behavior is exactly current.
7. **No regression:** sample outputs identical (modulo non-determinism).

## Pre-commit Gates

```bash
grep -rn "NEXT_PUBLIC.*PROMPT_CACHE_V2" platform/src --include="*.ts*" && echo "FAIL" || echo "PASS"
grep -n "cache_control" platform/src/lib/synthesis/prompt_assembler.ts && echo "PASS"
grep -n "cache_creation_input_tokens\|cache_read_input_tokens" platform/src/app/api/chat/consume/route.ts && echo "PASS"
npx jest --testPathPattern="O-S2|prompt-cache" --passWithNoTests
```

## Commit Template

```
feat(synthesis): 4-breakpoint cache_control layout (O-S2)

Adds Anthropic cache_control markers at the canonical positions: end of tools,
end of system, end of RAG bundle, last assistant turn. Cache metrics emitted to
Observatory pipeline. Guarded by MARSYS_FLAG_R11_PROMPT_CACHE_V2=false
(server-side; no NEXT_PUBLIC).

Expected: warm-cache turns at ~10% of base input cost.
```

## Decision Log

*(Executor: paste Open Item #4 ruling, measured hit rate after 20 sample turns, cost-per-turn delta vs flag=false.)*
