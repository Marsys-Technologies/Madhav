---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S7: LL.1 calibration to MCP query_signals"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S7
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S7
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S7 — Backport LL.1 calibration to MCP query_signals

## 1. Context

The portal `platform/src/lib/retrieve/msr_sql.ts` has LL.1 calibrated confidence floors:
- Finance/wealth domain: floor = 0.35 (lower than default because these signals have noisier activation patterns)
- Default floor: 0.55
- Ordering: `ORDER BY confidence * significance DESC` (weighted composite)
- Weights sourced from `01_FACTS_LAYER/ll1_weights_promoted_v1_0.json`

The MCP `platform-mcp/src/tools/query_signals.ts` returns raw uncalibrated rows — whatever confidence values are stored in the DB, no floor adjustment, plain `ORDER BY confidence DESC`.

This matters because the MCP channel (used by external acharya-grade clients) should serve the same calibration-adjusted signal ranking as the portal, not raw DB values which may over-represent low-confidence signals.

## 2. Scope

**may_touch:**
- `platform-mcp/src/tools/query_signals.ts`

**must_not_touch:**
- `platform/src/lib/retrieve/msr_sql.ts` (reference only)
- `platform-mcp/src/server.ts`
- `platform-mcp/src/tools/catalog.ts`
- All portal files
- `01_FACTS_LAYER/ll1_weights_promoted_v1_0.json` (read-only reference)
- Governance files

## 3. Files to read before starting

1. `platform/src/lib/retrieve/msr_sql.ts` — source of LL.1 calibration logic
2. `platform-mcp/src/tools/query_signals.ts` — current MCP version
3. `01_FACTS_LAYER/ll1_weights_promoted_v1_0.json` — the weight file; read to understand structure

## 4. Acceptance Criteria

- [ ] AC.1: MCP `query_signals` applies domain-specific confidence floor: finance/wealth domain rows with `confidence < 0.35` are filtered out (matching portal's floor)
- [ ] AC.2: All other domain rows apply default floor: `confidence < 0.55` filtered out (matching portal)
- [ ] AC.3: Ordering changes from `ORDER BY confidence DESC` to `ORDER BY confidence * significance DESC` (or equivalent weighted composite)
- [ ] AC.4: LL.1 weight adjustments from `ll1_weights_promoted_v1_0.json` applied post-query if the file is accessible; if not (MCP sidecar may not have FS access), implement the floor logic inline using the known domain floors
- [ ] AC.5: `min_confidence` param still overrides the floor when provided (existing filter param preserved)
- [ ] AC.6: TypeScript compiles: `cd platform-mcp && npx tsc --noEmit`
- [ ] AC.7: Existing filter params (domain, domains[], planet, dasha_lord, valence, temporal_activation) all unchanged

## 5. Implementation Steps

### Step 1 — Read all three files

```bash
cat platform/src/lib/retrieve/msr_sql.ts
cat platform-mcp/src/tools/query_signals.ts
cat 01_FACTS_LAYER/ll1_weights_promoted_v1_0.json 2>/dev/null | head -50
```

### Step 2 — Understand the LL.1 weight file structure

The JSON file likely has domain keys mapping to weight/floor values. Identify:
- Which domains get non-default floors
- What the adjustment formula is (multiplicative weight vs additive floor)

### Step 3 — Inline calibration constants in MCP tool

Since the MCP sidecar runs in Cloud Run and may not have reliable FS access to L1 files, inline the calibration constants directly in the MCP tool:

```typescript
// LL.1 calibration — domain-specific confidence floors
// Source: ll1_weights_promoted_v1_0.json (inlined for sidecar portability)
const LL1_CONFIDENCE_FLOORS: Record<string, number> = {
  finance: 0.35,
  wealth: 0.35,
  // default: 0.55
};
const LL1_DEFAULT_FLOOR = 0.55;

function getConfidenceFloor(domain: string): number {
  return LL1_CONFIDENCE_FLOORS[domain.toLowerCase()] ?? LL1_DEFAULT_FLOOR;
}
```

Cross-check these values against `ll1_weights_promoted_v1_0.json` — if the file shows different values, use the file's values.

### Step 4 — Apply floor post-query

After the SQL query returns rows, filter and re-order:
```typescript
const floor = input.min_confidence ?? undefined;
const calibratedRows = rows
  .filter(row => {
    const domainFloor = floor ?? getConfidenceFloor(row.domain ?? '');
    return row.confidence >= domainFloor;
  })
  .sort((a, b) => (b.confidence * b.significance) - (a.confidence * a.significance));
```

### Step 5 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform-mcp && npx tsc --noEmit 2>&1 | head -40
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform-mcp/src/tools/query_signals.ts
git commit -m "feat(UDA-Q-S7): backport LL.1 calibration to MCP query_signals

- Domain-specific confidence floors: finance/wealth=0.35, default=0.55
- ORDER BY confidence*significance DESC (was: confidence DESC)
- min_confidence param still overrides floor when provided
- Constants inlined for Cloud Run portability (no FS dependency)
- All existing filter params unchanged
- TypeScript clean

Quality gap closed: MCP query_signals now calibrated == portal msr_sql."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S7_v1_0.md*
