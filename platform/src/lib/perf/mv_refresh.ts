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

import { createClient } from '@supabase/supabase-js'

// Supabase admin client (service role key required for REFRESH MATERIALIZED VIEW CONCURRENTLY)
function getSupabaseAdmin() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? process.env.SUPABASE_URL ?? ''
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY ?? ''
  if (!url || !key) throw new Error('SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY required for MV refresh')
  return createClient(url, key, { auth: { persistSession: false } })
}

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
  const supabase = getSupabaseAdmin()
  const { error } = await supabase.rpc('refresh_mv', { mv_name: mvName })
  const duration_ms = Date.now() - start

  if (error) {
    // Fall back to direct SQL via the REST API's rpc if a stored proc isn't available
    // (WT-A's v3.1.0-S4 will add the refresh_mv() proc; graceful degradation here)
    console.warn(`[mv_refresh] rpc('refresh_mv') not available for ${mvName}: ${error.message}`)
    return { mv: mvName, refreshed_at: new Date().toISOString(), duration_ms, error: error.message }
  }
  return { mv: mvName, refreshed_at: new Date().toISOString(), duration_ms }
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
  const supabase = getSupabaseAdmin()
  const { data, error } = await supabase
    .from('mv_calibration_score')
    .select('*')
    .order('confidence_band')
    .order('domain')
    .order('horizon_bucket')

  if (error) {
    console.error('[mv_refresh] getMvCalibrationData error:', error.message)
    return []
  }
  return (data ?? []) as CalibrationRow[]
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
