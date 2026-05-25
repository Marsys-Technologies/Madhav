---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S7: Port query_drekkana_drishti + query_remedies_prescribed → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S7
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S7
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S7 — Port to portal: query_drekkana_drishti + query_remedies_prescribed

## 1. Context

**`query_drekkana_drishti` (Jaimini Drekkana Drishti):**
1. Fetches D3 chart positions via `divisional_query({varga:"D3"})`
2. Classifies each sign as moveable / fixed / dual
3. Applies Jaimini Drekkana Drishti rules:
   - Moveable signs: aspect ALL signs EXCEPT 2nd and 12th from them
   - Fixed signs: aspect all OTHER fixed signs
   - Dual signs: aspect all OTHER dual signs
4. Returns: per-planet drekkana sign, type, drishti targets, mutual aspects

**`query_remedies_prescribed` (Remedial Prescription Cross-Reference):**
1. Builds composite search query from `affliction`, `planet`, `house`, `condition` params
2. Calls `remedial_codex_query` (the existing portal tool) for remedy matches
3. Optionally enriches with chart_facts remedy/strength rows for the planet
4. Detects remedy_type from content keywords (mantra/gem/ritual/charity)
5. Filters by `remedy_type` if not "all"
6. Returns top 10 structured remedy results

**MCP source files (read-only):**
- `platform-mcp/src/tools/query_drekkana_drishti.ts`
- `platform-mcp/src/tools/query_remedies_prescribed.ts`

**Portal target files (create):**
- `platform/src/lib/retrieve/query_drekkana_drishti.ts`
- `platform/src/lib/retrieve/query_remedies_prescribed.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_drekkana_drishti.ts` (create)
- `platform/src/lib/retrieve/query_remedies_prescribed.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registrations)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_7.1: `platform/src/lib/retrieve/query_drekkana_drishti.ts` exists and exports a RetrievalTool
- [ ] AC.1_7.2: `platform/src/lib/retrieve/query_remedies_prescribed.ts` exists and exports a RetrievalTool
- [ ] AC.1_7.3: Both tools registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_7.4: `query_drekkana_drishti` calls portal `divisional_query`; `query_remedies_prescribed` calls portal `remedial_codex_query`
- [ ] AC.1_7.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_7.6: Commit message contains `UDA-1-S7`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source files

```bash
cat platform-mcp/src/tools/query_drekkana_drishti.ts
cat platform-mcp/src/tools/query_remedies_prescribed.ts
cat platform/src/lib/retrieve/remedial_codex_query.ts | head -60
```

### Step 2 — Create query_drekkana_drishti.ts (portal version)

Sign type classification:
```typescript
const MOVEABLE_SIGNS = ['Aries', 'Cancer', 'Libra', 'Capricorn']
const FIXED_SIGNS    = ['Taurus', 'Leo', 'Scorpio', 'Aquarius']
const DUAL_SIGNS     = ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
const ALL_SIGNS      = [...MOVEABLE_SIGNS, ...FIXED_SIGNS, ...DUAL_SIGNS]

function getDrishtiTargets(sign: string): string[] {
  if (MOVEABLE_SIGNS.includes(sign)) {
    const idx = ALL_SIGNS.indexOf(sign)
    const adj2nd  = ALL_SIGNS[(idx + 1) % 12]!
    const adj12th = ALL_SIGNS[(idx + 11) % 12]!
    return ALL_SIGNS.filter(s => s !== sign && s !== adj2nd && s !== adj12th)
  }
  if (FIXED_SIGNS.includes(sign)) return FIXED_SIGNS.filter(s => s !== sign)
  if (DUAL_SIGNS.includes(sign))  return DUAL_SIGNS.filter(s => s !== sign)
  return []
}
```

Call portal `divisional_query` with `divisional_chart: "D3"` to get D3 positions.

### Step 3 — Create query_remedies_prescribed.ts (portal version)

Call portal `remedial_codex_query` tool's execute function with the built search query.
Then optionally call `chart_facts_query` for the planet's remedy rows.
Detect remedy_type from content keywords (same keywords as MCP: "mantra", "gem", "ritual", "donate").

### Step 4 — Register in index.ts

```typescript
import * as queryDrekkanaDrishti from './query_drekkana_drishti'
import * as queryRemediesPrescribed from './query_remedies_prescribed'
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
git add platform/src/lib/retrieve/query_drekkana_drishti.ts \
        platform/src/lib/retrieve/query_remedies_prescribed.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S7): port query_drekkana_drishti + query_remedies_prescribed to portal

Jaimini Drekkana Drishti aspect system; remedial codex cross-reference.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "query_drekkana_drishti\|drekkana_drishti" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S7_DREKKANA: PASS'
grep -q "query_remedies_prescribed\|remedies_prescribed" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S7_REMEDIES: PASS'
git log --oneline -3 | grep -q 'UDA-1-S7' && echo 'GATE_UDA_1_S7_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S7_v1_0.md*
