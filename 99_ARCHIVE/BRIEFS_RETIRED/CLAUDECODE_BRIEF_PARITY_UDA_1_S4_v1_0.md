---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S4: Port query_planetary_period_predictions → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S4
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S4
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S4 — Port to portal: query_planetary_period_predictions

## 1. Context

`query_planetary_period_predictions` is a MCP composition recipe that retrieves classical shastra
predictions for MD/AD planetary period combinations by composing `vector_search` +
`read_classical_text` primitives. It is not available as a portal RETRIEVAL_TOOL.

**What it does:**
1. Builds a semantic query: `"${maha_dasha_lord} dasha ${antar_dasha_lord} predictions effects results"`
2. Calls `vector_search(query, top_k=15)` for semantic similarity
3. Calls `read_classical_text(query, limit=15)` for keyword-ranked classical chunks
4. Merges + deduplicates by `chunk_id` (higher relevance_score wins)
5. Filters: only chunks where content contains `maha_dasha_lord` (case-insensitive)
6. Sorts by relevance_score descending; returns top `max_results`
7. Derives school from `text_id`

**MCP source (read-only):** `platform-mcp/src/tools/query_planetary_period_predictions.ts`
**Portal target (create):** `platform/src/lib/retrieve/query_planetary_period_predictions.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_planetary_period_predictions.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registration)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_4.1: `platform/src/lib/retrieve/query_planetary_period_predictions.ts` exists and exports a RetrievalTool
- [ ] AC.1_4.2: Tool registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_4.3: Tool accepts `maha_dasha_lord` and `antar_dasha_lord` params and calls portal `vector_search` + `classical_text_search_tool` (the portal equivalents)
- [ ] AC.1_4.4: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_4.5: Commit message contains `UDA-1-S4`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source and portal equivalents

```bash
cat platform-mcp/src/tools/query_planetary_period_predictions.ts
cat platform/src/lib/retrieve/vector_search.ts | head -60
cat platform/src/lib/retrieve/classical_text_search_tool.ts | head -60
```

### Step 2 — Create query_planetary_period_predictions.ts (portal version)

The portal version calls the portal's `vector_search` and `classical_text_search_tool`
tools directly (calling their `execute()` methods) rather than using the MCP `callPlatformPrimitive`.

```typescript
import { getStorageClient } from '@/lib/storage'
import { vectorSearchTool } from './vector_search'       // import the actual tool
import { classicalTextSearchTool } from './classical_text_search_tool'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

// Build query, call both tools, merge and deduplicate, filter and sort
```

Port the school derivation map from the MCP tool (maps text_id to tradition name).

### Step 3 — Register in index.ts

```typescript
import * as queryPlanetaryPeriodPredictions from './query_planetary_period_predictions'
```

Add to RETRIEVAL_TOOLS.

### Step 4 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_planetary_period_predictions.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S4): port query_planetary_period_predictions to portal

Classical MD/AD prediction recipes via vector_search + classical text merge.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "query_planetary_period_predictions\|planetary_period_predictions" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S4_PPP: PASS'
test -f platform/src/lib/retrieve/query_planetary_period_predictions.ts && echo 'GATE_UDA_1_S4_FILE: PASS'
git log --oneline -3 | grep -q 'UDA-1-S4' && echo 'GATE_UDA_1_S4_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S4_v1_0.md*
