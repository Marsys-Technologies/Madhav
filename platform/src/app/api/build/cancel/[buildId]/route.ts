/**
 * DEPRECATED — superseded by PATCH /api/cockpit/runs/[id] (stop signal)
 */
import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json(
    { error: 'Decommissioned. Use PATCH /api/cockpit/runs/[id] with stop_requested_at.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
