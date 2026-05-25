---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S4: Quality Backport lel_query chart_state + significance enum → MCP"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S4
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S4
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S4 — Quality Backport: lel_query chart_state + significance enum → MCP

## 1. Context

The portal version of `lel_query` (`platform/src/lib/retrieve/lel_query.ts`) is ahead of the
MCP version (`platform-mcp/src/tools/lel_query.ts`) in two ways:

1. **`chart_state` column** — the portal tool retrieves the `chart_state` JSONB column from
   `life_events` (Swiss Ephemeris planetary positions at the time of each event). The MCP
   version does not include this field in its SELECT or output.
2. **Significance enum** — the portal tool filters by significance using a proper
   `"major" | "moderate" | "minor"` tier enum (mapped to float ranges internally).
   The MCP uses a raw float `min_significance: float` which callers must know the scale for.

This session backports both enhancements into `platform-mcp/src/tools/lel_query.ts`.

**Source of truth (read-only):** `platform/src/lib/retrieve/lel_query.ts`
**Target to modify:** `platform-mcp/src/tools/lel_query.ts`

---

## 2. Scope

**may_touch:**
- `platform-mcp/src/tools/lel_query.ts`

**must_not_touch:**
- `platform/src/lib/retrieve/lel_query.ts` (source reference only)
- `platform-mcp/src/server.ts` (no registration changes)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.Q4.1: `platform-mcp/src/tools/lel_query.ts` includes `chart_state` in the SELECT query or response enrichment
- [ ] AC.Q4.2: The MCP tool accepts `significance_tier?: "major" | "moderate" | "minor"` in its Zod schema (in addition to or replacing the raw float)
- [ ] AC.Q4.3: `significance_tier` is mapped to float thresholds: `major ≥ 0.8`, `moderate ≥ 0.5`, `minor ≥ 0.2`
- [ ] AC.Q4.4: `cd platform-mcp && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q4.5: Commit message contains `UDA-Q-S4`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tool files

```bash
cat platform/src/lib/retrieve/lel_query.ts
cat platform-mcp/src/tools/lel_query.ts
```

Understand:
- How the portal tool queries `chart_state` from the DB
- The portal's significance tier enum logic
- How the MCP tool calls `callPlatformPrimitive` (it proxies to the portal lel_query)

### Step 2 — Add significance_tier to Zod schema

In `platform-mcp/src/tools/lel_query.ts`, add to the Zod schema:

```typescript
significance_tier: z.enum(['major', 'moderate', 'minor']).optional().describe(
  'Filter by significance tier. major=≥0.8, moderate=≥0.5, minor=≥0.2. ' +
  'Alternative to min_significance float. If both are set, significance_tier takes precedence.'
),
```

### Step 3 — Map significance_tier to float before passing to platform primitive

```typescript
let resolvedMinSignificance = args.min_significance
if (args.significance_tier) {
  const tierMap = { major: 0.8, moderate: 0.5, minor: 0.2 }
  resolvedMinSignificance = tierMap[args.significance_tier]
}
```

Pass `resolvedMinSignificance` to `callPlatformPrimitive`.

### Step 4 — Add chart_state to the response

The MCP tool calls `callPlatformPrimitive('lel_query', ...)` which proxies to the portal tool.
If the portal tool already returns `chart_state`, it will flow through automatically. Verify
by checking the portal tool's response shape. If `chart_state` is not being returned by the
platform primitive, add it explicitly to the SELECT or the response enrichment in `lel_query.ts`.

If the MCP is directly querying the DB (check the source), add:
```typescript
SELECT *, chart_state FROM life_events WHERE ...
```

### Step 5 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform-mcp && npx tsc --noEmit
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform-mcp/src/tools/lel_query.ts
git commit -m "feat(UDA-Q-S4): backport chart_state + significance enum to MCP lel_query

Adds chart_state retrieval and significance_tier enum (major/moderate/minor)
to match portal quality level. tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "chart_state" platform-mcp/src/tools/lel_query.ts && echo 'GATE_UDA_Q_S4_CHART_STATE: PASS'
grep -q "major\|moderate\|minor" platform-mcp/src/tools/lel_query.ts && echo 'GATE_UDA_Q_S4_SIGNIFICANCE: PASS'
git log --oneline -3 | grep -q 'UDA-Q-S4' && echo 'GATE_UDA_Q_S4_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S4_v1_0.md*
