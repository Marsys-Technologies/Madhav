---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S5: Port query_dasamsha_career + query_shashtiamsha to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S5
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S5
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S5 — Port D10 career + D60 shashtiamsha tools to portal

## 1. Context

Two divisional chart tools:
- `query_dasamsha_career` — queries D10 (Dasamsha) divisional chart data for career/profession analysis. Returns the D10 lagna, planetary positions in D10, and career-relevant signals. Essential for career questions.
- `query_shashtiamsha` — queries D60 (Shashtiamsha), the finest divisional (1/60th division). Each D60 lord carries specific classical qualities. Used for past-life karma and overall life path analysis.

**Important:** The portal has `divisional_query.ts` — check if it already covers D10 and D60. If it does, assess whether the MCP-specific tools add anything beyond what `divisional_query` already returns. Port only if the MCP tools add distinct value (more targeted SQL, career-specific signals, D60 lord assignments).

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_dasamsha_career.ts` (create if needed)
- `platform/src/lib/retrieve/query_shashtiamsha.ts` (create if needed)
- `platform/src/lib/retrieve/divisional_query.ts` (upgrade if covering both — optional)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- MCP tool files (reference only)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_dasamsha_career.ts`
2. `platform-mcp/src/tools/query_shashtiamsha.ts`
3. `platform/src/lib/retrieve/divisional_query.ts` — check overlap
4. `platform/src/lib/retrieve/index.ts`

## 4. Acceptance Criteria

- [ ] AC.1: `query_dasamsha_career` in portal RETRIEVAL_TOOLS — either new file or registered alias
- [ ] AC.2: `query_shashtiamsha` in portal RETRIEVAL_TOOLS — either new file or registered alias
- [ ] AC.3: If `divisional_query` already covers both by passing `division: 10` or `division: 60`, add named wrappers that pre-fill those params (for planner discoverability)
- [ ] AC.4: D10-specific career signals returned (not just generic divisional positions)
- [ ] AC.5: D60 shashtiamsha lord names returned per planet
- [ ] AC.6: TypeScript compiles clean

## 5. Implementation Steps

### Step 1 — Compare MCP tools vs portal divisional_query

```bash
cat platform-mcp/src/tools/query_dasamsha_career.ts
cat platform-mcp/src/tools/query_shashtiamsha.ts
cat platform/src/lib/retrieve/divisional_query.ts
```

If `divisional_query` is a generic divisional tool (takes `division_number` param), create thin named wrappers:
```typescript
// query_dasamsha_career.ts
export const queryDasamshhaCareerTool = {
  name: 'query_dasamsha_career',
  description: 'Query D10 Dasamsha divisional chart for career analysis',
  inputSchema: z.object({ chart_id: z.string().uuid() }),
  execute: (input) => divisionalQuery({ ...input, division: 10, include_career_signals: true }),
};
```

If `divisional_query` doesn't cover career signals, create a full port from MCP.

### Step 2 — Create files and register

Follow UDA-1-S1 porting pattern.

### Step 3 — TypeScript check and commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
git add platform/src/lib/retrieve/query_dasamsha_career.ts
git add platform/src/lib/retrieve/query_shashtiamsha.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S5): port query_dasamsha_career + query_shashtiamsha to portal

D10 career tool and D60 shashtiamsha tool now in portal RETRIEVAL_TOOLS.
<note if wrappers over divisional_query or full ports>
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S5_v1_0.md*
