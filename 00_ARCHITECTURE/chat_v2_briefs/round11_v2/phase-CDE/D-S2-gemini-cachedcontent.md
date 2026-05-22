---
canonical_id: R11D_D_S2
session_id: D-S2
title: Gemini cachedContent API integration
phase: R11.D
depends_on: [D-S1]
flag: MARSYS_FLAG_R11D_GEMINI_CACHE (server-side, default false initially)
client_side: no
authored: 2026-05-22
---

# D-S2 — Gemini cachedContent API

## Context

Gemini uses a separate `cachedContent` API: create cached-content object → reference it in subsequent `generateContent` calls. Different mechanism from Anthropic's per-block markers.

## Files in Scope

- `platform/src/lib/providers/google/adapter.ts` — implement `cache()` method using Gemini's cachedContent API.
- `platform/src/lib/providers/google/cached_content.ts` (new) — create/reference helpers.
- `platform/src/app/api/chat/consume/route.ts` — capture `usage.cachedContentTokenCount` for Observatory.
- `platform/src/lib/config/feature_flags.ts` — register flag.

## Files MUST NOT Touch

- Anthropic cache path (D-S1)
- `.github/workflows/deploy.yml` (server-side flag)
- Stream-1 UI files

## Acceptance Criteria

1. With flag=true, Gemini requests reference a cachedContent object created with the RAG bundle + system prompt.
2. `cachedContentTokenCount` flows to Observatory.
3. Cost gate: warm-cache turns at ~25% of cold input cost.
4. With flag=false, no cachedContent created.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "cachedContent" src/lib/providers/google/adapter.ts src/lib/providers/google/cached_content.ts && echo "PASS"
npx jest --testPathPattern="D-S2|gemini.*cache" --passWithNoTests
```

## Commit Template

```
feat(synthesis): Gemini cachedContent API integration (D-S2)
```

## Decision Log

*(Executor: paste measured cachedContentTokenCount delta.)*
