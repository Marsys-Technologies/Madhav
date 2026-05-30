'use client'

/**
 * CascadePreviewModal — shows affected descendants before a rebuild
 * [PHASE-C-05]
 */

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { getAssetDisplayName } from '@/lib/build/asset_names'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

// ─── Types ────────────────────────────────────────────────────────────────────

interface CascadeData {
  target: string
  descendants: string[]
  count: number
}

interface Props {
  open: boolean
  onClose: () => void
  assetId: string
  buildId: string
  chartId: string
  onConfirm: () => void
}

// ─── Component ────────────────────────────────────────────────────────────────

export function CascadePreviewModal({ open, onClose, assetId, buildId, chartId, onConfirm }: Props) {
  const [cascade, setCascade] = useState<CascadeData | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    setError(null)
    fetch(`/api/build/cascade-preview?asset_id=${encodeURIComponent(assetId)}`)
      .then((r) => r.json())
      .then((d: CascadeData) => setCascade(d))
      .catch(() => setError('Failed to load cascade preview.'))
      .finally(() => setLoading(false))
  }, [open, assetId])

  if (!open) return null

  // Build mini graph data
  const graphNodes = cascade
    ? [
        { id: cascade.target, label: cascade.target, color: '#9c3a2a' },
        ...cascade.descendants.map((d) => ({ id: d, label: d, color: '#d4a648' })),
      ]
    : []
  const graphLinks = cascade
    ? cascade.descendants.map((d) => ({ source: cascade.target, target: d }))
    : []

  async function handleConfirm() {
    setConfirming(true)
    try {
      await fetch('/api/build/rebuild', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_id: assetId, build_id: buildId, chart_id: chartId }),
      })
      onConfirm()
    } finally {
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={onClose}>
      <div
        className="bg-[#0d0c10] border border-[#1a1820] rounded-xl p-6 w-[520px] max-h-[80vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-serif text-base text-[#d4a648]">Cascade Preview</h3>
          <button onClick={onClose} className="text-[#5a5550] hover:text-[#c8bfb0] text-lg leading-none">×</button>
        </div>

        {loading && (
          <p className="text-[#5a5550] text-sm py-8 text-center">Loading cascade…</p>
        )}

        {error && (
          <p className="text-[#9c3a2a] text-sm">{error}</p>
        )}

        {!loading && cascade && (
          <>
            {/* Mini force graph */}
            <div style={{ height: 300 }} className="rounded-lg overflow-hidden border border-[#1a1820] mb-4">
              <ForceGraph2D
                graphData={{ nodes: graphNodes, links: graphLinks } as unknown as { nodes: object[]; links: object[] }}
                nodeId="id"
                nodeColor={(n) => (n as { color: string }).color}
                nodeRelSize={5}
                linkColor={() => '#2a2830'}
                backgroundColor="#08070a"
                width={468}
                height={300}
              />
            </div>

            <p className="text-sm text-[#c8bfb0] mb-3">
              Rebuilding{' '}
              <span className="text-[#d4a648] font-medium">
                {getAssetDisplayName(cascade.target)}
              </span>{' '}
              will recompute{' '}
              <span className="text-[#d4a648] font-medium">{cascade.descendants.length}</span>{' '}
              downstream asset{cascade.descendants.length !== 1 ? 's' : ''}:
            </p>

            {cascade.descendants.length > 0 && (
              <ul className="mb-4 space-y-1 text-sm text-[#8a8070]">
                {cascade.descendants.map((d) => (
                  <li key={d} className="flex items-center gap-2">
                    <span className="text-[#d4a648]/50">→</span>
                    {getAssetDisplayName(d)}
                  </li>
                ))}
              </ul>
            )}

            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-sm text-[#8a8070] hover:text-[#c8bfb0] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={confirming}
                className="px-4 py-2 rounded-lg text-sm bg-[#d4a648] text-[#08070a] hover:bg-[#e8c878] font-medium disabled:opacity-50 transition-colors"
              >
                {confirming
                  ? 'Starting…'
                  : `Rebuild ${cascade.descendants.length + 1} asset${cascade.descendants.length !== 0 ? 's' : ''}`
                }
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
