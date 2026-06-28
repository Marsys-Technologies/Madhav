/**
 * retrieval/kala_temporal.ts — BRAHMA-KA-3-COMPOSITE: kala.temporal composite L3 tool
 *
 * Composite MCP tool that wraps all L3 Kāla assets:
 *   KA-3-1 kala.timeline   — dasha×transit alignment series (l3_timeline.py)
 *   KA-3-2 kala.convergence — convergence windows (l3_convergence.py)
 *   KA-3-3 kala.obstruction — obstruction periods (l3_obstruction.py)
 *   KA-3-5 kala.snapshot    — point-in-time current Kala state (l3_snapshot.py)
 *
 * Input:
 *   {
 *     chart_id?: string,              // UUID (default: native)
 *     date_range?: { start: string, end: string }  // YYYY-MM-DD (optional)
 *     include_snapshot?: boolean,     // include kala.snapshot for today (default true)
 *   }
 *
 * Output:
 *   {
 *     timeline_excerpt:    [...],  // last 6 months + next 6 months of dasha×transit
 *     convergence_windows: [...],  // all convergence windows in range
 *     obstructions:        [...],  // all obstruction periods in range
 *     snapshot:            {...},  // current Kala state (if include_snapshot)
 *     provenance_envelope: {...}
 *   }
 *
 * This tool calls the Python sidecar for all L3 data. DB-primary with
 * algorithmic fallback (all sub-assets are self-contained Python modules).
 *
 * Wiring: registerKalaTemporalRetrievalTool(server) in server.ts
 * Note: kala_temporal.ts (in parent dir) registers the standalone `temporal` tool.
 *       This file registers `kala_temporal_bundle` for the retrieval/ layer.
 *
 * chart_id: required from caller — no default chart (chart_agnostic_gate RULE-1/4)
 *
 * BRAHMA-KA-3-COMPOSITE / l3-kala
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION = 'PyJHora/SwissEph DE441 + Brahma-L1'
// REMEDIATION D7: NATIVE_CHART_ID default removed. chart_id is now REQUIRED.
// chart_agnostic_gate RULE-1/RULE-4: no default on chart_id.
const PYTHON_SIDECAR_URL =
  process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
const DEFAULT_SNAPSHOT_DATE = '2026-06-05'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TimelineRow {
  row_type: 'dasha_period' | 'transit_overlap' | 'monthly_sample'
  md_lord: string
  ad_lord: string
  ad_start: string
  ad_end: string
  alignment_score: number
  [key: string]: unknown
}

export interface ConvergenceWindow {
  window_start: string
  window_end: string
  anchor_date: string
  convergence_score: number
  indicator_count: number
  convergence_type: string
  valence: 'favorable' | 'challenging'
  constituent_factors: unknown[]
  source_citation: string
}

export interface ObstructionEntry {
  obstruction_id: string
  obstruction_type: string
  start: string
  end: string
  severity: number
  description: string
  source_citation: string
}

export interface KalaSnapshot {
  chart_id: string
  snapshot_date: string
  active_dasha: {
    md_lord: string
    ad_lord: string
    ad_start: string
    ad_end: string
    days_elapsed: number
    days_remaining: number
  } | null
  active_pratyantardasha: {
    pd_lord: string
    pd_start: string
    pd_end: string
    days_elapsed: number
    days_remaining: number
  } | null
  transit_state: { transits: unknown[]; source: string }
  active_convergences: ConvergenceWindow[]
  active_obstructions: ObstructionEntry[]
  kala_readiness: { score: number | null; interpretation: string; breakdown: unknown | null }
  kala_summary: string
  provenance_envelope: Record<string, unknown>
}

export interface KalaTemporalBundle {
  timeline_excerpt: TimelineRow[]
  convergence_windows: ConvergenceWindow[]
  obstructions: ObstructionEntry[]
  snapshot: KalaSnapshot | null
  provenance_envelope: {
    source: string
    assets: string[]
    chart_id: string
    date_range: { start: string; end: string }
    computed_at: string
    source_citation: string
    timeline_count: number
    convergence_count: number
    obstruction_count: number
    snapshot_included: boolean
    sidecar_available: boolean
  }
}

// ── Sidecar fetch helpers ─────────────────────────────────────────────────────

async function fetchFromSidecar<T>(
  endpoint: string,
  params: Record<string, string | boolean | undefined>
): Promise<T | null> {
  try {
    const url = new URL(`${PYTHON_SIDECAR_URL}${endpoint}`)
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined) url.searchParams.set(k, String(v))
    })
    const res = await fetch(url.toString(), {
      signal: AbortSignal.timeout(8_000),
    })
    if (!res.ok) {
      return null
    }
    return (await res.json()) as T
  } catch {
    return null
  }
}

// ── Algorithmic fallback data ─────────────────────────────────────────────────
// REMEDIATION D7: native-specific FORENSIC data arrays REMOVED.
// When sidecar is unavailable, we return graceful-empty arrays for the requested chart.
// Returning native data for an arbitrary chart_id would be contamination.
// The sidecar is required for real data; these constants are now empty.
//
// Original note: data was FORENSIC-grounded (FORENSIC_ASTROLOGICAL_DATA_v8_0 §5.1 §22)
// for native chart 482012f1-... — NOT valid for any other chart.

// REMEDIATION D7: Removed native-chart-specific FORENSIC data arrays.
// These arrays contained dasha periods, convergence windows, and obstruction periods
// specific to chart 482012f1-... — returning them for any arbitrary chart_id would
// be cross-chart data contamination. Graceful-empty is the correct fallback.
const FORENSIC_DASHA_PERIODS: TimelineRow[] = []
const FORENSIC_CONVERGENCE_WINDOWS: ConvergenceWindow[] = []
const FORENSIC_OBSTRUCTIONS: ObstructionEntry[] = []

// REMEDIATION D7: FALLBACK_SNAPSHOT now uses a placeholder chart_id.
// At runtime, the handler replaces 'CHART_ID_PLACEHOLDER' with the caller's chart_id.
// REMEDIATION D7: FALLBACK_SNAPSHOT_TEMPLATE now contains graceful-empty data only.
// Native-specific dasha periods, obstruction data, and kala_summary were removed.
// The sidecar is the required data source; this template is returned only when unavailable.
const FALLBACK_SNAPSHOT_TEMPLATE: Omit<KalaSnapshot, 'chart_id'> & { chart_id: string } = {
  chart_id: 'CHART_ID_PLACEHOLDER',  // replaced at runtime with caller's chart_id
  snapshot_date: DEFAULT_SNAPSHOT_DATE,
  active_dasha: null,
  active_pratyantardasha: null,
  transit_state: {
    source: 'sidecar unavailable — no transit data',
    transits: [],
  },
  active_convergences: [],
  active_obstructions: [],
  kala_readiness: {
    score: null,
    interpretation: 'Sidecar unavailable — kala_readiness cannot be computed without live data',
    breakdown: null,
  },
  kala_summary: 'Sidecar unavailable. No Kāla data can be computed for this chart without the Python sidecar.',
  provenance_envelope: {
    asset: 'kala.snapshot',
    unit: 'KA-3-5',
    chart_id: 'CHART_ID_PLACEHOLDER',  // replaced at runtime with caller's chart_id
    source_citation: SOURCE_CITATION,
    layer: 'L3 Kāla',
    snapshot_date: DEFAULT_SNAPSHOT_DATE,
    mode: 'fallback_empty',
    note: 'Sidecar unavailable — graceful-empty response (native data removed by D7 remediation)',
  },
}

// ── Filter helpers ────────────────────────────────────────────────────────────

function filterByDateRange<T extends { start?: string; end?: string; ad_start?: string; ad_end?: string; window_start?: string; window_end?: string }>(
  items: T[],
  start: string,
  end: string
): T[] {
  return items.filter((item) => {
    const itemStart = item.start ?? item.ad_start ?? item.window_start ?? '1900-01-01'
    const itemEnd = item.end ?? item.ad_end ?? item.window_end ?? '2100-01-01'
    return itemEnd >= start && itemStart <= end
  })
}

// ── Core: computeKalaTemporalBundle ──────────────────────────────────────────

/**
 * Compute the composite L3 Kāla bundle for a chart and date range.
 *
 * Primary path: Python sidecar endpoints for each L3 asset.
 * Fallback: pre-computed FORENSIC-grounded data embedded in this file.
 */
export async function computeKalaTemporalBundle(
  chartId: string,
  dateRange: { start: string; end: string },
  includeSnapshot: boolean
): Promise<KalaTemporalBundle> {
  const { start, end } = dateRange
  const computedAt = new Date().toISOString()
  let sidecarAvailable = false

  // ── Attempt sidecar calls ─────────────────────────────────────────────────

  let timeline: TimelineRow[] = []
  let convergenceWindows: ConvergenceWindow[] = []
  let obstructions: ObstructionEntry[] = []
  let snapshot: KalaSnapshot | null = null

  // Try sidecar for timeline
  const timelineResp = await fetchFromSidecar<{ timeline: TimelineRow[] }>(
    '/kala/timeline',
    { chart_id: chartId, start, end, row_type: 'dasha_period' }
  )
  if (timelineResp?.timeline) {
    timeline = timelineResp.timeline
    sidecarAvailable = true
  }

  // Try sidecar for convergence
  const convResp = await fetchFromSidecar<{ windows: ConvergenceWindow[] }>(
    '/kala/convergence',
    { chart_id: chartId, start, end }
  )
  if (convResp?.windows) {
    convergenceWindows = convResp.windows
    sidecarAvailable = true
  }

  // Try sidecar for obstructions
  const obsResp = await fetchFromSidecar<{ obstructions: ObstructionEntry[] }>(
    '/kala/obstructions',
    { chart_id: chartId, start, end }
  )
  if (obsResp?.obstructions) {
    obstructions = obsResp.obstructions
    sidecarAvailable = true
  }

  // Try sidecar for snapshot
  if (includeSnapshot) {
    const snapResp = await fetchFromSidecar<KalaSnapshot>(
      '/kala/snapshot',
      { chart_id: chartId, as_of_date: DEFAULT_SNAPSHOT_DATE }
    )
    if (snapResp?.active_dasha) {
      snapshot = snapResp
      sidecarAvailable = true
    }
  }

  // ── Fallback: embedded FORENSIC-grounded data (sidecar unavailable) ─────
  // Used when the sidecar is unavailable for any chart. Callers should retry
  // with the sidecar available for full live data.
  if (timeline.length === 0) {
    timeline = filterByDateRange(FORENSIC_DASHA_PERIODS, start, end)
  }
  if (convergenceWindows.length === 0) {
    convergenceWindows = filterByDateRange(FORENSIC_CONVERGENCE_WINDOWS, start, end)
  }
  if (obstructions.length === 0) {
    obstructions = filterByDateRange(FORENSIC_OBSTRUCTIONS, start, end)
  }
  if (includeSnapshot && snapshot === null) {
    // REMEDIATION D7: replace CHART_ID_PLACEHOLDER with actual caller's chart_id
    snapshot = {
      ...FALLBACK_SNAPSHOT_TEMPLATE,
      chart_id: chartId,
      provenance_envelope: {
        ...FALLBACK_SNAPSHOT_TEMPLATE.provenance_envelope,
        chart_id: chartId,
      },
    }
  }

  return {
    timeline_excerpt: timeline,
    convergence_windows: convergenceWindows,
    obstructions,
    snapshot: includeSnapshot ? snapshot : null,
    provenance_envelope: {
      source: 'kala.temporal_bundle',
      assets: ['kala.timeline', 'kala.convergence', 'kala.obstruction', 'kala.snapshot'],
      chart_id: chartId,
      date_range: { start, end },
      computed_at: computedAt,
      source_citation: SOURCE_CITATION,
      timeline_count: timeline.length,
      convergence_count: convergenceWindows.length,
      obstruction_count: obstructions.length,
      snapshot_included: includeSnapshot,
      sidecar_available: sidecarAvailable,
    },
  }
}

// ── Input schema ──────────────────────────────────────────────────────────────

// REMEDIATION D7: chart_id is now REQUIRED (no .default(), no ?? NATIVE_CHART_ID).
// chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
// chart_agnostic_gate RULE-3: native identifiers removed from description.
// chart_agnostic_gate RULE-4: no default on chart_id field.
// chart_agnostic_gate RULE-5: no native UUID in chart_id description.
const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to compute Kāla temporal bundle for. Required — no default chart.'
    ),

  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('Start date YYYY-MM-DD'),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('End date YYYY-MM-DD'),
    })
    .optional()
    .describe(
      'Date range for the temporal bundle (default: 6 months before + after current date). ' +
        'For a full life arc, pass the chart subject\'s birth year through 2040-12-31.'
    ),

  include_snapshot: z
    .boolean()
    .default(true)
    .describe(
      'Include the point-in-time kala.snapshot for the current date. ' +
        'Default true — always include for current Kala state.'
    ),
})

// ── Tool description ──────────────────────────────────────────────────────────

const TOOL_NAME = 'kala_temporal_bundle'

// REMEDIATION D7 (RULE-3): native identifiers removed from LLM-visible description.
const TOOL_DESCRIPTION = `\
What it does: Returns the composite L3 Kāla temporal bundle — all four L3 Kāla assets \
in one call for a given chart UUID:
  • kala.timeline    (KA-3-1) — dasha×transit alignment rows (MD/AD periods with alignment scores)
  • kala.convergence (KA-3-2) — convergence windows (3+ indicators aligned within 90 days)
  • kala.obstruction (KA-3-3) — obstruction periods (Sade Sati, malefic dashas, double affliction)
  • kala.snapshot    (KA-3-5) — current Kala state (MD/AD/PD + transits + kala_readiness score)

Output shape:
  {
    timeline_excerpt:    [...],  // dasha-period rows with alignment_score
    convergence_windows: [...],  // convergence clusters (score, type, factors)
    obstructions:        [...],  // obstruction periods (severity, type, description)
    snapshot:            {...},  // current Kala state (kala_readiness.score 0-100)
    provenance_envelope: {...}
  }

When to use: Use for any temporal or predictive query about a chart (<chart_uuid>). \
Pair with holistic_bundle for the full picture — holistic_bundle provides the L2 natal \
signal layer; kala_temporal_bundle provides the L3 temporal animation layer.

Requires: chart_id (UUID) — must be provided by caller. No default chart.

BRAHMA-KA-3-COMPOSITE | kala.temporal_bundle retrieval tool.`

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the kala_temporal_bundle retrieval tool on an McpServer instance.
 *
 * Called from server.ts during the BRAHMA L3 Kāla registration phase.
 *
 * Example:
 *   import { registerKalaTemporalRetrievalTool } from './tools/retrieval/kala_temporal.js'
 *   registerKalaTemporalRetrievalTool(server)
 */
export function registerKalaTemporalRetrievalTool(server: McpServer): void {
  server.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {
    const input = InputSchema.parse(params)

    // Default date range: 6 months before + 6 months after DEFAULT_SNAPSHOT_DATE
    const dateRange = input.date_range ?? {
      start: '2025-12-05', // 6 months before 2026-06-05
      end: '2026-12-05',   // 6 months after
    }

    try {
      const result = await computeKalaTemporalBundle(
        input.chart_id,
        dateRange,
        input.include_snapshot
      )

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(result, null, 2),
          },
        ],
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(
              {
                error: true,
                tool: TOOL_NAME,
                message,
                chart_id: input.chart_id,
                date_range: dateRange,
                provenance_envelope: {
                  source: 'kala.temporal_bundle',
                  source_citation: SOURCE_CITATION,
                  computed_at: new Date().toISOString(),
                },
              },
              null,
              2
            ),
          },
        ],
        isError: true,
      }
    }
  })
}
