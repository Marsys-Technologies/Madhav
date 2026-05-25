---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S1: Port query_transits_over_natal + query_yogas_active_now to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S1
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S1 — Port transit-over-natal + yogas-active tools to portal

## 1. Context

These two MCP tools exist only in the MCP sidecar and are unavailable to the portal (both Classic Marsys planner path and Claude-style agentic loop). Portal routing cannot call them even if the planner proposes them — `executeMCPTool()` returns `ERROR: Unknown tool`.

**Pattern for all UDA-1 sessions:** Read the MCP tool → create a matching portal retrieve file → register in `index.ts` → TypeScript check → commit. The portal file wraps the same SQL, adapted to the portal's DB connection pattern (pg pool, not MCP's DB client).

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_transits_over_natal.ts` (create)
- `platform/src/lib/retrieve/query_yogas_active_now.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add two registrations)

**must_not_touch:**
- `platform-mcp/src/tools/query_transits_over_natal.ts` (reference only)
- `platform-mcp/src/tools/query_yogas_active_now.ts` (reference only)
- Any `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_transits_over_natal.ts` — MCP source
2. `platform-mcp/src/tools/query_yogas_active_now.ts` — MCP source
3. `platform/src/lib/retrieve/index.ts` — to understand registration pattern
4. One existing portal tool (e.g., `platform/src/lib/retrieve/query_transit_event.ts`) — to understand the portal DB connection pattern

## 4. Acceptance Criteria

- [ ] AC.1: `platform/src/lib/retrieve/query_transits_over_natal.ts` created — matches MCP input schema
- [ ] AC.2: `platform/src/lib/retrieve/query_yogas_active_now.ts` created — matches MCP input schema
- [ ] AC.3: Both tools registered in `platform/src/lib/retrieve/index.ts` RETRIEVAL_TOOLS array
- [ ] AC.4: Both tools use the portal's DB connection pattern (not MCP's pattern)
- [ ] AC.5: Tool names in `index.ts` exactly match: `query_transits_over_natal` and `query_yogas_active_now`
- [ ] AC.6: TypeScript compiles: `cd platform && npx tsc --noEmit`
- [ ] AC.7: No import errors — all dependencies exist in portal codebase

## 5. Implementation Pattern (apply to both tools)

### Step 1 — Read the MCP implementation

```bash
cat platform-mcp/src/tools/query_transits_over_natal.ts
cat platform-mcp/src/tools/query_yogas_active_now.ts
```

For each tool, note:
- The Zod input schema (all params)
- The SQL query string and parameterization
- The output row shape
- Any helper functions

### Step 2 — Read the portal DB pattern

```bash
cat platform/src/lib/retrieve/query_transit_event.ts
head -60 platform/src/lib/retrieve/index.ts
```

Note: the portal uses a different DB client/pool than MCP. Adapt the MCP tool's `db.query()` calls to the portal's equivalent (likely `pool.query()` or a `withClient()` wrapper).

### Step 3 — Create portal files

Create `platform/src/lib/retrieve/query_transits_over_natal.ts`:
```typescript
// Ported from platform-mcp/src/tools/query_transits_over_natal.ts
// UDA-1-S1: Universal Parity Campaign
import { z } from 'zod';
import { <portal_db_import> } from '<portal_db_path>';

const inputSchema = z.object({
  // ... (copy from MCP tool) ...
});

export async function queryTransitsOverNatal(input: z.infer<typeof inputSchema>) {
  const validated = inputSchema.parse(input);
  // ... (adapted SQL from MCP tool) ...
}

export const queryTransitsOverNatalTool = {
  name: 'query_transits_over_natal',
  description: '<copy from MCP tool>',
  inputSchema,
  execute: queryTransitsOverNatal,
};
```

Repeat for `query_yogas_active_now.ts`.

### Step 4 — Register in index.ts

In `platform/src/lib/retrieve/index.ts`, add:
```typescript
import { queryTransitsOverNatalTool } from './query_transits_over_natal';
import { queryYogasActiveNowTool } from './query_yogas_active_now';
```

And add both to the RETRIEVAL_TOOLS array.

### Step 5 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_transits_over_natal.ts
git add platform/src/lib/retrieve/query_yogas_active_now.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S1): port query_transits_over_natal + query_yogas_active_now to portal

Both tools now available in portal RETRIEVAL_TOOLS (Classic + Claude-style).
Adapted from MCP implementations; portal DB connection pattern applied.
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S1_v1_0.md*
