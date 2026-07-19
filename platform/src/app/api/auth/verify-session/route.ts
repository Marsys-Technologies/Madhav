/**
 * POST /api/auth/verify-session — service-to-service Firebase session verification.
 *
 * Called by the MCP sidecar (platform-mcp) during the OAuth callback to verify
 * the user's Firebase __session cookie. This keeps firebase-admin credentials
 * in the platform (amjis-web) only — the MCP sidecar needs no Firebase credentials.
 *
 * Service-to-service only: X-MCP-Internal-Token required.
 *
 * Request body: { session: string }  — the raw __session cookie value.
 *
 * Response 200: { uid: string }    — the verified Firebase UID.
 * Response 401: { error: string }  — invalid session cookie.
 * Response 400: { error: string }  — bad request.
 *
 * M5 — MCP elevation arc (OAuth Firebase round-trip, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { verifySessionCookie } from '@/lib/firebase/server'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { session?: string }
  try {
    body = await request.json() as { session?: string }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.session) {
    return NextResponse.json({ error: 'session cookie required' }, { status: 400 })
  }

  try {
    const decoded = await verifySessionCookie(body.session)
    return NextResponse.json({ uid: decoded.uid })
  } catch (err) {
    // verifySessionCookie throws on invalid/expired cookies.
    const message = err instanceof Error ? err.message : String(err)
    console.error('[auth:verify-session] verifySessionCookie failed:', message)
    return NextResponse.json({ error: 'Invalid or expired session cookie' }, { status: 401 })
  }
}
