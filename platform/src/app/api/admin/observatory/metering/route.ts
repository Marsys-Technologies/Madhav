import { NextResponse } from 'next/server'
import { guardObservatoryRoute } from '../_guard'
import { usageResponse } from '@/lib/metering/http'
import { meteringEnabled } from '@/lib/metering/types'
export const dynamic = 'force-dynamic'
export async function GET(request: Request) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth
  if (!meteringEnabled()) return NextResponse.json({ error:'metering_not_enabled' },{ status:404 })
  return usageResponse(request,{ ownerId:null })
}
