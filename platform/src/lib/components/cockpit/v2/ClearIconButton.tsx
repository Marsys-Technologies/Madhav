'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { ClearConfirmModal } from './ClearConfirmModal'

interface ClearPreview {
  tables: { table: string; rows: number }[]
  total_rows: number
  affected_assets: string[]
  downstream_stale_assets: string[]
  preview_hash: string
  requires_typed_confirmation?: string
}

interface Props {
  chartId: string
  scope: 'global' | 'layer' | 'asset'
  scopeTarget?: string | null
  size?: number
  onSuccess?: () => void
}

export function ClearIconButton({ chartId, scope, scopeTarget, size = 28, onSuccess }: Props) {
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<ClearPreview | null>(null)

  async function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (loading) return
    setLoading(true)
    try {
      const r = await fetch('/api/cockpit/clear', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget ?? null }),
      })
      const body = await r.json()
      if (!r.ok) throw new Error(body.error ?? 'Preview failed')
      setPreview(body.preview)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load clear preview')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <button
        onClick={handleClick}
        title={`Clear ${scope === 'asset' ? scopeTarget ?? 'asset' : scope}`}
        disabled={loading}
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
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--marsys-error)'
          ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(181,71,76,0.10)'
        }}
        onMouseLeave={e => {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--on-dark-faint)'
          ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
        }}
      >
        {/* Trash2 icon (inline SVG, no Lucide dep) */}
        <svg
          width={Math.round(size * 0.57)}
          height={Math.round(size * 0.57)}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
          <path d="M10 11v6" />
          <path d="M14 11v6" />
          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
        </svg>
      </button>

      {preview && (
        <ClearConfirmModal
          chartId={chartId}
          scope={scope}
          scopeTarget={scopeTarget}
          preview={preview}
          onClose={() => setPreview(null)}
          onSuccess={() => {
            setPreview(null)
            onSuccess?.()
          }}
        />
      )}
    </>
  )
}
