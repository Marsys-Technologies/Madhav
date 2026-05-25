/**
 * MARSYS-JIS Retrieval tool — query_shashtiamsha (UDA-1-S5)
 *
 * D60 (Shashtiamsha) karma analysis — the finest divisional chart in Jyotish.
 * Fetches planet positions in the D60 chart and maps each to its classical
 * pada name and past-life karma interpretation.
 *
 * Each sign is divided into 60 padas of 0.5° each. Pada names cycle through
 * 12 classical names (Ghora, Rakshasa, Deva, Kubera, Yaksha, Kinnara,
 * Bhrashta, Kulaghna, Garuda, Agni, Maya, Purishaka).
 *
 * Pada number: Math.ceil(longitude_in_sign / 0.5); at 0°, pada = 1.
 * Cycle: pada N → D60_PADA_NAMES[((N-1) % 12) + 1]
 *
 * Ported from: platform-mcp/src/tools/query_shashtiamsha.ts
 * Session: UDA-1-S5
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool as divisionalQueryTool } from './divisional_query'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_shashtiamsha'
const TOOL_VERSION = '1.0.0'

// ── D60 Pada name cycle (1–12, cycling) ──────────────────────────────────────

/**
 * The 12 classical Shashtiamsha pada names with their interpretations.
 * Padas 1–12 map directly; padas 13–60 cycle back through this list.
 */
const D60_PADA_NAMES: Record<number, { name: string; interpretation: string }> = {
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
function resolvePadaEntry(padaNumber: number): { name: string; interpretation: string } {
  const clamped = Math.max(1, Math.min(60, padaNumber))
  const cycledIndex = ((clamped - 1) % 12) + 1
  return D60_PADA_NAMES[cycledIndex]!
}

/**
 * Calculate the D60 pada number for a planet at a given longitude within its sign.
 * Each pada = 0.5°; 60 padas × 0.5° = 30° (one full sign).
 * At 0°, pada = 1.
 */
function calculatePada(longitudeInSign: number): number {
  if (longitudeInSign <= 0) return 1
  const pada = Math.ceil(longitudeInSign / 0.5)
  return Math.max(1, Math.min(60, pada))
}

// ── Input type ────────────────────────────────────────────────────────────────

export interface QueryShashtiamshaInput {
  /** Chart UUID. Optional; omit to use the canonical native chart. */
  chart_id?: string
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

// ── D60 position extractor (from ToolBundle results) ───────────────────────────

function extractD60Positions(
  bundle: ToolBundle,
): Array<{ planet: string; sign: string; house: number; longitude_in_sign: number }> {
  const positions: Array<{ planet: string; sign: string; house: number; longitude_in_sign: number }> = []

  for (const r of bundle.results) {
    try {
      const parsed = JSON.parse(r.content) as Record<string, unknown>
      const planet = extractStringField(parsed, 'planet')
      const sign = extractSign(parsed)
      const house = extractNumber(parsed, 'house')
      const longitude =
        extractNumber(parsed, 'longitude_in_sign') ??
        extractNumber(parsed, 'longitude') ??
        0
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

// ── Core assembly ──────────────────────────────────────────────────────────────

function assembleShashtiamshaResult(
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

// ── Synthetic QueryPlan factory ───────────────────────────────────────────────

function makeSyntheticPlan(): QueryPlan {
  return {
    query_plan_id: crypto.randomUUID(),
    query_text: 'D60 shashtiamsha karma pada analysis',
    query_class: 'factual',
    domains: ['karma', 'divisional'],
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
  const input = (params ?? {}) as unknown as QueryShashtiamshaInput

  // Step 1: Fetch D60 positions via divisional_query
  const syntheticPlan = makeSyntheticPlan()
  const d60Bundle = await divisionalQueryTool.retrieve(syntheticPlan, {
    varga: 'D60',
    ...(input.chart_id ? { chart_id: input.chart_id } : {}),
  })

  // Step 2: Extract positions from the bundle
  const positions = extractD60Positions(d60Bundle)

  // Step 3: Assemble shashtiamsha result
  const shashtiamshaResult = assembleShashtiamshaResult(positions)

  // Step 4: Build ToolBundle result
  const resultContent = JSON.stringify({
    ok: true,
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
      division: 'D60',
      planets_found: positions.length,
      computation: 'classical_shashtiamsha_pada_cycle',
      pada_size_degrees: 0.5,
      total_padas: 60,
      pada_cycle_length: 12,
    },
  })

  const results: ToolBundleResult[] = [{
    content: resultContent,
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 0.8,
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
    'Use for questions about past-life karma, soul-level patterns, or deeply hidden chart signatures.',
  retrieve,
}
