---
canonical_id: R11D_D_S3
session_id: D-S3
title: OpenAI automatic caching — telemetry capture (no markers)
phase: R11.D
depends_on: [D-S2]
flag: FLAGLESS (telemetry only; OpenAI auto-caches without markers)
client_side: no
authored: 2026-05-22
---

# D-S3 — OpenAI Automatic Cache Telemetry

## Context

OpenAI caches automatically without marker annotations. This session only captures `prompt_tokens_details.cached_tokens` from responses and emits to Observatory.

## Files in Scope

- `platform/src/lib/providers/openai/adapter.ts` — `cache()` method returns a no-op config (OpenAI auto-caches).
- `platform/src/lib/providers/openai/observed.ts` (or adapter wrapper) — capture `cached_tokens` field from response usage.
- `platform/src/app/api/chat/consume/route.ts` — route the captured tokens to Observatory.

## Files MUST NOT Touch

- Anthropic/Gemini cache paths
- Stream-1 UI files

## Acceptance Criteria

1. OpenAI adapter's `cache()` returns no-op (no markers added to request).
2. `cached_tokens` field captured from every OpenAI response.
3. Tokens flow to Observatory.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "cached_tokens" src/lib/providers/openai/adapter.ts src/app/api/chat/consume/route.ts && echo "PASS"
npx jest --testPathPattern="D-S3|openai.*cache" --passWithNoTests
```

## Commit Template

```
feat(observatory): OpenAI cached_tokens telemetry (D-S3)
```

## Decision Log

*(Executor: paste sample telemetry record.)*
