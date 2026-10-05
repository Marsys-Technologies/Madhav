'use client'

import Link from 'next/link'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

// Conservative layer availability from server states. This is preparation evidence,
// not a promise that an arbitrary question or an empirical prediction is qualified.
export function preparationLayerState(assets: AssetRow[], stats: Map<string, AssetStats>, layer: string) {
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
  return [...required].every(id => {
    const s = stats.get(id)!
    return !s.error && !s.build_state_stale && (s.state === 'lit' || s.state === 'service_ok')
  }) ? 'Prepared' : 'Preparation incomplete'
}

export function PreparationReadiness({ assets, stats, unavailable, chartId }: {
  assets: AssetRow[]; stats: Map<string, AssetStats>; unavailable: boolean; chartId: string
}) {
  return <aside className="preparation-readiness" aria-label="What you can ask now">
    <h2>What you can ask now</h2>
    <ul>{[
      ['ganita', 'Structure, strengths and divisional charts', 'Gaṇita'],
      ['bodha', 'Yogas, house themes and significations', 'Bodha'],
      ['kala', 'Timing and activation windows', 'Kāla'],
      ['phala', 'Synthesised indications', 'Phala'],
      ['mimamsa', 'Falsifiers and prediction review', 'Mīmāṃsā'],
    ].map(([layer, label, name]) => <li key={layer}>
      {label}<small>{name} · {unavailable ? 'Status unavailable' : preparationLayerState(assets, stats, layer)}</small>
    </li>)}</ul>
    <p className="j1-note" style={{ margin: '16px 0' }}>These are layer preparation checks. Consultation checks the specific evidence each question needs.</p>
    <Link href={`/clients/${chartId}/pariprashna`} className="j1-btn">Open Consultation</Link>
  </aside>
}
