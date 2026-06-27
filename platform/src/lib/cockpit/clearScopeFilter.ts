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
    // L0 GATE (native ruling 2026-06-26): a global clear NEVER includes L0 (brahmagyan),
    // regardless of role. This mirrors the global Build/Rebuild gate in /api/cockpit/runs.
    // L0 is cleared ONLY via an explicit layer='brahmagyan' trigger or an individual bg_*
    // asset trigger — never as a side effect of the global Clear/Rebuild button. Without
    // this filter, a super_admin global clear would DELETE FROM each bg_* reference table
    // (no chart_id scoping) and wipe shared L0 data for every chart.
    return registry.filter(r => allowedScopes.includes(r.scope) && r.layer !== 'brahmagyan')
  } else if (scope === 'layer') {
    return registry.filter(r => r.layer === scopeTarget && allowedScopes.includes(r.scope))
  } else {
    return registry.filter(r => r.asset_id === scopeTarget && allowedScopes.includes(r.scope))
  }
}
