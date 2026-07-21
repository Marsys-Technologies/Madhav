#!/usr/bin/env -S npx tsx
/**
 * b1_driver.ts — B-1 Grand Bakeoff, NARROWED contender set, TRAIN-only
 * (pre-2020-01-01) scoring pass. Ad-hoc driver script for this dispatch —
 * NOT a committed harness artifact — wired against the REAL, merged
 * a3_scoring_harness modules (roster.ts, roster_bind.ts, harness.ts,
 * shape_scoring.ts, proper_scoring.ts, model_interface.ts,
 * permission_model.ts, ensemble_model.ts), no reimplementation.
 *
 * Scope: 13 evaluable contenders (pratyantar_lord + 12 PERMISSION
 * standalone system-generators) + the hierarchical ensemble (14 total),
 * against the TRAIN-eligible subset of D4B_PREREGISTRATION_PACKET_v1_0.md
 * v1.2's committed event set — every row with date < 2020-01-01 (the
 * sealed test split boundary, ESCALATION_POLICY_v1_0.md §4). Chain
 * milestones and open-ended intervals whose true date/bound crosses the
 * boundary are excluded or capped at 2019-12-31 (documented judgment call,
 * see train_events.json header note in the calling session's report).
 *
 * N=1000 coverage-matched shuffled-birth control shifts per NP-D4B-004.
 * CRPS/skill = primary (DR-15(b)); hit-rate (±45d/±75d top-decile) =
 * legacy secondary. DR-17 graded scale is NOT computed here (no existing
 * implementation in the harness — see calling session's report).
 */
import { readFileSync, writeFileSync } from 'node:fs'
import type { ChartContext, EventClass, TemporalCurveModel } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-bakeoff-narrowed/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { buildActiveRoster, buildActiveRosterWithEnsemble } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-bakeoff-narrowed/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/roster'
import { assertRosterBindable, RosterBindFailureError } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-bakeoff-narrowed/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/roster_bind'
import { runMirroredScoringHarness, type MirroredScoringParams } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-bakeoff-narrowed/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/harness'
import type { CurveEvent, DateConfidence, EventShape } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-bakeoff-narrowed/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/shape_scoring'
import { hierarchicalEnsembleModel } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-bakeoff-narrowed/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/ensemble_model'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const SIDECAR_URL = process.env.PYTHON_SIDECAR_URL || 'https://amjis-sidecar-938361928218.asia-south1.run.app'
const API_KEY = process.env.PYTHON_SIDECAR_API_KEY || ''
const SCRATCH = '/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/cb8619fb-b398-41cc-a7e7-6cc6c9eafb53/scratchpad'

// ── DOMAIN_LORDS / domainForCategory, carried verbatim from mechanisms.ts (T-0, live-verified 2026-07-17) ──
const DOMAIN_LORDS: Record<string, Record<string, number>> = {
  wealth: { Jupiter: 1.0, Saturn: 0.8, Venus: 1.0 },
  career: { Saturn: 0.8 },
  health: { Mercury: 1.0 },
  marriage: { Venus: 1.0 },
  general: { Mars: 1.0, Sun: 1.0 },
}
const CATEGORY_TO_DOMAIN: Record<string, string> = {
  finance: 'wealth', loss: 'wealth', career: 'career', health: 'health',
  psychological: 'health', relationship: 'marriage', family: 'marriage',
  education: 'general', creative: 'general', spiritual: 'general',
  travel: 'general', other: 'general', 'residential+travel': 'general',
}
function significatorsForCategory(category: string): Record<string, number> {
  return DOMAIN_LORDS[CATEGORY_TO_DOMAIN[category] ?? 'general'] ?? DOMAIN_LORDS.general
}

type RawEvent = {
  eventId: string; category: string; shape: EventShape; dateConfidence: DateConfidence
  eventDate?: string; intervalStart?: string; intervalEnd?: string
}

function toCurveEvent(r: RawEvent): CurveEvent {
  return {
    eventId: r.eventId, shape: r.shape, dateConfidence: r.dateConfidence,
    eventDate: r.eventDate ? new Date(r.eventDate + 'T00:00:00Z') : undefined,
    intervalStart: r.intervalStart ? new Date(r.intervalStart + 'T00:00:00Z') : undefined,
    intervalEnd: r.intervalEnd ? new Date(r.intervalEnd + 'T00:00:00Z') : undefined,
  }
}

function rangeForEvent(r: RawEvent): [Date, Date] {
  // Trimmed buffers (compute-budget judgment call, disclosed in the session
  // report): enough room either side of the tolerance band (DR-13(d): exact
  // ±45d, month ±75d, year_only -> secondary battery) for a genuine local-max
  // search, without ballooning server-side point counts on the live sidecar.
  const bufDays = r.dateConfidence === 'year_only' ? 150 : r.dateConfidence === 'month_known' ? 90 : 60
  const bufMs = bufDays * 86_400_000
  if (r.shape === 'interval') {
    const s = new Date(r.intervalStart! + 'T00:00:00Z').getTime()
    const e = new Date(r.intervalEnd! + 'T00:00:00Z').getTime()
    return [new Date(s - bufMs), new Date(Math.min(e + bufMs, Date.parse('2019-12-31T23:59:59Z')))]
  }
  const t = new Date(r.eventDate! + 'T00:00:00Z').getTime()
  return [new Date(t - bufMs), new Date(Math.min(t + bufMs, Date.parse('2019-12-31T23:59:59Z')))]
}

async function main() {
  const events: RawEvent[] = JSON.parse(readFileSync(`${SCRATCH}/train_events.json`, 'utf8'))
  const periodsRaw: { level_n: number; lord_graha: string; start_date: string; end_date: string }[] = JSON.parse(
    readFileSync(`${SCRATCH}/vimshottari_periods_train.json`, 'utf8')
  )
  const periods = periodsRaw.map((p) => ({ level: p.level_n, lord: p.lord_graha, start: new Date(p.start_date), end: new Date(p.end_date) }))

  const eventClassSignificators: Record<EventClass, Record<string, number>> = {}
  for (const e of events) eventClassSignificators[e.category] = significatorsForCategory(e.category)

  const chart: ChartContext = { chartId: CHART_ID, ayanamsha: AYANAMSHA, substrate: { periods } }
  // stepDays MUST match pratyantar_lord's own hardcoded grid (5 -- see
  // model_interface.ts's pratyantarLordModel, buildCurve(...,5)) or
  // hierarchicalEnsembleModel's own EnsembleGridMismatchError correctly
  // refuses to run (verified live this session -- widening to 15 tripped it
  // exactly as designed). Kept at the route's own default (5) for grid
  // alignment; speed comes from parallelizing the 12 permission binds
  // instead (see the Promise.all below), not from a coarser grid.
  const opts = { sidecarUrl: SIDECAR_URL, apiKey: API_KEY, stepDays: 5 }

  const roster = buildActiveRoster(eventClassSignificators, opts) // 13
  const ensemble = hierarchicalEnsembleModel(roster) // 14th
  const fullRoster: TemporalCurveModel[] = [...roster, ensemble]

  // ── §1: BIND-TIME ASSERTION (literal first action before any scoring) ──
  console.error('[b1_driver] running assertRosterBindable() probe...')
  const probeRange: [Date, Date] = [new Date('2007-01-01T00:00:00Z'), new Date('2007-06-01T00:00:00Z')]
  try {
    const report = await assertRosterBindable(fullRoster, chart, 'career', probeRange)
    console.error('[b1_driver] BIND-TIME ASSERTION PASSED for', report.length, 'contenders:', JSON.stringify(report))
  } catch (err) {
    if (err instanceof RosterBindFailureError) {
      console.error('[b1_driver] BIND-TIME ASSERTION FAILED:', JSON.stringify(err.failures, null, 2))
      writeFileSync(`${SCRATCH}/b1_bind_failure.json`, JSON.stringify({ failed: true, failures: err.failures }, null, 2))
      process.exit(1)
    }
    throw err
  }

  // ── §2: per-event, per-model scoring (CRPS primary + hit-rate secondary) ──
  const params: MirroredScoringParams = { percentile: 0.9, shuffleCount: 1000, includeSecondaryBattery: true }
  const results: Record<string, any[]> = {}
  let eventIdx = 0
  for (const raw of events) {
    eventIdx++
    const range = rangeForEvent(raw)
    const eventClass = raw.category
    const curveEvent = toCurveEvent(raw)
    console.error(`[b1_driver] event ${eventIdx}/${events.length} ${raw.eventId} (${eventClass}) range=${range[0].toISOString().slice(0,10)}..${range[1].toISOString().slice(0,10)}`)
    // Bind the 13 base contenders IN PARALLEL (driver-level orchestration
    // choice, not a harness-code change: ensemble_model.ts's own bind()
    // chains sequentially, which serializes 12 real HTTP round-trips per
    // event against the live sidecar). ensemble.curve() then reads the
    // now-populated caches synchronously -- no separate ensemble.bind() call
    // needed once its constituents are bound for this exact triple.
    const t0 = Date.now()
    await Promise.all(roster.map((m) => m.bind?.(chart, eventClass, range)))
    console.error(`[b1_driver]   bound ${roster.length} base contenders in ${Date.now() - t0}ms`)
    for (const model of fullRoster) {
      try {
        const r = runMirroredScoringHarness({ model, chart, eventClass, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
        results[model.modelId] = results[model.modelId] || []
        results[model.modelId].push({ eventId: raw.eventId, eventClass, range: [range[0].toISOString(), range[1].toISOString()], result: r })
      } catch (err) {
        results[model.modelId] = results[model.modelId] || []
        results[model.modelId].push({ eventId: raw.eventId, eventClass, error: err instanceof Error ? `${err.name}: ${err.message}` : String(err) })
      }
    }
    writeFileSync(`${SCRATCH}/b1_results_raw.json`, JSON.stringify(results, null, 2))
    writeFileSync(`${SCRATCH}/b1_progress.json`, JSON.stringify({ eventsDone: eventIdx, eventsTotal: events.length }, null, 2))
  }

  console.error('[b1_driver] DONE. Wrote', `${SCRATCH}/b1_results_raw.json`)
}

main().catch((err) => {
  console.error('[b1_driver] FATAL:', err)
  process.exit(1)
})
