/**
 * Read-only freshness projection consumed by build planning.
 *
 * Python owns digest calculation and reconciliation. This module deliberately
 * does not compare source, output, or upstream hashes: a Next.js process cannot
 * authoritatively observe the sidecar's deployed Python closure.
 */
export type FreshnessState = 'fresh' | 'stale' | 'unknown'

export interface FreshnessProjection {
  asset_id: string
  state: FreshnessState
  reasons: string[]
  observed_at: Date | null
}

export function freshnessForAsset(
  projection: ReadonlyMap<string, FreshnessProjection> | undefined,
  assetId: string,
): FreshnessProjection | undefined {
  return projection?.get(assetId)
}

export function isFresh(projection: FreshnessProjection | undefined): boolean {
  return projection?.state === 'fresh'
}
