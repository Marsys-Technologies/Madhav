---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P1-S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P1-S1
---

# CLAUDECODE_BRIEF — TR-P1-S1
## Phase 1.1 + 1.2: chart_summary envelope fix + query_transit_event event_type schema

## §0 — Start

You are in /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix on branch feature/tooling-remediation.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean before starting
```

## §1 — Scope

may_touch: platform-mcp/src/tools/chart_summary.ts, platform-mcp/src/tools/query_transit_event.ts, platform-mcp/src/tools/chart_summary.test.ts, platform-mcp/src/tools/query_transit_event.test.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

## §2 — Task

### Phase 0 findings that update this brief

Phase 0 (TR-P0-S1) determined:

**C1 — chart_summary:** Bug is in the **MCP wrapper**, not the platform primitive.
The wrapper calls `callPlatformPrimitive` which returns a `ToolBundle` envelope. The wrapper then reads `envelope.result.rows_by_category` directly, but the actual data is at `results[0].content` which is a serialised JSON string that must be parsed. The primitive itself is correct.

**C6 — query_transit_event:** Bug is in the **MCP wrapper** schema. `event_type` is a required parameter consumed by the underlying engine but is not declared in the MCP input schema, so callers never send it and the engine receives `undefined`.

---

### 2.1 — Fix chart_summary (C1)

File: `platform-mcp/src/tools/chart_summary.ts`

1. Read the file fully to understand the current `callPlatformPrimitive` invocation and how the result is unwrapped.
2. Find where the response is read after `callPlatformPrimitive` returns. The bug: code reads `result.rows_by_category` or similar directly off the envelope top level.
3. Fix: the `ToolBundle` envelope from `callPlatformPrimitive` returns `{ results: [{ content: "<JSON string>", ... }] }`. Unwrap by:
   ```typescript
   const raw = await callPlatformPrimitive(...);
   const content = raw?.results?.[0]?.content;
   const parsed = typeof content === 'string' ? JSON.parse(content) : content;
   // now read parsed.rows_by_category or parsed.summary etc.
   ```
4. If the structure differs slightly from above, read the actual runtime shape from the Phase 0 baseline at `eval-results/tooling_audit_baseline_20260524.json` key `tool_tests.C1_chart_summary.error_shape` to understand what the wrapper currently receives.
5. After fix, the tool must return a non-empty `rows_by_category` object for `chart_id: "362f9f17-95a5-490b-a5a7-027d3e0efda0"`.

### 2.2 — Add/update chart_summary regression test

File: `platform-mcp/src/tools/chart_summary.test.ts` (create if absent)

Test must:
- Call `chart_summary({ chart_id: "362f9f17-95a5-490b-a5a7-027d3e0efda0", tier: "super_admin" })`
- Assert `response.rows_by_category` is an object with at least one key
- Assert no top-level `error` key in the response

Mock `callPlatformPrimitive` to return a realistic ToolBundle envelope shape.

### 2.3 — Fix query_transit_event (C6)

File: `platform-mcp/src/tools/query_transit_event.ts`

1. Read the file fully. Find the Zod input schema (lines ~48–60 per audit).
2. Add `event_type` as a **required** enum parameter:
   ```typescript
   event_type: z.enum([
     "ingress", "station_retrograde", "station_direct", "exact_aspect",
     "opposition", "conjunction", "trine", "square", "sextile"
   ]).describe("Type of transit event to search for")
   ```
3. Also add a clear error message: if somehow `event_type` is undefined at runtime, throw:
   `"event_type is required. Valid values: ingress|station_retrograde|station_direct|exact_aspect|opposition|conjunction|trine|square|sextile"`
4. Pass `event_type` through to the underlying engine/primitive call.

### 2.4 — Add/update query_transit_event regression test

File: `platform-mcp/src/tools/query_transit_event.test.ts` (create if absent)

Test must:
- Assert that calling without `event_type` returns a Zod validation error (not "Unknown event_type 'undefined'")
- Assert that calling with a valid `event_type` reaches the engine (mock the primitive call)

### 2.5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git add platform-mcp/src/tools/chart_summary.ts \
        platform-mcp/src/tools/query_transit_event.ts \
        platform-mcp/src/tools/chart_summary.test.ts \
        platform-mcp/src/tools/query_transit_event.test.ts
git commit -m "fix(TR-P1-S1): chart_summary 0-rows root cause; query_transit_event event_type schema"
```

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `chart_summary.ts` unwraps ToolBundle envelope correctly (reads `results[0].content` parsed JSON) |
| AC.2 | `chart_summary.test.ts` passes — non-empty `rows_by_category` returned for native chart_id |
| AC.3 | `query_transit_event.ts` Zod schema includes `event_type` as required enum |
| AC.4 | `query_transit_event.test.ts` passes — calling without `event_type` yields schema validation error |
| AC.5 | Both tests pass: `npx vitest run src/tools/chart_summary.test.ts src/tools/query_transit_event.test.ts` exits 0 |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
grep -q 'TR-P1-S1.*COMPLETE\|TR-P1-S1: PASS' 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/CONDUCTOR_LOG.md || \
(cd platform-mcp && npx vitest run src/tools/chart_summary.test.ts --reporter=verbose 2>&1 | grep -q 'PASS')
```

## §5 — FINAL_SUMMARY (emit at session end)

```
---FINAL_SUMMARY---
session_id: TR-P1-S1
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <any info conductor needs>
---
```
