---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S3: Port query_jaimini_chara_dasha → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S3
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S3
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S3 — Port to portal: query_jaimini_chara_dasha

## 1. Context

`query_jaimini_chara_dasha` is a MCP surgical primitive that computes the Jaimini Chara Dasha
schedule. It exists only in `platform-mcp/src/tools/query_jaimini_chara_dasha.ts` and is not
available as a portal RETRIEVAL_TOOL.

**What it does:**
- Computes Jaimini Chara Dasha (12-rashi based timing system) for the native's sidereal chart
- Derives period lengths from sign lord's longitude in its own sign (odd vs even rashi rules)
- Returns active rashi dasha + antar dasha for a given date, OR full 12-rashi timeline
- Data source: Python sidecar `/jaimini_drishti/chara_dasha` endpoint

**MCP source (read-only):** `platform-mcp/src/tools/query_jaimini_chara_dasha.ts`
**Portal target (create):** `platform/src/lib/retrieve/query_jaimini_chara_dasha.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_jaimini_chara_dasha.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registration)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_3.1: `platform/src/lib/retrieve/query_jaimini_chara_dasha.ts` exists and exports a RetrievalTool
- [ ] AC.1_3.2: Tool is registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_3.3: Tool calls the Python sidecar `/jaimini_drishti/chara_dasha` endpoint (same as MCP version) OR computes directly using the same algorithm
- [ ] AC.1_3.4: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_3.5: Commit message contains `UDA-1-S3`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source and portal sidecar call patterns

```bash
cat platform-mcp/src/tools/query_jaimini_chara_dasha.ts
# Find how existing portal tools call the Python sidecar
grep -n "sidecar\|python\|/api/compute\|temporal" platform/src/lib/retrieve/temporal.ts | head -30
cat platform/src/lib/retrieve/query_muhurat.ts | head -60
```

### Step 2 — Create query_jaimini_chara_dasha.ts (portal version)

Adapt the MCP tool to portal patterns:
- Use `getStorageClient()` for native chart_id lookup if needed
- Call the Python sidecar using the portal's sidecar HTTP client (same pattern as `query_muhurat.ts`)
- Implement fallback: if sidecar is unavailable, compute directly from the MCP algorithm
  (port the Jaimini period calculation: odd rashis = 30 - floor(lord_lon), even = floor + 1)

Key inputs: `date?: string` (active dasha mode) OR `mode: 'full'` (full timeline)
Key output: `{ active_rashi_dasha, active_antar_dasha }` OR `{ full_periods }`

### Step 3 — Register in index.ts

```typescript
// UDA-1-S3: Jaimini Chara Dasha
import * as queryJaiminiCharaDasha from './query_jaimini_chara_dasha'
```

Add to RETRIEVAL_TOOLS array.

### Step 4 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_jaimini_chara_dasha.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S3): port query_jaimini_chara_dasha to portal

Jaimini Chara Dasha active period + full timeline. tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "query_jaimini_chara_dasha\|jaimini_chara_dasha" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S3_JCD: PASS'
test -f platform/src/lib/retrieve/query_jaimini_chara_dasha.ts && echo 'GATE_UDA_1_S3_FILE: PASS'
git log --oneline -3 | grep -q 'UDA-1-S3' && echo 'GATE_UDA_1_S3_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S3_v1_0.md*
