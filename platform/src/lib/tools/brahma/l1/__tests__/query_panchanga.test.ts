/**
 * query_panchanga.test.ts — Unit tests for brahma/l1/query_panchanga.ts (GA-1-7).
 *
 * Tests the retrieval layer: row→BirthPanchanga mapping, error surface,
 * and FORENSIC spot-check for native 1984-02-05.
 *
 * No live DB required — the `@/lib/db/client` module is mocked.
 *
 * Source: BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §B ganita.panchanga (GA-1-7)
 * Author: Brahma swarm Śilpī, 2026-06-03
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock DB client before importing the module under test ─────────────────────
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
import {
  queryPanchanga,
  queryPanchangaOrNull,
  PanchangaNotFoundError,
  type BirthPanchanga,
} from '../query_panchanga'

// ── FORENSIC reference row (native 1984-02-05, 10:43 IST, Bhubaneswar) ────────
// Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §Panchanga
// Phase 4C FORENSIC spot-check PASS 5/5 (2026-05-21):
//   tithi=Shukla Tritiya, vara=Ravivara, moon_nakshatra=Purva Bhadrapada,
//   yoga=Shiva, karana=Garaja

// FORENSIC ground truth for native 1984-02-05 10:43 IST Bhubaneswar
// Authoritative source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §15 Panchanga DNA
// Phase 4C FORENSIC spot-check PASS 5/5 (2026-05-21):
//   tithi=Shukla Tritiya (3), vara=Ravivara (1), nakshatra=Purva Bhadrapada (25),
//   yoga=Shiva (14), karana=Garaja (5)
// nakshatra_index uses PyJHora 1-based convention (1=Ashwini..27=Revati)
// source_citation per GA-1-7 contract: "PyJHora / SwissEph DE441"
const FORENSIC_ROW = {
  chart_id: 'native-1984-chart-uuid',
  build_id: 'brahma-ga-1-7-test',
  tithi_num: 3,
  tithi_name: 'Shukla Tritiya',
  paksha: 'shukla',
  tithi_elapsed_pct: 72.5,
  vara_num: 1,
  vara_name: 'Ravivara',
  moon_nakshatra: 'Purva Bhadrapada',
  moon_nakshatra_index: 25,
  moon_nakshatra_pada: 2,
  moon_longitude_deg: 335.6789,
  yoga_num: 14,
  yoga_name: 'Shiva',
  karana_num: 5,
  karana_name: 'Garaja',
  sunrise_ist: '06:36:00',
  sunrise_utc: '1984-02-05T01:06:00+00:00',
  ayanamsha_id: 'lahiri',
  source_citation: 'PyJHora / SwissEph DE441',
  engine_version: 'ganita.engine/1.0.0',
  computed_at: '2026-06-03T00:00:00+00:00',
}

const mockQuery = vi.mocked(query)

beforeEach(() => {
  vi.clearAllMocks()
})

// ── FORENSIC spot-check ───────────────────────────────────────────────────────

describe('queryPanchanga — FORENSIC spot-check (native 1984-02-05)', () => {
  beforeEach(() => {
    mockQuery.mockResolvedValue({ rows: [FORENSIC_ROW] } as any)
  })

  it('returns tithi=Shukla Tritiya', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.tithi.name).toBe('Shukla Tritiya')
    expect(result.tithi.num).toBe(3)
    expect(result.tithi.paksha).toBe('shukla')
  })

  it('returns vara=Ravivara', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.vara.name).toBe('Ravivara')
    expect(result.vara.num).toBe(1)
  })

  it('returns moon_nakshatra=Purva Bhadrapada (index 25, 1-based PyJHora)', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.nakshatra.name).toBe('Purva Bhadrapada')
    expect(result.nakshatra.index).toBe(25)
    expect(result.nakshatra.pada).toBe(2)
  })

  it('returns yoga=Shiva (num 14)', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.yoga.name).toBe('Shiva')
    expect(result.yoga.num).toBe(14)
  })

  it('returns karana=Garaja', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.karana.name).toBe('Garaja')
    expect(result.karana.num).toBe(5)
  })
})

// ── Row → BirthPanchanga mapping ──────────────────────────────────────────────

describe('queryPanchanga — row-to-type mapping', () => {
  beforeEach(() => {
    mockQuery.mockResolvedValue({ rows: [FORENSIC_ROW] } as any)
  })

  it('maps all provenance fields correctly', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.chart_id).toBe('native-1984-chart-uuid')
    expect(result.build_id).toBe('brahma-ga-1-7-test')
    expect(result.ayanamsha_id).toBe('lahiri')
    expect(result.source_citation).toBe('PyJHora / SwissEph DE441')
    expect(result.engine_version).toBe('ganita.engine/1.0.0')
    expect(result.computed_at).toBe('2026-06-03T00:00:00+00:00')
  })

  it('maps sunrise fields correctly', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.sunrise_ist).toBe('06:36:00')
    expect(result.sunrise_utc).toBe('1984-02-05T01:06:00+00:00')
  })

  it('maps moon longitude correctly', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.nakshatra.longitude_deg).toBe(335.6789)
  })

  it('maps tithi elapsed_pct correctly', async () => {
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.tithi.elapsed_pct).toBe(72.5)
  })

  it('correctly handles null tithi_elapsed_pct', async () => {
    mockQuery.mockResolvedValue({
      rows: [{ ...FORENSIC_ROW, tithi_elapsed_pct: null }],
    } as any)
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.tithi.elapsed_pct).toBeUndefined()
  })

  it('correctly handles null moon_longitude_deg', async () => {
    mockQuery.mockResolvedValue({
      rows: [{ ...FORENSIC_ROW, moon_longitude_deg: null }],
    } as any)
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.nakshatra.longitude_deg).toBeNull()
  })

  it('correctly handles null sunrise fields', async () => {
    mockQuery.mockResolvedValue({
      rows: [{ ...FORENSIC_ROW, sunrise_ist: null, sunrise_utc: null }],
    } as any)
    const result = await queryPanchanga('native-1984-chart-uuid')
    expect(result.sunrise_ist).toBeNull()
    expect(result.sunrise_utc).toBeNull()
  })
})

// ── DB query mechanics ────────────────────────────────────────────────────────

describe('queryPanchanga — DB query mechanics', () => {
  it('calls query() with the correct chart_id parameter', async () => {
    mockQuery.mockResolvedValue({ rows: [FORENSIC_ROW] } as any)
    await queryPanchanga('my-chart-uuid')
    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0] as [string, string[]]
    expect(sql).toContain('chart_panchanga')
    expect(sql).toContain('WHERE chart_id = $1')
    expect(params).toEqual(['my-chart-uuid'])
  })

  it('orders by computed_at DESC and takes LIMIT 1', async () => {
    mockQuery.mockResolvedValue({ rows: [FORENSIC_ROW] } as any)
    await queryPanchanga('any-chart-uuid')
    const [sql] = mockQuery.mock.calls[0] as [string, string[]]
    expect(sql).toContain('ORDER BY computed_at DESC')
    expect(sql).toContain('LIMIT 1')
  })
})

// ── PanchangaNotFoundError ────────────────────────────────────────────────────

describe('queryPanchanga — PanchangaNotFoundError', () => {
  it('throws PanchangaNotFoundError when no rows returned', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as any)
    await expect(queryPanchanga('nonexistent-chart')).rejects.toThrow(
      PanchangaNotFoundError,
    )
  })

  it('error message contains the chart_id', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as any)
    await expect(queryPanchanga('my-missing-chart')).rejects.toThrow(
      'my-missing-chart',
    )
  })

  it('error name is PanchangaNotFoundError', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as any)
    let err: Error | null = null
    try {
      await queryPanchanga('x')
    } catch (e) {
      err = e as Error
    }
    expect(err).toBeInstanceOf(PanchangaNotFoundError)
    expect(err!.name).toBe('PanchangaNotFoundError')
  })

  it('propagates DB errors', async () => {
    mockQuery.mockRejectedValue(new Error('DB connection refused'))
    await expect(queryPanchanga('any-chart')).rejects.toThrow('DB connection refused')
  })
})

// ── queryPanchangaOrNull ──────────────────────────────────────────────────────

describe('queryPanchangaOrNull', () => {
  it('returns null when chart not found', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as any)
    const result = await queryPanchangaOrNull('nonexistent')
    expect(result).toBeNull()
  })

  it('returns BirthPanchanga when chart exists', async () => {
    mockQuery.mockResolvedValue({ rows: [FORENSIC_ROW] } as any)
    const result = await queryPanchangaOrNull('native-1984-chart-uuid')
    expect(result).not.toBeNull()
    expect(result!.tithi.name).toBe('Shukla Tritiya')
  })

  it('re-throws non-not-found DB errors', async () => {
    mockQuery.mockRejectedValue(new Error('timeout'))
    await expect(queryPanchangaOrNull('any-chart')).rejects.toThrow('timeout')
  })
})
