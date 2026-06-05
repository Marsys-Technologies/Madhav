/**
 * GET /api/sidecar/health
 *
 * Server-side proxy for the Python sidecar /health endpoint.
 * Clients cannot call the sidecar directly (CORS restricts to Cloud Run origin).
 * Auth: requires authenticated user (401 if not).
 *
 * Response: { healthy: boolean; status?: string }
 * Cache-Control: no-store (health must be fresh).
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'

export const dynamic = 'force-dynamic'

export async function GET(): Promise<Response> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const sidecarUrl = process.env.PYTHON_SIDECAR_URL
  if (!sidecarUrl) {
    return NextResponse.json({ healthy: false }, { status: 200 })
  }

  try {
    const res = await fetch(`${sidecarUrl}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) return NextResponse.json({ healthy: false }, { status: 200 })
    const body = await res.json().catch(() => ({}))
    return NextResponse.json(
      { healthy: true, status: body?.status ?? 'ok' },
      { status: 200, headers: { 'Cache-Control': 'no-store' } },
    )
  } catch {
    return NextResponse.json({ healthy: false }, { status: 200 })
  }
}
