'use client'

import { useRef, useState } from 'react'
import { CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

const EVIDENCE_URL = '/api/admin/nirmana-elevation/evidence'

type Props = {
  snapshot: NirmanaElevationSnapshotV2
  onRefresh?: () => Promise<boolean>
}

type SupersessionCandidate = {
  observationId: string
  observedAt: string
  currentRevision: string
  currentDigest: string
  candidateDigest: string
  candidateCatalogueDigest: string
  newRevision: string
}

function deterministicRevision(observationId: string, observedAt: string): string {
  return `ntap-${observedAt.slice(0, 10).replaceAll('-', '')}-${observationId}`
}

function currentCandidate(snapshot: NirmanaElevationSnapshotV2): SupersessionCandidate | null {
  const sync = snapshot.program_sync
  if (!sync.supersession_eligible
    || snapshot.campaign.campaign_id !== 'nirmana-elevation'
    || snapshot.campaign.definition_status !== 'frozen'
    || snapshot.campaign.definition_revision === null
    || sync.source_observation_id === null
    || sync.observed_at === null
    || sync.current_definition_sha256 === null
    || sync.candidate_definition_sha256 === null
    || sync.candidate_catalogue_sha256 === null) return null

  return {
    observationId: sync.source_observation_id,
    observedAt: sync.observed_at,
    currentRevision: snapshot.campaign.definition_revision,
    currentDigest: sync.current_definition_sha256,
    candidateDigest: sync.candidate_definition_sha256,
    candidateCatalogueDigest: sync.candidate_catalogue_sha256,
    newRevision: deterministicRevision(sync.source_observation_id, sync.observed_at),
  }
}

function formatObservedAt(value: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'medium',
    timeZone: 'Asia/Kolkata',
  }).format(new Date(value))
}

const BLOCKER_COPY: Record<NirmanaElevationSnapshotV2['program_sync']['supersession_blockers'][number], string> = {
  not_plan_adaptation: 'The observation is not a plan-adaptation proposal.',
  current_definition_not_frozen: 'The current definition is not frozen.',
  current_definition_mismatch: 'The observation does not match the current definition.',
  candidate_mismatch: 'The live candidate no longer matches the observation.',
  source_unavailable: 'The authoritative monitor source is unavailable.',
  source_error: 'The authoritative monitor reported a source error.',
  observation_incomplete: 'The monitor observation is incomplete.',
  observation_stale: 'The monitor observation is no longer fresh.',
  release_not_in_sync: 'The release is not in sync.',
  runtime_not_quiet: 'The monitored runtime is not quiet.',
  campaign_events_present: 'The current definition already has campaign events.',
  definition_build_runs_present: 'The current definition already has build runs.',
  revision_not_unique: 'The proposed definition revision is already in use.',
  candidate_reconstruction_failed: 'The server could not reconstruct the candidate safely.',
}

export function DefinitionSupersessionPanel({ snapshot, onRefresh }: Props) {
  const candidate = currentCandidate(snapshot)
  const candidateIdentity = candidate === null ? null : [candidate.observationId, candidate.currentDigest, candidate.candidateDigest, candidate.candidateCatalogueDigest, candidate.newRevision].join(':')
  const requestGate = useRef<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [supersededIdentity, setSupersededIdentity] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [indeterminateResult, setIndeterminateResult] = useState<{ identity: string; message: string } | null>(null)
  const superseded = supersededIdentity === candidateIdentity
  const refreshRequired = indeterminateResult?.identity === candidateIdentity
  const error = refreshRequired ? indeterminateResult.message : null

  const refreshAfterIndeterminateResult = async (message: string) => {
    if (candidateIdentity === null) return
    setIndeterminateResult({ identity: candidateIdentity, message })
    if (!onRefresh) return
    setRefreshing(true)
    try {
      await onRefresh()
    } catch {
      // The view remains latched until its candidate identity changes.
    } finally {
      setRefreshing(false)
    }
  }

  if (!candidate) {
    if (snapshot.program_sync.status !== 'plan_adaptation_required' || snapshot.program_sync.supersession_blockers.length === 0) return null
    return <section role="status" aria-labelledby="definition-supersession-unavailable-heading" className="rounded-xl border border-brand-warn/60 bg-brand-warn/10 p-4">
      <h2 id="definition-supersession-unavailable-heading" className="font-serif text-lg text-brand-gold-cream">Definition supersession unavailable</h2>
      <p className="mt-1 text-sm text-brand-text-2">The server-derived eligibility check has withheld this control. Refresh the tracker after resolving every blocker.</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-brand-text-3">
        {snapshot.program_sync.supersession_blockers.map((blocker) => <li key={blocker}>{BLOCKER_COPY[blocker]}</li>)}
      </ul>
    </section>
  }

  const supersede = async () => {
    if (candidateIdentity === null || submitting || superseded || refreshRequired || requestGate.current === candidateIdentity) return
    const confirmed = window.confirm(
      'Supersede this exact frozen definition with the displayed candidate? This is a governed plan replacement, not permission to start or resume campaign work.',
    )
    if (!confirmed) return

    requestGate.current = candidateIdentity
    setSubmitting(true)
    try {
      const response = await fetch(EVIDENCE_URL, {
        method: 'POST',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: 'supersede_definition',
          campaign_id: 'nirmana-elevation',
          expected_current_revision: candidate.currentRevision,
          expected_current_manifest_sha256: candidate.currentDigest,
          source_observation_id: candidate.observationId,
          expected_candidate_sha256: candidate.candidateDigest,
          expected_candidate_catalogue_sha256: candidate.candidateCatalogueDigest,
          new_definition_revision: candidate.newRevision,
        }),
      })
      if (!response.ok) {
        await refreshAfterIndeterminateResult(response.status === 409
          ? 'The server safely refused this proposal because it changed or no longer meets the supersession safeguards. Refresh is required before another request.'
          : 'The server did not provide a definitive supersession outcome. Refresh is required before another request.')
        return
      }
      const body: unknown = await response.json()
      if (typeof body !== 'object' || body === null
        || !('outcome' in body)
        || (body.outcome !== 'superseded' && body.outcome !== 'idempotent')) {
        await refreshAfterIndeterminateResult('The server response was not a definitive supersession outcome. Refresh is required before another request.')
        return
      }
      setSupersededIdentity(candidateIdentity)
      if (onRefresh) {
        setRefreshing(true)
        let refreshed = false
        try {
          refreshed = await onRefresh()
        } catch {
          refreshed = false
        }
        setRefreshing(false)
        if (!refreshed) {
          setIndeterminateResult({ identity: candidateIdentity, message: 'The definition was superseded, but current evidence could not refresh. Reload the page to retrieve authoritative evidence.' })
        }
      }
    } catch {
      await refreshAfterIndeterminateResult('The supersession request result is unknown. Refresh is required before another request.')
    } finally {
      setSubmitting(false)
    }
  }

  return <section aria-labelledby="definition-supersession-heading" className="rounded-xl border border-brand-warn/60 bg-brand-warn/10 p-4">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="max-w-3xl">
        <p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-warn">
          <ShieldAlert aria-hidden="true" className="size-4" /> Governed plan replacement
        </p>
        <h2 id="definition-supersession-heading" className="mt-1 font-serif text-xl text-brand-gold-cream">Supersede the frozen definition</h2>
        <p className="mt-2 text-sm text-brand-text-2">
          This candidate is bound to the latest monitor observation. The server reconstructs the replacement definition and labels itself; this control never submits a caller-provided manifest.
        </p>
        <dl className="mt-3 grid gap-2 text-xs text-brand-text-3 sm:grid-cols-[auto_minmax(0,1fr)]">
          <dt className="font-semibold text-brand-text-2">Observation</dt><dd className="break-all font-mono">{candidate.observationId} · {formatObservedAt(candidate.observedAt)}</dd>
          <dt className="font-semibold text-brand-text-2">Current revision</dt><dd className="break-all font-mono">{candidate.currentRevision}</dd>
          <dt className="font-semibold text-brand-text-2">Current definition</dt><dd className="break-all font-mono">{candidate.currentDigest}</dd>
          <dt className="font-semibold text-brand-text-2">Candidate definition</dt><dd className="break-all font-mono">{candidate.candidateDigest}</dd>
          <dt className="font-semibold text-brand-text-2">Candidate labels</dt><dd className="break-all font-mono">{candidate.candidateCatalogueDigest}</dd>
          <dt className="font-semibold text-brand-text-2">New revision</dt><dd className="break-all font-mono">{candidate.newRevision}</dd>
        </dl>
        <p className="mt-3 text-xs text-brand-text-3">This eligibility decision is server-derived from the authoritative monitor, definition, event, build-run, and live-candidate checks. The server rechecks it atomically when submitted.</p>
      </div>
      <button
        type="button"
        disabled={submitting || superseded || refreshRequired}
        onClick={() => void supersede()}
        className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-brand-warn bg-brand-warn/15 px-4 py-2 text-sm font-semibold text-brand-gold-cream transition hover:bg-brand-warn/25 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {superseded
          ? <><CheckCircle2 aria-hidden="true" className="size-4" /> Definition superseded</>
          : <><ShieldCheck aria-hidden="true" className="size-4" /> {submitting ? 'Superseding definition' : 'Supersede definition'}</>}
      </button>
    </div>
    {superseded && refreshing && <p role="status" className="mt-3 text-sm text-brand-success">Definition superseded. Refreshing the tracker from authoritative evidence…</p>}
    {superseded && !refreshing && !error && <p role="status" className="mt-3 text-sm text-brand-success">Definition superseded. Current evidence refreshed.</p>}
    {refreshRequired && refreshing && <p role="status" className="mt-3 text-sm text-brand-warn">Refreshing authoritative evidence before another request…</p>}
    {refreshRequired && !refreshing && <p role="status" className="mt-3 text-sm text-brand-warn">This candidate is locked until the authoritative snapshot identity changes.</p>}
    {error && <p role="alert" className="mt-3 text-sm text-brand-warn">{error}</p>}
  </section>
}
