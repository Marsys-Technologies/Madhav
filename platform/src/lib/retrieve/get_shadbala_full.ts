/**
 * MARSYS-JIS Retrieval tool — get_shadbala_full (UDA-1-S2)
 *
 * Portal port of the MCP get_shadbala_full surgical primitive.
 * Queries chart_facts for all shadbala component rows, groups them into the
 * six canonical Shadbala components per planet, sums each component, and
 * returns total virupa + rupa with sufficiency assessment against classical minimums.
 *
 * Six Shadbala components:
 *   1. Sthana Bala    — positional strength (uchcha, saptvarga, ojayugma, kendradi, drekkana)
 *   2. Dig Bala       — directional strength
 *   3. Kala Bala      — temporal strength (natonnata, paksha, tribhaga, varsha, masa, dina, hora, ayana, yuddha)
 *   4. Cheshta Bala   — motional strength
 *   5. Naisargika Bala — natural strength
 *   6. Drig Bala      — aspectual strength
 *
 * Classical minimum rupas (Parashari):
 *   Sun: 6.5, Moon: 6.0, Mars: 5.0, Mercury: 7.0, Jupiter: 6.5, Venus: 5.5, Saturn: 5.0
 *
 * Source: platform-mcp/src/tools/get_shadbala_full.ts (TR-P6-S3)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'get_shadbala_full'
const TOOL_VERSION = '1.0.0'

// ── Classical minimum rupas ───────────────────────────────────────────────────

export const MINIMUM_RUPAS: Record<string, number> = {
  Sun: 6.5,
  Moon: 6.0,
  Mars: 5.0,
  Mercury: 7.0,
  Jupiter: 6.5,
  Venus: 5.5,
  Saturn: 5.0,
}

const CLASSICAL_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] as const
type ClassicalPlanet = typeof CLASSICAL_PLANETS[number]

// ── Input interface ───────────────────────────────────────────────────────────

export interface GetShadbalaFullInput {
  /**
   * Optional filter: array of classical planet names to include in the output.
   * Omit to return all 7 classical planets.
   * Valid values: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn.
   */
  planets?: ClassicalPlanet[]
}

// ── Component interfaces ──────────────────────────────────────────────────────

interface ShadbalaComponents {
  sthana_bala: number
  dig_bala: number
  kala_bala: number
  cheshta_bala: number
  naisargika_bala: number
  drig_bala: number
}

interface ShadbalaEntry extends ShadbalaComponents {
  total_virupa: number
  total_rupa: number
  minimum_required_rupa: number
  is_sufficient: boolean
}

// ── DB row interface ──────────────────────────────────────────────────────────

interface ChartFactsRow {
  fact_id: string
  category: string
  planet: string | null
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  sub_category: string | null
  label: string | null
  component_name: string | null
}

// ── Component grouping via regex ──────────────────────────────────────────────

function classifyComponent(componentName: string): keyof ShadbalaComponents | null {
  if (/sthana|uchcha|saptvarga|ojayugma|kendradi|drekkana/i.test(componentName)) return 'sthana_bala'
  // Dig Bala: match "dig" as a standalone word segment (not inside "drig"/"drishti")
  if (/(?<![r])dig(?![r])/i.test(componentName)) return 'dig_bala'
  if (/kala|natonnata|paksha|tribhaga|varsha|masa|dina|(?<![d])hora(?![\w])|ayana|yuddha/i.test(componentName)) return 'kala_bala'
  if (/cheshta/i.test(componentName)) return 'cheshta_bala'
  if (/naisargika|sahaj/i.test(componentName)) return 'naisargika_bala'
  if (/drig|drishti/i.test(componentName)) return 'drig_bala'
  return null
}

// ── Retrieve function ─────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  const input = (params ?? {}) as GetShadbalaFullInput

  const planetFilter = input.planets && input.planets.length > 0 ? input.planets : null

  const storage = getStorageClient()

  // ── Step 1: Fetch all shadbala rows from chart_facts ─────────────────────

  const shadResult = await storage.query<ChartFactsRow>(
    `SELECT fact_id, category, planet, value_text, value_number, value_json,
            value_json->>'sub_category' AS sub_category,
            value_json->>'label' AS label,
            value_json->>'component_name' AS component_name
     FROM chart_facts
     WHERE is_stale = false
       AND category = 'shadbala'
     ORDER BY planet, fact_id
     LIMIT 300`,
    [],
  )

  const sourceRowsUsed = shadResult.rows.length

  // ── Step 2: Group rows by planet, classify components ────────────────────

  const planetMap: Record<string, ShadbalaComponents> = {}

  for (const row of shadResult.rows) {
    const planet = row.planet
    if (!planet) continue

    // Apply planet filter
    const planetList = planetFilter ?? (CLASSICAL_PLANETS as readonly string[])
    if (!(planetList as string[]).includes(planet)) continue

    if (!planetMap[planet]) {
      planetMap[planet] = {
        sthana_bala: 0,
        dig_bala: 0,
        kala_bala: 0,
        cheshta_bala: 0,
        naisargika_bala: 0,
        drig_bala: 0,
      }
    }

    // Resolve component name from multiple possible columns
    const componentName =
      (row.component_name) ??
      (row.label) ??
      (row.sub_category) ??
      (typeof row.value_json?.['component_name'] === 'string'
        ? (row.value_json['component_name'] as string)
        : undefined) ??
      (typeof row.value_json?.['sub_category'] === 'string'
        ? (row.value_json['sub_category'] as string)
        : undefined) ??
      (typeof row.value_json?.['label'] === 'string'
        ? (row.value_json['label'] as string)
        : undefined) ??
      (row.value_text ?? '')

    const valueNum =
      typeof row.value_number === 'number'
        ? row.value_number
        : typeof row.value_json?.['value_num'] === 'number'
        ? (row.value_json['value_num'] as number)
        : typeof row.value_json?.['virupa'] === 'number'
        ? (row.value_json['virupa'] as number)
        : 0

    const group = classifyComponent(componentName)
    if (group) {
      planetMap[planet][group] += valueNum
    }
  }

  // ── Step 3: Build output with rupa + sufficiency assessment ──────────────

  const shadbala: Record<string, ShadbalaEntry> = {}

  const planetsToReport: readonly string[] = planetFilter ?? CLASSICAL_PLANETS

  for (const planet of planetsToReport) {
    const components = planetMap[planet] ?? {
      sthana_bala: 0,
      dig_bala: 0,
      kala_bala: 0,
      cheshta_bala: 0,
      naisargika_bala: 0,
      drig_bala: 0,
    }

    const totalVirupa =
      components.sthana_bala +
      components.dig_bala +
      components.kala_bala +
      components.cheshta_bala +
      components.naisargika_bala +
      components.drig_bala

    const totalRupa = totalVirupa / 60
    const minimumRupa = MINIMUM_RUPAS[planet] ?? 5.0
    const isSufficient = totalRupa >= minimumRupa

    shadbala[planet] = {
      ...components,
      total_virupa: totalVirupa,
      total_rupa: totalRupa,
      minimum_required_rupa: minimumRupa,
      is_sufficient: isSufficient,
    }
  }

  const payload = {
    ok: true,
    shadbala,
    source_rows_used: sourceRowsUsed,
    epistemics: { surgical: true },
  }

  const content = JSON.stringify(payload)

  const results: ToolBundleResult[] = [{
    content,
    source_canonical_id: 'CHART_FACTS',
    source_version: '1.0',
    confidence: 0.9,
    significance: 0.85,
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
    params_json: input as Record<string, unknown>,
    status: sourceRowsUsed === 0 ? 'zero_rows' : 'ok',
    rows_returned: sourceRowsUsed,
    latency_ms: Date.now() - start,
    token_estimate: Math.ceil(content.length / 4),
    data_asset_id: 'CHART_FACTS',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
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

// ── Export ────────────────────────────────────────────────────────────────────

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Fetches all shadbala component rows from chart_facts and rolls them up into ' +
    'the six canonical Shadbala groups (Sthana, Dig, Kala, Cheshta, Naisargika, Drig Bala) per planet. ' +
    'Returns total virupa, total rupa (virupa / 60), classical minimum required rupa, and is_sufficient flag. ' +
    'Classical minimums: Sun 6.5, Moon 6.0, Mars 5.0, Mercury 7.0, Jupiter 6.5, Venus 5.5, Saturn 5.0 rupas. ' +
    'Use for "Is Saturn shadbala-sufficient?" or "What is Jupiter\'s total Shadbala?". ' +
    'Prefer chart_facts_query with category "shadbala" for raw rows. ' +
    'Prefer holistic_bundle when strength in interpretive context is needed.',
  retrieve,
}
