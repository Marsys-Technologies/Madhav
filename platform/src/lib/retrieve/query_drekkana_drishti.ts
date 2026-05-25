/**
 * MARSYS-JIS Retrieval tool — query_drekkana_drishti (UDA-1-S7)
 *
 * Jaimini Drekkana Drishti — D3 (Drekkana) chart position lookup and special
 * aspect computation.
 *
 * Algorithm:
 *   1. Fetches planet positions in D3 divisional chart via divisional_query.
 *   2. Classifies each sign as moveable / fixed / dual.
 *   3. Applies Jaimini Drekkana Drishti rules:
 *      - Moveable signs: aspect ALL signs EXCEPT 2nd and 12th from them.
 *      - Fixed signs: aspect all OTHER fixed signs.
 *      - Dual signs: aspect all OTHER dual signs.
 *   4. Returns per-planet drekkana sign, sign type, drishti targets, mutual aspects.
 *
 * Ported from: platform-mcp/src/tools/query_drekkana_drishti.ts (TR-P7-S1)
 * Session: UDA-1-S7
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool as divisionalQueryTool } from './divisional_query'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_drekkana_drishti'
const TOOL_VERSION = '1.0.0'

// ── Constants ──────────────────────────────────────────────────────────────────

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

// ── Input interface ────────────────────────────────────────────────────────────

export interface QueryDrekkanaDisthi {
  chart_id?: string
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

// ── D3 position extractor (from ToolBundle results) ───────────────────────────

function extractD3Positions(
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
        positions.push({ planet, sign, house: house ?? signIndex(sign) })
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

// ── Synthetic QueryPlan factory ───────────────────────────────────────────────

function makeSyntheticPlan(): QueryPlan {
  return {
    query_plan_id: crypto.randomUUID(),
    query_text: 'D3 drekkana drishti analysis',
    query_class: 'factual',
    domains: ['divisional', 'jaimini'],
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
  const input = (params ?? {}) as unknown as QueryDrekkanaDisthi

  // Step 1: Fetch D3 positions via divisional_query
  const syntheticPlan = makeSyntheticPlan()
  const d3Bundle = await divisionalQueryTool.retrieve(syntheticPlan, {
    varga: 'D3',
    ...(input.chart_id ? { chart_id: input.chart_id } : {}),
  })

  // Step 2: Extract positions from the bundle
  const positions = extractD3Positions(d3Bundle)

  // Step 3: Compute Drekkana Drishti
  const drekkanaResult = computeDrekkanaResults(positions)

  // Step 4: Build ToolBundle result
  const resultContent = JSON.stringify({
    ok: true,
    result: drekkanaResult,
    epistemics: {
      surgical: true,
      confidence_band: 'high',
      horizon_days: null,
      falsifier: 'D3 position mismatch with FORENSIC v8.0',
      data_source: 'divisional_query:D3',
    },
    meta: {
      division: 'D3',
      planets_found: positions.length,
      computation: 'jaimini_drekkana_drishti_in_process',
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
    'Jaimini Drekkana Drishti — D3 (Drekkana) chart position lookup and special aspect computation. ' +
    'Fetches planet positions in the D3 divisional chart, classifies each sign as moveable/fixed/dual, ' +
    'and computes Jaimini-style aspect targets per Drekkana Drishti rules: ' +
    'moveable signs aspect all signs except the 2nd and 12th from them; ' +
    'fixed signs aspect all other fixed signs; dual signs aspect all other dual signs. ' +
    'Returns planets with their D3 placement, sign type, and aspect targets (with planet occupancy). ' +
    'Also reports mutual Drekkana Drishti pairs. ' +
    'Use for questions about siblings, courage, co-borns (D3 significations) with Jaimini aspect overlay.',
  retrieve,
}
