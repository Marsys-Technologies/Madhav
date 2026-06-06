/**
 * DEPRECATED — superseded by GET /api/cockpit/sse
 * build_events table decommissioned with migration 173.
 */
import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json(
    { error: 'Decommissioned. Use GET /api/cockpit/sse.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
