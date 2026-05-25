---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S4: Port query_planetary_period_predictions to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S4
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S4
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S4 — Port planetary period predictions tool to portal

## 1. Context

`query_planetary_period_predictions` returns logged predictions indexed to a specific dasha period — pulling from the Learning Layer's prediction log (M4 infrastructure). It answers: "what predictions have been logged for the current/specified MD-AD combination?" This tool connects the dasha-period context to the prospective prediction log, enabling the portal to surface calibrated, time-indexed predictions in the same way MCP does.

Currently MCP-only. Without it, the portal planner cannot access logged predictions even when a dasha question is asked.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_planetary_period_predictions.ts` (create)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- `platform-mcp/src/tools/query_planetary_period_predictions.ts` (reference only)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_planetary_period_predictions.ts`
2. `platform/src/lib/retrieve/index.ts`
3. `06_LEARNING_LAYER/` — scan for any prediction log schema reference

## 4. Acceptance Criteria

- [ ] AC.1: `query_planetary_period_predictions` registered in portal RETRIEVAL_TOOLS
- [ ] AC.2: Input schema matches MCP (chart_id, maha_dasha_lord, antar_dasha_lord, optional: date_from/date_to range)
- [ ] AC.3: Output: prediction rows with prediction_text, confidence, horizon, logged_at, outcome_status
- [ ] AC.4: If the prediction log table doesn't exist in the portal DB (M4 infra), the tool returns an empty array gracefully (not an error)
- [ ] AC.5: TypeScript compiles clean

## 5. Implementation Steps

### Step 1 — Read MCP tool

```bash
cat platform-mcp/src/tools/query_planetary_period_predictions.ts
```

Note the SQL table name (likely `mcp_predictions`, `prediction_log`, or `learning_layer_predictions`).

### Step 2 — Check if table exists in portal DB schema

```bash
grep -r "prediction\|mcp_predictions\|prediction_log" platform/supabase/migrations/ | head -20
```

Or check migration files for the table. If found, the portal DB has the table. If not, the tool should return `{ predictions: [], note: "Prediction log not yet available in this environment" }`.

### Step 3 — Create portal tool

```typescript
// Graceful empty-result if table doesn't exist
export async function queryPlanetaryPeriodPredictions(input) {
  try {
    const result = await pool.query(SQL, params);
    return { predictions: result.rows };
  } catch (err) {
    if (err.message?.includes('does not exist')) {
      return { predictions: [], note: 'Prediction log table not available' };
    }
    throw err;
  }
}
```

### Step 4 — Register and compile

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_planetary_period_predictions.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S4): port query_planetary_period_predictions to portal

Learning Layer prediction log now queryable from portal.
Graceful empty result if table unavailable.
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S4_v1_0.md*
