---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S1: Port query_transits_over_natal + query_yogas_active_now → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S1
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S1 — Port to portal: query_transits_over_natal + query_yogas_active_now

## 1. Context

Two MCP tools — `query_transits_over_natal` and `query_yogas_active_now` — exist only in
`platform-mcp/src/tools/` and are not available as portal RETRIEVAL_TOOLS. This session
ports both to the portal channel.

**MCP source files (read-only references):**
- `platform-mcp/src/tools/query_transits_over_natal.ts`
- `platform-mcp/src/tools/query_yogas_active_now.ts`

**Portal target files (create new):**
- `platform/src/lib/retrieve/query_transits_over_natal.ts`
- `platform/src/lib/retrieve/query_yogas_active_now.ts`

**Portal registration target (modify):**
- `platform/src/lib/retrieve/index.ts` — add both tools to RETRIEVAL_TOOLS

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_transits_over_natal.ts` (create)
- `platform/src/lib/retrieve/query_yogas_active_now.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registrations)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_1.1: `platform/src/lib/retrieve/query_transits_over_natal.ts` exists
- [ ] AC.1_1.2: `platform/src/lib/retrieve/query_yogas_active_now.ts` exists
- [ ] AC.1_1.3: Both tools are exported from `platform/src/lib/retrieve/index.ts` and appear in `RETRIEVAL_TOOLS`
- [ ] AC.1_1.4: Both tools conform to the `RetrievalTool` interface (have `name`, `description`, `execute` function)
- [ ] AC.1_1.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_1.6: Commit message contains `UDA-1-S1`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source files

```bash
cat platform-mcp/src/tools/query_transits_over_natal.ts
cat platform-mcp/src/tools/query_yogas_active_now.ts
```

Also read the portal RetrievalTool interface:
```bash
cat platform/src/lib/retrieve/types.ts | head -60
```

And a sample portal tool for interface pattern:
```bash
cat platform/src/lib/retrieve/query_dasha_periods.ts | head -80
```

### Step 2 — Create query_transits_over_natal.ts (portal version)

The portal version wraps the same computation logic but uses:
- `getStorageClient()` for DB access (via the portal's storage abstraction)
- The `RetrievalTool` interface with `execute(input: QueryPlan): Promise<ToolBundleResult>`
- The existing portal `query_ephemeris` tool as a dependency (call it directly)
- The existing portal `chart_facts_query` tool to fetch natal longitudes

Key computation: given `date_range`, `target_natal_point`, `orb_degrees`, `transit_planets`,
`aspects` — find transit windows where a transit planet forms an aspect to the natal point.

Port the algorithm directly from the MCP tool, adapting to use portal storage patterns.

### Step 3 — Create query_yogas_active_now.ts (portal version)

The portal version:
1. Calls `chart_facts_query` with `category: "yoga"` to get natal yoga rows
2. Calls `query_dasha_periods` with `as_of_date` (default today) to get active MD/AD
3. Classifies each yoga as "active", "latent", or "dormant" based on planet match
4. Returns classified list with activation reasons

Port the classification algorithm from the MCP tool.

### Step 4 — Add to index.ts

Add imports and RETRIEVAL_TOOLS entries at the end of `platform/src/lib/retrieve/index.ts`:

```typescript
// UDA-1-S1: ports from MCP — transit-to-natal aspects + yoga activation
import * as queryTransitsOverNatal from './query_transits_over_natal'
import * as queryYogasActiveNow from './query_yogas_active_now'
```

Add to RETRIEVAL_TOOLS array:
```typescript
queryTransitsOverNatal.tool,
queryYogasActiveNow.tool,
```

(Use whatever export name the tool uses, following the existing pattern in index.ts.)

### Step 5 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

Fix any errors.

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_transits_over_natal.ts \
        platform/src/lib/retrieve/query_yogas_active_now.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S1): port query_transits_over_natal + query_yogas_active_now to portal

Both tools adapted from MCP and registered in RETRIEVAL_TOOLS.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "query_transits_over_natal\|transits_over_natal" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S1_TRANSITS: PASS'
grep -q "query_yogas_active_now\|yogas_active_now" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S1_YOGAS: PASS'
test -f platform/src/lib/retrieve/query_transits_over_natal.ts && echo 'GATE_UDA_1_S1_FILE_TRANSITS: PASS'
test -f platform/src/lib/retrieve/query_yogas_active_now.ts && echo 'GATE_UDA_1_S1_FILE_YOGAS: PASS'
git log --oneline -3 | grep -q 'UDA-1-S1' && echo 'GATE_UDA_1_S1_COMMIT: PASS'
```

All 5 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S1_v1_0.md*
