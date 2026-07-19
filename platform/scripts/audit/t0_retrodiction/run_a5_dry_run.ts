#!/usr/bin/env -S npx tsx
/**
 * run_a5_dry_run.ts — D-4a Lane A-5 harness dry-run (gate lane, BRIEF_D4A.md §F1
 * Lane A-5). Scores midpoint-triangle, pratyantar-lord, and
 * transit-kernel-on-repaired-substrate through Lane A-3's scoring harness
 * (`lib/a3_scoring_harness/*`, used here strictly as a BLACK BOX — this
 * script imports it and does not modify a single line of its scoring logic)
 * against the full DR-13-shaped LEL corpus for chart 482012f1.
 *
 * ============================================================================
 * THESE ARE DIAGNOSTIC SCORES ONLY. This dry-run is explicitly NOT the DR-12
 * model adjudication ruling (DIS.025) — that determination is reserved for
 * wave D-4b. Do not cite the numbers this script produces as a model-
 * comparison verdict; a model scoring worse here is not "losing" anything.
 * ============================================================================
 *
 * Methodology (event set, exclusions, domain/significator resolution,
 * bounds, params, controls) is PRE-REGISTERED in
 * artifacts/D-4a/A-5/PREREGISTRATION_v1_0.md, committed in an earlier commit
 * than this script, per DIS.028/DR-15(d). This script implements that
 * document; it does not invent new methodology at run time.
 *
 * Sealed test-split discipline: this script only READS `life_events` (and
 * `chart_dashas`, a build artifact, not the LEL itself) — no write path
 * exists anywhere in this file.
 *
 * Run with (from platform/): node_modules/.bin/tsx --env-file=.env.local
 *   scripts/audit/t0_retrodiction/run_a5_dry_run.ts
 * (DATABASE_URL must be set — see platform/.env.local.example. `node --import
 * tsx/esm` hits Node 24's ERR_REQUIRE_CYCLE_MODULE on this repo's `pg` +
 * path-alias setup, same pre-existing quirk documented in
 * scripts/d4a/file_baseline_predictions.mts's header — the tsx CLI binary
 * avoids it.)
 */
import { Pool } from 'pg'
import { pratyantarLordModel, midpointTriangleModel, transitKernelModel, NotImplementedModelError, type ChartContext, type TemporalCurveModel } from './lib/a3_scoring_harness/model_interface'
import { runMirroredScoringHarness, type MirroredScoringParams, type HarnessResult } from './lib/a3_scoring_harness/harness'
import type { CurveEvent, EventShape, DateConfidence } from './lib/a3_scoring_harness/shape_scoring'
import type { DashaPeriod } from './lib/curve'
import { DOMAIN_LORDS, domainForCategory } from './lib/mechanisms'
import { parseDate } from './lib/dates'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const BOUNDS_START = parseDate('1984-02-05')
const BOUNDS_END = parseDate('2030-12-31')

// ── §3.1 pre-registered exclusions (PREREGISTRATION_v1_0.md) ─────────────
const EXCLUDED_EVENT_IDS = new Set<string>([
  '5d039007-0244-58c6-ad39-152c179c6ac8', // birth anchor (epoch_tautology)
  '5278d97c-e769-529a-b0c2-be1e965c2d6b', // A-4 synthetic test fixture, explicitly marked non-real
  '3e96c6da-3ad6-5329-a40b-0b9240a1cbdb', // superseded by -corr-congenital
  '8573c0ca-9fc5-52a0-8309-f1b324a51d4a', // superseded by -corr-day-lock
  '56a1222d-8c88-5445-b2a2-1fd89d470719', // superseded by -corr-2021-04
  '021e49f5-9c6a-5e0e-ad6c-84c8ea2ad83f', // superseded by -corr-2022-07-14
  '3e96c6da-3ad6-5329-a40b-0b9240a1cbdb-corr-congenital', // psychological_arc.congenital_onset kill-switch
])

// ── §6 pre-registered harness params ──────────────────────────────────────
const PARAMS: MirroredScoringParams = { percentile: 0.9, shuffleCount: 7, includeSecondaryBattery: true }

type LifeEventRow = {
  event_id: string
  event_date: string
  category: string
  domain: string
  description: string
  shape: EventShape
  date_confidence: DateConfidence
  interval_start: string | null
  interval_end: string | null
  chain_parent_event_id: string | null
}

async function fetchLifeEvents(pool: Pool): Promise<LifeEventRow[]> {
  const { rows } = await pool.query<LifeEventRow>(
    `SELECT event_id, to_char(event_date,'YYYY-MM-DD') AS event_date, category, domain, description,
            shape, date_confidence,
            to_char(interval_start,'YYYY-MM-DD') AS interval_start,
            to_char(interval_end,'YYYY-MM-DD') AS interval_end,
            chain_parent_event_id
     FROM life_events
     WHERE chart_id = $1
     ORDER BY event_date ASC`,
    [CHART_ID]
  )
  return rows
}

async function fetchDashaPeriods(pool: Pool): Promise<DashaPeriod[]> {
  const { rows } = await pool.query<{ level_n: number; lord_graha: string; start_date: string; end_date: string }>(
    `SELECT level_n, lord_graha, to_char(start_date,'YYYY-MM-DD') AS start_date, to_char(end_date,'YYYY-MM-DD') AS end_date
     FROM chart_dashas
     WHERE chart_id = $1 AND system_id = 'vimshottari' AND ayanamsha_id = $2 AND level_n <= 4
     ORDER BY level_n, start_date`,
    [CHART_ID, AYANAMSHA]
  )
  return rows.map((r) => ({ level: r.level_n, lord: r.lord_graha, start: parseDate(r.start_date), end: parseDate(r.end_date) }))
}

function toCurveEvent(row: LifeEventRow): CurveEvent {
  const base: CurveEvent = { eventId: row.event_id, shape: row.shape, dateConfidence: row.date_confidence }
  if (row.shape === 'interval') {
    return { ...base, intervalStart: parseDate(row.interval_start!), intervalEnd: parseDate(row.interval_end!) }
  }
  // shape === 'point' (no 'chain'-shaped rows exist in the live corpus — §3.4)
  return { ...base, eventDate: parseDate(row.event_date) }
}

type DomainGroup = { domain: string; events: CurveEvent[]; sourceEventIds: string[] }

function groupByDomain(rows: LifeEventRow[]): DomainGroup[] {
  const byDomain = new Map<string, CurveEvent[]>()
  const idsByDomain = new Map<string, string[]>()
  for (const row of rows) {
    if (EXCLUDED_EVENT_IDS.has(row.event_id)) continue
    const domain = domainForCategory(row.category)
    if (!byDomain.has(domain)) {
      byDomain.set(domain, [])
      idsByDomain.set(domain, [])
    }
    byDomain.get(domain)!.push(toCurveEvent(row))
    idsByDomain.get(domain)!.push(row.event_id)
  }
  return [...byDomain.entries()].map(([domain, events]) => ({ domain, events, sourceEventIds: idsByDomain.get(domain)! }))
}

type ModelRunResult =
  | { modelId: string; status: 'scored'; perDomain: HarnessResult[] }
  | { modelId: string; status: 'gap'; reason: string }

function runModel(model: TemporalCurveModel, chart: ChartContext, groups: DomainGroup[]): ModelRunResult {
  try {
    const perDomain = groups.map((g) =>
      runMirroredScoringHarness({
        model,
        chart,
        eventClass: g.domain,
        events: g.events,
        boundsStart: BOUNDS_START,
        boundsEnd: BOUNDS_END,
        params: PARAMS,
      })
    )
    return { modelId: model.modelId, status: 'scored', perDomain }
  } catch (err) {
    if (err instanceof NotImplementedModelError) {
      return { modelId: model.modelId, status: 'gap', reason: err.message }
    }
    throw err // a genuine, unexpected harness failure is NOT swallowed as a gap — halt class 3
  }
}

async function main() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  try {
    const [lifeEvents, periods] = await Promise.all([fetchLifeEvents(pool), fetchDashaPeriods(pool)])
    const groups = groupByDomain(lifeEvents)
    const scoredEventCount = groups.reduce((s, g) => s + g.events.length, 0)

    const chart: ChartContext = { chartId: CHART_ID, ayanamsha: AYANAMSHA, substrate: { periods } }

    const eventClassSignificators = DOMAIN_LORDS // §4: domain == eventClass in this run, reusing T-0/A-3's live-verified map
    const models: TemporalCurveModel[] = [pratyantarLordModel(eventClassSignificators), midpointTriangleModel(), transitKernelModel()]

    const results = models.map((m) => runModel(m, chart, groups))

    const receipt = {
      DISCLAIMER:
        'These are DIAGNOSTIC scores only. This dry-run is explicitly NOT the DR-12 model adjudication ruling (DIS.025) — that determination is reserved for wave D-4b. Do not cite these numbers as a model-comparison verdict.',
      harness: 'd4a_a5_dry_run',
      wave: 'D-4a',
      lane: 'A-5',
      preregistration: 'artifacts/D-4a/A-5/PREREGISTRATION_v1_0.md (committed before this run — DIS.028/DR-15(d))',
      chart_id: CHART_ID,
      ayanamsha_id: AYANAMSHA,
      run_at: new Date().toISOString(),
      bounds: { start: '1984-02-05', end: '2030-12-31' },
      params: PARAMS,
      substrate: {
        life_events_total_rows: lifeEvents.length,
        excluded_rows: [...EXCLUDED_EVENT_IDS],
        scorable_event_count: scoredEventCount,
        dasha_periods_loaded: periods.length,
        domain_groups: groups.map((g) => ({ domain: g.domain, event_count: g.events.length, event_ids: g.sourceEventIds })),
      },
      models: results.map((r) =>
        r.status === 'scored'
          ? { model_id: r.modelId, status: r.status, per_domain: r.perDomain }
          : { model_id: r.modelId, status: r.status, reason: r.reason }
      ),
      note:
        'peak_basis for the pratyantar_lord model is dasha_lord_confluence_v1 (DR-10 interim proxy, mirroring T-0). midpoint_triangle and transit_kernel are pre-registered-expected gaps (PREREGISTRATION_v1_0.md §2) — no curve() implementation exists in the codebase for either, independent of substrate quality. This receipt reports measurements, not a gate verdict.',
    }

    console.log(JSON.stringify(receipt, null, 2))
  } finally {
    await pool.end()
  }
}

main().catch((err) => {
  console.error('d4a_a5_dry_run FATAL:', err)
  process.exit(1)
})
