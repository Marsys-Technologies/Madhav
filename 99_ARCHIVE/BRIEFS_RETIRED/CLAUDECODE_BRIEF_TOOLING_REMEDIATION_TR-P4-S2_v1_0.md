---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P4-S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P4-S2
---

# CLAUDECODE_BRIEF — TR-P4-S2
## Phase 4.4–4.6: MCP wrappers for panchang sidecar — muhurta_finder, tara_balam_for_native, chandra_balam_for_native

## §0 — Start

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean
```

## §1 — Scope

may_touch: platform-mcp/src/tools/muhurta_finder.ts, platform-mcp/src/tools/tara_balam_for_native.ts, platform-mcp/src/tools/chandra_balam_for_native.ts, platform-mcp/src/tools/muhurta_finder.test.ts, platform-mcp/src/tools/tara_balam_for_native.test.ts, platform-mcp/src/tools/chandra_balam_for_native.test.ts, platform-mcp/src/server.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**, platform/src/**, platform/python-sidecar/**

## §2 — Task

### Orientation

These tools call the Python sidecar via HTTP, not callPlatformPrimitive. First, find the existing sidecar HTTP client pattern in platform-mcp:

```bash
grep -r "sidecar\|SIDECAR\|python.*sidecar\|8001\|8002" platform-mcp/src/ --include="*.ts" -l
```

Then read one of the existing sidecar-calling tools (e.g., `query_panchanga.ts`) to understand the HTTP call pattern (fetch URL, auth headers, request body format).

Also find the sidecar routes:
```bash
grep -r "muhurat\|muhurta\|tara\|chandra_bala" platform/python-sidecar/routers/ --include="*.py" -l
ls platform/python-sidecar/routers/
```

---

### 4.4 — muhurta_finder

File: `platform-mcp/src/tools/muhurta_finder.ts`

1. Find the sidecar route path for muhurat (from the routers grep above).
2. Zod input schema:
   ```typescript
   const schema = z.object({
     date_from: z.string().describe("Start date YYYY-MM-DD"),
     date_to: z.string().describe("End date YYYY-MM-DD (max 30 days from date_from)"),
     activity_type: z.string().describe("Activity type, e.g. 'travel', 'business', 'marriage', 'medical'"),
     tier: z.string().optional().default("super_admin"),
   });
   ```
3. Call the sidecar HTTP endpoint with the above params.
4. Response shape: `{ windows: [{ start_time, end_time, score, auspicious_factors }] }` — parse from sidecar response.
5. Test: mock the sidecar HTTP call; assert `muhurta_finder({ date_from: "2026-06-01", date_to: "2026-06-07", activity_type: "travel" })` returns a response with a `windows` array.

### 4.5 — tara_balam_for_native

File: `platform-mcp/src/tools/tara_balam_for_native.ts`

1. Find the sidecar route for tara_bala.
2. Schema:
   ```typescript
   const schema = z.object({
     date: z.string().describe("Date YYYY-MM-DD"),
     tier: z.string().optional().default("super_admin"),
   });
   ```
3. The sidecar computes tara count (1–9) for the native's birth star against the day's nakshatra.
4. Response: `{ tara_count, tara_name, score, interpretation }`.
5. Test: mock; assert response includes `tara_count` field.

### 4.6 — chandra_balam_for_native

File: `platform-mcp/src/tools/chandra_balam_for_native.ts`

1. Chandra bala and tara bala are often computed together in the same sidecar endpoint. Check if the route returns both. If so, call the same endpoint as tara_balam and extract the chandra_bala fields.
2. Schema:
   ```typescript
   const schema = z.object({
     date: z.string().describe("Date YYYY-MM-DD"),
     tier: z.string().optional().default("super_admin"),
   });
   ```
3. Response: `{ chandra_bala_score, interpretation, moon_nakshatra }`.
4. Test: mock; assert response includes `chandra_bala_score` field.

### 4.7 — Register all 3 tools in server.ts

File: `platform-mcp/src/server.ts`

Add imports and register all 3 new tools (tool count 26→29).

### 4.8 — Commit

```bash
git add platform-mcp/src/tools/muhurta_finder.ts \
        platform-mcp/src/tools/tara_balam_for_native.ts \
        platform-mcp/src/tools/chandra_balam_for_native.ts \
        platform-mcp/src/tools/muhurta_finder.test.ts \
        platform-mcp/src/tools/tara_balam_for_native.test.ts \
        platform-mcp/src/tools/chandra_balam_for_native.test.ts \
        platform-mcp/src/server.ts
git commit -m "feat(TR-P4-S2): add MCP wrappers — muhurta_finder, tara_balam, chandra_balam"
```

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `muhurta_finder.ts` exists, calls sidecar HTTP, returns `windows` array |
| AC.2 | `tara_balam_for_native.ts` exists, returns `tara_count` in response |
| AC.3 | `chandra_balam_for_native.ts` exists, returns `chandra_bala_score` in response |
| AC.4 | All 3 registered in server.ts (tool count +3) |
| AC.5 | All test files pass: `npx vitest run src/tools/muhurta_finder.test.ts src/tools/tara_balam_for_native.test.ts src/tools/chandra_balam_for_native.test.ts` exits 0 |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(npx vitest run src/tools/muhurta_finder.test.ts src/tools/tara_balam_for_native.test.ts src/tools/chandra_balam_for_native.test.ts --reporter=verbose 2>&1 | grep -E 'passed|PASS' | grep -q '.')
```

## §5 — FINAL_SUMMARY

```
---FINAL_SUMMARY---
session_id: TR-P4-S2
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <sidecar route paths found, any stubs encountered, deviations>
---
```
