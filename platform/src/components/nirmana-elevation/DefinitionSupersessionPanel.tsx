'use client'

import { useState } from 'react'
import { CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

const EVIDENCE_URL = '/api/admin/nirmana-elevation/evidence'

type Props = {
  snapshot: NirmanaElevationSnapshotV2
  onSuperseded?: () => Promise<boolean>
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
  const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
  const noProjectedCampaignUsage = snapshot.audit.raw_ledger_refs.length === 0 && snapshot.active_runs.length === 0
  if (sync.status !== 'plan_adaptation_required'
    || snapshot.campaign.campaign_id !== 'nirmana-elevation'
    || snapshot.campaign.definition_status !== 'frozen'
    || snapshot.campaign.definition_revision === null
    || monitor?.state !== 'fresh'
    || snapshot.sources.some((source) => source.state !== 'fresh')
    || snapshot.release.production_in_sync !== true
    || !noProjectedCampaignUsage
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

function publicFailureMessage(status: number): string {
  if (status === 409) return 'The proposal changed or no longer meets the supersession safeguards. Refresh the tracker before trying again.'
  if (status === 429) return 'Definition supersession is temporarily rate-limited. Wait briefly, then refresh the tracker.'
  if (status === 401 || status === 403) return 'Your super-admin session is no longer authorized. Sign in again, then refresh the tracker.'
  if (status === 503) return 'Supersession safeguards could not be verified. No definition change was made. Refresh the tracker before trying again.'
  return 'The definition could not be superseded. No program progress was changed. Refresh the tracker before trying again.'
}

export function DefinitionSupersessionPanel({ snapshot, onSuperseded }: Props) {
  const candidate = currentCandidate(snapshot)
  const [submitting, setSubmitting] = useState(false)
  const [superseded, setSuperseded] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!candidate) return null

  const supersede = async () => {
    const confirmed = window.confirm(
      'Supersede this exact frozen definition with the displayed candidate? This is a governed plan replacement, not permission to start or resume campaign work.',
    )
    if (!confirmed) return

    setSubmitting(true)
    setError(null)
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
        setError(publicFailureMessage(response.status))
        return
      }
      const body: unknown = await response.json()
      if (typeof body !== 'object' || body === null
        || !('outcome' in body)
        || (body.outcome !== 'superseded' && body.outcome !== 'idempotent')) {
        setError('The server returned an unexpected supersession result. Refresh the tracker before taking another action.')
        return
      }
      setSuperseded(true)
      if (onSuperseded) {
        setRefreshing(true)
        let refreshed = false
        try {
          refreshed = await onSuperseded()
        } catch {
          refreshed = false
        }
        setRefreshing(false)
        if (!refreshed) {
          setError('The definition was superseded, but current evidence could not refresh. Reload the page to retrieve authoritative evidence.')
        }
      }
    } catch {
      setError('The supersession request could not be completed. No definition change was made. Refresh the tracker before trying again.')
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
        <p className="mt-3 text-xs text-brand-text-3">Current tracker evidence shows no accepted campaign receipts or active runs. The server rechecks every supersession safeguard atomically.</p>
      </div>
      <button
        type="button"
        disabled={submitting || superseded}
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
    {error && <p role="alert" className="mt-3 text-sm text-brand-warn">{error}</p>}
  </section>
}
