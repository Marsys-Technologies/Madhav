'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchAssets } from '@/lib/performance/api_client'
import {
  LAYER_ORDER,
  layerLabel,
  BADGE_COLORS,
  type HealthBadge,
  type ReachabilityLabel,
  type AssetCatalogEntry,
} from '@/lib/performance/asset_health'

// ── Filter state ─────────────────────────────────────────────────────────────

interface Filters {
  layer: string | null
  health: HealthBadge | null
  reachability: ReachabilityLabel | null
}

function matches(entry: AssetCatalogEntry, filters: Filters): boolean {
  if (filters.layer && entry.layer !== filters.layer) return false
  if (filters.health && entry.health !== filters.health) return false
  if (filters.reachability && entry.reachability !== filters.reachability) return false
  return true
}

// ── Badge chip ────────────────────────────────────────────────────────────────

function Badge({ badge }: { badge: HealthBadge }) {
  const color = BADGE_COLORS[badge]
  const label = badge === 'green' ? '● OK' : badge === 'yellow' ? '● Drift' : badge === 'red' ? '● Stale' : '○ Hidden'
  return (
    <span className="text-[11px] font-medium tabular-nums" style={{ color }}>
      {label}
    </span>
  )
}

// ── Drilldown panel ───────────────────────────────────────────────────────────

function DrilldownPanel({
  entry,
  onClose,
}: {
  entry: AssetCatalogEntry
  onClose: () => void
}) {
  return (
    <div
      className="fixed inset-y-0 right-0 z-50 flex w-[420px] flex-col overflow-y-auto border-l p-6 shadow-xl"
      style={{
        background: 'var(--surface-panel)',
        borderColor: 'rgba(var(--brand-gold-rgb),0.18)',
      }}
    >
      <div className="flex items-start justify-between">
        <h3 className="bt-label bt-label-upper font-semibold" style={{ color: 'var(--brand-gold)' }}>
          {entry.canonical_id}
        </h3>
        <button
          onClick={onClose}
          className="text-xs text-muted-foreground hover:text-foreground"
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      <dl className="mt-4 space-y-3 text-[13px]">
        {[
          ['Path', entry.path],
          ['Layer', entry.layer],
          ['Version', entry.version],
          ['Status', entry.status],
          ['Interface version', entry.interface_version],
          ['Fingerprint', entry.fingerprint ? entry.fingerprint.slice(0, 16) + '…' : '—'],
          ['Representations', (entry.representations ?? []).join(', ') || '—'],
          ['Bound tools', entry.bound_tools.length > 0 ? entry.bound_tools.join(', ') : 'none'],
        ].map(([label, value]) => (
          <div key={label} className="grid grid-cols-[140px_1fr] gap-1">
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="break-all font-mono text-[12px]">{value}</dd>
          </div>
        ))}
      </dl>

      {entry.bound_tools.length > 0 && (
        <div className="mt-6">
          <p className="bt-label mb-2" style={{ color: 'var(--brand-gold)' }}>Retrieval tools</p>
          <ul className="space-y-1">
            {entry.bound_tools.map(t => (
              <li key={t} className="font-mono text-[12px] text-foreground">{t}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Asset row ─────────────────────────────────────────────────────────────────

function AssetRow({
  entry,
  onSelect,
}: {
  entry: AssetCatalogEntry
  onSelect: (e: AssetCatalogEntry) => void
}) {
  return (
    <tr
      className="cursor-pointer border-b transition-colors hover:bg-[rgba(212,175,55,0.04)]"
      style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.08)' }}
      onClick={() => onSelect(entry)}
    >
      <td className="py-2 pr-3 font-mono text-[12px] text-foreground">{entry.canonical_id}</td>
      <td className="py-2 pr-3 text-[12px] text-muted-foreground">{entry.layer}</td>
      <td className="py-2 pr-3 text-[12px] text-muted-foreground">{entry.version}</td>
      <td className="py-2 pr-3 text-[12px] text-muted-foreground">{entry.status}</td>
      <td className="py-2 pr-3">
        <Badge badge={entry.health} />
      </td>
      <td className="py-2 text-[12px] text-muted-foreground">
        {entry.bound_tools.length > 0
          ? <span style={{ color: 'var(--status-success)' }}>{entry.bound_tools.length} tool{entry.bound_tools.length > 1 ? 's' : ''}</span>
          : <span className="text-muted-foreground/50">—</span>}
      </td>
    </tr>
  )
}

// ── Layer section ─────────────────────────────────────────────────────────────

function LayerGroup({
  layer,
  entries,
  onSelect,
}: {
  layer: string
  entries: AssetCatalogEntry[]
  onSelect: (e: AssetCatalogEntry) => void
}) {
  const [collapsed, setCollapsed] = React.useState(false)
  return (
    <div>
      <button
        className="flex w-full items-center gap-2 py-2 text-left"
        onClick={() => setCollapsed(c => !c)}
      >
        <span className="bt-label" style={{ color: 'var(--brand-gold)' }}>
          {layerLabel(layer)}
        </span>
        <span className="text-xs text-muted-foreground">({entries.length})</span>
        <span className="ml-auto text-xs text-muted-foreground">{collapsed ? '▶' : '▼'}</span>
      </button>
      {!collapsed && (
        <table className="w-full">
          <thead>
            <tr className="text-left text-[11px] uppercase text-muted-foreground/60">
              <th className="pb-1 pr-3 font-normal">canonical_id</th>
              <th className="pb-1 pr-3 font-normal">layer</th>
              <th className="pb-1 pr-3 font-normal">version</th>
              <th className="pb-1 pr-3 font-normal">status</th>
              <th className="pb-1 pr-3 font-normal">health</th>
              <th className="pb-1 font-normal">tools</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(e => (
              <AssetRow key={e.canonical_id} entry={e} onSelect={onSelect} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ── Filter chip ───────────────────────────────────────────────────────────────

function FilterChip<T extends string>({
  label,
  value,
  active,
  onClick,
}: {
  label: string
  value: T
  active: boolean
  onClick: (v: T | null) => void
}) {
  return (
    <button
      onClick={() => onClick(active ? null : value)}
      className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
        active
          ? 'border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.12)] text-[var(--brand-gold)]'
          : 'border-transparent text-muted-foreground hover:border-[rgba(212,175,55,0.2)] hover:text-[var(--brand-gold)]'
      }`}
    >
      {label}
    </button>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function AssetCatalogSection() {
  const assetsQ = useQuery({
    queryKey: ['perf-assets'],
    queryFn: fetchAssets,
    staleTime: 300_000,
  })

  const [filters, setFilters] = React.useState<Filters>({ layer: null, health: null, reachability: null })
  const [selected, setSelected] = React.useState<AssetCatalogEntry | null>(null)

  const entries = React.useMemo(() => assetsQ.data?.entries ?? [], [assetsQ.data])

  const filtered = React.useMemo(
    () => entries.filter(e => matches(e, filters)),
    [entries, filters],
  )

  const byLayer = React.useMemo(() => {
    const map = new Map<string, AssetCatalogEntry[]>()
    for (const e of filtered) {
      const layer = e.layer ?? '?'
      const bucket = map.get(layer) ?? []
      bucket.push(e)
      map.set(layer, bucket)
    }
    return map
  }, [filtered])

  const availableLayers = React.useMemo(
    () => LAYER_ORDER.filter(l => entries.some(e => e.layer === l)),
    [entries],
  )

  const scoreboard = React.useMemo(() => ({
    total: entries.length,
    green: entries.filter(e => e.health === 'green').length,
    withTools: entries.filter(e => e.bound_tools.length > 0).length,
    reachable: entries.filter(e => e.reachability === 'reachable').length,
  }), [entries])

  return (
    <section className="space-y-4" data-testid="asset-catalog-section">
      <div className="flex items-baseline justify-between">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>Asset Catalog</h2>
        {assetsQ.isFetching && <span className="text-xs text-muted-foreground">loading…</span>}
      </div>

      {/* Scoreboard */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Total assets', value: scoreboard.total },
          { label: 'Healthy (green)', value: scoreboard.green },
          { label: 'With tools', value: scoreboard.withTools },
          { label: 'Reachable', value: scoreboard.reachable },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="rounded border p-3"
            style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)', background: 'rgba(var(--brand-gold-rgb),0.03)' }}
          >
            <div className="bt-display text-lg" style={{ color: 'var(--brand-gold-cream)' }}>{value}</div>
            <div className="bt-label mt-0.5 text-[11px] text-muted-foreground">{label}</div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="bt-label mr-1 text-muted-foreground">Layer:</span>
        {availableLayers.map(l => (
          <FilterChip
            key={l}
            label={l}
            value={l}
            active={filters.layer === l}
            onClick={v => setFilters(f => ({ ...f, layer: v }))}
          />
        ))}
        <span className="mx-2 text-muted-foreground/30">|</span>
        <span className="bt-label mr-1 text-muted-foreground">Health:</span>
        {(['green', 'yellow', 'red', 'gray'] as HealthBadge[]).map(h => (
          <FilterChip
            key={h}
            label={h}
            value={h}
            active={filters.health === h}
            onClick={v => setFilters(f => ({ ...f, health: v }))}
          />
        ))}
        <span className="mx-2 text-muted-foreground/30">|</span>
        <span className="bt-label mr-1 text-muted-foreground">Reach:</span>
        {(['reachable', 'no_tool'] as ReachabilityLabel[]).map(r => (
          <FilterChip
            key={r}
            label={r}
            value={r}
            active={filters.reachability === r}
            onClick={v => setFilters(f => ({ ...f, reachability: v }))}
          />
        ))}
        {(filters.layer || filters.health || filters.reachability) && (
          <button
            onClick={() => setFilters({ layer: null, health: null, reachability: null })}
            className="text-xs text-muted-foreground underline underline-offset-2"
          >
            clear
          </button>
        )}
      </div>

      {/* Asset list grouped by layer */}
      {assetsQ.isError && (
        <p className="text-sm text-destructive">Failed to load asset catalog.</p>
      )}
      {assetsQ.isSuccess && filtered.length === 0 && (
        <p className="text-sm text-muted-foreground">No assets match current filters.</p>
      )}
      <div className="space-y-4">
        {LAYER_ORDER.filter(l => byLayer.has(l)).map(l => (
          <LayerGroup
            key={l}
            layer={l}
            entries={byLayer.get(l)!}
            onSelect={setSelected}
          />
        ))}
      </div>

      {/* Drilldown */}
      {selected && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/30"
            onClick={() => setSelected(null)}
          />
          <DrilldownPanel entry={selected} onClose={() => setSelected(null)} />
        </>
      )}
    </section>
  )
}
