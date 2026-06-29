import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const maxDuration = 8

export async function GET(req: NextRequest) {
  // Read-only endpoint — any authenticated user may poll the active run for
  // their own chart. super_admin gate removed (it made isBuilding always false
  // for non-super-admin users, breaking the build tracker entirely).
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const chart_id = req.nextUrl.searchParams.get('chart_id')
  if (!chart_id) return NextResponse.json({ error: 'chart_id query param required' }, { status: 400 })

  try {
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
    if (!run) return NextResponse.json({ data: null })

    const assetsResult = await query<{
      asset_id: string
      position: number
      state: string
      started_at: string | null
      ended_at: string | null
      error: string | null
    }>(
      `SELECT asset_id, position, state, started_at, ended_at, error
       FROM build_run_assets WHERE run_id=$1 ORDER BY position`,
      [run.id]
    )

    return NextResponse.json({ data: { run, assets: assetsResult.rows } })
  } catch (err) {
    console.error('[cockpit/runs/active]', err)
    return NextResponse.json({ data: null, _error: (err as Error).message })
  }
}
