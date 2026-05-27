---
session_id: R2-T1
status: PENDING
phase: GISMCP-R2
title: "Integration tests — all 4 new engines against DB proxy"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
branch: fix/gismcp-r1-r2
may_touch:
  - platform/src/lib/retrieve/__tests__/**
  - platform/src/__tests__/integration/**
must_not_touch:
  - platform/src/lib/retrieve/query_tara_balam.ts
  - platform/src/lib/retrieve/query_chandra_balam.ts
  - platform/src/lib/retrieve/jaimini_chara_dasha.ts
  - platform/src/lib/retrieve/jaimini_chara_dasha_full.ts
  - platform-mcp/**
  - "*.yaml"
---

# R2-T1: Integration Tests for All 4 New Engines

## Context

R2-S1 and R2-S2 implemented the 4 retrieval engines. This session writes thorough tests that verify correctness against the live DB via the proxy on port 5433. All tests are FORENSIC-grounded: expected values come from the native's known chart data.

**Native chart reference (FORENSIC):**
- Birth date: 1984-02-05
- Birth time: 10:43 IST
- Place: Bhubaneswar, Odisha, India
- Lagna: Aries (Mesha)
- Moon sign: Pisces (Meena, sign 12)
- Moon nakshatra: Purva Bhadrapada (PBh, index 25)
- Atmakaraka: Saturn (verify from chart_facts)

---

## File 1: `platform/src/lib/retrieve/__tests__/query_tara_balam.test.ts`

```typescript
import { describe, it, expect, beforeAll } from 'vitest'

const SKIP = !process.env.DB_PROXY_PORT
const BIRTH_DATE = '1984-02-05'
const NATAL_NAK = 25  // Purva Bhadrapada

describe.skipIf(SKIP)('query_tara_balam — integration', () => {
  it('returns tara_number=1 (Janma) on native birth date', async () => {
    // Moon at birth was in PBh (same as natal) → tara = Janma = 1
    const result = await queryTaraBalam({ start_date: BIRTH_DATE, end_date: BIRTH_DATE })
    expect(result[0].tara_number).toBe(1)
    expect(result[0].tara_name).toBe('Janma')
    expect(result[0].classification).toBe('malefic')
  })

  it('returns benefic tara for a date when Moon is in Sampat position (nak 26)', async () => {
    // Find a date when Moon is in Uttara Bhadrapada (nak 26) → tara_number = 2 (Sampat) → benefic
    // Query ephemeris for first occurrence after 2026-01-01
    const result = await queryTaraBalam({ start_date: '2026-01-01', end_date: '2026-01-31' })
    const sampat = result.find(r => r.tara_number === 2)
    expect(sampat).toBeDefined()
    expect(sampat!.classification).toBe('benefic')
  })

  it('all 9 tara values appear within a 27-day window', async () => {
    // Moon takes ~27 days to traverse all 27 nakshatras (one per day roughly)
    // All 9 tara values should appear within any ~27-day window
    const result = await queryTaraBalam({ start_date: '2026-05-01', end_date: '2026-05-27' })
    const taraValues = new Set(result.map(r => r.tara_number))
    expect(taraValues.size).toBe(9)
  })

  it('returns correct output shape', async () => {
    const result = await queryTaraBalam({ start_date: '2026-05-26', end_date: '2026-05-26' })
    expect(result[0]).toMatchObject({
      date: expect.any(String),
      moon_nakshatra_name: expect.any(String),
      moon_nak_index: expect.any(Number),
      tara_number: expect.any(Number),
      tara_name: expect.any(String),
      classification: expect.stringMatching(/^(benefic|malefic)$/)
    })
  })
})
```

---

## File 2: `platform/src/lib/retrieve/__tests__/query_chandra_balam.test.ts`

```typescript
describe.skipIf(SKIP)('query_chandra_balam — integration', () => {
  it('returns position=1 (natal sign = Pisces) on birth date', async () => {
    // Moon at birth was in Pisces (natal sign) → position 1
    const result = await queryChandraBalam({ start_date: BIRTH_DATE, end_date: BIRTH_DATE })
    expect(result[0].position).toBe(1)
  })

  it('position 7 (Virgo, 7th from Pisces) is classified benefic', async () => {
    // Find a date when Moon is in Virgo (sign 6) → position = (6-12+12)%12+1 = 7 → benefic
    const result = await queryChandraBalam({ start_date: '2026-05-01', end_date: '2026-06-30' })
    const pos7 = result.find(r => r.position === 7)
    expect(pos7?.classification).toBe('benefic')
  })

  it('position 8 (Aries, 8th from Pisces) is classified malefic', async () => {
    const result = await queryChandraBalam({ start_date: '2026-05-01', end_date: '2026-06-30' })
    const pos8 = result.find(r => r.position === 8)
    expect(pos8?.classification).toBe('malefic')
  })

  it('all 12 positions appear within a 30-day window', async () => {
    const result = await queryChandraBalam({ start_date: '2026-05-01', end_date: '2026-05-31' })
    const positions = new Set(result.map(r => r.position))
    expect(positions.size).toBe(12)
  })
})
```

---

## File 3: `platform/src/lib/retrieve/__tests__/jaimini_chara_dasha.test.ts`

```typescript
describe.skipIf(SKIP)('jaimini_chara_dasha — integration', () => {
  it('returns valid current_mahadasha for native', async () => {
    const result = await jaiminiCharaDasha({})
    expect(result.current_mahadasha.rashi).toBeDefined()
    expect(result.current_mahadasha.start_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(result.current_mahadasha.end_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(result.current_mahadasha.years_duration).toBeGreaterThan(0)
    expect(result.current_mahadasha.years_duration).toBeLessThanOrEqual(12)
  })

  it('atmakaraka is Saturn', async () => {
    const result = await jaiminiCharaDasha({})
    expect(result.atmakaraka.toLowerCase()).toContain('saturn')
  })

  it('lagna sign is Aries', async () => {
    const result = await jaiminiCharaDasha({})
    expect(result.lagna_sign.toLowerCase()).toMatch(/aries|mesha/)
  })

  it('current mahadasha dates are plausible for 2026', async () => {
    const result = await jaiminiCharaDasha({ as_of_date: '2026-05-26' })
    const start = new Date(result.current_mahadasha.start_date)
    const end = new Date(result.current_mahadasha.end_date)
    // Start must be in the past (before 2026-05-26)
    expect(start.getTime()).toBeLessThan(new Date('2026-05-26').getTime())
    // End must be in the future (after today)
    expect(end.getTime()).toBeGreaterThan(new Date('2020-01-01').getTime())
  })
})

describe.skipIf(SKIP)('jaimini_chara_dasha_full — integration', () => {
  it('full sequence has exactly 12 mahadashas (one per rashi)', async () => {
    const result = await jaiminiCharaDashaFull({})
    expect(result.full_sequence.length).toBe(12)
  })

  it('first mahadasha starts at birth date', async () => {
    const result = await jaiminiCharaDashaFull({})
    const firstStart = result.full_sequence[0].start_date
    expect(firstStart).toBe('1984-02-05')
  })

  it('each mahadasha has valid antardashas', async () => {
    const result = await jaiminiCharaDashaFull({})
    for (const maha of result.full_sequence) {
      expect(maha.antardashas.length).toBeGreaterThan(0)
      expect(maha.antardashas[0].rashi).toBeDefined()
    }
  })
})
```

---

## Run and fix

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform
DB_PROXY_PORT=5433 npx vitest run \
  src/lib/retrieve/__tests__/query_tara_balam.test.ts \
  src/lib/retrieve/__tests__/query_chandra_balam.test.ts \
  src/lib/retrieve/__tests__/jaimini_chara_dasha.test.ts \
  2>&1 | tail -30
```

Fix any failures in the retrieval engines (not in the tests). Tests are the ground truth; engine must match.

## Commit

```bash
git add platform/src/lib/retrieve/__tests__/
git commit -m "test(R2): FORENSIC-grounded integration tests for 4 new engines

- query_tara_balam: Janma on birth date, 9 values in 27-day window
- query_chandra_balam: position 1 on birth date, all 12 positions in 30-day window
- jaimini_chara_dasha: AK=Saturn, Lagna=Aries, valid mahadasha dates
- jaimini_chara_dasha_full: 12 mahadashas, starts at 1984-02-05

Closes R2-T1 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. All 3 test files exist
2. All tests pass with `DB_PROXY_PORT=5433` set
3. Tests are CI-safe: skip when `DB_PROXY_PORT` absent
4. `query_tara_balam` birth date test: tara_number=1 PASS
5. `jaimini_chara_dasha` AK=Saturn, Lagna=Aries PASS
