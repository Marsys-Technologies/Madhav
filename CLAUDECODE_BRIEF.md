---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P7-S4_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Conductor (2026-05-25)
session_id: TR-P7-S4
---

# CLAUDECODE_BRIEF — TR-P7-S4
## Phase 7.4 + 7.5: query_dasamsha_career (D10) + query_shashtiamsha (D60)

## §0 — Start

You are in /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix on branch feature/tooling-remediation.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean before starting
```

## §1 — Scope

may_touch: platform-mcp/src/tools/query_dasamsha_career.ts, platform-mcp/src/tools/query_dasamsha_career.test.ts, platform-mcp/src/tools/query_shashtiamsha.ts, platform-mcp/src/tools/query_shashtiamsha.test.ts, platform-mcp/src/server.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

## §2 — Task

### 7.4 — query_dasamsha_career

**New file:** `platform-mcp/src/tools/query_dasamsha_career.ts`

The D10 (Dasamsha) chart governs career, profession, and public status.

1. Read `query_divisional_chart.ts` (built in TR-P4-S1) to understand how to call it.
2. The tool calls `query_divisional_chart({division:"D10", chart_id})` via `callPlatformPrimitive`.
3. Parse the D3-style response to get planet sign/house positions in D10.
4. **Career indicators** — hardcode these classical rules:
   - 10H lord in D10: strong career indicator.
   - Sun, Saturn, Mercury in D10 10H: additional career strength.
   - 10H lord in own sign, exalted, or in kendra/trikona → favourable career.
   - 10H lord in 6H/8H/12H → career obstacles.
5. **Response shape:**
   ```json
   {
     "d10_ascendant": "Aries",
     "planets": [
       {"planet":"Sun","sign":"Leo","house":5,"dignity":"own_sign"}
     ],
     "career_indicators": [
       {"indicator":"10H lord in D10","planet":"Saturn","classical_rule":"Saturn as 10L placed in 7H D10 — directional strength"}
     ]
   }
   ```
6. **Schema params:** `chart_id` (string, optional), `tier` (string, optional).
7. **Register** in server.ts.
8. **Tests** (mock `callPlatformPrimitive`):
   - Returns non-null `d10_ascendant`.
   - `planets` array has ≥ 1 entry.
   - `career_indicators` array is present (can be empty if no rule fires on mock data).

### 7.5 — query_shashtiamsha

**New file:** `platform-mcp/src/tools/query_shashtiamsha.ts`

The D60 (Shashtiamsha) is the finest divisional — shows past-life karma. Each D60 pada has a classical name.

1. Call `query_divisional_chart({division:"D60", chart_id})` via `callPlatformPrimitive`.
2. Map each planet's D60 position to a classical pada name + interpretation using this fixed lookup table (60 padas cycle through the 12 signs):

```typescript
const D60_PADA_NAMES: Record<number, { name: string; interpretation: string }> = {
  1: { name: "Ghora", interpretation: "Malefic; past-life violence or harsh karma" },
  2: { name: "Rakshasa", interpretation: "Demonic; indicates past-life cruelty" },
  3: { name: "Deva", interpretation: "Divine; past-life merit and piety" },
  4: { name: "Kubera", interpretation: "Wealth deity; past-life generosity" },
  5: { name: "Yaksha", interpretation: "Semi-divine; past-life association with nature spirits" },
  6: { name: "Kinnara", interpretation: "Celestial musician; artistic past-life" },
  7: { name: "Bhrashta", interpretation: "Fallen; past-life ethical violations" },
  8: { name: "Kulaghna", interpretation: "Family destroyer; past-life betrayal" },
  9: { name: "Garuda", interpretation: "Eagle deity; past-life spiritual aspiration" },
  10: { name: "Agni", interpretation: "Fire deity; transformative past-life experiences" },
  11: { name: "Maya", interpretation: "Illusion; past-life deception" },
  12: { name: "Purishaka", interpretation: "Impure; difficult past-life associations" },
  // Extend 13–60 by cycling through these 12 names: 13→Ghora, 14→Rakshasa, etc.
};
```

   The pada number for a planet = `Math.ceil((planet_longitude_in_sign % 30) / 0.5)` (each pada = 0.5°). If the planet is at 0°, pada = 1.

3. **Response shape:**
   ```json
   {
     "planets": [
       {
         "planet": "Jupiter",
         "d60_sign": "Leo",
         "d60_house": 5,
         "d60_longitude_in_sign": 14.5,
         "d60_pada_number": 29,
         "d60_pada_name": "Garuda",
         "d60_interpretation": "Eagle deity; past-life spiritual aspiration"
       }
     ]
   }
   ```
4. **Schema params:** `chart_id` (string, optional), `tier` (string, optional).
5. **Register** in server.ts.
6. **Tests** (mock `callPlatformPrimitive`):
   - Returns `planets` array with ≥ 1 entry.
   - Each planet has `d60_pada_name` (non-empty string).
   - Pada calculation: planet at 7.5° in sign → pada = `Math.ceil(7.5/0.5)` = 15 → name cycles to position 15 mod 12 = 3 → "Deva".

### Commit + Push

```bash
git add -A
git commit -m "feat(TR-P7-S4): query_dasamsha_career; query_shashtiamsha"
git push origin feature/tooling-remediation
```

This is the Wave 4 push boundary. Push after commit.

## §3 — Acceptance criteria

1. `query_dasamsha_career` is registered, returns D10 positions + career indicators.
2. `query_shashtiamsha` is registered, returns D60 positions with pada names + interpretations.
3. Pada cycle logic correct: pada 1–12 have names; 13→cycles back to Ghora, etc.
4. All tests pass: `npx vitest run src/tools/query_dasamsha_career.test.ts src/tools/query_shashtiamsha.test.ts`.
5. Git push to `feature/tooling-remediation` succeeds.

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(cd platform-mcp && npx vitest run src/tools/query_dasamsha_career.test.ts src/tools/query_shashtiamsha.test.ts --reporter=verbose 2>&1 | grep -E 'PASS|passed' | grep -q '.')
```

## §5 — FINAL_SUMMARY (emit at session end)

---FINAL_SUMMARY---
session_id: TR-P7-S4
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <any info conductor needs>
---
