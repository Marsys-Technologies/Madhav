import 'server-only'
import { query } from '@/lib/db/client'
import * as columnPresence from '@/lib/db/columnPresence'
import type { BuildPhase } from '@/hooks/useActiveRun'

/** Existing authorized active-run read, including its conditional schema probe.
 * No new caller permission, readiness inference, subscription or job is introduced.
 */
export async function readActiveBuildRun(chart_id: string) {
    const runResult = await query<{
      id: string
      scope: string
      scope_target: string | null
      action: string
      state: string
      plan: string[]
      current_asset_id: string | null
      created_at: string
      started_at: string | null
      pause_requested_at: string | null
      stop_requested_at: string | null
    }>(
      // Index: build_runs_chart_state_planned_idx covers planned/running/paused
      // See migration 359_fix_build_runs_active_index.sql
      `SELECT id, scope, scope_target, action, state, plan, current_asset_id,
              created_at, started_at, pause_requested_at, stop_requested_at
       FROM build_runs
       WHERE chart_id=$1 AND state IN ('planned','running','paused')
       ORDER BY created_at DESC LIMIT 1`,
      [chart_id]
    )

    const run = runResult.rows[0] ?? null
    if (!run) return null

    // Packet B1 (review B1_review_20260926T182200Z.md C-2b): this route reads
    // build_run_assets.state RAW — the one live surface the packet's own
    // before-measurement census missed entirely. AgentsView.tsx's "Errors this
    // run" bucket filtered on this route's `state === 'error'` with no disposition
    // field even available to distinguish a cascade victim from a genuine failure.
    // `disposition` already exists in production (predates blocked_by_asset_id) so
    // it is selected unconditionally; `blocked_by_asset_id` (migration 1201) and
    // phase-telemetry columns (migration 1420, NIR-03) are gated by the process-
    // cached column probes — never select a column that may not exist yet.
    const hasPhaseProbe = Object.prototype.hasOwnProperty.call(columnPresence, 'phaseTelemetryColumnsPresent')
      && typeof columnPresence.phaseTelemetryColumnsPresent === 'function'
    const [includeBlockedBy, includePhaseTelemetry] = await Promise.all([
      columnPresence.blockedByAssetIdColumnPresent(),
      hasPhaseProbe
        ? columnPresence.phaseTelemetryColumnsPresent()
        : Promise.resolve(false),
    ])
    const blockedByCol = includeBlockedBy ? 'blocked_by_asset_id' : 'NULL::text AS blocked_by_asset_id'
    const phaseCols = includePhaseTelemetry
      ? 'phase, substep_index, substep_total, substep_label, compute_ms, write_ms, verify_ms, publish_ms'
      : [
          'NULL::text AS phase',
          'NULL::integer AS substep_index',
          'NULL::integer AS substep_total',
          'NULL::text AS substep_label',
          'NULL::integer AS compute_ms',
          'NULL::integer AS write_ms',
          'NULL::integer AS verify_ms',
          'NULL::integer AS publish_ms',
        ].join(', ')
    const assetsResult = await query<{
      asset_id: string
      position: number
      state: string
      started_at: string | null
      ended_at: string | null
      error: string | null
      disposition: string | null
      blocked_by_asset_id: string | null
      phase: BuildPhase | null
      substep_index: number | null
      substep_total: number | null
      substep_label: string | null
      compute_ms: number | null
      write_ms: number | null
      verify_ms: number | null
      publish_ms: number | null
    }>(
      `SELECT asset_id, position, state, started_at, ended_at, error, disposition, ${blockedByCol}, ${phaseCols}
       FROM build_run_assets WHERE run_id=$1 ORDER BY position`,
      [run.id]
    )

    return { run, assets: assetsResult.rows }
}
