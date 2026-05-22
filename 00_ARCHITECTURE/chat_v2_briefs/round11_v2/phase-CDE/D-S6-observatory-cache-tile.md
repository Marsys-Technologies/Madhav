---
canonical_id: R11D_D_S6
session_id: D-S6
title: Observatory dashboard tile — cache hit rate × provider × per-day
phase: R11.D
depends_on: [D-S5]
flag: FLAGLESS (Observatory UI extension)
client_side: yes (Observatory dashboard)
authored: 2026-05-22
---

# D-S6 — Observatory Cache Dashboard Tile

## Context

Aggregate the per-request cache telemetry from D-S1..D-S4 into an Observatory dashboard tile: cache hit rate × provider × per-day, with cost-savings calculation per provider.

## Files in Scope

- `platform/src/components/observatory/CacheMetricsTile.tsx` (new) — dashboard tile.
- `platform/src/lib/observatory/cache_aggregation.ts` (new) — aggregation queries.
- `platform/src/app/observatory/page.tsx` (or equivalent) — mount the new tile.

## Files MUST NOT Touch

- Provider adapters
- Stream-1 UI files
- Sacred components

## Acceptance Criteria

1. Tile renders cache hit rate per provider per day.
2. Cost-savings calc: cold cost vs warm cost per provider.
3. Provider with null promptCaching (NVIDIA) shows "n/a" row.
4. Click-path documented.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
test -f src/components/observatory/CacheMetricsTile.tsx && echo "PASS"
npx jest --testPathPattern="CacheMetricsTile|D-S6" --passWithNoTests
```

## Commit Template

```
feat(observatory): cache hit rate dashboard tile (D-S6)
```

## Decision Log

*(Executor: paste tile screenshot with 5-provider hit-rate data.)*
