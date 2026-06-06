'use client'

import { useState } from 'react'

interface Props {
  chartId: string
  assetId: string
  downstreamStaleIds: string[]
  onDismiss: () => void
  onRunStarted: (runId: string) => void
}

export function CascadeBanner({ chartId, assetId, downstreamStaleIds, onDismiss, onRunStarted }: Props) {
  const [loading, setLoading] = useState(false)

  const triggerCascade = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/cockpit/runs', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_id: chartId,
          scope: 'asset',
          scope_target: assetId,
          action: 'cascade',
        }),
      })
      const body = await r.json()
      if (r.ok) onRunStarted(body.data.run_id)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        margin: '4px 0 0 24px',
        padding: '8px 12px',
        borderRadius: '6px',
        background: 'rgba(168,124,42,0.08)',
        border: '1px solid rgba(168,124,42,0.25)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '11px',
        fontFamily: 'var(--ui-stack)',
      }}
    >
      <span style={{ color: 'var(--gold-bright)' }}>
        {downstreamStaleIds.length} downstream asset{downstreamStaleIds.length !== 1 ? 's' : ''} stale after rebuild
      </span>
      <button
        onClick={triggerCascade}
        disabled={loading}
        style={{
          padding: '3px 10px',
          borderRadius: '4px',
          background: 'rgba(168,124,42,0.2)',
          border: '1px solid var(--gold-engrave)',
          color: 'var(--gold-bright)',
          fontSize: '10px',
          cursor: 'pointer',
          opacity: loading ? 0.6 : 1,
        }}
      >
        {loading ? '…' : 'Cascade rebuild'}
      </button>
      <button
        onClick={onDismiss}
        style={{
          background: 'transparent', border: 'none',
          color: 'var(--on-dark-faint)', fontSize: '11px',
          cursor: 'pointer',
        }}
      >
        Dismiss
      </button>
    </div>
  )
}
