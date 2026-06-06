'use client'

import { useState } from 'react'
import type { BuildAction, BuildScope } from '@/lib/build/plan'

interface PlanData {
  plan: string[]
  includes_upstream_count: number
  estimated_seconds: number | null
}

interface Props {
  chartId: string
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  label: string
  onClose: () => void
  onRunStarted: (runId: string) => void
}

export function PlanModal({ chartId, scope, scopeTarget, action, label, onClose, onRunStarted }: Props) {
  const [planData, setPlanData] = useState<PlanData | null>(null)
  const [loading, setLoading] = useState<'plan' | 'run' | null>('plan')
  const [error, setError] = useState<string | null>(null)

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

  const runPlan = async () => {
    if (!planData) return
    setLoading('run')
    setError(null)
    try {
      const r = await fetch('/api/cockpit/runs', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget, action }),
      })
      const body = await r.json()
      if (!r.ok) throw new Error(body.error ?? 'Failed to start run')
      onRunStarted(body.data.run_id)
    } catch (e) {
      setError((e as Error).message)
      setLoading(null)
    }
  }

  const estimateLabel = planData?.estimated_seconds == null
    ? 'unknown'
    : planData.estimated_seconds < 60
      ? `~${planData.estimated_seconds}s`
      : `~${Math.ceil(planData.estimated_seconds / 60)}m`

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
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
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={onClose}
                style={{
                  padding: '6px 14px', borderRadius: '6px', fontSize: '12px',
                  background: 'transparent', border: '1px solid var(--black-line)',
                  color: 'var(--on-dark-faint)', cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                className="marsys-btn-primary"
                onClick={runPlan}
                disabled={loading === 'run'}
                style={{ opacity: loading === 'run' ? 0.7 : 1 }}
              >
                {loading === 'run' ? 'Starting…' : 'Run plan'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
