/**
 * Serving-impact classification of build runs (Jātaka chart workspace, Phase-A2).
 *
 * Readiness treats an active run as reading-blocking unless the run is known
 * to leave the currently served chart dataset valid. The only non-blocking
 * signature today is the LEL recalibration run (`recalibrationEnqueue.ts`): an
 * asset/asset_set rebuild confined to the calibration assets a new life event
 * invalidates. Each writer commits its own transaction, so a reading in flight
 * sees either the previous or the new calibration, never a cleared chart.
 *
 * Everything else — a global or layer run, an asset run that touches any other
 * asset, a run whose planned assets are unknown or empty, an unknown scope —
 * blocks readings until it is explicitly classified here. Pure: no server-only
 * import, so the gate, the band and their tests share one rule.
 *
 * Kept equal to `LEL_DEPENDENT_ASSETS` by `servingImpact.test.ts`.
 */
export const NON_SERVING_RECALIBRATION_ASSETS: ReadonlySet<string> = new Set([
  'mi_jivanaghatana',
  'mi_pramana',
  'ph_rectification',
  'ph_pramana',
])

const NARROW_SCOPES = new Set(['asset', 'asset_set'])

export function runBlocksReadings(run: { scope?: string | null; planned_assets?: readonly string[] | null }): boolean {
  if (!run.scope || !NARROW_SCOPES.has(run.scope)) return true
  const planned = run.planned_assets
  if (!planned || planned.length === 0) return true
  return !planned.every((assetId) => NON_SERVING_RECALIBRATION_ASSETS.has(assetId))
}
