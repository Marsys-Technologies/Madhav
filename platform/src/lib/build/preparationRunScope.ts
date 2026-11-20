import 'server-only'

/** Matches the saved full-chart preparation scope even when the recovery plan is smaller. */
export function preparationRunScopeSql(run: 'r' | 'build_runs'): string {
  return `${run}.scope = 'asset_set'
    AND COALESCE(${run}.scope_target ~ '(^|,)[[:space:]]*ga_positions[[:space:]]*(,|$)', false)
    AND COALESCE(${run}.scope_target ~ '(^|,)[[:space:]]*bo_laksana[[:space:]]*(,|$)', false)`
}
