/**
 * elect_transit_null_f48.test.ts — PARIŚEṢA F-48, serving-layer half.
 *
 * F-48's ruling: `transit_quality` is REAL classical Gochara or it is null —
 * never a plausible neutral number standing in for "not assessed". The Python
 * scorer owns the computation; this file pins the ELECT facade's obligation on
 * the OTHER side of that contract: a null must be reported as not-assessed, and
 * must never be silently absorbed into the driver list as if the transits had
 * been checked and merely fell below the 0.6 driver threshold.
 *
 * Why this needs its own test: `windowDrivers`' guard is a `>=` comparison, and
 * in JS `null >= 0.6` is `false` — so a null would have produced exactly the
 * same driver list as a genuinely-weak-but-assessed transit score. That silent
 * equivalence is the §N.8 defect one layer up from the one F-48 fixed, and
 * nothing else in the suite would catch it.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockHandleMuhurtaFinder = vi.fn()

vi.mock('../../muhurta_finder.js', async () => {
  const actual = await vi.importActual<typeof import('../../muhurta_finder.js')>('../../muhurta_finder.js')
  return {
    ...actual,
    handleMuhurtaFinder: (...args: unknown[]) => mockHandleMuhurtaFinder(...args),
  }
})

const mockFetchLatticeSubstrate = vi.fn()

vi.mock('../../../lib/kala_lattice_query.js', async () => {
  const actual = await vi.importActual<typeof import('../../../lib/kala_lattice_query.js')>('../../../lib/kala_lattice_query.js')
  return {
    ...actual,
    fetchLatticeSubstrate: (...args: unknown[]) => mockFetchLatticeSubstrate(...args),
  }
})

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u1', key_id: 'k1', role: 'guest' as const }

function emptySubstrate() {
  return {
    lattice_rows: [], parihara_rules: [], census_rows: [],
    lattice_available: true, parihara_available: true, census_available: true,
    unavailable_reason: null,
  }
}

function resultWithTransit(transit_quality: number | null, transit_details?: unknown) {
  return {
    ok: true,
    chart_id: CHART_ID,
    action_type: 'business',
    query_window: { start: '2026-08-01', end: '2026-10-30' },
    windows: [
      {
        start: '2026-08-05T00:00:00Z',
        end: '2026-08-07T00:00:00Z',
        score: 0.82,
        factors: {
          panchanga_quality: 0.7,
          dasha_quality: 0.8,
          transit_quality,
          ...(transit_details ? { transit_details } : {}),
          signal_activation: 0.5,
          panchanga_details: {
            tithi_name: 'Tritiya', vara_lord: 'Guru', moon_nakshatra: 'Pushya',
            yoga: 'Siddha', inauspicious_windows: [],
          },
          dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
          avoid_notes: [],
        },
        source_citation: 'BPHS ch.46',
        hard_flag: false,
        disqualified: false,
        rank_penalty_reason: [],
        hora_ladder: [],
      },
    ],
    window_count: 1,
    provenance_envelope: { source: 'phala.muhurta', asset: 'PH-4-4' },
  }
}

async function drivers(transit_quality: number | null, transit_details?: unknown) {
  mockHandleMuhurtaFinder.mockResolvedValue({
    structuredContent: { object: resultWithTransit(transit_quality, transit_details) },
    content: [{ type: 'text', text: '{}' }],
  })
  const { handleKalaElectGet } = await import('../elect.js')
  const { response } = await handleKalaElectGet(
    { chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL,
  )
  return response!.candidates[0]!.drivers
}

describe('F-48 — kala_elect_get reports an unassessed transit honestly', () => {
  beforeEach(() => {
    mockHandleMuhurtaFinder.mockReset()
    mockFetchLatticeSubstrate.mockReset()
    mockFetchLatticeSubstrate.mockResolvedValue(emptySubstrate())
  })

  it('names transit_quality as not_assessed, with the reason, when it is null', async () => {
    const d = await drivers(null, {
      available: false,
      unavailable_reason: 'ephemeris_daily_unavailable_for_date',
    })
    const entry = d.find((s: string) => s.startsWith('transit_quality='))
    expect(entry).toBeDefined()
    expect(entry).toContain('not_assessed')
    expect(entry).toContain('ephemeris_daily_unavailable_for_date')
  })

  it('still says not_assessed when transit_details is absent entirely', async () => {
    const d = await drivers(null)
    expect(d.some((s: string) => s === 'transit_quality=not_assessed (unavailable)')).toBe(true)
  })

  it('a null is NOT reported the same way as an assessed-but-weak transit', async () => {
    const nullDrivers = await drivers(null, {
      available: false, unavailable_reason: 'natal_moon_sign_unavailable',
    })
    const weakDrivers = await drivers(0.2, { available: true })
    expect(nullDrivers).not.toEqual(weakDrivers)
    // The assessed-but-weak case correctly contributes NO transit driver
    // (below the 0.6 threshold) — the null case must be visible instead.
    expect(weakDrivers.some((s: string) => s.startsWith('transit_quality='))).toBe(false)
    expect(nullDrivers.some((s: string) => s.startsWith('transit_quality='))).toBe(true)
  })

  it('a genuinely strong REAL transit score still reads as a driver', async () => {
    const d = await drivers(0.85, { available: true, method: 'gochara_from_natal_moon' })
    expect(d.some((s: string) => s === 'transit_quality=0.85')).toBe(true)
  })
})
