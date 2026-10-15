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

export type ChartScopedClearResolution =
  | {
      ok: true
      /** Per-chart assets only. A global asset is never in this list. */
      assets: RegistryRow[]
      /** Global assets that a layer/global sweep passed over; they are NOT cleared. */
      globalAssetsLeftUntouched: string[]
    }
  | { ok: false; status: 422; code: 'GLOBAL_CLEAR_FORBIDDEN'; error: string }

/**
 * FIX2 (portal Rebuild, 2026-10): the single decision point for what a clear
 * requested from a CHART page may delete.
 *
 * A global asset's table (scope='global': reference/L0 tables, global export logs)
 * is shared by every chart, and its DELETE carries no chart filter. A chart page
 * therefore must never clear one — not for a super_admin either; global assets are
 * rebuilt in place by the global dispatcher, never cleared from a chart. (The old
 * behaviour let a super_admin's layer/asset_set clear run `DELETE FROM <table>` with
 * no WHERE, then the unforced run could delta-skip and leave the table EMPTY.)
 *
 *  - Naming a global asset explicitly (scope asset / asset_set), or a layer that holds
 *    nothing but global assets (e.g. brahmagyan), is REFUSED with 422.
 *  - A broad sweep (global scope, or a mixed layer) simply passes over its global
 *    members: they stay untouched and are reported in `globalAssetsLeftUntouched`.
 *
 * Callers must use `assets` as the ONLY clear set, and must not widen it again with a
 * role-derived scope list.
 */
export function resolveChartScopedClear(
  registry: RegistryRow[],
  scope: 'global' | 'layer' | 'asset' | 'asset_set',
  scopeTarget: string | null,
): ChartScopedClearResolution {
  const requested = filterScopeAssets(registry, scope, scopeTarget, ['per_chart', 'global'])
  const globals = requested.filter(r => r.scope === 'global')
  const perChart = requested.filter(r => r.scope !== 'global')
  const explicit = scope === 'asset' || scope === 'asset_set'
  const onlyGlobals = scope === 'layer' && perChart.length === 0 && globals.length > 0
  if (globals.length > 0 && (explicit || onlyGlobals)) {
    const ids = globals.map(g => g.asset_id).join(', ')
    return {
      ok: false,
      status: 422,
      code: 'GLOBAL_CLEAR_FORBIDDEN',
      error:
        `Clear refused: ${ids} ${globals.length === 1 ? 'is' : 'are'} shared by every chart, ` +
        'so it cannot be cleared from one chart\'s page. Clearing it would empty the table for all charts. ' +
        'Shared assets are rebuilt in place by the global build, not cleared here.',
    }
  }
  return { ok: true, assets: perChart, globalAssetsLeftUntouched: globals.map(g => g.asset_id) }
}
