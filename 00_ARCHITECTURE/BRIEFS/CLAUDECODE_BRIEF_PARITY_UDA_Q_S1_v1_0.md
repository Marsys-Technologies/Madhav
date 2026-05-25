---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S1: query_dasha_periods PD/SD backport to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S1
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-Q-S1 — Backport pratyantar/sookshma dasha levels to portal

## 1. Context

The MCP tool `platform-mcp/src/tools/query_dasha_periods.ts` (enhanced by TR-P7-S1, bace7b45) supports four dasha levels: `maha`, `antar`, `pratyantar`, and `sookshma`. It computes sub-period durations via:

```
PD duration = AD_duration × (vimshottari_years[planet] / 120)
SD duration = PD_duration × (vimshottari_years[planet] / 120)
```

The portal tool `platform/src/lib/retrieve/query_dasha_periods.ts` only returns MD+AD. This session ports the pratyantar and sookshma levels to the portal tool so both channels are identical in depth.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_dasha_periods.ts`

**must_not_touch:**
- `platform-mcp/src/tools/query_dasha_periods.ts` (reference only — do not modify)
- `platform/src/lib/retrieve/index.ts` (no registration changes needed — tool already registered)
- `platform-mcp/` any other files
- All governance files (`CLAUDE.md`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`)

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_dasha_periods.ts` — source of truth for enhanced implementation
2. `platform/src/lib/retrieve/query_dasha_periods.ts` — current degraded portal version to be upgraded

## 4. Acceptance Criteria

- [ ] AC.1: `level` param accepts `'maha' | 'antar' | 'pratyantar' | 'sookshma'` (add `pratyantar` and `sookshma` to existing portal enum)
- [ ] AC.2: `computePratyantar(adRows, planet)` function added — computes PD duration = `ad_duration_days × (vimshottari_years[planet] / 120)` for each AD; returns sub_periods array
- [ ] AC.3: `computeSookshma(pdRows, planet)` function added — same formula applied to PD durations
- [ ] AC.4: When `level === 'pratyantar'`, response includes `sub_periods` array nested under each AD
- [ ] AC.5: When `level === 'sookshma'`, response includes `sub_periods` nested under each PD
- [ ] AC.6: Existing `maha` and `antar` behavior is UNCHANGED — no regression
- [ ] AC.7: TypeScript compiles without errors: `cd platform && npx tsc --noEmit`
- [ ] AC.8: Vimshottari years map present: `{ Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16, Saturn: 19, Mercury: 17, Ketu: 7, Venus: 20 }`

## 5. Implementation Steps

### Step 1 — Read both files

```bash
cat platform-mcp/src/tools/query_dasha_periods.ts
cat platform/src/lib/retrieve/query_dasha_periods.ts
```

### Step 2 — Add vimshottari years constant

In `platform/src/lib/retrieve/query_dasha_periods.ts`, add near the top (after imports):

```typescript
const VIMSHOTTARI_YEARS: Record<string, number> = {
  Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16,
  Saturn: 19, Mercury: 17, Ketu: 7, Venus: 20
};
```

### Step 3 — Add level enum to input schema

Expand the existing `level` Zod schema (or add it if absent):
```typescript
level: z.enum(['maha', 'antar', 'pratyantar', 'sookshma']).optional().default('antar')
```

### Step 4 — Add computePratyantar and computeSookshma helpers

Port directly from the MCP tool — the logic is identical. The helpers iterate over AD rows and compute fractional sub-periods using the planet's vimshottari fraction.

### Step 5 — Wire level dispatch

In the main handler function, after computing AD rows, dispatch on `level`:
- `'pratyantar'` → call `computePratyantar()` and attach `sub_periods` to each AD row
- `'sookshma'` → call `computePratyantar()` then `computeSookshma()` and attach nested

### Step 6 — TypeScript check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform
npx tsc --noEmit 2>&1 | head -40
```

Fix any type errors before committing.

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_dasha_periods.ts
git commit -m "feat(UDA-Q-S1): backport pratyantar/sookshma dasha levels to portal

Portal query_dasha_periods now matches MCP depth:
- level enum: maha | antar | pratyantar | sookshma
- computePratyantar(): PD = AD_days × (vimshottari_years[P] / 120)
- computeSookshma(): SD = PD_days × (vimshottari_years[P] / 120)
- sub_periods[] nested in response at both levels
- Existing maha/antar behavior unchanged

Quality gap closed: portal now == MCP for dasha depth."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S1_v1_0.md*
