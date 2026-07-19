/**
 * /api/mcp/authz — Chart authorization check for the MCP sidecar.
 *
 * Called by platform-mcp before invoking the Python sidecar for chart-scoped
 * tools. Runs authorizeChartAccess and returns the resolved Permission so the
 * MCP server can enforce the gate without a direct DB connection.
 *
 * Auth model: X-MCP-Internal-Token service-to-service header (same as primitives).
 *
 * Request:
 *   POST /api/mcp/authz
 *   X-MCP-Internal-Token: <service-secret>
 *   Body: { user_uid: string; chart_id: string; required: 'view' | 'all' }
 *
 * Response:
 *   { authorized: boolean; permission: 'all' | 'view' | 'deny' }
 *
 * M0 entitlement gate (2026-06-30).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { user_uid?: string; chart_id?: string; required?: 'view' | 'all' }
  try {
    body = (await request.json()) as typeof body
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const { user_uid, chart_id, required = 'view' } = body
  if (!user_uid || !chart_id) {
    return NextResponse.json({ error: 'user_uid and chart_id are required' }, { status: 400 })
  }

  const role = await resolveMcpPrincipalRole(user_uid)
  const permission = await authorizeChartAccess({
    principal: { uid: user_uid, role },
    chartId: chart_id,
    db: { query },
  })

  const authorized = required === 'all' ? permission === 'all' : permission !== 'deny'

  return NextResponse.json({ authorized, permission })
}
