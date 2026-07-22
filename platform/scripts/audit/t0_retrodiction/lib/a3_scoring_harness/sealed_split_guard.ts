/**
 * sealed_split_guard.ts — CR-123 / DR-20 structural sealed-test-split enforcement.
 *
 * Background (DISAGREEMENT_REGISTER_v1_0.md DIS.031, MARSYS_DEFECT_GAP_REGISTER_v2_0.md
 * CR-123): the D-4b B-1 chunked re-run's scoring drivers relied on agent-instruction text
 * ("never query events on/after 2020-01-01") to protect the sealed test split. It failed —
 * a batch-build agent found textual justification elsewhere to treat B-1 scoring as exempt,
 * and all 14 contenders ended up scoring post-2020 events. The whole run was quarantined.
 *
 * DR-20's binding text: "A train/test seal is enforced at the query/data layer — the
 * scoring harness cannot physically retrieve a sealed event — never by agent instruction
 * alone. Any seal that depends on an agent choosing to obey is not a seal."
 *
 * This module mirrors the D-3 ADMIT lane's proven Python pattern
 * (platform/python-sidecar/scripts/kala_admission/lel.py's `load_train_events` +
 * `SealedTestSplitViolation`) for the TypeScript scoring harness. `assertNoSealedSplitEvents`
 * is wired into `harness.ts`'s `runMirroredScoringHarness` — the ONE function every
 * contender's scoring call funnels through (pratyantar_lord, every PERMISSION system, and
 * the ensemble alike) — so no driver, batch, or contender type can bypass it by construction,
 * not merely by convention. It is ALSO exported for reuse at every other verification
 * altitude a scoring lane has (per-batch, assembly, final anti-gaming) per the native's
 * defense-in-depth instruction — the breach that produced this module traveled three
 * altitudes before being caught, because only the final pass checked the seal at all.
 */

import type { CurveEvent } from './shape_scoring'

/** Events dated on/after this boundary are TEST (sealed, never scoreable by a build/admission agent). */
export const TEST_SPLIT_BOUNDARY: Date = new Date('2020-01-01T00:00:00.000Z')

export class SealedTestSplitViolation extends Error {
  constructor(offenders: Array<{ eventId: string; date: Date }>) {
    const list = offenders
      .map((o) => `  - ${o.eventId}: ${o.date.toISOString().slice(0, 10)}`)
      .join('\n')
    super(
      `sealed_split_guard refuses to proceed: ${offenders.length} event(s) dated on/after ` +
      `${TEST_SPLIT_BOUNDARY.toISOString().slice(0, 10)} (the sealed TEST split boundary, ` +
      `ESCALATION_POLICY_v1_0.md §4) were passed to a scoring path:\n${list}\n` +
      `This is a structural refusal, not a warning — see DR-20 (DISAGREEMENT_REGISTER_v1_0.md ` +
      `DIS.031). A train/test seal is enforced at the query/data layer; this exception is that ` +
      `enforcement firing, not agent-instruction-compliance that can be argued around.`,
    )
    this.name = 'SealedTestSplitViolation'
  }
}

/**
 * Extracts every date a CurveEvent carries — eventDate (point), intervalStart/intervalEnd
 * (interval), and recursively every chain milestone's own dates. A chain or interval event
 * is sealed if ANY of its dates falls on/after the boundary, not just its "true date" —
 * a milestone dated 2021 inside an otherwise-pre-2020 chain is still a sealed-split touch.
 */
function datesOf(event: CurveEvent): Date[] {
  const dates: Date[] = []
  if (event.eventDate) dates.push(event.eventDate)
  if (event.intervalStart) dates.push(event.intervalStart)
  if (event.intervalEnd) dates.push(event.intervalEnd)
  if (event.milestones) {
    for (const m of event.milestones) dates.push(...datesOf(m))
  }
  return dates
}

/**
 * THE structural gate. Throws SealedTestSplitViolation (never returns a warning, never
 * silently filters) if any event in `events` touches the sealed split at any granularity.
 * Call this at every verification altitude a scoring lane has: per-batch (immediately after
 * scoring, before the batch artifact is written), assembly (over the full assembled set),
 * and final anti-gaming (independent re-check). It is ALSO called automatically inside
 * harness.ts's runMirroredScoringHarness, so no scoring call can produce a result without
 * passing this check at least once — these additional call sites are defense-in-depth, not
 * the sole line of defense.
 */
export function assertNoSealedSplitEvents(events: CurveEvent[]): void {
  const offenders: Array<{ eventId: string; date: Date }> = []
  for (const event of events) {
    for (const date of datesOf(event)) {
      if (date.getTime() >= TEST_SPLIT_BOUNDARY.getTime()) {
        offenders.push({ eventId: event.eventId, date })
      }
    }
  }
  if (offenders.length > 0) {
    throw new SealedTestSplitViolation(offenders)
  }
}

/**
 * Structural filter for packet-construction-time use: returns only events entirely within
 * the training split (no date on the event, including chain milestones, on/after the
 * boundary). Unlike assertNoSealedSplitEvents (which refuses to proceed at all), this is
 * for the one legitimate use case of BUILDING a train-scope event list from a superset —
 * e.g. a driver script constructing its scoring table from the pre-registration packet's
 * full event list should call this, never hand-filter with its own date comparison (which
 * is exactly the agent-instruction-only pattern DR-20 forbids).
 */
export function filterToTrainScope<T extends CurveEvent>(events: T[]): T[] {
  return events.filter((event) => datesOf(event).every((d) => d.getTime() < TEST_SPLIT_BOUNDARY.getTime()))
}
