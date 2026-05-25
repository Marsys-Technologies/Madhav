---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S3: chart_facts_query populated_count to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S3
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S3
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S3 — Backport chart_facts introspection fields to portal

## 1. Context

The MCP `platform-mcp/src/tools/query_chart_facts.ts` (enhanced TR-P3-S2) adds:
- `include_empty_counts: boolean` — when true, categories with 0 matching rows are still returned in the response (shows data coverage gaps)
- `populated_count` annotated on each returned category bucket — the number of rows with non-null values

The portal `platform/src/lib/retrieve/chart_facts_query.ts` has all 27 categories but omits both fields. This session adds them.

Both tools query the `chart_facts` table. The portal tool file name is `chart_facts_query.ts` (different from MCP's `query_chart_facts.ts`).

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/chart_facts_query.ts`

**must_not_touch:**
- `platform-mcp/src/tools/query_chart_facts.ts` (reference only)
- `platform/src/lib/retrieve/index.ts`
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_chart_facts.ts` — source of truth for the two new fields
2. `platform/src/lib/retrieve/chart_facts_query.ts` — current portal version

## 4. Acceptance Criteria

- [ ] AC.1: `include_empty_counts: z.boolean().optional().default(false)` added to input schema
- [ ] AC.2: When `include_empty_counts=true`, categories with 0 rows are included in response with `count: 0` and `populated_count: 0`
- [ ] AC.3: When `include_empty_counts=false` (default), behavior is identical to current (zero-count categories excluded)
- [ ] AC.4: Each returned category bucket includes `populated_count: number` — count of rows where the primary value field is NOT NULL
- [ ] AC.5: TypeScript compiles: `cd platform && npx tsc --noEmit`
- [ ] AC.6: Existing category filter / `categories[]` param behavior unchanged

## 5. Implementation Steps

### Step 1 — Read both files

```bash
cat platform-mcp/src/tools/query_chart_facts.ts
cat platform/src/lib/retrieve/chart_facts_query.ts
```

### Step 2 — Add input schema fields

In the portal tool's Zod schema, add:
```typescript
include_empty_counts: z.boolean().optional().default(false),
```

### Step 3 — Compute populated_count

After the main SQL query returns rows per category bucket, add a secondary count:
```sql
SELECT COUNT(*) as populated_count 
FROM chart_facts 
WHERE chart_id = $1 
  AND category = $2 
  AND value IS NOT NULL
```

Or compute it in-application from the returned rows. Port the approach from the MCP tool.

### Step 4 — Handle include_empty_counts

After assembling all category buckets:
```typescript
if (!include_empty_counts) {
  results = results.filter(bucket => bucket.count > 0);
}
```

### Step 5 — Attach populated_count to each bucket

Ensure each item in the returned array has:
```typescript
{ category: string, count: number, populated_count: number, rows: [...] }
```

### Step 6 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/chart_facts_query.ts
git commit -m "feat(UDA-Q-S3): backport chart_facts introspection fields to portal

- include_empty_counts: boolean (show zero-row categories)
- populated_count: number annotated per category bucket
- Existing filter/category behavior unchanged
- TypeScript clean

Quality gap closed: portal chart_facts_query now == MCP depth."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S3_v1_0.md*
