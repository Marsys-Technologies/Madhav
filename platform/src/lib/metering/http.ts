import 'server-only'
import { NextResponse } from 'next/server'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { meteringEnabled } from './types'
import { parseUsageFilter, usageSummary, usageEvents, usageBreakdown, usageConversations, usageCsv, type UsageScope } from './queries'
export async function usageOwner() {
  const ctx = await getServerUserWithProfile()
  if (!ctx) return NextResponse.json({ error:'unauthorized' },{ status:401 })
  if (ctx.profile.status !== 'active') return NextResponse.json({ error:'account_inactive' },{ status:403 })
  if (!meteringEnabled()) return NextResponse.json({ error:'metering_not_enabled' },{ status:404 })
  return ctx
}
export async function usageResponse(request: Request, scope: UsageScope) {
  let input
  try { input = parseUsageFilter(new URL(request.url),scope) }
  catch { return NextResponse.json({ error:'invalid_usage_filters' },{ status:400 }) }
  try {
    if (input.view==='summary') return NextResponse.json(await usageSummary(input,scope),{ headers:{ 'Cache-Control':'private, no-store' } })
    if (input.view==='breakdown') return NextResponse.json(await usageBreakdown(input,scope),{ headers:{ 'Cache-Control':'private, no-store' } })
    if (input.view==='conversations') return NextResponse.json(await usageConversations(input,scope),{ headers:{ 'Cache-Control':'private, no-store' } })
    const data = await usageEvents(input,scope)
    if (input.view==='export') return new NextResponse(usageCsv(data.events),{ headers:{ 'Content-Type':'text/csv; charset=utf-8',
      'Content-Disposition':'attachment; filename="ai-usage.csv"','Cache-Control':'private, no-store',
      ...(data.nextCursor ? { 'X-Next-Cursor':data.nextCursor } : {}) } })
    return NextResponse.json(data,{ headers:{ 'Cache-Control':'private, no-store' } })
  } catch { return NextResponse.json({ error:'usage_unavailable' },{ status:503 }) }
}
