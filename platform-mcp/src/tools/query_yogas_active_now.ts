/**
 * query_yogas_active_now.ts — MCP Tier 3 surgical primitive: yoga activation status.
 *
 * What it does: Evaluates which natal yogas are currently activated by the
 * running Vimshottari dasha. For each yoga row from chart_facts (category=yoga),
 * checks whether any key planet (planet, lord, significator, planets_involved,
 * primary_planet) matches the active Mahadasha (MD) or Antardasha (AD) planet.
 * Classifies each yoga as "active", "latent" (partial match), or "dormant"
 * (no dasha match) and returns the full classified list with activation reasons.
 *
 * Algorithm:
 *   1. Call query_chart_facts with categories:["yoga"] to get natal yoga rows.
 *   2. Call query_dasha_periods with active_only:true to get current MD/AD/PD.
 *   3. For each yoga row, extract key planets and compare against MD/AD planet.
 *   4. Classify: active (MD or AD match), latent (partial/secondary match), dormant (none).
 *   5. Apply status_filter if provided.
 *
 * When to prefer: Use for "which yogas are active now?" or "what yogas are
 * triggered by my current dasha?". Prefer holistic_bundle when you need
 * synthesised interpretation of the yogas in context of the whole chart.
 * Prefer query_chart_facts with category:"yoga" for raw yoga rows without activation scoring.
 *
 * TR-P6-S2: new MCP tool.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_YOGAS_ACTIVE_NOW_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Evaluates natal yoga activation status against the current Vimshottari ' +
    'dasha (MD/AD). Returns each yoga classified as "active" (key planet matches MD or AD), ' +
    '"latent" (partial planet overlap), or "dormant" (no dasha match), with activation reasons.',
  whenToPrefer:
    'Use for "which yogas are triggered by my current dasha?" without full synthesis. ' +
    'Prefer holistic_bundle when synthesised interpretation of active yogas in chart context is needed. ' +
    'Prefer query_chart_facts with category "yoga" for raw yoga rows without activation scoring.',
})

// ── Zod schema ────────────────────────────────────────────────────────────────

const QueryYogasActiveNowInputSchema = z.object({
  date: z.string().optional().describe(
    'ISO date for dasha evaluation (YYYY-MM-DD). Default: today.'
  ),
  status_filter: z.enum(['active', 'latent', 'dormant', 'all']).optional().default('all').describe(
    'Filter returned yogas by activation status. Default: "all" returns all yogas.'
  ),
})

type QueryYogasActiveNowInput = z.infer<typeof QueryYogasActiveNowInputSchema>

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

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Unwrap ToolBundle envelope returned by callPlatformPrimitive.
 * Returns parsed inner data from results[0].content, or the result object directly.
 */
function unwrapEnvelope(envelope: Record<string, unknown>): unknown {
  const result = envelope['result']
  if (!result || typeof result !== 'object') return null
  const resultObj = result as Record<string, unknown>

  // ToolBundle pattern: result.results[0].content (JSON string)
  const bundleResults = resultObj['results'] as Array<{ content: unknown }> | undefined
  if (bundleResults && bundleResults.length > 0) {
    const raw = bundleResults[0].content
    if (typeof raw === 'string') {
      try { return JSON.parse(raw) } catch { /* fall through */ }
    }
    if (raw !== null && raw !== undefined) return raw
  }

  // Direct result object
  return resultObj
}

/**
 * Extract yoga rows from chart_facts response data.
 * Supports both direct rows array and rows_by_category batched response.
 */
function extractYogaRows(data: unknown): unknown[] {
  if (!data || typeof data !== 'object') return []
  const d = data as Record<string, unknown>

  // Direct rows array
  if (Array.isArray(d['rows'])) return d['rows']

  // Batched rows_by_category
  const rbc = d['rows_by_category'] as Record<string, unknown[]> | undefined
  if (rbc) {
    if (Array.isArray(rbc['yoga'])) return rbc['yoga']
  }

  return []
}

/**
 * Extract key planet names from a yoga row.
 * Inspects multiple possible field names used across different yoga row formats.
 */
function extractKeyPlanets(row: Record<string, unknown>): string[] {
  const planets: string[] = []

  // Single-value planet fields
  for (const field of ['planet', 'lord', 'significator', 'primary_planet']) {
    const val = row[field]
    if (typeof val === 'string' && val.trim()) {
      planets.push(val.trim())
    }
  }

  // Array or comma-separated multi-planet fields
  for (const field of ['planets_involved', 'planets', 'grahas']) {
    const val = row[field]
    if (Array.isArray(val)) {
      for (const v of val) {
        if (typeof v === 'string' && v.trim()) planets.push(v.trim())
      }
    } else if (typeof val === 'string' && val.trim()) {
      // Comma or slash separated
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
 * Extract a string value from a row, trying multiple field name aliases.
 */
function extractString(row: Record<string, unknown>, ...fields: string[]): string | null {
  for (const f of fields) {
    const val = row[f]
    if (typeof val === 'string' && val.trim()) return val.trim()
  }
  return null
}

/**
 * Parse dasha context (MD/AD/PD) from query_dasha_periods response.
 * The platform returns periods[] with mahadasha/antardasha/pratyantar fields.
 */
function extractDashaContext(data: unknown): DashaContext | null {
  if (!data || typeof data !== 'object') return null
  const d = data as Record<string, unknown>

  // Try periods array (structured dasha response)
  const periods = d['periods'] as unknown[] | undefined
  if (!Array.isArray(periods) || periods.length === 0) {
    // Try rows array (raw chart_facts dasha row shape)
    const rows = d['rows'] as unknown[] | undefined
    if (!Array.isArray(rows) || rows.length === 0) return null
    const row = rows[0] as Record<string, unknown>
    return {
      md: extractString(row, 'mahadasha', 'md', 'maha_dasha') ?? null,
      ad: extractString(row, 'antardasha', 'ad', 'antar_dasha', 'bhukti') ?? null,
      pd: extractString(row, 'pratyantar', 'pd', 'pratyantar_dasha', 'pratyantardasha') ?? null,
    }
  }

  const period = periods[0] as Record<string, unknown>
  return {
    md: extractString(period, 'mahadasha', 'md', 'maha_dasha') ?? null,
    ad: extractString(period, 'antardasha', 'ad', 'antar_dasha', 'bhukti') ?? null,
    pd: extractString(period, 'pratyantar', 'pd', 'pratyantar_dasha', 'pratyantardasha') ?? null,
  }
}

/**
 * Normalise a planet name to lowercase for case-insensitive comparison.
 */
function normalizePlanet(name: string): string {
  return name.toLowerCase().trim()
}

/**
 * Check whether a planet name from the yoga matches a dasha lord name.
 * Handles common aliases (e.g. "Rahu" vs "North Node", "Ketu" vs "South Node").
 */
function planetMatchesDasha(yogaPlanet: string, dashaLord: string | null): boolean {
  if (!dashaLord) return false
  const yp = normalizePlanet(yogaPlanet)
  const dl = normalizePlanet(dashaLord)
  if (yp === dl) return true

  // Common aliases
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
 * Classify a yoga's activation status given its key planets and the dasha context.
 * Returns { status, activation_reason, dasha_match }.
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

  // Latent: yoga has planets but none match current dasha lords — partial potential
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

  // Dormant: no extractable key planets
  return {
    status: 'dormant',
    activation_reason:
      'Dormant: no key planets could be extracted from this yoga row to compare against dasha.',
    dasha_match: false,
  }
}

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerQueryYogasActiveNow(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_yogas_active_now',
    QUERY_YOGAS_ACTIVE_NOW_DESCRIPTION,
    QueryYogasActiveNowInputSchema.shape,
    async (args: QueryYogasActiveNowInput) => {
      const principal = getPrincipal()
      const evaluationDate = args.date ?? new Date().toISOString().slice(0, 10)

      // ── Step 1: Fetch natal yoga rows ────────────────────────────────────────

      const yogaResult = await callPlatformPrimitive(
        'query_chart_facts',
        { categories: ['yoga'], limit: 100 },
        principal,
      )

      let yogaRows: unknown[] = []
      if (yogaResult.envelope.ok && yogaResult.status < 400) {
        const data = unwrapEnvelope(yogaResult.envelope as Record<string, unknown>)
        yogaRows = extractYogaRows(data)
      }

      // ── Step 2: Fetch current dasha periods ──────────────────────────────────

      let dashaContext: DashaContext | null = null

      const dashaResult = await callPlatformPrimitive(
        'query_dasha_periods',
        { active_only: true, at: evaluationDate },
        principal,
      )

      if (dashaResult.envelope.ok && dashaResult.status < 400) {
        const data = unwrapEnvelope(dashaResult.envelope as Record<string, unknown>)
        dashaContext = extractDashaContext(data)
      }
      // If dasha call fails: dashaContext remains null → all yogas become dormant

      // ── Step 3: Classify each yoga ───────────────────────────────────────────

      const allYogas: YogaResult[] = []

      for (const rawRow of yogaRows) {
        if (!rawRow || typeof rawRow !== 'object') continue
        const row = rawRow as Record<string, unknown>

        const yogaName =
          extractString(row, 'yoga_name', 'name', 'value_text', 'title') ??
          extractString(row, 'yoga_type', 'category_detail', 'description') ??
          'Unknown Yoga'

        const yogaId =
          extractString(row, 'fact_id', 'yoga_id', 'id') ?? null

        const keyPlanets = extractKeyPlanets(row)
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

      const statusFilter = args.status_filter ?? 'all'
      const filteredYogas =
        statusFilter === 'all'
          ? allYogas
          : allYogas.filter(y => y.status === statusFilter)

      const activeCount = allYogas.filter(y => y.status === 'active').length

      return okResult({
        ok: true,
        evaluation_date: evaluationDate,
        dasha_context: dashaContext,
        yogas: filteredYogas,
        total_yogas: allYogas.length,
        active_count: activeCount,
        epistemics: { surgical: true },
      })
    },
  )
}
