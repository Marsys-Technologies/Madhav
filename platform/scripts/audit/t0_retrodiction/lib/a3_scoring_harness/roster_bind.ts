/**
 * roster_bind.ts — D-4b permission-bridge lane (wave/D-4b/permission-bridge).
 *
 * The BIND-TIME ASSERTION: "at bind (before any scoring call), the harness
 * must verify every contender in the ACTIVE/narrowed roster resolves to a
 * working, non-stub curve() implementation — fail loudly and immediately
 * if not, so this exact blocker class (a gate passing while the standing
 * interface silently regressed to stubs) cannot recur."
 *
 * This is precisely the blocker `B1_BAKEOFF_STATUS_v1_0.md` found by
 * manual code inspection (4 of 5 requested contenders were stubs or had no
 * adapter at all) — this module makes that check MECHANICAL and repeatable
 * instead of relying on a future session re-discovering it by hand. A
 * future B-1 scoring driver calls `assertRosterBindable(roster, ...)` as
 * its literal first line, before `runMirroredScoringHarness`/
 * `runComparativeHarness` (harness.ts) ever runs.
 *
 * "Fail loudly and immediately": every contender is probed (not just the
 * first), and any failure — a `NotImplementedModelError` stub, a `bind()`
 * network/HTTP failure, an empty curve, any other thrown error — is
 * collected; if the collected list is non-empty, ONE `RosterBindFailureError`
 * is thrown naming every failing `modelId` and its underlying reason
 * (mirrors `ControlMirroringViolationError`'s "name every differing field"
 * discipline in harness.ts) — never a silent partial pass.
 */
import type { ChartContext, EventClass, TemporalCurveModel } from './model_interface'

export type RosterBindFailure = { modelId: string; reason: string }

export class RosterBindFailureError extends Error {
  readonly failures: RosterBindFailure[]
  constructor(failures: RosterBindFailure[]) {
    super(
      `roster bind-time assertion FAILED for ${failures.length} contender(s) — no scoring call may proceed: ` +
        failures.map((f) => `${f.modelId} (${f.reason})`).join('; ')
    )
    this.name = 'RosterBindFailureError'
    this.failures = failures
  }
}

export type RosterBindReport = { modelId: string; pointCount: number }

/**
 * Probes every model in `roster` against a small `probeRange` (does NOT
 * need to be the real scoring window — this is a liveness/non-stub check,
 * not a scoring run; a short range keeps the sidecar round-trips cheap).
 * Throws `RosterBindFailureError` naming every failing contender if any
 * fail; otherwise returns a report of each contender's probe point count
 * (useful for logging "verified N contenders bindable" before scoring
 * starts).
 */
export async function assertRosterBindable(
  roster: TemporalCurveModel[],
  chart: ChartContext,
  eventClass: EventClass,
  probeRange: [Date, Date]
): Promise<RosterBindReport[]> {
  const failures: RosterBindFailure[] = []
  const report: RosterBindReport[] = []

  for (const model of roster) {
    try {
      await model.bind?.(chart, eventClass, probeRange)
      const curve = model.curve(chart, eventClass, probeRange)
      if (!Array.isArray(curve) || curve.length === 0) {
        failures.push({ modelId: model.modelId, reason: 'curve() returned an empty/non-array result — treated as a non-working implementation, not a valid honest-zero curve for a bind-time liveness probe' })
        continue
      }
      report.push({ modelId: model.modelId, pointCount: curve.length })
    } catch (err) {
      const reason = err instanceof Error ? `${err.name}: ${err.message}` : String(err)
      failures.push({ modelId: model.modelId, reason })
    }
  }

  if (failures.length > 0) throw new RosterBindFailureError(failures)
  return report
}
