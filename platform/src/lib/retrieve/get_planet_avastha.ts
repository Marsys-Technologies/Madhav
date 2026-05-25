/**
 * MARSYS-JIS Retrieval tool — get_planet_avastha (UDA-1-S2)
 *
 * Portal port of the MCP get_planet_avastha surgical primitive.
 * Returns the avastha (planetary state/condition) for a specific planet
 * from the chart_facts table, plus classical meaning string.
 *
 * Six Parashari avasthas:
 *   Lajjita (Ashamed), Garvita (Proud), Kshudita (Hungry),
 *   Trushita (Thirsty), Mudita (Delighted), Kshobhita (Agitated).
 *
 * Fallback chain:
 *   1. chart_facts category "avastha" — direct row lookup for the planet.
 *   2. chart_facts category "dignity_scores" — infer avastha from dignity classification.
 *   3. Default to "Mudita" (neutral-positive) with source "default_fallback".
 *
 * Source: platform-mcp/src/tools/get_planet_avastha.ts (TR-P6-S3)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'get_planet_avastha'
const TOOL_VERSION = '1.0.0'

// ── Avastha meaning map ───────────────────────────────────────────────────────

export const AVASTHA_MEANINGS: Record<string, string> = {
  Lajjita: 'Ashamed — planet is suppressed; significations delayed or frustrated',
  Garvita: 'Proud — planet is strong; significations fulfilled',
  Kshudita: 'Hungry — planet lacks support; results delayed',
  Trushita: 'Thirsty — planet craves what it lacks; creates longing',
  Mudita: 'Delighted — planet is comfortable; benevolent results',
  Kshobhita: 'Agitated — planet is disturbed; volatile results',
}

const VALID_AVASTHAS = Object.keys(AVASTHA_MEANINGS)

// ── Dignity → avastha inference map ──────────────────────────────────────────

const DIGNITY_TO_AVASTHA: Record<string, string> = {
  exalted: 'Garvita',
  own_sign: 'Mudita',
  great_friend: 'Mudita',
  friend: 'Mudita',
  neutral: 'Mudita',
  enemy: 'Kshudita',
  great_enemy: 'Kshudita',
  debilitated: 'Lajjita',
}

// ── Valid planets ─────────────────────────────────────────────────────────────

const VALID_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] as const

// ── Input interface ───────────────────────────────────────────────────────────

export interface GetPlanetAvasthaInput {
  /** The graha to look up. One of the nine classical planets. */
  planet: typeof VALID_PLANETS[number]
  /**
   * When true (default), returns natal chart avastha.
   * Reserved for future transit-avastha mode; currently only natal is supported.
   */
  use_natal?: boolean
}

// ── DB row interface ──────────────────────────────────────────────────────────

interface ChartFactsRow {
  fact_id: string
  category: string
  planet: string | null
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
}

// ── Retrieve function ─────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  const input = (params ?? {}) as unknown as GetPlanetAvasthaInput

  const planet = input.planet
  const useNatal = input.use_natal !== false // default true

  const storage = getStorageClient()

  let usedFallback = false
  let source: 'chart_facts' | 'computed' | 'default_fallback' = 'chart_facts'
  let avastha = 'Mudita'

  // ── Step 1: Query chart_facts for avastha category ────────────────────────

  const avasthaResult = await storage.query<ChartFactsRow>(
    `SELECT fact_id, category, planet, value_text, value_number, value_json
     FROM chart_facts
     WHERE is_stale = false
       AND category = 'avastha'
       AND LOWER(planet) = LOWER($1)
     LIMIT 10`,
    [planet],
  )

  const avasthaRow = avasthaResult.rows[0] ?? null

  if (avasthaRow) {
    // Extract avastha from the row — try value_text first, then value_json fields
    const rawAvastha =
      avasthaRow.value_text?.trim() ??
      (typeof avasthaRow.value_json?.['avastha'] === 'string'
        ? (avasthaRow.value_json['avastha'] as string).trim()
        : undefined) ??
      (typeof avasthaRow.value_json?.['value'] === 'string'
        ? (avasthaRow.value_json['value'] as string).trim()
        : undefined) ??
      ''

    // Normalise to capitalised form matching AVASTHA_MEANINGS keys
    const matched = VALID_AVASTHAS.find(
      (a) => a.toLowerCase() === rawAvastha.toLowerCase(),
    )
    avastha = matched ?? (rawAvastha || 'Mudita')
    source = 'chart_facts'
  } else {
    // ── Step 2: Fallback — dignity_scores inference ──────────────────────────
    const dignityResult = await storage.query<ChartFactsRow>(
      `SELECT fact_id, category, planet, value_text, value_number, value_json
       FROM chart_facts
       WHERE is_stale = false
         AND category = 'dignity_scores'
         AND LOWER(planet) = LOWER($1)
       LIMIT 10`,
      [planet],
    )

    const dignityRow = dignityResult.rows[0] ?? null

    if (dignityRow) {
      const dignityClass =
        dignityRow.value_text?.trim().toLowerCase() ??
        (typeof dignityRow.value_json?.['dignity'] === 'string'
          ? (dignityRow.value_json['dignity'] as string).toLowerCase().trim()
          : undefined) ??
        (typeof dignityRow.value_json?.['classification'] === 'string'
          ? (dignityRow.value_json['classification'] as string).toLowerCase().trim()
          : undefined) ??
        ''

      const inferredAvastha = DIGNITY_TO_AVASTHA[dignityClass] ?? 'Mudita'
      avastha = inferredAvastha
      source = 'computed'
      usedFallback = true
    } else {
      // ── Step 3: Default fallback ─────────────────────────────────────────
      avastha = 'Mudita'
      source = 'default_fallback'
      usedFallback = true
    }
  }

  const avasthaMeaning = AVASTHA_MEANINGS[avastha] ?? `Unknown avastha: ${avastha}`

  const payload = {
    ok: true,
    planet,
    avastha,
    avastha_meaning: avasthaMeaning,
    is_natal: useNatal,
    source,
    epistemics: { surgical: true },
  }

  const content = JSON.stringify(payload)

  const results: ToolBundleResult[] = [{
    content,
    source_canonical_id: 'CHART_FACTS',
    source_version: '1.0',
    confidence: source === 'chart_facts' ? 0.95 : source === 'computed' ? 0.75 : 0.5,
    significance: 0.8,
  }]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(content.slice(0, 200))
      .digest('hex')

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as unknown as Record<string, unknown>,
    status: 'ok',
    rows_returned: 1,
    latency_ms: Date.now() - start,
    token_estimate: Math.ceil(content.length / 4),
    data_asset_id: 'CHART_FACTS',
    error_code: null,
    served_from_cache: false,
    fallback_used: usedFallback,
  })

  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: input as unknown as object,
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }
}

// ── Export ────────────────────────────────────────────────name────────────────

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Returns the avastha (planetary state) for a specific graha from chart_facts. ' +
    'Avasthas classify a planet\'s experiential condition: Lajjita (Ashamed/suppressed), ' +
    'Garvita (Proud/strong), Kshudita (Hungry/lacking), Trushita (Thirsty/craving), ' +
    'Mudita (Delighted/comfortable), Kshobhita (Agitated/disturbed). ' +
    'Fallback chain: (1) avastha category direct lookup → (2) dignity_scores inference → ' +
    '(3) default "Mudita". ' +
    'Use for "What is Jupiter\'s avastha?" or "Is Venus agitated?". ' +
    'Prefer holistic_bundle when interpretation in context is needed.',
  retrieve,
}
