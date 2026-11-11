/**
 * DEPRECATED — super-admin stop uses POST /api/cockpit/runs/[id]/stop with a current run ID.
 */
import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json(
    { error: 'Decommissioned. Super admins can stop a run with POST /api/cockpit/runs/[id]/stop using a current run ID.', code: 'ENDPOINT_GONE' },
    { status: 410 },
  )
}
