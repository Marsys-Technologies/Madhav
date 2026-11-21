'use client'

import Link from 'next/link'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { ActiveRun, ActiveRunAsset } from '@/hooks/useActiveRun'

// Conservative layer availability from server states. This is preparation evidence,
// not a promise that an arbitrary question or an empirical prediction is qualified.
export function preparationLayerState(
  assets: AssetRow[], stats: Map<string, AssetStats>, layer: string,
  preparingAssets: ReadonlySet<string> = new Set(),
  retryAssets: ReadonlySet<string> = new Set(),
) {
  const active = assets.filter(a => a.layer.toLowerCase() === layer && a.is_active)
  const registry = new Map(assets.map(a => [a.asset_id, a]))
  const required = new Set<string>()
  function collect(id: string) {
    if (required.has(id)) return
    required.add(id)
    for (const dependency of registry.get(id)?.depends_on ?? []) collect(dependency)
  }
  active.forEach(a => collect(a.asset_id))
  if (!active.length || [...required].some(id => !registry.get(id)?.is_active || !stats.has(id))) return 'Status unavailable'
  if ([...required].some(id => preparingAssets.has(id))) return 'Preparation in progress'
  if ([...required].some(id => retryAssets.has(id) || stats.get(id)?.state === 'error')) return 'Preparation needs a retry'
  const evidence = [...required].map(id => stats.get(id)!)
  if (evidence.some(stat => stat.state === 'stale' || stat.build_state_stale)) return 'Needs refresh'
  return evidence.every(s => !s.error && (s.state === 'lit' || s.state === 'service_ok'))
    ? 'Prepared' : 'Preparation incomplete'
}

const EMPTY_ACTIVE_RUN_ASSETS: ActiveRunAsset[] = []

export function PreparationReadiness({ assets, stats, unavailable, chartId, activeRun, activeRunAssets = EMPTY_ACTIVE_RUN_ASSETS, preparationRetryAssets = [] }: {
  assets: AssetRow[]; stats: Map<string, AssetStats>; unavailable: boolean; chartId: string; activeRun: ActiveRun | null
  activeRunAssets?: ActiveRunAsset[]
  preparationRetryAssets?: string[]
}) {
  const terminalInRun = new Set(
    activeRunAssets
      .filter(a => a.state === 'complete' || a.state === 'skipped' || a.state === 'error' || a.state === 'aborted')
      .map(a => a.asset_id),
  )
  const preparing = new Set(
    (activeRun?.plan?.length
      ? activeRun.plan
      : activeRunAssets.map(a => a.asset_id)
    ).filter(id => !terminalInRun.has(id)),
  )
  const retry = new Set(preparationRetryAssets)
  if (activeRun && !activeRun.plan.length && !activeRunAssets.length) {
    for (const asset of assets) {
      if (activeRun.scope === 'global' || (activeRun.scope === 'layer' && activeRun.scope_target === asset.layer)
        || (activeRun.scope === 'asset' && activeRun.scope_target === asset.asset_id)
        || (activeRun.scope === 'asset_set' && activeRun.scope_target?.split(',').map(id => id.trim()).includes(asset.asset_id))) {
        preparing.add(asset.asset_id)
      }
    }
  }
  const effectiveStats = new Map(stats)
  if (activeRunAssets.length > 0) {
    const registryById = new Map(assets.map(a => [a.asset_id, a]))
    for (const ra of activeRunAssets) {
      const existing = effectiveStats.get(ra.asset_id)
      if (!existing) continue
      if (ra.state === 'complete' && existing.state !== 'incomplete' && existing.state !== 'partial') {
        const reg = registryById.get(ra.asset_id)
        const isService = reg?.asset_type === 'service' || reg?.asset_kind === 'service'
        effectiveStats.set(ra.asset_id, {
          ...existing,
          state: isService ? 'service_ok' : 'lit',
          error: null,
          build_state_stale: false,
        })
      } else if (ra.state === 'error' && ra.disposition !== 'blocked_dependency' && existing.state !== 'incomplete' && existing.state !== 'partial') {
        effectiveStats.set(ra.asset_id, {
          ...existing,
          state: 'error',
          error: existing.error ?? ra.error,
        })
      }
    }
  }
  return <aside className="preparation-readiness" aria-label="What you can ask now">
    <h2>What you can ask now</h2>
    <ul>{[
      ['ganita', 'Structure, strengths and divisional charts', 'Gaṇita'],
      ['bodha', 'Yogas, house themes and significations', 'Bodha'],
      ['kala', 'Timing and activation windows', 'Kāla'],
      ['phala', 'Synthesised indications', 'Phala'],
      ['mimamsa', 'Falsifiers and prediction review', 'Mīmāṃsā'],
    ].map(([layer, label, name]) => <li key={layer}>
      {label}<small>{name} · {unavailable ? 'Status unavailable'
        : preparationLayerState(assets, effectiveStats, layer, preparing, retry)}</small>
    </li>)}</ul>
    <p className="j1-note" style={{ margin: '16px 0' }}>These are layer preparation checks. Consultation checks the specific evidence each question needs.</p>
    <Link href={`/clients/${chartId}/pariprashna`} className="j1-btn">Open Consultation</Link>
  </aside>
}
