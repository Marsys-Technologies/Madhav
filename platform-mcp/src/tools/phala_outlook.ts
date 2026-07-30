/**
 * phala_outlook.ts — BRAHMA-PH-4-5: phala.outlook
 *
 * Composite predictive bundle — B.11 L4 entrypoint.
 *
 * Contract (BRAHMA PH-4-5):
 *   Tool:   phala_outlook(chart_id, horizon_months) →
 *             {
 *               anchors: [...],           // PH-4-1
 *               mitigations: [...],       // PH-4-2
 *               rectification: {...},     // PH-4-3
 *               auspicious_windows: [...], // PH-4-4 / panchanga_daily
 *               summary_confidence: FLOAT, // mean(anchor.confidence)
 *               provenance_envelope: {
 *                 source: "phala.outlook",
 *                 layers: ["PH-4-1","PH-4-2","PH-4-3","PH-4-4"],
 *                 computed_at: ISO,
 *                 ...
 *               }
 *             }
 *   No new table — API aggregation only.
 *   summary_confidence = mean(anchors[].confidence), clamped to [0.0, 1.0].
 *   Acceptance:
 *     AC1 — all 4 subsystems present in response
 *     AC2 — summary_confidence in [0.0, 1.0]
 *     AC3 — tool smoke: chart returns valid structure
 *
 * Reference birth: 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *
 * Wiring: registerPhalaOutlookTool(server) → server.ts during L4 Phala registration.
 *
 * BRAHMA-PH-4-5
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { finalizeMcpBudget, type TrimmableSection } from '../lib/response_budget.js'

// R5.2 A2 (punch #3, estate-wide budget sweep): phala_outlook's default call measured
// 461KB on the native chart — the worst offender in the "234KB class" the brief names,
// caused by 100 anchors + 100 mitigations + 30 auspicious_windows served at full detail
// with no ceiling (same failure class C1 already fixed for judgment_query/graha_portrait/
// pact_query). Reuses the SAME shared trimmer (response_budget.ts), not a bespoke cut.
const PHALA_OUTLOOK_BUDGET_KB = 30

function phalaOutlookSections(): TrimmableSection<PhalOutlookResult>[] {
  return [
    {
      path: 'anchors', label: 'anchors', minKeep: 10,
      getArray: (c) => c.anchors, setArray: (c, kept) => { c.anchors = kept as PhalOutlookResult['anchors'] },
      recover: { instrument: 'phala_predictive_anchors_get', hint: 'full anchors list with posterior_provenance' },
    },
    {
      path: 'mitigations', label: 'mitigations', minKeep: 10,
      getArray: (c) => c.mitigations, setArray: (c, kept) => { c.mitigations = kept as PhalOutlookResult['mitigations'] },
      recover: { instrument: 'bodha_remedies_get', hint: 'full mitigation/remedy list' },
    },
    {
      path: 'auspicious_windows', label: 'auspicious_windows', minKeep: 5,
      getArray: (c) => c.auspicious_windows, setArray: (c, kept) => { c.auspicious_windows = kept as PhalOutlookResult['auspicious_windows'] },
      recover: { instrument: 'kala_muhurta_get', hint: 'full auspicious-window list for the horizon' },
    },
  ]
}

// ── Environment ────────────────────────────────────────────────────────────────

const PYTHON_SIDECAR_URL = (
  process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
).replace(/\/$/, '')

const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''
const TOOL_TIMEOUT_MS = 45_000  // Composite call needs more time than individual sub-tools

// ── Types ──────────────────────────────────────────────────────────────────────

export interface OutlookProvenanceEnvelope {
  source: 'phala.outlook'
  asset: 'PH-4-5'
  asset_version: string
  layers: ['PH-4-1', 'PH-4-2', 'PH-4-3', 'PH-4-4']
  layer_provenances: {
    'PH-4-1': Record<string, unknown>
    'PH-4-2': Record<string, unknown>
    'PH-4-3': Record<string, unknown>
    'PH-4-4': Record<string, unknown>
  }
  chart_id: string
  horizon_months: number
  date_range: { start: string; end: string }
  summary_confidence_algorithm: string
  computed_at: string  // ISO datetime
}

export interface PhalOutlookResult {
  ok: boolean
  chart_id: string
  horizon_months: number
  query_window: { start: string; end: string }
  anchors: Array<Record<string, unknown>>
  mitigations: Array<Record<string, unknown>>
  rectification: Record<string, unknown>
  auspicious_windows: Array<Record<string, unknown>>
  summary_confidence: number  // mean(anchor.confidence), in [0.0, 1.0]
  provenance_envelope: OutlookProvenanceEnvelope
  trim_report?: unknown
}

// ── Sidecar call ───────────────────────────────────────────────────────────────

async function callSidecar<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  const url = `${PYTHON_SIDECAR_URL}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (SIDECAR_API_KEY) {
    headers['X-API-Key'] = SIDECAR_API_KEY
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TOOL_TIMEOUT_MS)

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      const text = await response.text().catch(() => '')
      throw new Error(
        `Sidecar HTTP ${response.status} from ${path}: ${text.slice(0, 300)}`
      )
    }

    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

// ── Core composite fetch ───────────────────────────────────────────────────────

/**
 * Fetch the composite phala.outlook bundle.
 *
 * Calls /api/compute/phala/outlook on the Python sidecar which aggregates
 * all 4 L4 Phala subsystems in one server-side call:
 *   - PH-4-1: calibrated event anchors (anchors[])
 *   - PH-4-2: classical BPHS remedies (mitigations[])
 *   - PH-4-3: birth-time rectification (rectification{})
 *   - PH-4-4: auspicious muhurat windows (auspicious_windows[])
 *
 * summary_confidence = mean(anchors[].confidence), clamped to [0.0, 1.0].
 */
export async function fetchPhalaOutlook(
  chartId: string,
  horizonMonths: number = 12,
  opts: { minConfidence?: number } = {}
): Promise<PhalOutlookResult> {
  const body: Record<string, unknown> = {
    chart_id: chartId,
    horizon_months: horizonMonths,
  }
  if (opts.minConfidence !== undefined) {
    body.min_confidence = opts.minConfidence
  }
  return callSidecar<PhalOutlookResult>('/api/compute/phala/outlook', body)
}

// ── Tool registration ──────────────────────────────────────────────────────────

const TOOL_NAME = 'phala_outlook'

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to query. Must be a valid chart UUID from the charts table.'
    ),

  horizon_months: z
    .number()
    .int()
    .min(1)
    .max(120)
    .default(12)
    .describe(
      'Forecast horizon in months (1–120, default 12). ' +
        'The date range is computed as today → today + horizon_months*30 days. ' +
        'All 4 subsystems are queried for this window.'
    ),

  min_confidence: z
    .number()
    .min(0.0)
    .max(1.0)
    .optional()
    .describe(
      'Optional minimum confidence filter applied to PH-4-1 anchors [0.0–1.0]. ' +
        'Default 0.0 (all anchors returned). ' +
        'High confidence ≥ 0.65; Medium 0.45–0.64; Low < 0.45.'
    ),
})

/**
 * Register the phala_outlook MCP tool (PH-4-5) on an McpServer.
 *
 * This is the B.11 entrypoint for L4 Phala — a single call that surfaces
 * the full predictive picture for a horizon:
 *
 *   anchors           — PH-4-1: calibrated probabilistic event anchors
 *   mitigations       — PH-4-2: BPHS-grounded classical remedies per anchor
 *   rectification     — PH-4-3: birth-time rectification result
 *   auspicious_windows — PH-4-4: panchanga-derived muhurat windows
 *   summary_confidence — mean(anchors[].confidence) across all anchors
 *   provenance_envelope — source="phala.outlook", layers=[PH-4-1..PH-4-4]
 *
 * Called from server.ts during L4 Phala registration.
 *
 * Example:
 *   import { registerPhalaOutlookTool } from './tools/phala_outlook.js'
 *   registerPhalaOutlookTool(server)
 */
export function registerPhalaOutlookTool(server: McpServer, principal: Principal): void {
  server.tool(
    TOOL_NAME,
    'Composite predictive bundle for a chart and forecast horizon (BRAHMA-PH-4-5).\n\n' +
      'Aggregates all 4 L4 Phala subsystems in one call:\n' +
      '  anchors           (PH-4-1) — calibrated probabilistic event anchors\n' +
      '                               confidence = dasha_quality × signal_strength × convergence_score\n' +
      '                               each anchor has falsifier + source_citation (B.3 mandate)\n' +
      '  mitigations       (PH-4-2) — BPHS-grounded classical remedies per anchor\n' +
      '                               mitigation_type ∈ {mantra, charity, gemstone, ritual, timing}\n' +
      '  rectification     (PH-4-3) — birth-time rectification via LEL train/test split\n' +
      '                               best_candidate_time, confidence, train_score, test_score\n' +
      '  auspicious_windows (PH-4-4) — panchanga-derived muhurat windows for the horizon\n' +
      '                               per-day: tithi, vara, nakshatra, yoga, choghadiya slots\n\n' +
      'summary_confidence = mean(anchors[].confidence), clamped to [0.0, 1.0].\n' +
      '  Returns 0.0 when no anchors exist for the requested horizon.\n\n' +
      'provenance_envelope:\n' +
      '  source: "phala.outlook"\n' +
      '  layers: ["PH-4-1", "PH-4-2", "PH-4-3", "PH-4-4"]\n' +
      '  layer_provenances: per-layer provenance from each sub-system\n' +
      '  computed_at: ISO UTC datetime\n\n' +
      'No new DB table — pure API aggregation layer over the 4 L4 sub-tools.\n' +
      'All 4 subsystems degrade gracefully: if a sub-system is unavailable,\n' +
      'its slot is returned as empty list / empty dict + an error provenance.\n\n' +
      'BRAHMA-PH-4-5 | phala.outlook contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return {
          content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }],
          isError: true,
        }
      }

      try {
        const result = await fetchPhalaOutlook(
          input.chart_id,
          input.horizon_months,
          { minConfidence: input.min_confidence }
        )

        // W3-L5 (budget unification, R-2 item 5 / W-8): migrated off the bare
        // applyResponseBudget call — that mechanism measures the trim BEFORE attaching
        // trim_report, so a response needing many trims could ship OVER budget once
        // trim_report's own bytes were added back in (the exact gap finalizeMcpBudget's
        // self-verifying re-measurement closes; see response_budget.ts's doc-comment).
        const budgeted = finalizeMcpBudget(result as unknown as Record<string, unknown>, {
          maxKb: PHALA_OUTLOOK_BUDGET_KB,
          sections: phalaOutlookSections() as unknown as TrimmableSection<Record<string, unknown>>[],
        })

        return {
          content: [
            {
              type: 'text' as const,
              // Compact, not pretty-printed — the budget mechanism measures compact bytes;
              // pretty-printing after trimming would ship larger than the declared ceiling.
              text: JSON.stringify(budgeted),
            },
          ],
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        // F-028: standardized error envelope { ok: false, error, tool }
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  ok: false,
                  error: message,
                  tool: TOOL_NAME,
                  asset: 'PH-4-5',
                  chart_id: input.chart_id,
                  horizon_months: input.horizon_months,
                  hint:
                    'Ensure all 4 L4 sub-systems are seeded: ' +
                    'PH-4-1 (phala_anchors), PH-4-2 (phala_mitigation), ' +
                    'PH-4-3 (phala_rectification), PH-4-4 (panchanga_daily). ' +
                    'Also verify DATABASE_URL and PYTHON_SIDECAR_URL are set.',
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        }
      }
    }
  )
}
