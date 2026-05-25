---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-1-S6: Port query_eclipse_transits + query_planet_war → portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S6
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S6
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-1-S6 — Port to portal: query_eclipse_transits + query_planet_war

## 1. Context

**`query_eclipse_transits` (Eclipse Detection):**
Scans a date range for solar and lunar eclipses using ephemeris data.
- Solar eclipse: Sun–Moon angular separation ≤ 1° AND Moon within 12° of Rahu or Ketu
- Lunar eclipse: Sun–Moon separation within 1° of 180° AND Moon within 12° of a node
- Optionally flags eclipses conjunct native's natal Sun, Moon, or ASC within 5°
- Data source: `query_ephemeris` (day-by-day positions)

**`query_planet_war` (Graha Yuddha Detection):**
Detects Graha Yuddha (planetary war) events within a date range.
- Two true planets (Sun/Moon excluded) within 1° of ecliptic longitude on the same day
- Winner: planet with higher absolute declination (or higher speed as fallback)
- Returns: date, planets in war, winner, duration, classical interpretation
- 360° wrap: `min(|a-b|, 360-|a-b|)` for correct boundary handling

**MCP source files (read-only):**
- `platform-mcp/src/tools/query_eclipse_transits.ts`
- `platform-mcp/src/tools/query_planet_war.ts`

**Portal target files (create):**
- `platform/src/lib/retrieve/query_eclipse_transits.ts`
- `platform/src/lib/retrieve/query_planet_war.ts`

---

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_eclipse_transits.ts` (create)
- `platform/src/lib/retrieve/query_planet_war.ts` (create)
- `platform/src/lib/retrieve/index.ts` (add registrations)

**must_not_touch:**
- `platform-mcp/` (source reference only)
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.1_6.1: `platform/src/lib/retrieve/query_eclipse_transits.ts` exists and exports a RetrievalTool
- [ ] AC.1_6.2: `platform/src/lib/retrieve/query_planet_war.ts` exists and exports a RetrievalTool
- [ ] AC.1_6.3: Both tools registered in `index.ts` RETRIEVAL_TOOLS
- [ ] AC.1_6.4: Both tools call portal `query_ephemeris` for their astronomical data
- [ ] AC.1_6.5: `cd platform && npx tsc --noEmit` passes with 0 errors
- [ ] AC.1_6.6: Commit message contains `UDA-1-S6`

---

## 4. Step-by-Step Execution

### Step 1 — Read MCP source files

```bash
cat platform-mcp/src/tools/query_eclipse_transits.ts
cat platform-mcp/src/tools/query_planet_war.ts
```

### Step 2 — Create query_eclipse_transits.ts (portal version)

Eclipse detection algorithm:
1. Call portal `query_ephemeris` for Sun, Moon, Rahu, Ketu in the date range
2. For each day, compute Sun–Moon separation (with 360° wrap)
3. Solar eclipse: separation ≤ 1° AND (Moon–Rahu ≤ 12° OR Moon–Ketu ≤ 12°)
4. Lunar eclipse: |separation - 180°| ≤ 1° AND (Moon–Rahu ≤ 12° OR Moon–Ketu ≤ 12°)
5. If `natal_sensitive_points=true`, fetch native's natal Sun/Moon/ASC from chart_facts
   and flag eclipses within 5° of those points

For native natal points, use `getStorageClient()` to query chart_facts directly
(category='planet' for Sun/Moon, category='house' for ASC longitude).

### Step 3 — Create query_planet_war.ts (portal version)

Graha Yuddha algorithm:
1. Call portal `query_ephemeris` for all 7 true planets (exclude Sun, Moon per classical rule)
2. For each day, compare each pair of planet longitudes with 360° wrap
3. If angular distance ≤ 1°: war event
4. Winner: higher absolute declination; if not available, higher speed
5. Append classical interpretation per winner

Planet pair: Exclude Sun and Moon from war detection (classical rule). True planets = Mars, Mercury, Jupiter, Venus, Saturn.

### Step 4 — Register in index.ts

```typescript
import * as queryEclipseTransits from './query_eclipse_transits'
import * as queryPlanetWar from './query_planet_war'
```

Add to RETRIEVAL_TOOLS.

### Step 5 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform && npx tsc --noEmit
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_eclipse_transits.ts \
        platform/src/lib/retrieve/query_planet_war.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S6): port query_eclipse_transits + query_planet_war to portal

Eclipse detection (solar/lunar + natal sensitivity); Graha Yuddha detection.
tsc: 0 errors."
```

---

## 5. Gate Commands

```bash
grep -q "query_eclipse_transits\|eclipse_transits" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S6_ECLIPSE: PASS'
grep -q "query_planet_war\|planet_war" platform/src/lib/retrieve/index.ts && echo 'GATE_UDA_1_S6_PLANETWAR: PASS'
git log --oneline -3 | grep -q 'UDA-1-S6' && echo 'GATE_UDA_1_S6_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S6_v1_0.md*
