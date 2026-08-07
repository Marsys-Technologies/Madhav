/**
 * tools/kala_views/dasha_sandhi.ts — ṢAḌ-DARŚANA W3, Item 1-full
 * (SHAD_DARSHANA_BRIEF_v2_0.md §1 item 1, §3 W3)
 *
 * Daśā-sandhi calendar — ALL levels (Mahādaśā → Antardaśā → Pratyantardaśā →
 * Sūkṣmadaśā), BOTH directions (past N years + future N years from as_of date).
 *
 * ── WHAT THIS MODULE DOES ─────────────────────────────────────────────────────
 * A JOIN, not a new computation (CLAUDE.md §N.5/B.10). It reads the existing
 * chart_dashas table via `marsys://tool/L1/get_dashas` (the L1 Gaṇita layer's
 * authoritative dasha surface), extracts period START and END dates (= sandhi
 * boundaries), filters to the bilateral window [as_of - past_years, as_of +
 * future_years], and returns them with their level / lord / kind annotations.
 *
 * No new migration required — chart_dashas is an existing L1 asset.
 * No new astrological computation — sandhi dates ARE the already-computed
 * start_date/end_date values from that table.
 *
 * ── WHY A DEDICATED TOOL (not just `ganita_dashas_get`) ──────────────────────
 * `ganita_dashas_get` (marsys://tool/L1/get_dashas) serves the raw period rows
 * with all their factual fields. Item 1 is a CONSUMING-LLM-friendly calendar
 * surface that:
 *   (a) flattens each period into TWO boundary rows (start + end), labelled
 *       `period_start` / `period_end`, so a consuming LLM can reason about
 *       daśā junctions without parsing both dates out of one row;
 *   (b) applies a BILATERAL WINDOW across the full level hierarchy — the raw
 *       tool is unwindowed-by-default and windowed-single-direction-by-default;
 *   (c) flags which boundaries are NEAR `as_of` (the is_near_as_of field, a
 *       direct serving-layer annotation over existing data, same pattern as
 *       now.ts's `is_now_within_band` on dasha_sandhi W1-lite);
 *   (d) provides explicit provenance (authority_note naming chart_dashas) per
 *       §N.5 and KALA_SUPREME_ELEVATION_v1_0.md §2 C1 / item 44.
 *
 * ── TILING GUARANTEE ─────────────────────────────────────────────────────────
 * The brief's mandatory property test: "sandhi intervals tile with no gaps/
 * overlaps — every millisecond in the horizon belongs to exactly one daśā
 * period at each level." This property is a contract of the L1 writer (the
 * chart_dashas build), not something this serving layer re-derives. The test
 * in kala_dasha_sandhi_get_w3.test.ts asserts it at the serving layer by
 * checking that consecutive periods share the exact same boundary date —
 * serving this data verbatim (§N.5) preserves the guarantee end-to-end.
 *
 * ── ACCURACY STANDARD (≥3 anchors) ──────────────────────────────────────────
 * The mandatory accuracy anchors verified by the test suite:
 *   ANCHOR 1: Ju MD start date 2019-02-07 (served verbatim from chart_dashas)
 *   ANCHOR 2: Ju/Ve AD end date 2026-10-02 (served verbatim from chart_dashas)
 *   ANCHOR 3: Pratyantar Ra start date 2026-08-12 (served verbatim)
 * These are §N.5-clean: the boundary dates come from L1, not from this module.
 *
 * CONFORMS TO CLAUDE.md §N.5 / B.10:
 * - dasha_source = 'marsys://tool/L1/get_dashas' (single temporal authority)
 * - authority_note = 'chart_dashas — L1 Gaṇita layer build artifact'
 * - no value re-derived here; all dates are verbatim from the source rows
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import {
  computedCoverage,
  honestEmptyCoverage,
  type KalaCoverageEntry,
} from '../../lib/kala_envelope.js'

// ── Infrastructure (self-contained proxy helper — same pattern as now.ts) ──────
const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistry(
  uri: string,
  args: Record<string, unknown>,
  principal: Principal,
): Promise<unknown> {
  const resp = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!resp.ok) throw new Error(`registry ${uri} returned HTTP ${resp.status}`)
  const payload = (await resp.json()) as { ok: boolean; content: unknown; error?: string }
  if (!payload.ok) throw new Error(`registry ${uri} returned error: ${payload.error ?? 'unknown'}`)
  return payload.content
}

// ── Types ─────────────────────────────────────────────────────────────────────

/** A single daśā-sandhi boundary: either the START or END of one period. */
export interface SandhiBoundary {
  /** The unique daśā period row-id from chart_dashas (verbatim). */
  period_id: string
  /** Vimśottarī level: 1=Mahādaśā, 2=Antardaśā, 3=Pratyantardaśā, 4=Sūkṣmadaśā */
  level_n: number
  /** Human-readable level name verbatim from chart_dashas. */
  level_name: string
  /** Dasha system id (e.g. 'vimshottari'). */
  system_id: string
  /** Lord graha abbreviation (e.g. 'JU', 'VE', 'SA'). */
  lord_graha: string
  /** ISO date of this boundary (YYYY-MM-DD) — verbatim from chart_dashas start_date or end_date. */
  boundary_date: string
  /** Whether this is the START or END of the period. */
  boundary_kind: 'period_start' | 'period_end'
  /** True when boundary_date is within NEAR_DAYS of the as_of date. */
  is_near_as_of: boolean
}

/** Result shape for computeDashaSandhiCalendar. */
export interface DashaSandhiCalendarResult {
  /** All period boundaries (start + end) within the bilateral horizon. */
  boundaries: SandhiBoundary[]
  /** ISO date of the query's as_of. */
  as_of: string
  /** Bilateral window start (as_of minus past_years). */
  horizon_start: string
  /** Bilateral window end (as_of plus future_years). */
  horizon_end: string
  /** Coverage entries per §N.6 / B.10 discipline. */
  coverage: KalaCoverageEntry[]
  /** Provenance — naming the L1 authority per §N.5 / item 44. */
  provenance: {
    dasha_source: string
    authority_note: string
  }
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** Boundaries within this many days of as_of are flagged is_near_as_of=true. */
const NEAR_DAYS = 30

const DASHA_SOURCE = 'marsys://tool/L1/get_dashas'
const AUTHORITY_NOTE = 'chart_dashas — L1 Gaṇita layer build artifact'

// ── Horizon helpers ───────────────────────────────────────────────────────────

function addYearsIso(isoDate: string, years: number): string {
  const d = new Date(isoDate + 'T00:00:00Z')
  // Simple year arithmetic; Feb-29 falls back to Feb-28 on non-leap target years
  const target = new Date(d)
  target.setUTCFullYear(target.getUTCFullYear() + years)
  // If the result overflowed (e.g. Feb 29 -> Feb 30), Date normalises to March 1.
  // The setUTCFullYear path is safe for ±years arithmetic on YYYY-MM-DD strings.
  return target.toISOString().slice(0, 10)
}

function daysBetween(dateA: string, dateB: string): number {
  const a = new Date(dateA + 'T00:00:00Z').getTime()
  const b = new Date(dateB + 'T00:00:00Z').getTime()
  return Math.abs((b - a) / (24 * 60 * 60 * 1000))
}

// ── Core logic ────────────────────────────────────────────────────────────────

/**
 * Fetch raw dasha rows from L1 via the existing `get_dashas` capability, then
 * project them into the SandhiBoundary calendar shape.
 *
 * §N.5 / B.10: every boundary date is verbatim from the source row; this
 * function performs NO astronomical re-derivation.
 */
async function fetchDashaRows(
  chartId: string,
  windowStart: string,
  windowEnd: string,
  principal: Principal,
): Promise<{ rows: Record<string, unknown>[]; reachable: boolean }> {
  try {
    const data = (await callRegistry(DASHA_SOURCE, {
      chart_id: chartId,
      // Returning all levels across the bilateral window.
      // ayanamsha_id NOT filtered here so we get all systems — the billing is
      // on the serving layer to decide which system to surface; default = vimshottari
      // (the system parameter on get_dashas defaults to 'vimshottari').
      all_levels: true,
      window_start: windowStart,
      window_end: windowEnd,
      fields: 'compact',
      limit: 2000,  // sufficient for a ±5y window even at Sūkṣma level
    }, principal)) as { rows: Record<string, unknown>[]; total: number }
    return { rows: Array.isArray(data.rows) ? data.rows : [], reachable: true }
  } catch {
    return { rows: [], reachable: false }
  }
}

/**
 * Turn a flat list of period rows into a bilateral boundary list.
 *
 * Each period row → 2 boundary rows (period_start + period_end), each filtered
 * to the [horizonStart, horizonEnd] window (a boundary outside the window is
 * excluded — but the PERIOD is still fetched because overlapping-period windows
 * are the correct way to find all boundary dates within the window).
 */
function buildBoundaries(
  rows: Record<string, unknown>[],
  horizonStart: string,
  horizonEnd: string,
  asOf: string,
): SandhiBoundary[] {
  const out: SandhiBoundary[] = []
  for (const row of rows) {
    const periodId = String(row['dasha_row_id'] ?? '')
    const levelN = Number(row['level_n'] ?? 0)
    const levelName = String(row['level_name'] ?? String(row['level_n'] ?? ''))
    const systemId = String(row['system_id'] ?? 'vimshottari')
    const lord = String(row['lord_graha'] ?? '')
    const startDate = String(row['start_date'] ?? '')
    const endDate = String(row['end_date'] ?? '')

    if (!periodId || !levelN || !lord || !startDate || !endDate) continue

    // Each period contributes boundary rows for whichever of its start/end dates
    // falls within the bilateral horizon. A boundary outside the window is omitted
    // (§B.10 / honest-empty: we serve what the window covers, not what it doesn't).
    // The L1 get_dashas window_start/window_end filter returns OVERLAPPING periods,
    // so a period may contribute only its end boundary (started before the window)
    // or only its start boundary (ends after the window) — both are valid.
    for (const [boundaryDate, kind] of [
      [startDate, 'period_start' as const],
      [endDate, 'period_end' as const],
    ] as [string, 'period_start' | 'period_end'][]) {
      // Only include boundaries within the bilateral horizon
      if (boundaryDate < horizonStart || boundaryDate > horizonEnd) continue
      out.push({
        period_id: periodId,
        level_n: levelN,
        level_name: levelName,
        system_id: systemId,
        lord_graha: lord,
        boundary_date: boundaryDate,
        boundary_kind: kind,
        is_near_as_of: daysBetween(boundaryDate, asOf) <= NEAR_DAYS,
      })
    }
  }
  // Sort ascending by boundary date, then by level (finer levels after coarser)
  out.sort((a, b) =>
    a.boundary_date.localeCompare(b.boundary_date) || a.level_n - b.level_n,
  )
  return out
}

// ── Public surface ────────────────────────────────────────────────────────────

/**
 * Compute the full daśā-sandhi calendar for a chart across all dasha levels,
 * in both directions (past N years + future N years from as_of).
 *
 * This is the implementation of SHAD_DARSHANA_BRIEF_v2_0.md item 1-full (W3).
 * It reads chart_dashas via `marsys://tool/L1/get_dashas` and projects period
 * boundaries into the SandhiBoundary shape. No new computation (§N.5 / B.10).
 */
export async function computeDashaSandhiCalendar(
  chartId: string,
  params: {
    as_of?: string
    past_years?: number
    future_years?: number
  },
  _principal: Principal,
): Promise<DashaSandhiCalendarResult> {
  const asOf = params.as_of ?? new Date().toISOString().slice(0, 10)
  const pastYears = Math.max(0, Math.min(params.past_years ?? 5, 50))
  const futureYears = Math.max(0, Math.min(params.future_years ?? 5, 50))

  const horizonStart = addYearsIso(asOf, -pastYears)
  const horizonEnd = addYearsIso(asOf, futureYears)

  const { rows, reachable } = await fetchDashaRows(chartId, horizonStart, horizonEnd, _principal)

  if (!reachable) {
    return {
      boundaries: [],
      as_of: asOf,
      horizon_start: horizonStart,
      horizon_end: horizonEnd,
      coverage: [
        honestEmptyCoverage(
          'dasha_sandhi_calendar',
          'L1 dasha registry (marsys://tool/L1/get_dashas) could not be dispatched this call.',
        ),
      ],
      provenance: { dasha_source: DASHA_SOURCE, authority_note: AUTHORITY_NOTE },
    }
  }

  if (rows.length === 0) {
    return {
      boundaries: [],
      as_of: asOf,
      horizon_start: horizonStart,
      horizon_end: horizonEnd,
      coverage: [
        honestEmptyCoverage(
          'dasha_sandhi_calendar',
          `no dasha rows returned for chart ${chartId} in window ${horizonStart}..${horizonEnd} — chart may not have L1 data built yet.`,
        ),
      ],
      provenance: { dasha_source: DASHA_SOURCE, authority_note: AUTHORITY_NOTE },
    }
  }

  const boundaries = buildBoundaries(rows, horizonStart, horizonEnd, asOf)

  return {
    boundaries,
    as_of: asOf,
    horizon_start: horizonStart,
    horizon_end: horizonEnd,
    coverage: [computedCoverage('dasha_sandhi_calendar')],
    provenance: { dasha_source: DASHA_SOURCE, authority_note: AUTHORITY_NOTE },
  }
}

// ── MCP tool registration ─────────────────────────────────────────────────────

/**
 * Register `kala_dasha_sandhi_get` on the MCP server.
 *
 * This is the W3-full implementation of daśā-sandhi calendar delivery —
 * all levels, both directions. The W1-lite surface (sandhi bands around
 * the ACTIVE periods only) lives in tools/kala_views/now.ts as the
 * `dasha_sandhi` field on `kala_now_get`.
 */
export function registerDashaSandhiCalendar(server: McpServer): void {
  server.tool(
    'kala_dasha_sandhi_get',
    'Daśā-sandhi (period-junction) calendar for a chart, at ALL dasha levels ' +
      '(Mahādaśā → Antardaśā → Pratyantardaśā → Sūkṣmadaśā), across a BILATERAL ' +
      'time window (past N years + future N years from as_of). ' +
      'Each period boundary (daśā-sandhi = the moment one period ends and the next begins) ' +
      'is a served row with level, lord, date, and direction label. ' +
      'Source: L1 chart_dashas table via marsys://tool/L1/get_dashas — §N.5 JOIN, ' +
      'no re-derivation. Use this to answer "what daśā junctions have I recently passed ' +
      'through, and which are coming?" across the full period hierarchy. ' +
      'ṢAḌ-DARŚANA W3, item 1-full (SHAD_DARSHANA_BRIEF_v2_0.md §1).',
    {
      chart_id: z.string().describe('Chart UUID (required — never defaulted).'),
      as_of: z
        .string()
        .optional()
        .describe('ISO date (YYYY-MM-DD) for the bilateral window anchor. Defaults to today.'),
      past_years: z
        .number()
        .optional()
        .describe('Years before as_of to include. Default 5; max 50.'),
      future_years: z
        .number()
        .optional()
        .describe('Years after as_of to include. Default 5; max 50.'),
    },
    async (args) => {
      // Tool context does not provide a Principal in the MCP SDK handler signature;
      // we pass a minimal placeholder matching the pattern used across this codebase.
      const principal: Principal = { user_uid: 'system', key_id: 'system', role: 'super_admin' }
      try {
        const result = await computeDashaSandhiCalendar(
          args.chart_id as string,
          {
            as_of: args.as_of as string | undefined,
            past_years: args.past_years as number | undefined,
            future_years: args.future_years as number | undefined,
          },
          principal,
        )
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
          isError: false,
        }
      } catch (err) {
        return {
          content: [{ type: 'text', text: `kala_dasha_sandhi_get error: ${String(err)}` }],
          isError: true,
        }
      }
    },
  )
}
