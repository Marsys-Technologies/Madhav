'use client'

import { useEffect, useState } from 'react'
import { Trash2 } from 'lucide-react'
import { formatDate } from '@/lib/utils/date'
import { useActiveRun } from '@/hooks/useActiveRun'
import { BuildActionButton } from './BuildActionButton'

function deriveGlobalLabel(assets: { state: string }[]): 'Build' | 'Update' | 'Rebuild' {
  const total = assets.length
  if (total === 0) return 'Build'
  const dormant = assets.filter(a => a.state === 'dormant' || a.state === 'not_migrated').length
  const stale = assets.filter(a => a.state === 'stale').length
  if (dormant === total) return 'Build'
  if (stale > 0) return 'Update'
  return 'Rebuild'
}

interface Props {
  chartId: string
  chartName?: string | null
  birthDate?: string | null
  birthPlace?: string | null
  assets?: { state: string }[]
  proMode?: boolean
  onProModeToggle?: () => void
  onGlobalClear?: () => void
  onGlobalRebuild?: () => void
}

export function CockpitHeader({
  chartId,
  chartName,
  birthDate,
  birthPlace,
  assets = [],
  proMode = false,
  onProModeToggle,
  onGlobalClear,
  onGlobalRebuild,
}: Props) {
  const [sidecarHealthy, setSidecarHealthy] = useState<boolean | null>(null)
  const { run: activeRun, refresh: refreshRun } = useActiveRun(chartId)

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch('/api/sidecar/health', {
          credentials: 'include',
          cache: 'no-store',
        })
        const body = await r.json()
        setSidecarHealthy(!!body.healthy)
      } catch {
        setSidecarHealthy(false)
      }
    }
    check()
    const t = setInterval(check, 30_000)
    return () => clearInterval(t)
  }, [])

  const sidecarLabel =
    sidecarHealthy === null ? '…' : sidecarHealthy ? 'OK' : 'DOWN'

  const globalRunId = activeRun?.id ?? null
  const globalRunPaused = activeRun?.state === 'paused'

  const globalLabel = deriveGlobalLabel(assets)
  const dormantCount = assets.filter(a => a.state === 'dormant' || a.state === 'not_migrated').length
  const staleCount = assets.filter(a => a.state === 'stale').length

  return (
    <div
      style={{
        background: 'var(--black-raised)',
        border: '1px solid var(--black-line)',
        borderRadius: 'var(--r-card)',
        padding: '20px 24px',
        margin: '0 0 8px 0',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* Left: chart name + coords */}
        <div>
          <h1
            style={{
              fontFamily: 'var(--display-stack)',
              color: 'var(--gold-high)',
              fontSize: '20px',
              fontVariant: 'small-caps',
              margin: 0,
            }}
          >
            {chartName ?? 'Loading chart…'}
          </h1>
          <div
            style={{
              fontFamily: 'var(--ui-stack)',
              fontSize: '12px',
              color: 'var(--on-dark-mut)',
              marginTop: '2px',
            }}
          >
            {formatDate(birthDate) || '—'} · {birthPlace ?? '—'}{' '}
            <span
              style={{
                fontFamily: 'var(--mono-stack)',
                fontSize: '11px',
                color: 'var(--on-dark-faint)',
              }}
            >
              {chartId.slice(0, 8)}…
            </span>
          </div>
        </div>
        {/* Right: Pro view pill + Build CTA (SIDECAR status lives in telemetry strip below) */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={onProModeToggle}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 10px',
              borderRadius: '12px',
              background: proMode ? 'rgba(168,124,42,0.28)' : 'rgba(168,124,42,0.10)',
              border: `1px solid ${proMode ? 'var(--gold-engrave)' : 'rgba(168,124,42,0.35)'}`,
              color: proMode ? 'var(--gold-bright)' : 'var(--on-dark-faint)',
              fontSize: '10px',
              fontFamily: 'var(--ui-stack)',
              fontWeight: 600,
              letterSpacing: '0.05em',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            ◆ Pro view
          </button>
          <BuildActionButton
            chartId={chartId}
            scope="global"
            scopeTarget={null}
            stats={{
              total: assets.length || 1,
              dormant: dormantCount,
              stale: staleCount,
              active_run_id: globalRunId,
              is_paused: globalRunPaused,
            }}
            onRunStarted={refreshRun}
            onRunStateChange={refreshRun}
            onRebuildOverride={globalLabel === 'Rebuild' ? onGlobalRebuild : undefined}
          />
          {!globalRunId && (
            <button
              title="Clear instrument"
              onClick={() => onGlobalClear?.()}
              className="w-[28px] h-[28px] flex items-center justify-center rounded hover:bg-red-500/20 text-white/40 hover:text-red-400 transition-colors ml-1"
            >
              <Trash2 size={15} />
            </button>
          )}
        </div>
      </div>
      {/* Telemetry strip */}
      <div
        style={{
          marginTop: '12px',
          display: 'flex',
          gap: '16px',
          fontSize: '11px',
          color: 'var(--on-dark-faint)',
          fontFamily: 'var(--mono-stack)',
          flexWrap: 'wrap',
        }}
      >
        {(
          [
            ['WRITERS', '—'],
            ['QUEUE', '—'],
            ['QPS', '—'],
            ['BUILD', '—'],
            ['SIDECAR', sidecarLabel],
            ['SPEND', '—'],
          ] as [string, string][]
        ).map(([k, v]) => (
          <span key={k}>
            <span
              style={{
                color: 'var(--on-dark-faint)',
                textTransform: 'uppercase',
                fontSize: '9.5px',
                letterSpacing: '0.08em',
              }}
            >
              {k}
            </span>{' '}
            <span style={{ color: 'var(--on-dark)' }}>{v}</span>
          </span>
        ))}
      </div>
    </div>
  )
}
