---
canonical_id: R11A_A_S10
session_id: A-S10
title: Migration adapter — wrap existing single-shot pipeline as a CapabilityAdapter
phase: R11.A — Foundation
depends_on: [A-S7]
flag: MARSYS_FLAG_R11V2_USE_ADAPTERS
flag_default: true
client_side: "no — server-side adapter bridge"
authored: 2026-05-22
---

# A-S10 — Migration Adapter

## Context

The dispatcher (A-S7) routes capability calls to provider adapters (A-S2..A-S6). But the **existing single-shot pipeline** (planner + bundle + tool dispatch + synthesis) still does most of the actual work. Future phases (R11.D for cache, R11.E for agentic tool loops) replace pieces of this pipeline with native provider mechanisms.

Until those phases ship, the migration adapter **wraps the existing pipeline** as the chat() method's underlying implementation. The per-provider adapters delegate `chat()` to the migration adapter for now; later phases swap in native paths per-capability.

This is the **safety net** that keeps R11.A merging without breaking any production behavior. After A-S12 verifies all 5 providers smoke-pass through the adapter layer, `MARSYS_FLAG_R11V2_USE_ADAPTERS` flips on by default.

## Files in Scope

### Add

- `platform/src/lib/providers/migration-adapter.ts` — bridges the existing pipeline into the adapter shape:
  ```typescript
  export class MigrationAdapter {
    /** Wraps the existing pipeline_planner + consume route logic into the chat() signature */
    async *chat(request: ChatRequest, stackId: StackId): AsyncIterable<ChatEvent> {
      // Calls existing pipeline_planner.callPipelinePlanner with the active stackId
      // Routes through existing tool execution + synthesis
      // Translates existing SSE events (data-stage, data-tool, data-citation, data-cost, etc.)
      // into unified ChatEvent shape
      // Preserves R10 Y-S3 word-aware smooth_stream + Y-S4 reasoning step labels
      // Sacred components untouched
    }
  }
  ```
- `platform/tests/providers/migration-adapter.test.ts` — regression tests:
  - Anthropic stack: end-to-end query returns same response shape as legacy path
  - Google stack: same
  - OpenAI stack: same
  - DeepSeek stack: same (including <think> extraction)
  - NVIDIA stack: planner routes through correctly
  - All 5 SSE event types still emitted (data-stage, data-tool, data-citation, data-cost, data-observability, data-persistence)

### Modify

- `platform/src/lib/providers/anthropic/adapter.ts` — `chat()` delegates to `MigrationAdapter.chat()` until R11.D/R11.E ship native cache+loop paths. Pre-existing wrapping of `anthropic_observed.ts` from A-S2 becomes the inner call inside MigrationAdapter.
- `platform/src/lib/providers/google/adapter.ts` — same delegation pattern
- `platform/src/lib/providers/openai/adapter.ts` — same
- `platform/src/lib/providers/deepseek/adapter.ts` — same; preserves `<think>` middleware path
- `platform/src/lib/providers/nvidia/adapter.ts` — same; preserves planner routing

## Files MUST NOT Touch

- Existing pipeline code (`pipeline_planner.ts`, `consume/route.ts` core logic, `synthesis/`) — A-S10 WRAPS, doesn't modify
- Existing SSE event shapes
- R10 Y-S3 smooth_stream
- R10 Y-S4 reasoning step labels + ReasoningProgress
- PerMessageDetailsDrawer, PanelMember, Cost Visibility (sacred per NATIVE_RULINGS §5)
- Phase 4C files

## Acceptance Criteria

1. `MigrationAdapter` wraps the existing pipeline; `chat()` returns the same `ChatEvent` shape as native adapter calls.
2. All 5 provider adapters delegate `chat()` to `MigrationAdapter` for R11.A's release.
3. **No behavior regression on any of the 5 providers**: regression tests assert byte-identical SSE event sequences (modulo timestamps + nonces) between legacy and adapter paths.
4. Sacred components (PerMessageDetailsDrawer, Cost Visibility, PanelMember) still render unchanged.
5. R10 Y-S3 smooth-stream still applies.
6. R10 Y-S4 reasoning step labels still appear.
7. DeepSeek `<think>` extraction still works.
8. NVIDIA planner routing still works (`NVIDIA_PLANNER_ENABLED=true`).
9. Telemetry (A-S9) fires for every chat() dispatch.
10. Flag `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` defaults engaged after this session.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/migration-adapter.ts && echo "PASS"
# Each adapter delegates to MigrationAdapter
for p in anthropic google openai deepseek nvidia; do
  grep -n "MigrationAdapter\|migration-adapter" src/lib/providers/$p/adapter.ts && echo "PASS: $p delegates"
done
# Regression test gate
npx jest --testPathPattern="migration-adapter|A-S10" --passWithNoTests
# Sacred components untouched
grep -rn "PerMessageDetailsDrawer\|PanelMember" src/components --include="*.tsx" | wc -l  # baseline count
```

## Commit Template

```
feat(providers): migration adapter wraps legacy pipeline (A-S10)

MigrationAdapter wraps the existing single-shot pipeline (planner + bundle +
tool exec + synthesis) into the CapabilityAdapter.chat() shape. All 5 provider
adapters delegate chat() to this until R11.D/R11.E ship native cache + loop
paths.

PRESERVED VERBATIM:
- Existing pipeline_planner.ts logic
- All SSE event shapes (data-stage / data-tool / data-citation / data-cost /
  data-observability / data-persistence)
- R10 Y-S3 word-aware smooth_stream
- R10 Y-S4 reasoning step labels + ReasoningProgress
- DeepSeek <think> middleware
- NVIDIA planner routing
- Sacred components per NATIVE_RULINGS §5

Regression tests assert byte-identical SSE sequences between legacy and
adapter paths on all 5 stacks. MARSYS_FLAG_R11V2_USE_ADAPTERS=true after
this session lands.
```

## Decision Log

*(Executor: paste the regression-test report — 5 stacks × N queries each, byte-identical SSE events. Document any deltas.)*
