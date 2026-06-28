'use client'

import { useRef, useState } from 'react'
import { toast } from 'sonner'

interface Props {
  runId: string
  size?: number
  onStopped?: () => void
}

export function StopIconButton({ runId, size = 22, onStopped }: Props) {
  const [loading, setLoading] = useState(false)
  // Once a stop is successfully requested, keep the button locked until the parent
  // unmounts it (i.e. the run leaves the active state). Without this, the button
  // resets to clickable ~200ms after the API returns — before the Python sidecar
  // has finished the current asset — which makes the user think the stop failed.
  const stopRequestedRef = useRef(false)

  async function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (loading || stopRequestedRef.current) return
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
      // Mark stop as requested — keeps button locked until parent unmounts this component
      stopRequestedRef.current = true
      toast.success('Stop requested — finishing current asset…')
      onStopped?.()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to stop run')
      setLoading(false)
    }
    // Note: setLoading(false) is intentionally NOT in a finally block.
    // On success, stopRequestedRef keeps the button visually disabled until unmount.
    // On error, setLoading(false) is called above to restore interactivity.
  }

  const isStopping = stopRequestedRef.current
  const isDisabled = loading || isStopping

  return (
    <button
      onClick={handleClick}
      disabled={isDisabled}
      title={isStopping ? 'Stopping…' : 'Stop build'}
      aria-label={isStopping ? 'Stopping…' : 'Stop build'}
      style={{
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: isStopping ? 'rgba(181,71,76,0.10)' : 'transparent',
        border: 'none',
        borderRadius: '4px',
        cursor: isDisabled ? 'wait' : 'pointer',
        color: isStopping ? 'var(--marsys-error, #e05252)' : 'var(--on-dark-faint)',
        padding: 0,
        transition: 'color 0.15s, background 0.15s',
        opacity: isStopping ? 0.6 : 1,
      }}
      onMouseEnter={e => {
        if (isDisabled) return
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--marsys-error, #e05252)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(181,71,76,0.15)'
      }}
      onMouseLeave={e => {
        if (isDisabled) return
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--on-dark-faint)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
      }}
    >
      {isStopping ? (
        /* Pulsing ring = stopping in progress */
        <svg
          width={Math.round(size * 0.48)}
          height={Math.round(size * 0.48)}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className="animate-spin"
        >
          <circle cx="12" cy="12" r="9" strokeOpacity="0.3" />
          <path d="M12 3a9 9 0 0 1 9 9" />
        </svg>
      ) : (
        /* Filled square = stop */
        <svg
          width={Math.round(size * 0.48)}
          height={Math.round(size * 0.48)}
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <rect x="3" y="3" width="18" height="18" rx="2" />
        </svg>
      )}
    </button>
  )
}
