import 'server-only'
import { NextResponse } from 'next/server'
import { guardPerformanceRoute } from '../_guard'
import { getRetrievalStats } from '@/lib/performance/retrieval_aggregator'

export async function GET(request: Request): Promise<NextResponse> {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  const url = new URL(request.url)
  const windowParam = url.searchParams.get('window')
  const windowHours = windowParam ? Math.max(1, Math.min(720, parseInt(windowParam, 10) || 168)) : 168

  try {
    const stats = await getRetrievalStats(windowHours)
    return NextResponse.json(stats)
  } catch (err) {
    console.error('[api/performance/retrieval-stats] failed', err)
    return NextResponse.json({ error: 'retrieval_stats_failed' }, { status: 500 })
  }
}
