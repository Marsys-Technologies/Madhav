/**
 * GET /api/brahma/sutravali/by_planet/[planet]
 *
 * Proxy to Python sidecar: /api/brahma/sutravali/by_planet/{planet}
 * Returns all sutravali rules for the given planet canonical name.
 * Internal endpoint used by MCP resource marsys://resource/sutravali/all-by-planet/{planet}
 *
 * Auth: x-mcp-internal-token header required.
 *
 * BRAHMA L0 Stream D — Sūtravali (2026-06-07)
 */

import { NextRequest, NextResponse } from 'next/server'
import { validateServiceToken } from '@/lib/mcp/service_token'

const SIDECAR_URL = (process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000').replace(/\/$/, '')
const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ planet: string }> }
): Promise<NextResponse> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 })
  }

  const { planet } = await params
  const limit = req.nextUrl.searchParams.get('limit') ?? '500'

  try {
    const sidecarResp = await fetch(
      `${SIDECAR_URL}/api/brahma/sutravali/by_planet/${encodeURIComponent(planet)}?limit=${limit}`,
      {
        headers: { 'x-api-key': SIDECAR_KEY },
        signal: AbortSignal.timeout(10_000),
      }
    )
    if (!sidecarResp.ok) {
      return NextResponse.json({ error: 'sidecar_error', status: sidecarResp.status }, { status: 502 })
    }
    const data = await sidecarResp.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error('[sutravali/by_planet] sidecar fetch error:', err)
    return NextResponse.json({ error: 'sidecar_unreachable' }, { status: 502 })
  }
}
