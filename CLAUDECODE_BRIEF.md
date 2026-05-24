---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P7-S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Conductor (2026-05-25)
session_id: TR-P7-S1
---

# CLAUDECODE_BRIEF — TR-P7-S1
## Phase 7.1 + 7.6: query_dasha_periods PD/SD levels; query_drekkana_drishti

## §0 — Start

You are in /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix on branch feature/tooling-remediation.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean before starting
```

## §1 — Scope

may_touch: platform-mcp/src/tools/query_dasha_periods.ts, platform-mcp/src/tools/query_dasha_periods.test.ts, platform-mcp/src/tools/query_drekkana_drishti.ts, platform-mcp/src/tools/query_drekkana_drishti.test.ts, platform/src/lib/retrieve/*, platform-mcp/src/server.ts, platform-mcp/src/index.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

## §2 — Task

### 7.1 — query_dasha_periods level extension

**File:** `platform-mcp/src/tools/query_dasha_periods.ts`

1. Read the existing file fully to understand current schema and engine call.
2. Add `level` param to the Zod schema: `z.enum(["maha","antar","pratyantar","sookshma"]).default("antar")`.
3. Thread `level` through to the engine/primitive call. Check the platform primitive at `platform/src/lib/retrieve/` — grep for `query_dasha_periods` or `vimshottari`.
4. PD (Pratyantar) and SD (Sookshma) are computed from MD/AD durations × planet ratios (standard Vimshottari proportion). If the engine already computes them, expose via level param. If not, implement:
   - Pratyantar period for planet P within AD of planet A within MD of planet M:
     `duration_pratyantar = duration_AD(A,M) × vimshottari_years[P] / 120`
   - Sookshma period for planet S within PD of P:
     `duration_sookshma = duration_PD(P,A,M) × vimshottari_years[S] / 120`
   - Vimshottari years: Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16, Saturn=19, Mercury=17, Ketu=7, Venus=20.
5. Response shape: same as current but with nested `sub_periods` for PD/SD when level is pratyantar/sookshma.
6. Write regression tests in `platform-mcp/src/tools/query_dasha_periods.test.ts`:
   - `query_dasha_periods({level:"antar"})` returns periods (existing baseline).
   - `query_dasha_periods({level:"pratyantar"})` returns periods with `duration_days` smaller than corresponding AD periods.
   - `query_dasha_periods({level:"sookshma"})` returns periods with even smaller durations.

### 7.6 — query_drekkana_drishti (new tool)

**New files:** `platform-mcp/src/tools/query_drekkana_drishti.ts` + `platform-mcp/src/tools/query_drekkana_drishti.test.ts`

The D3 (Drekkana) chart governs siblings, courage, and Jaimini-style aspects.

1. Fetch D3 positions: call `query_divisional_chart({division:"D3"})` (already built in TR-P4-S1). Parse the planet positions from the response.
2. Alternatively, check if `chart_facts` has rows with `category: "divisional_d3"` — prefer chart_facts if populated (faster).
3. Compute Jaimini Drekkana Drishti:
   - **Moveable signs** (Aries, Cancer, Libra, Capricorn): cast drishti on all signs EXCEPT the adjacent signs (the 2nd and 12th from them).
   - **Fixed signs** (Taurus, Leo, Scorpio, Aquarius): cast drishti on all other fixed signs.
   - **Dual signs** (Gemini, Virgo, Sagittarius, Pisces): cast drishti on all other dual signs.
4. For each planet in D3, compute which signs it aspects based on its D3 sign type (moveable/fixed/dual).
5. For each aspected sign, check if any other planet occupies that sign → record aspect with strength (full=1.0 for in-sign).
6. Output shape:
   ```json
   {
     "planets": [
       {
         "planet": "Jupiter",
         "drekkana_sign": "Aries",
         "drekkana_house": 1,
         "sign_type": "moveable",
         "drishti_targets": [
           {"sign": "Leo", "planet_in_sign": "Sun", "aspect_strength": 1.0},
           {"sign": "Scorpio", "planet_in_sign": null, "aspect_strength": 1.0}
         ]
       }
     ],
     "mutual_drekkana_drishti": []
   }
   ```
7. Schema params: `chart_id` (string, optional — default native's), `tier` (string).
8. Register the new tool in `platform-mcp/src/server.ts` (or index.ts — wherever other tools are registered).
9. Write tests:
   - `query_drekkana_drishti({})` returns a non-empty `planets` array.
   - Each planet in the response has `drekkana_sign`, `drekkana_house`, `drishti_targets`.

### Commit

```bash
git add -A
git commit -m "feat(TR-P7-S1): dasha_periods PD/SD levels; query_drekkana_drishti"
```

## §3 — Acceptance criteria

1. `query_dasha_periods` Zod schema includes `level` enum param with default "antar".
2. `query_dasha_periods({level:"pratyantar"})` returns non-empty response with periods having shorter durations than the AD level.
3. `query_drekkana_drishti({})` is a registered MCP tool that returns planet positions in D3 with Jaimini drishti targets.
4. All new tests pass: `npx vitest run src/tools/query_dasha_periods.test.ts src/tools/query_drekkana_drishti.test.ts --reporter=verbose`.
5. Commit SHA exists: `git log --format=%H -1` returns a new commit.

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(cd platform-mcp && npx vitest run src/tools/query_dasha_periods.test.ts src/tools/query_drekkana_drishti.test.ts --reporter=verbose 2>&1 | grep -E 'PASS|passed' | grep -q '.')
```

## §5 — FINAL_SUMMARY (emit at session end)

---FINAL_SUMMARY---
session_id: TR-P7-S1
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <any info conductor needs>
---
