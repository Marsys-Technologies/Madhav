/**
 * DEPRECATED — superseded by GET /api/cockpit/runs/active
 */
import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json(
    { error: 'Decommissioned. Use GET /api/cockpit/runs/active.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
