'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion } from 'framer-motion'
import type { BuildAction, BuildScope } from '@/lib/build/plan'
import { MiniDAG } from './MiniDAG'
import { DUR, EASE } from './motion'

interface PlanData {
  plan: string[]
  includes_upstream_count: number
  estimated_seconds: number | null
}

interface AssetNode {
  asset_id: string
  sanskrit_name: string
  english_name: string
  depends_on?: string[] | null
}

interface Props {
  chartId: string
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  label: string
  onClose: () => void
  onRunStarted: (runId: string) => void
  assets?: AssetNode[]
}

export function PlanModal({ chartId, scope, scopeTarget, action, label, onClose, onRunStarted, assets }: Props) {
  const [planData, setPlanData] = useState<PlanData | null>(null)
  const [loading, setLoading] = useState<'plan' | 'run' | null>('plan')
  const [isClearing, setIsClearing] = useState(false)
  // When the server returns requires_double_confirm for L0 brahmagyan clear, show inline panel
  const [l0ConfirmPending, setL0ConfirmPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Portal mount guard (SSR-safe): mounting to <body> lifts the modal out of the
  // cockpit's nested stacking contexts so the constellation SVG can't overpaint it.
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  // Fetch plan on first render
  useState(() => {
    ;(async () => {
      try {
        const r = await fetch('/api/cockpit/plan', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget, action }),
        })
        const body = await r.json()
        if (!r.ok) throw new Error(body.error ?? 'Failed to resolve plan')
        setPlanData(body.data)
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(null)
      }
    })()
  })

  const runPlan = async (opts: { forceL0?: boolean } = {}) => {
    if (!planData) return
    setLoading('run')
    setError(null)
    setL0ConfirmPending(false)
    const clearBefore = action === 'rebuild'
    if (clearBefore) setIsClearing(true)
    try {
      const r = await fetch('/api/cockpit/runs', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_id: chartId,
          scope,
          scope_target: scopeTarget,
          action,
          clear_before: clearBefore,
          ...(opts.forceL0 ? { force_l0: true } : {}),
        }),
      })
      const body = await r.json()
      setIsClearing(false)
      // HTTP 202 = L0 double-confirm required
      if (r.status === 202 && body.requires_double_confirm) {
        setL0ConfirmPending(true)
        setLoading(null)
        return
      }
      if (!r.ok) throw new Error(body.error ?? 'Failed to start run')
      onRunStarted(body.data.run_id)
    } catch (e) {
      setIsClearing(false)
      setError((e as Error).message)
      setLoading(null)
    }
  }

  const estimateLabel = planData?.estimated_seconds == null
    ? 'unknown'
    : planData.estimated_seconds < 60
      ? `~${planData.estimated_seconds}s`
      : `~${Math.ceil(planData.estimated_seconds / 60)}m`

  // Button label: "Clear & Rebuild" for rebuild, "Run plan" for build/cascade/update
  const confirmLabel = action === 'rebuild' ? 'Clear & Rebuild' : 'Run plan'
  const loadingLabel = isClearing ? 'Clearing…' : 'Starting…'

  if (!mounted) return null

  return createPortal(
    <motion.div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: DUR.modal }}
    >
      <motion.div
        style={{
          background: 'var(--black-raised)',
          border: '1px solid var(--black-line)',
          borderRadius: 'var(--r-card)',
          padding: '24px',
          width: '480px',
          maxHeight: '70vh',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
        initial={{ opacity: 0, scale: 0.98, y: 6 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: DUR.modal, ease: EASE.out }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontFamily: 'var(--display-stack)', color: 'var(--gold-high)', fontSize: '16px', margin: 0 }}>
            {label} plan
          </h2>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--on-dark-faint)', fontSize: '18px', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>

        {loading === 'plan' && (
          <div style={{ color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)', fontSize: '12px' }}>
            Resolving plan…
          </div>
        )}

        {error && (
          <div style={{ color: 'var(--marsys-error)', fontSize: '12px', fontFamily: 'var(--ui-stack)' }}>
            {error}
          </div>
        )}

        {planData && (
          <>
            <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', fontFamily: 'var(--ui-stack)' }}>
              {planData.plan.length} asset{planData.plan.length !== 1 ? 's' : ''} · estimated {estimateLabel}
              {action === 'rebuild' && (
                <span style={{ marginLeft: '8px', color: 'rgba(181,71,76,0.9)', fontSize: '11px' }}>
                  · existing data will be cleared first
                </span>
              )}
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {planData.plan.map((assetId, i) => (
                <div
                  key={assetId}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    padding: '5px 0',
                    borderBottom: '1px solid var(--black-line)',
                    fontFamily: 'var(--mono-stack)', fontSize: '11px',
                    color: 'var(--on-dark)',
                  }}
                >
                  <span style={{ color: 'var(--on-dark-faint)', minWidth: '20px' }}>{i + 1}.</span>
                  <span>{assetId}</span>
                </div>
              ))}
            </div>

            {/* MiniDAG — shown for multi-asset rebuild/update plans when assets data is available */}
            {planData.plan.length > 1 && action !== 'build' && scopeTarget && assets && assets.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{
                  fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em',
                  color: 'var(--on-dark-faint)', marginBottom: '8px',
                }}>
                  Rebuild closure
                </div>
                <MiniDAG
                  targetAssetId={scopeTarget}
                  planAssetIds={planData.plan}
                  assets={assets}
                />
              </div>
            )}
            {/* L0 double-confirm panel — shown when server returns requires_double_confirm */}
            {l0ConfirmPending && (
              <div style={{
                padding: '12px',
                background: 'rgba(181,71,76,0.12)',
                border: '1px solid rgba(181,71,76,0.4)',
                borderRadius: '6px',
                fontSize: '12px',
                fontFamily: 'var(--ui-stack)',
                color: 'var(--on-dark)',
                lineHeight: 1.5,
              }}>
                <div style={{ color: 'rgba(220,100,104,1)', fontWeight: 600, marginBottom: '6px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  L0 Brahmagyan — clear confirmation required
                </div>
                This will permanently delete all Brahmagyan layer data before rebuilding. This action cannot be undone.
              </div>
            )}

            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={onClose}
                disabled={loading === 'run'}
                style={{
                  padding: '6px 14px', borderRadius: '6px', fontSize: '12px',
                  background: 'transparent', border: '1px solid var(--black-line)',
                  color: 'var(--on-dark-faint)', cursor: loading === 'run' ? 'default' : 'pointer',
                  opacity: loading === 'run' ? 0.5 : 1,
                }}
              >
                Cancel
              </button>
              {l0ConfirmPending ? (
                <button
                  className="marsys-btn-danger"
                  onClick={() => runPlan({ forceL0: true })}
                  disabled={loading === 'run'}
                  style={{ opacity: loading === 'run' ? 0.7 : 1 }}
                >
                  {loading === 'run' ? loadingLabel : 'Confirm — clear L0 & rebuild'}
                </button>
              ) : (
                <button
                  className="marsys-btn-primary"
                  onClick={() => runPlan()}
                  disabled={loading === 'run'}
                  style={{ opacity: loading === 'run' ? 0.7 : 1 }}
                >
                  {loading === 'run' ? loadingLabel : confirmLabel}
                </button>
              )}
            </div>
          </>
        )}
      </motion.div>
    </motion.div>,
    document.body,
  )
}
