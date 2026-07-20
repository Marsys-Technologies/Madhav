/**
 * lel.ts — Life Event Log access for the T-0 retrodiction-gate harness
 * (BRIEF_D3.md §F1 Lane T-0 / BIND_D-3.md §B-3).
 *
 * Two responsibilities, kept separate and independently unit-testable:
 *   1. `fetchAllLelEvents` — pages `lel_query` to EXHAUSTION. BIND_D-3.md
 *      confirmed live (2026-07-17) that the deployed connector caps a page
 *      at 50 rows regardless of the `limit` argument, and that a second
 *      event dated exactly on the last page's cutoff date can be hidden
 *      behind that cut (two 2025-07-01 events on 482012f1; a naive
 *      single-page read missed `a95552d7` — health/chronic_resolution).
 *      `lel_query` exposes no `offset` param, only `date_from`/`date_to`,
 *      so pagination is a date cursor: re-issue with `date_from` = the
 *      max event_date seen so far (inclusive, to catch same-day
 *      duplicates), dedupe by `event_id`, and stop when a pass adds no
 *      new events (§F3 Definition-of-DONE: "no absence claim from a
 *      truncated page — page to exhaustion or use an authoritative total").
 *   2. `isScorable` — BIND_D-3.md §B-3's exclusion rule, applied here
 *      exactly as it must be documented in the harness output (not
 *      asserted): "discrete-onset events with month-or-better date
 *      precision". The LEL server stores one event_date per row with no
 *      precision metadata, so this is approximated from the free-text
 *      `description` for the vagueness cues the LEL corpus visibly uses
 *      when only a year (or less) was known at intake (multi-phase arcs,
 *      "~YYYY", "circa", a bare "around YYYY" with no month, an explicit
 *      N-year span, "or" between two months). This is a documented
 *      heuristic, not a claim of ground truth — the harness reports the
 *      excluded list alongside the scorable count so the rule is
 *      auditable, per §F3's "derived, not asserted" instruction.
 */
import type { McpClient } from '../../doctrine_harness/lib/mcp_client'

export type LelEvent = {
  event_id: string
  event_date: string
  category: string
  domain: string
  description: string
  event_type: string
  // LEL schema v2 (D-4a Lane A-1, DR-13/DIS.026) — additive, optional here
  // because the server may not yet serve these columns on every deployment
  // and every pre-v2 row is implicitly shape='point'/date_confidence='exact'
  // per the migration's own column defaults. Do not assume presence.
  shape?: 'point' | 'interval' | 'chain'
  date_confidence?: 'exact' | 'month_known' | 'year_only'
  interval_start?: string
  interval_end?: string
  chain_parent_event_id?: string
  milestone_label?: string
}

type LelQueryResponse = {
  ok?: boolean
  events?: LelEvent[]
  total_count?: number
}

const PAGE_LIMIT = 200 // server hard-caps the actual page at 50 regardless of this
const MAX_PAGES = 40 // guard against an infinite loop if the cursor ever fails to advance

/**
 * Pages `lel_query` to exhaustion via a date_from cursor (no server-side
 * offset exists). Returns every distinct event_id, deduplicated, sorted by
 * event_date ascending. `expectedTotal` (from the first unfiltered call's
 * `total_count` — the only call where that field reflects the WHOLE
 * corpus, not the filtered subset) is reported for cross-checking, not
 * trusted blindly as a loop-exit condition on its own.
 */
export async function fetchAllLelEvents(
  client: McpClient,
  chartId: string
): Promise<{ events: LelEvent[]; expectedTotal: number | undefined; pagesFetched: number }> {
  const seen = new Map<string, LelEvent>()
  let dateFrom: string | undefined
  let expectedTotal: number | undefined
  let pages = 0

  for (; pages < MAX_PAGES; pages++) {
    const args: Record<string, unknown> = { chart_id: chartId, limit: PAGE_LIMIT }
    if (dateFrom) args.date_from = dateFrom
    const { content } = await client.callTool('lel_query', args)
    const body = content as LelQueryResponse
    const events = body.events ?? []
    if (pages === 0) expectedTotal = body.total_count

    let newCount = 0
    let maxDateThisPage: string | undefined
    for (const e of events) {
      if (!seen.has(e.event_id)) {
        seen.set(e.event_id, e)
        newCount++
      }
      if (!maxDateThisPage || e.event_date > maxDateThisPage) maxDateThisPage = e.event_date
    }

    if (events.length === 0) break // nothing left at all
    if (newCount === 0) break // this page added nothing new — cursor has stalled, stop
    if (maxDateThisPage === dateFrom && newCount === 0) break // defensive, same as above
    dateFrom = maxDateThisPage
    if (expectedTotal !== undefined && seen.size >= expectedTotal) break
  }

  const events = [...seen.values()].sort((a, b) => (a.event_date < b.event_date ? -1 : a.event_date > b.event_date ? 1 : 0))
  return { events, expectedTotal, pagesFetched: pages + 1 }
}

const VAGUENESS_PATTERNS: { label: string; re: RegExp }[] = [
  { label: 'phase_marker', re: /\bphase\s*\d/i },
  { label: 'arc_marker', re: /\barc\b/i },
  { label: 'multi_year_marker', re: /\bmulti-?year\b/i },
  { label: 'ongoing_marker', re: /\bongoing\b/i },
  { label: 'resurfaced_marker', re: /\bresurfaced\b/i },
  { label: 'persisted_n_years', re: /\bpersist(ed)?\s+~?\d+\s*years?\b/i },
  { label: 'tilde_year', re: /~\s*\d{4}/ },
  { label: 'circa', re: /\bcirca\b/i },
  { label: 'approximately', re: /\bapproximately\b/i },
  { label: 'bare_around_year', re: /\baround\s+\d{4}\b/i }, // "around 2010" (no month) — "around March 2001" does NOT match (month intervenes)
  { label: 'month_or_month', re: /\b[A-Z][a-z]+\s+or\s+[A-Z][a-z]+\s+\d{4}\b/ }, // "June or July 2009"
  { label: 'year_span_years', re: /\b\d+-\d+\s*years?\b/i }, // "7-10 years"
  { label: 'paren_year_range', re: /\(~?\d{4}-\d{4}\)/ }, // "(~2001-2004)" / "(1995-2006)"
]

export type ScorabilityVerdict = {
  event_id: string
  scorable: boolean
  reasons: string[] // vagueness markers matched, or [] if scorable
}

/**
 * BIND_D-3.md §B-3 exclusion rule: "scorable = discrete-onset events with
 * month-or-better date precision". The birth-anchor row (event_type='other',
 * domain='other/birth') is never scorable — it anchors the chart, it is not
 * an outcome to retrodict. Every other event is scorable unless its
 * description trips one of the documented vagueness markers above.
 */
export function classifyScorability(event: LelEvent): ScorabilityVerdict {
  if (event.domain === 'other/birth') {
    return { event_id: event.event_id, scorable: false, reasons: ['birth_anchor_not_an_outcome'] }
  }
  const reasons = VAGUENESS_PATTERNS.filter((p) => p.re.test(event.description)).map((p) => p.label)
  return { event_id: event.event_id, scorable: reasons.length === 0, reasons }
}

export function partitionScorable(events: LelEvent[]): { scorable: LelEvent[]; excluded: (LelEvent & { reasons: string[] })[] } {
  const scorable: LelEvent[] = []
  const excluded: (LelEvent & { reasons: string[] })[] = []
  for (const e of events) {
    const v = classifyScorability(e)
    if (v.scorable) scorable.push(e)
    else excluded.push({ ...e, reasons: v.reasons })
  }
  return { scorable, excluded }
}
