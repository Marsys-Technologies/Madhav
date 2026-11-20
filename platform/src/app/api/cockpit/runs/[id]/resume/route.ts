import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { claimPausedBuildRun, readBuildRunResumeState, restorePausedBuildRunAfterDispatchFailure } from '@/lib/build/runControlData'
import { invokeRunJob } from '@/lib/build/jobInvoker'

export const maxDuration = 8

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const user = await requireSuperAdmin()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const { id } = await params

  try {
    // Claim first. The Cloud Run invocation is intentionally outside the SQL
    // statement, but only the request that atomically moved paused -> planned may
    // dispatch it. The runner itself owns planned -> running after its lock.
    const result = await claimPausedBuildRun(id)

    if (result.rows.length === 0) {
      const { rows } = await readBuildRunResumeState(id)
      if (rows[0]?.state === 'paused' && !rows[0].has_manifest) {
        return NextResponse.json({
          error: 'This paused run predates immutable manifests and cannot be resumed safely',
          code: 'LEGACY_RUN_MANIFEST_MISSING',
        }, { status: 409 })
      }
      return NextResponse.json({ error: 'Run not found or not in paused state' }, { status: 404 })
    }

    const requestedAt = result.rows[0].resume_requested_at
    try {
      // A paused writer can have matching input receipts from before it wrote.
      // This also covers a one-asset repair of a larger interrupted preparation.
      await invokeRunJob(id, { forceExecute: true })
    } catch (err) {
      const detail = (err as Error).message
      // Do not strand a paused run as planned when the dispatch did not happen.
      // The state predicate prevents an unusually fast runner from being moved
      // backwards after it has already claimed the work.
      await restorePausedBuildRunAfterDispatchFailure(detail, id, requestedAt)
      console.error('[cockpit/runs/resume] job dispatch failed:', detail)
      return NextResponse.json(
        { error: 'Failed to dispatch resumed build job', detail, run_id: id, code: 'JOB_DISPATCH_FAILED' },
        { status: 503 }
      )
    }

    return NextResponse.json({ data: { run_id: id, resumed: true } })
  } catch (err) {
    console.error('[cockpit/runs/resume]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}
