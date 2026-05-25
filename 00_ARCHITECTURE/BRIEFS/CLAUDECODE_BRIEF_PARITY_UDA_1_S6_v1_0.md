---
title: "CLAUDECODE_BRIEF — Parity UDA-1-S6: Port query_eclipse_transits + query_planet_war to portal"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_1_S6
version: 1.0
status: CURRENT
phase: UDA-1
session_id: UDA-1-S6
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-1-S6 — Port eclipse transits + graha yuddha tools to portal

## 1. Context

Two event-based transit tools:
- `query_eclipse_transits` — returns solar and lunar eclipse events overlaid on the native's natal chart. Returns which natal planets are activated (within orb), eclipse type (solar/lunar, total/partial), and date. Critical for event timing analysis.
- `query_planet_war` — returns Graha Yuddha (planetary war) events where two planets are within 1° of each other. The loser of the war (lower northern latitude) is weakened. Returns winner/loser, degree, date range.

These are event-search tools that scan an ephemeris table rather than returning static chart data.

## 2. Scope

**may_touch:**
- `platform/src/lib/retrieve/query_eclipse_transits.ts` (create)
- `platform/src/lib/retrieve/query_planet_war.ts` (create)
- `platform/src/lib/retrieve/index.ts`

**must_not_touch:**
- MCP tool files (reference only)
- All `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/tools/query_eclipse_transits.ts`
2. `platform-mcp/src/tools/query_planet_war.ts`
3. `platform/src/lib/retrieve/query_transit_event.ts` — existing portal transit tool (DB pattern)
4. `platform/src/lib/retrieve/index.ts`

## 4. Acceptance Criteria

- [ ] AC.1: `query_eclipse_transits` in portal RETRIEVAL_TOOLS
- [ ] AC.2: Eclipse results include: eclipse_type, date, activated_natal_planets[], within_orb_degrees
- [ ] AC.3: `query_planet_war` in portal RETRIEVAL_TOOLS
- [ ] AC.4: Planet war results include: planet_a, planet_b, winner, loser, date, longitude_at_war
- [ ] AC.5: Both use date range params consistent with existing portal transit tools
- [ ] AC.6: TypeScript compiles clean

## 5. Implementation Steps

### Step 1 — Read MCP implementations

```bash
cat platform-mcp/src/tools/query_eclipse_transits.ts
cat platform-mcp/src/tools/query_planet_war.ts
cat platform/src/lib/retrieve/query_transit_event.ts  # DB pattern reference
```

### Step 2 — Port both tools

Follow UDA-1-S1 porting pattern. Both tools likely query the `ephemeris` or `transit_events` table with specific WHERE clauses:
- Eclipse: `WHERE event_type IN ('solar_eclipse', 'lunar_eclipse')`
- Planet war: `WHERE ABS(planet_a_longitude - planet_b_longitude) < 1.0`

Adapt to portal DB pattern.

### Step 3 — Register and compile

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit 2>&1 | head -40
```

### Step 4 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add platform/src/lib/retrieve/query_eclipse_transits.ts
git add platform/src/lib/retrieve/query_planet_war.ts
git add platform/src/lib/retrieve/index.ts
git commit -m "feat(UDA-1-S6): port query_eclipse_transits + query_planet_war to portal

Eclipse transits (solar/lunar) and Graha Yuddha events now in portal.
Both search ephemeris table; date range params consistent with existing transit tools.
TypeScript clean."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_1_S6_v1_0.md*
