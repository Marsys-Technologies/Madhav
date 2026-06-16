---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S8: Port tara_balam_for_native + chandra_balam_for_native + muhurta_finder → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S8
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S8
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S8 — Port to portal: tara_balam_for_native + chandra_balam_for_native + muhurta_finder

## 1. Context

Three MCP muhurta-related tools need to be ported. This is the final UDA-1 session.

**`tara_balam_for_native` (Tara Bala / Star Strength):**
- Native's birth nakshatra: Purva Bhadrapada (nakshatra_id=25)
- For a given date, fetch Moon's nakshatra from `query_ephemeris` (or panchanga table)
- Count position from birth nakshatra (1-indexed); apply 9-tara cycle scoring:
  1=Janma (0.50), 2=Sampat (0.90), 3=Vipat (0.00), 4=Kshema (0.85),
  5=Pratyari (0.10), 6=Sadhaka (0.95), 7=Vadha (0.00), 8=Mitra (0.80), 9=Ati-Mitra (1.00)
  Positions 10–18: 0.80 attenuation. Positions 19–27: 0.60 attenuation.

**`chandra_balam_for_native` (Chandra Bala / Moon Strength):**
- Native's birth Moon sign: Pisces / Meena (moon_sign_id=12)
- For a given date, fetch Moon's sign from `query_ephemeris`
- Count position from birth Moon sign (1-indexed); apply position scoring:
  1=0.80, 2=0.30, 3=0.90, 4=0.20, 5=0.30, 6=0.90, 7=0.85, 8=0.10, 9=0.40,
  10=0.90, 11=0.95, 12=0.30

**`muhurta_finder` (Auspicious Muhurta Window Finder):**
- Finds top auspicious muhurta windows for a given activity type over a date range (max 30 days)
- Calls Python sidecar `/api/compute/muhurat` endpoint
- Native chart overlay (Tara Bala + Chandra Bala) applied automatically
- Returns scored time windows with auspicious factors breakdown
- The portal already has `query_muhurat.ts` — `muhurta_finder` is the richer version
  with native overlay scoring

**MCP source files (read-only):**
- `platform-mcp/src/tools/tara_balam_for_native.ts`
- `platform-mcp/src/tools/chandra_balam_for_native.ts`
- `platform-mcp/src/tools/muhurta_finder.ts`

**Portal target files (create):**
- `platform/src/lib/retrieve/tara_balam_for_native.ts`
- `platform/src/lib/retrieve/chandra_balam_for_native.ts`
- `platform/src/lib/retrieve/muhurta_finder.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/tara_balam_for_native.ts` (create)
- `platform/src/lib/retrieve/chandra_balam_for_native.ts` (create)
- `platform/src/lib/retrieve/muhurta_finder.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registrations)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- `platform/src/lib/retrieve/query_muhurat.ts` (existing sidecar wrapper — do not modify)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_8.1: `platform/src/lib/retrieve/tara_balam_for_native.ts` exists and exports a RetrievalTool
- [ ] AC.1_8.2: `platform/src/lib/retrieve/chandra_balam_for_native.ts` exists and exports a RetrievalTool
- [ ] AC.1_8.3: `platform/src/lib/retrieve/muhurta_finder.ts` exists and exports a RetrievalTool
- [ ] AC.1_8.4: All three tools registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_8.5: `tara_balam_for_native` and `chandra_balam_for_native` use the correct hardcoded native birth nakshatra (Purva Bhadrapada=25) and Moon sign (Pisces=12)
- [ ] AC.1_8.6: `muhurta_finder` calls the Python sidecar (same endpoint as `query_muhurat.ts`)
- [ ] AC.1_8.7: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_8.8: Commit message contains `UDA-1-S8`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source files

```bash
cat platform-mcp/src/tools/tara_balam_for_native.ts
cat platform-mcp/src/tools/chandra_balam_for_native.ts
cat platform-mcp/src/tools/muhurta_finder.ts
cat platform/src/lib/retrieve/query_muhurat.ts | head -80  # sidecar call pattern
```

### Step 2 — Create tara_balam_for_native.ts (portal version)

```typescript
const NATIVE_BIRTH_NAKSHATRA_ID = 25 // Purva Bhadrapada
const NAKSHATRA_COUNT = 27

const TARA_SCORES = [0.50, 0.90, 0.00, 0.85, 0.10, 0.95, 0.00, 0.80, 1.00]
const TARA_NAMES  = ['Janma','Sampat','Vipat','Kshema','Pratyari','Sadhaka','Vadha','Mitra','Ati-Mitra']
const ATTENUATION = [1.0, 0.80, 0.60]

function getTaraBala(moonNakshatraId: number) {
  let position = ((moonNakshatraId - NATIVE_BIRTH_NAKSHATRA_ID) % NAKSHATRA_COUNT + NAKSHATRA_COUNT) % NAKSHATRA_COUNT
  const cycle = Math.floor(position / 9)
  const taraIndex = position % 9
  const score = (TARA_SCORES[taraIndex] ?? 0.5) * (ATTENUATION[cycle] ?? 0.6)
  return { tara_count: position + 1, tara_name: TARA_NAMES[taraIndex]!, score }
}
```

Fetch Moon's nakshatra from `panchanga_daily` table (if available) OR from `query_ephemeris`
Moon position and compute nakshatra (longitude / (360/27) + 1).

### Step 3 — Create chandra_balam_for_native.ts (portal version)

```typescript
const NATIVE_BIRTH_MOON_SIGN_ID = 12 // Pisces / Meena
const SIGN_COUNT = 12

const CHANDRA_SCORES = [0.80, 0.30, 0.90, 0.20, 0.30, 0.90, 0.85, 0.10, 0.40, 0.90, 0.95, 0.30]

function getChandraBala(moonSignId: number) {
  const position = ((moonSignId - NATIVE_BIRTH_MOON_SIGN_ID) % SIGN_COUNT + SIGN_COUNT) % SIGN_COUNT
  return { position: position + 1, score: CHANDRA_SCORES[position] ?? 0.5 }
}
```

Fetch Moon's sign from `query_ephemeris` or `panchanga_daily`.

### Step 4 — Create muhurta_finder.ts (portal version)

Follow the same sidecar call pattern as `query_muhurat.ts`. The difference is that
`muhurta_finder` accepts `activity_type` (vivah/griha_pravesh/vyapara/yatra/property_purchase/mantra_initiation)
and `date_from`/`date_to` range (max 30 days), and automatically includes the native's
chart overlay (Tara Bala + Chandra Bala) in the sidecar request.

### Step 5 — Register all three in index.ts

```typescript
import * as taraBalamForNative from './tara_balam_for_native'
import * as chandraBalamForNative from './chandra_balam_for_native'
import * as muhurtaFinder from './muhurta_finder'
```

Add to RETRIEVAL_TOOLS.

### Step 6 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 7 — Push phase boundary

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/tara_balam_for_native.ts \
        platform/src/lib/retrieve/chandra_balam_for_native.ts \
        platform/src/lib/retrieve/muhurta_finder.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S8): port tara_balam_for_native + chandra_balam_for_native + muhurta_finder to portal

Tara Bala 9-tara cycle; Chandra Bala 12-sign scoring; Muhurta Finder sidecar wrapper.
UDA-1 phase complete. tsc: 0 errors."
git push origin feature/universal-parity
```

---

## 5. Gate Commands

```bash
grep -q "tara_balam_for_native\|tara_balam" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S8_TARA: PASS'
grep -q "chandra_balam_for_native\|chandra_balam" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S8_CHANDRA: PASS'
grep -q "muhurta_finder\|muhurta" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S8_MUHURTA: PASS'
git log --oneline -3 | grep -q 'UDA-1-S8' && echo 'GATE_UDA_1_S8_COMMIT: PASS'
```

All 4 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S8_v1_0.md*
