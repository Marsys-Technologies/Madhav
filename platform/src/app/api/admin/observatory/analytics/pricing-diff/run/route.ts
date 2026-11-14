// POST /api/admin/observatory/analytics/pricing-diff/run
//
// Scheduled-run endpoint: explicitly collects pricing health and dispatches
// alerts for unhealthy providers. GET only collects; command effects belong
// to this POST endpoint (checkPricingHealth).
//
// Phase O — O.4 Analytics. Authored by USTAD_S4_4_PRICING_DIFF.

import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardObservatoryRoute } from '../../../_guard'
import { checkPricingHealth } from '@/lib/observatory/analytics/pricing_diff'

export async function POST() {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const result = await checkPricingHealth()
    return NextResponse.json(result)
  } catch (err) {
    console.error(
      '[admin/observatory/analytics/pricing-diff/run] POST failed',
      err,
    )
    return res.internal('Failed to run pricing diff check.')
  }
}
