/**
 * DEPRECATED — superseded by GET /api/cockpit/status
 * build_events and build_steps tables decommissioned with migration 173.
 */
import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json(
    { error: 'Decommissioned. Use GET /api/cockpit/status.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
