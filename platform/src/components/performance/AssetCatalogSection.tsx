'use client'

import * as React from 'react'
import type { AssetEntry, AssetCatalog, HealthBadge } from '@/lib/performance/asset_health'

// Re-export types so the component is self-contained for consumers
export type { AssetEntry, AssetCatalog, HealthBadge }

const LAYER_ORDER = ['L0', 'L1', 'L1.5', 'L2.5', 'L3', 'L3.5', 'L6', 'L8', 'L9', 'governance', 'Other']

function HealthDot({ badge }: { badge: HealthBadge }) {
  const colors: Record<HealthBadge, string> = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-400',
    red: 'bg-red-500',
    gray: 'bg-gray-400',
  }
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${colors[badge]}`}
      title={badge}
      aria-label={`health: ${badge}`}
    />
  )
}

function pathLastSegment(p: string): string {
  const parts = p.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] ?? p
}

function DrilldownPanel({
  entry,
  onClose,
}: {
  entry: AssetEntry
  onClose: () => void
}) {
  const { health, ...rest } = entry
  return (
    <div
      className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col border-l bg-card shadow-xl"
      style={{ borderColor: 'rgba(212,175,55,0.20)' }}
    >
      <div
        className="flex items-center justify-between border-b px-4 py-3"
        style={{ borderColor: 'rgba(212,175,55,0.15)' }}
      >
        <span className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>
          Asset detail
        </span>
        <button
          onClick={onClose}
          className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted/20 hover:text-foreground"
          aria-label="Close"
        >
          Close ✕
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-3 flex items-center gap-2">
          <HealthDot badge={health} />
          <span className="text-sm font-medium" style={{ color: 'var(--brand-gold-cream)' }}>
            {entry.canonical_id ?? pathLastSegment(entry.path)}
          </span>
        </div>
        <pre
          className="overflow-x-auto rounded border p-3 text-xs"
          style={{
            background: 'oklch(0.10 0.010 70)',
            borderColor: 'rgba(212,175,55,0.15)',
            color: 'oklch(0.82 0.060 88)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {JSON.stringify({ health, ...rest }, null, 2)}
        </pre>
      </div>
    </div>
  )
}

const ALL_STATUSES = ['CURRENT', 'LIVING', 'SUPERSEDED', 'DEAD_DATA', 'GOVERNANCE_CLOSED'] as const
type StatusFilter = 'all' | typeof ALL_STATUSES[number]

export function AssetCatalogSection() {
  const [catalog, setCatalog] = React.useState<AssetCatalog | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [selectedLayer, setSelectedLayer] = React.useState<string>('all')
  const [statusFilter, setStatusFilter] = React.useState<StatusFilter>('all')
  const [collapsed, setCollapsed] = React.useState<Record<string, boolean>>({})
  const [drilldown, setDrilldown] = React.useState<AssetEntry | null>(null)

  React.useEffect(() => {
    setLoading(true)
    fetch('/api/performance/assets')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<AssetCatalog>
      })
      .then((data) => {
        setCatalog(data)
        setLoading(false)
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : 'unknown error')
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="space-y-2 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 rounded bg-muted/20" />
        ))}
      </div>
    )
  }

  if (error || !catalog) {
    return (
      <div className="rounded border border-red-500/30 p-4 text-sm text-red-400">
        Failed to load asset catalog{error ? `: ${error}` : ''}
      </div>
    )
  }

  const { byLayer, totalCount, reachableCount } = catalog
  const reachablePct = totalCount > 0 ? ((reachableCount / totalCount) * 100).toFixed(1) : '0.0'

  // Ordered layers present in data
  const layers = [
    ...LAYER_ORDER.filter((l) => l in byLayer),
    ...Object.keys(byLayer).filter((l) => !LAYER_ORDER.includes(l)),
  ]

  // Apply filters
  const filteredByLayer: Record<string, AssetEntry[]> = {}
  for (const layer of layers) {
    if (selectedLayer !== 'all' && layer !== selectedLayer) continue
    const entries = (byLayer[layer] ?? []).filter((e) => {
      if (statusFilter === 'all') return true
      return e.status === statusFilter
    })
    if (entries.length > 0) filteredByLayer[layer] = entries
  }

  const filteredLayers = Object.keys(filteredByLayer)
  const totalFiltered = filteredLayers.reduce((n, l) => n + filteredByLayer[l].length, 0)

  function toggleCollapse(layer: string) {
    setCollapsed((prev) => ({ ...prev, [layer]: !prev[layer] }))
  }

  return (
    <>
      {/* Coverage scoreboard */}
      <div
        className="mb-3 flex flex-wrap items-center gap-4 rounded border p-3 text-xs"
        style={{ borderColor: 'rgba(212,175,55,0.18)', background: 'rgba(212,175,55,0.04)' }}
      >
        <span style={{ color: 'var(--brand-gold-cream)' }}>
          Total assets: <strong>{totalCount}</strong>
        </span>
        <span style={{ color: 'var(--brand-gold-cream)' }}>
          Reachable by planner:{' '}
          <strong>
            {reachableCount} ({reachablePct}%)
          </strong>
        </span>
        <span className="text-muted-foreground">Showing {totalFiltered} entries</span>
      </div>

      {/* Filter bar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1">
          <span className="bt-label mr-1 text-xs text-muted-foreground">Layer:</span>
          {['all', ...layers].map((l) => (
            <button
              key={l}
              onClick={() => setSelectedLayer(l)}
              className={`rounded-full border px-2 py-0.5 text-xs font-medium transition-colors ${
                selectedLayer === l
                  ? 'border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.12)] text-[var(--brand-gold)]'
                  : 'border-transparent text-muted-foreground hover:bg-[rgba(212,175,55,0.06)]'
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1">
          <span className="bt-label mr-1 text-xs text-muted-foreground">Status:</span>
          {(['all', 'CURRENT', 'LIVING', 'SUPERSEDED'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-full border px-2 py-0.5 text-xs font-medium transition-colors ${
                statusFilter === s
                  ? 'border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.12)] text-[var(--brand-gold)]'
                  : 'border-transparent text-muted-foreground hover:bg-[rgba(212,175,55,0.06)]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Asset list */}
      {filteredLayers.length === 0 ? (
        <div className="rounded border p-6 text-center text-sm text-muted-foreground" style={{ borderColor: 'rgba(212,175,55,0.12)' }}>
          No assets match the current filter
        </div>
      ) : (
        <div className="space-y-3">
          {filteredLayers.map((layer) => {
            const isCollapsed = !!collapsed[layer]
            const entries = filteredByLayer[layer]
            return (
              <div key={layer} className="rounded border" style={{ borderColor: 'rgba(212,175,55,0.14)' }}>
                <button
                  className="flex w-full items-center justify-between px-3 py-2 text-left"
                  onClick={() => toggleCollapse(layer)}
                  style={{ background: 'rgba(212,175,55,0.05)' }}
                >
                  <span className="text-xs font-semibold" style={{ color: 'var(--brand-gold)' }}>
                    {layer}
                    <span className="ml-2 font-normal text-muted-foreground">({entries.length})</span>
                  </span>
                  <span className="text-xs text-muted-foreground">{isCollapsed ? '▸' : '▾'}</span>
                </button>
                {!isCollapsed && (
                  <div className="divide-y" style={{ borderColor: 'rgba(212,175,55,0.08)' }}>
                    {entries.map((entry, idx) => {
                      const displayName = entry.canonical_id ?? pathLastSegment(entry.path)
                      return (
                        <button
                          key={`${layer}-${idx}`}
                          className="flex w-full items-center gap-3 px-3 py-2 text-left text-xs hover:bg-[rgba(212,175,55,0.04)] transition-colors"
                          onClick={() => setDrilldown(entry)}
                        >
                          <HealthDot badge={entry.health} />
                          <span className="min-w-0 flex-1 truncate font-mono" style={{ color: 'var(--brand-gold-cream)' }}>
                            {displayName}
                          </span>
                          <span className="shrink-0 text-muted-foreground">{entry.status ?? '—'}</span>
                          <span className="shrink-0" title={entry.tool_name ? `tool: ${entry.tool_name}` : 'not planner-reachable'}>
                            {entry.tool_name ? '✓' : '—'}
                          </span>
                          <span className="shrink-0 text-muted-foreground" title="expose_to_chat">
                            {entry.expose_to_chat === true ? '💬' : entry.expose_to_chat === false ? '—' : '?'}
                          </span>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Drilldown panel */}
      {drilldown && (
        <DrilldownPanel entry={drilldown} onClose={() => setDrilldown(null)} />
      )}
    </>
  )
}
