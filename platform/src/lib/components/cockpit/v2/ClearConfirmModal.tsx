'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { DUR, EASE } from './motion'

interface TableCount {
  table: string
  rows: number
  error?: string
}

interface LayerSummaryItem {
  layer: string
  rows: number
  asset_count: number
}

interface LabeledAsset {
  id: string
  label: string
  layer?: string
  sanskrit_name?: string
  rows?: number
}

interface ClearPreview {
  tables: TableCount[]
  total_rows: number
  affected_assets: string[]
  not_clearable_assets?: LabeledAsset[]
  downstream_stale_assets: string[]
  downstream_stale_assets_labeled?: LabeledAsset[]
  // E1: reconciling breakdown
  assets_clearable?: LabeledAsset[]
  assets_reset_only?: LabeledAsset[]
  scope_label?: string | null
  preview_hash: string
  requires_typed_confirmation?: string
  layer_summary?: LayerSummaryItem[]
}

const LAYER_LABELS: Record<string, string> = {
  brahmagyan: 'Brahma Jñāna (L0)',
  ganita: 'Gaṇita (L1)',
  bodha: 'Bodha (L2)',
  kala: 'Kāla (L3)',
  phala: 'Phala (L4)',
  mimamsa: 'Mīmāṃsā (L5)',
}

const LAYER_ORDER = ['brahmagyan', 'ganita', 'bodha', 'kala', 'phala', 'mimamsa']

/** Layer-grouped list of named assets — used for downstream stale tree (E2) */
function DownstreamTree({ assets }: { assets: LabeledAsset[] }) {
  const [expanded, setExpanded] = useState(false)
  if (assets.length === 0) return null

  const PREVIEW_LIMIT = 3
  const grouped = new Map<string, LabeledAsset[]>()
  for (const a of assets) {
    const layer = a.layer ?? 'unknown'
    if (!grouped.has(layer)) grouped.set(layer, [])
    grouped.get(layer)!.push(a)
  }
  const sortedLayers = [...grouped.keys()].sort(
    (a, b) => (LAYER_ORDER.indexOf(a) ?? 99) - (LAYER_ORDER.indexOf(b) ?? 99)
  )

  const showExpander = assets.length > PREVIEW_LIMIT

  return (
    <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', marginBottom: '12px' }}>
      <div style={{ marginBottom: '6px' }}>
        {assets.length} built asset{assets.length !== 1 ? 's' : ''} that depend on this will need rebuilding:
      </div>
      <AnimatePresence initial={false}>
        {(expanded || !showExpander) && (
          <motion.div
            key="tree"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            style={{ overflow: 'hidden' }}
          >
            {sortedLayers.map(layer => (
              <div key={layer} style={{ marginBottom: '6px' }}>
                <div style={{ color: 'rgba(236,197,106,0.6)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '2px' }}>
                  {LAYER_LABELS[layer] ?? layer}
                </div>
                {grouped.get(layer)!.map(a => (
                  <div key={a.id} style={{ paddingLeft: '10px', paddingBottom: '2px', display: 'flex', gap: '6px' }}>
                    <span style={{ color: 'rgba(255,255,255,0.4)' }}>•</span>
                    <span>
                      <span style={{ color: 'var(--on-dark-mut)' }}>{a.sanskrit_name ?? a.label}</span>
                      {a.sanskrit_name && a.label !== a.sanskrit_name && (
                        <span style={{ color: 'rgba(255,255,255,0.3)', marginLeft: '4px' }}>— {a.label}</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
      {!expanded && showExpander && (
        <div style={{ paddingLeft: '10px', color: 'rgba(255,255,255,0.3)' }}>
          {assets.slice(0, PREVIEW_LIMIT).map(a => a.sanskrit_name ?? a.label).join(', ')} +{assets.length - PREVIEW_LIMIT} more…
          {' '}
          <button
            onClick={() => setExpanded(true)}
            style={{ background: 'none', border: 'none', color: 'rgba(236,197,106,0.6)', cursor: 'pointer', padding: 0, fontSize: '12px', textDecoration: 'underline' }}
          >
            show all
          </button>
        </div>
      )}
      {expanded && showExpander && (
        <button
          onClick={() => setExpanded(false)}
          style={{ background: 'none', border: 'none', color: 'rgba(236,197,106,0.6)', cursor: 'pointer', padding: '4px 0 0', fontSize: '11px', textDecoration: 'underline' }}
        >
          collapse
        </button>
      )}
    </div>
  )
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
  // Portal mount guard: document is unavailable during SSR. Mounting to <body>
  // lifts the modal out of the cockpit's nested stacking contexts so the
  // constellation SVG (own stacking context) can no longer overpaint it.
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const config = SCOPE_LABELS[scope]
  const isGlobal = scope === 'global'
  const isL0Layer = scope === 'layer' && scopeTarget === 'brahmagyan'
  const requiresTypedConfirmation = isGlobal || isL0Layer
  const confirmTarget = preview.requires_typed_confirmation ?? ''
  const typedMatch = !requiresTypedConfirmation || typed === confirmTarget

  // E1: use reconciling fields when present; fall back to legacy for older API responses
  const assetsClearable = preview.assets_clearable ?? []
  const assetsResetOnly = preview.assets_reset_only ?? []
  const hasReconcilingData = preview.assets_clearable != null

  // Layer summary — always show when present (global or layer scope)
  const showLayerSummary = Array.isArray(preview.layer_summary) && preview.layer_summary.length > 0

  // E2: downstream tree — use enriched list with layer+names when available
  const downstreamList = preview.downstream_stale_assets_labeled ?? preview.downstream_stale_assets.map(id => ({ id, label: id }))

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
      const txt = await r.text()
      let body: Record<string, unknown>
      try {
        body = JSON.parse(txt)
      } catch {
        throw new Error(`Server error (${r.status}): ${txt.substring(0, 200) || 'no response body'}`)
      }
      if (!r.ok) throw new Error((body.error as string | undefined) ?? `Clear failed (${r.status})`)
      if (onAfterClear) await onAfterClear()
      onSuccess()
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  if (!mounted) return null

  return createPortal(
    <motion.div
      style={overlay}
      onClick={onClose}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: DUR.modal }}
    >
      <motion.div
        style={modal}
        onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.98, y: 6 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: DUR.modal, ease: EASE.out }}
      >
        {/* Title */}
        <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--marsys-error)', marginBottom: '16px' }}>
          {config.title(preview.scope_label ?? scopeTarget)}
        </div>

        {/* E1: Unified reconciling summary — same layout for asset/layer/global scope */}
        <div style={{ marginBottom: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.07)', padding: '12px 14px', background: 'rgba(255,255,255,0.02)' }}>
          {/* Per-layer row count breakdown */}
          {showLayerSummary && (
            <div style={{ marginBottom: '8px' }}>
              {[...preview.layer_summary!]
                .sort((a, b) => (LAYER_ORDER.indexOf(a.layer) ?? 99) - (LAYER_ORDER.indexOf(b.layer) ?? 99))
                .map(ls => (
                  <div key={ls.layer} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: '12px' }}>
                    <span style={{ color: 'var(--on-dark-mut)' }}>
                      {LAYER_LABELS[ls.layer] ?? ls.layer}{' '}
                      <span style={{ color: 'var(--on-dark-faint)', fontSize: '10px' }}>({ls.asset_count} assets)</span>
                    </span>
                    <span style={{ color: 'var(--on-dark)', fontFamily: 'var(--mono-stack)' }}>{ls.rows.toLocaleString()} rows</span>
                  </div>
                ))}
            </div>
          )}

          {/* Total row count */}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
            <span style={{ color: 'var(--on-dark-mut)' }}>Total rows deleted</span>
            <span style={{ color: 'var(--on-dark)', fontFamily: 'var(--mono-stack)' }}>{preview.total_rows.toLocaleString()}</span>
          </div>

          {/* E1: reconciling asset counts — arithmetic visible */}
          {hasReconcilingData ? (
            <div style={{ fontSize: '11px', color: 'var(--on-dark-faint)', lineHeight: '1.7' }}>
              <span style={{ color: 'var(--on-dark-mut)' }}>{assetsClearable.length}</span> assets cleared (rows deleted)
              {' · '}
              <span style={{ color: 'var(--on-dark-mut)' }}>{assetsResetOnly.length}</span> reset to dormant (0 rows)
              {' · '}
              <span style={{ color: 'var(--on-dark-mut)' }}>{preview.tables.length}</span> table{preview.tables.length !== 1 ? 's' : ''} touched
            </div>
          ) : (
            <div style={{ fontSize: '11px', color: 'var(--on-dark-faint)' }}>
              {preview.affected_assets.length} asset{preview.affected_assets.length !== 1 ? 's' : ''} reset to dormant
              {' · '}
              {preview.tables.length} table{preview.tables.length !== 1 ? 's' : ''} touched
            </div>
          )}
        </div>

        {/* E2: Downstream stale tree — layer-grouped, named, expandable */}
        <DownstreamTree assets={downstreamList as LabeledAsset[]} />

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
      </motion.div>
    </motion.div>,
    document.body,
  )
}
