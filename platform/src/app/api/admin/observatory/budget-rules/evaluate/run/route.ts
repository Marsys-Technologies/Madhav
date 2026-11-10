// POST /api/admin/observatory/budget-rules/evaluate/run
//
// Scheduled-run endpoint for the budget rules framework. Cloud Scheduler (or
// any super-admin caller) hits this with an empty body; the handler evaluates
// every active rule against current spend and dispatches alerts for any rule
// whose status is not 'ok'.
//
// Phase O — O.3 Budgets. Authored by USTAD_S3_2_ALERT_DISPATCHER.
//
// Auth: same MARSYS_FLAG_OBSERVATORY_ENABLED + requireSuperAdmin() gate as the rest of
// the observatory admin API. Cloud Scheduler should authenticate as a
// super-admin service account; there is no scheduler-specific bypass.

import { NextResponse } from 'next/server'
import { guardObservatoryRoute } from '../../../_guard'
import { evaluateAllRules } from '@/lib/observatory/budget/evaluate'
import {
  dispatchAlerts,
  type DispatchResult,
} from '@/lib/observatory/budget/alert_dispatcher'

export async function POST() {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  const evaluatedAt = new Date().toISOString()

  let results
  try {
    results = await evaluateAllRules()
  } catch (err) {
    console.error(
      '[admin/observatory/budget-rules/evaluate/run] evaluateAllRules failed',
      err,
    )
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json(
      { error: 'evaluation_failed', message },
      { status: 500 },
    )
  }

  const dispatchResults: DispatchResult[] = []
  let alertsFiredCount = 0
  for (const result of results) {
    if (result.status === 'ok') continue
    alertsFiredCount += 1
    dispatchResults.push(await dispatchAlerts(result))
  }

  return NextResponse.json({
    evaluated_count: results.length,
    alerts_fired_count: alertsFiredCount,
    dispatch_results: dispatchResults,
    evaluated_at: evaluatedAt,
  })
}
