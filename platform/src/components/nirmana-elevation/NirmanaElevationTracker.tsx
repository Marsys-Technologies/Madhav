'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, CloudOff, ShieldCheck } from 'lucide-react'
import {
  NirmanaElevationSnapshotSchema,
  type NirmanaElevationSnapshot,
  type NirmanaElevationSnapshotV2,
} from '@/lib/nirmana-elevation/types'
import { AuditDrawer } from './AuditDrawer'
import { BaselineAcceptancePanel } from './BaselineAcceptancePanel'
import { CampaignSnapshotStrip } from './CampaignSnapshotStrip'
import { CampaignSpine } from './CampaignSpine'
import {
  NIRMANA_V1_PUBLIC_SOURCE_ERROR,
  NirmanaElevationTrackerV1,
} from './NirmanaElevationTrackerV1'
import { NowNextRail } from './NowNextRail'

const SNAPSHOT_URL = '/api/admin/nirmana-elevation/snapshot'
const DEFAULT_VISIBLE_POLL_MS = 15_000
const DEFAULT_HIDDEN_POLL_MS = 60_000
const MAX_BACKOFF_MS = 300_000

type Props = {
  /** Test-only interval override. The production page uses the safe defaults. */
  pollIntervalMs?: number
  hiddenPollIntervalMs?: number
}

type SnapshotFailure = {
  message: string
  occurredAt: Date
}

class SnapshotUnavailableError extends Error {}

function formatTime(value: string | Date | null | undefined): string {
  if (!value) return 'Unknown'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.valueOf())) return 'Unknown'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(date)
}

function failureMessage(snapshot: NirmanaElevationSnapshot): string {
  if (snapshot.schema_version === '1.0') {
    const unavailable = snapshot.sources.find((source) => source.state === 'unavailable' && source.error)
    return unavailable ? NIRMANA_V1_PUBLIC_SOURCE_ERROR : 'The snapshot source is unavailable.'
  }
  const unavailable = snapshot.sources.find((source) => source.state === 'unavailable' && source.error_message)
  return unavailable?.error_message ?? 'The snapshot source is unavailable.'
}

function NirmanaElevationTrackerV2View({ snapshot, onBaselineAccepted }: {
  snapshot: NirmanaElevationSnapshotV2
  onBaselineAccepted?: () => void | Promise<void>
}) {
  const [auditAssetId, setAuditAssetId] = useState<string | null>(null)
  const [auditOpen, setAuditOpen] = useState(false)
  const auditOpener = useRef<HTMLElement | null>(null)

  const rememberAuditOpener = () => {
    auditOpener.current = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
  }

  const openAudit = (assetId: string) => {
    rememberAuditOpener()
    setAuditAssetId(assetId)
    setAuditOpen(true)
  }

  const onAuditOpenChange = (open: boolean) => {
    if (open) rememberAuditOpener()
    setAuditAssetId(null)
    setAuditOpen(open)
  }

  return <main className="space-y-4">
    <CampaignSnapshotStrip snapshot={snapshot} />
    <BaselineAcceptancePanel
      key={snapshot.program_sync.source_observation_id ?? snapshot.program_sync.status}
      snapshot={snapshot}
      onAccepted={onBaselineAccepted}
    />
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
      <CampaignSpine snapshot={snapshot} onOpenAudit={openAudit} />
      <NowNextRail snapshot={snapshot} />
    </div>
    <AuditDrawer
      snapshot={snapshot}
      assetId={auditAssetId}
      open={auditOpen}
      onOpenChange={onAuditOpenChange}
      finalFocus={auditOpener}
    />
  </main>
}

export function NirmanaElevationTrackerView({ snapshot, fetchedAt, onBaselineAccepted }: {
  snapshot: NirmanaElevationSnapshot
  fetchedAt: Date
  onBaselineAccepted?: () => void | Promise<void>
}) {
  if (snapshot.schema_version === '1.0') {
    return <NirmanaElevationTrackerV1 snapshot={snapshot} fetchedAt={fetchedAt} />
  }
  return <NirmanaElevationTrackerV2View snapshot={snapshot} onBaselineAccepted={onBaselineAccepted} />
}

export function NirmanaElevationTracker({
  pollIntervalMs = DEFAULT_VISIBLE_POLL_MS,
  hiddenPollIntervalMs = DEFAULT_HIDDEN_POLL_MS,
}: Props) {
  const [snapshot, setSnapshot] = useState<NirmanaElevationSnapshot | null>(null)
  const [fetchedAt, setFetchedAt] = useState<Date | null>(null)
  const [failure, setFailure] = useState<SnapshotFailure | null>(null)
  const [failures, setFailures] = useState(0)
  const [visible, setVisible] = useState(() => typeof document === 'undefined' || document.visibilityState !== 'hidden')
  const requestId = useRef(0)
  const abortController = useRef<AbortController | null>(null)
  const mounted = useRef(false)

  const refresh = useCallback(async () => {
    abortController.current?.abort()
    const controller = new AbortController()
    abortController.current = controller
    const currentRequest = ++requestId.current
    try {
      const response = await fetch(SNAPSHOT_URL, { cache: 'no-store', signal: controller.signal })
      const parsed = NirmanaElevationSnapshotSchema.safeParse(await response.json())
      if (!parsed.success) throw new SnapshotUnavailableError('The snapshot response did not satisfy the shared evidence contract.')
      const body = parsed.data
      if (!response.ok) throw new SnapshotUnavailableError(failureMessage(body))
      if (!mounted.current || currentRequest !== requestId.current) return
      setSnapshot(body)
      setFetchedAt(new Date())
      setFailure(null)
      setFailures(0)
    } catch (error) {
      if (controller.signal.aborted || !mounted.current || currentRequest !== requestId.current) return
      const message = error instanceof SnapshotUnavailableError
        ? error.message
        : error instanceof Error
          ? error.message
          : 'The live snapshot could not be loaded.'
      setFailure({ message, occurredAt: new Date() })
      setFailures((count) => count + 1)
    }
  }, [])

  useEffect(() => {
    mounted.current = true
    // Schedule after subscription setup so the initial request is cancellable on unmount.
    const initialRefresh = window.setTimeout(() => void refresh(), 0)
    const onVisibility = () => {
      const isVisible = document.visibilityState !== 'hidden'
      setVisible(isVisible)
      if (isVisible) void refresh()
    }
    const onReconnect = () => void refresh()
    document.addEventListener('visibilitychange', onVisibility)
    window.addEventListener('focus', onReconnect)
    window.addEventListener('online', onReconnect)
    return () => {
      mounted.current = false
      window.clearTimeout(initialRefresh)
      abortController.current?.abort()
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('focus', onReconnect)
      window.removeEventListener('online', onReconnect)
    }
  }, [refresh])

  useEffect(() => {
    const base = visible ? pollIntervalMs : hiddenPollIntervalMs
    const delay = Math.min(base * 2 ** failures, MAX_BACKOFF_MS)
    const timer = window.setInterval(() => void refresh(), delay)
    return () => window.clearInterval(timer)
  }, [failures, hiddenPollIntervalMs, pollIntervalMs, refresh, visible])

  const stale = Boolean(failure)
    || snapshot?.data_quality.verdict !== 'reliable'
    || snapshot?.sources.some((source) => source.state === 'stale' || source.state === 'unavailable' || source.state === 'unknown')

  if (!snapshot) {
    return <section aria-live="polite" className="rounded-xl border border-brand-border bg-brand-surface p-6 text-center">
      <CloudOff aria-hidden="true" className="mx-auto size-6 text-brand-warn" />
      <h1 className="mt-3 font-serif text-2xl text-brand-gold-cream">Nirmāṇa Elevation Tracker</h1>
      <p className="mt-2 text-sm text-brand-text-2">{failure ? `Live snapshot unavailable — ${failure.message}` : 'Obtaining the live evidence snapshot…'}</p>
    </section>
  }

  return <div className={`relative mx-auto max-w-[1600px] space-y-5 py-6 ${stale ? 'after:pointer-events-none after:absolute after:inset-0 after:rounded-xl after:border-2 after:border-brand-warn/60' : ''}`}>
    {stale && <aside role="alert" aria-live="assertive" className="rounded-xl border-2 border-brand-warn bg-brand-warn/15 p-4 text-brand-text-1">
      <div className="flex gap-3">
        <AlertTriangle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-brand-warn" />
        <div>
          <p className="font-semibold uppercase tracking-wide">Current state unknown</p>
          {failure
            ? <><p className="mt-1 text-sm text-brand-text-2">{failure.message} Displaying the last successful snapshot from {formatTime(fetchedAt)}.</p><p className="mt-1 text-xs text-brand-text-3">Failure observed <time dateTime={failure.occurredAt.toISOString()}>{formatTime(failure.occurredAt)}</time>.</p></>
            : <p className="mt-1 text-sm text-brand-text-2">One or more sources are stale, unknown, or unavailable. The rendered state is not a current conclusion.</p>}
        </div>
      </div>
    </aside>}
    <NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={fetchedAt ?? new Date()} onBaselineAccepted={refresh} />
    <p className="flex items-center gap-2 text-xs text-brand-text-3"><ShieldCheck aria-hidden="true" className="size-4" /> Evidence-backed tracker · automatic refresh while this page remains open.</p>
  </div>
}
