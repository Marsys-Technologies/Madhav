/**
 * query_jaimini_chara_dasha.ts — MCP Tier 3 surgical primitive: Jaimini Chara Dasha lookup.
 *
 * What it does: Returns the active Jaimini Chara Dasha period (maha dasha + antar dasha)
 * for a given date, based on the native's sidereal chart. Optionally returns the full
 * 12-rashi dasha timeline with start/end dates spanning the native's 120-year cycle.
 *
 * Algorithm (standard Jaimini Chara Dasha):
 *   - Each of the 12 rashis serves as a dasha lord.
 *   - Period length is determined by the sign lord's longitude within its own sign:
 *       Odd rashis  (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius):
 *           years = 30 − floor(lord_lon_in_sign)
 *       Even rashis (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces):
 *           years = floor(lord_lon_in_sign) + 1
 *   - Years capped at 12 per rashi; total cycle = 120 years.
 *   - Sequence starts from the native's Lagna rashi.
 *   - Sub-periods subdivide each rashi's period proportionally.
 *
 * Data source: Python sidecar /jaimini_drishti/chara_dasha endpoint.
 *
 * When to prefer: Use for Jaimini-tradition timing questions ("What is the active
 * Chara Dasha right now?", "When does the Gemini dasha begin?"). Prefer
 * query_dasha_periods for Vimshottari Dasha. Prefer holistic_bundle when
 * synthesised interpretation is needed.
 *
 * Output shape:
 *   date mode:   {ok, active_rashi_dasha: {rashi, sign_lord, start_date, end_date},
 *                active_antar_dasha: {rashi, sign_lord, start_date, end_date}}
 *   full mode:   {ok, full_periods: [{rashi, sign_lord, years, start_date, end_date}], ...}
 *
 * Session: TR-P7-S2
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_JAIMINI_CHARA_DASHA_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns the active Jaimini Chara Dasha period (maha dasha + antar dasha) ' +
    'for a given date, computed from the native\'s sidereal chart using standard Jaimini ' +
    'Chara Dasha algorithm (sign lord longitude determines period length; 12 rashi cycle = 120 years). ' +
    'With include_sub_periods=true, returns the full 12-rashi dasha timeline with start/end dates.',
  whenToPrefer:
    'Use for Jaimini-tradition timing questions: "What is the active Chara Dasha right now?", ' +
    '"When does the Scorpio dasha begin?", "Show the full Jaimini dasha timeline." ' +
    'Prefer query_dasha_periods for Vimshottari Dasha. ' +
    'Prefer holistic_bundle when synthesised interpretation of the dasha is needed.',
})

// ── Zod schema ────────────────────────────────────────────────────────────────

const QueryJaiminiCharaDashaInputSchema = z.object({
  date: z.string().optional().describe(
    'ISO date (YYYY-MM-DD) to query the active dasha for. Defaults to today.'
  ),
  include_sub_periods: z.boolean().optional().default(false).describe(
    'If true, returns full_periods array with all 12 rashi periods and their antar dasha breakdown. ' +
    'Default false (returns only the active period).'
  ),
  tier: z.string().optional().default('super_admin').describe(
    'Audience tier for response filtering. Defaults to super_admin.'
  ),
})

type QueryJaiminiCharaDashaInput = z.infer<typeof QueryJaiminiCharaDashaInputSchema>

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RashiPeriod {
  rashi: string
  sign_lord: string
  years?: number
  start_date: string
  end_date: string
}

export interface CharaDashaResponse {
  ok: boolean
  query_date?: string
  active_rashi_dasha?: RashiPeriod
  active_antar_dasha?: RashiPeriod | null
  full_periods?: RashiPeriod[]
  total_years?: number
  algorithm?: string
  epistemics?: { surgical: boolean }
}

// ── Envelope unwrap helper ────────────────────────────────────────────────────

/**
 * Unwrap the platform primitive response envelope.
 * Handles both the ToolBundle pattern (result.results[0].content) and
 * direct result object pattern.
 */
function unwrapPrimitiveResult(envelope: Record<string, unknown>): unknown {
  const result = envelope['result']
  if (!result || typeof result !== 'object') return envelope

  const resultObj = result as Record<string, unknown>

  // ToolBundle pattern: results[0].content (JSON string)
  const bundleResults = resultObj['results'] as Array<{ content: unknown }> | undefined
  if (bundleResults && bundleResults.length > 0) {
    const raw = bundleResults[0]!.content
    if (typeof raw === 'string') {
      try { return JSON.parse(raw) } catch { /* fall through */ }
    }
    if (raw !== null && raw !== undefined) return raw
  }

  // Direct result object
  return resultObj
}

// ── Core logic ────────────────────────────────────────────────────────────────

/**
 * Call the sidecar's Chara Dasha endpoint (active dasha for a given date).
 * Route: GET /jaimini_drishti/chara_dasha?date=YYYY-MM-DD
 * Called via the platform primitive dispatcher as 'jaimini_chara_dasha'.
 */
async function fetchActiveCharaDasha(
  date: string | undefined,
  principal: Principal,
): Promise<{ status: number; data: unknown }> {
  const params: Record<string, unknown> = {}
  if (date) params['date'] = date

  const { status, envelope } = await callPlatformPrimitive(
    'jaimini_chara_dasha',
    params,
    principal,
  )
  return { status, data: unwrapPrimitiveResult(envelope as unknown as Record<string, unknown>) }
}

/**
 * Call the sidecar's full Chara Dasha timeline endpoint.
 * Route: GET /jaimini_drishti/chara_dasha/full
 * Called via the platform primitive dispatcher as 'jaimini_chara_dasha_full'.
 */
async function fetchFullCharaDasha(
  date: string | undefined,
  principal: Principal,
): Promise<{ status: number; data: unknown }> {
  const params: Record<string, unknown> = {
    include_sub_periods: true,
  }
  if (date) params['date'] = date

  const { status, envelope } = await callPlatformPrimitive(
    'jaimini_chara_dasha_full',
    params,
    principal,
  )
  return { status, data: unwrapPrimitiveResult(envelope as unknown as Record<string, unknown>) }
}

/**
 * Extract the active rashi dasha from the sidecar response.
 */
function extractActiveDasha(data: unknown): {
  active_rashi_dasha?: RashiPeriod
  active_antar_dasha?: RashiPeriod | null
  query_date?: string
} | null {
  if (!data || typeof data !== 'object') return null
  const d = data as Record<string, unknown>

  if (d['ok'] !== true) return null

  const activeRd = d['active_rashi_dasha'] as RashiPeriod | undefined
  const activeAd = d['active_antar_dasha'] as RashiPeriod | null | undefined

  if (!activeRd || !activeRd.rashi) return null

  return {
    active_rashi_dasha: activeRd,
    active_antar_dasha: activeAd ?? null,
    query_date: d['query_date'] as string | undefined,
  }
}

/**
 * Extract full periods from the sidecar response.
 */
function extractFullPeriods(data: unknown): {
  full_periods?: RashiPeriod[]
  total_years?: number
} | null {
  if (!data || typeof data !== 'object') return null
  const d = data as Record<string, unknown>

  if (d['ok'] !== true) return null

  const periods = d['periods'] as RashiPeriod[] | undefined
  if (!Array.isArray(periods)) return null

  const totalYears = d['total_years'] as number | undefined

  return {
    full_periods: periods,
    total_years: totalYears ?? periods.reduce((sum, p) => sum + (p.years ?? 0), 0),
  }
}

/**
 * Build a synthetic "full periods" response from the active dasha data,
 * used when the sidecar is only returning active dasha info but include_sub_periods=true.
 * In practice this should not happen — the full endpoint is called when include_sub_periods=true.
 */
function buildSyntheticFullPeriods(activeData: unknown): RashiPeriod[] | null {
  if (!activeData || typeof activeData !== 'object') return null
  const d = activeData as Record<string, unknown>

  const periods = d['periods'] as RashiPeriod[] | undefined
  if (Array.isArray(periods) && periods.length > 0) return periods

  return null
}

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerQueryJaiminiCharaDasha(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_jaimini_chara_dasha',
    QUERY_JAIMINI_CHARA_DASHA_DESCRIPTION,
    QueryJaiminiCharaDashaInputSchema.shape,
    async (args: QueryJaiminiCharaDashaInput) => {
      const principal = getPrincipal()
      const queryDate = args.date

      if (args.include_sub_periods) {
        // Fetch full timeline from sidecar
        const { status, data } = await fetchFullCharaDasha(queryDate, principal)

        if (status >= 400) {
          const errData = data as Record<string, unknown>
          return errorResult({
            ok: false,
            error: 'sidecar_error',
            message: errData?.['detail'] ?? errData?.['message'] ?? 'Sidecar returned an error',
            sidecar_status: status,
          })
        }

        const fullResult = extractFullPeriods(data)

        if (!fullResult || !fullResult.full_periods) {
          // Try to extract active dasha as a fallback
          return errorResult({
            ok: false,
            error: 'full_periods_not_found',
            message:
              'Sidecar response did not contain a "periods" array. ' +
              'Ensure the /jaimini_drishti/chara_dasha/full endpoint is wired.',
          })
        }

        // Also fetch active dasha for the query date
        const { data: activeData } = await fetchActiveCharaDasha(queryDate, principal)
        const activeResult = extractActiveDasha(activeData)

        return okResult({
          ok: true,
          query_date: queryDate ?? new Date().toISOString().split('T')[0],
          active_rashi_dasha: activeResult?.active_rashi_dasha ?? null,
          active_antar_dasha: activeResult?.active_antar_dasha ?? null,
          full_periods: fullResult.full_periods,
          total_years: fullResult.total_years,
          algorithm: 'jaimini_chara_dasha',
          epistemics: { surgical: true },
        })
      } else {
        // Fetch only the active dasha
        const { status, data } = await fetchActiveCharaDasha(queryDate, principal)

        if (status >= 400) {
          const errData = data as Record<string, unknown>
          return errorResult({
            ok: false,
            error: 'sidecar_error',
            message: errData?.['detail'] ?? errData?.['message'] ?? 'Sidecar returned an error',
            sidecar_status: status,
          })
        }

        const activeResult = extractActiveDasha(data)

        if (!activeResult || !activeResult.active_rashi_dasha) {
          return errorResult({
            ok: false,
            error: 'active_dasha_not_found',
            message:
              'Sidecar response did not contain a valid active_rashi_dasha. ' +
              'Check that the /jaimini_drishti/chara_dasha endpoint is implemented.',
          })
        }

        return okResult({
          ok: true,
          query_date: activeResult.query_date ?? queryDate ?? new Date().toISOString().split('T')[0],
          active_rashi_dasha: activeResult.active_rashi_dasha,
          active_antar_dasha: activeResult.active_antar_dasha ?? null,
          algorithm: 'jaimini_chara_dasha',
          epistemics: { surgical: true },
        })
      }
    },
  )
}
