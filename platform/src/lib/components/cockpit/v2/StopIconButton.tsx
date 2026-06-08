'use client'

import { useState } from 'react'
import { toast } from 'sonner'

interface Props {
  runId: string
  size?: number
  onStopped?: () => void
}

export function StopIconButton({ runId, size = 22, onStopped }: Props) {
  const [loading, setLoading] = useState(false)

  async function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (loading) return
    setLoading(true)
    try {
      const r = await fetch(`/api/cockpit/runs/${runId}/stop`, {
        method: 'POST',
        credentials: 'include',
      })
      if (!r.ok) {
        const body = await r.json().catch(() => ({}))
        throw new Error((body.error as string | undefined) ?? `Stop failed (${r.status})`)
      }
      onStopped?.()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to stop run')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      title="Stop build"
      style={{
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'transparent',
        border: 'none',
        borderRadius: '4px',
        cursor: loading ? 'wait' : 'pointer',
        color: 'var(--on-dark-faint)',
        padding: 0,
        transition: 'color 0.15s, background 0.15s',
      }}
      onMouseEnter={e => {
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--marsys-error, #e05252)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(181,71,76,0.15)'
      }}
      onMouseLeave={e => {
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--on-dark-faint)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
      }}
    >
      {/* Filled square = stop */}
      <svg
        width={Math.round(size * 0.48)}
        height={Math.round(size * 0.48)}
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <rect x="3" y="3" width="18" height="18" rx="2" />
      </svg>
    </button>
  )
}
