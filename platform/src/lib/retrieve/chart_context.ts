/**
 * MARSYS-JIS retrieve/chart_context — single source for the active chart_id.
 *
 * Unit 2a (G4 gate): no `NATIVE_CHART_ID` or `DEFAULT_CHART_ID` literals may
 * appear inside platform/src/lib/retrieve/* outside test files. Tools that
 * need a chart_id MUST resolve it via `requireChartId(input.chart_id)` so the
 * resolution is centralised and operator-overridable.
 *
 * Resolution order (`requireChartId(explicit?)`):
 *   1. `explicit` argument (per-request override, e.g. QueryPlan.chart_id)
 *   2. process.env.MARSYS_ACTIVE_CHART_ID (server-side runtime config)
 *   3. throws — the caller MUST supply a chart_id OR the environment MUST
 *      set MARSYS_ACTIVE_CHART_ID. No hard-coded native fallback.
 *
 * `getActiveChartIdOrNull()` is the soft variant for diagnostic paths
 * (returns null instead of throwing).
 */

/**
 * Resolve the active chart_id. Throws if no source is available.
 *
 * Soft callers (diagnostic JSON, telemetry) should use
 * `getActiveChartIdOrNull()` instead.
 */
export function requireChartId(explicit?: string | null | undefined): string {
  if (explicit && explicit.length > 0) return explicit
  const fromEnv = process.env.MARSYS_ACTIVE_CHART_ID
  if (fromEnv && fromEnv.length > 0) return fromEnv
  throw new Error(
    'retrieve/chart_context: no chart_id supplied. Pass `chart_id` in the tool ' +
      'input or set MARSYS_ACTIVE_CHART_ID in the environment.',
  )
}

/**
 * Soft resolve — returns null if no chart_id is available. Use for diagnostic
 * row content (e.g. empty-state notes) where falling back is acceptable.
 */
export function getActiveChartIdOrNull(
  explicit?: string | null | undefined,
): string | null {
  if (explicit && explicit.length > 0) return explicit
  const fromEnv = process.env.MARSYS_ACTIVE_CHART_ID
  return fromEnv && fromEnv.length > 0 ? fromEnv : null
}
