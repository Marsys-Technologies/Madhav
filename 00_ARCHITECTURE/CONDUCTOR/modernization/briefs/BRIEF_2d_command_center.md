---
status: COMPLETE
unit: 2d
wave: 2
title: Command Center scaffold — runtime gate + data-source control plane
stream: C
worktree: ../MadhavStreamC
blockedBy: [naming_ci]
on_red: rollback
---

## Context (self-contained)
Behaviour is governed today by scattered `MARSYS_FLAG_*` env constants + hardcoded thresholds + `STACK_ROUTING`.
Target (MASTER_PLAN §8): a DB-backed control plane surfaced as a super-admin-only **Command Center** tab in the
Cockpit, governing all gate classes at runtime — no redeploy. This unit builds the substrate + the tab shell;
deeper wiring of individual gates follows as their owning units land.

## Scope
- **`gate_registry`** (static catalogue in code): per controllable gate `{key, class, scope, value_type,
  default, description, hot_reload, danger}`. Classes: feature_flag · pipeline_threshold · model_routing ·
  access_capability · **data_source**.
- **`runtime_config`** table + **`gate_change_log`** table; extend `configService` to read `runtime_config`
  (cached, invalidated on write) with the env/code value as bootstrap default — establishing the **single flag
  source** (retire the second `getFlag` key set with no `MARSYS_FLAG_` mirror).
- **Command Center tab** under Cockpit: super-admin-only (`requireSuperAdmin` on page + API); lists gates by
  class; edit → writes `runtime_config` + `gate_change_log`; `danger:true` needs a confirm; "reset to default".
- **Data-source controls (the §8.4 + your data-source requirement):** every data asset (FORENSIC, MSR, CDLM,
  CGM, RM, UCN, **LEL**, panchanga, classical T0, ephemeris) gets an enable/disable that disables its dependent
  retrieval tools via the manifest `data_dependency` graph — enforced at the gateway/registry, not cosmetic.
  **LEL** carries the serve-time-only + build-exclusion rule; per-query LEL toggle subordinate to this global switch.
- **Ayanamsha-source controls (NEW):** surface the `ayanamsha_registry` (canonical/kp/reference) as a
  data-source class so the super-admin can see/govern which ayanamsha roles are active — read-only display is
  enough for now; do not allow disabling `canonical`.
- **Multi-tenant:** add the chart/guest dropdown to the cockpit; per-chart-scoped gates edit under the selected chart.

## Acceptance criteria (all automated)
1. `configService` reads `runtime_config` with env fallback; existing `getFlag` callers unchanged (test).
2. Command Center page + API are super-admin-only (401/403 for guest — mount test, not prop-injection).
3. A data-source toggle flips a `runtime_config` row and the dependent tools report disabled via `data_coverage`.
4. LEL switch OFF makes LEL unavailable to synthesis for all charts; gate_change_log records every edit.
5. Ayanamsha registry renders in the Command Center; `canonical` cannot be disabled (guard test).

## must_not_touch
`platform/python-sidecar/**` (engine), the charts table (2c owns), `platform/src/lib/contract/**` (2b owns),
the `l25_*` data-build tables (2a owns).

## Commit cadence / rollback
Commits: (1) gate_registry + runtime_config/gate_change_log migration + configService extension, (2) Command
Center tab + data-source/LEL/ayanamsha controls, (3) multi-tenant dropdown + tests. Rollback = revert; env
defaults keep behaviour identical if runtime_config is empty.
