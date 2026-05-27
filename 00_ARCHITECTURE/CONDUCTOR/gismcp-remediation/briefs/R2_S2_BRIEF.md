---
session_id: R2-S2
status: PENDING
phase: GISMCP-R2
title: "jaimini_chara_dasha + jaimini_chara_dasha_full retrieval engines"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
branch: fix/gismcp-r1-r2
may_touch:
  - platform/src/lib/retrieve/jaimini_chara_dasha.ts
  - platform/src/lib/retrieve/jaimini_chara_dasha_full.ts
  - platform/src/lib/retrieve/index.ts
  - platform/src/lib/retrieve/__tests__/**
must_not_touch:
  - platform-mcp/**
  - platform/src/lib/mcp/primitives_registry.ts
  - supabase/**
  - "*.yaml"
---

# R2-S2: jaimini_chara_dasha + jaimini_chara_dasha_full Retrieval Engines

## Context

These tools compute Jaimini Chara Dasha periods for the native. They are whitelisted in `primitives_registry.ts` but have no platform retrieval engine. This session implements both.

**Before starting:** Read `platform/src/lib/retrieve/query_dasha_periods.ts` to understand the dasha retrieval pattern. Also read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` §Planet-Positions to extract the exact degree values needed for Jaimini computation.

Also check if there is an existing `jaimini` or `chara_dasha` table in the DB:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_name ILIKE '%jaimini%' OR table_name ILIKE '%chara%';
```

---

## Jaimini Chara Dasha Algorithm

### Step 1: Identify Atmakaraka (AK)

The Atmakaraka is the planet with the **highest degree in its sign** (fractional part, 0-30°), excluding Rahu/Ketu. The 7 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) compete.

From FORENSIC data (read to confirm):
- Planet degrees in sign for the native's birth chart
- The planet with the highest degree (within-sign) is the AK

**Expected result (verify from FORENSIC):** Saturn is the AK for Abhisek Mohanty (born 1984-02-05, 10:43 IST, Bhubaneswar).

### Step 2: Determine Dasha sequence

Standard Parashari Chara Dasha variant:
- Start from Lagna sign (Aries=1, Taurus=2, ..., Pisces=12)
- For ODD signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius): sequence goes FORWARD (Aries→Taurus→...)
- For EVEN signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces): sequence goes BACKWARD (Taurus→Aries→Pisces→...)
- **Native's Lagna:** Aries (Mesha) = sign 1 (ODD) → forward sequence
- So dasha order: Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces

### Step 3: Calculate dasha period lengths

For each rashi in the sequence:
- Find the **sign lord** (Aries→Mars, Taurus→Venus, Gemini→Mercury, Cancer→Moon, Leo→Sun, Virgo→Mercury, Libra→Venus, Scorpio→Mars, Sagittarius→Jupiter, Capricorn→Saturn, Aquarius→Saturn, Pisces→Jupiter)
- Find the sign lord's **position in its own sign or another sign** from the native's chart
- Period = `(30 − degrees_of_sign_lord_in_its_rashi_at_birth) + 1` years (some traditions: just the remaining degrees)

**Simpler standard formula used by most software:**
- Period for rashi = number of years equal to the degrees REMAINING for the sign lord in its sign (if in own sign) OR based on a lookup table per sign

**Recommended approach:** Use the precomputed Chara Dasha if it's already in a table (check DB). If not, implement using the stored planet degree values from the `chart_facts` table (which has planet positions).

```sql
-- Check if chart_facts has what we need
SELECT category, key, value FROM chart_facts 
WHERE chart_id = '<native_chart_id>'
  AND category IN ('planets', 'lagna', 'jaimini')
ORDER BY category, key;
```

### Step 4: Compute period dates

Starting from birth date (1984-02-05):
- Each rashi gets N years (from Step 3)
- Accumulate to get start/end dates for each mahadasha
- Within each mahadasha, compute antardashas in the same order (sub-cycle)

---

## Implementation Plan

### Approach A (preferred): Read from existing DB computation

If `chart_facts` or a Jaimini-specific table already has Chara Dasha computed (MCP Transformation may have added it), read from there. The MCP Transformation processed `chart_facts` with 27 categories — check if `jaimini_chara_dasha` is one.

```sql
SELECT DISTINCT category FROM chart_facts;
SELECT * FROM chart_facts WHERE category = 'jaimini_chara_dasha' LIMIT 5;
```

If data exists: write a retrieval tool that queries it directly.

### Approach B (fallback): Compute from chart_facts planet positions

If no precomputed Chara Dasha table exists:

1. Read planet positions from `chart_facts` (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn degrees in sign)
2. Compute AK (highest degree)
3. Read Lagna sign from chart_facts
4. Apply the period formula to generate the full sequence
5. Store in TypeScript (no new migrations — compute in the retrieval function)

---

## Tool 1: `jaimini_chara_dasha`

**Input schema:**
```typescript
{
  chart_id?: string,     // defaults to native's canonical chart
  as_of_date?: string    // ISO date, defaults to today
}
```

**Output:**
```typescript
{
  atmakaraka: string,           // planet name
  lagna_sign: string,           // Aries etc.
  current_mahadasha: {
    rashi: string,
    start_date: string,
    end_date: string,
    years_duration: number,
    balance_years: number
  },
  current_antardasha: {
    rashi: string,
    start_date: string,
    end_date: string
  }
}
```

## Tool 2: `jaimini_chara_dasha_full`

Same as above but returns the full sequence from birth to 120 years forward.

**Output adds:**
```typescript
{
  full_sequence: Array<{
    mahadasha_rashi: string,
    start_date: string,
    end_date: string,
    years_duration: number,
    antardashas: Array<{
      rashi: string,
      start_date: string,
      end_date: string
    }>
  }>
}
```

---

## Export from index.ts

Add:
```typescript
export { jaiminiCharaDasha } from './jaimini_chara_dasha'
export { jaiminiCharaDashaFull } from './jaimini_chara_dasha_full'
```

Register both in RETRIEVAL_TOOLS under `'jaimini_chara_dasha'` and `'jaimini_chara_dasha_full'`.

---

## Commit

```bash
git add platform/src/lib/retrieve/jaimini_chara_dasha.ts \
        platform/src/lib/retrieve/jaimini_chara_dasha_full.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(R2): jaimini_chara_dasha + jaimini_chara_dasha_full retrieval engines

- Jaimini Chara Dasha computed from chart_facts planet positions
- AK: Saturn (verify from FORENSIC), Lagna: Aries (forward sequence)
- jaimini_chara_dasha: current mahadasha + antardasha
- jaimini_chara_dasha_full: complete sequence birth to +120y
- Both exported from retrieve/index.ts

Closes R2-S2 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `test -f platform/src/lib/retrieve/jaimini_chara_dasha.ts`
2. `test -f platform/src/lib/retrieve/jaimini_chara_dasha_full.ts`
3. Both exported in retrieve/index.ts and in RETRIEVAL_TOOLS
4. `jaimini_chara_dasha` returns a valid `current_mahadasha.rashi` (non-empty string) for native
5. `jaimini_chara_dasha_full` returns `full_sequence.length >= 12` (12 rashis in full cycle)
