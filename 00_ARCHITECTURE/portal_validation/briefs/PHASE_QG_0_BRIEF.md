---
status: OPEN
session_id: PIV_QG_0
phase: QG.0
phase_name: "Portal inventory + integration map + M1–M10 deliverable catalog"
next_session: PIV_QG_1
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_0
## Portal Integration Validation, Step 0 — Inventory + Map

---

## §0 — Executor orientation

QG.0 is doc-only. No code, no live LLM calls. Produces the foundational
artifact that the remaining 8 sub-phases reference: a complete map of
what's in the portal, where the integration seams live, and what every
M1–M10 macro-phase contributed.

Read `00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md`
fully before starting.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md (the M1–M10 arc)
5. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (active state)
6. 00_ARCHITECTURE/CAPABILITY_MANIFEST.json (catalog of every artifact)
7. M-close sealing artifacts (read each that exists):
     00_ARCHITECTURE/M2_CLOSE_v1_0.md
     00_ARCHITECTURE/M3_CLOSE_v1_0.md
     06_LEARNING_LAYER/M4_CLOSE_v1_0.md
     06_LEARNING_LAYER/M5_CLOSE_v1_0.md
     M6/M8/M9 close artifacts (locate via CAPABILITY_MANIFEST or grep)
8. 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ — LL.1 weights
9. 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md (or latest MSR — 573 signals expected)
10. platform/src/lib/pipeline/** (bundle_hydrator, planner, manifest)
11. platform/src/lib/adapters/** (Phase 2)
12. platform/src/components/consume/** (Phase 3)
13. platform/src/lib/db/schema/** (every audit/log table)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/PORTAL_INVENTORY.md   # NEW — the main deliverable
00_ARCHITECTURE/portal_validation/QG0_M_MODULE_MAP.md   # NEW — per-module deliverable matrix
CLAUDECODE_BRIEF.md
```

### must_not_touch
- Everything outside may_touch. PIV is read-only on application code, data, and all other governance.

---

## §3 — Work plan

### 3.1 — PORTAL_INVENTORY.md

Author with these sections:

**§1 — Component tree.** Walk `platform/src/` and `platform/scripts/` and
produce a structured listing of:
- API routes (under `app/api/`)
- UI surfaces (under `app/(...)/` and `components/`)
- Lib modules (under `lib/`)
- Scripts (under `scripts/`)
Group by area (synthesis, retrieval, adapters, aiops, observatory, etc.).
For each area, one sentence describing its purpose.

**§2 — Integration seams.** Tabulate the seven seams from the master plan
§1, but with concrete file paths:

| Seam | Source | Sink | Files at the boundary |
|---|---|---|---|
| AIOps config → runtime | `/api/admin/aiops/stack` | `runtime_config.ts` | …list… |
| runtime_config → adapter | `runtime_config.ts` | `adapters/dispatcher.ts` | …list… |
| adapter → provider | `adapters/providers/adapter_<p>.ts` | `lib/llm/providers/<p>_observed.ts` | … |
| adapter events → UI | `streamAdapter` events | `useChatLifecycle` hook | … |
| M1–M10 → context bundle | various data sources | `bundle_hydrator.ts` | … |
| Query path → audit | `consume/route.ts` + adapters | `audit_events` + `llm_usage_events` + `query_trace_steps` tables | … |
| Audit tables → Observatory | DB tables | `/observatory/**` | … |

**§3 — Audit + observability surfaces.** Tabulate every DB table the
query pipeline writes to. For each: schema location, writer module, reader
module(s), purpose.

```
| Table | Schema | Writer | Reader(s) | Purpose |
|---|---|---|---|---|
| audit_events | …                | … | Observatory + replay | Per-stage pipeline events |
| llm_usage_events | …            | …observed wrappers | Observatory cost dashboards | Token + cost telemetry |
| query_trace_steps | mig 040    | trace writer | /trace UI | Lifecycle steps for /trace |
| llm_stack_config | mig 046     | aiops PUT /stack | runtime_config | Active stack pointer |
| llm_stack_routing_override | mig 047 | aiops PUT /routing | runtime_config | Per-(stack, call_type) routing |
| llm_param_override | mig 048   | aiops PUT /params | runtime_config | Per-param override |
| llm_model_health | mig 049     | probe runner | aiops UI | Per-model health pip |
| llm_config_audit | mig 050     | aiops endpoints | aiops audit rail + Observatory | Config change log |
| llm_catalog_snapshot | mig 051 | catalog cache | UI dropdowns | Provider catalog history |
| audit_events | mig 011/045    | synthesis | replay + Observatory | Held-out-sacrosanct audit |
| (others?)            | …          | … | … | Discover and add |
```

Discover the full list by grepping for `INSERT INTO`, `await query(`,
schema file names. Include both Phase 1 (mig 046–052) and pre-existing
audit tables.

**§4 — Feature flag inventory.** Every entry in `feature_flags.ts`'s
`FeatureFlag` union + `DEFAULT_FLAGS` record. Per flag: name, default
value, current production value (from gcloud Cloud Run env), purpose,
who flips it.

**§5 — Worktrees.** Output of `git worktree list` plus a one-line note
on each.

### 3.2 — QG0_M_MODULE_MAP.md

For each macro-phase M1 through M10:

```
## M<N> — <Name>

### Status
- Closed: <Y/N>, closing artifact: <path>
- Production-active: <Y/N>

### Deliverables
- <data artifact 1>: <path> (e.g., MSR_v5_0.md at 025_HOLISTIC_SYNTHESIS/)
- <data artifact 2>: …
- <code module>: <path>
- <DB schema>: <migration N>

### Expected consumer in the query pipeline
- <Component/path that should read or invoke this deliverable>
- <Specific seam>

### Validation hypothesis (for QG.3 to test)
- "If M<N> is wired correctly, then ... <observable behavior>"
- e.g., "If MSR v5.0 is wired, then bundle_hydrator should attach a bundle with
  573 signals when invoked. If still pulling v4.0, only 543 signals."

### Open question for QG.3
- <what QG.3 needs to verify>
```

Cover all 10 even if some are "not yet active in pipeline" (e.g., M10
acharya panel may still be future scope).

### 3.3 — Sanity check

After authoring, walk the doc and ensure:
- Every M-phase has an entry (even if "not yet integrated")
- Every audit table has a writer + reader column populated
- Every feature flag has a current-production-value column
- No fictional paths — every file path cited must exist

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG0.1 | PORTAL_INVENTORY.md exists with §1–§5 populated | grep section headers |
| AC.QG0.2 | All audit tables present in §3 (≥10) | row count |
| AC.QG0.3 | All feature flags present in §4 (≥6) | row count |
| AC.QG0.4 | QG0_M_MODULE_MAP.md has entries for M1 through M10 | grep "## M" |
| AC.QG0.5 | Every M-module has a validation hypothesis | grep "Validation hypothesis" |
| AC.QG0.6 | No fictional paths (every cited file exists) | spot-check 10 paths |
| AC.QG0.7 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
docs(piv-QG.0): portal inventory + M1–M10 module map

- PORTAL_INVENTORY.md: component tree, integration seams (7), audit
  surfaces, feature flags, worktrees.
- QG0_M_MODULE_MAP.md: per-macro-phase deliverables + expected pipeline
  consumers + validation hypotheses for QG.3.
- No code changes; PIV is audit-only.

AC summary: 7/7 PASS
```

Rotate `CLAUDECODE_BRIEF.md` → `PHASE_QG_1_BRIEF.md`.

---

## §6 — BAIL OUT

- M-close sealing artifacts unfindable (e.g., M8_CLOSE doesn't exist as expected) — bail and report which.
- An expected audit table doesn't exist in the DB schema files — bail with table name.

---

*End of PHASE_QG_0_BRIEF.md*
