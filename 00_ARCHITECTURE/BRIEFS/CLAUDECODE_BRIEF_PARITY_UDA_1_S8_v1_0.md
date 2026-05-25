---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S8: Port tara_balam + chandra_balam + muhurta_finder to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S8
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S8
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S8 — Port Tara/Chandra Bala + Muhurta tools to portal

## 1. Context

Three auspiciousness-scoring tools:
- `tara_balam_for_native` — computes Tara Bala (star strength) for the native. Based on the moon's current nakshatra relative to the native's birth nakshatra — produces a score indicating favorable/unfavorable quality of the day. Returns tara_number (1–9) and quality.
- `chandra_balam_for_native` — computes Chandra Bala (moon strength) for the native. Based on the moon's current sign relative to the native's natal moon sign — returns a numeric bala score and qualitative assessment.
- `muhurta_finder` — returns auspicious time windows for a given date range. Queries the `panchanga_daily` table (populated by Phase 4C). Supports action_type filter (travel, marriage, business, etc.) and returns choghadiya + hora windows scored for the action.

**Note:** `muhurta_finder` has a UI surface at `/panchang` (Phase 4C). The portal RETRIEVAL_TOOLS version enables the planner to surface muhurta data in text responses without the user navigating to the UI.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/tara_balam_for_native.ts` (create)
- `platform/src/lib/retrieve/chandra_balam_for_native.ts` (create)
- `platform/src/lib/retrieve/muhurta_finder.ts` (create)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- MCP tool files (reference only)
- Phase 4C panchang sidecar (`platform/python-sidecar/`) — read only
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/tara_balam_for_native.ts`
2. `platform-mcp/src/tools/chandra_balam_for_native.ts`
3. `platform-mcp/src/tools/muhurta_finder.ts`
4. `platform/src/lib/retrieve/query_panchanga.ts` — existing panchanga tool (muhurta uses same table)
5. `platform/src/lib/retrieve/index.ts`

## 4. Acceptance Criteria

- [ ] AC.1: `tara_balam_for_native` in portal RETRIEVAL_TOOLS — returns tara_number, tara_name, quality for given date
- [ ] AC.2: `chandra_balam_for_native` in portal RETRIEVAL_TOOLS — returns chandra_bala score and quality for given date
- [ ] AC.3: `muhurta_finder` in portal RETRIEVAL_TOOLS — returns scored time windows from `panchanga_daily`
- [ ] AC.4: Tara and Chandra Bala tools compute dynamically (need: native's birth nakshatra/moon sign from natal chart + current moon position)
- [ ] AC.5: `muhurta_finder` respects `action_type` filter and returns top-N windows with scores
- [ ] AC.6: All three registered in `index.ts`
- [ ] AC.7: TypeScript compiles clean

## 5. Implementation Steps

### Step 1 — Read all MCP implementations

```bash
cat platform-mcp/src/tools/tara_balam_for_native.ts
cat platform-mcp/src/tools/chandra_balam_for_native.ts
cat platform-mcp/src/tools/muhurta_finder.ts
cat platform/src/lib/retrieve/query_panchanga.ts  # for muhurta DB pattern
```

### Step 2 — Port Tara and Chandra Bala

These tools compute based on:
1. Native's natal data (birth nakshatra/moon sign) — pull from `chart_facts` or `forensic_data` table
2. Current moon position — pull from `panchanga_daily` for the requested date

Adapt the MCP calculation logic to portal DB pattern.

### Step 3 — Port muhurta_finder

This wraps `panchanga_daily` with auspiciousness scoring. The portal already has `query_panchanga.ts` — the muhurta finder adds the scoring layer on top. Port the scoring logic from MCP, using the same panchanga table.

### Step 4 — Register all three in index.ts

### Step 5 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/tara_balam_for_native.ts
git add platform/src/lib/retrieve/chandra_balam_for_native.ts
git add platform/src/lib/retrieve/muhurta_finder.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S8): port tara_balam + chandra_balam + muhurta_finder to portal

Tara Bala (nakshatra strength), Chandra Bala (moon strength), and Muhurta
Finder (auspicious time windows) now in portal RETRIEVAL_TOOLS.
Muhurta uses panchanga_daily table (Phase 4C).
TypeScript clean.

UDA-1 COMPLETE: all 14 MCP-only Class B engines now in portal."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S8_v1_0.md*
