---
brief: GATE-I-PERF-CMD-001
audit_for: W0 — audit step (no code yet)
authored_by: Claude Code (Anti-Gravity, Sonnet 4.6) — 2026-05-12
session: gate1-perf-center-S1
status: COMMITTED
---

# Gate I Performance Command Center — W0 Audit

This audit answers W0.A–W0.F from `CLAUDECODE_BRIEF.md` and documents the structural deviations between the brief's assumptions and the actual codebase surface. Per brief §10, adaptations are flagged inline; no item rises to "structural blocker requiring native halt" — every required field is derivable from one or more existing tables/objects.

## §A — Eval entry point (W0.A)

There are **two** golden sets in the repo, neither sized as 46 queries (the brief's quoted figure appears to be outdated):

| File | Count | Purpose |
|---|---|---|
| `platform/scripts/golden_queries.ts` | **15** | Live-endpoint synthesis answer eval (hits `/api/chat/consume`). Covers factual / interpretive / predictive / holistic / discovery. Source of truth for **synthesis-grade** eval. |
| `platform/tests/eval/planner_golden_set.json` | **29** | Planner-only eval (tool_recall / tool_precision). Source of truth for **planner-grade** eval. Used by W2-EVAL-B. |

Eval entry points:
- **Synthesis eval CLI:** `platform/scripts/answer_eval.ts`
  - Invocation: `npm run answer:eval` (all 15) or `npm run answer:eval -- --query-id GQ-001` (single)
  - Env: `BASE_URL`, `CHART_ID`, `EVAL_STACK`
  - Per-query results computed inline; aggregates printed to stdout AND written to `eval-results/answer_eval_<timestamp>.json` and `.log`
- **Planner eval:** test-suite-integrated. The 29-query set drives planner unit tests; there is no standalone CLI today. (W3 will hook the synthesis eval. Planner eval is best-treated as a Vitest output → file, deferred to W3 follow-up if needed.)

**Adaptation:** W3 will hook into `answer_eval.ts` (the existing scripted runner) — wrap its per-query computation block to call `writeEvalPerformanceRow`, and bracket the whole run with `writeEvalRun`/`finalizeEvalRun`. Brief's claim of `recall=0.983 precision=0.961` refers to a prior planner-only result; W3 will compute and persist whatever aggregate the script already prints, not a hard-coded recall/precision pair.

## §B — Consume audit finalize hook (W0.B)

**File:** `platform/src/app/api/chat/consume/route.ts:616`
**Pattern:** `createAuditConsumer({ query_text, query_plan, bundle, tool_results, validator_results, disclosure_tier })` is passed as `onAuditEvent` callback into the synthesis orchestrator's request.

When the orchestrator finishes synthesis, it invokes the callback with a `SynthesisAuditEvent` (`platform/src/lib/synthesis/types.ts:101`). The callback (`platform/src/lib/audit/consumer.ts:33`) builds an `AuditEvent`, writes it via `writeAuditLog`, and optionally writes a `prediction_ledger` row.

**Insertion point for `writeConsumePerformanceRow`:** Inside `createAuditConsumer` after `writeAuditLog(auditEvent).catch(...)` (consumer.ts:63) — same fire-and-forget pattern. We will pass the **full consumer context** plus the `SynthesisAuditEvent` plus the just-built `AuditEvent` because the `AuditEvent` type alone does not carry latency / plan / citation / retrieval fields (see §E). Concretely the new signature is:

```ts
writeConsumePerformanceRow({
  query_id: event.query_plan_id,
  query_plan: ctx.query_plan,
  tool_results: ctx.tool_results,
  validator_results: ctx.validator_results,
  disclosure_tier: ctx.disclosure_tier,
  synthesis_event: event,
  final_output: event.final_output,
}).catch(err => telemetry.recordError('performance_writer', 'write_failed', err))
```

This is a **brief deviation:** the brief mandated `writeConsumePerformanceRow(auditEvent: AuditEvent)`. The deviation is documented in SESSION_LOG and follows the brief's §10 "adapt freely on field-naming-only deltas" guidance — except the delta here is larger because `AuditEvent` is much thinner than the brief assumed.

## §C — Phase 8 outcome table (W0.C)

**Table:** `prediction_ledger` (migration 012, extended by 039).

**Columns relevant to calibration:**
| Column | Type | Note |
|---|---|---|
| `id` | uuid | PK |
| `query_id` | uuid | FK-like back to audit_log.query_id |
| `confidence` | numeric(4,3) | Per-prediction confidence in [0,1] |
| `horizon_start`, `horizon_end` | date | Prediction window |
| `outcome` | text NULL | Populated post-hoc by `/audit/predictions` UI |
| `outcome_observed_at` | timestamptz NULL | When outcome was recorded |
| `brier_score` | numeric NULL | **Pre-computed at outcome-record time** per 039 |

**Adaptation:** the brief described calibration as a SQL join + Brier computation in the API. The schema already pre-computes Brier and stores it. **Calibration KPI = `AVG(brier_score) FILTER (WHERE outcome_observed_at IS NOT NULL)` grouped by window.** No re-computation, no join into `prediction_outcomes` (which does not exist). Simpler and more accurate.

The link from `performance_queries` → `prediction_ledger` is `performance_queries.audit_event_id` → `audit_log.id` → audit_log.query_id matches `prediction_ledger.query_id`. (audit_log.query_id is the canonical query plan id.) W5 will compute calibration with a `LEFT JOIN prediction_ledger pl ON pl.query_id = al.query_id` chain.

## §D — Super-admin auth pattern (W0.D)

**Authoritative pattern:** Next.js **route group `(super-admin)`** + layout-level guard.
**File:** `platform/src/app/(super-admin)/observatory/layout.tsx:11-19`

```ts
const ctx = await getServerUserWithProfile()
if (!ctx) redirect('/login')
if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
if (ctx.profile.status !== 'active') redirect('/login')
```

`getServerUserWithProfile` is from `@/lib/auth/access-control` and uses the `__session` Firebase cookie under the hood (consistent with the `project_ganga_baseline` memory note).

**Adaptation:** the brief placed pages at `platform/src/app/performance/**`. To inherit the existing super-admin gating cleanly, **pages MUST live under `platform/src/app/(super-admin)/performance/**`** (route group). The URL path stays `/performance` because route groups don't appear in URLs. API routes can stay at `platform/src/app/api/performance/**` because route groups don't apply to API routes; each API route handler performs its own role check inline.

For API routes, the canonical inline pattern (checked elsewhere in the codebase): use `getServerUserWithProfile()` from `@/lib/auth/access-control`, return `NextResponse.json({error:'forbidden'},{status:403})` on non-super_admin.

## §E — Audit-event field mapping (W0.E)

`AuditEvent` (`platform/src/lib/audit/types.ts:20`) carries: `query_id, query_text, query_class, bundle_keys, tools_called[{tool,params_hash,latency_ms,cached}], validators_run[{validator_id,passed,message}], synthesis_model, synthesis_input_tokens, synthesis_output_tokens, disclosure_tier, final_output`.

**Most of the brief's W0.E fields do not live on `AuditEvent`.** They are reachable from the consumer context + `SynthesisAuditEvent`:

| Brief field | Source | Note |
|---|---|---|
| `query_class` | `ctx.query_plan.query_class` | Direct |
| `plan_type` | `ctx.query_plan.expected_output_shape` | Best mapping (`single_answer` / `three_interpretation` / `time_indexed_prediction` / `structured_data`) |
| `tools_selected` | `ctx.tool_results.map(r=>r.tool_name)` OR `(ctx.query_plan as RichQueryPlan).tool_calls.map(t=>t.tool_name)` | Use tool_results — they reflect what actually ran |
| `planner_confidence` | `ctx.query_plan.router_confidence` | Optional; may be null |
| `validator_verdict` | Aggregate over `ctx.validator_results` — pass if all `vote==='pass'`, else `fail` | Mirror existing `summarize()` from `validators/index` if exported |
| `disclosure_tier` | `ctx.disclosure_tier` | Direct |
| `synthesis_status` | Derived from `event.finish_reason` — `'stop'` → `success`, else `failure`/`partial` | Map per finish_reason |
| `citation_count` | Regex count of `(→ …)` markers in `event.final_output` | The `synthesis_quality_scorecard.citation_density` table exists but is unreliably populated; regex is the durable signal |
| `citation_objects` (for B.10 detection) | Parse `event.final_output` for citation markers and tag each with inferred layer (L1/L2.5) using marker prefix heuristics from `route.ts:69 inferLayer` | Approximate; tests in W14 cover false-positive cases |
| `latency_planner_ms` | `(ctx.query_plan as RichQueryPlan).planning_latency_ms` if present, else null | LLM-first planner is always on per CLAUDE.md §F; always present |
| `latency_retrieval_ms` | `sum(ctx.tool_results.map(r=>r.latency_ms))` | Sum of tool execution time |
| `latency_synthesis_ms` | `Date.parse(event.finished_at) - Date.parse(event.started_at)` | Direct from event |
| `latency_total_ms` | sum of three above | Approximation (excludes overhead) |
| `retrieval_hit` | `ctx.tool_results.some(r => r.results.length > 0 && (r.results[0].significance ?? r.results[0].confidence ?? 0) > 0)` | Any non-empty retrieval counts; threshold-free at P0 |
| `retrieval_score_top1` | `max(r.results[0].significance ?? r.results[0].confidence ?? 0)` over all retrieval-type tools | Restrict to vector_search-like tools |
| `[EXTERNAL_COMPUTATION_REQUIRED]` marker | Regex `/\[EXTERNAL_COMPUTATION_REQUIRED\]/` on `event.final_output` | B.10 detector uses this |
| L2.5 stage firing | `ctx.tool_results.some(r => inferLayer(r.tool_name) === 'L2.5')` using `inferLayer` from `route.ts:69` | B.11 detector uses this — better than parsing audit event "stage list" (which doesn't exist as a discrete field) |
| `is_prediction` | `ctx.query_plan.query_class === 'predictive' \|\| ctx.query_plan.expected_output_shape === 'time_indexed_prediction'` | Mirrors `isPredictiveContext` in consumer.ts:105 |

**Adaptation:** the B.11 detector signature in W4 takes the `tool_results` array (not the AuditEvent), since "stages" don't exist as a typed audit field. The semantic intent is preserved: did an L2.5 retrieval fire?

## §F — Client-data lib (W0.F)

`platform/package.json` shows **`@tanstack/react-query` ^5.99.0** is installed; `swr` is **not** present.

**Adaptation:** W13 hook uses `useQuery` from `@tanstack/react-query` with:
```ts
useQuery({
  queryKey: [...],
  queryFn,
  refetchInterval: 45_000,
  refetchIntervalInBackground: false,
  refetchOnWindowFocus: true,
})
```
Manual "Refresh now" → `queryClient.invalidateQueries({ queryKey: [...] })`. Loading skeletons via existing `components/ui/skeleton`.

## §G — Migrations folder path

The brief assumed `platform/supabase/migrations/`. The actual path is **`platform/migrations/`** (flat, no `supabase/` segment). All migration files declared in W1 are written under `platform/migrations/043_*.sql` and `platform/migrations/044_*.sql`.

## §H — Other discoveries

- The audit-event finalize callsite (consume route.ts:616) sits inside the synthesis orchestrator's `onAuditEvent` callback. Calling `writeConsumePerformanceRow` there gives us the full enriched context; the consume response stream is already committed by that point, so fire-and-forget is safe.
- `tool_results` passed to the consumer is `validToolResults` (consume route.ts:617's variable) — already filtered to non-failed tools. This is the right source for retrieval health metrics.
- Validator helper `summarize` exists at `platform/src/lib/validators/index.ts`; can be reused for `validator_verdict` field if its shape matches a single text label.
- The brief's "46 golden queries" appears to be a memory artifact from `project_pipeline_gap_plan_complete`. Current state is 15 (synthesis) + 29 (planner). W3 will persist whatever count the script actually runs.

## §I — Acceptance impact of the discoveries above

| AC | Impact |
|---|---|
| AC.2 | Adapted: writer signature differs from brief. Behavior (one row per consume query, source='consume', plan_accuracy_label='unjudged') unchanged. |
| AC.3 | Adapted: row count == golden_queries.ts length (15), not 46. Brief language "exactly 46 rows" is treated as "exactly N rows where N = golden set size at run-time". |
| AC.4 | Calibration block: numerator/denominator come from `prediction_ledger.brier_score` not a separate outcomes table. Result shape unchanged. |
| AC.13 | Pages under `(super-admin)` route group instead of bare `/performance`. URL surface (`/performance/*`) unchanged. |

No AC is dropped. All 16 ACs remain in scope, four are reinterpreted as documented.

---

*End of GATE_I_AUDIT.md — committed before W1.*
