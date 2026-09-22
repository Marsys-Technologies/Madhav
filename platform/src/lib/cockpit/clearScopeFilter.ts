export interface RegistryRow {
  asset_id: string
  layer: string
  scope: string
  target_table: string | null
  count_sql?: string | null
  depends_on?: string[]
  estimated_seconds?: number | null
  /**
   * `asset_registry.is_active`. Optional so a caller that does not select the
   * column is not silently emptied; see `isClearable` below for the exact
   * semantics and why they are deliberately narrow.
   */
  is_active?: boolean | null
}

/**
 * B1 (Kāla pre-elevation Phase 1.1, Strategy W0): a RETIRED asset is never in
 * scope for a Clear.
 *
 * `ka_gochara_sweep` is `is_active=false`, `catalog_status='RETIRED'`,
 * `scope='per_chart'`, `layer='kala'`, and its registry `count_sql` is
 * generation-scoped to `kala_gochara_windows WHERE generation='v1'` — the
 * 38,287-row snapshot the L3 strategy calls "retired, snapshot-protected and
 * never rebuildable" (no `@register`; the build system cannot regenerate it).
 * Because `allowedScopes` is `['per_chart']` for an ordinary chart owner, a
 * layer-scoped Clear of `kala` reached it through this function, which matched
 * on `layer` + `scope` only. Every sibling cockpit route already filters
 * `is_active` (refresh:49, status:11, runs:243, stats:257) — so the BUILD path
 * excluded the retired asset while the DELETE path did not.
 *
 * SEMANTICS, chosen narrowly and on purpose: only an EXPLICIT `false` excludes.
 * `undefined` (a caller that did not select the column) and `null` do not, so
 * this filter can only narrow a set the route has already filtered — it is the
 * second of two independent layers, never the one that decides alone. Measured
 * on production 2026-09-22: `asset_registry` holds 0 NULL / 1 false / 128 true,
 * and the single `false` row is `ka_gochara_sweep`.
 */
function isClearable(r: RegistryRow): boolean {
  return r.is_active !== false
}

/**
 * Filters the asset registry to the assets that should be cleared for a given
 * scope request, honoring the caller's allowed-scope list (role-derived).
 */
export function filterScopeAssets(
  registry: RegistryRow[],
  scope: 'global' | 'layer' | 'asset' | 'asset_set',
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
    return registry.filter(r => isClearable(r) && allowedScopes.includes(r.scope) && r.layer !== 'brahmagyan')
  } else if (scope === 'layer') {
    return registry.filter(r => isClearable(r) && r.layer === scopeTarget && allowedScopes.includes(r.scope))
  } else if (scope === 'asset_set') {
    // scope_target carries a comma-separated asset_id list — clear each in-set asset.
    const wanted = new Set(
      (scopeTarget ?? '').split(',').map(s => s.trim()).filter(Boolean)
    )
    return registry.filter(r => isClearable(r) && wanted.has(r.asset_id) && allowedScopes.includes(r.scope))
  } else {
    return registry.filter(r => isClearable(r) && r.asset_id === scopeTarget && allowedScopes.includes(r.scope))
  }
}
