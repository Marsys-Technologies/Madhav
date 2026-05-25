---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S6: msr_sql filter enrichment to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S6
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S6
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S6 — Backport MCP query_signals filter richness to portal msr_sql

## 1. Context

The MCP `platform-mcp/src/tools/query_signals.ts` (enhanced TR-P1-S2) has filter params the portal `platform/src/lib/retrieve/msr_sql.ts` is missing:
- `dasha_lord: string` — filter signals where dasha_lord field matches a planet
- `valence: enum('positive','negative','mixed','neutral')` — filter by signal valence
- `temporal_activation: boolean` — filter for temporally active signals only
- `forward_looking: boolean` — filter prospective signals only
- `domains: string[]` — multi-domain filter (portal only has single `domain`)

Meanwhile portal's `msr_sql.ts` has LL.1 calibration that MCP is missing (addressed in UDA-Q-S7).

This session adds the MCP's richer filters to the portal `msr_sql.ts`. The LL.1 calibration already present in portal is PRESERVED.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/msr_sql.ts`

**must_not_touch:**
- `platform-mcp/src/tools/query_signals.ts` (reference only)
- `platform/src/lib/retrieve/index.ts`
- `01_FACTS_LAYER/ll1_weights_promoted_v1_0.json` (read-only if needed)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_signals.ts` — source of filter-rich params
2. `platform/src/lib/retrieve/msr_sql.ts` — current portal version with LL.1 calibration
3. `01_FACTS_LAYER/ll1_weights_promoted_v1_0.json` — LL.1 weight file (reference for calibration logic)

## 4. Acceptance Criteria

- [ ] AC.1: `dasha_lord: z.string().optional()` added — filters `WHERE dasha_lord = $N`
- [ ] AC.2: `valence: z.enum(['positive','negative','mixed','neutral']).optional()` added — filters `WHERE valence = $N`
- [ ] AC.3: `temporal_activation: z.boolean().optional()` added — when true, filters `WHERE temporal_activation = true`
- [ ] AC.4: `forward_looking: z.boolean().optional()` added — when true, filters for prospective signals
- [ ] AC.5: `domains: z.array(z.string()).optional()` added — when provided, filters `WHERE domain = ANY($N)` (multi-domain)
- [ ] AC.6: Existing LL.1 calibration (domain-specific confidence floors: finance/wealth at 0.35, default 0.55) is PRESERVED exactly — do not remove or alter calibration code
- [ ] AC.7: Existing `domain` single-filter param preserved for backward compat (if `domain` provided without `domains`, still works)
- [ ] AC.8: TypeScript compiles: `cd platform && npx tsc --noEmit`

## 5. Implementation Steps

### Step 1 — Read both files

```bash
cat platform-mcp/src/tools/query_signals.ts
cat platform/src/lib/retrieve/msr_sql.ts
```

Identify the LL.1 calibration block in `msr_sql.ts` — mark it clearly with a comment like `// LL.1 CALIBRATION — DO NOT REMOVE` so it's protected.

### Step 2 — Add params to Zod schema

Add the five new optional params to the existing schema without touching existing params:
```typescript
dasha_lord: z.string().optional(),
valence: z.enum(['positive', 'negative', 'mixed', 'neutral']).optional(),
temporal_activation: z.boolean().optional(),
forward_looking: z.boolean().optional(),
domains: z.array(z.string()).optional(),
```

### Step 3 — Add SQL filter clauses

In the WHERE clause builder (or wherever `AND` conditions are assembled), add:
```typescript
if (dasha_lord) { clauses.push(`dasha_lord = $${params.push(dasha_lord)}`); }
if (valence) { clauses.push(`valence = $${params.push(valence)}`); }
if (temporal_activation !== undefined) { clauses.push(`temporal_activation = $${params.push(temporal_activation)}`); }
if (forward_looking !== undefined) { clauses.push(`forward_looking = $${params.push(forward_looking)}`); }
if (domains && domains.length > 0) { clauses.push(`domain = ANY($${params.push(domains)})`); }
```

If columns don't exist in the table, log a warning and skip that filter rather than erroring. Check actual column names against the MCP tool's SQL.

### Step 4 — Preserve LL.1 calibration

After the SQL query returns results, the LL.1 weight adjustment must still run on the result set. Do NOT remove the calibration block. Verify it still executes after the new filters are applied.

### Step 5 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/msr_sql.ts
git commit -m "feat(UDA-Q-S6): backport MCP filter richness to portal msr_sql

Added filter params from query_signals:
- dasha_lord: string filter
- valence: positive|negative|mixed|neutral enum
- temporal_activation: boolean filter
- forward_looking: boolean filter
- domains: string[] multi-domain filter

LL.1 calibration PRESERVED (domain-specific confidence floors intact).
Backward compat: existing domain + min_confidence params unchanged.
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S6_v1_0.md*
