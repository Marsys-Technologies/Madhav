// GET /api/admin/observatory/analytics/anomaly
//
// Phase O — O.4 Analytics — anomaly detection. Authored by USTAD_S4_6.
// Runs the same z-score sweep as the nightly /run endpoint and may dispatch
// configured notifications. Optional query params: lookback_days, z_threshold.

import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardObservatoryRoute } from '../../_guard'
import {
  detectAnomalies,
  type AnomalyConfig,
} from '@/lib/observatory/analytics/anomaly'

function parseConfig(sp: URLSearchParams): Partial<AnomalyConfig> {
  const out: Partial<AnomalyConfig> = {}
  const lookback = sp.get('lookback_days')
  if (lookback !== null) {
    const n = Number(lookback)
    if (Number.isFinite(n) && n > 0) out.lookback_days = Math.floor(n)
  }
  const z = sp.get('z_threshold')
  if (z !== null) {
    const n = Number(z)
    if (Number.isFinite(n) && n > 0) out.z_threshold = n
  }
  const min = sp.get('min_data_points')
  if (min !== null) {
    const n = Number(min)
    if (Number.isFinite(n) && n > 0) out.min_data_points = Math.floor(n)
  }
  return out
}

export async function GET(request: Request) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  const sp = new URL(request.url).searchParams
  const config = parseConfig(sp)

  try {
    const result = await detectAnomalies(config)
    return NextResponse.json(result)
  } catch (err) {
    console.error('[admin/observatory/analytics/anomaly] GET failed', err)
    return res.internal('Failed to detect anomalies.')
  }
}
