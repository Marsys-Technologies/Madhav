/**
 * mv_refresh.ts — Materialized view refresh scheduler (Track B — v3.4-S1)
 *
 * Refreshes the perf-system materialized views on their schedules:
 *   - mv_tool_metrics_24h      → every 5 min (WT-A migration 073 creates it)
 *   - mv_data_source_coverage  → every 5 min (WT-A migration 073 creates it)
 *   - mv_grounding_rate        → every 5 min (WT-A migration 073 creates it)
 *   - mv_calibration_score     → nightly at 04:00 UTC (wilson.sql creates it)
 *
 * This module exports:
 *   - refreshMvCalibrationScore()  — single MV refresh, called by the nightly job
 *   - refreshAll5min()             — refreshes all 5-min MVs
 *   - getMvCalibrationData()       — reads mv_calibration_score for the dashboard
 *
 * The 5-min MVs are refreshed by a setInterval started in the Next.js server
 * startup (or a Cloud Scheduler job POSTing to /api/admin/mcp/mv-refresh).
 * mv_calibration_score is refreshed by a Cloud Scheduler job at 04:00 UTC daily.
 */

import { query as dbQuery } from '../db/client'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface CalibrationRow {
  confidence_band: string
  domain: string
  horizon_bucket: string
  total_predictions: number
  realized: number
  disconfirmed: number
  partial: number
  pending: number
  realized_rate: number | null
  realized_rate_ci_low: number | null
  realized_rate_ci_high: number | null
  last_outcome_at: string | null
}

export interface MvRefreshResult {
  mv: string
  refreshed_at: string
  duration_ms: number
  error?: string
}

// ── Refresh helpers ───────────────────────────────────────────────────────────

async function refreshMv(mvName: string): Promise<MvRefreshResult> {
  const start = Date.now()
  try {
    await dbQuery(`REFRESH MATERIALIZED VIEW CONCURRENTLY ${mvName}`)
    return { mv: mvName, refreshed_at: new Date().toISOString(), duration_ms: Date.now() - start }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.warn(`[mv_refresh] refresh failed for ${mvName}: ${msg}`)
    return { mv: mvName, refreshed_at: new Date().toISOString(), duration_ms: Date.now() - start, error: msg }
  }
}

export async function refreshMvCalibrationScore(): Promise<MvRefreshResult> {
  return refreshMv('mv_calibration_score')
}

export async function refreshAll5min(): Promise<MvRefreshResult[]> {
  const MVS_5MIN = ['mv_tool_metrics_24h', 'mv_data_source_coverage', 'mv_grounding_rate']
  return Promise.all(MVS_5MIN.map(refreshMv))
}

// ── Data readers ─────────────────────────────────────────────────────────────

export async function getMvCalibrationData(): Promise<CalibrationRow[]> {
  try {
    const result = await dbQuery<CalibrationRow>(
      `SELECT * FROM mv_calibration_score ORDER BY confidence_band, domain, horizon_bucket`
    )
    return result.rows
  } catch (err) {
    console.error('[mv_refresh] getMvCalibrationData error:', err instanceof Error ? err.message : String(err))
    return []
  }
}

// ── Nightly job entry point ───────────────────────────────────────────────────
// Called by Cloud Scheduler POST /api/admin/mcp/mv-refresh?mv=calibration

export async function runNightlyCalibrationRefresh(): Promise<void> {
  console.log('[mv_refresh] nightly mv_calibration_score refresh starting...')
  const result = await refreshMvCalibrationScore()
  if (result.error) {
    console.error(`[mv_refresh] refresh failed: ${result.error}`)
    throw new Error(result.error)
  }
  console.log(`[mv_refresh] mv_calibration_score refreshed in ${result.duration_ms}ms`)
}
