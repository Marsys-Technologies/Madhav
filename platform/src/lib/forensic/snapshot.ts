import 'server-only'
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '@/lib/retrieval/address_resolver'

export interface PlanetPlacement {
  planet: string
  sign: string
  house: number
  degreeDms: string
}

export interface ForensicChart {
  chartId: string
  lagnaSign: string
  lagnaDegreeDms: string
  houses: Array<{ house: number; sign: string; planets: string[] }>
  topYogas: string[]
  currentDasha: { md: string; ad: string; adEnd: string } | null
  isEmpty: boolean
}

// Sign order by house number when Lagna is known
const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

// Canonical L1 chart for Abhisek Mohanty (FORENSIC v8.0 §4; chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
// Used as fallback when chart_facts table is not yet ingested for a chart.
function buildAbhisekFallback(chartId: string): ForensicChart {
  return {
    chartId,
    lagnaSign: 'Aries',
    lagnaDegreeDms: '12°23′55″',
    houses: [
      { house: 1, sign: 'Aries', planets: [] },
      { house: 2, sign: 'Taurus', planets: ['Rahu'] },
      { house: 3, sign: 'Gemini', planets: [] },
      { house: 4, sign: 'Cancer', planets: [] },
      { house: 5, sign: 'Leo', planets: [] },
      { house: 6, sign: 'Virgo', planets: [] },
      { house: 7, sign: 'Libra', planets: ['Saturn', 'Mars'] },
      { house: 8, sign: 'Scorpio', planets: ['Ketu'] },
      { house: 9, sign: 'Sagittarius', planets: ['Jupiter', 'Venus'] },
      { house: 10, sign: 'Capricorn', planets: ['Sun', 'Mercury'] },
      { house: 11, sign: 'Aquarius', planets: ['Moon'] },
      { house: 12, sign: 'Pisces', planets: [] },
    ],
    topYogas: ['Kalpadruma', 'Nipuna (Budha-Aditya)', 'Kedaara'],
    // DSH.V.023 — current as of 2026-04-30 (FORENSIC dates canonical per GAP.09)
    currentDasha: { md: 'Mercury', ad: 'Saturn', adEnd: '2027-08-21' },
    isEmpty: false,
  }
}

// TODO(ws-2): repoint via ganita_positions + ganita_dashas once Brahma depth-build
// populates those tables for every chart_id. Parsing logic lives in the original
// chart_facts query block (pre-WS-0C); restore and adapt column names.
export async function getForensicSnapshot(chartId: string): Promise<ForensicChart> {
  // chart_facts dropped in WS-0; ganita_positions schema differs (no fact_id/category).
  // Always return the FORENSIC_ASTROLOGICAL_DATA fallback until WS-2 Brahma repoint.
  try {
    const result = { rows: [] as { fact_id: string; category: string; value_text: string | null; value_number: number | null }[] }

    if (result.rows.length === 0) {
      return buildAbhisekFallback(chartId)
    }

    // Parse planet rows: fact_id = PLN.SUN.SIGN → planet=SUN, attr=SIGN
    const planetSigns: Record<string, number> = {}
    const houseSignMap: Record<number, string> = {}
    let lagnaSign = ''
    let lagnaDegreeDms = ''

    for (const row of result.rows) {
      if (row.category === 'planet' && row.fact_id.endsWith('.SIGN') && row.value_text) {
        const planet = row.fact_id.split('.')[1]
        const signIdx = SIGNS.indexOf(row.value_text)
        if (signIdx >= 0) planetSigns[planet] = signIdx
      }
      if (row.category === 'house' && row.fact_id.endsWith('.SIGN') && row.value_text) {
        const houseNum = parseInt(row.fact_id.split('.')[1])
        if (!isNaN(houseNum)) houseSignMap[houseNum] = row.value_text
      }
      if (row.fact_id === 'MET.LAGNA.SIGN' && row.value_text) lagnaSign = row.value_text
      if (row.fact_id === 'MET.LAGNA.DEG' && row.value_text) lagnaDegreeDms = row.value_text
    }

    if (!lagnaSign) return buildAbhisekFallback(chartId)

    const lagnaSignIdx = SIGNS.indexOf(lagnaSign)

    // Build house array: house N has sign at (lagnaSignIdx + N - 1) % 12
    const houses = Array.from({ length: 12 }, (_, i) => {
      const houseNum = i + 1
      const sign = houseSignMap[houseNum] ?? SIGNS[(lagnaSignIdx + i) % 12]
      return { house: houseNum, sign, planets: [] as string[] }
    })

    // Assign planets to houses. Values sourced from the graha SSoT
    // (address_resolver.grahaCodeOf + GRAHA_CODE_TO_NAME) rather than
    // hardcoded literals — ADHIṢṬHĀNA Lane A2.
    const PLANET_DISPLAY: Record<string, string> = Object.fromEntries(
      ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU']
        .map(p => [p, GRAHA_CODE_TO_NAME[grahaCodeOf(p)]]),
    )
    for (const [planet, signIdx] of Object.entries(planetSigns)) {
      const houseIdx = ((signIdx - lagnaSignIdx) % 12 + 12) % 12
      const displayName = PLANET_DISPLAY[planet] ?? planet
      houses[houseIdx]?.planets.push(displayName)
    }

    return {
      chartId,
      lagnaSign,
      lagnaDegreeDms,
      houses,
      topYogas: ['Kalpadruma', 'Nipuna (Budha-Aditya)', 'Kedaara'],
      currentDasha: { md: 'Mercury', ad: 'Saturn', adEnd: '2027-08-21' },
      isEmpty: false,
    }
  } catch {
    return buildAbhisekFallback(chartId)
  }
}
