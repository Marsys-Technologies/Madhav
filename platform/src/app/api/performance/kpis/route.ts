import { NextResponse } from 'next/server'
import { guardPerformanceRoute, parseSource, parseTimeWindow } from '../_guard'
import { computeKpis } from '@/lib/performance/kpi_aggregator'

export async function GET(request: Request) {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  const url = new URL(request.url)
  const win = parseTimeWindow(url)
  if ('error' in win) return NextResponse.json({ error: win.error }, { status: 400 })
  const source = parseSource(url)

  try {
    const data = await computeKpis({ start: win.start, end: win.end, source })
    return NextResponse.json(data)
  } catch (err) {
    console.error('[api/performance/kpis] failed', err)
    return NextResponse.json({ error: 'kpi_compute_failed' }, { status: 500 })
  }
}
