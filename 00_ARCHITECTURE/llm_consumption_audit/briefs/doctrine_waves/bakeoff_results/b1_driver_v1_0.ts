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
 *
 * ── F-1 FIX (2026-07-22, wave/D-4b/F1-resonance-map) ────────────────────
 * This run's original `event_class` value for every PERMISSION-system bind/
 * curve call was `raw.category` (a raw `life_events.category` string like
 * "family"/"finance"/"career") passed straight through — this essentially
 * never matches a `gochara_resonance_map.event_class` row, degrading all 12
 * PERMISSION contenders to the sidecar's fallback path SILENTLY
 * (`B1_NARROWED_STATUS_v1_0.md` §5a; `REPORT_D4B.md` §0). Fixed: every
 * event's REAL resonance-map `event_class` is now resolved via
 * `event_class_resolution.ts`'s `resolveEventClass()` (evidence-cited,
 * `life_events.domain`-driven — see that module's own docstring for the
 * full defect/disposition writeup), and a live `assertEventClassCoverage()`
 * pass runs BEFORE any scoring and writes a run-header disclosing, per
 * event, whether it resolved to a POPULATED class or is UNRESOLVED (task
 * item c — "no silent gaps"). `pratyantar_lord`'s own significator lookup
 * is UNCHANGED (it is keyed by raw category via `CATEGORY_TO_DOMAIN`, an
 * independent mechanism that was never the bug — see that block below).
 * For an event whose class does not resolve to a populated row, the 12
 * PERMISSION contenders + the hierarchical ensemble are SKIPPED for that
 * event (not silently scored against a degraded fallback curve) —
 * `pratyantar_lord` alone is still scored, since it does not depend on
 * `gochara_resonance_map` at all.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import type { ChartContext, EventClass, TemporalCurveModel } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { buildActiveRoster, buildActiveRosterWithEnsemble } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/roster'
import { assertRosterBindable, RosterBindFailureError } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/roster_bind'
import { runMirroredScoringHarness, type MirroredScoringParams } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/harness'
import type { CurveEvent, DateConfidence, EventShape } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/shape_scoring'
import { hierarchicalEnsembleModel } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/ensemble_model'
import {
  assertEventClassCoverage,
  type RawEventForResolution,
  type EventClassCoverageReport,
} from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/event_class_resolution'
// NOTE (F-1 fix): this script lives outside platform/, so a bare `import
// 'pg'` cannot resolve (Node walks up from the IMPORTING FILE's own
// directory looking for node_modules, never finds platform/node_modules
// from here) -- the same reason the original driver never imported any npm
// package directly and instead read pre-fetched substrate from SCRATCH JSON
// files (train_events.json, vimshottari_periods_train.json). The live
// gochara_resonance_map read follows that SAME established pattern: run
// `platform/scripts/audit/t0_retrodiction/fetch_populated_event_classes.ts`
// (a real, committed, platform-resident script -- 'pg' resolves fine there)
// FIRST to produce `${SCRATCH}/populated_event_classes.json`, then this
// driver reads it. `assertEventClassCoverage()` itself (imported above) is
// pure/DB-free by design (see event_class_resolution.ts) -- only the LIVE
// fetch needed relocating.

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
  /** life_events.domain — REQUIRED for F-1's event_class_resolution.ts to
   * resolve this event against gochara_resonance_map's populated classes.
   * (F-1 fix, 2026-07-22: the original driver never carried this field and
   * passed raw.category straight through as event_class — see module
   * docstring below and event_class_resolution.ts's own docstring for the
   * full defect + disposition writeup.) */
  domain?: string
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

  // ── F-1: live event-class coverage assertion, BEFORE any scoring ──────
  // Never a hardcoded "3 classes" literal -- `populated_event_classes.json`
  // is produced by `fetch_populated_event_classes.ts` querying
  // gochara_resonance_map live (see that script + the NOTE above this
  // driver's imports for why the DB read itself lives there, not here).
  const populatedLive: string[] = JSON.parse(readFileSync(`${SCRATCH}/populated_event_classes.json`, 'utf8'))
  const forResolution: RawEventForResolution[] = events.map((e) => ({ eventId: e.eventId, category: e.category, domain: e.domain }))
  const coverage: EventClassCoverageReport = assertEventClassCoverage(CHART_ID, forResolution, populatedLive)
  const resolvedByEventId = new Map(coverage.entries.map((e) => [e.eventId, e]))
  console.error(
    `[b1_driver] F-1 coverage: ${coverage.resolvedAndPopulatedCount}/${coverage.entries.length} events resolve to a ` +
      `populated gochara_resonance_map class (live: ${coverage.populatedEventClassesLive.join(', ')}); ` +
      `${coverage.unresolvedCount} UNRESOLVED (PERMISSION contenders skipped for those, pratyantar_lord still scored) -- see run header.`
  )
  writeFileSync(`${SCRATCH}/b1_run_header_f1.json`, JSON.stringify({
    fix: 'F-1 (wave/D-4b/F1-resonance-map) -- event_class now resolved via event_class_resolution.ts, not raw.category passthrough',
    chart_id: CHART_ID,
    generated_at: new Date().toISOString(),
    populated_event_classes_live: coverage.populatedEventClassesLive,
    resolved_and_populated_count: coverage.resolvedAndPopulatedCount,
    unresolved_count: coverage.unresolvedCount,
    per_event: coverage.entries,
  }, null, 2))

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
    // pratyantar_lord's OWN eventClass argument stays the raw LEL category --
    // its significator lookup (eventClassSignificators, built above) is
    // keyed by raw category via CATEGORY_TO_DOMAIN, an independent mechanism
    // that never touches gochara_resonance_map and was never the F-1 bug.
    const rawCategoryEventClass = raw.category
    // The RESOLVED gochara_resonance_map event_class (F-1 fix) -- this is
    // what the 12 PERMISSION contenders + ensemble actually need.
    const resolution = resolvedByEventId.get(raw.eventId)
    const permissionEventClass = resolution?.populated ? resolution.resolvedEventClass! : null
    const curveEvent = toCurveEvent(raw)
    console.error(
      `[b1_driver] event ${eventIdx}/${events.length} ${raw.eventId} (category=${raw.category}, ` +
        `resolved=${permissionEventClass ?? 'UNRESOLVED'}) range=${range[0].toISOString().slice(0, 10)}..${range[1].toISOString().slice(0, 10)}`
    )

    if (permissionEventClass) {
      // Bind the 13 base contenders IN PARALLEL (driver-level orchestration
      // choice, not a harness-code change: ensemble_model.ts's own bind()
      // chains sequentially, which serializes 12 real HTTP round-trips per
      // event against the live sidecar). ensemble.curve() then reads the
      // now-populated caches synchronously -- no separate ensemble.bind() call
      // needed once its constituents are bound for this exact triple.
      //
      // pratyantar_lord itself is bound here too, with permissionEventClass
      // (NOT rawCategoryEventClass) -- harmless (pratyantarLordModel.bind is
      // undefined, so `m.bind?.(...)` is a no-op for it); its curve() call
      // below still uses rawCategoryEventClass, unaffected.
      const t0 = Date.now()
      await Promise.all(roster.map((m) => m.bind?.(chart, permissionEventClass, range)))
      console.error(`[b1_driver]   bound ${roster.length} base contenders in ${Date.now() - t0}ms`)
      for (const model of fullRoster) {
        const eventClass = model.modelId === 'pratyantar_lord' ? rawCategoryEventClass : permissionEventClass
        try {
          const r = runMirroredScoringHarness({ model, chart, eventClass, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
          results[model.modelId] = results[model.modelId] || []
          results[model.modelId].push({ eventId: raw.eventId, eventClass, range: [range[0].toISOString(), range[1].toISOString()], result: r })
        } catch (err) {
          results[model.modelId] = results[model.modelId] || []
          results[model.modelId].push({ eventId: raw.eventId, eventClass, error: err instanceof Error ? `${err.name}: ${err.message}` : String(err) })
        }
      }
    } else {
      // F-1: event_class does not resolve to a POPULATED gochara_resonance_map
      // row for this event (see run header, b1_run_header_f1.json, for the
      // reason). The 12 PERMISSION contenders + ensemble are SKIPPED for this
      // event, explicitly and visibly -- not silently scored against the
      // sidecar's target_count=0 fallback path (the original bug).
      // pratyantar_lord alone is still scored -- it does not read
      // gochara_resonance_map at all.
      const pratyantarLord = fullRoster.find((m) => m.modelId === 'pratyantar_lord')!
      try {
        const r = runMirroredScoringHarness({ model: pratyantarLord, chart, eventClass: rawCategoryEventClass, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
        results['pratyantar_lord'] = results['pratyantar_lord'] || []
        results['pratyantar_lord'].push({ eventId: raw.eventId, eventClass: rawCategoryEventClass, range: [range[0].toISOString(), range[1].toISOString()], result: r })
      } catch (err) {
        results['pratyantar_lord'] = results['pratyantar_lord'] || []
        results['pratyantar_lord'].push({ eventId: raw.eventId, eventClass: rawCategoryEventClass, error: err instanceof Error ? `${err.name}: ${err.message}` : String(err) })
      }
      for (const model of fullRoster) {
        if (model.modelId === 'pratyantar_lord') continue
        results[model.modelId] = results[model.modelId] || []
        results[model.modelId].push({
          eventId: raw.eventId,
          eventClass: null,
          skipped: 'unresolved_event_class',
          reason: resolution?.reason ?? 'no coverage-report entry found for this eventId (driver bug if it occurs)',
        })
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
