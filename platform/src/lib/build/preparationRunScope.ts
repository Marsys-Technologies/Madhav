import 'server-only'
import { parseAssetSetTarget } from './plan'

const PREPARATION_LAYERS = new Set(['ganita', 'bodha'])

function isPreparationAssetId(assetId: string): boolean {
  return assetId.startsWith('ga_') || assetId.startsWith('bo_')
}

export function isPreparationRunScope(scope: string, target: string | null): boolean {
  if (scope === 'global') return true
  if (scope === 'layer') return target !== null && PREPARATION_LAYERS.has(target)
  if (scope !== 'asset_set') return false
  return parseAssetSetTarget(target).some(isPreparationAssetId)
}

/** Matches whole-layer, global, and partial L1/L2 asset_set preparation scopes. */
export function preparationRunScopeSql(run: 'r' | 'build_runs'): string {
  return `(${run}.scope = 'global'
    OR (${run}.scope = 'layer' AND ${run}.scope_target IN ('ganita', 'bodha'))
    OR (${run}.scope = 'asset_set' AND COALESCE(${run}.scope_target ~ '(^|,)[[:space:]]*(ga|bo)_[a-z0-9_]+[[:space:]]*(,|$)', false)))`
}
