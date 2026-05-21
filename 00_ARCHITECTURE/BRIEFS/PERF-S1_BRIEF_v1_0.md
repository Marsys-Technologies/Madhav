---
brief_id: PERF-S1
version: 1.0
status: EXECUTING
authored: 2026-05-21
session: PERF-S1
audit_ref: "CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md §H.1"
branch: feature/m5-coverage-remediation
---

# PERF-S1 Brief — Performance Tab Wiring Fixes and Metric Correctness

## Mission

Resolve the six wiring defects in §D.2 of the Capability Coverage and Performance Audit. These
defects cause the Performance tab to display incorrect or misleading metrics; this session
corrects each one with minimal surface area.

## Scope

**may_touch:**
- `platform/src/lib/performance/compliance.ts`
- `platform/src/lib/performance/ingestion.ts`
- `platform/src/lib/performance/kpi_aggregator.ts`
- `platform/src/components/performance/PerformanceClient.tsx`
- `platform/supabase/migrations/` (new migration 069 additions — compose_bundle_latency_ms,
  retrieval_scores jsonb, latency_complete boolean)
- `platform/src/lib/performance/__tests__/compliance.test.ts`
- `platform/src/lib/performance/__tests__/ingestion.test.ts`

**must_not_touch:**
- `platform/src/app/**`
- `platform/src/lib/pipeline/**`
- `platform/src/lib/retrieve/index.ts` (read-only reference)
- `platform/src/lib/retrieve/types.ts` (read-only reference)
- Any file not in the performance module, migration folder, or performance tests

## Six Defects Being Fixed

### (a) B.11 compliance — hardcoded 8-tool list in compliance.ts

**Defect:** `L2_5_TOOLS` set hardcodes 8 tool names. The `inferLayer()` function in
`platform/src/app/api/chat/consume/route.ts` already has 10 tools and has diverged.
Post-M9 additions (`multi_school_signal_lookup`, `convergence_score_lookup`) are missing;
post-M3 additions from the audit spec (`query_signal_state`, `query_kp_ruling_planets`,
`query_varshaphala`, `cross_varga_dignity_query`) are also absent.

**Fix:** The `RetrievalTool` type (from `platform/src/lib/retrieve/types.ts`) has no
`inferLayer` field, so a runtime filter against `RETRIEVAL_TOOLS[]` is not structurally
possible. Instead, expand the hardcoded set to include all missing tools, and add a
comment linking back to `route.ts:inferLayer()` as the single source of truth that
this set must be kept in sync with. Tools added: `multi_school_signal_lookup`,
`convergence_score_lookup`, `query_signal_state`, `query_kp_ruling_planets`,
`query_varshaphala`, `cross_varga_dignity_query`.

### (b) Per-tool top-score capture — retrieval_scores jsonb

**Defect:** `RETRIEVAL_TOP_SCORE_TOOLS = new Set(['vector_search'])` captures top-1 score
only for vector_search, discarding signal quality data from all other 29 tools.

**Fix:** Add `retrieval_scores jsonb` column to `performance_queries` (new migration).
Change ingestion to capture `tool_name → top_score` across all tools with a meaningful
score. Keep `retrieval_score_top1` column for backwards compatibility (nothing reads it in
`kpi_aggregator.ts` but the column is in the schema).

### (c) compose_bundle stage latency

**Defect:** `compose_bundle` stage latency is available in `route.ts` (as `composeBundleMs`)
but is not threaded through to `ConsumePerformanceInput`, so the performance log has no record
of bundle-assembly time.

**Fix:** Add `compose_bundle_latency_ms integer` nullable column (new migration). Add the
field as an optional property on `ConsumePerformanceInput` and wire it into the INSERT. Column
is nullable — most existing rows will be null; rows from the updated consume path will populate.
The audit consumer (`consumer.ts`) does not have access to `composeBundleMs`; add a TODO
noting that threading this value requires a route.ts change (out of PERF-S1 scope per
`must_not_touch`).

### (d) Null latency preservation + latency_complete flag

**Defect:** `ingestion.ts` line 63 uses `Number.isFinite(synthesisLatencyMs) ? synthesisLatencyMs : 0`
for `totalLatencyMs`, silently turning an invalid timestamp difference into 0. This makes the
dashboard show 0 ms instead of surfacing the incomplete data.

**Fix:** Add `latency_complete boolean default true` column (new migration). Preserve null when
timestamps are invalid; set `latency_complete: false` for those rows. The INSERT now passes null
for `latency_total_ms` and `false` for `latency_complete` when synthesis timestamps are missing or
non-finite. Existing rows inherit `default true` from the migration default, which is correct
(they were inserted with computed totals, even if some were 0).

### (e) Citation rate — regex heuristic

**Defect:** `parseCitations()` uses a regex on `(→ ...)` markers in synthesis text. The R7
footnote citation format (`[^N]`) is not matched. `query_trace_steps` has `step_name`,
`data_summary` JSONB, and `payload` JSONB but no discrete citation-count column.

**Fix:** The regex heuristic is retained for now — there is no clean path to a record-driven
count without either (a) a new column in `query_trace_steps` or (b) a join on `payload` JSONB
which is fragile. Add a prominent TODO comment citing this defect and the prerequisite
(`query_trace_steps` needs a `citation_count` column populated by the consume path; candidate
for PERF-S4). The R7 footnote format `[^N]` is added to the regex so at least GFM footnote
citations are captured.

### (f) Honest "live" indicator in PerformanceClient.tsx

**Defect:** The static `<span>live</span>` badge in the header does not tell the operator
when the data was last fetched. The query refetches every 45 seconds but the UI shows "live"
unconditionally (except when `isFetching`).

**Fix:** Track `lastFetchedAt` as a React ref updated on each successful fetch via
`useQuery`'s `onSuccess` / data change detection. Render "Updated Xs ago" calculated from
the difference between now and `lastFetchedAt`, refreshed every 10 seconds with a local
interval. Falls back to "never" before the first successful fetch.

## Acceptance Criteria

- [ ] `L2_5_TOOLS` set contains ≥ 14 tools (original 8 + 6 additions)
- [ ] `multi_school_signal_lookup` and `convergence_score_lookup` are in the set (matching route.ts)
- [ ] New migration file `069_performance_wiring_fixes.sql` (or next available number) adds three
  columns: `retrieval_scores jsonb`, `compose_bundle_latency_ms integer`, `latency_complete boolean default true`
- [ ] Ingestion populates `retrieval_scores` as a JSON object across all tools with non-null scores
- [ ] `latency_complete` is `false` when synthesis timestamps produce non-finite latency
- [ ] `null` is preserved for `latency_total_ms` in incomplete rows (not coerced to 0)
- [ ] `parseCitations()` regex extended to also match GFM `[^N]` footnote citations
- [ ] PerformanceClient.tsx shows "Updated Xs ago" instead of static "live"
- [ ] All existing compliance.test.ts and ingestion.test.ts tests pass without modification
- [ ] `npx tsc --noEmit` exits 0
- [ ] `npx vitest run` exits 0 (all tests)

## Migration Naming

Next available migration number in `platform/supabase/migrations/` is 069 (last seen: 068).
File: `069_performance_wiring_fixes.sql`

## Out of Scope

- Threading `composeBundleMs` from route.ts into the audit consumer (requires touching `must_not_touch` files)
- Replacing the citation heuristic with a DB join (requires a new `query_trace_steps` column)
- Any PERF-S2, PERF-S3, PERF-S4 UI sections

## Changelog

- v1.0 (2026-05-21): Initial brief for PERF-S1 session.
