# Stream 1 Complete — V1.3 Production Activation

Generated: 2026-06-05

## PR Triage Summary
- CLOSE_STALE: 6 closed (#205, #204, #203, #202, #201, #170)
- MERGE_WITH_REBASE merged: 5 (#198 ganita.divisionals, #197 ganita.engine, #193 brahmagyan.texts, #191 panchanga, #189 facts_store)
- KEEP_OPEN (conflicts): 10 (#206, #199, #196, #195, #194, #190, #185, #183, #180, #179)
  - Common conflict: platform-mcp/src/server.ts (ws3 rewrite blocks many), deploy.yml (ws arc), CockpitShell.tsx (ws1)

## Migration Inventory Summary
- Applied in prod: 6 (build-infra only)
- Pending (NEW tables): pyramid_layers, classical_text_chunks, classical_chunks, reference_*, brahma_ontology, chart_divisionals, chart_panchanga
- Pending (idempotent, tables exist): all brahma_* migrations
- CRITICAL: pyramid_layers (portal 500 root cause) — migration authored at platform/migrations/v13_pyramid_layers.sql

## Key Finding
Portal 500 root cause = pyramid_layers missing. Migration committed. Stream 2 applies it first.

## Outputs
- /tmp/v13_migration_apply_order.md — full apply order (29 migrations)
- /tmp/v13_prod_baseline.txt — pre-activation prod state
- platform/migrations/v13_pyramid_layers.sql — new migration
