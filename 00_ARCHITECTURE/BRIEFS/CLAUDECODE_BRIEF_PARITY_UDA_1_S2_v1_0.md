---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S2: Port get_planet_avastha + get_shadbala_full → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S2
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S2
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S2 — Port to portal: get_planet_avastha + get_shadbala_full

## 1. Context

Two MCP surgical primitives — `get_planet_avastha` and `get_shadbala_full` — are not available
as portal RETRIEVAL_TOOLS. This session ports both.

**What they do:**

`get_planet_avastha`: Returns the avastha (planetary state) for a given planet from
`chart_facts` category "avastha", with classical meaning. Fallback chain:
1. chart_facts category "avastha" direct lookup
2. chart_facts category "dignity_scores" → infer avastha from dignity
3. Default "Mudita" (neutral-positive)

`get_shadbala_full`: Queries all shadbala component rows from chart_facts, groups by the
6 canonical components (Sthana, Dig, Kala, Cheshta, Naisargika, Drig), sums each, and
returns total virupa + rupa with sufficiency check against classical minimums.

**MCP source files (read-only references):**
- `platform-mcp/src/tools/get_planet_avastha.ts`
- `platform-mcp/src/tools/get_shadbala_full.ts`

**Portal target files (create):**
- `platform/src/lib/retrieve/get_planet_avastha.ts`
- `platform/src/lib/retrieve/get_shadbala_full.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/get_planet_avastha.ts` (create)
- `platform/src/lib/retrieve/get_shadbala_full.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registrations)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_2.1: `platform/src/lib/retrieve/get_planet_avastha.ts` exists and exports a RetrievalTool
- [ ] AC.1_2.2: `platform/src/lib/retrieve/get_shadbala_full.ts` exists and exports a RetrievalTool
- [ ] AC.1_2.3: Both tools registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_2.4: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_2.5: Commit message contains `UDA-1-S2`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source files

```bash
cat platform-mcp/src/tools/get_planet_avastha.ts
cat platform-mcp/src/tools/get_shadbala_full.ts
cat platform/src/lib/retrieve/chart_facts_query.ts | head -80  # for storage pattern
```

### Step 2 — Create get_planet_avastha.ts (portal version)

Implement using `getStorageClient()`:

```typescript
// platform/src/lib/retrieve/get_planet_avastha.ts
import { getStorageClient } from '@/lib/storage'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const AVASTHA_MEANINGS: Record<string, string> = {
  Lajjita: 'Ashamed — significations suppressed, shame, inhibition',
  Garvita: 'Proud — significations elevated, confidence, status',
  Kshudita: 'Hungry — significations unfulfilled, longing, dissatisfaction',
  Trushita: 'Thirsty — restless, unfulfilled desires',
  Mudita: 'Delighted — significations flow naturally, contentment',
  Kshobhita: 'Agitated — volatility, disturbance, conflict',
}

// ... implement execute() to query chart_facts for avastha row for the given planet
// with the three-step fallback from the MCP tool
```

### Step 3 — Create get_shadbala_full.ts (portal version)

Implement using `getStorageClient()`:

```typescript
// platform/src/lib/retrieve/get_shadbala_full.ts
const CLASSICAL_MINIMUMS: Record<string, number> = {
  Sun: 6.5, Moon: 6.0, Mars: 5.0, Mercury: 7.0, Jupiter: 6.5, Venus: 5.5, Saturn: 5.0,
}

const SHADBALA_COMPONENTS = [
  'sthana_bala', 'dig_bala', 'kala_bala', 'cheshta_bala', 'naisargika_bala', 'drig_bala',
]

// Query chart_facts WHERE category = 'shadbala', group by planet, sum components,
// compare to classical minimums, return roll-up
```

### Step 4 — Register in index.ts

```typescript
import * as getPlanetAvastha from './get_planet_avastha'
import * as getShadbalaFull from './get_shadbala_full'
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
git add platform/src/lib/retrieve/get_planet_avastha.ts \
        platform/src/lib/retrieve/get_shadbala_full.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S2): port get_planet_avastha + get_shadbala_full to portal

Avastha 3-step fallback chain; Shadbala 6-component roll-up with classical minimums.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "get_planet_avastha\|planet_avastha" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S2_AVASTHA: PASS'
grep -q "get_shadbala_full\|shadbala_full" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S2_SHADBALA: PASS'
git log --oneline -3 | grep -q 'UDA-1-S2' && echo 'GATE_UDA_1_S2_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S2_v1_0.md*
