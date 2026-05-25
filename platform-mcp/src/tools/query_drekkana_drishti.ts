/**
 * query_drekkana_drishti.ts — MCP Tier 3 surgical primitive: Jaimini Drekkana Drishti.
 *
 * What it does:
 *   1. Fetches D3 (Drekkana) chart positions via query_divisional_chart({division:"D3"}).
 *   2. Classifies each sign as moveable / fixed / dual.
 *   3. Applies Jaimini Drekkana Drishti rules to compute which signs each planet aspects.
 *   4. Reports aspect targets with planet occupancy and aspect strength.
 *
 * Jaimini Drekkana Drishti rules:
 *   Moveable signs (Aries, Cancer, Libra, Capricorn): aspect ALL signs EXCEPT the
 *     two adjacent signs (2nd and 12th from them).
 *   Fixed signs (Taurus, Leo, Scorpio, Aquarius): aspect all OTHER fixed signs.
 *   Dual signs (Gemini, Virgo, Sagittarius, Pisces): aspect all OTHER dual signs.
 *
 * Output shape:
 *   {
 *     planets: [{
 *       planet, drekkana_sign, drekkana_house, sign_type,
 *       drishti_targets: [{ sign, planet_in_sign, aspect_strength }]
 *     }],
 *     mutual_drekkana_drishti: [{ planet_a, planet_b, sign_a, sign_b }]
 *   }
 *
 * TR-P7-S1: New tool. Registered in server.ts.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

// ── Constants ──────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

/** Canonical sign list in zodiacal order (1-indexed by position+1). */
export const SIGNS = [
  'Aries',       // 1  — moveable
  'Taurus',      // 2  — fixed
  'Gemini',      // 3  — dual
  'Cancer',      // 4  — moveable
  'Leo',         // 5  — fixed
  'Virgo',       // 6  — dual
  'Libra',       // 7  — moveable
  'Scorpio',     // 8  — fixed
  'Sagittarius', // 9  — dual
  'Capricorn',   // 10 — moveable
  'Aquarius',    // 11 — fixed
  'Pisces',      // 12 — dual
] as const

export type SignName = typeof SIGNS[number]

export type SignType = 'moveable' | 'fixed' | 'dual'

/** Map each sign to its Jaimini sign-type category. */
export const SIGN_TYPE_MAP: Record<SignName, SignType> = {
  Aries: 'moveable',
  Taurus: 'fixed',
  Gemini: 'dual',
  Cancer: 'moveable',
  Leo: 'fixed',
  Virgo: 'dual',
  Libra: 'moveable',
  Scorpio: 'fixed',
  Sagittarius: 'dual',
  Capricorn: 'moveable',
  Aquarius: 'fixed',
  Pisces: 'dual',
}

// ── Drishti computation engine ─────────────────────────────────────────────────

/**
 * Return the 1-based zodiacal index for a sign (1=Aries … 12=Pisces).
 * Returns 0 for unknown sign names.
 */
export function signIndex(sign: string): number {
  const idx = SIGNS.indexOf(sign as SignName)
  return idx < 0 ? 0 : idx + 1
}

/**
 * Return the sign name for a 1-based zodiacal index.
 * Handles wrap-around via modulo.
 */
export function signFromIndex(idx: number): SignName {
  // Normalize to 1-12 range
  const normalized = ((idx - 1 + 120) % 12) + 1
  return SIGNS[normalized - 1]!
}

/**
 * Given a sign, return the set of signs it aspects under Jaimini Drekkana Drishti.
 *
 * Moveable: aspects all 12 signs EXCEPT the 2nd and 12th from itself.
 * Fixed:    aspects all OTHER fixed signs (3 total).
 * Dual:     aspects all OTHER dual signs (3 total).
 */
export function computeDrekkanaAspects(sign: string): SignName[] {
  const type = SIGN_TYPE_MAP[sign as SignName]
  if (!type) return []

  if (type === 'moveable') {
    const idx = signIndex(sign)
    if (idx === 0) return []
    const excluded = new Set<string>([
      signFromIndex(idx + 1),  // 2nd from
      signFromIndex(idx - 1),  // 12th from
      sign,                    // itself
    ])
    return SIGNS.filter(s => !excluded.has(s))
  }

  if (type === 'fixed') {
    return SIGNS.filter(s => SIGN_TYPE_MAP[s] === 'fixed' && s !== sign)
  }

  if (type === 'dual') {
    return SIGNS.filter(s => SIGN_TYPE_MAP[s] === 'dual' && s !== sign)
  }

  return []
}

// ── Result types ───────────────────────────────────────────────────────────────

export interface DrishtiTarget {
  sign: SignName
  planet_in_sign: string | null
  aspect_strength: number
}

export interface PlanetDrekkanaRecord {
  planet: string
  drekkana_sign: SignName
  drekkana_house: number
  sign_type: SignType
  drishti_targets: DrishtiTarget[]
}

export interface MutualDrekkana {
  planet_a: string
  planet_b: string
  sign_a: SignName
  sign_b: SignName
}

export interface DrekkanaResult {
  planets: PlanetDrekkanaRecord[]
  mutual_drekkana_drishti: MutualDrekkana[]
}

// ── D3 position parser ─────────────────────────────────────────────────────────

/**
 * Parse D3 positions from the platform primitive response.
 * The divisional_query tool returns a ToolBundle with results[].content as JSON strings.
 * Each content item may carry { planet, sign, house, varga } or similar shapes.
 */
export function parseD3Positions(
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
        const planet = extractPlanet(parsed)
        const sign = extractSign(parsed)
        const house = extractHouse(parsed)
        if (planet && sign) {
          positions.push({ planet, sign, house: house ?? signIndex(sign) })
        }
      } catch {
        // skip malformed content
      }
    }
    return positions
  }

  // Shape 2: direct rows_by_category (some endpoints return this)
  const rows = (result['rows_by_category'] as Record<string, unknown> | undefined)
  if (rows) {
    const allRows = Object.values(rows).flat() as Array<Record<string, unknown>>
    return allRows
      .map(r => ({
        planet: extractPlanet(r) ?? '',
        sign: extractSign(r) ?? '',
        house: extractHouse(r) ?? 0,
      }))
      .filter(r => r.planet && r.sign)
  }

  return []
}

function extractPlanet(obj: Record<string, unknown>): string | null {
  if (typeof obj['planet'] === 'string') return obj['planet']
  // Check nested placement
  const placement = obj['placement'] as Record<string, unknown> | undefined
  if (placement && typeof placement['planet'] === 'string') return placement['planet']
  // value_json may carry planet
  const vj = obj['value_json'] as Record<string, unknown> | undefined
  if (vj && typeof vj['planet'] === 'string') return vj['planet']
  return null
}

function extractSign(obj: Record<string, unknown>): string | null {
  if (typeof obj['sign'] === 'string') return obj['sign']
  const placement = obj['placement'] as Record<string, unknown> | undefined
  if (placement && typeof placement['sign'] === 'string') return placement['sign']
  const vj = obj['value_json'] as Record<string, unknown> | undefined
  if (vj && typeof vj['sign'] === 'string') return vj['sign']
  // value_text may carry "Planet in Sign" phrasing
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

// ── Core computation ───────────────────────────────────────────────────────────

/**
 * Compute Jaimini Drekkana Drishti for a list of D3 planet positions.
 */
export function computeDrekkanaResults(
  positions: Array<{ planet: string; sign: string; house: number }>,
): DrekkanaResult {
  // Build sign → planet lookup (first planet in sign wins if multiple)
  const signToPlanet = new Map<string, string>()
  for (const pos of positions) {
    if (!signToPlanet.has(pos.sign)) {
      signToPlanet.set(pos.sign, pos.planet)
    }
  }

  const planets: PlanetDrekkanaRecord[] = positions.map(pos => {
    const drekkanaSign = pos.sign as SignName
    const signType = SIGN_TYPE_MAP[drekkanaSign] ?? 'moveable'
    const aspects = computeDrekkanaAspects(drekkanaSign)
    const drishtiTargets: DrishtiTarget[] = aspects.map(targetSign => ({
      sign: targetSign,
      planet_in_sign: signToPlanet.get(targetSign) ?? null,
      aspect_strength: 1.0,
    }))

    return {
      planet: pos.planet,
      drekkana_sign: drekkanaSign,
      drekkana_house: pos.house,
      sign_type: signType,
      drishti_targets: drishtiTargets,
    }
  })

  // Mutual drishti: planet A aspects sign of planet B AND planet B aspects sign of planet A
  const mutual: MutualDrekkana[] = []
  for (let i = 0; i < planets.length; i++) {
    for (let j = i + 1; j < planets.length; j++) {
      const a = planets[i]!
      const b = planets[j]!
      const aAspectsB = a.drishti_targets.some(t => t.sign === b.drekkana_sign)
      const bAspectsA = b.drishti_targets.some(t => t.sign === a.drekkana_sign)
      if (aAspectsB && bAspectsA) {
        mutual.push({
          planet_a: a.planet,
          planet_b: b.planet,
          sign_a: a.drekkana_sign,
          sign_b: b.drekkana_sign,
        })
      }
    }
  }

  return { planets, mutual_drekkana_drishti: mutual }
}

// ── Tool description ───────────────────────────────────────────────────────────

const QUERY_DREKKANA_DRISHTI_DESCRIPTION =
  'Jaimini Drekkana Drishti — D3 (Drekkana) chart position lookup and special aspect computation. ' +
  'Fetches planet positions in the D3 divisional chart, classifies each sign as moveable/fixed/dual, ' +
  'and computes Jaimini-style aspect targets per Drekkana Drishti rules: ' +
  'moveable signs aspect all signs except the 2nd and 12th from them; ' +
  'fixed signs aspect all other fixed signs; dual signs aspect all other dual signs. ' +
  'Returns planets with their D3 placement, sign type, and aspect targets (with planet occupancy). ' +
  'Also reports mutual Drekkana Drishti pairs. ' +
  'Use for questions about siblings, courage, co-borns (D3 significations) with Jaimini aspect overlay.'

// ── Zod schema ─────────────────────────────────────────────────────────────────

const QueryDrekkanaInputSchema = z.object({
  chart_id: z.string().optional().describe(
    "Chart UUID. Defaults to the native's chart (362f9f17-95a5-490b-a5a7-027d3e0efda0)."
  ),
  tier: z.string().optional().default('super_admin').describe(
    'Audience tier. Defaults to "super_admin".'
  ),
})

type QueryDrekkanaInput = z.infer<typeof QueryDrekkanaInputSchema>

// ── Registration ───────────────────────────────────────────────────────────────

export function registerQueryDrekkanaDisthi(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_drekkana_drishti',
    QUERY_DREKKANA_DRISHTI_DESCRIPTION,
    QueryDrekkanaInputSchema.shape,
    async (args: QueryDrekkanaInput) => {
      const principal = getPrincipal()
      const chartId = args.chart_id ?? NATIVE_CHART_ID

      // Step 1: Fetch D3 positions from divisional_query
      const { status, envelope } = await callPlatformPrimitive(
        'divisional_query',
        {
          chart_id: chartId,
          varga: 'D3',
        },
        principal
      )

      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Step 2: Parse D3 positions from the response
      const positions = parseD3Positions(envelope as unknown as Record<string, unknown>)

      // Step 3: Compute Drekkana Drishti
      const drekkanaResult = computeDrekkanaResults(positions)

      // Step 4: Return enriched result
      return okResult({
        ok: true,
        trace_id: (envelope as unknown as Record<string, unknown>)['trace_id'] ?? null,
        result: drekkanaResult,
        epistemics: {
          surgical: true,
          confidence_band: 'high',
          horizon_days: null,
          falsifier: 'D3 position mismatch with FORENSIC v8.0',
          data_source: 'divisional_query:D3',
        },
        meta: {
          chart_id: chartId,
          division: 'D3',
          planets_found: positions.length,
          computation: 'jaimini_drekkana_drishti_in_process',
        },
      })
    }
  )
}
