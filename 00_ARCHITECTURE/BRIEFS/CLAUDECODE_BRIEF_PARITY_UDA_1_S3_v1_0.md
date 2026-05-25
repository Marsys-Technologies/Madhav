---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S3: Port query_jaimini_chara_dasha to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S3
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S3
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S3 — Port Jaimini Chara Dasha tool to portal

## 1. Context

`query_jaimini_chara_dasha` returns the Jaimini Chara Dasha periods for a native — the rashi-based Jaimini system's major and sub-periods with their start/end dates. This is essential for multi-school synthesis (Parashari + Jaimini comparison is a core B.11 whole-chart-read requirement). Currently MCP-only; the portal planner cannot retrieve Jaimini Chara Dasha even when it should.

Note: The portal may have a partial Jaimini tool under a different name. Check `platform/src/lib/retrieve/` for any `jaimini*.ts` file. If one exists, compare and upgrade rather than duplicate.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_jaimini_chara_dasha.ts` (create or upgrade existing)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- `platform-mcp/src/tools/query_jaimini_chara_dasha.ts` (reference only)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_jaimini_chara_dasha.ts`
2. `platform/src/lib/retrieve/` — scan for existing jaimini tools
3. `platform/src/lib/retrieve/index.ts`
4. One existing portal tool for DB connection pattern

## 4. Acceptance Criteria

- [ ] AC.1: `query_jaimini_chara_dasha` in portal RETRIEVAL_TOOLS with exact name match
- [ ] AC.2: Input schema matches MCP (at minimum: `chart_id`, `level` for MD/AD distinction)
- [ ] AC.3: Output includes: rashi_sign as dasha lord, start_date, end_date, duration_years for each period
- [ ] AC.4: Registered in `index.ts`
- [ ] AC.5: TypeScript compiles clean

## 5. Implementation Steps

### Step 1 — Scan for existing Jaimini tools

```bash
ls platform/src/lib/retrieve/ | grep -i jaimini
cat platform-mcp/src/tools/query_jaimini_chara_dasha.ts
```

### Step 2 — Port or create

Follow UDA-1-S1 pattern. The Jaimini Chara Dasha calculation is likely:
- SQL against a `jaimini_dasha` or `chara_dasha` table in the DB
- Returns periods with rashi signs as period lords (Ar, Ta, Ge... rather than planets)
- Level param for major/antara distinction

Key: Jaimini Chara Dasha lords are RASHIS not planets — ensure the output schema reflects this (e.g., `rashi_lord: string` not `planet_lord: string`).

### Step 3 — Register and compile

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 4 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_jaimini_chara_dasha.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S3): port query_jaimini_chara_dasha to portal

Jaimini Chara Dasha (rashi-based periods) now available in portal.
Critical for multi-school B.11 whole-chart-read compliance.
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S3_v1_0.md*
