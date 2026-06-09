'use client'

import { useState } from 'react'
import type { AssetRow as AssetRowType } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import { ClearIconButton } from './ClearIconButton'
import { RefreshIconButton } from './RefreshIconButton'
import { StopIconButton } from './StopIconButton'
import { PlanModal } from './PlanModal'
import { formatDateTime, formatRelative } from '@/lib/utils/date'
import { Zap } from 'lucide-react'
import { AssetProgressBar } from './AssetProgressBar'
import { useUserRole } from '@/hooks/useUserRole'

interface Props {
  asset: AssetRowType
  stat: AssetStats | null
  chartId: string
  activeRunId: string | null
  activeRunPaused: boolean
  highlighted?: boolean
  allAssets?: AssetRowType[]
  onRunStarted: () => void
}

function derivePrimaryLabel(dormant: boolean): string {
  return dormant ? 'Build' : 'Rebuild'
}

// Service-health pill — replaces progress bar for asset_type='service' rows.
// state='lit' ⟹ GREEN probe passed; 'error' ⟹ probe failed; 'building' ⟹ probe running.
function ServiceHealthPill({
  state,
  hasError,
  errorMsg,
}: {
  state: string
  hasError: boolean
  errorMsg?: string | null
}) {
  const isGreen = state === 'lit'
  const isRunning = state === 'building'
  const isError = hasError || state === 'error'

  const bg = isGreen ? 'rgba(83,180,95,0.15)' : isRunning ? 'rgba(236,197,106,0.12)' : 'rgba(200,60,60,0.12)'
  const border = isGreen ? 'rgba(83,180,95,0.4)' : isRunning ? 'rgba(236,197,106,0.4)' : 'rgba(200,60,60,0.35)'
  const color = isGreen ? 'rgba(83,200,100,0.95)' : isRunning ? '#ECC56A' : 'rgba(220,80,80,0.9)'
  const label = isGreen ? '● GREEN' : isRunning ? '◎ probing…' : isError ? '✕ degraded' : '— dormant'

  return (
    <div>
      <span
        title={isError && errorMsg ? errorMsg : `service health: ${label}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          fontSize: '10px',
          fontFamily: 'var(--mono-stack)',
          padding: '2px 7px',
          borderRadius: '4px',
          background: bg,
          border: `1px solid ${border}`,
          color,
          letterSpacing: '0.03em',
        }}
      >
        {label}
      </span>
      {isError && errorMsg && (
        <div style={{ fontSize: '9px', color: 'var(--marsys-error)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
          {errorMsg.slice(0, 28)}
        </div>
      )}
    </div>
  )
}

export function AssetRow({ asset, stat, chartId, activeRunId, activeRunPaused, highlighted, allAssets, onRunStarted }: Props) {
  const [showPlanModal, setShowPlanModal] = useState(false)
  const { isSuperAdmin } = useUserRole()
  const isActive = asset.is_active
  const hasError = stat?.error != null && stat.error !== 'missing_table'

  // Derive state: prefer throughput state, fallback to row-count heuristic
  const throughputState = stat?.state
  const derivedState: string = !isActive
    ? 'not_migrated'
    : throughputState ?? (stat?.actual_rows ? 'lit' : 'dormant')

  return (
    <div
      data-asset-id={asset.asset_id}
      style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0,42%) minmax(0,28%) minmax(0,14%) minmax(0,16%)',
        gap: '8px',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        fontFamily: 'var(--ui-stack)',
        background: highlighted ? 'rgba(236,197,106,0.08)' : 'transparent',
        boxShadow: highlighted ? 'inset 0 0 0 1px rgba(236,197,106,0.25)' : 'none',
        transition: 'background 0.4s ease, box-shadow 0.4s ease',
      }}
    >
      {/* Asset name — bilingual two-line + catalog_status badge */}
      <div style={{ minWidth: 0 }} title={asset.asset_id}>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <div className="text-[16px] leading-tight font-serif text-[#C4942A]">
              {asset.sanskrit_name}
            </div>
            {asset.catalog_status && (
              <span
                title={`catalog_status: ${asset.catalog_status}`}
                style={{
                  fontSize: '8px',
                  fontFamily: 'var(--mono-stack)',
                  padding: '1px 4px',
                  borderRadius: '3px',
                  letterSpacing: '0.04em',
                  background: asset.catalog_status === 'CURRENT'
                    ? 'rgba(83,180,95,0.18)' : 'rgba(255,255,255,0.07)',
                  color: asset.catalog_status === 'CURRENT'
                    ? 'rgba(83,200,100,0.9)' : 'rgba(255,255,255,0.4)',
                  border: `1px solid ${asset.catalog_status === 'CURRENT'
                    ? 'rgba(83,180,95,0.35)' : 'rgba(255,255,255,0.12)'}`,
                }}
              >
                {asset.catalog_status}
              </span>
            )}
          </div>
          <div className="text-[13px] leading-tight text-white/85 mt-0.5">
            {asset.english_name}
          </div>
        </div>
      </div>

      {/* Progress bar or service-health pill */}
      <div>
        {asset.asset_type === 'service' ? (
          <ServiceHealthPill state={derivedState} hasError={hasError} errorMsg={stat?.error} />
        ) : (
          <>
            <AssetProgressBar
              state={derivedState as 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'not_migrated'}
              actualRows={stat?.actual_rows ?? null}
              targetVolume={asset.target_floor ?? null}
            />
            {hasError && stat?.error && (
              <div style={{ fontSize: '9px', color: 'var(--marsys-error)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
                {stat.error.slice(0, 24)}
              </div>
            )}
          </>
        )}
      </div>

      {/* Last built — relative time with full datetime tooltip */}
      <div
        style={{ fontSize: '11px', color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)' }}
        title={stat?.last_built_at ? formatDateTime(stat.last_built_at) : 'never built'}
      >
        {stat?.last_built_at ? (formatRelative(stat.last_built_at) ?? '—') : '—'}
      </div>

      {/* Actions cell — right edge: [Build/Rebuild] [Refresh] [Stop | Delete] */}
      <div className="flex items-center justify-end gap-1.5">
        {isActive && (
          <>
            {/* Build/Rebuild — hidden when run active */}
            {!activeRunId && (
              <button
                title={derivePrimaryLabel(derivedState === 'dormant')}
                onClick={() => setShowPlanModal(true)}
                className="w-[22px] h-[22px] flex items-center justify-center rounded hover:bg-white/10 text-white/60 hover:text-white transition-colors"
              >
                <Zap size={12} />
              </button>
            )}

            {/* Refresh — always (role-gated for brahmagyan) */}
            {(isSuperAdmin || asset.layer !== 'brahmagyan') && (
              <RefreshIconButton
                chartId={chartId}
                scope="asset"
                scopeTarget={asset.asset_id}
                size={22}
                onRefreshed={onRunStarted}
              />
            )}

            {/* Stop (when running) or Delete (when idle) — role-gated for brahmagyan */}
            {(isSuperAdmin || asset.layer !== 'brahmagyan') && (
              activeRunId ? (
                <StopIconButton runId={activeRunId} size={22} onStopped={onRunStarted} />
              ) : (
                <ClearIconButton
                  chartId={chartId}
                  scope="asset"
                  scopeTarget={asset.asset_id}
                  size={22}
                  onSuccess={onRunStarted}
                />
              )
            )}
          </>
        )}
      </div>

      {showPlanModal && (
        <PlanModal
          chartId={chartId}
          scope="asset"
          scopeTarget={asset.asset_id}
          action={derivedState === 'dormant' ? 'build' : 'rebuild'}
          label={derivePrimaryLabel(derivedState === 'dormant')}
          assets={allAssets}
          onClose={() => setShowPlanModal(false)}
          onRunStarted={(_runId) => {
            setShowPlanModal(false)
            onRunStarted?.()
          }}
        />
      )}
    </div>
  )
}
