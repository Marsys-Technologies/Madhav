/**
 * MARSYS-JIS Retrieval tool — query_dasamsha_career (UDA-1-S5)
 *
 * D10 (Dasamsha) career analysis. Fetches planet positions in the D10
 * divisional chart and overlays classical Parashari career-indicator rules:
 *   (1) 10H lord placement in D10 — kendra/trikona = strong; dusthana = obstacles
 *   (2) 10H lord in own sign or exaltation = very favourable
 *   (3) Sun, Saturn, Mercury in D10 10H = direct career strength
 *
 * Returns d10_ascendant, planet placements with dignity, and career_indicators array.
 *
 * Ported from: platform-mcp/src/tools/query_dasamsha_career.ts
 * Session: UDA-1-S5
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool as divisionalQueryTool } from './divisional_query'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_dasamsha_career'
const TOOL_VERSION = '1.0.0'

// ── Constants ──────────────────────────────────────────────────────────────────

/** Canonical sign list in zodiacal order. */
const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

type SignName = typeof SIGNS[number]

/** 10H lord by D10 ascendant sign (corrected Parashari lordships). */
const CORRECTED_TENTH_LORD: Record<SignName, string> = {
  Aries:       'Saturn',   // 10H = Capricorn → Saturn
  Taurus:      'Saturn',   // 10H = Aquarius → Saturn
  Gemini:      'Jupiter',  // 10H = Pisces → Jupiter (corrected from Mars)
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

/** 10H sign name from D10 ascendant sign (0-based: 10th sign = asc + 9). */
function tenthSignFrom(ascSign: string): string {
  const idx = SIGNS.indexOf(ascSign as SignName)
  if (idx < 0) return 'Unknown'
  return SIGNS[(idx + 9) % 12]!
}

/** Own-sign map per planet. */
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

/** Career-significator planets whose presence in D10 10H is classical career strength. */
const CAREER_SIGNIFICATORS = new Set(['Sun', 'Saturn', 'Mercury'])

// ── Input type ────────────────────────────────────────────────────────────────

export interface QueryDasamshhaCareerInput {
  /** Chart UUID. Optional; omit to use the canonical native chart. */
  chart_id?: string
}

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

// ── Dignity classifier ─────────────────────────────────────────────────────────

function classifyDignity(planet: string, sign: string): string {
  if (EXALTATION_SIGNS[planet] === sign) return 'exalted'
  if (OWN_SIGNS[planet]?.includes(sign)) return 'own_sign'
  return 'neutral'
}

// ── D10 position extractor (from ToolBundle results) ───────────────────────────

function extractD10Positions(
  bundle: ToolBundle,
): Array<{ planet: string; sign: string; house: number }> {
  const positions: Array<{ planet: string; sign: string; house: number }> = []

  for (const r of bundle.results) {
    try {
      const parsed = JSON.parse(r.content) as Record<string, unknown>
      const planet = extractStringField(parsed, 'planet')
      const sign = extractSign(parsed)
      const house = extractNumber(parsed, 'house')
      if (planet && sign) {
        positions.push({ planet, sign, house: house ?? 1 })
      }
    } catch {
      // skip malformed content
    }
  }

  return positions
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
  if (typeof obj['value_text'] === 'string') {
    const match = /\bin\s+([A-Z][a-z]+)\b/.exec(obj['value_text'] as string)
    if (match) return match[1] ?? null
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

// ── Career indicator engine ────────────────────────────────────────────────────

function computeCareerIndicators(
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

      // Rule C extended: 10H lord in kendra/trikona (only when not own/exalted)
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

// ── Core assembly ──────────────────────────────────────────────────────────────

function assembleDasamshhaResult(
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

// ── Synthetic QueryPlan factory ───────────────────────────────────────────────

function makeSyntheticPlan(): QueryPlan {
  return {
    query_plan_id: crypto.randomUUID(),
    query_text: 'D10 dasamsha career analysis',
    query_class: 'factual',
    domains: ['career', 'divisional'],
    forward_looking: false,
    audience_tier: 'acharya_reviewer',
    tools_authorized: ['divisional_query'],
    history_mode: 'research',
    panel_mode: false,
    expected_output_shape: 'structured_data',
    manifest_fingerprint: 'synthetic',
    schema_version: '1.0',
  }
}

// ── Core retrieval ────────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'FORENSIC',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as unknown as QueryDasamshhaCareerInput

  // Step 1: Fetch D10 positions via divisional_query
  const syntheticPlan = makeSyntheticPlan()
  const d10Bundle = await divisionalQueryTool.retrieve(syntheticPlan, {
    varga: 'D10',
    ...(input.chart_id ? { chart_id: input.chart_id } : {}),
  })

  // Step 2: Extract positions from the bundle
  const positions = extractD10Positions(d10Bundle)

  // Step 3: Assemble career result
  const careerResult = assembleDasamshhaResult(positions)

  // Step 4: Build ToolBundle result
  const resultContent = JSON.stringify({
    ok: true,
    result: careerResult,
    epistemics: {
      surgical: true,
      confidence_band: 'high',
      horizon_days: null,
      falsifier: 'D10 position mismatch with FORENSIC v8.0',
      data_source: 'divisional_query:D10',
    },
    meta: {
      division: 'D10',
      planets_found: positions.length,
      computation: 'classical_career_indicators_parashari',
    },
  })

  const results: ToolBundleResult[] = [{
    content: resultContent,
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 0.9,
    significance: 1.0,
  }]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: params ?? {},
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: (params ?? {}) as Record<string, unknown>,
    status: 'success',
    rows_returned: results.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'FORENSIC',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'D10 (Dasamsha) career analysis. Fetches planet positions in the D10 divisional chart ' +
    'and overlays classical Parashari career-indicator rules: ' +
    '(1) 10H lord placement in D10 — kendra/trikona = strong; dusthana = obstacles; ' +
    '(2) 10H lord in own sign or exaltation = very favourable; ' +
    '(3) Sun, Saturn, Mercury in D10 10H = direct career strength. ' +
    'Returns d10_ascendant, planet placements with dignity, and career_indicators array. ' +
    'Use for questions about profession, public status, career trajectory, or vocational aptitude.',
  retrieve,
}
