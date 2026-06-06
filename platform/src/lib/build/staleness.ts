export interface StalenessAsset {
  asset_id: string
  last_built_at: Date | null
  built_against_upstream_hash: string | null
  built_against_writer_hash: string | null
}

export interface StalenessUpstream {
  asset_id: string
  last_built_at: Date | null
  content_hash: string | null
}

export interface StalenessCodeRef {
  asset_id: string
  current_writer_hash: string | null
}

/**
 * Returns true if the asset should be considered stale:
 *   - data invalidation: any upstream was rebuilt after this asset, or upstream
 *     content hash changed
 *   - code invalidation: the writer source hash changed since this was built
 */
export function isStale(
  asset: StalenessAsset,
  upstreams: StalenessUpstream[],
  codeRef: StalenessCodeRef
): boolean {
  if (asset.last_built_at == null) return false // dormant, not stale

  // Data invalidation
  for (const up of upstreams) {
    if (up.last_built_at != null && up.last_built_at > asset.last_built_at) return true
    if (
      up.content_hash != null &&
      asset.built_against_upstream_hash != null &&
      up.content_hash !== asset.built_against_upstream_hash
    ) return true
  }

  // Code invalidation
  if (
    codeRef.current_writer_hash != null &&
    asset.built_against_writer_hash != null &&
    codeRef.current_writer_hash !== asset.built_against_writer_hash
  ) return true

  return false
}
