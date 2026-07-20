/**
 * GET /api/mcp/my/charts — return the caller's entitled chart list.
 *
 * Called by platform-mcp list_my_charts tool via the X-MCP-Internal-Token
 * service-to-service header. The MCP sidecar passes the resolved principal's
 * uid + role (from Bearer key validation); this route delegates to
 * getEntitledCharts and returns the entitled set.
 *
 * Request:
 *   GET /api/mcp/my/charts
 *   X-MCP-Internal-Token: <service-secret>
 *   X-MCP-User: <user_uid>
 *   X-MCP-Role: guest | super_admin
 *
 * Response:
 *   200: { charts: [{ id: string; display_name: string; index: number }] }
 *   400: { error: string }  — missing required headers
 *   401: { error: string }  — invalid service token
 *
 * M2 chart selection (MCP elevation arc, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { getEntitledCharts } from '@/lib/auth/getEntitledCharts'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function GET(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const uid = request.headers.get('x-mcp-user')
  const roleHeader = request.headers.get('x-mcp-role')

  if (!uid) {
    return NextResponse.json({ error: 'X-MCP-User header required' }, { status: 400 })
  }

  const role: 'guest' | 'super_admin' =
    roleHeader === 'super_admin' ? 'super_admin' : 'guest'

  const charts = await getEntitledCharts(uid, role, { query })

  return NextResponse.json({
    charts: charts.map((c, index) => ({
      id: c.id,
      display_name: c.display_name,
      index,
    })),
  })
}
