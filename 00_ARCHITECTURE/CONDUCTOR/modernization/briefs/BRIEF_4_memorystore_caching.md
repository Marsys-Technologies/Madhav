---
status: COMPLETE
unit: 4.memorystore_caching
wave: 4
title: Memorystore (Redis) caching layer — retrieval bundles, planner, embeddings
stream: C
worktree: ../MadhavStreamC
blockedBy: [3.cutover]
on_red: rollback
---

## Context (self-contained)
Caching today is process-local 60s maps (per `dataSource.ts`) + a Postgres MV bundle cache. With
`min-instances=1` × 3 services and multi-tenant traffic coming, a shared **Memorystore Redis** cache for
retrieval bundles / planner results / Vertex embeddings cuts DB load + LLM spend and survives Cloud Run
instance recycling. (Per master plan §4.2-3 — recommended incremental investment.)

## Scope
- Provision a Memorystore Redis instance (asia-south1) via IaC; wire connection from amjis-web + amjis-mcp.
- Add `platform/src/lib/cache/` adapter with TTL + per-chart cache keys + invalidation hooks.
- Cache: retrieval-bundle results (per `(chart_id, ayanamsha_id, tool, params_hash)`), planner outputs,
  Vertex embedding lookups. Process-local 60s maps retired in favour of the shared cache.
- Cache hit/miss metrics fed to observability (lands with 4.observability).

## Acceptance criteria (all automated)
1. Redis client connects from both services; cache adapter unit tests green.
2. Process-local 60s caches removed (grep); shared cache covers the same surfaces.
3. Cache miss falls back to compute cleanly (chaos test: flush Redis mid-request → recovers).
4. No prod regression: a representative chat query latency is ≤ pre-Memorystore baseline.

## must_not_touch
`chart_facts`/`l25_*` (2a-owned data), `platform/python-sidecar/**` (engine compute path), `platform/src/lib/synthesis/panel/**`.

## Commit cadence / rollback
Commits: (1) Memorystore IaC + client wiring, (2) cache adapter + per-surface integration, (3) retire local
caches + tests. Rollback = revert (process-local caches restored if needed; Redis instance can be deleted).
