/**
 * dasha_fetch.ts — network access for the T-0 harness's dasha-period
 * substrate (BRIEF_D3.md §F1 Lane T-0). Kept separate from curve.ts/
 * checks.ts (pure math) so those stay unit-testable without a live
 * connector — this module is exercised only by the live run.
 *
 * `ganita_dasha_periods_get` caps its response at ~40 rows per call
 * regardless of `limit` (byte-budget trim, not a row-count limit — verified
 * live 2026-07-17: a levels<=3, full-life-arc request reported
 * `total: 325` but `trim_report.kept_count: 40`). It DOES honor `offset`,
 * so this pages by offset until `offset >= total`, per §F3's "page to
 * exhaustion" Definition-of-DONE rule (same discipline lel.ts applies to
 * lel_query, which has no offset and needs a date-cursor instead).
 */
import type { McpClient } from '../../doctrine_harness/lib/mcp_client'
import { parseDate } from './dates'
import type { DashaPeriod } from './curve'

type DashaPeriodsResponse = {
  content?: {
    rows?: { level_n: number; lord_graha: string; start_date: string; end_date: string }[]
    total?: number
  }
}

const MAX_PAGES = 60

export async function fetchAllDashaPeriods(
  client: McpClient,
  chartId: string,
  ayanamshaId: string,
  windowStart: string,
  windowEnd: string
): Promise<{ periods: DashaPeriod[]; total: number | undefined; pagesFetched: number }> {
  const out: DashaPeriod[] = []
  let offset = 0
  let total: number | undefined
  let pages = 0

  for (; pages < MAX_PAGES; pages++) {
    const { content } = await client.callTool('ganita_dasha_periods_get', {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      window_start: windowStart,
      window_end: windowEnd,
      limit: 25000,
      offset,
      fields: 'compact',
    })
    const body = content as DashaPeriodsResponse
    const rows = body?.content?.rows ?? []
    if (total === undefined) total = body?.content?.total
    for (const r of rows) {
      out.push({ level: r.level_n, lord: r.lord_graha, start: parseDate(r.start_date), end: parseDate(r.end_date) })
    }
    if (rows.length === 0) break
    offset += rows.length
    if (total !== undefined && offset >= total) break
  }

  return { periods: out, total, pagesFetched: pages + 1 }
}

type DashaLordCapabilityResponse = {
  rows?: { lord: string; ratification_factor: number | null; ratification_domains: string[] }[]
}

/**
 * Returns { graha -> { domain -> ratification_factor } } from
 * `ganita_dasha_lord_capability_get` — the servable-today domain-to-karaka
 * mapping mechanisms.ts's DOMAIN_LORDS table documents (used here to
 * cross-check that table stays in sync with the live surface, not to
 * re-derive it at runtime — the constant is what the checks actually use,
 * per the brief asking for a documented, auditable curve construction).
 */
export async function fetchDashaLordRatifications(client: McpClient, chartId: string): Promise<Record<string, Record<string, number>>> {
  const { content } = await client.callTool('ganita_dasha_lord_capability_get', { chart_id: chartId })
  const body = content as DashaLordCapabilityResponse
  const out: Record<string, Record<string, number>> = {}
  for (const row of body.rows ?? []) {
    if (row.ratification_factor === null) continue
    for (const domain of row.ratification_domains) {
      out[row.lord] = out[row.lord] ?? {}
      out[row.lord][domain] = row.ratification_factor
    }
  }
  return out
}
