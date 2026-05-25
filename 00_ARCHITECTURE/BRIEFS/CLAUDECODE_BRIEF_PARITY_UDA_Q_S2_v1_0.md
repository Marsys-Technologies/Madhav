---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S2: query_ephemeris enhancements to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S2
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S2
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S2 — Backport ephemeris enhancements to portal

## 1. Context

The MCP `platform-mcp/src/tools/query_ephemeris.ts` (enhanced by TR-P1-S2) has:
- Structured `date_range: { from: string, to: string }` object (required)
- `sample_step: enum('1d','7d','30d')` parameter (default `'1d'`)
- `return_changes_only: boolean` parameter (default `false`) — omits rows where no sign/nakshatra change occurred
- 1825-day (5-year) span guard with a clean error message

The portal `platform/src/lib/retrieve/query_ephemeris.ts` uses flat `start_date`/`end_date` string params, has no `sample_step`, no `return_changes_only`, and no span guard. This session brings the portal version to full parity.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_ephemeris.ts`

**must_not_touch:**
- `platform-mcp/src/tools/query_ephemeris.ts` (reference only)
- `platform/src/lib/retrieve/index.ts`
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_ephemeris.ts` — source of truth
2. `platform/src/lib/retrieve/query_ephemeris.ts` — current portal version

## 4. Acceptance Criteria

- [ ] AC.1: Input schema accepts `date_range: z.object({ from: z.string(), to: z.string() })` as primary date input (keep backward compat with `start_date`/`end_date` via alias or deprecation comment if present callers need them)
- [ ] AC.2: `sample_step: z.enum(['1d','7d','30d']).optional().default('1d')` added
- [ ] AC.3: `return_changes_only: z.boolean().optional().default(false)` added
- [ ] AC.4: Span guard: if `(to - from) > 1825 days`, return error `{ error: "Date range exceeds 5-year maximum (1825 days). Split into smaller windows." }`
- [ ] AC.5: When `return_changes_only=true`, rows where sign AND nakshatra are unchanged from previous row are filtered out
- [ ] AC.6: When `sample_step='7d'` or `'30d'`, query respects the step (either SQL `WHERE date_trunc` or application-side sampling)
- [ ] AC.7: TypeScript compiles: `cd platform && npx tsc --noEmit`
- [ ] AC.8: Existing queries with `start_date`/`end_date` still work (backward compatible)

## 5. Implementation Steps

### Step 1 — Read both files

```bash
cat platform-mcp/src/tools/query_ephemeris.ts
cat platform/src/lib/retrieve/query_ephemeris.ts
```

### Step 2 — Update input schema

Replace or augment the existing schema. Accept both forms:
```typescript
const inputSchema = z.object({
  // New primary form (matches MCP)
  date_range: z.object({ from: z.string(), to: z.string() }).optional(),
  // Legacy backward-compat
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  sample_step: z.enum(['1d', '7d', '30d']).optional().default('1d'),
  return_changes_only: z.boolean().optional().default(false),
  // existing params preserved
  planets: z.array(z.string()).optional(),
});
```

Resolve `from`/`to` in handler: prefer `date_range` if present, fall back to `start_date`/`end_date`.

### Step 3 — Add span guard

```typescript
const fromMs = new Date(from).getTime();
const toMs = new Date(to).getTime();
const days = (toMs - fromMs) / (1000 * 60 * 60 * 24);
if (days > 1825) {
  return { error: 'Date range exceeds 5-year maximum (1825 days). Split into smaller windows.' };
}
```

### Step 4 — Implement sample_step

For `'7d'` and `'30d'`, apply post-query filtering on the result rows (keep every Nth row where N = step days), OR add a SQL `AND EXTRACT(DOY FROM date) % <step> = 0` clause. Port the approach from the MCP tool.

### Step 5 — Implement return_changes_only

Post-filter: keep a row only if `sign` or `nakshatra` differs from the previous row for that planet. Port from the MCP tool.

### Step 6 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_ephemeris.ts
git commit -m "feat(UDA-Q-S2): backport ephemeris enhancements to portal

- date_range: {from, to} object input (legacy start_date/end_date kept)
- sample_step: '1d' | '7d' | '30d' (default '1d')
- return_changes_only: boolean (filters unchanged sign/nakshatra rows)
- 1825-day span guard with clean error message
- TypeScript clean

Quality gap closed: portal query_ephemeris now == MCP depth."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S2_v1_0.md*
