import 'server-only'
import { query } from '@/lib/db/client'

export interface BuildRunHistoryRow {
  id: string
  scope: string
  scope_target: string | null
  action: string
  state: string
  created_at: string
  ended_at: string | null
  last_error: string | null
}

/** Build owns the chart-scoped history projection; callers authorize access first. */
export async function readBuildRunHistory(chart_id: string): Promise<BuildRunHistoryRow[]> {
  const { rows } = await query<BuildRunHistoryRow>(
    `SELECT id, scope, scope_target, action, state, created_at, ended_at, last_error
         FROM build_runs
        WHERE chart_id = $1
        ORDER BY created_at DESC
        LIMIT 20`,
    [chart_id]
  )
  return rows
}
