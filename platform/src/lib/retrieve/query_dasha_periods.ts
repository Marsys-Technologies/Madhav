/**
 * MARSYS-JIS Retrieval tool — query_dasha_periods (Phase 5A)
 *
 * Surgical dasha-schedule lookup. Reads chart_facts rows where category is
 * one of the three dasha categories (vimshottari / yogini / chara) and
 * value_json carries {md_lord, ad_lord, start_date, end_date}.
 *
 * 50 dasha_vimshottari rows (1984-02-05 → 2060-08-21). Coverage: Jupiter
 * MD (partial first) → Saturn MD → Mercury MD (current) → Ketu MD (next) →
 * Venus MD → Sun MD.
 *
 * Default empty params returns: today's active row (start_date <= today <
 * end_date) PLUS the next 3 MD-transition rows. This is the "what's my dasha
 * situation?" one-tool-call answer.
 *
 * Distinct from chart_facts_query: chart_facts_query handles 37 categories
 * including dasha; this tool is semantically dasha-only with helpers for
 * next_count / prev_count / active-chain shortcuts that the planner can
 * compose without needing date arithmetic.
 *
 * Distinct from temporal.dasha_context_required: that calls /dasha_chain
 * sidecar which returns the active 5-level chain at ONE date only. This
 * tool returns the schedule from the canonical chart_facts table, with
 * full upcoming + historical visibility.
 *
 * UDA-Q-S1: sub_level param ('pratyantar'|'sookshma') backported from MCP
 * quality version. Sub-periods computed via Vimshottari planet ratios
 * matching platform-mcp/src/tools/query_dasha_periods.ts implementation.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_dasha_periods'
const TOOL_VERSION = '1.1.0'

type DashaSystem = 'vimshottari' | 'yogini' | 'chara'
type DashaLevel = 'M' | 'A' | 'P' | 'all'

// ── Vimshottari constants (UDA-Q-S1) ─────────────────────────────────────────

/** Total Vimshottari cycle in years (used as divisor for sub-period ratios). */
const VIMSHOTTARI_TOTAL_YEARS = 120

/**
 * Canonical Vimshottari years per planet.
 * Order: Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, Venus.
 */
const VIMSHOTTARI_YEARS: Record<string, number> = {
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
const VIMSHOTTARI_SEQUENCE = [
  'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
  'Saturn', 'Mercury', 'Ketu', 'Venus',
]

// ── Sub-period computation helpers (UDA-Q-S1) ────────────────────────────────

interface SubPeriod {
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
 * planet whose index in VIMSHOTTARI_SEQUENCE follows (or equals) the AD lord.
 */
export function computePratyantar(
  adLord: string,
  adStartDate: string,
  adEndDate: string,
): SubPeriod[] {
  const adStart = new Date(adStartDate)
  const adEnd = new Date(adEndDate)
  const adDurationMs = adEnd.getTime() - adStart.getTime()

  const startIndex = VIMSHOTTARI_SEQUENCE.indexOf(adLord)
  // If unknown lord, start from 0
  const base = startIndex < 0 ? 0 : startIndex

  const sub: SubPeriod[] = []
  let cursor = adStart

  for (let i = 0; i < 9; i++) {
    const planet = VIMSHOTTARI_SEQUENCE[(base + i) % 9]!
    const ratio = (VIMSHOTTARI_YEARS[planet] ?? 0) / VIMSHOTTARI_TOTAL_YEARS
    const durationMs = adDurationMs * ratio
    const durationDays = Math.round(durationMs / 86_400_000)
    const periodEnd = new Date(cursor.getTime() + durationMs)

    sub.push({
      planet,
      start_date: cursor.toISOString().slice(0, 10),
      end_date: periodEnd.toISOString().slice(0, 10),
      duration_days: durationDays,
    })
    cursor = periodEnd
  }

  // Clamp last sub-period end to AD end to avoid floating-point drift
  if (sub.length > 0) {
    sub[sub.length - 1]!.end_date = adEndDate
    const lastStart = new Date(sub[sub.length - 1]!.start_date)
    sub[sub.length - 1]!.duration_days = Math.round(
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

const SYSTEM_CATEGORY: Record<DashaSystem, string> = {
  vimshottari: 'dasha_vimshottari',
  yogini: 'dasha_yogini',
  chara: 'dasha_chara',
}

export interface QueryDashaPeriodsInput {
  /** Defaults to 'vimshottari'. */
  system?: DashaSystem
  /** Default 'all'. 'M' deduplicates to one row per MD cluster (the AD row where ad_lord == md_lord). */
  level?: DashaLevel
  /**
   * Sub-period depth (UDA-Q-S1).
   * 'pratyantar' — each AD row in the response carries a sub_periods array of 9 PD rows.
   * 'sookshma'   — each AD row carries PD sub_periods, and each PD row carries 9 SD sub_periods.
   * Sub-periods are computed dynamically from Vimshottari planet ratios; they are not stored in DB.
   */
  sub_level?: 'pratyantar' | 'sookshma'
  /** ISO date (YYYY-MM-DD). Returns rows whose start_date <= d < end_date. */
  as_of_date?: string
  /** If set, returns next N MD-transition rows after as_of_date (or today). */
  next_count?: number
  /** If set, returns prev N MD-transition rows before as_of_date (or today). */
  prev_count?: number
  /** Filter to MD lord (canonical name; case-insensitive ILIKE). */
  md_lord?: string
  /** Filter to AD lord. */
  ad_lord?: string
  /** Range start — end_date >= from_date. */
  from_date?: string
  /** Range end — start_date <= to_date. */
  to_date?: string
  /** Max rows. Default 30, max 100. */
  limit?: number
}

interface DashaRow {
  fact_id: string
  category: string
  value_json: {
    md_lord: string
    ad_lord: string
    start_date: string
    end_date: string
  }
  source_section: string | null
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'CHART_FACTS_DASHA',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as QueryDashaPeriodsInput
  const system: DashaSystem = input.system ?? 'vimshottari'
  const category = SYSTEM_CATEGORY[system]
  const limit = Math.max(1, Math.min(100, input.limit ?? 30))
  const today = new Date().toISOString().slice(0, 10)

  const conditions: string[] = ['is_stale = false', 'category = $1']
  const args: unknown[] = [category]
  let idx = 2

  if (input.as_of_date) {
    conditions.push(
      `(value_json->>'start_date')::date <= $${idx}::date AND ` +
      `(value_json->>'end_date')::date > $${idx + 1}::date`
    )
    args.push(input.as_of_date, input.as_of_date)
    idx += 2
  }

  if (input.md_lord) {
    conditions.push(`value_json->>'md_lord' ILIKE $${idx}`)
    args.push(`%${input.md_lord}%`)
    idx++
  }

  if (input.ad_lord) {
    conditions.push(`value_json->>'ad_lord' ILIKE $${idx}`)
    args.push(`%${input.ad_lord}%`)
    idx++
  }

  // next_count / prev_count: anchor date filter
  let anchorDate: string | undefined
  if (input.from_date) {
    conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
    args.push(input.from_date)
    idx++
  } else if (input.next_count) {
    anchorDate = input.as_of_date ?? today
    conditions.push(`(value_json->>'start_date')::date >= $${idx}::date`)
    args.push(anchorDate)
    idx++
  } else if (input.prev_count) {
    anchorDate = input.as_of_date ?? today
    conditions.push(`(value_json->>'end_date')::date <= $${idx}::date`)
    args.push(anchorDate)
    idx++
  }

  if (input.to_date) {
    conditions.push(`(value_json->>'start_date')::date <= $${idx}::date`)
    args.push(input.to_date)
    idx++
  }

  // Default empty-params: return today's active row + next 3 MDs
  const isDefaultQuery =
    !input.as_of_date && !input.next_count && !input.prev_count &&
    !input.md_lord && !input.ad_lord && !input.from_date && !input.to_date

  if (isDefaultQuery) {
    // Add start_date >= (today - 1 year) as a loose lower bound to avoid returning
    // all historical rows; default will include today's active row + upcoming
    conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
    args.push(today)
    idx++
  }

  const orderDir = input.prev_count ? 'DESC' : 'ASC'
  let actualLimit = limit
  if (input.next_count) actualLimit = Math.min(limit, input.next_count * 9)
  if (input.prev_count) actualLimit = Math.min(limit, input.prev_count * 9)

  const sql = `
    SELECT fact_id, category, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY (value_json->>'start_date')::date ${orderDir}
    LIMIT ${actualLimit}
  `

  const storage = getStorageClient()
  const result = await storage.query<DashaRow>(sql, args)
  const rows = result.rows

  // Level='M' dedup: keep only the row where ad_lord == md_lord (MD-start row)
  let filteredRows = rows
  if (input.level === 'M') {
    const seenMd = new Set<string>()
    filteredRows = rows.filter(r => {
      if (r.value_json.ad_lord === r.value_json.md_lord) {
        const key = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
        if (seenMd.has(key)) return false
        seenMd.add(key)
        return true
      }
      return false
    })
  }

  // Cap next_count / prev_count to N MD clusters (each ~9 AD rows)
  if (input.next_count) {
    const clusters = new Set<string>()
    filteredRows = filteredRows.filter(r => {
      const k = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
      clusters.add(k)
      return clusters.size <= input.next_count!
    })
  }
  if (input.prev_count) {
    const clusters = new Set<string>()
    // rows are DESC; cap to prev_count clusters, then reverse for presentation
    const capped = filteredRows.filter(r => {
      const k = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
      clusters.add(k)
      return clusters.size <= input.prev_count!
    })
    filteredRows = capped.reverse()
  }

  // Build sub_periods enrichment if sub_level is set (UDA-Q-S1)
  const subLevel = input.sub_level

  const results: ToolBundleResult[] = filteredRows.length > 0
    ? filteredRows.map(r => {
        const baseRecord: Record<string, unknown> = {
          fact_id: r.fact_id,
          system,
          level: r.value_json.ad_lord === r.value_json.md_lord ? 'M_start' : 'A',
          md_lord: r.value_json.md_lord,
          ad_lord: r.value_json.ad_lord,
          start_date: r.value_json.start_date,
          end_date: r.value_json.end_date,
          source_section: r.source_section,
        }

        if (subLevel === 'pratyantar') {
          baseRecord['sub_periods'] = computePratyantar(
            r.value_json.ad_lord,
            r.value_json.start_date,
            r.value_json.end_date,
          )
        } else if (subLevel === 'sookshma') {
          const pdPeriods = computePratyantar(
            r.value_json.ad_lord,
            r.value_json.start_date,
            r.value_json.end_date,
          )
          baseRecord['sub_periods'] = pdPeriods.map(pd => ({
            ...pd,
            sub_periods: computeSookshma(pd.planet, pd.start_date, pd.end_date),
          }))
        }

        return {
          content: JSON.stringify(baseRecord),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 1.0,
        }
      })
    : [{
        content: JSON.stringify({
          note: `No ${category} rows match the given filters. Available date range: 1984-02-05 to 2060-08-21.`,
          params: input,
        }),
        source_canonical_id: 'CHART_FACTS_DASHA',
        source_version: '1.0',
        confidence: 0,
        significance: 0,
      }]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { ...input, system, limit: actualLimit },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as Record<string, unknown>,
    status: filteredRows.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: filteredRows.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'CHART_FACTS_DASHA',
    error_code: null,
    served_from_cache: false,
    fallback_used: filteredRows.length === 0,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Surgical Vimshottari / Yogini / Chara dasha schedule lookup. Reads ' +
    'chart_facts dasha rows (50 Vimshottari rows covering 1984-02-05 → ' +
    '2060-08-21) with semantic helpers for active-chain / next-N / prev-N / ' +
    "specific-lord queries. Default empty params returns today's active " +
    'row plus next 3 MDs.',
  retrieve,
}
