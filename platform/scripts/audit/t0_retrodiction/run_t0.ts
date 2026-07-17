#!/usr/bin/env -S npx tsx
/**
 * run_t0.ts — D-3 Lane T-0 executable retrodiction-gate harness
 * (BRIEF_D3.md §F1 Lane T-0; BIND_D-3.md §B-3/DR-10/DR-11).
 *
 * Three checks against chart 482012f1's Life Event Log, scored against a
 * dasha-lord-confluence proxy curve (see lib/curve.ts header for the full
 * "what curve and why" — the D-3 transit kernel has not shipped, T-0 has
 * no dependency on it and builds first per the brief):
 *   (a) PEAK-PROXIMITY — 8L-Mars->2H loss mechanism peaks within ±45d of
 *       the 2025-05-15 loss/financial_deception event, top-decile of its
 *       own 5yr window.
 *   (b) WINDFALL — Venus+Jupiter dhana-yoga mechanism peaks within ±45d of
 *       the 2010-07-01 finance/family_windfall event, top-decile.
 *   (c) BLIND BATTERY — ≥50% hit-rate (±45d / top-tercile) across every
 *       LEL-scorable event (BIND_D-3 §B-3 exclusion rule, derived not
 *       asserted — see lib/lel.ts), scored above a shuffled-birth-proxy
 *       negative control (DR-11 anti-gaming rule).
 * Plus the §G anti-gaming pass: curve variance floor + top-decile-day-
 * fraction < 15%, applied to the (a)/(b) mechanism curves.
 *
 * Output: one JSON receipt to stdout — data over flags (CLAUDE.md §N.6):
 * every check reports the underlying numbers, not just a boolean. Exit 0
 * always (this harness measures and reports; it does not gate merge —
 * the wave's gate runner and Adjudicator make the pass/fail call per
 * CONDUCTOR_PROTOCOL §3 Phase 2). Non-zero exit is reserved for a genuine
 * run failure (bad credential, transport exhaustion).
 *
 * Credentials: same resolution order as
 * platform/scripts/audit/doctrine_harness/run.ts (not duplicated here as
 * a shared import to keep this harness's `may_touch` scope limited to its
 * own new directory — CONDUCTOR_PROTOCOL §3(d) scope-warden).
 *   1. --target already carries `?api_key=...`
 *   2. MARSYS_MCP_API_KEY env -> appended to --target/default as api_key
 *   3. MARSYS_MCP_KEY or MCP_SMOKE_BEARER_TOKEN env -> Authorization: Bearer
 */
import { McpClient } from '../doctrine_harness/lib/mcp_client'
import { fetchAllLelEvents, partitionScorable, type LelEvent } from './lib/lel'
import { fetchAllDashaPeriods, fetchDashaLordRatifications } from './lib/dasha_fetch'
import { buildCurve } from './lib/curve'
import { LOSS_SIGNIFICATORS, WINDFALL_SIGNIFICATORS, significatorsForCategory } from './lib/mechanisms'
import { scoreEvent, runBlindBattery, runShuffledControls, checkCurveNotDegenerate, PROXIMITY_DAYS } from './lib/checks'
import { parseDate } from './lib/dates'

const ABHISEK_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const DEFAULT_TARGET = 'https://amjis-mcp-qm256lasva-el.a.run.app/mcp'
const LOSS_EVENT_ID = 'd81fae4e-edf4-58d9-b201-cced7eae19d7' // loss/financial_deception 2025-05-15
const WINDFALL_EVENT_ID = 'bd7f5711-8668-5315-8e25-94dc94f2a101' // finance/family_windfall 2010-07-01
const BIRTH_DATE = '1984-02-05'
const HORIZON_END = '2034-12-31'
const SHUFFLE_COUNT = 7

function resolveClient(target: string): McpClient {
  if (target.includes('api_key=')) return new McpClient(target)
  const apiKey = process.env.MARSYS_MCP_API_KEY
  if (apiKey) {
    const sep = target.includes('?') ? '&' : '?'
    return new McpClient(`${target}${sep}api_key=${apiKey}`)
  }
  const bearer = process.env.MARSYS_MCP_KEY || process.env.MCP_SMOKE_BEARER_TOKEN
  if (bearer) return new McpClient(target, bearer)
  console.error(
    JSON.stringify({
      error: 'NO_CREDENTIAL',
      message: 'No MCP credential resolved. Pass --target with an embedded ?api_key=..., or set MARSYS_MCP_API_KEY / MARSYS_MCP_KEY / MCP_SMOKE_BEARER_TOKEN.',
    })
  )
  process.exit(2)
}

function parseArgs(argv: string[]): { target: string } {
  let target = DEFAULT_TARGET
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--target') target = argv[++i]
  }
  return { target }
}

async function main() {
  const { target } = parseArgs(process.argv.slice(2))
  const client = resolveClient(target)
  const boundsStart = parseDate(BIRTH_DATE)
  const boundsEnd = parseDate(HORIZON_END)

  // ── Substrate fetch ────────────────────────────────────────────────
  const [{ periods, total: dashaTotal, pagesFetched: dashaPages }, { events, expectedTotal, pagesFetched: lelPages }, ratifications] =
    await Promise.all([
      fetchAllDashaPeriods(client, ABHISEK_CHART_ID, AYANAMSHA, BIRTH_DATE, HORIZON_END),
      fetchAllLelEvents(client, ABHISEK_CHART_ID),
      fetchDashaLordRatifications(client, ABHISEK_CHART_ID),
    ])

  const { scorable, excluded } = partitionScorable(events)
  const lossEvent = events.find((e) => e.event_id === LOSS_EVENT_ID)
  const windfallEvent = events.find((e) => e.event_id === WINDFALL_EVENT_ID)

  const substrate = {
    lel_total_events_reported: expectedTotal,
    lel_events_collected: events.length,
    lel_pages_fetched: lelPages,
    lel_scorable_count: scorable.length,
    lel_excluded_count: excluded.length,
    lel_excluded: excluded.map((e) => ({ event_id: e.event_id, event_date: e.event_date, domain: e.domain, reasons: e.reasons })),
    dasha_periods_total_reported: dashaTotal,
    dasha_periods_collected: periods.length,
    dasha_pages_fetched: dashaPages,
    dasha_lord_ratifications_live: ratifications,
    scorable_rule: 'discrete-onset events with month-or-better date precision (BIND_D-3.md §B-3); birth anchor excluded; see lib/lel.ts VAGUENESS_PATTERNS for the exact heuristic applied per-row.',
  }

  // ── Check (a) PEAK-PROXIMITY ──────────────────────────────────────
  let checkA: unknown = { error: 'LOSS_EVENT_NOT_FOUND_IN_LEL', event_id: LOSS_EVENT_ID }
  let lossCurveAntiGaming: unknown = null
  if (lossEvent) {
    const eventDate = parseDate(lossEvent.event_date)
    const scoreA = scoreEvent(periods, LOSS_SIGNIFICATORS, lossEvent.event_id, eventDate, boundsStart, boundsEnd, 0.9)
    checkA = { ...scoreA, mechanism: '8L-Mars→2H wealth-loss (BRIEF_D3 §F0 DR-9)', significators: LOSS_SIGNIFICATORS }
    const halfMs = 2.5 * 365 * 86_400_000
    const s = new Date(Math.max(eventDate.getTime() - halfMs, boundsStart.getTime()))
    const e = new Date(Math.min(eventDate.getTime() + halfMs, boundsEnd.getTime()))
    const curve = buildCurve(periods, LOSS_SIGNIFICATORS, s, e, 5)
    lossCurveAntiGaming = checkCurveNotDegenerate(curve)
  }

  // ── Check (b) WINDFALL ─────────────────────────────────────────────
  let checkB: unknown = { error: 'WINDFALL_EVENT_NOT_FOUND_IN_LEL', event_id: WINDFALL_EVENT_ID }
  let windfallCurveAntiGaming: unknown = null
  if (windfallEvent) {
    const eventDate = parseDate(windfallEvent.event_date)
    const scoreB = scoreEvent(periods, WINDFALL_SIGNIFICATORS, windfallEvent.event_id, eventDate, boundsStart, boundsEnd, 0.9)
    checkB = { ...scoreB, mechanism: 'Venus+Jupiter dhana_yoga_2_5_9_11 (9th house)', significators: WINDFALL_SIGNIFICATORS }
    const halfMs = 2.5 * 365 * 86_400_000
    const s = new Date(Math.max(eventDate.getTime() - halfMs, boundsStart.getTime()))
    const e = new Date(Math.min(eventDate.getTime() + halfMs, boundsEnd.getTime()))
    const curve = buildCurve(periods, WINDFALL_SIGNIFICATORS, s, e, 5)
    windfallCurveAntiGaming = checkCurveNotDegenerate(curve)
  }

  // ── Check (c) BLIND BATTERY + shuffled-birth negative control ─────
  const blindInputs = scorable.map((e: LelEvent) => ({
    event_id: e.event_id,
    date: parseDate(e.event_date),
    significators: significatorsForCategory(e.category),
  }))
  const blindReal = runBlindBattery(periods, blindInputs, boundsStart, boundsEnd)
  const shuffled = runShuffledControls(periods, blindInputs, boundsStart, boundsEnd, SHUFFLE_COUNT)
  const shuffledMean = shuffled.reduce((s, r) => s + r.hit_rate, 0) / (shuffled.length || 1)
  const controlGap = blindReal.hit_rate - shuffledMean

  const checkC = {
    threshold_hit_rate: 0.5, // DR-11
    scored_count: blindReal.scored_count,
    hit_count: blindReal.hit_count,
    hit_rate: blindReal.hit_rate,
    meets_threshold: blindReal.hit_rate >= 0.5,
    lead_lag_distribution_days: blindReal.lead_lag_distribution,
    per_event: blindReal.per_event,
    shuffled_birth_control: { shifts: shuffled, mean_hit_rate: shuffledMean },
    control_gap: controlGap,
    beats_shuffled_control: controlGap > 0,
    pass: blindReal.hit_rate >= 0.5 && controlGap > 0,
  }

  const receipt = {
    harness: 't0_retrodiction_gate',
    wave: 'D-3',
    lane: 'T-0',
    chart_id: ABHISEK_CHART_ID,
    ayanamsha_id: AYANAMSHA,
    run_at: new Date().toISOString(),
    proximity_days: PROXIMITY_DAYS,
    substrate,
    check_a_peak_proximity: checkA,
    check_a_anti_gaming: lossCurveAntiGaming,
    check_b_windfall: checkB,
    check_b_anti_gaming: windfallCurveAntiGaming,
    check_c_blind_battery: checkC,
    note:
      'This receipt reports measurements, not a gate verdict — CONDUCTOR_PROTOCOL §1: the Implementer never verifies its own work. peak_basis on every score is dasha_lord_confluence_v1 (DR-10 interim proxy; NOT pratyantar_lord|midpoint_triangle|transit_kernel — those ship with T-2/T-3/T-6).',
  }

  console.log(JSON.stringify(receipt, null, 2))
  process.exit(0)
}

main().catch((err) => {
  console.error('t0_retrodiction_gate FATAL:', err)
  process.exit(1)
})
