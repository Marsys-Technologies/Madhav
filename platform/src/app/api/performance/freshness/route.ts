import 'server-only'
import { NextResponse } from 'next/server'
import { guardPerformanceRoute } from '../_guard'
import { getFreshnessReport } from '@/lib/performance/freshness'

export async function GET(): Promise<NextResponse> {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const report = getFreshnessReport()
    return NextResponse.json(report)
  } catch (err) {
    console.error('[api/performance/freshness] failed', err)
    return NextResponse.json({ error: 'freshness_report_failed' }, { status: 500 })
  }
}
