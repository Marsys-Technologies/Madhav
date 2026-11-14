// GET /api/admin/observatory/analytics/pricing-diff
//
// Read-only health check of the per-provider pricing model. Runs the same
// collection SQL as the explicit POST command without dispatching alerts.
//
// Phase O — O.4 Analytics. Authored by USTAD_S4_4_PRICING_DIFF.

import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardObservatoryRoute } from '../../_guard'
import { collectPricingHealth } from '@/lib/observatory/analytics/pricing_diff'

export async function GET() {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const result = await collectPricingHealth()
    return NextResponse.json(result)
  } catch (err) {
    console.error('[admin/observatory/analytics/pricing-diff] GET failed', err)
    return res.internal('Failed to check pricing health.')
  }
}
