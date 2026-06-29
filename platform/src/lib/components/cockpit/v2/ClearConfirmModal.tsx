'use client'

import { useState, useEffect, useRef } from 'react'
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

export interface ClearPreview {
  tables: TableCount[]
  total_rows: number
  affected_assets: string[]
  not_clearable_assets?: LabeledAsset[]
  downstream_stale_assets: string[]
  downstream_stale_assets_labeled?: LabeledAsset[]
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

// ── Downstream stale tree ──────────────────────────────────────────────────────

function DownstreamTree({ assets }: { assets: LabeledAsset[] }) {
  const [expanded, setExpanded] = useState(false)
  if (assets.length === 0) return null

  const LIMIT = 3
  const grouped = new Map<string, LabeledAsset[]>()
  for (const a of assets) {
    const layer = a.layer ?? 'unknown'
    if (!grouped.has(layer)) grouped.set(layer, [])
    grouped.get(layer)!.push(a)
  }
  const sortedLayers = [...grouped.keys()].sort(
    (a, b) => (LAYER_ORDER.indexOf(a) ?? 99) - (LAYER_ORDER.indexOf(b) ?? 99)
  )
  const showExpander = assets.length > LIMIT

  return (
    <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', marginBottom: '14px' }}>
      <div style={{ marginBottom: '6px', color: 'var(--on-dark-mut)' }}>
        {assets.length} built asset{assets.length !== 1 ? 's' : ''} will become stale and need rebuilding:
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
                <div style={{
                  color: 'rgba(236,197,106,0.55)',
                  fontSize: '10px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  marginBottom: '3px',
                }}>
                  {LAYER_LABELS[layer] ?? layer}
                </div>
                {grouped.get(layer)!.map(a => (
                  <div key={a.id} style={{ paddingLeft: '10px', paddingBottom: '2px', display: 'flex', gap: '6px' }}>
                    <span style={{ color: 'rgba(255,255,255,0.25)' }}>·</span>
                    <span>
                      <span style={{ color: 'var(--on-dark-mut)' }}>{a.sanskrit_name ?? a.label}</span>
                      {a.sanskrit_name && a.label !== a.sanskrit_name && (
                        <span style={{ color: 'rgba(255,255,255,0.28)', marginLeft: '5px', fontSize: '11px' }}>
                          — {a.label}
                        </span>
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
        <div style={{ paddingLeft: '10px', color: 'rgba(255,255,255,0.28)', fontSize: '11px' }}>
          {assets.slice(0, LIMIT).map(a => a.sanskrit_name ?? a.label).join(', ')}
          {' +'}{ assets.length - LIMIT} more{' '}
          <button
            onClick={() => setExpanded(true)}
            style={{ background: 'none', border: 'none', color: 'rgba(236,197,106,0.55)', cursor: 'pointer', padding: 0, fontSize: '11px', textDecoration: 'underline' }}
          >
            show all
          </button>
        </div>
      )}
      {expanded && showExpander && (
        <button
          onClick={() => setExpanded(false)}
          style={{ background: 'none', border: 'none', color: 'rgba(236,197,106,0.55)', cursor: 'pointer', padding: '4px 0 0', fontSize: '11px', textDecoration: 'underline' }}
        >
          collapse
        </button>
      )}
    </div>
  )
}

// ── Loading skeleton ───────────────────────────────────────────────────────────

function Shimmer({ width = '100%', height = 14, radius = 4 }: { width?: string | number; height?: number; radius?: number }) {
  return (
    <div style={{
      width,
      height,
      borderRadius: radius,
      background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.04) 100%)',
      backgroundSize: '200% 100%',
      animation: 'clear-modal-shimmer 1.6s ease-in-out infinite',
    }} />
  )
}

// ── Execution progress bar ─────────────────────────────────────────────────────

function ExecProgressBar({ pct, label }: { pct: number; label: string }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{
        position: 'relative',
        height: '5px',
        borderRadius: '3px',
        background: 'rgba(181,71,76,0.12)',
        border: '1px solid rgba(181,71,76,0.2)',
        overflow: 'hidden',
        marginBottom: '6px',
      }}>
        <motion.div
          style={{
            position: 'absolute', top: 0, left: 0, bottom: 0,
            background: 'linear-gradient(90deg, rgba(181,71,76,0.7), rgba(210,90,95,0.85))',
            borderRadius: '3px',
          }}
          animate={{ width: `${pct}%` }}
          transition={{ type: 'spring', stiffness: 40, damping: 14 }}
        />
        {pct < 100 && (
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: 'linear-gradient(90deg, transparent 0%, rgba(255,120,120,0.18) 50%, transparent 100%)',
            animation: 'clear-modal-shimmer 2s linear infinite',
          }} />
        )}
      </div>
      <div style={{ fontSize: '11px', color: 'rgba(181,71,76,0.85)', fontFamily: 'var(--mono-stack)', letterSpacing: '0.04em' }}>
        {label}
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

const SCOPE_CONFIG: Record<string, { title: (t?: string | null) => string; confirmLabel: string }> = {
  asset: {
    title: (t) => `Clear ${t ?? 'asset'}?`,
    confirmLabel: 'Clear data',
  },
  layer: {
    title: (t) => `Clear ${t ?? 'layer'} assets?`,
    confirmLabel: 'Clear layer',
  },
  global: {
    title: () => 'Clear all chart data?',
    confirmLabel: 'Clear instrument',
  },
}

interface Props {
  chartId: string
  scope: 'global' | 'layer' | 'asset'
  scopeTarget?: string | null
  /** Null while preview is loading (show skeleton). */
  preview: ClearPreview | null
  /** True while the preview API call is in-flight. */
  isLoading?: boolean
  onClose: () => void
  onSuccess: () => void
  onAfterClear?: () => Promise<void>
}

export function ClearConfirmModal({
  chartId,
  scope,
  scopeTarget,
  preview,
  isLoading,
  onClose,
  onSuccess,
  onAfterClear,
}: Props) {
  const [typed, setTyped] = useState('')
  const [executing, setExecuting] = useState(false)
  const [execPct, setExecPct] = useState(0)
  const [execLabel, setExecLabel] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => { setMounted(true) }, [])

  // Close on Escape
  useEffect(() => {
    if (typeof window === 'undefined') return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape' && !executing) onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose, executing])

  // Cleanup timer on unmount
  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current) }, [])

  const cfg = SCOPE_CONFIG[scope]
  const isGlobal = scope === 'global'
  const isL0Layer = scope === 'layer' && scopeTarget === 'brahmagyan'
  const requiresTypedConf = isGlobal || isL0Layer
  const confirmTarget = preview?.requires_typed_confirmation ?? ''
  const typedMatch = !requiresTypedConf || typed === confirmTarget

  const assetsClearable = preview?.assets_clearable ?? []
  const assetsResetOnly = preview?.assets_reset_only ?? []
  const hasReconcilingData = preview?.assets_clearable != null
  const downstreamList: LabeledAsset[] = preview
    ? (preview.downstream_stale_assets_labeled ?? preview.downstream_stale_assets.map(id => ({ id, label: id })))
    : []
  const showLayerSummary = Array.isArray(preview?.layer_summary) && preview!.layer_summary!.length > 0

  function startProgress(durationMs: number) {
    setExecPct(0)
    const n = preview?.affected_assets.length ?? 0
    const tables = preview?.tables.length ?? 0
    setExecLabel(`Clearing ${n} asset${n !== 1 ? 's' : ''} across ${tables} table${tables !== 1 ? 's' : ''}…`)
    const start = Date.now()
    timerRef.current = setInterval(() => {
      const elapsed = Date.now() - start
      const pct = Math.min(88, (elapsed / durationMs) * 100)
      setExecPct(pct)
      if (pct >= 88) clearInterval(timerRef.current!)
    }, 60)
  }

  function finishProgress(success: boolean) {
    if (timerRef.current) clearInterval(timerRef.current)
    if (success) {
      setExecPct(100)
      setExecLabel('Done.')
    } else {
      setExecPct(0)
    }
  }

  async function handleConfirm() {
    if (!preview) return
    setExecuting(true)
    setError(null)
    // Estimate time: row throughput ~50k/s, plus 0.5s per table for FK handling
    const estimatedMs = Math.max(1500, (preview.total_rows / 50000) * 1000 + preview.tables.length * 500)
    startProgress(estimatedMs)
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
          ...(requiresTypedConf ? { typed_confirmation: typed } : {}),
        }),
      })
      const txt = await r.text()
      let body: Record<string, unknown>
      try { body = JSON.parse(txt) }
      catch { throw new Error(`Server error (${r.status}): ${txt.substring(0, 200) || 'no body'}`) }
      if (!r.ok) throw new Error((body.error as string | undefined) ?? `Clear failed (${r.status})`)
      finishProgress(true)
      if (onAfterClear) await onAfterClear()
      onSuccess()
      onClose()
    } catch (e) {
      finishProgress(false)
      setError((e as Error).message)
    } finally {
      setExecuting(false)
    }
  }

  const displayTitle = cfg.title(preview?.scope_label ?? scopeTarget)
  const canConfirm = !executing && !isLoading && !!preview && typedMatch

  if (!mounted) return null

  return createPortal(
    <>
      <style>{`
        @keyframes clear-modal-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
      <AnimatePresence>
        <motion.div
          key="clear-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: DUR.modal, ease: EASE.out }}
          onClick={() => { if (!executing) onClose() }}
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(4,3,2,0.78)',
            backdropFilter: 'blur(2px)',
          }}
        >
          <motion.div
            key="clear-modal"
            initial={{ opacity: 0, scale: 0.97, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 6 }}
            transition={{ duration: DUR.modal, ease: EASE.out }}
            role="dialog"
            aria-modal="true"
            aria-label={displayTitle}
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--black-raised)',
              border: '1px solid rgba(181,71,76,0.28)',
              borderTop: '2px solid rgba(181,71,76,0.55)',
              borderRadius: 'var(--r-card)',
              padding: '24px 28px 22px',
              maxWidth: '500px',
              width: '90vw',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              fontFamily: 'var(--ui-stack)',
              boxShadow: '0 20px 56px rgba(0,0,0,0.72), 0 0 0 1px rgba(181,71,76,0.08)',
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '18px' }}>
              <div>
                <div style={{
                  fontSize: '10px', fontFamily: 'var(--mono-stack)',
                  textTransform: 'uppercase', letterSpacing: '0.12em',
                  color: 'rgba(181,71,76,0.75)', marginBottom: '5px',
                }}>
                  Destructive action
                </div>
                <h2 style={{
                  fontSize: '16px', fontWeight: 600,
                  color: 'var(--on-dark)', margin: 0, lineHeight: 1.3,
                }}>
                  {displayTitle}
                </h2>
              </div>
              {!executing && (
                <button
                  onClick={onClose}
                  aria-label="Close"
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--on-dark-faint)', padding: '2px', marginLeft: '12px',
                    display: 'flex', alignItems: 'center', borderRadius: '4px',
                    transition: 'color 0.15s',
                    flexShrink: 0,
                  }}
                  onMouseEnter={e => (e.currentTarget.style.color = 'var(--on-dark)')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'var(--on-dark-faint)')}
                >
                  <svg width={14} height={14} viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round">
                    <path d="M1 1l12 12M13 1L1 13" />
                  </svg>
                </button>
              )}
            </div>

            {/* Scrollable body */}
            <div style={{ flex: '1 1 auto', minHeight: 0, overflowY: 'auto' }}>

              {/* Impact summary card */}
              <div style={{
                borderRadius: '8px',
                border: '1px solid rgba(255,255,255,0.07)',
                background: 'rgba(255,255,255,0.025)',
                padding: '12px 14px',
                marginBottom: '14px',
              }}>
                {isLoading || !preview ? (
                  // Loading skeleton
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <Shimmer width="60%" height={12} />
                    <Shimmer width="75%" height={12} />
                    <Shimmer width="45%" height={12} />
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', marginTop: '2px', paddingTop: '10px' }}>
                      <Shimmer width="80%" height={13} />
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Per-layer row breakdown */}
                    {showLayerSummary && (
                      <div style={{ marginBottom: '10px' }}>
                        {[...preview.layer_summary!]
                          .sort((a, b) => (LAYER_ORDER.indexOf(a.layer) ?? 99) - (LAYER_ORDER.indexOf(b.layer) ?? 99))
                          .map(ls => (
                            <div key={ls.layer} style={{
                              display: 'flex', justifyContent: 'space-between',
                              padding: '4px 0',
                              borderBottom: '1px solid rgba(255,255,255,0.04)',
                              fontSize: '12px',
                            }}>
                              <span style={{ color: 'var(--on-dark-mut)' }}>
                                {LAYER_LABELS[ls.layer] ?? ls.layer}
                                <span style={{ color: 'var(--on-dark-faint)', fontSize: '10px', marginLeft: '6px' }}>
                                  {ls.asset_count} asset{ls.asset_count !== 1 ? 's' : ''}
                                </span>
                              </span>
                              <span style={{ color: 'var(--on-dark)', fontFamily: 'var(--mono-stack)', fontSize: '12px' }}>
                                {ls.rows.toLocaleString()} rows
                              </span>
                            </div>
                          ))}
                      </div>
                    )}

                    {/* Total */}
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      fontSize: '13px', fontWeight: 600, marginBottom: '8px',
                    }}>
                      <span style={{ color: 'var(--on-dark-mut)' }}>Total rows deleted</span>
                      <span style={{ color: 'var(--on-dark)', fontFamily: 'var(--mono-stack)' }}>
                        {preview.total_rows.toLocaleString()}
                      </span>
                    </div>

                    {/* Reconciling counts */}
                    {hasReconcilingData ? (
                      <div style={{ fontSize: '11px', color: 'var(--on-dark-faint)', lineHeight: 1.8 }}>
                        <span style={{ color: 'var(--on-dark-mut)' }}>{assetsClearable.length}</span> assets cleared
                        {' · '}
                        <span style={{ color: 'var(--on-dark-mut)' }}>{assetsResetOnly.length}</span> reset to dormant
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
                  </>
                )}
              </div>

              {/* Downstream stale tree */}
              {!isLoading && <DownstreamTree assets={downstreamList} />}

              {/* Warning */}
              <div style={{
                fontSize: '12px',
                color: 'rgba(255,255,255,0.38)',
                marginBottom: requiresTypedConf ? '16px' : '20px',
                lineHeight: 1.5,
              }}>
                This action cannot be undone.
                {isGlobal && ' The entire instrument will need to be rebuilt from L0.'}
                {isL0Layer && ' All Brahmagyan foundation data must be rebuilt.'}
              </div>

              {/* Typed confirmation */}
              {requiresTypedConf && preview && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--on-dark-mut)', marginBottom: '4px' }}>
                    Type the subject name to confirm:
                  </div>
                  <div style={{
                    fontSize: '12px', color: 'rgba(181,71,76,0.75)',
                    fontFamily: 'var(--mono-stack)', marginBottom: '7px', letterSpacing: '0.03em',
                  }}>
                    {confirmTarget}
                  </div>
                  <input
                    type="text"
                    value={typed}
                    onChange={e => setTyped(e.target.value)}
                    placeholder={confirmTarget}
                    disabled={executing}
                    autoFocus
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      padding: '8px 11px',
                      background: 'rgba(0,0,0,0.4)',
                      border: `1px solid ${typed === confirmTarget && typed ? 'rgba(74,140,92,0.8)' : typed && typed !== confirmTarget ? 'rgba(181,71,76,0.7)' : 'rgba(255,255,255,0.12)'}`,
                      borderRadius: '5px',
                      color: 'var(--on-dark)',
                      fontFamily: 'var(--ui-stack)', fontSize: '13px',
                      transition: 'border-color 0.15s',
                      outline: 'none',
                    }}
                  />
                </div>
              )}

              {/* Error */}
              {error && (
                <div style={{
                  color: 'var(--marsys-error)', fontSize: '12px',
                  marginBottom: '14px', lineHeight: 1.5,
                  padding: '8px 10px',
                  background: 'rgba(181,71,76,0.08)',
                  border: '1px solid rgba(181,71,76,0.22)',
                  borderRadius: '5px',
                }}>
                  {error}
                </div>
              )}

              {/* Progress bar (during execute) */}
              {executing && <ExecProgressBar pct={execPct} label={execLabel} />}
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '4px', flexShrink: 0 }}>
              <button
                onClick={onClose}
                disabled={executing}
                style={{
                  padding: '7px 18px',
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: 'var(--r-btn)',
                  color: executing ? 'var(--on-dark-faint)' : 'var(--on-dark-mut)',
                  cursor: executing ? 'not-allowed' : 'pointer',
                  fontFamily: 'var(--ui-stack)', fontSize: '13px',
                  transition: 'color 0.15s, border-color 0.15s',
                }}
                onMouseEnter={e => { if (!executing) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)' }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={!canConfirm}
                style={{
                  padding: '7px 18px',
                  background: canConfirm
                    ? 'rgba(181,71,76,0.82)'
                    : 'rgba(181,71,76,0.2)',
                  border: '1px solid rgba(181,71,76,0.45)',
                  borderRadius: 'var(--r-btn)',
                  color: canConfirm ? '#fff' : 'rgba(255,255,255,0.3)',
                  cursor: canConfirm ? 'pointer' : 'not-allowed',
                  fontFamily: 'var(--ui-stack)', fontSize: '13px',
                  fontWeight: 600,
                  transition: 'background 0.15s, color 0.15s',
                  minWidth: '110px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                }}
                onMouseEnter={e => { if (canConfirm) e.currentTarget.style.background = 'rgba(181,71,76,0.95)' }}
                onMouseLeave={e => { if (canConfirm) e.currentTarget.style.background = 'rgba(181,71,76,0.82)' }}
              >
                {executing ? (
                  <>
                    <svg width={11} height={11} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" style={{ animation: 'clear-exec-spin 0.8s linear infinite', flexShrink: 0 }}>
                      <style>{`@keyframes clear-exec-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                    </svg>
                    Clearing…
                  </>
                ) : isLoading ? (
                  <>
                    <svg width={11} height={11} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" style={{ animation: 'clear-exec-spin 0.8s linear infinite', flexShrink: 0 }}>
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                    </svg>
                    Loading…
                  </>
                ) : cfg.confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </>,
    document.body,
  )
}
