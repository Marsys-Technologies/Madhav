/**
 * /clients/[id]/pratikruti — BA-P7B Portal Learning Loops
 *
 * Five learning loop surfaces for the native:
 *   Step 1  Ask-Cards (Loop C)      — adjudicate UNRESOLVED closed predictions
 *   Step 2  LEL Intake              — structured life-event entry → markdown append
 *   Step 3  Prashna Follow-ups (Loop B) — due follow-up asks from Q4 verdicts
 *   Step 4  Co-Sign Surface         — approve/revoke calibration snapshots
 *   Step 5  Resonance (QUARANTINED) — reading resonance capture (no path to weights)
 */

import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { PratikrutiClient } from './PratikrutiClient'

export default async function PratikrutiPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 space-y-8">
      <div>
        <h1 className="text-xl font-serif font-semibold text-foreground">
          Pratikruti — Learning Loops
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Adjudicate predictions, add life events, and co-sign calibration snapshots.
        </p>
      </div>
      <PratikrutiClient chartId={id} />
    </div>
  )
}
