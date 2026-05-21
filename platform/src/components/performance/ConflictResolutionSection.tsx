'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import type { ConflictArtifact, ConflictsResponse } from '@/app/api/performance/conflicts/route'

// ─────────────────────────────────────────────────────────────────────────────
// Fetcher
// ─────────────────────────────────────────────────────────────────────────────

async function fetchConflicts(): Promise<ConflictsResponse> {
  const res = await fetch('/api/performance/conflicts')
  if (!res.ok) throw new Error(`conflicts fetch failed: ${res.status}`)
  return res.json() as Promise<ConflictsResponse>
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: 'proposed' | 'resolved' }) {
  const isResolved = status === 'resolved'
  return (
    <span
      className="inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{
        background: isResolved
          ? 'rgba(34,197,94,0.12)'
          : 'rgba(212,175,55,0.12)',
        color: isResolved ? 'var(--status-success)' : 'var(--brand-gold)',
        border: isResolved
          ? '1px solid rgba(34,197,94,0.25)'
          : '1px solid rgba(212,175,55,0.25)',
      }}
    >
      {status}
    </span>
  )
}

function ArtifactCard({ artifact }: { artifact: ConflictArtifact }) {
  const [expanded, setExpanded] = React.useState(false)

  return (
    <div
      className="rounded border p-3 space-y-1.5"
      style={{ borderColor: 'rgba(212,175,55,0.12)', background: 'rgba(255,255,255,0.02)' }}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="bt-label font-mono text-xs" style={{ color: 'var(--brand-gold-cream)' }}>
            {artifact.conflict_id}
          </span>
          <span className="bt-label text-xs text-muted-foreground">
            {artifact.signal_id} · {artifact.field}
          </span>
        </div>
        <StatusBadge status={artifact.status} />
      </div>

      <div className="text-xs space-y-0.5">
        <div>
          <span className="text-muted-foreground">from: </span>
          <span className="font-mono" style={{ color: 'rgba(239,68,68,0.85)' }}>
            {artifact.current_value}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">to: </span>
          <span className="font-mono" style={{ color: 'var(--status-success)' }}>
            {artifact.proposed_value}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <span className="bt-label text-[10px] text-muted-foreground">
          {artifact.proposed_at ? new Date(artifact.proposed_at).toLocaleString() : '—'}
        </span>
        <button
          onClick={() => setExpanded(v => !v)}
          className="bt-label text-[10px] underline-offset-2 hover:underline"
          style={{ color: 'var(--brand-gold)' }}
        >
          {expanded ? 'hide rationale' : 'rationale →'}
        </button>
      </div>

      {expanded && (
        <p className="text-xs text-muted-foreground border-t pt-1.5" style={{ borderColor: 'rgba(212,175,55,0.08)' }}>
          {artifact.rationale}
        </p>
      )}
    </div>
  )
}

function Column({
  title,
  artifacts,
  emptyMsg,
}: {
  title: string
  artifacts: ConflictArtifact[]
  emptyMsg: string
}) {
  return (
    <div className="flex-1 min-w-0 space-y-2">
      <div className="flex items-center gap-2">
        <h3 className="bt-label bt-label-upper text-xs" style={{ color: 'var(--brand-gold)' }}>
          {title}
        </h3>
        <span
          className="rounded-full px-1.5 py-0.5 text-[10px] font-medium"
          style={{ background: 'rgba(212,175,55,0.10)', color: 'var(--brand-gold)' }}
        >
          {artifacts.length}
        </span>
      </div>
      {artifacts.length === 0 ? (
        <p className="text-xs text-muted-foreground italic">{emptyMsg}</p>
      ) : (
        <div className="space-y-2">
          {artifacts.map(a => (
            <ArtifactCard key={a.filename} artifact={a} />
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────────────────

export function ConflictResolutionSection() {
  const q = useQuery({
    queryKey: ['perf-conflicts'],
    queryFn: fetchConflicts,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  })

  if (q.isPending) {
    return (
      <p className="bt-label text-xs text-muted-foreground animate-pulse">
        Loading conflict artifacts…
      </p>
    )
  }

  if (q.isError) {
    return (
      <p className="bt-label text-xs" style={{ color: 'var(--status-error)' }}>
        Failed to load conflict artifacts.
      </p>
    )
  }

  const { proposed = [], resolved = [] } = q.data ?? {}

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-4">
        <Column
          title="Awaiting Review (PROPOSED/)"
          artifacts={proposed}
          emptyMsg="No proposed patches — PROPOSED/ is empty."
        />
        <Column
          title="Applied (RESOLVED/)"
          artifacts={resolved}
          emptyMsg="No resolved patches yet."
        />
      </div>
    </div>
  )
}
