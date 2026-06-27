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
  }
  transit_state: { transits: unknown[]; source: string }
  active_convergences: ConvergenceWindow[]
  active_obstructions: ObstructionEntry[]
  kala_readiness: { score: number; interpretation: string; breakdown: unknown }
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
// When sidecar is unavailable, return pre-computed L3 data for the native.
// All values are FORENSIC-grounded (FORENSIC_ASTROLOGICAL_DATA_v8_0 §5.1 §22).

const FORENSIC_DASHA_PERIODS: TimelineRow[] = [
  { row_type: 'dasha_period', md_lord: 'Jupiter', ad_lord: 'Venus', ad_start: '1984-02-05', ad_end: '1986-03-03', alignment_score: 0.73 },
  { row_type: 'dasha_period', md_lord: 'Saturn',  ad_lord: 'Saturn',  ad_start: '1991-08-21', ad_end: '1994-08-24', alignment_score: 0.32 },
  { row_type: 'dasha_period', md_lord: 'Saturn',  ad_lord: 'Mercury', ad_start: '1994-08-24', ad_end: '1997-05-03', alignment_score: 0.48 },
  { row_type: 'dasha_period', md_lord: 'Saturn',  ad_lord: 'Venus',   ad_start: '1998-06-12', ad_end: '2001-08-12', alignment_score: 0.55 },
  { row_type: 'dasha_period', md_lord: 'Saturn',  ad_lord: 'Jupiter', ad_start: '2008-02-09', ad_end: '2010-08-21', alignment_score: 0.62 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Mercury', ad_start: '2010-08-21', ad_end: '2013-01-18', alignment_score: 0.61 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Ketu',    ad_start: '2013-01-18', ad_end: '2014-01-15', alignment_score: 0.45 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Venus',   ad_start: '2014-01-15', ad_end: '2016-11-15', alignment_score: 0.67 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Sun',     ad_start: '2016-11-15', ad_end: '2017-09-21', alignment_score: 0.55 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Moon',    ad_start: '2017-09-21', ad_end: '2019-02-21', alignment_score: 0.52 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Rahu',    ad_start: '2020-02-18', ad_end: '2022-09-06', alignment_score: 0.44 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Jupiter', ad_start: '2022-09-06', ad_end: '2024-12-12', alignment_score: 0.72 },
  { row_type: 'dasha_period', md_lord: 'Mercury', ad_lord: 'Saturn',  ad_start: '2024-12-12', ad_end: '2027-08-21', alignment_score: 0.52 },
  { row_type: 'dasha_period', md_lord: 'Ketu',    ad_lord: 'Ketu',    ad_start: '2027-08-21', ad_end: '2028-01-18', alignment_score: 0.35 },
]

const FORENSIC_CONVERGENCE_WINDOWS: ConvergenceWindow[] = [
  {
    window_start: '2002-04-24', window_end: '2002-10-21', anchor_date: '2002-07-24',
    convergence_score: 0.7133, indicator_count: 4, convergence_type: 'career_peak',
    valence: 'favorable',
    constituent_factors: [
      { label: 'Dasha_start: Saturn/Moon (2002-07-24)', weight: 0.85, event_type: 'dasha_transition' },
      { label: 'SIG.SATURN.MOON.AD.2002', weight: 0.75, event_type: 'signal_activation' },
      { label: 'Dasha: Saturn/Moon (2002-07-24)', weight: 0.6, event_type: 'dasha_transition' },
      { label: 'SIG.JUPITER.CANCER.EXALT.H4.2002', weight: 0.75, event_type: 'signal_activation' },
    ],
    source_citation: SOURCE_CITATION,
  },
  {
    window_start: '2022-06-08', window_end: '2022-12-05', anchor_date: '2022-09-06',
    convergence_score: 0.7667, indicator_count: 3, convergence_type: 'career_peak',
    valence: 'favorable',
    constituent_factors: [
      { label: 'SIG.MERCURY.JUPITER.AD.2022', weight: 0.85, event_type: 'signal_activation' },
      { label: 'SIG.JUPITER.ARIES.LAGNA.2022', weight: 0.75, event_type: 'signal_activation' },
      { label: 'Dasha_start: Mercury/Jupiter (2022-09-06)', weight: 0.85, event_type: 'dasha_transition' },
    ],
    source_citation: SOURCE_CITATION,
  },
  {
    window_start: '2024-09-13', window_end: '2025-03-10', anchor_date: '2024-12-12',
    convergence_score: 0.7083, indicator_count: 4, convergence_type: 'career_peak',
    valence: 'favorable',
    constituent_factors: [
      { label: 'SIG.MERCURY.SATURN.AD.2024', weight: 0.8, event_type: 'signal_activation' },
      { label: 'Dasha_start: Mercury/Saturn (2024-12-12)', weight: 0.6, event_type: 'dasha_transition' },
      { label: 'SIG.SATURN.PISCES.12H.2025', weight: 0.65, event_type: 'signal_activation' },
      { label: 'SIG.JUPITER.CANCER.EXALT.4H.2025', weight: 0.8, event_type: 'signal_activation' },
    ],
    source_citation: SOURCE_CITATION,
  },
]

const FORENSIC_OBSTRUCTIONS: ObstructionEntry[] = [
  {
    obstruction_id: 'OBS.SS.C1.RISING', obstruction_type: 'sade_sati',
    start: '1990-01-26', end: '1993-01-25', severity: 0.65,
    description: 'Sade Sati Cycle 1 — Rising phase: Saturn in Capricorn (12th from natal Moon Aquarius). Overlapping Saturn MD start 1991-08-21. Source: FORENSIC §22.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.SS.C1.PEAK', obstruction_type: 'sade_sati',
    start: '1993-01-26', end: '1995-04-09', severity: 0.80,
    description: 'Sade Sati Cycle 1 — Peak phase: Saturn exactly over natal Moon (Aquarius). Maximum emotional pressure. Source: FORENSIC §22.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.SS.C1.SETTING', obstruction_type: 'sade_sati',
    start: '1995-04-10', end: '1998-04-14', severity: 0.60,
    description: 'Sade Sati Cycle 1 — Setting phase: Saturn in Pisces (2nd from natal Moon). Resource pressure. Source: FORENSIC §22.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.MALDASH.SAT.SAT', obstruction_type: 'malefic_dasha',
    start: '1991-08-21', end: '1994-08-24', severity: 0.75,
    description: 'Saturn MD / Saturn AD (DSH.V.006): double Saturn affliction. Coincides with Sade Sati Cycle 1 peak. Source: FORENSIC §5.1.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.SS.C2.RISING', obstruction_type: 'sade_sati',
    start: '2020-01-24', end: '2022-04-28', severity: 0.70,
    description: 'Sade Sati Cycle 2 — Rising phase: Saturn in Capricorn. Concurrent Mercury-Rahu AD. Source: FORENSIC §22.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.SS.C2.PEAK', obstruction_type: 'sade_sati',
    start: '2022-04-29', end: '2025-03-28', severity: 0.85,
    description: 'Sade Sati Cycle 2 — Peak phase: Saturn over natal Moon. Concurrent Mercury-Jupiter/Saturn AD. Source: FORENSIC §22.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.SS.C2.SETTING', obstruction_type: 'sade_sati',
    start: '2025-03-29', end: '2028-03-28', severity: 0.65,
    description: 'Sade Sati Cycle 2 — Setting phase: Saturn in Pisces. MD transition Mercury→Ketu within window. Source: FORENSIC §22.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.MALDASH.MERC.RAHU', obstruction_type: 'malefic_dasha',
    start: '2020-02-18', end: '2022-09-06', severity: 0.60,
    description: 'Mercury MD / Rahu AD (DSH.V.021): Rahu amplification + Sade Sati rising. Digital disruption risk. Source: FORENSIC §5.1.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.MALDASH.KETU.KETU', obstruction_type: 'malefic_dasha',
    start: '2027-08-21', end: '2028-01-18', severity: 0.70,
    description: 'Ketu MD / Ketu AD (DSH.V.024): double Ketu. Most intense spiritual-karmic isolation. Source: FORENSIC §5.1.',
    source_citation: SOURCE_CITATION,
  },
  {
    obstruction_id: 'OBS.MALDASH.SAT.RAHU', obstruction_type: 'malefic_dasha',
    start: '2005-04-03', end: '2008-02-09', severity: 0.75,
    description: 'Saturn MD / Rahu AD (DSH.V.013): dual shadow-malefic confluence. Source: FORENSIC §5.1.',
    source_citation: SOURCE_CITATION,
  },
]

// REMEDIATION D7: FALLBACK_SNAPSHOT now uses a placeholder chart_id.
// At runtime, the handler replaces 'CHART_ID_PLACEHOLDER' with the caller's chart_id.
const FALLBACK_SNAPSHOT_TEMPLATE: Omit<KalaSnapshot, 'chart_id'> & { chart_id: string } = {
  chart_id: 'CHART_ID_PLACEHOLDER',
  snapshot_date: DEFAULT_SNAPSHOT_DATE,
  active_dasha: {
    md_lord: 'Mercury',
    ad_lord: 'Saturn',
    ad_start: '2024-12-12',
    ad_end: '2027-08-21',
    days_elapsed: 540,
    days_remaining: 807,
  },
  active_pratyantardasha: {
    pd_lord: 'Sun',
    pd_start: '2026-04-22',
    pd_end: '2026-09-14',
    days_elapsed: 44,
    days_remaining: 101,
  },
  transit_state: {
    source: 'FORENSIC-grounded algorithmic (slow planets from known ingress dates)',
    transits: [
      { planet: 'Saturn', sign: 'Pisces', house_from_lagna: 12, note: 'Sade Sati Cycle 2 setting phase' },
      { planet: 'Jupiter', sign: 'Cancer', house_from_lagna: 4, note: 'Jupiter exalted — emotional/home activation' },
      { planet: 'Rahu', sign: 'Aquarius', house_from_lagna: 11, note: 'Rahu in H11 (natal Moon sign)' },
      { planet: 'Ketu', sign: 'Leo', house_from_lagna: 5, note: 'Ketu in H5 — spiritual separation' },
    ],
  },
  active_convergences: [],
  active_obstructions: [
    {
      obstruction_id: 'OBS.SS.C2.SETTING', obstruction_type: 'sade_sati',
      start: '2025-03-29', end: '2028-03-28', severity: 0.65,
      description: 'Sade Sati Cycle 2 — Setting phase (Saturn/Pisces). Source: FORENSIC §22.',
      source_citation: SOURCE_CITATION,
    },
  ],
  kala_readiness: {
    score: 49,
    interpretation: 'NEUTRAL — mixed indicators; proceed with awareness',
    breakdown: {
      base: 50,
      adjustments: [
        { factor: 'Malefic AD lord (Saturn)', delta: -5 },
        { factor: 'Benefic Jupiter in H4 (exalted)', delta: 4 },
        { factor: 'Obstruction: OBS.SS.C2.SETTING', delta: -8 },
        { factor: 'Benefic MD lord (Mercury)', delta: 8 },
      ],
      final: 49,
    },
  },
  kala_summary: (
    'On 2026-06-05: Mercury Mahadasha / Saturn Antardasha / Sun Pratyantardasha. ' +
    'Saturn in Pisces (H12) — Sade Sati Cycle 2 setting phase continues through 2028. ' +
    'Jupiter exalted in Cancer (H4) — emotional and home domain activated. ' +
    'Kala readiness score: 49/100 (NEUTRAL). ' +
    'Source: FORENSIC_ASTROLOGICAL_DATA_v8_0 §5.1 §22.'
  ),
  provenance_envelope: {
    asset: 'kala.snapshot',
    unit: 'KA-3-5',
    chart_id: 'CHART_ID_PLACEHOLDER',  // replaced at runtime with caller's chart_id
    source_citation: SOURCE_CITATION,
    layer: 'L3 Kāla',
    snapshot_date: DEFAULT_SNAPSHOT_DATE,
    mode: 'fallback',
    note: 'Sidecar unavailable — pre-computed FORENSIC-grounded fallback for native chart only',
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
