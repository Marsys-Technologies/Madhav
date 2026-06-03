/**
 * muhurta_finder.ts — MCP tool: muhurta_finder (PH-4-4)
 * Layer L4 · Phala (Predictive Engine) · Asset PH-4-4 (phala.muhurta)
 * BRAHMA-PH-4-4
 *
 * INVERTS the Phala prediction engine:
 *   - Prediction: "what will happen given the current time?"
 *   - Electional: "WHEN is best to act for a desired action_type?"
 *
 * Tool: muhurta_finder(chart_id, action_type, date_range, min_score?)
 *   → {windows:[{start,end,score,factors}], provenance_envelope}
 *
 * Algorithm: for each 48-hour window in the requested date range (max 90 days):
 *   auspiciousness_score = panchanga_quality(40%) + dasha_quality(30%)
 *                        + transit_quality(20%) + signal_activation(10%)
 *
 * action_types: marriage | travel | business | medical | education | property | general
 *
 * Contract (BRAHMA PH-4-4):
 *   - 0 <= score <= 1 on every window
 *   - len(windows) >= 1 for a valid 90-day range
 *   - source_citation non-null on every window (B.3 mandate)
 *   - provenance_envelope on every response
 *
 * FORENSIC grounding:
 *   Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
 *   A high-score education muhurta for the native should align with
 *   Mercury+Pushya windows (Mercury MD + Pushya nakshatra per BPHS ch.46).
 *
 * Architecture:
 *   MCP tool → callPlatformPrimitive('muhurta_finder', params)
 *   → /api/mcp/primitives/muhurta_finder (platform) → query_muhurat retrieval tool
 *   → sidecar POST /api/compute/muhurat (Phase 4C-6 muhurat router)
 *
 * surgical: true (pure retrieval; no LLM calls)
 * BRAHMA-PH-4-4
 */

import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'

// ── Input schema ───────────────────────────────────────────────────────────────

export const MuhurtaFinderInputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to find auspicious windows for. ' +
      'Native chart (Abhisek Mohanty, 1984-02-05 10:43 IST Bhubaneswar): ' +
      '362f9f17-95a5-490b-a5a7-027d3e0efda0'
    ),

  action_type: z
    .enum(['marriage', 'travel', 'business', 'medical', 'education', 'property', 'general'])
    .describe(
      'The type of action to find auspicious windows for. ' +
      'marriage — vivah muhurta (Rohini/Guruvara auspicious per BPHS ch.46); ' +
      'travel — yatra muhurta (Ashwini/Mrigashira/Pushya preferred); ' +
      'business — vyapara muhurta (Rohini/Hasta/Budhavara); ' +
      'medical — rogashanti muhurta (Pushya/Ashwini; avoid Krittika); ' +
      'education — vidya muhurta (Pushya nakshatra most auspicious; Mercury/Thursday days); ' +
      'property — griha/bhumi muhurta (Uttaraphalguni/Uttarashada); ' +
      'general — all action types permissible.'
    ),

  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
    })
    .describe(
      'Date range to search for auspicious windows. ' +
      'Maximum 90 days (up to 45 × 48-hour windows). ' +
      'Windows are 48-hour blocks starting at midnight UTC. ' +
      'Example next 90 days: {"start":"2026-06-04","end":"2026-09-01"}.'
    ),

  min_score: z
    .number()
    .min(0.0)
    .max(1.0)
    .optional()
    .describe(
      'Minimum auspiciousness_score [0.0–1.0]. Default 0.0 (all windows). ' +
      'Recommended thresholds: high ≥ 0.70; medium 0.50–0.69; low < 0.50. ' +
      'Score = panchanga_quality(40%) + dasha_quality(30%) ' +
      '+ transit_quality(20%) + signal_activation(10%).'
    ),

  limit: z
    .number()
    .int()
    .min(1)
    .max(45)
    .default(20)
    .describe(
      'Maximum number of windows to return, ranked by auspiciousness_score DESC. ' +
      'Default 20; maximum 45 (one per 48-hour slot in a 90-day range).'
    ),
})

export type MuhurtaFinderInput = z.infer<typeof MuhurtaFinderInputSchema>

// ── Output shape (documented; actual shape comes from the platform) ────────────

/** Factors breakdown for one muhurta window. */
export interface MuhurtaFactors {
  panchanga_quality: number      // [0.0, 1.0] — tithi × vara × nakshatra × yoga
  dasha_quality: number          // [0.0, 1.0] — active MD/AD benefic quality
  transit_quality: number        // [0.0, 1.0] — key transits in the window
  signal_activation: number      // [0.0, 1.0] — MSR signal activation for action_type
  panchanga_details: {
    tithi_name: string
    vara_lord: string
    moon_nakshatra: string
    yoga: string
    inauspicious_windows: string[]
  }
  dasha_details: {
    md_lord: string
    ad_lord: string
  }
  avoid_notes: string[]          // empty if no knockout conditions apply
}

/** One ranked auspicious window. */
export interface MuhurtaWindow {
  start: string                  // ISO datetime UTC
  end: string                    // ISO datetime UTC (48h after start)
  score: number                  // auspiciousness_score [0.0, 1.0]
  factors: MuhurtaFactors
  source_citation: string        // NEVER null — B.3 mandate
}

/** Provenance envelope on every muhurta_finder response. */
export interface MuhurtaProvenanceEnvelope {
  source: string           // 'phala.muhurta'
  asset: string            // 'PH-4-4'
  algorithm: string        // score formula
  min_score_applied: number
  chart_id: string
  action_type: string
  queried_at: string       // ISO datetime UTC
  l1_ground_truth: string  // FORENSIC + panchanga_daily + MSR citations
  b3_citation_compliant: boolean
}

/** Full muhurta_finder response. */
export interface MuhurtaFinderResult {
  ok: boolean
  chart_id: string
  action_type: string
  query_window: { start: string; end: string }
  windows: MuhurtaWindow[]
  window_count: number
  provenance_envelope: MuhurtaProvenanceEnvelope
}

// ── Tool description ───────────────────────────────────────────────────────────

export const MUHURTA_FINDER_DESCRIPTION =
  'Electional auspicious time-window finder (phala.muhurta / PH-4-4). ' +
  'INVERTS the Phala prediction engine: instead of "what will happen?", asks ' +
  '"WHEN is best to act for a given action_type?" ' +
  'For each 48-hour window in the requested date range (max 90 days), computes: ' +
  '  auspiciousness_score = panchanga_quality(40%) + dasha_quality(30%) ' +
  '                       + transit_quality(20%) + signal_activation(10%) ' +
  'Returns windows ranked by auspiciousness_score DESC. ' +
  'action_types: marriage | travel | business | medical | education | property | general. ' +
  'panchanga_quality: classical BPHS ch.46 muhurta rules — tithi, vara, nakshatra, yoga. ' +
  'dasha_quality: active Vimshottari MD/AD benefic quality for the chart. ' +
  'transit_quality: key planetary transits during the window. ' +
  'signal_activation: MSR v5.0 signal ensemble for the action_type. ' +
  'B.3 mandate: source_citation NON-NULL on every window. ' +
  'provenance_envelope present on every response. ' +
  'FORENSIC grounding: native chart Abhisek Mohanty 1984-02-05 10:43 IST Bhubaneswar. ' +
  'Education muhurta: Pushya nakshatra + Mercury/Thursday days most auspicious (BPHS ch.46 §vidya). ' +
  'Marriage muhurta: Rohini/Revati/Hasta + Monday/Thursday/Friday most auspicious. ' +
  'surgical: true — pure retrieval + pre-computed scoring, no LLM synthesis. ' +
  'BRAHMA-PH-4-4 | phala.muhurta contract.'

// ── Tool handler ───────────────────────────────────────────────────────────────

/**
 * muhurta_finder MCP tool handler.
 *
 * Delegates to /api/mcp/primitives/muhurta_finder on the platform service
 * (which maps to the query_muhurat retrieval tool via MCP_TO_RETRIEVAL_TOOL).
 *
 * Returns ranked auspicious windows with provenance_envelope.
 *
 * Error contract:
 *   - If date_range > 90 days, platform returns 422 validation error.
 *   - If chart_id has no pre-computed rows, falls back to on-the-fly scoring.
 *   - Invalid action_type returns 422 validation error.
 */
export async function handleMuhurtaFinder(
  input: MuhurtaFinderInput,
  principal: Principal
): Promise<unknown> {
  const params: Record<string, unknown> = {
    chart_id: input.chart_id,
    action_type: input.action_type,
    date_range: input.date_range,
    limit: input.limit,
  }
  if (input.min_score !== undefined) {
    params['min_score'] = input.min_score
  }

  const result = await callPlatformPrimitive('muhurta_finder', params, principal)
  const env = result.envelope
  if (!env.ok) return env

  const resultData = env.result as MuhurtaFinderResult | undefined
  const windows: MuhurtaWindow[] = resultData?.windows ?? []

  // Assert B.3 grounding contract: surface any citation-null windows as a warning
  const uncited = windows.filter((w) => !w.source_citation)
  if (uncited.length > 0) {
    console.warn(
      `[PH-4-4] muhurta_finder: ${uncited.length} windows have null source_citation — ` +
      `contract violation (B.3 mandate)`
    )
  }

  // Assert score invariant
  const outOfRange = windows.filter((w) => w.score < 0.0 || w.score > 1.0)
  if (outOfRange.length > 0) {
    console.warn(
      `[PH-4-4] muhurta_finder: ${outOfRange.length} windows have score outside [0.0, 1.0]`
    )
  }

  const provenanceEnvelope: MuhurtaProvenanceEnvelope = resultData?.provenance_envelope ?? {
    source: 'phala.muhurta',
    asset: 'PH-4-4',
    algorithm: 'panchanga_quality(40%) + dasha_quality(30%) + transit_quality(20%) + signal_activation(10%)',
    min_score_applied: input.min_score ?? 0.0,
    chart_id: input.chart_id,
    action_type: input.action_type,
    queried_at: new Date().toISOString(),
    l1_ground_truth: 'FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD (2026-2043); panchanga_daily; MSR v5.0 SIG.*',
    b3_citation_compliant: uncited.length === 0,
  }

  return {
    ...env,
    result: {
      ok: true,
      chart_id: input.chart_id,
      action_type: input.action_type,
      query_window: input.date_range,
      windows,
      window_count: resultData?.window_count ?? windows.length,
      provenance_envelope: provenanceEnvelope,
    } satisfies MuhurtaFinderResult,
  }
}

// ── MCP server registration helper ────────────────────────────────────────────

/**
 * Register the muhurta_finder tool on an McpServer instance.
 *
 * Usage in server.ts:
 *   import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
 *   registerMuhurtaFinder(server, getPrincipal)
 *
 * The tool is surgical (pure retrieval + pre-computed scoring) and appropriate
 * for all principal tiers. Maps to query_muhurat via MCP_TO_RETRIEVAL_TOOL.
 *
 * Contract assertions:
 *   - source_citation non-null on all returned windows (B.3 mandate)
 *   - provenance_envelope present in every response
 *   - 0 <= score <= 1 on every window
 *   - action_type ∈ {marriage, travel, business, medical, education, property, general}
 *
 * BRAHMA-PH-4-4
 */
export function registerMuhurtaFinder(
  server: {
    tool: (
      name: string,
      description: string,
      schema: Record<string, unknown>,
      handler: (args: unknown) => Promise<unknown>
    ) => void
  },
  getPrincipal: () => Principal
): void {
  server.tool(
    'muhurta_finder',
    MUHURTA_FINDER_DESCRIPTION,
    {
      chart_id: z
        .string()
        .uuid()
        .describe(
          'UUID of the chart. ' +
          'Native (Abhisek Mohanty 1984-02-05 10:43 IST Bhubaneswar): 362f9f17-95a5-490b-a5a7-027d3e0efda0'
        ),
      action_type: z
        .enum(['marriage', 'travel', 'business', 'medical', 'education', 'property', 'general'])
        .describe(
          'Action type: marriage | travel | business | medical | education | property | general. ' +
          'education = Pushya/Mercury/Thursday auspicious; marriage = Rohini/Guruvara; ' +
          'business = Rohini/Hasta/Budhavara; travel = Ashwini/Mrigashira.'
        ),
      date_range: z
        .object({
          start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
          end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
        })
        .describe(
          'Search range (YYYY-MM-DD). Max 90 days. ' +
          '48-hour blocks returned. Example: {"start":"2026-06-04","end":"2026-09-01"}.'
        ),
      min_score: z
        .number()
        .min(0.0)
        .max(1.0)
        .optional()
        .describe(
          'Minimum auspiciousness_score [0.0–1.0]. Default 0.0. ' +
          'High ≥ 0.70; Medium 0.50–0.69.'
        ),
      limit: z
        .number()
        .int()
        .min(1)
        .max(45)
        .default(20)
        .describe('Max windows to return (ranked by score DESC). Default 20.'),
    },
    async (args: unknown) => {
      const parsed = MuhurtaFinderInputSchema.parse(args)
      return handleMuhurtaFinder(parsed, getPrincipal())
    }
  )
}
