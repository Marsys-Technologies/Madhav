---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S5: Port query_dasamsha_career + query_shashtiamsha → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S5
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S5
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S5 — Port to portal: query_dasamsha_career + query_shashtiamsha

## 1. Context

Two MCP divisional-chart analysis tools need to be ported to the portal:

**`query_dasamsha_career` (D10 Career Analysis):**
1. Fetches D10 chart positions via `divisional_query({varga:"D10"})`
2. Parses planet sign/house positions in D10
3. Applies classical career-indicator rules (10H lord placement, career planet positions)
4. Returns `{ d10_ascendant, planets, career_indicators }`

**`query_shashtiamsha` (D60 Karma Analysis):**
1. Fetches D60 chart positions via `divisional_query({varga:"D60"})`
2. Maps each planet's D60 position to a classical pada name + interpretation
3. Pada names cycle: Ghora, Rakshasa, Deva... (12 names × 5 repeats = 60 padas, 0.5° each)
4. Returns `{ planets: [{planet, d60_sign, d60_house, d60_pada_number, d60_pada_name, d60_interpretation}] }`

**MCP source files (read-only):**
- `platform-mcp/src/tools/query_dasamsha_career.ts`
- `platform-mcp/src/tools/query_shashtiamsha.ts`

**Portal target files (create):**
- `platform/src/lib/retrieve/query_dasamsha_career.ts`
- `platform/src/lib/retrieve/query_shashtiamsha.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_dasamsha_career.ts` (create)
- `platform/src/lib/retrieve/query_shashtiamsha.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registrations)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_5.1: `platform/src/lib/retrieve/query_dasamsha_career.ts` exists and exports a RetrievalTool
- [ ] AC.1_5.2: `platform/src/lib/retrieve/query_shashtiamsha.ts` exists and exports a RetrievalTool
- [ ] AC.1_5.3: Both tools registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_5.4: Both tools call portal `divisional_query` (the existing portal tool) to fetch chart data
- [ ] AC.1_5.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_5.6: Commit message contains `UDA-1-S5`

---

## 4. Step-by-Step Execution

### Step 1 — Read source files and portal divisional_query

```bash
cat platform-mcp/src/tools/query_dasamsha_career.ts
cat platform-mcp/src/tools/query_shashtiamsha.ts
cat platform/src/lib/retrieve/divisional_query.ts | head -80
```

### Step 2 — Create query_dasamsha_career.ts

Port the career rules:
- 10H lord in any D10 house = career indicator
- Sun, Saturn, Mercury in D10 10H = additional strength
- 10H lord in own sign / exalted / kendra (1,4,7,10) / trikona (1,5,9) = favourable
- 10H lord in 6H / 8H / 12H = career obstacle

Call the portal's `divisional_query` tool execute function directly (do not use MCP callPlatformPrimitive).

### Step 3 — Create query_shashtiamsha.ts

Port the D60 pada names array and calculation:
```typescript
const D60_PADA_NAMES = [
  'Ghora', 'Rakshasa', 'Deva', 'Kubera', 'Yaksha', 'Kinnar',
  'Bhrashta', 'Kulaghna', 'Garala', 'Vahni', 'Maya', 'Purishaka',
]

function getPadaName(longitudeInSign: number): { pada_number: number; pada_name: string } {
  const padaNumber = Math.max(1, Math.ceil(longitudeInSign / 0.5))
  const pada_name = D60_PADA_NAMES[(padaNumber - 1) % 12]!
  return { pada_number: padaNumber, pada_name }
}
```

### Step 4 — Register in index.ts

```typescript
import * as queryDasamshaaCareer from './query_dasamsha_career'
import * as queryShashtiamsha from './query_shashtiamsha'
```

Add to RETRIEVAL_TOOLS.

### Step 5 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_dasamsha_career.ts \
        platform/src/lib/retrieve/query_shashtiamsha.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S5): port query_dasamsha_career + query_shashtiamsha to portal

D10 career indicator rules; D60 Shashtiamsha karma pada analysis.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "query_dasamsha_career\|dasamsha_career" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S5_DASAMSHA: PASS'
grep -q "query_shashtiamsha\|shashtiamsha" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S5_SHASHTIAMSHA: PASS'
git log --oneline -3 | grep -q 'UDA-1-S5' && echo 'GATE_UDA_1_S5_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S5_v1_0.md*
