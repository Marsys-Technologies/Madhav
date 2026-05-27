---
session_id: R2-S1
status: PENDING
phase: GISMCP-R2
title: "query_tara_balam + query_chandra_balam retrieval engines"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
branch: fix/gismcp-r1-r2
may_touch:
  - platform/src/lib/retrieve/query_tara_balam.ts
  - platform/src/lib/retrieve/query_chandra_balam.ts
  - platform/src/lib/retrieve/index.ts
  - platform/src/lib/retrieve/__tests__/**
must_not_touch:
  - platform-mcp/**
  - platform/src/lib/mcp/primitives_registry.ts
  - supabase/**
  - "*.yaml"
---

# R2-S1: query_tara_balam + query_chandra_balam Retrieval Engines

## Context

These two tools are whitelisted in `primitives_registry.ts` as `'query_tara_balam'` and `'query_chandra_balam'`. The dispatcher finds them in the whitelist but then calls `RETRIEVAL_TOOLS['query_tara_balam']` and fails because no retrieval tool is registered under that name. This session creates both engines.

**Before starting:** Read an existing retrieve tool for pattern reference. Read `platform/src/lib/retrieve/query_dasha_periods.ts` or `platform/src/lib/retrieve/lel_query.ts` to understand the exact shape: export structure, Zod schema, `execute` function signature, DB connection pattern, error handling.

Also read `platform/src/lib/retrieve/index.ts` to understand how tools are exported and registered.

---

## Tool 1: query_tara_balam

### Astrological definition

Tara Balam = the 9-fold Nakshatra cycle from the native's natal Moon nakshatra.

- **Native's natal Moon nakshatra:** Purva Bhadrapada (index 25, using 1-based count where Ashwini=1)
- For any queried date range, look up the transit Moon nakshatra from the `ephemeris` table (column likely: `moon_nakshatra` or `moon_nak_index`)
- **Tara number** = `((transit_nak_index − 25 + 27) % 27) % 9 + 1`  (result is 1–9)
- **Tara name map:**
  1. Janma, 2. Sampat, 3. Vipat, 4. Kshema, 5. Pratyari, 6. Sadhaka, 7. Vadha, 8. Mitra, 9. Ati-Mitra
- **Classification:** benefic = [2, 4, 6, 8, 9]; malefic = [1, 3, 5, 7]

### Implementation steps

1. Read the `ephemeris` table schema first:
   ```sql
   SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name = 'ephemeris' ORDER BY ordinal_position;
   ```
   Find the column name for Moon nakshatra (may be `moon_nakshatra`, `moon_nak_num`, or similar).

2. Create `platform/src/lib/retrieve/query_tara_balam.ts`:

```typescript
// Input schema:
// {
//   start_date: string (ISO date, e.g. "2026-05-26"),
//   end_date: string (ISO date),
//   native_natal_moon_nak_index?: number  // default 25 (PBh) — can be overridden for other natives
// }

// Output per date:
// {
//   date: string,
//   moon_nakshatra_name: string,
//   moon_nak_index: number,
//   tara_number: number,   // 1-9
//   tara_name: string,     // Janma..Ati-Mitra
//   classification: 'benefic' | 'malefic'
// }
```

3. SQL query pattern:
```sql
SELECT
  date,
  <moon_nak_column> AS moon_nak_index,
  <moon_nak_name_column> AS moon_nakshatra_name,
  ((<moon_nak_column> - $natal_nak + 27) % 27) % 9 + 1 AS tara_number
FROM ephemeris
WHERE date >= $start_date AND date <= $end_date
ORDER BY date
```

4. Map tara_number → tara_name and classification in TypeScript.

5. If the ephemeris table doesn't have a `moon_nak_name` column, derive the name from the index using a static map (Ashwini=1 through Revati=27).

### Spot-check

For `start_date=1984-02-05, end_date=1984-02-05` (native birth date):
- Moon was in PBh (natal nakshatra = transit nakshatra)
- tara_number should be 1 (Janma), classification = malefic
- This is the expected result — assert it in the test.

---

## Tool 2: query_chandra_balam

### Astrological definition

Chandra Balam = transit Moon sign relative to native's natal Moon sign.

- **Native's natal Moon sign:** Pisces / Meena = sign 12 (1-based, Aries=1)
- For any queried date range, look up transit Moon sign from `ephemeris` table
- **Position** = `((transit_moon_sign − 12 + 12) % 12) + 1`  (1-based from natal sign)
- **Classification (standard muhurta rule):**
  - Benefic positions: 1, 3, 6, 7, 10, 11
  - Malefic positions: 2, 4, 5, 8, 9, 12

### Implementation steps

1. Find Moon sign column in `ephemeris` (may be `moon_sign`, `moon_rashi`, `moon_sign_num`).

2. Create `platform/src/lib/retrieve/query_chandra_balam.ts`:

```typescript
// Input: { start_date: string, end_date: string, native_natal_moon_sign?: number }
// Output per date: { date, moon_sign_name, moon_sign_num, position, classification }
```

3. SQL:
```sql
SELECT date, <moon_sign_col> AS moon_sign_num,
  ((<moon_sign_col> - 12 + 12) % 12) + 1 AS chandra_position
FROM ephemeris
WHERE date >= $start_date AND date <= $end_date
ORDER BY date
```

4. Map moon_sign_num → sign name (Aries..Pisces) and position → benefic/malefic.

---

## Step: Export from index.ts

Add both tools to `platform/src/lib/retrieve/index.ts`:

```typescript
export { queryTaraBalam } from './query_tara_balam'
export { queryChandraBalam } from './query_chandra_balam'
```

Also ensure the RETRIEVAL_TOOLS registry (however it's structured) includes these two tools under the keys `'query_tara_balam'` and `'query_chandra_balam'`.

---

## Step: Commit

```bash
git add platform/src/lib/retrieve/query_tara_balam.ts \
        platform/src/lib/retrieve/query_chandra_balam.ts \
        platform/src/lib/retrieve/index.ts
git commit -m "feat(R2): query_tara_balam + query_chandra_balam retrieval engines

- Tara Balam: 9-fold nakshatra cycle from natal Moon PBh (nak index 25)
- Chandra Balam: transit Moon sign vs natal Pisces (sign 12)
- Both exported from retrieve/index.ts
- Registered in RETRIEVAL_TOOLS under correct keys

Closes R2-S1 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `test -f platform/src/lib/retrieve/query_tara_balam.ts`
2. `test -f platform/src/lib/retrieve/query_chandra_balam.ts`
3. Both exported in `platform/src/lib/retrieve/index.ts`
4. Both registered in RETRIEVAL_TOOLS registry
5. For birth date 1984-02-05: query_tara_balam returns tara_number=1 (Janma) when called directly
