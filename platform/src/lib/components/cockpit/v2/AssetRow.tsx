'use client'

import { useState } from 'react'
import type { AssetRow as AssetRowType } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { SubstepOverlay } from './DataAssetsView'
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
  substep?: SubstepOverlay | null
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
  const isGreen = state === 'lit' || state === 'service_ok'
  const isRunning = state === 'building'
  const isError = hasError || state === 'error'

  // Same block geometry as AssetProgressBar (full-width 22px track + right-edge
  // state pill), so a service row reads consistently with the data rows.
  const fill = isGreen ? 'rgba(83,180,95,0.55)' : isRunning ? 'rgba(168,124,48,0.7)' : isError ? 'rgba(232,108,108,0.55)' : 'rgba(122,86,24,0.0)'
  const stroke = isGreen ? 'rgba(83,180,95,0.7)' : isRunning ? 'rgba(200,154,70,0.75)' : isError ? 'rgba(232,108,108,0.85)' : 'rgba(122,86,24,0.4)'
  const pillColor = isGreen ? 'rgba(140,210,140,0.95)' : isRunning ? 'rgba(236,197,106,0.95)' : isError ? 'rgba(232,108,108,1)' : 'rgba(155,131,80,0.8)'
  const pill = isGreen ? 'LIVE' : isRunning ? 'PROBING' : isError ? 'FAILED' : 'DORMANT'

  return (
    <div>
      <div
        style={{ position: 'relative', height: '22px', width: '100%' }}
        title={isError && errorMsg ? errorMsg : `service health: ${pill}`}
      >
        {/* Track */}
        <div style={{ position: 'absolute', inset: 0, borderRadius: '3px', border: `1px solid ${stroke}`, background: 'rgba(15,12,8,0.6)' }} />
        {/* Fill */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, borderRadius: '3px', background: fill }} />
        {/* State pill — right edge, mirrors AssetProgressBar */}
        <div
          style={{
            position: 'absolute', top: '2px', right: '2px', bottom: '2px',
            display: 'flex', alignItems: 'center', padding: '0 6px',
            borderRadius: '2px', background: 'rgba(10,8,6,0.85)',
            color: pillColor, fontFamily: 'var(--mono-stack)',
            fontSize: '8px', letterSpacing: '0.06em', textTransform: 'uppercase',
          }}
        >
          {pill}
        </div>
      </div>
      {isError && errorMsg && (
        <div style={{ fontSize: '9px', color: 'var(--marsys-error)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
          {errorMsg.slice(0, 28)}
        </div>
      )}
    </div>
  )
}

// Per-asset status dot — collapses the repeated "CURRENT" text chip into a
// single colored circle. green = CURRENT + healthy/lit; amber = building/stale/
// dormant-but-current; red = error / not_migrated / catalog DRAFT.
function StatusDot({
  catalogStatus,
  state,
}: {
  catalogStatus: string | null
  state: string
}) {
  const isDraft = catalogStatus === 'DRAFT'
  const isHealthy = state === 'lit' || state === 'service_ok'
  const isAmber = state === 'building' || state === 'stale' || state === 'dormant' || state === 'reconnecting'
  const isRed = state === 'error' || state === 'not_migrated' || isDraft

  const color = isRed
    ? 'rgba(220,80,80,0.95)'
    : isHealthy
      ? 'rgba(83,200,100,0.95)'
      : isAmber
        ? '#ECC56A'
        : 'rgba(255,255,255,0.35)'

  const word = isHealthy ? 'healthy' : state
  const title = `${catalogStatus ?? 'unknown'} · ${word}`

  return (
    <span
      title={title}
      style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 4px ${color}`,
        flexShrink: 0,
        display: 'inline-block',
      }}
    />
  )
}

export function AssetRow({ asset, stat, chartId, activeRunId, activeRunPaused, highlighted, allAssets, substep, onRunStarted }: Props) {
  const [showPlanModal, setShowPlanModal] = useState(false)
  const { isSuperAdmin } = useUserRole()
  const isActive = asset.is_active
  const isDataPlaneDown = stat?.error_class === 'dataplane'
  // Suppress red-error display when the failure is a transient data-plane blip
  const hasError = stat?.error != null && stat.error !== 'missing_table' && !isDataPlaneDown

  // Derive state: prefer throughput state, fallback to row-count heuristic.
  // Data-plane errors show as 'reconnecting' (amber) rather than 'error' (red)
  // so a transient proxy restart doesn't falsely mark healthy assets as FAILED.
  const throughputState = stat?.state
  const derivedState: string = !isActive
    ? 'not_migrated'
    : isDataPlaneDown
      ? 'reconnecting'
      : throughputState ?? (stat?.actual_rows ? 'lit' : 'dormant')

  return (
    <div
      data-asset-id={asset.asset_id}
      style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0,42%) minmax(0,28%) minmax(0,14%) minmax(0,16%)',
        gap: '16px',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        fontFamily: 'var(--ui-stack)',
        background: highlighted ? 'rgba(236,197,106,0.08)' : 'transparent',
        boxShadow: highlighted ? 'inset 0 0 0 1px rgba(236,197,106,0.25)' : 'none',
        transition: 'background 0.4s ease, box-shadow 0.4s ease',
      }}
    >
      {/* Asset name — bilingual two-line + status dot */}
      <div style={{ minWidth: 0 }} title={asset.asset_id}>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <StatusDot catalogStatus={asset.catalog_status} state={derivedState} />
            <div className="text-[18px] leading-tight font-serif font-medium text-[#C4942A]">
              {asset.sanskrit_name}
            </div>
          </div>
          <div className="text-[13px] leading-tight text-white/85 mt-0.5">
            {asset.english_name}
          </div>
        </div>
      </div>

      {/* Progress bar or service-health pill */}
      <div>
        {(asset.asset_type === 'service' || asset.asset_kind === 'service') ? (
          <ServiceHealthPill state={derivedState} hasError={hasError} errorMsg={stat?.error} />
        ) : (
          <>
            <AssetProgressBar
              state={derivedState as 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'not_migrated' | 'reconnecting'}
              actualRows={stat?.actual_rows ?? null}
              targetVolume={asset.target_floor ?? null}
            />
            {/* Live substep progress — visible only during building when orchestrator emits asset.substep */}
            {derivedState === 'building' && substep != null && (
              <div style={{ display: 'flex', gap: '8px', marginTop: '3px', fontFamily: 'var(--mono-stack)', fontSize: '9px', color: 'rgba(255,255,255,0.45)', lineHeight: 1 }}>
                {substep.actual_rows > 0 && (
                  <span>{substep.actual_rows.toLocaleString()} rows</span>
                )}
                {substep.substep_total > 0 && (
                  <span>Step {substep.substep_index} / {substep.substep_total}</span>
                )}
              </div>
            )}
            {/* build-state stale badge: data present but throughput record is stale/absent */}
            {stat?.build_state_stale && (
              <div style={{ fontSize: '9px', color: 'rgba(236,197,106,0.65)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
                build-state stale
              </div>
            )}
            {/* Transient data-plane blip — amber, not red */}
            {isDataPlaneDown && (
              <div style={{ fontSize: '9px', color: '#ECC56A', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
                data plane reconnecting…
              </div>
            )}
            {hasError && stat?.error && (
              <div style={{ fontSize: '9px', color: 'var(--marsys-error)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
                {stat.error.slice(0, 24)}
              </div>
            )}
          </>
        )}
      </div>

      {/* Last built — relative time with full datetime tooltip (centered column) */}
      <div
        style={{ fontSize: '11px', color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)', textAlign: 'center' }}
        title={stat?.last_built_at ? formatDateTime(stat.last_built_at) : 'never built'}
      >
        {stat?.last_built_at ? (formatRelative(stat.last_built_at) ?? '—') : '—'}
      </div>

      {/* Actions cell — centered column: [Build/Rebuild] [Refresh] [Stop | Delete] */}
      <div className="flex items-center justify-center gap-1.5">
        {isActive && (
          <>
            {/* Build/Rebuild — hidden when run active; role-gated for brahmagyan */}
            {!activeRunId && (isSuperAdmin || asset.layer !== 'brahmagyan') && (
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
