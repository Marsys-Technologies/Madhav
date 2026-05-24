---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P8-S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Conductor (2026-05-25)
session_id: TR-P8-S2
---

# CLAUDECODE_BRIEF — TR-P8-S2
## Phase 8.3: query_remedies_prescribed + v1.0 close summary (FINAL SESSION)

## §0 — Start

You are in /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix on branch feature/tooling-remediation.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean before starting
```

## §1 — Scope

may_touch: platform-mcp/src/tools/query_remedies_prescribed.ts, platform-mcp/src/tools/query_remedies_prescribed.test.ts, platform-mcp/src/server.ts, eval-results/tooling_remediation_v1_0_close.json, 00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

## §2 — Task

### 8.3 — query_remedies_prescribed

**New file:** `platform-mcp/src/tools/query_remedies_prescribed.ts`

This tool cross-references natal chart conditions with the remedial codex.

1. Read `query_remedial_mantras.ts` (built in TR-P4-S1) to understand the remedial codex access pattern.

2. **Schema params** (Zod):
   - `affliction`: `z.string().optional()` — e.g. "Saturn afflicts 1H", "debilitated Mars", "Rahu-Ketu axis on 7H"
   - `planet`: `z.string().optional()` — e.g. "Saturn", "Rahu"
   - `house`: `z.number().min(1).max(12).optional()` — 1–12
   - `condition`: `z.string().optional()` — free text query for RAG search
   - `remedy_type`: `z.enum(["mantra","gem","ritual","charity","all"]).default("all")`
   - `tier`: `z.string().optional()`

3. **Algorithm:**
   a. Build a search query from the provided params: `"${affliction ?? ''} ${planet ?? ''} house ${house ?? ''} ${condition ?? ''} remedy mantra gem".trim()`
   b. Call `query_remedial_mantras` primitive (via callPlatformPrimitive) with the constructed query and the planet/house filters.
   c. Also call `query_chart_facts` for the planet's chart_facts row (category: "remedy" or "strength") if planet is provided.
   d. Filter results by remedy_type if not "all".
   e. For each result, detect remedy_type from content keywords: "mantra" → mantra, "gem"|"gemstone"|"ratna" → gem, "ritual"|"puja"|"homa" → ritual, "donate"|"charity"|"daan" → charity.
   f. Return top 10 results.

4. **Response:**
   ```json
   {
     "affliction_query": "Saturn afflicts 1H",
     "results": [
       {
         "condition": "Saturn affliction",
         "remedy_type": "mantra",
         "remedy_text": "Om Sham Shanaischaraya Namah — recite 108 times on Saturdays",
         "timing": "Saturday, Pushya nakshatra, dawn",
         "classical_source": "BPHS chapter 56",
         "relevance_score": 0.87
       }
     ],
     "result_count": N
   }
   ```

5. **Register** in server.ts.

6. **Tests** (mock callPlatformPrimitive):
   - `query_remedies_prescribed({planet:"Saturn"})` returns results.
   - remedy_type filter "mantra" returns only mantra entries.
   - Result has `remedy_type`, `remedy_text`, `classical_source`.
   - Empty query (no params) returns empty results gracefully.

### Close summary steps

After the tool is built and tests pass, execute these close-out steps:

**Step 1: Run the full vitest suite**
```bash
cd platform-mcp && npx vitest run --reporter=verbose 2>&1 | tail -30
```
Capture the pass/fail summary line (e.g. "X passed, Y failed").

**Step 2: Update TOOLING_AUDIT_TRACKER_v1_0.md**
Read `00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md`. Find any items that are not yet marked DONE. Mark all items with a session reference as DONE:
- Items in Phase 8 column: mark DONE (TR-P8-S2)
- Items from Phase 7 if any still open: mark DONE (TR-P7-S1 through TR-P7-S4)
- Overall status: set to "v1.0 COMPLETE (2026-05-25)"

**Step 3: Write closing summary**
Write `eval-results/tooling_remediation_v1_0_close.json`:
```json
{
  "sessions_completed": 26,
  "tools_fixed": "<count from tracker>",
  "tools_added": "<count from tracker>",
  "tracker_open_items": 0,
  "vitest_summary": "<paste the tail -30 summary line>",
  "next_steps": [
    "Phase 12: spouse chart integration when data available",
    "query_tara_balam + query_chandra_balam primitives_registry.ts wiring (noted TR-P4-S2)",
    "query_dasamsha_career stub for query_dasamsha_career in TR-P9-S2 career_timing_audit recipe"
  ],
  "completed_at": "2026-05-25"
}
```

**Step 4: Commit**
```bash
git add -A
git commit -m "feat(TR-P8-S2): query_remedies_prescribed; v1.0 close summary"
```

**Step 5: Push**
```bash
git push origin feature/tooling-remediation
```

**Step 6: Emit the PR command (do not run it — print it for the human)**
```
PR TO MAIN (human action required):
gh pr create \
  --title "feat: MARSYS-JIS Tooling Remediation v1.0 (87 findings fixed)" \
  --base main \
  --head feature/tooling-remediation \
  --body "26 sessions. 87 audit findings addressed. See eval-results/tooling_remediation_v1_0_close.json for summary."
```

## §3 — Acceptance criteria

1. `query_remedies_prescribed` is registered, accepts affliction/planet/house/condition/remedy_type params.
2. All tests pass: `npx vitest run src/tools/query_remedies_prescribed.test.ts`.
3. Full vitest suite run completed and summary captured.
4. `eval-results/tooling_remediation_v1_0_close.json` written.
5. `TOOLING_AUDIT_TRACKER_v1_0.md` updated to "v1.0 COMPLETE".
6. Commit + push to `feature/tooling-remediation` succeeds.

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(cd platform-mcp && npx vitest run --reporter=verbose 2>&1 | tail -20 | grep -E 'passed|PASS') && \
git log --oneline origin/feature/tooling-remediation | head -1 | grep -q 'TR-P8-S2'
```

## §5 — FINAL_SUMMARY (emit at session end)

---FINAL_SUMMARY---
session_id: TR-P8-S2
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <any info conductor needs>
---
