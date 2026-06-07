'use client'

import { useState } from 'react'
import { toast } from 'sonner'

interface Props {
  chartId: string
  scope: 'global' | 'layer' | 'asset'
  scopeTarget?: string | null
  size?: number
  onRefreshed?: () => void
}

export function RefreshIconButton({ chartId, scope, scopeTarget, size = 22, onRefreshed }: Props) {
  const [loading, setLoading] = useState(false)

  async function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (loading) return
    setLoading(true)
    try {
      const r = await fetch('/api/cockpit/refresh', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget ?? null }),
      })
      const txt = await r.text()
      let body: Record<string, unknown>
      try {
        body = JSON.parse(txt)
      } catch {
        throw new Error(`Server error (${r.status}): ${txt.substring(0, 200) || 'no response body'}`)
      }
      if (!r.ok) throw new Error((body.error as string | undefined) ?? 'Refresh failed')
      const label = scope === 'asset' ? (scopeTarget ?? 'asset') : scope
      toast.success(`Refreshed ${label}`)
      onRefreshed?.()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Refresh failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      title={`Refresh ${scope === 'asset' ? (scopeTarget ?? 'asset') : scope}`}
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
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--gold-high)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(168,124,42,0.10)'
      }}
      onMouseLeave={e => {
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--on-dark-faint)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
      }}
    >
      {/* RefreshCw icon inline SVG */}
      <svg
        width={Math.round(size * 0.57)}
        height={Math.round(size * 0.57)}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={loading ? { animation: 'spin 1s linear infinite' } : undefined}
      >
        <polyline points="23 4 23 10 17 10" />
        <polyline points="1 20 1 14 7 14" />
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
      </svg>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </button>
  )
}
