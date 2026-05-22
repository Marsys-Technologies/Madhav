/**
 * GET /api/admin/mcp/health/calibration
 *
 * Returns mv_calibration_score rows for the PredictionsCalibration dashboard tab.
 * Also reports the current MSR signal grounding % for the AC.S1.1 badge.
 *
 * Auth: super_admin only (requireSuperAdmin).
 */

import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { getMvCalibrationData } from '@/lib/perf/mv_refresh'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

interface GroundingStats {
  grounded: number
  total: number
}

async function getGroundingPct(): Promise<number | null> {
  try {
    const { rows } = await query<GroundingStats>(`
      SELECT
        count(*) FILTER (WHERE source_citation IS NOT NULL AND source_citation != '') AS grounded,
        count(*) AS total
      FROM msr_signals
      WHERE native_id = 'abhisek'
    `)
    const total   = parseInt(String(rows[0]?.total ?? 0), 10)
    const grounded = parseInt(String(rows[0]?.grounded ?? 0), 10)
    return total > 0 ? grounded / total : null
  } catch {
    return null
  }
}

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    const [calibrationRows, groundingPct] = await Promise.all([
      getMvCalibrationData(),
      getGroundingPct(),
    ])

    return NextResponse.json({
      rows: calibrationRows,
      refreshed_at: calibrationRows.length > 0
        ? calibrationRows.reduce((latest, r) => {
            const ts = r.last_outcome_at
            if (!ts) return latest
            if (!latest) return ts
            return ts > latest ? ts : latest
          }, null as string | null)
        : null,
      grounding_pct: groundingPct,
    })
  } catch (err) {
    console.error('[admin/mcp/health/calibration] error:', err)
    return res.internal('Failed to load calibration data.')
  }
}
