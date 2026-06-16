---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P4-S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P4-S1
---

# CLAUDECODE_BRIEF — TR-P4-S1
## Phase 4.1–4.3: new MCP wrappers — query_varshphal, query_divisional_chart, query_remedial_mantras

## §0 — Start

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean
```

## §1 — Scope

may_touch: platform-mcp/src/tools/query_varshphal.ts, platform-mcp/src/tools/query_divisional_chart.ts, platform-mcp/src/tools/query_remedial_mantras.ts, platform-mcp/src/tools/query_varshphal.test.ts, platform-mcp/src/tools/query_divisional_chart.test.ts, platform-mcp/src/tools/query_remedial_mantras.test.ts, platform-mcp/src/server.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**, platform/src/**

## §2 — Task

### Orientation

Follow the existing wrapper pattern exactly — look at `query_chart_facts.ts` as the reference. Each wrapper:
1. Defines a Zod input schema
2. Calls `callPlatformPrimitive(toolName, toolParams, tier)` (or equivalent)
3. Unwraps the ToolBundle response (read `results[0].content` as parsed JSON — the C1 fix from TR-P1-S1)
4. Returns a clean response object

NATIVE_CHART_ID = `"362f9f17-95a5-490b-a5a7-027d3e0efda0"`

Before writing any wrapper, grep `platform/src/lib/retrieve/` to find the exact function names and parameter shapes used by each engine.

---

### 4.1 — query_varshphal

File: `platform-mcp/src/tools/query_varshphal.ts`

1. Find the source engine: grep `platform/src/lib/retrieve/` for `varshaphal` or `varshphal`. Read the function signature.
2. Create the MCP wrapper with this schema:
   ```typescript
   const schema = z.object({
     chart_id: z.string().optional().describe("Chart UUID; defaults to native's chart"),
     year: z.number().int().min(1900).max(2100).describe("Gregorian year, e.g. 2026"),
     tier: z.string().optional().default("super_admin"),
   });
   ```
3. Call the primitive with `{ chart_id: input.chart_id ?? NATIVE_CHART_ID, year: input.year }`.
4. Tier visibility: super_admin + acharya (add a tier check before calling the primitive).
5. Test: mock `callPlatformPrimitive`; assert `query_varshphal({ year: 2026 })` returns a non-empty response object.

### 4.2 — query_divisional_chart

File: `platform-mcp/src/tools/query_divisional_chart.ts`

1. Find source engine: grep for `divisional` or `D1` or `D9` in `platform/src/lib/retrieve/`. Read the function signature and how it accepts the division parameter.
2. Create the MCP wrapper:
   ```typescript
   const VALID_DIVISIONS = ["D1","D2","D3","D4","D7","D9","D10","D12","D16","D20","D24","D27","D30","D40","D45","D60"] as const;
   const schema = z.object({
     chart_id: z.string().optional(),
     division: z.enum(VALID_DIVISIONS).describe("Divisional chart: D1=Rasi, D9=Navamsha, D10=Dasamsha, D60=Shashtiamsha, etc."),
     tier: z.string().optional().default("super_admin"),
   });
   ```
3. Pass `{ chart_id: ..., division: input.division }` to the primitive.
4. Test: mock primitive; assert `query_divisional_chart({ division: "D9" })` returns response with ≥1 planet row (or non-empty response).

### 4.3 — query_remedial_mantras

File: `platform-mcp/src/tools/query_remedial_mantras.ts`

1. This wraps the remedial codex RAG filter. Find the source: grep `platform/src/lib/retrieve/` for `remedial` or `remedy`. If no dedicated function exists, look for how `vector_search` is called with `doc_type='l4_remedial'` or `source='remedial'`.
2. Create the MCP wrapper:
   ```typescript
   const schema = z.object({
     planet: z.string().optional().describe("Planet name, e.g. 'Saturn'"),
     house: z.number().int().min(1).max(12).optional().describe("House number 1-12"),
     condition: z.string().optional().describe("Free-text condition query, e.g. 'debilitated Mars'"),
     tier: z.string().optional().default("super_admin"),
   });
   ```
3. Build a query string from the inputs: `[planet, house && `house ${house}`, condition].filter(Boolean).join(' ')`.
4. Call the remedial codex query (vector search with doc_type filter or dedicated primitive).
5. Test: mock; assert `query_remedial_mantras({ planet: "Saturn" })` returns ≥1 chunk in response.

### 4.4 — Register all 3 tools

File: `platform-mcp/src/server.ts`

Add all 3 new tools to the registered tools array (follow the same pattern as existing tool registrations).

### 4.5 — Commit

```bash
git add platform-mcp/src/tools/query_varshphal.ts \
        platform-mcp/src/tools/query_divisional_chart.ts \
        platform-mcp/src/tools/query_remedial_mantras.ts \
        platform-mcp/src/tools/query_varshphal.test.ts \
        platform-mcp/src/tools/query_divisional_chart.test.ts \
        platform-mcp/src/tools/query_remedial_mantras.test.ts \
        platform-mcp/src/server.ts
git commit -m "feat(TR-P4-S1): add MCP wrappers — query_varshphal, query_divisional_chart, query_remedial_mantras"
```

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `query_varshphal.ts` exists, calls primitive with chart_id + year, registered in server.ts |
| AC.2 | `query_divisional_chart.ts` exists, division enum validated, registered |
| AC.3 | `query_remedial_mantras.ts` exists, builds query from planet/house/condition, registered |
| AC.4 | All 3 test files pass: `npx vitest run src/tools/query_varshphal.test.ts src/tools/query_divisional_chart.test.ts src/tools/query_remedial_mantras.test.ts` exits 0 |
| AC.5 | Tool count in server.ts increases by 3 |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(npx vitest run src/tools/query_varshphal.test.ts src/tools/query_divisional_chart.test.ts src/tools/query_remedial_mantras.test.ts --reporter=verbose 2>&1 | grep -E 'passed|PASS' | grep -q '.')
```

## §5 — FINAL_SUMMARY

```
---FINAL_SUMMARY---
session_id: TR-P4-S1
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <primitive function names found, any missing engines, deviations>
---
```
