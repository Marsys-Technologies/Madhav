/**
 * query_panchanga.ts — Brahma GA-1-7: ganita.panchanga retrieval tool.
 *
 * Returns the birth-moment panchanga (five limbs: tithi, vara, nakshatra, yoga, karana)
 * for a given chart_id from the chart_panchanga table.
 *
 * Contract:
 *   - Input:  chart_id (UUID string)
 *   - Output: BirthPanchanga (5 limbs + metadata)
 *   - Source: chart_panchanga table (written by panchanga_writer.py)
 *   - FORENSIC spot-check (native 1984-02-05):
 *       tithi=Shukla Tritiya, vara=Ravivara, moon_nakshatra=Purva Bhadrapada,
 *       yoga=Shiva, karana=Garaja
 *
 * Source: BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §B ganita.panchanga (GA-1-7)
 * Author: Brahma swarm Śilpī, 2026-06-03
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Types ────────────────────────────────────────────────────────────────────

export interface BirthPanchangaTithi {
  num: number           // 1..30
  name: string          // e.g. 'Shukla Tritiya'
  paksha: string        // 'shukla' | 'krishna'
  elapsed_pct?: number  // 0..100 (% elapsed at birth); may be null
}

export interface BirthPanchangaVara {
  num: number           // 1 (Sun) .. 7 (Sat)
  name: string          // e.g. 'Ravivara'
}

export interface BirthPanchangaNakshatra {
  index: number         // 0-based (0=Ashwini .. 26=Revati)
  name: string          // e.g. 'Purva Bhadrapada'
  pada: number          // 1..4
  longitude_deg?: number | null  // sidereal Lahiri moon longitude
}

export interface BirthPanchangaYoga {
  num: number           // 1..27
  name: string          // e.g. 'Shiva'
}

export interface BirthPanchangaKarana {
  num: number           // 1..11
  name: string          // e.g. 'Garaja'
}

/** Full birth panchanga — the five limbs + provenance. */
export interface BirthPanchanga {
  chart_id: string
  tithi: BirthPanchangaTithi
  vara: BirthPanchangaVara
  nakshatra: BirthPanchangaNakshatra
  yoga: BirthPanchangaYoga
  karana: BirthPanchangaKarana
  /** Sunrise IST at birth location, 'HH:MM:SS' or null */
  sunrise_ist: string | null
  /** Sunrise UTC ISO string or null */
  sunrise_utc: string | null
  ayanamsha_id: string
  source_citation: string
  engine_version: string
  computed_at: string
  build_id: string
}

export class PanchangaNotFoundError extends Error {
  constructor(chartId: string) {
    super(`No panchanga found for chart_id=${chartId}`)
    this.name = 'PanchangaNotFoundError'
  }
}

// ── DB row type ───────────────────────────────────────────────────────────────

interface ChartPanchangaRow {
  chart_id: string
  build_id: string
  tithi_num: number
  tithi_name: string
  paksha: string
  tithi_elapsed_pct: number | null
  vara_num: number
  vara_name: string
  moon_nakshatra: string
  moon_nakshatra_index: number
  moon_nakshatra_pada: number
  moon_longitude_deg: number | null
  yoga_num: number
  yoga_name: string
  karana_num: number
  karana_name: string
  sunrise_ist: string | null
  sunrise_utc: string | null
  ayanamsha_id: string
  source_citation: string
  engine_version: string
  computed_at: string
}

// ── Query ────────────────────────────────────────────────────────────────────

const SELECT_SQL = `
  SELECT
    chart_id, build_id,
    tithi_num, tithi_name, paksha, tithi_elapsed_pct,
    vara_num, vara_name,
    moon_nakshatra, moon_nakshatra_index, moon_nakshatra_pada, moon_longitude_deg,
    yoga_num, yoga_name,
    karana_num, karana_name,
    sunrise_ist, sunrise_utc::text AS sunrise_utc,
    ayanamsha_id, source_citation, engine_version,
    computed_at::text AS computed_at
  FROM chart_panchanga
  WHERE chart_id = $1
  ORDER BY computed_at DESC
  LIMIT 1
`

function rowToPanchanga(row: ChartPanchangaRow): BirthPanchanga {
  return {
    chart_id: row.chart_id,
    tithi: {
      num: row.tithi_num,
      name: row.tithi_name,
      paksha: row.paksha,
      elapsed_pct: row.tithi_elapsed_pct ?? undefined,
    },
    vara: {
      num: row.vara_num,
      name: row.vara_name,
    },
    nakshatra: {
      index: row.moon_nakshatra_index,
      name: row.moon_nakshatra,
      pada: row.moon_nakshatra_pada,
      longitude_deg: row.moon_longitude_deg,
    },
    yoga: {
      num: row.yoga_num,
      name: row.yoga_name,
    },
    karana: {
      num: row.karana_num,
      name: row.karana_name,
    },
    sunrise_ist: row.sunrise_ist,
    sunrise_utc: row.sunrise_utc,
    ayanamsha_id: row.ayanamsha_id,
    source_citation: row.source_citation,
    engine_version: row.engine_version,
    computed_at: row.computed_at,
    build_id: row.build_id,
  }
}

/**
 * Retrieve the birth-moment panchanga for a chart.
 *
 * @param chartId UUID of the chart (maps to chart_panchanga.chart_id).
 * @returns BirthPanchanga — the five limbs + provenance metadata.
 * @throws PanchangaNotFoundError if no row exists for the chart.
 * @throws Error on DB failure.
 */
export async function queryPanchanga(chartId: string): Promise<BirthPanchanga> {
  const result = await query<ChartPanchangaRow>(SELECT_SQL, [chartId])
  if (result.rows.length === 0) {
    throw new PanchangaNotFoundError(chartId)
  }
  return rowToPanchanga(result.rows[0])
}

/**
 * Retrieve the birth panchanga, returning null instead of throwing on miss.
 */
export async function queryPanchangaOrNull(
  chartId: string,
): Promise<BirthPanchanga | null> {
  try {
    return await queryPanchanga(chartId)
  } catch (err) {
    if (err instanceof PanchangaNotFoundError) return null
    throw err
  }
}
