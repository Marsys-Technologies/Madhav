export interface RegistryRow {
  asset_id: string
  layer: string
  scope: string
  target_table: string | null
  count_sql?: string | null
  depends_on?: string[]
  estimated_seconds?: number | null
}

/**
 * Filters the asset registry to the assets that should be cleared for a given
 * scope request, honoring the caller's allowed-scope list (role-derived).
 */
export function filterScopeAssets(
  registry: RegistryRow[],
  scope: 'global' | 'layer' | 'asset',
  scopeTarget: string | null,
  allowedScopes: string[]
): RegistryRow[] {
  if (scope === 'global') {
    return registry.filter(r => allowedScopes.includes(r.scope))
  } else if (scope === 'layer') {
    return registry.filter(r => r.layer === scopeTarget && allowedScopes.includes(r.scope))
  } else {
    return registry.filter(r => r.asset_id === scopeTarget && allowedScopes.includes(r.scope))
  }
}
