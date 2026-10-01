import { NextResponse } from 'next/server'
import { usageOwner, usageResponse } from '@/lib/metering/http'
export const dynamic = 'force-dynamic'
export async function GET(request: Request) {
  const auth = await usageOwner()
  if (auth instanceof NextResponse) return auth
  return usageResponse(request,{ ownerId:auth.user.uid })
}
