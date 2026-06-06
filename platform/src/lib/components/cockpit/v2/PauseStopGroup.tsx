'use client'

import { useState } from 'react'

interface Props {
  runId: string
  chartId: string
  isPaused: boolean
  onStateChange?: () => void
}

export function PauseStopGroup({ runId, isPaused, onStateChange }: Props) {
  const [loading, setLoading] = useState<'pause' | 'resume' | 'stop' | null>(null)
  const [confirmStop, setConfirmStop] = useState(false)

  const request = async (action: 'pause' | 'resume' | 'stop') => {
    setLoading(action)
    try {
      await fetch(`/api/cockpit/runs/${runId}/${action}`, {
        method: 'POST',
        credentials: 'include',
      })
      onStateChange?.()
    } finally {
      setLoading(null)
      setConfirmStop(false)
    }
  }

  const chipBase: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 10px',
    borderRadius: '6px',
    fontSize: '11px',
    fontFamily: 'var(--ui-stack)',
    fontWeight: 600,
    cursor: 'pointer',
    border: '1px solid',
    letterSpacing: '0.03em',
    opacity: loading ? 0.6 : 1,
  }

  return (
    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
      {!isPaused ? (
        <button
          style={{ ...chipBase, background: 'rgba(168,124,42,0.15)', borderColor: 'var(--gold-engrave)', color: 'var(--gold-bright)' }}
          onClick={() => request('pause')}
          disabled={!!loading}
        >
          {loading === 'pause' ? '…' : '⏸ Pause'}
        </button>
      ) : (
        <button
          style={{ ...chipBase, background: 'rgba(62,124,75,0.15)', borderColor: 'var(--marsys-success)', color: 'var(--marsys-success)' }}
          onClick={() => request('resume')}
          disabled={!!loading}
        >
          {loading === 'resume' ? '…' : '▶ Resume'}
        </button>
      )}

      {confirmStop ? (
        <>
          <button
            style={{ ...chipBase, background: 'rgba(181,71,76,0.2)', borderColor: 'var(--marsys-error)', color: 'var(--marsys-error)' }}
            onClick={() => request('stop')}
            disabled={!!loading}
          >
            {loading === 'stop' ? '…' : 'Confirm stop'}
          </button>
          <button
            style={{ ...chipBase, background: 'transparent', borderColor: 'var(--black-line)', color: 'var(--on-dark-faint)' }}
            onClick={() => setConfirmStop(false)}
            disabled={!!loading}
          >
            Cancel
          </button>
        </>
      ) : (
        <button
          style={{ ...chipBase, background: 'transparent', borderColor: 'var(--black-line)', color: 'var(--on-dark-faint)' }}
          onClick={() => setConfirmStop(true)}
          disabled={!!loading}
        >
          ■ Stop
        </button>
      )}
    </div>
  )
}
