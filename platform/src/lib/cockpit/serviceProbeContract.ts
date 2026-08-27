/**
 * Cockpit admission contract for the frozen, no-writer L0 service probes.
 *
 * The T0 manifest assigns `execution_obligation: 'probe'` to these assets.
 * They have no WriterBase implementation, so they may be dispatched only as a
 * singleton `asset_set`; all other services stay out of the normal build
 * planner. The backend checks the full registry shape at admission; the UI
 * checks the registry projection it receives, so an ID alone never selects the
 * singleton request shape.
 */
export const COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS = [
  'bg_ephemeris_engine',
  'bg_panchanga',
] as const

export type CockpitDispatchableServiceProbeId =
  (typeof COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS)[number]

type ServiceProbeRegistryShape = {
  asset_id: string
  scope: string
  has_writer?: boolean
  asset_kind: string | null
  asset_type: string | null
  health_probe: Record<string, unknown> | null
}

export function isCockpitDispatchableServiceProbe(
  asset: ServiceProbeRegistryShape,
): asset is ServiceProbeRegistryShape & { asset_id: CockpitDispatchableServiceProbeId } {
  return (COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS as readonly string[]).includes(asset.asset_id)
    && asset.scope === 'global'
    && asset.has_writer !== true
    && asset.asset_kind === 'service'
    && asset.asset_type === 'service'
    && asset.health_probe !== null
}
