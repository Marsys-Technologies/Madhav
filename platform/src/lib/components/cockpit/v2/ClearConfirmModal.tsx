'use client'

import { useState } from 'react'

interface TableCount {
  table: string
  rows: number
}

interface ClearPreview {
  tables: TableCount[]
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
  preview: ClearPreview
  onClose: () => void
  onSuccess: () => void
  /** Called after a successful clear, before onSuccess+onClose. Used for rebuild chaining. */
  onAfterClear?: () => Promise<void>
}

const SCOPE_LABELS: Record<string, { title: (t?: string | null) => string; confirmLabel: string }> = {
  asset: {
    title: (t) => `Clear ${t ?? 'asset'}?`,
    confirmLabel: 'Clear data',
  },
  layer: {
    title: (t) => `Clear all ${t ?? 'layer'} assets?`,
    confirmLabel: 'Clear layer',
  },
  global: {
    title: () => 'Clear ALL data for this chart?',
    confirmLabel: 'Clear instrument',
  },
}

const overlay: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,0.72)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
}

const modal: React.CSSProperties = {
  background: 'var(--black-raised)',
  border: '1px solid rgba(181,71,76,0.35)',
  borderRadius: '10px',
  padding: '28px 32px',
  maxWidth: '520px',
  width: '90vw',
  fontFamily: 'var(--ui-stack)',
}

export function ClearConfirmModal({ chartId, scope, scopeTarget, preview, onClose, onSuccess, onAfterClear }: Props) {
  const [typed, setTyped] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const config = SCOPE_LABELS[scope]
  const isGlobal = scope === 'global'
  const isL0Layer = scope === 'layer' && scopeTarget === 'brahmagyan'
  const requiresTypedConfirmation = isGlobal || isL0Layer
  const confirmTarget = preview.requires_typed_confirmation ?? ''
  const typedMatch = !requiresTypedConfirmation || typed === confirmTarget

  // Limit table display (show top 5, collapse rest)
  const SHOW = 5
  const visibleTables = preview.tables.slice(0, SHOW)
  const remaining = preview.tables.length - SHOW

  async function handleConfirm() {
    setLoading(true)
    setError(null)
    try {
      const r = await fetch('/api/cockpit/clear/execute', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_id: chartId,
          scope,
          scope_target: scopeTarget ?? null,
          preview_hash: preview.preview_hash,
          ...(requiresTypedConfirmation ? { typed_confirmation: typed } : {}),
        }),
      })
      const body = await r.json()
      if (!r.ok) throw new Error(body.error ?? 'Clear failed')
      if (onAfterClear) await onAfterClear()
      onSuccess()
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={overlay} onClick={onClose}>
      <div style={modal} onClick={e => e.stopPropagation()}>
        {/* Title */}
        <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--marsys-error)', marginBottom: '16px' }}>
          {config.title(scopeTarget)}
        </div>

        {/* Table breakdown */}
        <div style={{ marginBottom: '12px' }}>
          {visibleTables.map(t => (
            <div key={t.table} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '13px' }}>
              <span style={{ color: 'var(--on-dark-mut)', fontFamily: 'var(--mono-stack)' }}>{t.table}</span>
              <span style={{ color: 'var(--on-dark)', fontFamily: 'var(--mono-stack)' }}>{t.rows.toLocaleString()} rows</span>
            </div>
          ))}
          {remaining > 0 && (
            <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', paddingTop: '4px' }}>
              and {remaining} more table{remaining > 1 ? 's' : ''}
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0 4px', fontSize: '13px', fontWeight: 600 }}>
            <span style={{ color: 'var(--on-dark-mut)' }}>{preview.tables.length} tables total</span>
            <span style={{ color: 'var(--on-dark)' }}>{preview.total_rows.toLocaleString()} rows</span>
          </div>
        </div>

        {/* Asset reset note */}
        {preview.affected_assets.length > 0 && (
          <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', marginBottom: '4px' }}>
            Reset {preview.affected_assets.length} asset{preview.affected_assets.length !== 1 ? 's' : ''} to dormant.
          </div>
        )}

        {/* Downstream stale note */}
        {preview.downstream_stale_assets.length > 0 && (
          <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', marginBottom: '12px' }}>
            Mark {preview.downstream_stale_assets.length} downstream asset{preview.downstream_stale_assets.length !== 1 ? 's' : ''} stale:{' '}
            {preview.downstream_stale_assets.slice(0, 3).join(', ')}
            {preview.downstream_stale_assets.length > 3 ? '…' : ''}
          </div>
        )}

        {/* Warning */}
        <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.45)', marginBottom: requiresTypedConfirmation ? '16px' : '20px' }}>
          This cannot be undone.
          {isGlobal && ' The entire instrument will need to be rebuilt from L0.'}
          {isL0Layer && ' All L0 Brahmagyan foundation data will be erased and must be rebuilt.'}
        </div>

        {/* Typed confirmation for global or L0 layer scope */}
        {requiresTypedConfirmation && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', color: 'var(--on-dark-mut)', marginBottom: '6px' }}>
              To confirm, type the chart subject name exactly:
            </div>
            <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', marginBottom: '6px', fontStyle: 'italic' }}>
              {confirmTarget}
            </div>
            <input
              type="text"
              value={typed}
              onChange={e => setTyped(e.target.value)}
              placeholder={confirmTarget}
              style={{
                width: '100%',
                padding: '8px 10px',
                background: 'var(--black)',
                border: `1px solid ${typed && typed !== confirmTarget ? 'var(--marsys-error)' : 'rgba(255,255,255,0.15)'}`,
                borderRadius: '4px',
                color: 'var(--on-dark)',
                fontFamily: 'var(--ui-stack)',
                fontSize: '13px',
                boxSizing: 'border-box',
              }}
              autoFocus
            />
          </div>
        )}

        {error && (
          <div style={{ color: 'var(--marsys-error)', fontSize: '12px', marginBottom: '12px' }}>{error}</div>
        )}

        {/* Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            onClick={onClose}
            disabled={loading}
            style={{
              padding: '7px 16px',
              background: 'transparent',
              border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: '5px',
              color: 'var(--on-dark-mut)',
              cursor: 'pointer',
              fontFamily: 'var(--ui-stack)',
              fontSize: '13px',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || !typedMatch}
            style={{
              padding: '7px 16px',
              background: typedMatch ? 'rgba(181,71,76,0.85)' : 'rgba(181,71,76,0.25)',
              border: '1px solid rgba(181,71,76,0.5)',
              borderRadius: '5px',
              color: typedMatch ? '#fff' : 'rgba(255,255,255,0.35)',
              cursor: typedMatch && !loading ? 'pointer' : 'not-allowed',
              fontFamily: 'var(--ui-stack)',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            {loading ? 'Clearing…' : config.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
