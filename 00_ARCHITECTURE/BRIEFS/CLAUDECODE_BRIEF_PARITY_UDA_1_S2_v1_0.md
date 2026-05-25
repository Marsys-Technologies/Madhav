---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S2: Port get_planet_avastha + get_shadbala_full to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S2
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S2
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S2 — Port avastha + shadbala tools to portal

## 1. Context

Two MCP-only tools to port. **Important:** the portal may already have a `shadbala_query.ts` — check before creating a new file. If an equivalent exists, compare schemas and either upgrade the existing file or register the MCP version under the new name.

- `get_planet_avastha` — returns the avastha (planetary state/dignity) breakdown for each planet: bal avastha, jagrut/swapna/sushupti, shayana/upaveshana/netrapani, etc. Rich planetary state data used in interpretation.
- `get_shadbala_full` — returns the complete shadbala (six-fold strength) calculation: sthana bala, dig bala, kala bala, chesta bala, naisargika bala, drig bala, with totals and relative rankings.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/get_planet_avastha.ts` (create)
- `platform/src/lib/retrieve/get_shadbala_full.ts` (create, or upgrade existing `shadbala_query.ts` if present)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- MCP tool files (reference only)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/get_planet_avastha.ts`
2. `platform-mcp/src/tools/get_shadbala_full.ts`
3. `platform/src/lib/retrieve/` — list to check for existing shadbala tool
4. `platform/src/lib/retrieve/index.ts` — registration pattern

## 4. Acceptance Criteria

- [ ] AC.1: `get_planet_avastha` available in portal RETRIEVAL_TOOLS (new file or upgraded existing)
- [ ] AC.2: `get_shadbala_full` available in portal RETRIEVAL_TOOLS (new file or upgraded existing `shadbala_query.ts` — if upgrading, keep original name registered too for backward compat)
- [ ] AC.3: Both tools registered in `index.ts` with exact names matching MCP tool names
- [ ] AC.4: Input schemas match MCP versions exactly (same params, same types)
- [ ] AC.5: TypeScript compiles clean
- [ ] AC.6: If an existing portal shadbala tool was upgraded, old tool name still resolves (add an alias entry in `index.ts`)

## 5. Implementation Steps

### Step 1 — Check for existing tools

```bash
ls platform/src/lib/retrieve/ | grep -i "shadbala\|avastha"
```

If `shadbala_query.ts` exists:
```bash
cat platform/src/lib/retrieve/shadbala_query.ts
cat platform-mcp/src/tools/get_shadbala_full.ts
```

Compare schemas. If MCP has more fields (likely), upgrade the portal file to match but keep both `shadbala_query` AND `get_shadbala_full` registered (one can delegate to the other).

### Step 2 — Create/upgrade files

Follow UDA-1-S1 porting pattern: copy SQL + schema from MCP, adapt to portal DB client.

For `get_planet_avastha.ts`: straightforward port — no existing equivalent.
For `get_shadbala_full.ts`: if upgrading existing, add `get_shadbala_full` as an alias export that calls the upgraded `shadbala_query` with full params.

### Step 3 — Register in index.ts

Add new exports and RETRIEVAL_TOOLS entries.

### Step 4 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/get_planet_avastha.ts
git add platform/src/lib/retrieve/get_shadbala_full.ts  # or shadbala_query.ts if upgraded
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S2): port get_planet_avastha + get_shadbala_full to portal

Both avastha and full shadbala strength now available in portal RETRIEVAL_TOOLS.
<note if shadbala_query.ts was upgraded; old name preserved for compat>
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S2_v1_0.md*
