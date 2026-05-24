---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P1-S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P1-S2
---

# CLAUDECODE_BRIEF — TR-P1-S2
## Phase 1.3 + 1.4: query_signals filter enforcement + query_ephemeris date_range fix

## §0 — Start

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean before starting
```

## §1 — Scope

may_touch: platform-mcp/src/tools/query_signals.ts, platform-mcp/src/tools/query_ephemeris.ts, platform/src/lib/retrieve/*, platform-mcp/src/tools/query_signals.test.ts, platform-mcp/src/tools/query_ephemeris.test.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

## §2 — Task

### Phase 0 findings

**C4 — query_signals:** Bug confirmed as **wrapper** layer. The wrapper does not translate `forward_looking`/`min_confidence` params into the `toolParams` passed to the primitive. The MCP input schema has these fields but the handler ignores them.

**C5 — query_ephemeris:** Partially working. Schema uses `start`/`end` (not `from`/`to`) and accepts a single planet string not array. Returns only one date even with a date range. Core fix needed in how the date range is passed to the primitive.

---

### 2.1 — Fix query_signals filter enforcement (C4)

File: `platform-mcp/src/tools/query_signals.ts`

1. Read the file fully. Find where `callPlatformPrimitive` (or equivalent) is called.
2. The MCP input schema already exposes `forward_looking`, `min_confidence`, `valence`, `temporal_activation`, `domains[]`. Verify these exist in the Zod schema; if any are missing, add them:
   - `forward_looking?: z.boolean()`
   - `min_confidence?: z.number().min(0).max(1)`
   - `valence?: z.enum(["positive","negative","neutral"])`
   - `temporal_activation?: z.enum(["permanent","dasha_tied","transit_tied"])`
   - `domains?: z.array(z.string())`
3. Find the `toolParams` object passed to the primitive. Ensure ALL of the above fields are included in `toolParams` when provided. Map them exactly:
   ```typescript
   const toolParams = {
     chart_id: input.chart_id ?? NATIVE_CHART_ID,
     forward_looking: input.forward_looking,
     min_confidence: input.min_confidence,
     valence: input.valence,
     temporal_activation: input.temporal_activation,
     domains: input.domains,
     // ... other existing params
   };
   ```
4. In the platform primitive (platform/src/lib/retrieve/ — grep for query_signals or getSignals), find the SQL WHERE clause. Add filter conditions for the new params:
   - `forward_looking=true` → `AND temporal_direction = 'forward'`
   - `min_confidence` → `AND confidence >= $min_confidence`
   - `valence` → `AND valence = $valence` (if the column exists)
   - `temporal_activation` → `AND temporal_activation = $temporal_activation` (if column exists)
   - `domains[]` → `AND domain = ANY($domains)`
   - If a column doesn't exist in the schema, skip that filter and note it in FINAL_SUMMARY.

### 2.2 — query_signals regression tests

File: `platform-mcp/src/tools/query_signals.test.ts` (create if absent)

- Mock `callPlatformPrimitive`; assert `forward_looking=true` and `min_confidence=0.9` are included in the `toolParams` argument.
- Test that default chart_id fallback is applied when chart_id not provided.

### 2.3 — Fix query_ephemeris date_range (C5)

File: `platform-mcp/src/tools/query_ephemeris.ts`

1. Read the file fully.
2. Current schema may use `start`/`end` top-level, or a `date_range` object. Read Phase 0 baseline at `eval-results/tooling_audit_baseline_20260524.json` key `tool_tests.C5_query_ephemeris_date_range` for actual error shape.
3. Standardise on `date_range: { from: string, to: string }` in the Zod schema (with backward-compat alias of `start`/`end` if needed).
4. In the primitive call, pass `start_date = date_range.from` and `end_date = date_range.to`.
5. Add new params:
   - `sample_step?: z.enum(["1d","7d","30d"]).default("1d")` — when "7d" or "30d", add a `WHERE date_part('dow', date) = 0` or similar sampling in the SQL, or post-filter in TS.
   - `return_changes_only?: z.boolean().default(false)` — when true, only return rows where at least one planet position differs by >1 degree from the previous row.
6. Cap: if `date_range` spans more than 1825 days, return an error: `"Date range exceeds 5-year maximum (1825 days). Please narrow the range."`
7. Accept `planets` as either a single string or an array. Normalise to array internally.

### 2.4 — query_ephemeris regression tests

File: `platform-mcp/src/tools/query_ephemeris.test.ts` (create if absent)

- Test: `date_range: {from: "2026-06-01", to: "2026-06-30"}` is passed correctly to the primitive as start_date/end_date.
- Test: range > 1825 days returns an error response.
- Test: `sample_step: "7d"` is included in toolParams.

### 2.5 — Commit

```bash
git add platform-mcp/src/tools/query_signals.ts \
        platform-mcp/src/tools/query_ephemeris.ts \
        platform/src/lib/retrieve/ \  # only if primitive files were modified
        platform-mcp/src/tools/query_signals.test.ts \
        platform-mcp/src/tools/query_ephemeris.test.ts
git commit -m "fix(TR-P1-S2): query_signals filter enforcement; query_ephemeris date_range+sample_step"
```

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `query_signals.ts` passes `forward_looking`, `min_confidence`, `valence`, `temporal_activation`, `domains` to `toolParams` |
| AC.2 | `query_signals.test.ts` asserts these params appear in the primitive call arguments |
| AC.3 | `query_ephemeris.ts` accepts `date_range.{from,to}` and enforces 1825-day cap |
| AC.4 | `query_ephemeris.ts` accepts `sample_step` and `return_changes_only` params |
| AC.5 | Both test files pass: `npx vitest run src/tools/query_signals.test.ts src/tools/query_ephemeris.test.ts` exits 0 |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(npx vitest run src/tools/query_signals.test.ts src/tools/query_ephemeris.test.ts --reporter=verbose 2>&1 | grep -E 'passed|PASS' | grep -q '.')
```

## §5 — FINAL_SUMMARY

```
---FINAL_SUMMARY---
session_id: TR-P1-S2
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <any columns that don't exist in the schema, any deviations>
---
```
