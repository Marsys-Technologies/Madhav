/**
 * MARSYS-JIS Retrieval tool — query_yogas_active_now (UDA-1-S1)
 *
 * Portal port of the MCP query_yogas_active_now surgical primitive.
 * Evaluates which natal yogas are currently activated by the running
 * Vimshottari dasha (MD/AD).
 *
 * Algorithm:
 *   1. Query chart_facts with category='yoga' to get natal yoga rows.
 *   2. Query chart_facts dasha_vimshottari with active_only to get current MD/AD.
 *   3. For each yoga row, extract key planets and compare against MD/AD.
 *   4. Classify: active (MD or AD match), latent (partial/secondary), dormant (none).
 *   5. Apply status_filter if provided.
 *
 * Source: platform-mcp/src/tools/query_yogas_active_now.ts (TR-P6-S2)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_yogas_active_now'
const TOOL_VERSION = '1.0.0'

// ── Input interface ───────────────────────────────────────────────────────────

export interface QueryYogasActiveNowInput {
  /** ISO date for dasha evaluation (YYYY-MM-DD). Default: today. */
  date?: string
  /** Filter returned yogas by activation status. Default: 'all'. */
  status_filter?: 'active' | 'latent' | 'dormant' | 'all'
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface YogaResult {
  yoga_id: string | null
  yoga_name: string
  status: 'active' | 'latent' | 'dormant'
  activation_reason: string
  key_planets: string[]
  dasha_match: boolean
}

interface DashaContext {
  md: string | null
  ad: string | null
  pd: string | null
}

interface ChartFactsRow {
  fact_id: string
  category: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Extract a string value from a row object, trying multiple field name aliases.
 */
function extractString(row: Record<string, unknown>, ...fields: string[]): string | null {
  for (const f of fields) {
    const val = row[f]
    if (typeof val === 'string' && val.trim()) return val.trim()
  }
  return null
}

/**
 * Extract yoga rows from chart_facts results.
 */
function extractYogaRows(rows: ChartFactsRow[]): ChartFactsRow[] {
  return rows.filter(r => r.category === 'yoga')
}

/**
 * Extract key planet names from a yoga row's value_json.
 */
function extractKeyPlanets(vj: Record<string, unknown> | null): string[] {
  if (!vj) return []
  const planets: string[] = []

  // Single-value planet fields
  for (const field of ['planet', 'lord', 'significator', 'primary_planet']) {
    const val = vj[field]
    if (typeof val === 'string' && val.trim()) {
      planets.push(val.trim())
    }
  }

  // Array or comma-separated multi-planet fields
  for (const field of ['planets_involved', 'planets', 'grahas']) {
    const val = vj[field]
    if (Array.isArray(val)) {
      for (const v of val) {
        if (typeof v === 'string' && v.trim()) planets.push(v.trim())
      }
    } else if (typeof val === 'string' && val.trim()) {
      for (const p of val.split(/[,/]+/)) {
        const trimmed = p.trim()
        if (trimmed) planets.push(trimmed)
      }
    }
  }

  // Deduplicate (case-preserving — keep first occurrence)
  const seen = new Set<string>()
  return planets.filter(p => {
    const lower = p.toLowerCase()
    if (seen.has(lower)) return false
    seen.add(lower)
    return true
  })
}

/**
 * Normalise a planet name to lowercase for comparison.
 */
function normalizePlanet(name: string): string {
  return name.toLowerCase().trim()
}

/**
 * Check whether a yoga planet name matches a dasha lord.
 * Handles common aliases (Rahu = north node, Ketu = south node, etc.).
 */
function planetMatchesDasha(yogaPlanet: string, dashaLord: string | null): boolean {
  if (!dashaLord) return false
  const yp = normalizePlanet(yogaPlanet)
  const dl = normalizePlanet(dashaLord)
  if (yp === dl) return true

  const aliases: Record<string, string[]> = {
    rahu: ['north node', 'ascending node'],
    ketu: ['south node', 'descending node'],
    asc: ['ascendant', 'lagna'],
  }
  const yAliases = aliases[yp] ?? []
  const dAliases = aliases[dl] ?? []
  return yAliases.includes(dl) || dAliases.includes(yp)
}

/**
 * Classify a yoga's activation status against the current dasha context.
 */
function classifyYoga(
  keyPlanets: string[],
  dashaCtx: DashaContext | null,
): { status: 'active' | 'latent' | 'dormant'; activation_reason: string; dasha_match: boolean } {
  if (!dashaCtx || (dashaCtx.md === null && dashaCtx.ad === null)) {
    return {
      status: 'dormant',
      activation_reason: 'No dasha context available; classified dormant by default.',
      dasha_match: false,
    }
  }

  const mdMatches = keyPlanets.filter(p => planetMatchesDasha(p, dashaCtx.md))
  const adMatches = keyPlanets.filter(p => planetMatchesDasha(p, dashaCtx.ad))

  if (mdMatches.length > 0 && adMatches.length > 0) {
    return {
      status: 'active',
      activation_reason:
        `Active: key planet(s) [${mdMatches.join(', ')}] match MD (${dashaCtx.md}) ` +
        `and [${adMatches.join(', ')}] match AD (${dashaCtx.ad}). Double-dasha activation.`,
      dasha_match: true,
    }
  }

  if (mdMatches.length > 0) {
    return {
      status: 'active',
      activation_reason:
        `Active: key planet(s) [${mdMatches.join(', ')}] match MD (${dashaCtx.md}).`,
      dasha_match: true,
    }
  }

  if (adMatches.length > 0) {
    return {
      status: 'active',
      activation_reason:
        `Active: key planet(s) [${adMatches.join(', ')}] match AD (${dashaCtx.ad}).`,
      dasha_match: true,
    }
  }

  if (keyPlanets.length > 0) {
    const mdStr = dashaCtx.md ?? 'unknown'
    const adStr = dashaCtx.ad ?? 'unknown'
    return {
      status: 'latent',
      activation_reason:
        `Latent: key planet(s) [${keyPlanets.join(', ')}] do not match current MD (${mdStr}) ` +
        `or AD (${adStr}). Yoga exists natally but is not dasha-triggered at this time.`,
      dasha_match: false,
    }
  }

  return {
    status: 'dormant',
    activation_reason:
      'Dormant: no key planets could be extracted from this yoga row to compare against dasha.',
    dasha_match: false,
  }
}

// ── Retrieve function ─────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  const input = (params ?? {}) as QueryYogasActiveNowInput

  const evaluationDate = input.date ?? new Date().toISOString().slice(0, 10)
  const statusFilter = input.status_filter ?? 'all'

  const storage = getStorageClient()

  // ── Step 1: Fetch natal yoga rows from chart_facts ────────────────────────

  const yogaResult = await storage.query<ChartFactsRow>(
    `SELECT fact_id, category, value_text, value_number, value_json
     FROM chart_facts
     WHERE is_stale = false
       AND category = 'yoga'
     ORDER BY fact_id
     LIMIT 200`,
    [],
  )

  const yogaRows = extractYogaRows(yogaResult.rows)

  // ── Step 2: Fetch current dasha (MD/AD) from chart_facts ─────────────────

  let dashaContext: DashaContext | null = null

  const dashaResult = await storage.query<ChartFactsRow>(
    `SELECT fact_id, category, value_text, value_number, value_json
     FROM chart_facts
     WHERE is_stale = false
       AND category = 'dasha_vimshottari'
       AND (value_json->>'start_date')::date <= $1::date
       AND (value_json->>'end_date')::date > $1::date
     ORDER BY (value_json->>'start_date')::date DESC
     LIMIT 5`,
    [evaluationDate],
  )

  if (dashaResult.rows.length > 0) {
    const row = dashaResult.rows[0]!
    const vj = row.value_json ?? {}
    dashaContext = {
      md: extractString(vj, 'md_lord', 'mahadasha', 'md', 'maha_dasha') ?? null,
      ad: extractString(vj, 'ad_lord', 'antardasha', 'ad', 'antar_dasha', 'bhukti') ?? null,
      pd: extractString(vj, 'pd_lord', 'pratyantar', 'pd', 'pratyantar_dasha', 'pratyantardasha') ?? null,
    }
  }
  // If dasha lookup fails: dashaContext remains null → all yogas become dormant

  // ── Step 3: Classify each yoga ───────────────────────────────────────────

  const allYogas: YogaResult[] = []

  for (const row of yogaRows) {
    const vj = row.value_json ?? {}

    const yogaName =
      extractString(vj, 'yoga_name', 'name', 'value_text', 'title') ??
      extractString(vj, 'yoga_type', 'category_detail', 'description') ??
      (row.value_text ? row.value_text.trim() : null) ??
      'Unknown Yoga'

    const yogaId = extractString(vj, 'fact_id', 'yoga_id', 'id') ?? row.fact_id ?? null

    const keyPlanets = extractKeyPlanets(vj)
    const { status, activation_reason, dasha_match } = classifyYoga(keyPlanets, dashaContext)

    allYogas.push({
      yoga_id: yogaId,
      yoga_name: yogaName,
      status,
      activation_reason,
      key_planets: keyPlanets,
      dasha_match,
    })
  }

  // ── Step 4: Apply status_filter ──────────────────────────────────────────

  const filteredYogas =
    statusFilter === 'all'
      ? allYogas
      : allYogas.filter(y => y.status === statusFilter)

  const activeCount = allYogas.filter(y => y.status === 'active').length

  const payload = {
    ok: true,
    evaluation_date: evaluationDate,
    dasha_context: dashaContext,
    yogas: filteredYogas,
    total_yogas: allYogas.length,
    active_count: activeCount,
    epistemics: { surgical: true },
  }

  const content = JSON.stringify(payload)

  const results: ToolBundleResult[] = [{
    content,
    source_canonical_id: 'CHART_FACTS',
    source_version: '1.0',
    confidence: 0.85,
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
    params_json: input as Record<string, unknown>,
    status: allYogas.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: filteredYogas.length,
    latency_ms: Date.now() - start,
    token_estimate: Math.ceil(content.length / 4),
    data_asset_id: 'CHART_FACTS',
    error_code: null,
    served_from_cache: false,
    fallback_used: dashaContext === null,
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
    'Evaluates natal yoga activation status against the current Vimshottari dasha (MD/AD). ' +
    'Returns each yoga classified as "active" (key planet matches MD or AD), ' +
    '"latent" (planets exist but no dasha match), or "dormant" (no key planets or no dasha). ' +
    'Reads yoga rows from chart_facts and active dasha from dasha_vimshottari. ' +
    'Use for "which yogas are triggered by my current dasha?". ' +
    'Prefer holistic_bundle when synthesised interpretation is needed. ' +
    'Prefer chart_facts_query with category "yoga" for raw yoga rows without activation scoring.',
  retrieve,
}
