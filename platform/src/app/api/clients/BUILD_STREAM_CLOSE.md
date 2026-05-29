# B-Stream Close Artifact

Sessions: B-01 through B-12
Branch: feature/build-orch/stream-b

## Migrations applied: 124–132

Tables created:
- builds
- build_steps
- engine_versions
- build_notifications
- chart_facts_history
- chart_facts_supersedence
- chart_ayanamsha_reports
- chart_documents
- ayanamsha_registry

## Deliverables

UI:       NewClientForm — 5-ayanamsha multi-select (B-11)
API:      POST /api/clients — hardened create handler (D-05)
          POST /api/build/start — build trigger extension (B-series)
Tests:    20 DB-backed integration tests (B-12)
          platform/src/app/api/clients/__tests__/create.integration.test.ts

## Status

COMPLETE — all 12 sessions closed, all migrations applied to production amjis.
Integration tests skip gracefully when DATABASE_URL / DB_URL is not set.
Run with: DATABASE_URL=<dsn> npx vitest run src/app/api/clients/__tests__/create.integration.test.ts
