---
report_id: GATE-II-5-DISCOVERY
generated: 2026-05-13
generated_by: Gate II.5 W1 autonomous session (Claude Sonnet 4.6)
query_used_for_spot_checks: 5067ea2a-9d88-41ee-92a0-8e70e145b26c (2026-05-01)
---

# Gate II.5 Discovery Report

Sections §A–§F per CLAUDECODE_BRIEF §4 W1. All findings are from live DB
queries (DB host 127.0.0.1:5433, database amjis) and source-code inspection
of the `feature/gate2-trace-pipeline-align` worktree.

---

## §A — audit_events schema mismatch

### Live production columns (\d audit_events)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | uuid | NOT NULL | gen_random_uuid() |
| `query_id` | uuid | NOT NULL | — |
| `query_plan_id` | uuid | nullable | — |
| `query_text` | text | nullable | — |
| `query_class` | text | nullable | — |
| `user_id` | text | nullable | — |
| `chart_id` | uuid | nullable | — |
| `conversation_id` | uuid | nullable | — |
| `tool_bundles` | jsonb | nullable | — |
| `latency_ms` | integer | nullable | — |
| `audit_status` | text | NOT NULL | 'ok' |
| `audit_warnings` | jsonb | nullable | — |
| `created_at` | timestamptz | NOT NULL | now() |

Indexes: PRIMARY KEY on `id`; index on `created_at DESC`, `query_class`, `query_id`, `user_id`.

No `audit_event_id`, `audit_event_version`, `disclosure_tier`, `validator_verdict`,
`b10_compliant`, or `b11_compliant` columns exist.

### What loadAuditRow() currently queries

```sql
SELECT audit_event_id, audit_event_version, disclosure_tier,
       validator_verdict, b10_compliant, b11_compliant
FROM audit_events WHERE query_id = $1::uuid LIMIT 1
```

Every one of these six columns is absent from the live table. The `.catch()` in
`loadAuditRow()` silently returns `{ rows: [] }` on every production call.
`buildGrouped()` receives `auditRow = null` and falls into the
`placeholder_note: 'Audit data is not on the trace stream ...'` branch.
**Every production query's Audit step shows placeholder text, regardless of
whether an `audit_events` row exists.**

### Column-by-column mapping needed

| Assembler column | Live column | Action |
|---|---|---|
| `audit_event_id` | `id` | Rename in SELECT |
| `audit_event_version` | _(absent)_ | Omit from SELECT |
| `disclosure_tier` | _(absent)_ | ADD via migration 045 (D11) |
| `validator_verdict` | `audit_status` | Rename in SELECT; map values |
| `b10_compliant` | _(absent)_ | ADD via migration 045 (D11) |
| `b11_compliant` | _(absent)_ | ADD via migration 045 (D11) |

Also present in live table but not currently queried:
- `audit_warnings` (jsonb) — should be selected and surfaced in AuditDetail
- `query_class` — useful for AuditDetail context; optionally select

### Value-mapping note for validator_verdict

Live `audit_status` values (from production rows): `'ok'`, `'warn'`, `'block'`.
Assembler `AuditStepMetadata.validator_verdict` type is `'PASS' | 'WARN' | 'ERROR' | 'UNKNOWN'`.
W4 must map: `'ok' → 'PASS'`, `'warn' → 'WARN'`, `'block' → 'ERROR'`.

---

## §B — production stage vocabulary

### Query run

```sql
SELECT step_type, COUNT(*) AS occurrences, MIN(created_at) AS first_seen, MAX(created_at) AS last_seen
FROM query_trace_steps
WHERE created_at > NOW() - INTERVAL '14 days'
GROUP BY step_type ORDER BY occurrences DESC;
```

Result: `gcs` 3262, `llm` 2036, `deterministic` 2028, `sql` 1247, `vector` 712.

*Note: `step_type` is a technical execution type (`llm`, `gcs`, `sql`, `vector`,
`deterministic`). The logical stage name is `step_name`.*

### Observed step_name values in production (test query)

```
step_seq  step_name            step_type      parallel_group
1         classify             deterministic  —
2         compose_bundle       deterministic  —
3         plan_per_tool        llm            —
4         msr_sql              sql            tool_fetch
5         pattern_register     gcs            tool_fetch
6         remedial_codex_query gcs            tool_fetch
7         context_assembly     deterministic  —
7         chart_facts_query    gcs            tool_fetch
8         synthesis            llm            —
```

### Cross-reference with STAGE_FROM_STEP_NAME (trace/types.ts)

| step_name | Maps to PipelineStage | Status |
|---|---|---|
| `classify` | `'planner'` | ✓ correct |
| `compose_bundle` | `'planner'` | ✓ correct |
| `plan_per_tool` | **null (unmapped)** | ❌ **GAP — must add to 'planner'** |
| `<tool_name>` (parallel_group='tool_fetch') | `'retrieval'` | ✓ correct |
| `context_assembly` | `'synthesis'` | ✓ correct |
| `synthesis` | `'synthesis'` | ✓ correct |
| `citation_warn` | `'audit'` | ✓ correct |
| `citation_error` | `'audit'` | ✓ correct |

**Critical gap: `plan_per_tool` is not in `STAGE_FROM_STEP_NAME`.**
In `mapStepToStage()`, it returns `null` and the step is silently dropped from
all grouped projections. Per D9, it belongs inside the Planning container as
the third inline sub-row (after classify + compose_bundle).

### Updated STAGE_FROM_STEP_NAME (to apply in W3)

Add: `plan_per_tool: 'planner'`

---

## §C — 21-tool enumeration

### DB query

```sql
SELECT DISTINCT step_name AS tool_name, COUNT(*) AS occurrences
FROM query_trace_steps
WHERE parallel_group = 'tool_fetch' AND created_at > NOW() - INTERVAL '30 days'
GROUP BY step_name ORDER BY occurrences DESC;
```

### Result (14 tools fired in last 30 days)

| tool_name | occurrences |
|---|---|
| `msr_sql` | 1213 |
| `cgm_graph_walk` | 823 |
| `pattern_register` | 771 |
| `vector_search` | 712 |
| `resonance_register` | 597 |
| `cluster_atlas` | 259 |
| `contradiction_register` | 251 |
| `chart_facts_query` | 200 |
| `temporal` | 190 |
| `remedial_codex_query` | 117 |
| `query_msr_aggregate` | 34 |
| `divisional_query` | 20 |
| `kp_query` | 18 |
| `timeline_query` | 16 |

### Full 21-tool universe from RETRIEVAL_TOOLS registry

Source: `platform/src/lib/retrieve/index.ts` — `RETRIEVAL_TOOLS` array (21 entries).

Tools not fired in last 30 days (7): `manifest_query`, `saham_query`,
`cross_varga_dignity_query`, `domain_report_query`, `query_signal_state`,
`query_kp_ruling_planets`, `query_varshaphala`.

**Full canonical 21-tool list (in registry order):**

```typescript
export const ALL_21_RETRIEVAL_TOOLS = [
  'msr_sql',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'temporal',
  'query_msr_aggregate',
  'cgm_graph_walk',
  'manifest_query',
  'vector_search',
  'kp_query',
  'saham_query',
  'divisional_query',
  'chart_facts_query',
  'cross_varga_dignity_query',
  'domain_report_query',
  'remedial_codex_query',
  'timeline_query',
  'query_signal_state',
  'query_kp_ruling_planets',
  'query_varshaphala',
] as const
```

Per D10: all 21 always rendered in Retrieval container. Sub-rows for unfired tools
render dimmed. Per R1: no hard-coding in the renderer — sub-rows derive from
`ALL_21_RETRIEVAL_TOOLS` + the fired set.

---

## §D — per-stage metadata shapes

Confirmed from live `query_trace_steps` rows.

### classify (deterministic)

`data_summary` shape:
```typescript
interface ClassifyDataSummary {
  result: string            // query_class value (e.g. 'holistic', 'factual', 'remedial')
  confidence: number        // 0.0–1.0
  query_class: string       // same as result (promoted in B3)
  planning_confidence: number  // same as confidence (promoted in B3)
}
```

`payload`: typically `{}` (planner payload with `query_plan` and `tool_calls` in some rows).
Note: `step_name === 'classify'` is the planner LLM call. Its payload carries `query_plan`.

### compose_bundle (deterministic)

`data_summary` shape:
```typescript
interface ComposeBundleDataSummary {
  result: string  // e.g. "5 bundles · 4 tools" or "2 assets · 2 tools"
  // optional floor_enforced flag not always present
}
```

`payload`: typically `{}`.
This is the **bundle hydration** step (hydrateBundle call in route.ts). It fires
immediately after classify/planner, before tool_fetch.

### plan_per_tool (llm)

`data_summary` shape (from live rows):
```typescript
interface PlanPerToolDataSummary {
  tool_count: number      // number of tools planned
  tools_refined: number   // 0 in most production rows
  planner_active: boolean // true when planning model is active
}
```

When `planner_active: false`, `tool_count: 0` — the LLM planner was skipped
(fallback to heuristics or disabled flag). This is separate from the main
`classify` step. W3 must add `plan_per_tool: 'planner'` to STAGE_FROM_STEP_NAME.

### tool_fetch (step_name = tool registry name, parallel_group = 'tool_fetch')

`data_summary` shape varies by tool type:
```typescript
// SQL/GCS tools
interface ToolFetchDataSummary_RowBased {
  tool_name: string
  rows_returned: number
  token_estimate: number
}
// Vector tools
interface ToolFetchDataSummary_Vector {
  tool_name: string
  chunks_returned: number
  top_score?: number
  token_estimate: number
}
```

### context_assembly (deterministic)

`data_summary`:
```typescript
interface ContextAssemblyDataSummary {
  token_estimate: number
  // optional: short_circuited, reason, total_token_estimate, threshold
}
```

This step fires AFTER tool_fetch, BEFORE synthesis. Assembler currently maps it
to 'synthesis' stage (via STAGE_FROM_STEP_NAME['context_assembly'] = 'synthesis').
This mapping is correct and should be preserved.

### synthesis (llm)

`data_summary`:
```typescript
interface SynthesisDataSummary {
  model: string           // e.g. 'gemini-2.5-pro'
  temperature: number     // e.g. 0
  input_tokens: number
  output_tokens: number
  citation_count: number  // number of SIG.MSR.NNN citations
}
```

### audit_events (JOIN, not a trace step)

Live row values (from query 5067ea2a via DB inspection):
```typescript
{
  id: '73920808-7a29-4cbb-89c5-57fbda82a725',
  audit_status: 'ok',      // 'ok' | 'warn' | 'block'
  audit_warnings: null,    // jsonb array or null
  query_class: 'remedial', // matches classify step
}
// disclosure_tier, b10_compliant, b11_compliant: absent (to add via D11)
```

---

## §E — existing renderer mismatch inventory

### LifecycleGraph.tsx

| Component behavior | Expected (D9/D10) | Actual | Gap |
|---|---|---|---|
| Planner rendered as | Container with 3 inline sub-rows (classify, compose_bundle, plan_per_tool) | Single `StageNode` button | ❌ Missing sub-rows |
| plan_per_tool | Sub-row inside Planning container | Dropped (unmapped) | ❌ Never rendered |
| compose_bundle | Sub-row inside Planning container | Not individually surfaced | ❌ Not shown |
| Retrieval rendered as | Container with 21 sub-rows (7 dimmed) | Container with fired tools only (dynamic) | ❌ Missing 7 unfired sub-rows |
| Unfired tools | Rendered dimmed | Not shown | ❌ Missing |

**Key code locations:**
- [LifecycleGraph.tsx:109](platform/src/components/trace/LifecycleGraph.tsx#L109) — `plannerStep = groups.planner.find(s => s.step_name === 'classify')` — only classify used, compose_bundle and plan_per_tool ignored
- [LifecycleGraph.tsx:142-159](platform/src/components/trace/LifecycleGraph.tsx#L142) — Retrieval sub-rows rendered from fired steps only; no dim rows for unfired

### AuditDetail.tsx

| Field | Expected | Actual (assembled from DB) | Gap |
|---|---|---|---|
| `validator_verdict` | 'PASS'/'WARN'/'ERROR'/'UNKNOWN' | Always 'UNKNOWN' (loadAuditRow silently fails) | ❌ DB column is `audit_status` |
| `disclosure_tier` | string or null | null | ❌ Column doesn't exist yet (add via D11) |
| `b10_compliant` | boolean or null | null | ❌ Column doesn't exist yet (add via D11) |
| `b11_compliant` | boolean or null | null | ❌ Column doesn't exist yet (add via D11) |
| `audit_event_id` | real UUID | null | ❌ DB column is `id`, not `audit_event_id` |
| `placeholder_note` | null (when row exists) | Always populated | ❌ Because loadAuditRow returns null |

### PlannerDetail.tsx

The PlannerDetail renders `assembled.grouped.planner` (PlannerStepMetadata).
Current `buildGrouped()` in trace_assembler.ts derives planner from the `classify`
step only; `compose_bundle` provides `bundle_summary` but `plan_per_tool` is
dropped (unmapped stage). After W3 adds `plan_per_tool: 'planner'`, the assembler
will receive it in `byStage.planner[]` but will need to explicitly extract it.

### trace_schema.ts (lib/trace/types.ts)

The `PipelineStage` union currently is:
```typescript
export type PipelineStage = 'planner' | 'retrieval' | 'synthesis' | 'audit' |
  'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'
```

Per D9, the NEW taxonomy uses production-stage names directly as canonical stages:
```typescript
export type PipelineStage =
  | 'classify' | 'compose_bundle' | 'plan_per_tool'  // Planning container sub-stages
  | 'tool_fetch'                                       // Retrieval container sub-stages
  | 'synthesis' | 'audit'
  | 'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'
```

**Autonomous decision (R2):** The brief's D9 says to use production names. The
current schema uses `'planner'` and `'retrieval'` as container-level stages. W3
will ADD the new sub-stage names while preserving backward-compatible container
stages (`'planner'` → Planning container, `'retrieval'` → Retrieval container)
to avoid breaking existing consumers. The `PlannerStepMetadata` interface will
be extended with explicit `classify`, `compose_bundle`, `plan_per_tool` sub-step
metadata. See W3 for full schema update.

---

## §F — compose_bundle confirmation

### Question
Is `compose_bundle` the renamed ContextAssembly from Pipeline-Transform-S1?

### Finding: NO — they are distinct steps

**compose_bundle** (route.ts:443):
- Purpose: bundle hydration via `hydrateBundle(plan, manifest)` — builds the asset
  bundle that tool fetches will use
- Fires at step_seq 2, immediately after `classify` (planner), before `tool_fetch`
- step_type: `deterministic`
- stage: 'planner' (it's a sub-step of the planning phase)

**context_assembly** (route.ts:550):
- Purpose: pre-synthesis context assembly — assembles tool results into LLM context
- Fires at step_seq 7, AFTER all tool_fetch steps, BEFORE synthesis
- step_type: `deterministic`
- stage: 'synthesis' (correctly mapped in STAGE_FROM_STEP_NAME)
- The `CONTEXT_ASSEMBLY_ENABLED` flag was retired in Pipeline-Transform-S1, but
  the `context_assembly` trace step itself is still emitted (comment in route.ts:550
  references "UQE-9: pre-allocate context_assembly seq")

### Conclusion for governance correction (W9)

The CLOSE_REPORT §13 T2 claim that "ContextAssembly was renamed to compose_bundle
and preserved; only the feature flag was retired" is **partially incorrect**.
The accurate picture:

1. `compose_bundle` = NEW step introduced in Pipeline-Transform-S1 (bundle hydration)
2. `context_assembly` = pre-existing step, still emitted in production (pre-synthesis)
3. `CONTEXT_ASSEMBLY_ENABLED` flag was retired (the flag is gone), but the
   `context_assembly` trace step itself is still written by `single_model_strategy`
4. These are two separate stages with separate purposes

**Impact on W9:** The CURRENT_STATE_v1_0.md correction should clarify that:
- The feature flag was retired ✓
- The context_assembly step itself still fires in production ✓
- compose_bundle is a separate new step (bundle hydration), not a rename ✓

---

## Summary of changes required (input to W2–W11)

| Work Item | Key change |
|---|---|
| W2 | Migration 045: ADD `disclosure_tier TEXT`, `b10_compliant BOOLEAN`, `b11_compliant BOOLEAN` to audit_events |
| W3 | STAGE_FROM_STEP_NAME: add `plan_per_tool: 'planner'`; PipelineStage union update; AuditStepMetadata: add `audit_warnings`, rename fields to match DB; RetrievalSubTool: formalize as const array of 21 |
| W4 | loadAuditRow(): SELECT `id AS audit_event_id, audit_status AS validator_verdict, audit_warnings, disclosure_tier, b10_compliant, b11_compliant`; buildGrouped(): extract plan_per_tool sub-step from byStage.planner |
| W5 | LifecycleGraph: Planner → container with 3 inline sub-rows; Retrieval → 21 sub-rows with dimmed unfired |
| W6 | AuditDetail: add audit_warnings render; add D11 nullable columns with "—" + tooltip; fix validator_verdict → audit_status value mapping |
| W7 | HealthRail/QueryDNAPanel/RetrievalScorecard: taxonomy update for plan_per_tool |

*End of DISCOVERY_REPORT — Gate II.5 W1 — 2026-05-13*
