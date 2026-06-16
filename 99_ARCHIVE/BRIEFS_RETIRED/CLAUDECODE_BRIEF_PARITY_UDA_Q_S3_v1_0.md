---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-Q-S3: Quality Backport chart_facts_query populated_count → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S3
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S3
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-Q-S3 — Quality Backport: chart_facts_query populated_count → portal

## 1. Context

The MCP version of `query_chart_facts` (`platform-mcp/src/tools/query_chart_facts.ts`) has two
enhancements not present in the portal `chart_facts_query.ts`:

1. **`include_empty_counts: boolean`** — when true, appends a `category_counts` object showing
   how many rows each category has (including zero-count categories). Useful for inventory / debugging.
2. **`populated_count` annotation** — each returned row (or the summary) carries a `populated_count`
   field showing the total number of non-null `value_json` rows for that category.

This session adds both enhancements to `platform/src/lib/retrieve/chart_facts_query.ts`.

**Source of truth (read-only):** `platform-mcp/src/tools/query_chart_facts.ts`
**Target to modify:** `platform/src/lib/retrieve/chart_facts_query.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/chart_facts_query.ts`

**must_not_touch:**
- `platform-mcp/` (source reference only)
- `platform/src/lib/retrieve/index.ts`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.Q3.1: `ChartFactsQueryInput` includes `include_empty_counts?: boolean`
- [ ] AC.Q3.2: The response type or return shape includes a `populated_count` field (on the summary or per-row)
- [ ] AC.Q3.3: When `include_empty_counts=true`, the tool issues an additional COUNT query per category and returns results
- [ ] AC.Q3.4: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.Q3.5: Commit message contains `UDA-Q-S3`

---

## 4. Step-by-Step Execution

### Step 1 — Read both tools

```bash
cat platform-mcp/src/tools/query_chart_facts.ts
cat platform/src/lib/retrieve/chart_facts_query.ts
```

### Step 2 — Add include_empty_counts to input interface

```typescript
/** When true, appends category_counts: Record<category, number> to the response. */
include_empty_counts?: boolean
```

### Step 3 — Add populated_count to response type

In the return value / ToolBundle content, add:
```typescript
populated_count?: number  // total non-null value_json rows for the queried category
```

This can be computed alongside the main query:
```typescript
const countResult = await storage.query(
  `SELECT COUNT(*) as cnt FROM chart_facts WHERE chart_id=$1 AND value_json IS NOT NULL ${categoryClause}`,
  params
)
const populated_count = parseInt(countResult.rows[0]?.cnt ?? '0', 10)
```

### Step 4 — Implement include_empty_counts

When `input.include_empty_counts === true`, after the main query fetch all categories and their counts:
```typescript
const categoryCounts = await storage.query(
  `SELECT category, COUNT(*) as cnt FROM chart_facts WHERE chart_id=$1 GROUP BY category ORDER BY category`,
  [chartId]
)
```
Return as `category_counts: Object.fromEntries(categoryCounts.rows.map(r => [r.category, parseInt(r.cnt)]))`

### Step 5 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/chart_facts_query.ts
git commit -m "feat(UDA-Q-S3): backport include_empty_counts + populated_count to portal chart_facts_query

Matches MCP quality level. tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "include_empty_counts\|populated_count" platform/src/lib/retrieve/chart_facts_query.ts && echo 'GATE_UDA_Q_S3_FIELDS: PASS'
git log --oneline -3 | grep -q 'UDA-Q-S3' && echo 'GATE_UDA_Q_S3_COMMIT: PASS'
```

All 2 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S3_v1_0.md*
