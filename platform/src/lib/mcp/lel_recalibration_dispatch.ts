/**
 * lel_recalibration_dispatch.ts — the LEL-append → RECALIBRATION hand-off, as a TRACKED,
 * SCOPED ORCHESTRATOR BUILD RUN.
 *
 * ṢAḌ-DARŚANA W2, Lane E. Spec: `SHAD_DARSHANA_BRIEF_v2_0.md` §2.5.5 (binding) and
 * `KALA_W2_FIELD_DESIGN_v1_0.md` §7.6 "Dispatch discipline".
 *
 * ── THE RULE, AND WHY IT IS STRUCTURAL RATHER THAN A CONVENTION ────────────────────────
 *   "The LEL-append hook dispatches a **standard, tracked, scoped build run**
 *    (`asset_set = ['mi_bhara', <biographical-join refresh>]`) through the
 *    orchestrator/pipeline. **No side-channel recomputation** — the orchestrator remains the
 *    sole build-state writer. Nirmāṇa must see state, progress, and throughput for a
 *    recalibration exactly as for any other build."
 *
 * This module therefore BUILDS A REQUEST and does nothing else. It performs no fetch, opens no
 * connection, and computes nothing a build would compute. That is deliberate: a module that
 * could both decide to recalibrate AND perform the recalculation is one refactor away from
 * being the side channel the rule forbids. Keeping the decision and the execution in different
 * processes makes the rule impossible to violate by accident rather than merely discouraged.
 *
 * ── THE ASSET SET IS EXACTLY `['mi_bhara']` ────────────────────────────────────────────
 * §7.6's flow names five steps — falsifier resolution, weight update, skill/GOF recompute,
 * biographical-join refresh, maturity update. All five are PHASES INSIDE `mi_bhara.run()`
 * (`platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py`), not separate assets.
 * So the asset set has one member and there is no second id that could silently drift out of
 * sync with this constant. `platform/python-sidecar/services/mi_bhara/living_lel.py`'s
 * `RECALIBRATION_ASSET_SET` is the Python twin; `lel_recalibration_dispatch.test.ts` asserts
 * the two agree by reading that file, so a change on either side fails CI rather than
 * diverging quietly.
 *
 * ── WIRING ─────────────────────────────────────────────────────────────────────────────
 * The intended call site is the LEL intake write path — `recordLelEvent` in
 * `./lel_event_writer.ts` — whose caller POSTs the returned body to `/api/cockpit/runs`
 * (`platform/src/app/api/cockpit/runs/route.ts`), the same endpoint a user-initiated build
 * uses. That route's `scope='asset_set'` branch splits `scope_target` with
 * `parseAssetSetTarget` and hands it to `resolveBuildPlan`, so the run is topo-sorted, gated
 * and tracked identically to any other. Note its Gate 0: a 409 `RUN_ACTIVE` when a build is
 * already in flight for the chart is CORRECT behaviour here — the append will be picked up by
 * the next run — and must not be routed around with a direct recompute.
 *
 * @module lel_recalibration_dispatch
 */

/**
 * The assets a recalibration rebuilds. One member, by design — see the module docstring.
 * Mirrors `services/mi_bhara/living_lel.py::RECALIBRATION_ASSET_SET`.
 */
export const RECALIBRATION_ASSET_SET = ['mi_bhara'] as const

/** Why a recalibration was dispatched. Carried for the audit trail, not for control flow. */
export type RecalibrationReason = 'lel_append' | 'lel_correction' | 'manual_refit'

/**
 * A `POST /api/cockpit/runs` request body plus the provenance of the append that caused it.
 * `toRequestBody()` yields exactly the four fields that route requires; everything else on
 * this object is for the ledger.
 */
export interface RecalibrationDispatch {
  chart_id: string
  scope: 'asset_set'
  scope_target: string
  action: 'rebuild'
  reason: RecalibrationReason
  triggering_event_ids: string[]
}

/**
 * Build the tracked-run request for an LEL append.
 *
 * `action: 'rebuild'` rather than `'build'` is load-bearing: `resolveBuildPlan`'s `'build'`
 * branch filters candidates to those in a `dormant`/`error` state and NO-OPS on an already
 * `lit` asset. A chart whose `mi_bhara` is lit — which is every chart that has been calibrated
 * once — would silently skip its own recalibration under `'build'`. `'rebuild'` takes every
 * in-scope asset regardless of state, which is what "the LEL changed, re-fit" means.
 *
 * @param chartId the chart whose LEL was appended to
 * @param triggeringEventIds the `life_events.event_id`s that caused this dispatch
 * @param reason audit-trail classification; defaults to a plain append
 */
export function buildRecalibrationDispatch(
  chartId: string,
  triggeringEventIds: readonly string[] = [],
  reason: RecalibrationReason = 'lel_append',
): RecalibrationDispatch {
  if (!chartId) {
    throw new Error(
      'buildRecalibrationDispatch requires a chart_id — a recalibration is per-chart, and an ' +
      'unscoped run would recalibrate the wrong native (or every native).',
    )
  }
  return {
    chart_id: chartId,
    scope: 'asset_set',
    scope_target: RECALIBRATION_ASSET_SET.join(','),
    action: 'rebuild',
    reason,
    triggering_event_ids: [...triggeringEventIds],
  }
}

/** The exact body `POST /api/cockpit/runs` expects — no extra keys, no missing ones. */
export function toRequestBody(dispatch: RecalibrationDispatch): {
  chart_id: string
  scope: string
  scope_target: string
  action: string
} {
  return {
    chart_id: dispatch.chart_id,
    scope: dispatch.scope,
    scope_target: dispatch.scope_target,
    action: dispatch.action,
  }
}
