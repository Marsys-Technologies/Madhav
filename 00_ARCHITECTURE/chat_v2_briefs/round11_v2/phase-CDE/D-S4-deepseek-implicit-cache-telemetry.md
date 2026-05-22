---
canonical_id: R11D_D_S4
session_id: D-S4
title: DeepSeek implicit cache — telemetry capture (no markers)
phase: R11.D
depends_on: [D-S3]
flag: FLAGLESS (telemetry only)
client_side: no
authored: 2026-05-22
---

# D-S4 — DeepSeek Implicit Cache Telemetry

## Context

DeepSeek's API reports `prompt_cache_hit_tokens` implicitly. Capture for Observatory. NVIDIA is documented in manifest as `promptCaching: null` (no work needed).

## Files in Scope

- `platform/src/lib/providers/deepseek/adapter.ts` — `cache()` returns no-op.
- `platform/src/lib/providers/deepseek/observed.ts` — capture `prompt_cache_hit_tokens` from usage.
- Observatory wiring (extends D-S3 pattern).

## Files MUST NOT Touch

- Other providers' cache work
- Stream-1 UI files

## Acceptance Criteria

1. DeepSeek `cache()` returns no-op.
2. `prompt_cache_hit_tokens` captured and flows to Observatory.
3. NVIDIA manifest `promptCaching: null` confirmed (capability hint surfaces "Switch to other stack" if user expects caching).

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "prompt_cache_hit_tokens" src/lib/providers/deepseek/adapter.ts && echo "PASS"
npx jest --testPathPattern="D-S4|deepseek.*cache" --passWithNoTests
```

## Commit Template

```
feat(observatory): DeepSeek prompt_cache_hit_tokens telemetry (D-S4)
```

## Decision Log

*(Executor: paste sample telemetry; note NVIDIA's null manifest declaration.)*
