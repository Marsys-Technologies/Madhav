# Brahma Deferred Features

Features removed from the platform during WS-0 / WS-0B / WS-0C because their backing
tables were dropped. Each section records what was removed, why, and the rebuild trigger.

---

## 1. AIOps LLM-health observability surface

**Removed:** 2026-06-04, WS-0B hot-patch.

**What it was.** The LLM health prober (`lib/aiops/health/`), probe route
(`/api/admin/aiops/probe`), health route (`/api/admin/aiops/health`), and health-summary
route (`/api/admin/aiops/health/summary`) that polled `llm_model_health` for per-model
pass/fail/timeout status. Backed by migrations 046–052.

**Why removed.** WS-0 dropped `llm_model_health`. The prober had been silently broken with
no observable production impact. Native disposition: Option A — delete rather than restore
and stub.

**Where it goes.** Rebuild under Mīmāṃsā/L5 as the LLM-quality calibration concern. Do not
resurrect piecemeal; build it fresh alongside the param/routing override surfaces (section 2).

**Rebuild trigger.** When Mīmāṃsā/L5 work begins.

---

## 2. AIOps LLM stack-routing override + config audit + param override admin surface

**Removed:** 2026-06-04, WS-0C Sub-B.

**What it was.** The full AIOps Control Panel:
- Admin routes: `/api/admin/aiops/routing`, `/api/admin/aiops/params`,
  `/api/admin/aiops/audit`, `/api/admin/aiops/state`, `/api/admin/aiops/stack`,
  `/api/admin/aiops/smoke`, `/api/admin/aiops/catalog`
- UI: `(super-admin)/aiops/control/page.tsx` + `AiopsTabs`, `AuditRail`, and 16 other
  components under `lib/components/aiops/`
- Library: `lib/aiops/` (health, catalog, probe, specs subdirectories)
- Schema types: `LlmStackRoutingOverrideRow`, `LlmParamOverrideRow`, `LlmConfigAuditRow`,
  `AiopsModelHealthStatus`, `LlmModelHealthRow`, `LlmCatalogSnapshotRow` removed from
  `lib/db/schema/aiops.ts`

Backed by tables `llm_stack_routing_override`, `llm_config_audit`, `llm_param_override`,
`llm_model_health`, `llm_catalog_snapshot` (all dropped in WS-0).

The runtime model-resolver (`lib/models/runtime_config.ts`) previously read routing/param
overrides from DB as priority-2 in a 3-level cascade (header → DB → static registry).
Sub-B removed the DB queries; the resolver now uses a 2-level cascade (header → static
registry). `invalidateRuntimeConfigCache()` retained for future use.

**Why removed.** All backing tables dropped in WS-0; the surface had been silently broken
for days with no observable production impact. Same Option-A disposition as section 1.
Reverse-citation gate: no scheduler, Cloud Run Job, or live non-admin imports found.

**Where it goes.** Rebuild alongside section 1 under Mīmāṃsā/L5 as the LLM-quality
calibration concern. Single rebuild for both AIOps surfaces; do not resurrect either
piecemeal.

**Rebuild trigger.** When Mīmāṃsā/L5 work begins.
