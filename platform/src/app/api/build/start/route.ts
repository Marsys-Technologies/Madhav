/**
 * DEPRECATED — superseded by POST /api/cockpit/runs
 */
import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json(
    { error: 'Decommissioned. Use POST /api/cockpit/runs.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
