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
 *   Reference birth: 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *   A high-score education muhurta for this chart should align with
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
import { remoteAuthorize } from '../lib/authz.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── MCP response wrapping (T-7 fix) ─────────────────────────────────────────
//
// R6 0b-deadtools (T-7): muhurta_finder returned nothing at all — no windows,
// no empty_reason, no error object. Root cause: handleMuhurtaFinder's early
// auth-denied branch aside, both the `!env.ok` branch and the success branch
// returned the raw McpEnvelope-shaped object ({ok, trace_id, epistemics,
// result, ...}) directly from the tool handler. The MCP SDK tool-call
// contract requires a `{content: [...], structuredContent?, isError?}` shape
// (see every sibling tool's `dualOutput`/`errOut` helper, e.g.
// kala_muhurta_get in register_p1_aliases.ts) — an object with no `content`
// key is not a valid tool result, so the client silently rendered empty.
// This was never an unreturned promise; it was a mis-shaped resolved one.
// W3-L5 (budget unification): muhurta_finder's `windows` array (up to a 90-day scan of
// 48-hour windows) previously shipped through this dualOutput with no response-budget
// pass at all — part of the ~36-of-~115 unclamped surface (GT-48).
function dualOutput(data: unknown): { structuredContent: { type: 'object'; object: unknown }; content: [{ type: 'text'; text: string }] } {
  const budgeted = budgetMcpContent(data, 'muhurta_finder')
  return {
    structuredContent: { type: 'object', object: budgeted },
    content: [{ type: 'text', text: JSON.stringify(budgeted) }],
  }
}

function errorOutput(message: string, extra?: Record<string, unknown>): { structuredContent: { type: 'object'; object: unknown }; content: [{ type: 'text'; text: string }]; isError: true } {
  return { ...dualOutput({ ok: false, error: message, tool: 'muhurta_finder', ...extra }), isError: true }
}

// ── Input schema ───────────────────────────────────────────────────────────────

export const MuhurtaFinderInputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to find auspicious windows for. Must be a valid chart UUID from the charts table.'
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
  /**
   * R5.1 C3 — present (and windows: []) when the requested date_range has no
   * real panchanga_daily coverage (outside the rolling +12-month populated
   * window). Never fabricated data for out-of-window dates — see
   * brahmagyan/phala/muhurta.py muhurta_finder()'s empty_reason construction.
   */
  empty_reason?: string
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
/**
 * Unwrap a surgical-primitive result into the raw MuhurtaFinderResult object.
 *
 * `getToolByName().retrieve()` (tool_name_bridge.ts) wraps EVERY capability
 * handler's return value into the generic legacy ToolBundle shape
 * (`{tool_bundle_id, results: [{content: "<JSON string>"}], ...}`) via
 * `capabilityResultToToolBundle` / `toToolBundleResults` — it never returns
 * the capability's raw object directly. `env.result` from
 * `callPlatformPrimitive()` is therefore that ToolBundle, not
 * `MuhurtaFinderResult`, so a direct cast (`env.result as MuhurtaFinderResult`)
 * always misses `.windows` and silently degrades to an empty array regardless
 * of what real data the underlying query_muhurat capability returned.
 *
 * This handles both shapes defensively: the ToolBundle (`results[0].content`,
 * either a JSON string or an already-parsed object depending on bridge
 * version) and a hypothetical direct-object result, so it keeps working if
 * the bridge's wrapping behavior ever changes.
 */
function unwrapMuhurtaFinderResult(raw: unknown): MuhurtaFinderResult | undefined {
  if (!raw || typeof raw !== 'object') return undefined

  // Already the raw shape (has `windows` directly) — no ToolBundle wrapper.
  if ('windows' in (raw as Record<string, unknown>)) {
    return raw as MuhurtaFinderResult
  }

  // ToolBundle shape: { results: [{ content: string | object }], ... }
  const bundle = raw as { results?: Array<{ content?: unknown }> }
  if (Array.isArray(bundle.results) && bundle.results.length > 0) {
    const content = bundle.results[0]?.content
    if (typeof content === 'string') {
      try {
        const parsed: unknown = JSON.parse(content)
        if (parsed && typeof parsed === 'object') return parsed as MuhurtaFinderResult
      } catch {
        // Not JSON — fall through to undefined below.
      }
    } else if (content && typeof content === 'object') {
      return content as MuhurtaFinderResult
    }
  }

  return undefined
}

export async function handleMuhurtaFinder(
  input: MuhurtaFinderInput,
  principal: Principal
): Promise<unknown> {
  const authorized = await remoteAuthorize(principal, input.chart_id)
  if (!authorized) {
    return {
      content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }],
      isError: true,
    }
  }

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
  if (!env.ok) return errorOutput(env.error?.message ?? 'muhurta_finder platform call failed', { chart_id: input.chart_id, trace_id: env.trace_id })

  const resultData = unwrapMuhurtaFinderResult(env.result)
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

  const finalResult: MuhurtaFinderResult = {
    ok: true,
    chart_id: input.chart_id,
    action_type: input.action_type,
    query_window: input.date_range,
    windows,
    window_count: resultData?.window_count ?? windows.length,
    provenance_envelope: provenanceEnvelope,
  }
  // R5.1 C3: propagate the honest empty-with-reason signal for out-of-window
  // date ranges instead of silently dropping it (never fabricate windows).
  if (resultData?.empty_reason) {
    finalResult.empty_reason = resultData.empty_reason
  }

  return dualOutput(finalResult)
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
          'UUID of the chart. Must be a valid chart UUID from the charts table.'
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
