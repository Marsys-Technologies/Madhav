---
canonical_id: R11D_D_S0
session_id: D-S0
title: Caching capability check via adapter manifests
phase: R11.D (within R11.CDE composite)
depends_on: [R11C-MERGE]
flag: FLAGLESS
client_side: no
authored: 2026-05-22
---

# D-S0 — Caching Capability Check

## Context

Verify each provider's manifest correctly declares `promptCaching`:
- Anthropic: `'explicit_4bp'`
- Google: `'cached_content_api'`
- OpenAI: `'automatic'`
- DeepSeek: `'implicit'`
- NVIDIA: `null` (hide-and-hint)

## Files in Scope

- `platform/tests/providers/caching-capability-check.test.ts` (new) — manifest assertion.

## Acceptance Criteria

1. All 5 manifests report correct promptCaching value.
2. Test passes.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
npx jest --testPathPattern="caching-capability-check|D-S0" --passWithNoTests
```

## Commit Template

```
test(providers): caching capability check (D-S0)
```

## Decision Log

*(Executor: paste manifest readouts.)*
