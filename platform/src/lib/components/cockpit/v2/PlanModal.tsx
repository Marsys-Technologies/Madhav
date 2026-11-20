'use client'

import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion } from 'framer-motion'
import type { BlockerEntry, BuildAction, BuildScope } from '@/lib/build/plan'
import { MiniDAG } from './MiniDAG'
import { DUR, EASE } from './motion'
import { useMounted } from '@/hooks/useMounted'

interface PlanData {
  plan: string[]
  plan_waves: string[][]
  status: 'ok' | 'blocked'
  blocked?: boolean
  blockers: (BlockerEntry | string)[]
  includes_upstream_count: number
  estimated_seconds: number | null
  downstream_may_become_stale?: string[]
  protected_assets?: { asset_id: string; message: string }[]
  duration_history?: { sample_count: number; lower_seconds: number | null; upper_seconds: number | null }
}

interface AssetNode {
  asset_id: string
  sanskrit_name: string
  english_name: string
  depends_on?: string[] | null
  catalog_status?: string | null   // 'DRAFT' | 'CURRENT' | 'RETIRED' | null
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
  preparation?: boolean
}

export function PlanModal({ chartId, scope, scopeTarget, action, label, onClose, onRunStarted, assets, preparation = false }: Props) {
  const [planData, setPlanData] = useState<PlanData | null>(null)
  const [loading, setLoading] = useState<'plan' | 'run' | null>('plan')
  const [isClearing, setIsClearing] = useState(false)
  // When the server returns requires_double_confirm for L0 brahmagyan clear, show inline panel
  const [l0ConfirmPending, setL0ConfirmPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const clearBefore = !preparation && action === 'rebuild' && !(scope === 'layer' && scopeTarget === 'brahmagyan')
  const throughBodha = preparation && scope === 'asset_set'
  // Portal mount guard (SSR-safe): mounting to <body> lifts the modal out of the
  // cockpit's nested stacking contexts so the constellation SVG can't overpaint it.
  const mounted = useMounted()
  const dialogRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef(onClose)
  useEffect(() => { closeRef.current = onClose }, [onClose])
  useEffect(() => {
    if (!mounted) return
    const previous = document.activeElement as HTMLElement | null
    dialogRef.current?.querySelector<HTMLButtonElement>('button')?.focus()
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') closeRef.current()
      if (event.key !== 'Tab') return
      const buttons = dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')
      const first = buttons?.[0], last = buttons?.[buttons.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    document.addEventListener('keydown', handleKey)
    return () => { document.removeEventListener('keydown', handleKey); if (previous?.isConnected) previous.focus() }
  }, [mounted])

  useEffect(() => {
    const controller = new AbortController()
    ;(async () => {
      try {
        const r = await fetch('/api/cockpit/plan', {
          method: 'POST',
          credentials: 'include',
          signal: controller.signal,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chart_id: chartId, scope, scope_target: scopeTarget, action,
            ...(throughBodha ? { preparation: true } : {}),
          }),
        })
        const body = await r.json()
        if (!r.ok) throw new Error(body.error ?? 'Failed to resolve plan')
        const rawData = body.data as PlanData
        if (rawData.status === 'blocked' || rawData.blocked === true) {
          throw new Error(
            rawData.blockers?.length
              ? 'Build blocked — upstream assets must be rebuilt first: ' +
                rawData.blockers.map(b => typeof b === 'string'
                  ? b
                  : `${b.dep_asset_id} is ${b.dep_state}${b.required_by.length ? `; required by ${b.required_by.join(', ')}` : ''}`
                ).join('\n')
              : 'Build blocked by upstream dependencies'
          )
        }
        if (!controller.signal.aborted) {
          setPlanData({ ...rawData, plan: rawData.plan_waves?.flat() ?? rawData.plan ?? [] })
        }
      } catch (e) {
        if (!controller.signal.aborted) setError((e as Error).message)
      } finally {
        if (!controller.signal.aborted) setLoading(null)
      }
    })()
    return () => controller.abort()
  }, [chartId, scope, scopeTarget, action, throughBodha])

  const runPlan = async (opts: { forceL0?: boolean } = {}) => {
    if (!planData) return
    setLoading('run')
    setError(null)
    setL0ConfirmPending(false)
    // Preparation replaces data in each writer's own transaction. Shared Brahmagyan is never pre-cleared.
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
          ...(throughBodha ? {
            expected_plan: planData.plan,
            expected_downstream: planData.downstream_may_become_stale ?? [],
          } : {}),
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
      if (!r.ok) {
        if (body?.code === 'PRECONDITION_FAILED' && Array.isArray(body.missing)) {
          throw new Error(body.missing.join('\n'))
        }
        if (body?.code === 'UPSTREAM_BLOCKED' && Array.isArray(body?.blockers)) {
          const lines = (body.blockers as { dep_asset_id: string }[])
            .map(b => `• ${b.dep_asset_id}`)
            .join('\n')
          throw new Error(
            `Build blocked — these upstream assets must be ready first:\n${lines}`
          )
        }
        throw new Error(body.error ?? 'Failed to start run')
      }
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
  const history = planData?.duration_history
  const duration = history && history.sample_count >= 3 &&
    history.lower_seconds != null && history.upper_seconds != null
    ? `${Math.ceil(history.lower_seconds / 60)}–${Math.ceil(history.upper_seconds / 60)} min for the middle half of ${history.sample_count} comparable runs`
    : 'More completed runs are needed for a duration range'

  const confirmLabel = clearBefore ? 'Clear & Rebuild' : action === 'rebuild' ? 'Rebuild' : 'Run plan'
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
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={`${label} plan`}
        style={{
          background: 'var(--black-raised)',
          border: '1px solid var(--black-line)',
          borderRadius: 'var(--r-card)',
          padding: '24px',
          width: 'min(480px, 90vw)',
          maxHeight: '70vh',
          overflow: 'hidden',
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
            aria-label="Close plan"
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
          <div style={{ color: 'var(--marsys-error)', fontSize: '12px', fontFamily: 'var(--ui-stack)', whiteSpace: 'pre-wrap' }}>
            {error}
          </div>
        )}

        {planData && (
          <>
            <div style={{ fontSize: '12px', color: 'var(--on-dark-faint)', fontFamily: 'var(--ui-stack)' }}>
              {planData.plan.length} asset{planData.plan.length !== 1 ? 's' : ''} · {throughBodha ? duration : `estimated ${estimateLabel}`}
              {clearBefore && (
                <span style={{ marginLeft: '8px', color: 'rgba(181,71,76,0.9)', fontSize: '11px' }}>
                  · existing data will be cleared first
                </span>
              )}
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {!!planData.protected_assets?.length && <p>
                Protected assets: {planData.protected_assets.map(a => a.asset_id).join(', ')}
              </p>}
              {!!planData.downstream_may_become_stale?.length && <p>
                Results that may need a later refresh: {planData.downstream_may_become_stale
                  .map(id => assets?.find(asset => asset.asset_id === id)?.english_name ?? id).join(', ')}
              </p>}
              {planData.plan.map((assetId, i) => {
                const assetMeta = assets?.find(a => a.asset_id === assetId)
                const isDraft = assetMeta?.catalog_status === 'DRAFT'
                return (
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
                    <span>{preparation ? assetMeta?.english_name ?? assetId : assetId}</span>
                    {isDraft && (
                      <span style={{
                        fontSize: '9px', padding: '1px 5px', borderRadius: '3px',
                        background: 'var(--gold-glow)', color: 'var(--gold-high)',
                        border: '1px solid var(--gold-core)',
                        textTransform: 'uppercase', letterSpacing: '0.04em', marginLeft: 'auto',
                      }}>
                        DRAFT
                      </span>
                    )}
                  </div>
                )
              })}

              {/* MiniDAG — inside scroll area so tall DAGs don't push buttons off-screen */}
              {planData.plan.length > 1 && scope === 'asset' && action !== 'build' && scopeTarget && assets && assets.length > 0 && (
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
            </div>
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
                  disabled={loading === 'run' || planData.plan.length === 0}
                  style={{ opacity: loading === 'run' ? 0.7 : 1 }}
                >
                  {loading === 'run' ? loadingLabel : 'Confirm — clear L0 & rebuild'}
                </button>
              ) : (
                <button
                  className="marsys-btn-primary"
                  onClick={() => runPlan()}
                  disabled={loading === 'run' || planData.plan.length === 0}
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
