/**
 * query_shashtiamsha.ts — MCP Tier 3 surgical primitive: D60 (Shashtiamsha) karma analysis.
 *
 * What it does:
 *   1. Fetches D60 (Shashtiamsha) chart positions via divisional_query({varga:"D60"}).
 *   2. Maps each planet's D60 position to a classical pada name + interpretation.
 *
 * The D60 is the finest divisional chart — each sign is divided into 60 padas of 0.5° each.
 * Padas cycle through 12 classical names (Ghora, Rakshasa, Deva, …, Purishaka) repeating
 * 5 times across the 60 padas.
 *
 * Pada number calculation:
 *   pada = Math.ceil((longitude_in_sign % 30) / 0.5)
 *   At 0°, pada = 1.
 *
 * Output shape:
 *   { planets: [{ planet, d60_sign, d60_house, d60_longitude_in_sign,
 *                 d60_pada_number, d60_pada_name, d60_interpretation }] }
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

// ── D60 Pada name cycle (1–12, cycling) ──────────────────────────────────────

/**
 * The 12 classical Shashtiamsha pada names with their interpretations.
 * Padas 1–12 map directly; padas 13–60 cycle back through this list.
 * Cycle: pada N → PADA_NAMES[((N - 1) % 12) + 1]
 */
export const D60_PADA_NAMES: Record<number, { name: string; interpretation: string }> = {
  1:  { name: 'Ghora',     interpretation: 'Malefic; past-life violence or harsh karma' },
  2:  { name: 'Rakshasa',  interpretation: 'Demonic; indicates past-life cruelty' },
  3:  { name: 'Deva',      interpretation: 'Divine; past-life merit and piety' },
  4:  { name: 'Kubera',    interpretation: 'Wealth deity; past-life generosity' },
  5:  { name: 'Yaksha',    interpretation: 'Semi-divine; past-life association with nature spirits' },
  6:  { name: 'Kinnara',   interpretation: 'Celestial musician; artistic past-life' },
  7:  { name: 'Bhrashta',  interpretation: 'Fallen; past-life ethical violations' },
  8:  { name: 'Kulaghna',  interpretation: 'Family destroyer; past-life betrayal' },
  9:  { name: 'Garuda',    interpretation: 'Eagle deity; past-life spiritual aspiration' },
  10: { name: 'Agni',      interpretation: 'Fire deity; transformative past-life experiences' },
  11: { name: 'Maya',      interpretation: 'Illusion; past-life deception' },
  12: { name: 'Purishaka', interpretation: 'Impure; difficult past-life associations' },
}

// ── Pada lookup ────────────────────────────────────────────────────────────────

/**
 * Given a raw pada number (1–60), return the cycling pada entry (1–12).
 * Pada 13 → 1 (Ghora), pada 14 → 2 (Rakshasa), etc.
 */
export function resolvePadaEntry(padaNumber: number): { name: string; interpretation: string } {
  // Clamp to valid range
  const clamped = Math.max(1, Math.min(60, padaNumber))
  // Cycle to 1–12 using 1-based modulo
  const cycledIndex = ((clamped - 1) % 12) + 1
  return D60_PADA_NAMES[cycledIndex]!
}

/**
 * Calculate the D60 pada number for a planet at a given longitude within its sign.
 *
 * Each pada = 0.5°; 60 padas × 0.5° = 30° (one full sign).
 * Formula: Math.ceil(longitude_in_sign / 0.5)
 * At 0°, pada = 1 (special case).
 *
 * @param longitudeInSign — planet's longitude within sign, 0–30 (exclusive)
 */
export function calculatePada(longitudeInSign: number): number {
  if (longitudeInSign <= 0) return 1
  const pada = Math.ceil(longitudeInSign / 0.5)
  return Math.max(1, Math.min(60, pada))
}

// ── Result types ───────────────────────────────────────────────────────────────

export interface D60PlanetRecord {
  planet: string
  d60_sign: string
  d60_house: number
  d60_longitude_in_sign: number
  d60_pada_number: number
  d60_pada_name: string
  d60_interpretation: string
}

export interface ShashtiamshaResult {
  planets: D60PlanetRecord[]
}

// ── D60 position parser ────────────────────────────────────────────────────────

/**
 * Parse D60 positions from the platform primitive response.
 * The divisional_query tool returns a ToolBundle with results[].content as JSON strings.
 */
export function parseD60Positions(
  envelope: Record<string, unknown>,
): Array<{ planet: string; sign: string; house: number; longitude_in_sign: number }> {
  const result = envelope['result'] as Record<string, unknown> | undefined
  if (!result) return []

  // Shape 1: ToolBundle.results[].content (standard divisional_query response)
  const bundleResults = result['results'] as Array<{ content: string }> | undefined
  if (Array.isArray(bundleResults) && bundleResults.length > 0) {
    const positions: Array<{ planet: string; sign: string; house: number; longitude_in_sign: number }> = []
    for (const r of bundleResults) {
      try {
        const parsed = JSON.parse(r.content) as Record<string, unknown>
        const planet = extractStringField(parsed, 'planet')
        const sign = extractSign(parsed)
        const house = extractNumber(parsed, 'house')
        const longitude = extractNumber(parsed, 'longitude_in_sign') ?? extractNumber(parsed, 'longitude') ?? 0
        if (planet && sign) {
          positions.push({
            planet,
            sign,
            house: house ?? 1,
            longitude_in_sign: longitude,
          })
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
        planet: extractStringField(r, 'planet') ?? '',
        sign: extractSign(r) ?? '',
        house: extractNumber(r, 'house') ?? 1,
        longitude_in_sign: extractNumber(r, 'longitude_in_sign') ?? 0,
      }))
      .filter(r => r.planet && r.sign)
  }

  return []
}

function extractStringField(obj: Record<string, unknown>, field: string): string | null {
  if (typeof obj[field] === 'string') return obj[field] as string
  const placement = obj['placement'] as Record<string, unknown> | undefined
  if (placement && typeof placement[field] === 'string') return placement[field] as string
  const vj = obj['value_json'] as Record<string, unknown> | undefined
  if (vj && typeof vj[field] === 'string') return vj[field] as string
  return null
}

function extractSign(obj: Record<string, unknown>): string | null {
  const direct = extractStringField(obj, 'sign')
  if (direct) return direct
  // Fallback: "Planet in Sign" pattern in value_text
  if (typeof obj['value_text'] === 'string') {
    const match = /\bin\s+([A-Z][a-z]+)\b/.exec(obj['value_text'] as string)
    if (match) return match[1]
  }
  return null
}

function extractNumber(obj: Record<string, unknown>, field: string): number | null {
  if (typeof obj[field] === 'number') return obj[field] as number
  const placement = obj['placement'] as Record<string, unknown> | undefined
  if (placement && typeof placement[field] === 'number') return placement[field] as number
  const vj = obj['value_json'] as Record<string, unknown> | undefined
  if (vj && typeof vj[field] === 'number') return vj[field] as number
  return null
}

// ── Core assembly function ─────────────────────────────────────────────────────

/**
 * Assemble the full ShashtiamshaResult from raw D60 positions.
 */
export function assembleShashtiamshaResult(
  positions: Array<{ planet: string; sign: string; house: number; longitude_in_sign: number }>,
): ShashtiamshaResult {
  const planets: D60PlanetRecord[] = positions.map(pos => {
    const padaNumber = calculatePada(pos.longitude_in_sign)
    const padaEntry = resolvePadaEntry(padaNumber)

    return {
      planet: pos.planet,
      d60_sign: pos.sign,
      d60_house: pos.house,
      d60_longitude_in_sign: pos.longitude_in_sign,
      d60_pada_number: padaNumber,
      d60_pada_name: padaEntry.name,
      d60_interpretation: padaEntry.interpretation,
    }
  })

  return { planets }
}

// ── Zod schema ─────────────────────────────────────────────────────────────────

const QueryShashtiamshaInputSchema = z.object({
  chart_id: z.string().optional().describe(
    "Chart UUID. Defaults to the native's chart (362f9f17-95a5-490b-a5a7-027d3e0efda0)."
  ),
  tier: z.string().optional().default('super_admin').describe(
    'Audience tier. Defaults to "super_admin".'
  ),
})

type QueryShashtiamshaInput = z.infer<typeof QueryShashtiamshaInputSchema>

// ── Tool description ───────────────────────────────────────────────────────────

const QUERY_SHASHTIAMSHA_DESCRIPTION =
  'D60 (Shashtiamsha) karma analysis — the finest divisional chart in Jyotish. ' +
  'Fetches planet positions in the D60 chart and maps each to its classical pada name ' +
  'and past-life karma interpretation. ' +
  'Each sign is divided into 60 padas of 0.5° each; pada names cycle through 12 classical ' +
  'names (Ghora=malefic karma, Rakshasa=cruelty, Deva=merit, Kubera=generosity, ' +
  'Yaksha=nature spirits, Kinnara=artistic, Bhrashta=ethical violations, ' +
  'Kulaghna=betrayal, Garuda=spiritual aspiration, Agni=transformation, ' +
  'Maya=deception, Purishaka=difficult associations). ' +
  'Returns planets with d60_sign, d60_house, d60_longitude_in_sign, d60_pada_number, ' +
  'd60_pada_name, d60_interpretation. ' +
  'Use for questions about past-life karma, soul-level patterns, or deeply hidden chart signatures.'

// ── Registration ───────────────────────────────────────────────────────────────

export function registerQueryShashtiamsha(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_shashtiamsha',
    QUERY_SHASHTIAMSHA_DESCRIPTION,
    QueryShashtiamshaInputSchema.shape,
    async (args: QueryShashtiamshaInput) => {
      const principal = getPrincipal()
      const chartId = args.chart_id ?? NATIVE_CHART_ID

      // Step 1: Fetch D60 positions from divisional_query
      const { status, envelope } = await callPlatformPrimitive(
        'divisional_query',
        {
          chart_id: chartId,
          varga: 'D60',
        },
        principal
      )

      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Step 2: Parse D60 positions
      const positions = parseD60Positions(envelope as Record<string, unknown>)

      // Step 3: Assemble shashtiamsha result
      const shashtiamshaResult = assembleShashtiamshaResult(positions)

      // Step 4: Return enriched result
      return okResult({
        ok: true,
        trace_id: (envelope as Record<string, unknown>)['trace_id'] ?? null,
        result: shashtiamshaResult,
        epistemics: {
          surgical: true,
          confidence_band: 'medium',
          horizon_days: null,
          falsifier: 'D60 position mismatch with FORENSIC v8.0 or longitude_in_sign imprecision',
          data_source: 'divisional_query:D60',
          note: 'D60 pada requires sub-degree longitude precision; positions from DB may carry rounding',
        },
        meta: {
          chart_id: chartId,
          division: 'D60',
          planets_found: positions.length,
          computation: 'classical_shashtiamsha_pada_cycle',
          pada_size_degrees: 0.5,
          total_padas: 60,
          pada_cycle_length: 12,
        },
      })
    }
  )
}
