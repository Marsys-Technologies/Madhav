'use client'

import { useState } from 'react'
import { CheckCircle2, Fingerprint, ShieldCheck } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

const EVIDENCE_URL = '/api/admin/nirmana-elevation/evidence'

type Props = {
  snapshot: NirmanaElevationSnapshotV2
  onAccepted?: () => void | Promise<void>
}

type AcceptanceCandidate = {
  observationId: string
  observedAt: string
  definitionDigest: string
  catalogueDigest: string
  definitionRevision: string
}

function deterministicDefinitionRevision(observationId: string, observedAt: string): string {
  const date = observedAt.slice(0, 10).replaceAll('-', '')
  return `ntap-${date}-${observationId}`
}

function currentCandidate(snapshot: NirmanaElevationSnapshotV2): AcceptanceCandidate | null {
  const sync = snapshot.program_sync
  const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
  if (sync.status !== 'baseline_missing'
    || monitor?.state !== 'fresh'
    || snapshot.sources.some((source) => source.state !== 'fresh')
    || sync.source_observation_id === null
    || sync.observed_at === null
    || sync.age_seconds === null
    || sync.candidate_definition_sha256 === null
    || sync.candidate_catalogue_sha256 === null) return null

  return {
    observationId: sync.source_observation_id,
    observedAt: sync.observed_at,
    definitionDigest: sync.candidate_definition_sha256,
    catalogueDigest: sync.candidate_catalogue_sha256,
    definitionRevision: deterministicDefinitionRevision(sync.source_observation_id, sync.observed_at),
  }
}

function formatObservedAt(value: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'medium',
    timeZone: 'Asia/Kolkata',
  }).format(new Date(value))
}

function abbreviatedDigest(label: string, digest: string): string {
  return `${label} ${digest.slice(0, 12)}…`
}

function publicFailureMessage(status: number): string {
  if (status === 409) return 'The proposal changed or another baseline was accepted. Refresh the tracker before trying again.'
  if (status === 429) return 'Baseline acceptance is temporarily rate-limited. Wait briefly, then refresh the tracker.'
  if (status === 401 || status === 403) return 'Your super-admin session is no longer authorized. Sign in again, then refresh the tracker.'
  return 'The baseline could not be accepted. No program progress was changed. Refresh the tracker before trying again.'
}

export function BaselineAcceptancePanel({ snapshot, onAccepted }: Props) {
  const candidate = currentCandidate(snapshot)
  const [submitting, setSubmitting] = useState(false)
  const [accepted, setAccepted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!candidate) return null

  const accept = async () => {
    const confirmed = window.confirm(
      'Accept this exact current baseline? This freezes program identity and labels only. It does not start or resume campaign work.',
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
          command: 'accept_baseline_candidate',
          definition_revision: candidate.definitionRevision,
          source_observation_id: candidate.observationId,
          expected_candidate_sha256: candidate.definitionDigest,
          expected_candidate_catalogue_sha256: candidate.catalogueDigest,
        }),
      })
      if (!response.ok) {
        setError(publicFailureMessage(response.status))
        return
      }
      const body: unknown = await response.json()
      if (typeof body !== 'object' || body === null
        || !('outcome' in body)
        || (body.outcome !== 'created' && body.outcome !== 'idempotent')) {
        setError('The server returned an unexpected acceptance result. Refresh the tracker before taking another action.')
        return
      }
      setAccepted(true)
      void Promise.resolve(onAccepted?.()).catch(() => {
        setError('The baseline was accepted, but the tracker could not refresh. Reload the page to retrieve authoritative evidence.')
      })
    } catch {
      setError('The baseline request could not be completed. No program progress was changed. Refresh the tracker before trying again.')
    } finally {
      setSubmitting(false)
    }
  }

  return <section aria-labelledby="baseline-proposal-heading" className="rounded-xl border border-brand-gold-1/50 bg-brand-gold-1/5 p-4">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="max-w-3xl">
        <p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">
          <Fingerprint aria-hidden="true" className="size-4" /> Identity checkpoint
        </p>
        <h2 id="baseline-proposal-heading" className="mt-1 font-serif text-xl text-brand-gold-cream">Current baseline proposal</h2>
        <p className="mt-2 text-sm text-brand-text-2">
          The latest monitor observation can freeze the current program identity and accepted asset labels. This does not mark any stage, layer, or asset as complete.
        </p>
        <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-brand-text-3">
          <div><dt className="inline font-semibold text-brand-text-2">Scope:</dt> <dd className="inline">{snapshot.assets.length} registry assets</dd></div>
          <div><dt className="inline font-semibold text-brand-text-2">Observed:</dt> <dd className="inline">{formatObservedAt(candidate.observedAt)}</dd></div>
          <div><dt className="inline font-semibold text-brand-text-2">Candidate:</dt> <dd className="inline">{abbreviatedDigest('Definition', candidate.definitionDigest)} · {abbreviatedDigest('Labels', candidate.catalogueDigest)}</dd></div>
        </dl>
      </div>
      <button
        type="button"
        disabled={submitting || accepted}
        onClick={() => void accept()}
        className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-brand-gold-1 bg-brand-gold-1/15 px-4 py-2 text-sm font-semibold text-brand-gold-cream transition hover:bg-brand-gold-1/25 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {accepted
          ? <><CheckCircle2 aria-hidden="true" className="size-4" /> Baseline accepted</>
          : <><ShieldCheck aria-hidden="true" className="size-4" /> {submitting ? 'Accepting current baseline' : 'Accept current baseline'}</>}
      </button>
    </div>
    {accepted && <p role="status" className="mt-3 text-sm text-brand-success">Baseline accepted. Refreshing the tracker from authoritative evidence…</p>}
    {error && <p role="alert" className="mt-3 text-sm text-brand-warn">{error}</p>}
  </section>
}
