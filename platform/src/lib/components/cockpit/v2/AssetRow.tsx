'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import type { AssetRow as AssetRowType } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { SubstepOverlay } from './DataAssetsView'
import { ClearIconButton } from './ClearIconButton'
import { RefreshIconButton } from './RefreshIconButton'
import { StopIconButton } from './StopIconButton'
import { formatDateTime, formatRelative } from '@/lib/utils/date'
import { Zap, Database, Cpu, Link2 } from 'lucide-react'
import { AssetProgressBar } from './AssetProgressBar'
import { deriveBuildStage } from './buildStage'
import type { SubstepInfo } from './buildStage'
import { useUserRole } from '@/hooks/useUserRole'
import { CascadePreviewModal, type PlanAssetInfo } from '@/components/cockpit/CascadePreviewModal'

interface Props {
  asset: AssetRowType
  stat: AssetStats | null
  chartId: string
  activeRunId: string | null
  activeRunPaused: boolean
  /** True only for the single asset the run is currently building — gates the Stop control
   *  so idle/queued/completed assets don't each show a (whole-run) Stop during a build. */
  isActiveAsset?: boolean
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
  const prefersReducedMotion = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const isGreen = state === 'lit' || state === 'service_ok'
  const isRunning = state === 'building'
  const isError = hasError || state === 'error'

  // Same block geometry as AssetProgressBar (full-width 28px track + right-edge
  // state pill), so a service row reads consistently with the data rows.
  // Gold brand palette for lit/service_ok (F2: revert green→gold, native ruling 2026-06-26)
  const fill = isGreen ? 'rgba(176,137,58,0.92)' : isRunning ? 'rgba(168,124,48,0.7)' : isError ? 'rgba(232,108,108,0.55)' : 'rgba(122,86,24,0.0)'
  const stroke = isGreen ? 'rgba(212,166,72,0.9)' : isRunning ? 'rgba(200,154,70,0.75)' : isError ? 'rgba(232,108,108,0.85)' : 'rgba(122,86,24,0.4)'
  const pillColor = isGreen ? 'rgba(236,197,106,0.95)' : isRunning ? 'rgba(236,197,106,0.95)' : isError ? 'rgba(232,108,108,1)' : 'rgba(155,131,80,0.8)'
  const pill = isGreen ? 'LIVE' : isRunning ? 'PROBING' : isError ? 'FAILED' : 'DORMANT'

  const dotColor = isGreen ? '#4CAF50' : isRunning ? '#ECC56A' : isError ? '#B5474C' : 'rgba(255,255,255,0.2)'
  const dotShadow = isGreen ? '0 0 6px rgba(76,175,80,0.6)' : isRunning ? '0 0 6px rgba(236,197,106,0.6)' : 'none'
  const dotAnimation = (isGreen || isRunning) && !prefersReducedMotion ? 'obs-live-pulse 1.8s ease-in-out infinite' : 'none'
  const labelColor = isGreen ? 'rgba(255,255,255,0.7)' : isRunning ? 'var(--gold-high)' : isError ? 'rgba(232,108,108,0.8)' : 'var(--on-dark-faint)'
  const labelText = isGreen ? 'Service responding' : isRunning ? 'Probing…' : isError ? 'Service failed' : 'Dormant'

  // Fill tint color at reduced opacity for heartbeat background
  const fillTint = isGreen ? 'rgba(176,137,58,0.3)' : isRunning ? 'rgba(168,124,48,0.3)' : isError ? 'rgba(232,108,108,0.3)' : 'rgba(122,86,24,0.0)'

  return (
    <div>
      <div
        style={{ position: 'relative', height: '28px', width: '100%' }}
        title={isError && errorMsg ? errorMsg : `service health: ${pill}`}
      >
        {/* Track */}
        <div style={{ position: 'absolute', inset: 0, borderRadius: '4px', border: `1px solid ${stroke}`, background: 'rgba(15,12,8,0.6)' }} />
        {/* Fill — heartbeat treatment: reduced-opacity tint + pulsing dot + label */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, borderRadius: '4px', background: fillTint }}>
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', paddingLeft: 10, gap: 7, paddingRight: 64 }}>
            {/* Pulsing dot */}
            <div style={{
              width: 6, height: 6, borderRadius: '50%',
              background: dotColor,
              boxShadow: dotShadow,
              animation: dotAnimation,
              flexShrink: 0,
            }} />
            {/* Status label */}
            <span style={{
              fontFamily: 'var(--mono-stack)', fontSize: 10,
              color: labelColor,
            }}>
              {labelText}
            </span>
          </div>
        </div>
        {/* State pill — right edge, mirrors AssetProgressBar */}
        <div
          style={{
            position: 'absolute', top: '3px', right: '3px', bottom: '3px',
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
          {errorMsg.slice(0, 80)}
        </div>
      )}
    </div>
  )
}

// Per-asset status dot — collapses the repeated "CURRENT" text chip into a
// single colored circle. green = healthy/lit regardless of catalog status;
// amber = building/stale/dormant; red = error / not_migrated / DRAFT·unhealthy.
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
  // DRAFT only forces red when the asset is NOT healthy — a running DRAFT asset is green.
  const isRed = state === 'error' || state === 'not_migrated' || (isDraft && !isHealthy)

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

interface CascadePending {
  assetId: string
  action: 'build' | 'rebuild'
  plan: string[]
  planInfo?: PlanAssetInfo[]
  estimatedSeconds?: number | null
}

export function AssetRow({ asset, stat, chartId, activeRunId, activeRunPaused, isActiveAsset, highlighted, allAssets, substep, onRunStarted }: Props) {
  const [pendingCascade, setPendingCascade] = useState<CascadePending | null>(null)
  const [planLoading, setPlanLoading] = useState(false)
  const { isSuperAdmin } = useUserRole()

  async function handleRebuildClick() {
    const action = derivedState === 'dormant' ? 'build' : 'rebuild'
    setPlanLoading(true)
    // open modal in loading state immediately
    setPendingCascade({ assetId: asset.asset_id, action, plan: [], estimatedSeconds: null })
    try {
      const r = await fetch('/api/cockpit/plan', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope: 'asset', scope_target: asset.asset_id, action }),
      })
      const body = await r.json().catch(() => null)
      if (!r.ok || !body?.data) {
        toast.error(body?.error ?? 'Failed to resolve build plan')
        setPendingCascade(null)
        return
      }
      const { plan, estimated_seconds } = body.data as { plan: string[]; estimated_seconds: number | null }
      // E2: enrich plan with names + layer from allAssets for structured modal display
      const planInfo: PlanAssetInfo[] | undefined = allAssets
        ? plan.map(id => {
            const a = allAssets.find(r => r.asset_id === id)
            return {
              asset_id: id,
              layer: a?.layer ?? '',
              english_name: a?.english_name ?? id,
              sanskrit_name: a?.sanskrit_name ?? id,
            }
          })
        : undefined
      setPendingCascade({ assetId: asset.asset_id, action, plan, planInfo, estimatedSeconds: estimated_seconds })
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to fetch plan')
      setPendingCascade(null)
    } finally {
      setPlanLoading(false)
    }
  }

  async function handleCascadeConfirm() {
    if (!pendingCascade) return
    try {
      const r = await fetch('/api/cockpit/runs', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_id: chartId,
          scope: 'asset',
          scope_target: pendingCascade.assetId,
          action: pendingCascade.action,
        }),
      })
      const body = await r.json().catch(() => null)
      if (!r.ok) {
        toast.error(body?.error ?? 'Failed to start build')
        return
      }
      setPendingCascade(null)
      onRunStarted()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to start build')
    }
  }
  // O1: distinguish BLOCKED cascade errors from genuine root failures
  function isBlockedCascade(errorMessage: string): boolean {
    return errorMessage.startsWith('BLOCKED:')
  }

  const isActive = asset.is_active
  const isDataPlaneDown = stat?.error_class === 'dataplane'
  // Suppress red-error display when the failure is a transient data-plane blip
  const hasError = stat?.error != null && stat.error !== 'missing_table' && !isDataPlaneDown

  // Derive state: prefer throughput state, fallback to row-count heuristic.
  // Data-plane errors show as 'reconnecting' (amber) rather than 'error' (red)
  // so a transient proxy restart doesn't falsely mark healthy assets as FAILED.
  const throughputState = stat?.state
  const derivedState: string = !isActive
    ? (asset.catalog_status === 'RETIRED' ? 'retired' : 'not_migrated')
    : isDataPlaneDown
      ? 'reconnecting'
      : throughputState ?? (stat?.actual_rows ? 'lit' : 'dormant')

  // Derive build stage from substep + state data.
  // isQueued: asset appears as building in polled stats but no SSE state event has
  // arrived yet (substep overlay is absent) — treat as queued in the run plan.
  const substepData: SubstepInfo | undefined = (substep && substep.substep_total > 0)
    ? { index: substep.substep_index, total: substep.substep_total, label: substep.substep_label }
    : undefined
  const isQueued = derivedState === 'building' && substep == null
  const buildStage = deriveBuildStage({
    polledState: derivedState,
    substepIndex: substepData?.index,
    substepTotal: substepData?.total,
    isQueued,
  })

  return (
    <>
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
      {/* Asset name — bilingual two-line + status dot + type icon */}
      <div style={{ minWidth: 0 }} title={asset.asset_id}>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <StatusDot catalogStatus={asset.catalog_status} state={derivedState} />
            {/* F1: service vs data glyph — keyed off asset_type / asset_kind */}
            {(asset.asset_type === 'service' || asset.asset_kind === 'service')
              ? <Cpu size={10} style={{ color: 'rgba(212,166,72,0.55)', flexShrink: 0 }} aria-label="service" />
              : <Database size={10} style={{ color: 'rgba(212,166,72,0.35)', flexShrink: 0 }} aria-label="data" />
            }
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
              state={derivedState}
              actualRows={stat?.actual_rows ?? null}
              targetVolume={asset.target_floor ?? null}
              stage={buildStage}
              substep={substepData}
              isQueued={isQueued}
            />
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
              isBlockedCascade(stat.error) ? (
                // O1: blocked cascade — amber/orange, chain icon, distinct tooltip
                <div
                  style={{ fontSize: '9px', color: 'rgba(236,147,50,0.9)', marginTop: '2px', fontFamily: 'var(--mono-stack)', maxWidth: '52ch', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '4px' }}
                  title={`Blocked by upstream failure — ${stat.error}`}
                >
                  <Link2 size={9} style={{ flexShrink: 0, color: 'rgba(236,147,50,0.8)' }} />
                  <span>blocked by upstream failure</span>
                </div>
              ) : (
                // O1: genuine root failure — keep existing red styling
                <div
                  style={{ fontSize: '9px', color: 'var(--marsys-error)', marginTop: '2px', fontFamily: 'var(--mono-stack)', maxWidth: '52ch', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                  title={stat.error}
                >
                  {stat.error.slice(0, 64)}
                </div>
              )
            )}
            {/* O2: lit asset with 0 rows — subtle note, not alarming */}
            {derivedState === 'lit' && stat?.rows_written === 0 && (
              <div
                style={{ fontSize: '9px', color: 'rgba(255,255,255,0.35)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}
                title={asset.target_floor === 0 ? '0 rows by design (target_floor = 0 for this asset)' : '0 rows written — expected for some chart types'}
              >
                {asset.target_floor === 0 ? '0 rows (by design)' : '0 rows'}
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
                onClick={handleRebuildClick}
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

            {/* Stop only on the asset actually building; idle/queued/completed assets during a
                run show nothing (Stop everywhere is misleading — it just halts the whole run).
                Delete shows only when no run is active. Role-gated for brahmagyan. */}
            {(isSuperAdmin || asset.layer !== 'brahmagyan') && (
              activeRunId ? (
                isActiveAsset
                  ? <StopIconButton runId={activeRunId} size={22} onStopped={onRunStarted} />
                  : null
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

    </div>
    <CascadePreviewModal
      isOpen={pendingCascade !== null}
      isLoading={planLoading}
      onClose={() => setPendingCascade(null)}
      onConfirm={handleCascadeConfirm}
      rootAssetId={asset.asset_id}
      rootAssetLabel={asset.english_name ?? asset.asset_id}
      plan={pendingCascade?.plan ?? []}
      planInfo={pendingCascade?.planInfo}
      estimatedSeconds={pendingCascade?.estimatedSeconds}
    />
    </>
  )
}
