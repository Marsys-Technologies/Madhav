import 'server-only'
import { NextResponse } from 'next/server'
import { getFlag } from '@/lib/config'
import { normalizeAiError } from '@/lib/ai-console/errors'
import { revalidateStaleConnections } from '@/lib/ai-console/revalidation'
import { safeEqual } from '@/lib/security/safe_equal'

export async function POST(request: Request) {
  // Exact existing admin-cron guard: Authorization is reserved for Scheduler OIDC.
  const expected = process.env.MARSYS_CRON_SECRET
  const auth = request.headers.get('x-marsys-cron-secret')
  if (!safeEqual(auth, expected)) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }
  if (!getFlag('AI_CONSOLE_BYOK')) return NextResponse.json({ error: 'not_found' }, { status: 404 })
  try {
    return NextResponse.json(await revalidateStaleConnections(request.signal), { headers: { 'Cache-Control': 'no-store' } })
  } catch (error) {
    return NextResponse.json({ error: normalizeAiError(error, { source: 'provider' }) }, { status: 503, headers: { 'Cache-Control': 'no-store' } })
  }
}
