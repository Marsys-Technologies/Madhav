/**
 * query_dasha_periods.ts — MCP Tier 3 surgical primitive: dasha schedule lookup.
 *
 * What it does: Queries the Vimshottari dasha schedule for the native's chart and
 * returns structured period records. Given a date or range, returns the active
 * Mahadasha, Antardasha, and Pratyantar with exact start/end dates. Given no
 * parameters, returns the full dasha sequence. Bypasses the planner and synthesis
 * stages; tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use query_dasha_periods when the question is precisely "what dasha
 * is active on date X?" or "give me the full dasha timeline from 2020 to 2030".
 * Prefer holistic_bundle when you also want synthesis — e.g., "what does this dasha
 * mean for career in light of the chart?" Prefer query_chart_facts with
 * category:"dasha_vimshottari" for raw DB rows without the structured period wrapper.
 *
 * Input shape hints:
 *   at — optional ISO date; returns the period active on that date (e.g. "2026-05-21").
 *   range — optional {start, end} ISO date pair; returns all periods overlapping the range.
 *   system — optional dasha system name; defaults to "vimshottari".
 *   level — optional enum "maha"|"antar"|"pratyantar"|"sookshma"; defaults to "antar".
 *     "antar" returns MD+AD rows (existing behavior).
 *     "pratyantar" returns MD+AD rows each decorated with a sub_periods array of PD rows.
 *     "sookshma" returns MD+AD+PD rows each decorated with a sub_periods array of SD rows.
 *
 * Output shape preview: {ok, result: {periods: DashaPeriod[]}, trace_id, epistemics: {surgical: true}}.
 *
 * TR-P7-S1: level enum param added; PD (pratyantar) and SD (sookshma) computed
 * from Vimshottari planet ratios on top of the MD/AD schedule returned by the
 * platform primitive.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// ── Vimshottari constants ──────────────────────────────────────────────────────

/** Total Vimshottari cycle in years (used as divisor for sub-period ratios). */
const VIMSHOTTARI_TOTAL_YEARS = 120

/**
 * Canonical Vimshottari years per planet.
 * Order: Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, Venus.
 */
export const VIMSHOTTARI_YEARS: Record<string, number> = {
  Sun: 6,
  Moon: 10,
  Mars: 7,
  Rahu: 18,
  Jupiter: 16,
  Saturn: 19,
  Mercury: 17,
  Ketu: 7,
  Venus: 20,
}

/** Canonical planet order for sub-period sequences (Vimshottari sequence). */
export const VIMSHOTTARI_ORDER = [
  'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
  'Saturn', 'Mercury', 'Ketu', 'Venus',
]

// ── Sub-period computation helpers ────────────────────────────────────────────

/** Parse an ISO date string into a Date object. */
function parseDate(iso: string): Date {
  return new Date(iso)
}

/** Format a Date object to an ISO date string (YYYY-MM-DD). */
function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export interface SubPeriod {
  planet: string
  start_date: string
  end_date: string
  duration_days: number
}

/**
 * Compute the 9 Pratyantar Dasha (PD) sub-periods for a given Antardasha.
 *
 * For planet P within AD of planet A within MD of planet M:
 *   duration_PD(P) = duration_AD × (vimshottari_years[P] / 120)
 *
 * The sub-period sequence starts at the AD start date, beginning with the
 * planet whose index in VIMSHOTTARI_ORDER follows (or equals) the AD lord.
 */
export function computePratyantar(
  adLord: string,
  adStartDate: string,
  adEndDate: string,
): SubPeriod[] {
  const adStart = parseDate(adStartDate)
  const adEnd = parseDate(adEndDate)
  const adDurationMs = adEnd.getTime() - adStart.getTime()

  const startIndex = VIMSHOTTARI_ORDER.indexOf(adLord)
  // If unknown lord, start from 0
  const base = startIndex < 0 ? 0 : startIndex

  const sub: SubPeriod[] = []
  let cursor = adStart

  for (let i = 0; i < 9; i++) {
    const planet = VIMSHOTTARI_ORDER[(base + i) % 9]
    const ratio = (VIMSHOTTARI_YEARS[planet] ?? 0) / VIMSHOTTARI_TOTAL_YEARS
    const durationMs = adDurationMs * ratio
    const durationDays = Math.round(durationMs / 86_400_000)
    const periodEnd = new Date(cursor.getTime() + durationMs)

    sub.push({
      planet,
      start_date: formatDate(cursor),
      end_date: formatDate(periodEnd),
      duration_days: durationDays,
    })
    cursor = periodEnd
  }

  // Clamp last sub-period end to AD end to avoid floating-point drift
  if (sub.length > 0) {
    sub[sub.length - 1].end_date = adEndDate
    const lastStart = parseDate(sub[sub.length - 1].start_date)
    sub[sub.length - 1].duration_days = Math.round(
      (adEnd.getTime() - lastStart.getTime()) / 86_400_000
    )
  }

  return sub
}

/**
 * Compute the 9 Sookshma Dasha (SD) sub-periods for a given Pratyantar.
 *
 * For planet S within PD of planet P:
 *   duration_SD(S) = duration_PD × (vimshottari_years[S] / 120)
 */
export function computeSookshma(
  pdLord: string,
  pdStartDate: string,
  pdEndDate: string,
): SubPeriod[] {
  // Same algorithm as computePratyantar but applied to the PD duration
  return computePratyantar(pdLord, pdStartDate, pdEndDate)
}

// ── Tool description ───────────────────────────────────────────────────────────

export const QUERY_DASHA_PERIODS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns the Vimshottari dasha schedule for the native\'s chart — ' +
    'Mahadasha, Antardasha, Pratyantar, Sookshma — with exact start/end dates, bypassing synthesis. ' +
    'Input: at (single ISO date), range ({start, end}), or omit both for the full sequence. ' +
    'level param controls depth: "maha" (MD only), "antar" (MD+AD, default), ' +
    '"pratyantar" (MD+AD+PD sub_periods), "sookshma" (MD+AD+PD+SD sub_periods).',
  whenToPrefer:
    'Use for "what dasha is active on date X?" without synthesis overhead. ' +
    'Prefer holistic_bundle when you also need interpretation of what the period means for the native. ' +
    'Prefer query_chart_facts with category "dasha_vimshottari" for raw DB rows without the structured period wrapper.',
})

// ── Zod schema ─────────────────────────────────────────────────────────────────

const QueryDashaPeriodsInputSchema = z.object({
  at: z.string().optional().describe(
    'ISO date to look up the active dasha period for (e.g. "2026-05-21").'
  ),
  range: z.object({
    start: z.string().describe('ISO start date of the range.'),
    end: z.string().describe('ISO end date of the range.'),
  }).optional().describe('Date range to retrieve all overlapping dasha periods.'),
  system: z.string().optional().default('vimshottari').describe(
    'Dasha system. Defaults to "vimshottari".'
  ),
  level: z.enum(['maha', 'antar', 'pratyantar', 'sookshma']).default('antar').describe(
    'Dasha depth level. "maha" = Mahadasha only. "antar" = MD + Antardasha (default). ' +
    '"pratyantar" = MD + AD with Pratyantar sub_periods computed from Vimshottari ratios. ' +
    '"sookshma" = MD + AD + PD with Sookshma sub_periods.'
  ),
})

type QueryDashaPeriodsInput = z.infer<typeof QueryDashaPeriodsInputSchema>

// ── Period enrichment ──────────────────────────────────────────────────────────

/**
 * Enrich a flat list of platform periods with sub_periods based on the requested level.
 *
 * The platform primitive returns periods shaped as:
 *   { mahadasha, antardasha, start_date, end_date, ... }
 *
 * For "pratyantar": each period gets a sub_periods array with 9 PD entries.
 * For "sookshma": each PD entry in turn gets a sub_periods array with 9 SD entries.
 * For "maha": collapse to unique MD periods (deduplicate by md+start-year).
 */
function enrichPeriods(
  rawPeriods: Array<Record<string, unknown>>,
  level: 'maha' | 'antar' | 'pratyantar' | 'sookshma',
): Array<Record<string, unknown>> {
  if (level === 'maha') {
    // Deduplicate: keep only the first AD row per MD lord (one row per Mahadasha).
    const seen = new Set<string>()
    return rawPeriods.filter(p => {
      const md = String(p['mahadasha'] ?? p['md_lord'] ?? '')
      if (!md || seen.has(md)) return false
      seen.add(md)
      return true
    })
  }

  if (level === 'antar') {
    // Return periods as-is (existing behavior)
    return rawPeriods
  }

  if (level === 'pratyantar') {
    return rawPeriods.map(p => {
      const adLord = String(p['antardasha'] ?? p['ad_lord'] ?? '')
      const startDate = String(p['start_date'] ?? p['start'] ?? '')
      const endDate = String(p['end_date'] ?? p['end'] ?? '')
      if (!adLord || !startDate || !endDate) return p
      return {
        ...p,
        sub_periods: computePratyantar(adLord, startDate, endDate),
      }
    })
  }

  if (level === 'sookshma') {
    return rawPeriods.map(p => {
      const adLord = String(p['antardasha'] ?? p['ad_lord'] ?? '')
      const adStart = String(p['start_date'] ?? p['start'] ?? '')
      const adEnd = String(p['end_date'] ?? p['end'] ?? '')
      if (!adLord || !adStart || !adEnd) return p

      const pdPeriods = computePratyantar(adLord, adStart, adEnd).map(pd => ({
        ...pd,
        sub_periods: computeSookshma(pd.planet, pd.start_date, pd.end_date),
      }))

      return {
        ...p,
        sub_periods: pdPeriods,
      }
    })
  }

  return rawPeriods
}

// ── Registration ───────────────────────────────────────────────────────────────

export function registerQueryDashaPeriods(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_dasha_periods',
    QUERY_DASHA_PERIODS_DESCRIPTION,
    QueryDashaPeriodsInputSchema.shape,
    async (args: QueryDashaPeriodsInput) => {
      const principal = getPrincipal()
      const level = args.level ?? 'antar'

      const { status, envelope } = await callPlatformPrimitive(
        'query_dasha_periods',
        {
          ...(args.at ? { at: args.at } : {}),
          ...(args.range ? { range: args.range } : {}),
          system: args.system ?? 'vimshottari',
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Enrich with sub-periods if level requires it
      const result = envelope['result'] as Record<string, unknown> | undefined
      if (result && Array.isArray(result['periods']) && (level === 'pratyantar' || level === 'sookshma' || level === 'maha')) {
        const enriched = enrichPeriods(
          result['periods'] as Array<Record<string, unknown>>,
          level,
        )
        return okResult({
          ...envelope,
          result: { ...result, periods: enriched, level },
        })
      }

      // For "antar" (default) — return as-is with level annotated
      if (result && Array.isArray(result['periods'])) {
        return okResult({
          ...envelope,
          result: { ...result, level },
        })
      }

      return okResult(envelope)
    }
  )
}
