/**
 * DEPRECATED — superseded by POST /api/cockpit/watchdog
 */
import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json(
    { error: 'Decommissioned. Use POST /api/cockpit/watchdog.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
