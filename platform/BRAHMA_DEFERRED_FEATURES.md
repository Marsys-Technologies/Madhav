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

---

## 3. Sub-C empty stubs awaiting WS-2 Brahma depth-build

**Created:** 2026-06-04, WS-0C Sub-C.

### 3a. `lib/forensic/snapshot.ts` — `getForensicSnapshot`

**What it was.** Queried `chart_facts` for planet positions, house signs, lagna, and
dasha_balance rows to build a `ForensicChart` struct displayed in the client profile
page (`clients/[id]/page.tsx`), `RasiChartSVG`, `ChartHero`, and `ProfileSideRail`.

**Current state.** The function body returns `buildAbhisekFallback()` immediately
(hardcoded canonical Abhisek chart from FORENSIC_ASTROLOGICAL_DATA_v8_0.md §4).
Consumers compile and render correctly — they display the native's chart. The stub
will serve all new clients with an empty-ish chart until WS-2.

**Rebuild trigger.** WS-2 Brahma depth-build: repoint to `ganita_positions` +
`ganita_dashas` (schema differs from `chart_facts` — fact_id/category model replaced by
typed planet/dasha rows). Parsing logic was in the original function (see git history
commit 01c32903 for the original SQL). Adapt column names.

### 3b. `lib/tools/multi_school_signal_lookup.ts` — Tool 27

**What it was.** Queried `school_signal_coverage JOIN l25_msr_signals JOIN classical_chunks`
to report per-school (Parashari/Jaimini/Tajika/KP/Nadi/BNN/Yogini) signal coverage with
attribution references. Full implementation shipped M9-D-S1 (2026-05-14).

**Current state.** Returns `{ results_by_school: [], total_signals_found: 0, ... }`.
Exported from `lib/tools/index.ts` (CLASSICAL_TOOL_REGISTRY tool 27). Any query routed
to this tool gets an empty multi-school result — planner should fall through gracefully.

**Rebuild trigger.** WS-2 Brahma depth-build: repopulate `school_signal_coverage` JOIN
`bodha_signals` (replaces `l25_msr_signals`). SQL prototype in git history at 01c32903.
