/**
 * query_dasamsha_career.ts — MCP Tier 3 surgical primitive: D10 (Dasamsha) career analysis.
 *
 * What it does:
 *   1. Fetches D10 (Dasamsha) chart positions via divisional_query({varga:"D10"}).
 *   2. Parses planet sign/house positions in D10.
 *   3. Applies classical career-indicator rules to flag significant career signals.
 *
 * Classical rules applied:
 *   - 10H lord in D10 (any house): strong career indicator.
 *   - Sun, Saturn, Mercury in D10 10H: additional career strength (career significators).
 *   - 10H lord in own sign, exalted, or in kendra (1,4,7,10) / trikona (1,5,9): favourable.
 *   - 10H lord in 6H, 8H, or 12H: career obstacles.
 *
 * Output shape:
 *   { d10_ascendant, planets, career_indicators }
 *
 * TR-P7-S4: new MCP tool.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

// ── Constants ──────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

/** Canonical sign list in zodiacal order. */
const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

type SignName = typeof SIGNS[number]

/** 10H lord by sign (traditional Parashari lordships). */
const TENTH_LORD_BY_SIGN: Record<SignName, string> = {
  Aries:       'Saturn',   // 10H = Capricorn
  Taurus:      'Saturn',   // 10H = Aquarius
  Gemini:      'Mars',     // 10H = Pisces... wait — 10H from Gemini Asc = Pisces → Jupiter
  Cancer:      'Mars',     // 10H = Aries → Mars
  Leo:         'Venus',    // 10H = Taurus → Venus
  Virgo:       'Mercury',  // 10H = Gemini → Mercury
  Libra:       'Moon',     // 10H = Cancer → Moon
  Scorpio:     'Sun',      // 10H = Leo → Sun
  Sagittarius: 'Mercury',  // 10H = Virgo → Mercury
  Capricorn:   'Venus',    // 10H = Libra → Venus
  Aquarius:    'Mars',     // 10H = Scorpio → Mars
  Pisces:      'Jupiter',  // 10H = Sagittarius → Jupiter
}

// Corrected: Gemini Asc → 10H = Pisces → Jupiter
const CORRECTED_TENTH_LORD: Record<SignName, string> = {
  ...TENTH_LORD_BY_SIGN,
  Gemini: 'Jupiter',  // 10H from Gemini = Pisces → Jupiter
}

/** 10H sign name from D10 ascendant sign. */
function tenthSignFrom(ascSign: string): string {
  const idx = SIGNS.indexOf(ascSign as SignName)
  if (idx < 0) return 'Unknown'
  return SIGNS[(idx + 9) % 12]!  // 10th sign = ascendant index + 9 (0-based)
}

/** Own-sign and exaltation map per planet. */
const OWN_SIGNS: Record<string, string[]> = {
  Sun:     ['Leo'],
  Moon:    ['Cancer'],
  Mars:    ['Aries', 'Scorpio'],
  Mercury: ['Gemini', 'Virgo'],
  Jupiter: ['Sagittarius', 'Pisces'],
  Venus:   ['Taurus', 'Libra'],
  Saturn:  ['Capricorn', 'Aquarius'],
  Rahu:    [],
  Ketu:    [],
}

const EXALTATION_SIGNS: Record<string, string> = {
  Sun:     'Aries',
  Moon:    'Taurus',
  Mars:    'Capricorn',
  Mercury: 'Virgo',
  Jupiter: 'Cancer',
  Venus:   'Pisces',
  Saturn:  'Libra',
}

const KENDRA_HOUSES = new Set([1, 4, 7, 10])
const TRIKONA_HOUSES = new Set([1, 5, 9])
const DUSTHANA_HOUSES = new Set([6, 8, 12])

/** Career-significator planets in 10H of D10. */
const CAREER_SIGNIFICATORS = new Set(['Sun', 'Saturn', 'Mercury'])

// ── Result types ───────────────────────────────────────────────────────────────

export interface D10PlanetRecord {
  planet: string
  sign: string
  house: number
  dignity: string
}

export interface CareerIndicator {
  indicator: string
  planet: string
  classical_rule: string
}

export interface DasamshhaCareerResult {
  d10_ascendant: string
  planets: D10PlanetRecord[]
  career_indicators: CareerIndicator[]
}

// ── D10 position parser ────────────────────────────────────────────────────────

/**
 * Parse D10 positions from the platform primitive response.
 * The divisional_query tool returns a ToolBundle with results[].content as JSON strings.
 */
export function parseD10Positions(
  envelope: Record<string, unknown>,
): Array<{ planet: string; sign: string; house: number }> {
  const result = envelope['result'] as Record<string, unknown> | undefined
  if (!result) return []

  // Shape 1: ToolBundle.results[].content (standard divisional_query response)
  const bundleResults = result['results'] as Array<{ content: string }> | undefined
  if (Array.isArray(bundleResults) && bundleResults.length > 0) {
    const positions: Array<{ planet: string; sign: string; house: number }> = []
    for (const r of bundleResults) {
      try {
        const parsed = JSON.parse(r.content) as Record<string, unknown>
        const planet = extractField(parsed, 'planet')
        const sign = extractSign(parsed)
        const house = extractHouse(parsed)
        if (planet && sign) {
          positions.push({ planet, sign, house: house ?? 1 })
        }
      } catch {
        // skip malformed content
      }
    }
    return positions
  }

  // Shape 2: direct rows_by_category
  const rows = result['rows_by_category'] as Record<string, unknown> | undefined
  if (rows) {
    const allRows = Object.values(rows).flat() as Array<Record<string, unknown>>
    return allRows
      .map(r => ({
        planet: extractField(r, 'planet') ?? '',
        sign: extractSign(r) ?? '',
        house: extractHouse(r) ?? 1,
      }))
      .filter(r => r.planet && r.sign)
  }

  return []
}

function extractField(obj: Record<string, unknown>, field: string): string | null {
  if (typeof obj[field] === 'string') return obj[field] as string
  const placement = obj['placement'] as Record<string, unknown> | undefined
  if (placement && typeof placement[field] === 'string') return placement[field] as string
  const vj = obj['value_json'] as Record<string, unknown> | undefined
  if (vj && typeof vj[field] === 'string') return vj[field] as string
  return null
}

function extractSign(obj: Record<string, unknown>): string | null {
  const direct = extractField(obj, 'sign')
  if (direct) return direct
  // Fallback: "Planet in Sign" pattern in value_text
  if (typeof obj['value_text'] === 'string') {
    const match = /\bin\s+([A-Z][a-z]+)\b/.exec(obj['value_text'] as string)
    if (match) return match[1] ?? null
  }
  return null
}

function extractHouse(obj: Record<string, unknown>): number | null {
  if (typeof obj['house'] === 'number') return obj['house']
  const placement = obj['placement'] as Record<string, unknown> | undefined
  if (placement && typeof placement['house'] === 'number') return placement['house']
  const vj = obj['value_json'] as Record<string, unknown> | undefined
  if (vj && typeof vj['house'] === 'number') return vj['house']
  return null
}

// ── Dignity classifier ─────────────────────────────────────────────────────────

export function classifyDignity(planet: string, sign: string): string {
  if (EXALTATION_SIGNS[planet] === sign) return 'exalted'
  if (OWN_SIGNS[planet]?.includes(sign)) return 'own_sign'
  return 'neutral'
}

// ── Career indicator engine ────────────────────────────────────────────────────

/**
 * Given D10 planet positions and the D10 ascendant sign, apply classical
 * career indicator rules and return indicator records.
 */
export function computeCareerIndicators(
  positions: Array<{ planet: string; sign: string; house: number }>,
  ascSign: string,
): CareerIndicator[] {
  const indicators: CareerIndicator[] = []

  const tenth10H = tenthSignFrom(ascSign)
  const tenthLord = CORRECTED_TENTH_LORD[ascSign as SignName] ?? null

  // Rule A: 10H lord identified → record as strong career indicator
  if (tenthLord) {
    const lordPos = positions.find(p => p.planet === tenthLord)
    if (lordPos) {
      const houseDesc = `placed in ${lordPos.house}H D10`
      const rule = `${tenthLord} as 10L (10H = ${tenth10H}) ${houseDesc} — ${
        KENDRA_HOUSES.has(lordPos.house) || TRIKONA_HOUSES.has(lordPos.house)
          ? 'kendra/trikona placement: strong career directional energy'
          : DUSTHANA_HOUSES.has(lordPos.house)
          ? 'dusthana placement: career obstacles or hidden work'
          : 'neutral house placement'
      }`
      indicators.push({
        indicator: '10H lord in D10',
        planet: tenthLord,
        classical_rule: rule,
      })

      // Rule C: 10H lord in own sign or exalted
      const dignity = classifyDignity(tenthLord, lordPos.sign)
      if (dignity === 'own_sign' || dignity === 'exalted') {
        indicators.push({
          indicator: '10H lord in own sign or exalted',
          planet: tenthLord,
          classical_rule: `${tenthLord} in ${lordPos.sign} (${dignity}) in D10 — very favourable for career realisation`,
        })
      }

      // Rule C extended: 10H lord in kendra/trikona
      if (KENDRA_HOUSES.has(lordPos.house) || TRIKONA_HOUSES.has(lordPos.house)) {
        if (dignity !== 'own_sign' && dignity !== 'exalted') {
          indicators.push({
            indicator: '10H lord in kendra/trikona',
            planet: tenthLord,
            classical_rule: `${tenthLord} as 10L in ${lordPos.house}H (kendra/trikona) D10 — favourable career trajectory`,
          })
        }
      }

      // Rule D: 10H lord in dusthana
      if (DUSTHANA_HOUSES.has(lordPos.house)) {
        indicators.push({
          indicator: '10H lord in dusthana (6H/8H/12H)',
          planet: tenthLord,
          classical_rule: `${tenthLord} as 10L in ${lordPos.house}H D10 — career obstacles, hidden effort, or interruption likely`,
        })
      }
    }
  }

  // Rule B: Sun/Saturn/Mercury in D10 10H
  for (const pos of positions) {
    if (CAREER_SIGNIFICATORS.has(pos.planet) && pos.house === 10) {
      indicators.push({
        indicator: 'Career significator in D10 10H',
        planet: pos.planet,
        classical_rule: `${pos.planet} in 10H of D10 — direct career strength; ${pos.planet} significates authority/discipline/intellect in career`,
      })
    }
  }

  return indicators
}

// ── Core assembly function ─────────────────────────────────────────────────────

/**
 * Assemble the full DasamshhaCareerResult from raw D10 positions.
 */
export function assembleDasamshhaResult(
  positions: Array<{ planet: string; sign: string; house: number }>,
): DasamshhaCareerResult {
  // Ascendant sign = sign of house 1
  const ascRow = positions.find(p => p.house === 1)
  const d10Ascendant = ascRow?.sign ?? (positions[0]?.sign ?? 'Unknown')

  const planets: D10PlanetRecord[] = positions.map(pos => ({
    planet: pos.planet,
    sign: pos.sign,
    house: pos.house,
    dignity: classifyDignity(pos.planet, pos.sign),
  }))

  const careerIndicators = computeCareerIndicators(positions, d10Ascendant)

  return {
    d10_ascendant: d10Ascendant,
    planets,
    career_indicators: careerIndicators,
  }
}

// ── Zod schema ─────────────────────────────────────────────────────────────────

const QueryDasamshhaCareerInputSchema = z.object({
  chart_id: z.string().optional().describe(
    "Chart UUID. Defaults to the native's chart (362f9f17-95a5-490b-a5a7-027d3e0efda0)."
  ),
  tier: z.string().optional().default('super_admin').describe(
    'Audience tier. Defaults to "super_admin".'
  ),
})

type QueryDasamshhaCareerInput = z.infer<typeof QueryDasamshhaCareerInputSchema>

// ── Tool description ───────────────────────────────────────────────────────────

const QUERY_DASAMSHA_CAREER_DESCRIPTION =
  'D10 (Dasamsha) career analysis. Fetches planet positions in the D10 divisional chart ' +
  'and overlays classical Parashari career-indicator rules: ' +
  '(1) 10H lord placement in D10 — kendra/trikona = strong; dusthana = obstacles; ' +
  '(2) 10H lord in own sign or exaltation = very favourable; ' +
  '(3) Sun, Saturn, Mercury in D10 10H = direct career strength. ' +
  'Returns d10_ascendant, planet placements with dignity, and career_indicators array. ' +
  'Use for questions about profession, public status, career trajectory, or vocational aptitude.'

// ── Registration ───────────────────────────────────────────────────────────────

export function registerQueryDasamshhaCareer(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_dasamsha_career',
    QUERY_DASAMSHA_CAREER_DESCRIPTION,
    QueryDasamshhaCareerInputSchema.shape,
    async (args: QueryDasamshhaCareerInput) => {
      const principal = getPrincipal()
      const chartId = args.chart_id ?? NATIVE_CHART_ID

      // Step 1: Fetch D10 positions from divisional_query
      const { status, envelope } = await callPlatformPrimitive(
        'divisional_query',
        {
          chart_id: chartId,
          varga: 'D10',
        },
        principal
      )

      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Step 2: Parse D10 positions
      const positions = parseD10Positions(envelope as unknown as Record<string, unknown>)

      // Step 3: Assemble career result
      const careerResult = assembleDasamshhaResult(positions)

      // Step 4: Return enriched result
      return okResult({
        ok: true,
        trace_id: (envelope as unknown as Record<string, unknown>)['trace_id'] ?? null,
        result: careerResult,
        epistemics: {
          surgical: true,
          confidence_band: 'high',
          horizon_days: null,
          falsifier: 'D10 position mismatch with FORENSIC v8.0',
          data_source: 'divisional_query:D10',
        },
        meta: {
          chart_id: chartId,
          division: 'D10',
          planets_found: positions.length,
          computation: 'classical_career_indicators_parashari',
        },
      })
    }
  )
}
