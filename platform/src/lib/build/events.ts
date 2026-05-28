/**
 * build_events read + write helpers for the cockpit SSE rail.
 *
 * The write side (`recordBuildEvent`) is also called by the task handler to
 * surface "dispatched" / "failed_to_dispatch" rows; the Python pipeline
 * appends its own rows directly via SQL.
 */

import 'server-only'
import { query } from '@/lib/db/client'

export interface BuildEventRow {
  build_id: string
  stage_seq: number
  chart_id: string
  ayanamsha_role: string
  asset: string
  stage: string
  status: 'started' | 'progress' | 'complete' | 'failed' | 'rolled_back'
  percent: number | null
  message: string | null
  metadata: Record<string, unknown>
  emitted_at: string
}

export async function listBuildEvents(buildId: string): Promise<BuildEventRow[]> {
  const res = await query<BuildEventRow>(
    `SELECT build_id, stage_seq, chart_id, ayanamsha_role,
            asset, stage, status, percent, message, metadata, emitted_at
       FROM build_events
      WHERE build_id = $1
      ORDER BY stage_seq ASC`,
    [buildId],
  )
  return res.rows
}

export async function listLatestBuildForChart(chartId: string): Promise<string | null> {
  const res = await query<{ build_id: string }>(
    `SELECT build_id
       FROM build_events
      WHERE chart_id = $1
   ORDER BY emitted_at DESC
      LIMIT 1`,
    [chartId],
  )
  return res.rows[0]?.build_id ?? null
}

export interface BuildEventInput {
  buildId: string
  chartId: string
  ayanamshaRole: string
  asset: string
  stage: string
  status: BuildEventRow['status']
  percent?: number | null
  message?: string | null
  metadata?: Record<string, unknown>
}

/**
 * Append the next stage_seq for build_id. Single-writer assumption inside the
 * task handler — concurrent writes from the Python pipeline use its own
 * monotonically-increasing counter; conflicts are tolerated via the PK.
 */
export async function recordBuildEvent(ev: BuildEventInput): Promise<number> {
  const seqRes = await query<{ next_seq: number }>(
    `SELECT COALESCE(MAX(stage_seq), -1) + 1 AS next_seq
       FROM build_events
      WHERE build_id = $1`,
    [ev.buildId],
  )
  const seq = seqRes.rows[0]?.next_seq ?? 1
  await query(
    `INSERT INTO build_events
       (build_id, stage_seq, chart_id, ayanamsha_role,
        asset, stage, status, percent, message, metadata)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
     ON CONFLICT (build_id, stage_seq) DO NOTHING`,
    [
      ev.buildId,
      seq,
      ev.chartId,
      ev.ayanamshaRole,
      ev.asset,
      ev.stage,
      ev.status,
      ev.percent ?? null,
      ev.message ?? null,
      JSON.stringify(ev.metadata ?? {}),
    ],
  )
  return seq
}
