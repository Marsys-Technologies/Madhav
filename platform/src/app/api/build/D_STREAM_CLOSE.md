# D-Stream Close Artifact

**Stream:** D — Build API Routes
**Sessions:** D-01 through D-09
**Closed:** 2026-05-29
**Tag:** [BUILD-ORCH-D-09]

---

## API Routes Delivered

| Session | Route | Description |
|---------|-------|-------------|
| D-01 | `POST /api/build/start` | Trigger build — ayanamshas[] support, 14 build_steps created, Cloud Tasks enqueue |
| D-02 | `POST /api/build/cancel/[buildId]` | Cancel build — status transitions (queued/running → cancelling), terminal-state 409, idempotent re-cancel 200 |
| D-03 | `GET /api/build/active` | In-progress builds with progress_pct derived from build_steps; scoped by uid / super_admin |
| D-04 | `GET /api/build/recent` | Unseen completed builds (24h window); graceful notification_views degradation; Cache-Control: no-store |
| D-05 | `POST /api/clients/create` | Create chart — hardened with rate-limit (5/hr) + idempotency key + ayanamshas[] validation |
| D-06 | `GET /api/engine/current` | Current engine version metadata — public (no auth); Cache-Control: max-age=300 |
| D-07 | `GET /api/conversations/[id]/active-ayanamshas` | Per-conversation ayanamsha selection; graceful J-01 column-absent degradation; source field |
| D-08 | `GET /api/charts/[id]/ayanamsha-status` | 5-ayanamsha per-chart build state; canonical order; is_latest_engine; finished_at fallback |

---

## Test Coverage

### Unit Test Files (mocked DB)

| File | Route | Assertions |
|------|-------|-----------|
| `__tests__/start_route.test.ts` | POST /api/build/start | flag kill-switch, auth, happy path, super_admin |
| `__tests__/cancel_route.test.ts` | POST /api/build/cancel/[buildId] | auth, owner cancel, terminal 409, idempotent, super_admin |
| `__tests__/active_route.test.ts` | GET /api/build/active | auth, empty, queued/running/cancelling, shape, progress_pct, super_admin, Cache-Control |
| `__tests__/recent_route.test.ts` | GET /api/build/recent | auth, empty, inclusion, shape, super_admin, NV degradation, ordering, Cache-Control |
| `__tests__/e2e.test.ts` | start → task chain | happy path E2E, failure path rollback, authz path |
| `__tests__/task_route.test.ts` | POST /api/build/task | dispatch, rollback event |
| `engine/__tests__/current_route.test.ts` | GET /api/engine/current | 200/404, field mapping, sentinel nulls, Cache-Control, no-auth |
| `conversations/__tests__/active_ayanamshas.test.ts` | GET …/active-ayanamshas | auth, column degradation, explicit/default source, chart_build_ayanamshas |
| `charts/__tests__/ayanamsha_status.test.ts` | GET …/ayanamsha-status | auth, chart ownership, 5-item array, canonical order, not_built, is_latest_engine |
| `clients/create/__tests__/route.test.ts` | POST /api/clients/create | auth, 422 validation, rate-limit 429, happy path, idempotency, constants |

### Integration Test File (real DB, DB-skip-guarded)

`__tests__/build.integration.test.ts` — **D-09** [BUILD-ORCH-D-09]

- 30 test cases across all 8 routes
- Requires `DB_URL` or `DATABASE_URL` env var; skipped entirely when absent
- Real PostgreSQL via `@/lib/db/client`; Firebase + Cloud Tasks + Cloud Run mocked
- Seed helpers: `seedProfile`, `seedChart`, `seedBuild`, `seedBuildSteps`, `seedEngineVersion`, `seedConversation`
- Cleanup helpers: `cleanupBuild`, `cleanupChart`, `cleanupEngineVersion`, `cleanupConversation`
- Coverage groups:
  - Route 1 (start): IT-R1-01..06 — DB row creation, 14 steps, defaults, 401/403/503, super_admin
  - Route 2 (cancel): IT-R2-01..05 — DB persist, 409 terminal, idempotent 200, 403, super_admin
  - Route 3 (active): IT-R3-01..05 — empty, progress_pct, exclusion filter, shape, Cache-Control
  - Route 4 (recent): IT-R4-01..06 — 1h window, >24h excluded, failed build, active excluded, Cache-Control, 401
  - Route 5 (engine/current): IT-R5-01..03 — metadata, no-auth, Cache-Control
  - Route 6 (active-ayanamshas): IT-R6-01..05 — J-01 degradation, 401, 404, conversation_id echo, Cache-Control
  - Route 7 (ayanamsha-status): IT-R7-01..08 — 5-item array, not_built, complete, canonical order, 401, 404, super_admin, Cache-Control
  - Route 8 (clients/create): IT-R8-01..08 — DB row creation, defaults, subset, 422/401/429, idempotency
  - Cross-route: IT-AUTH-01..02 — 401 across all auth-required routes; engine/current no-auth

---

## Status

**COMPLETE — 9/9 sessions closed**

---

## Unlocks

- **Stream H** — Constellation UI (build cockpit / progress visualization)
- **Stream I** — Notifications (build_notifications SSE event log)

Both streams depend on the 8 API routes delivered in Stream D being stable and
tested. D-stream close confirms the contract is in place.

---

## Schema Dependencies

Migrations that must be applied before the integration tests run:

| Migration | Table(s) |
|-----------|---------|
| 121 | `builds`, `build_steps` |
| 122 | `engine_versions`, `build_engine_versions` |
| 127 | `build_notifications` |
| (pre-existing) | `charts`, `pyramid_layers`, `profiles`, `conversations` |

---

*D_STREAM_CLOSE.md — authored D-09 2026-05-29*
