'use client'

import { AssetNodeData } from './AssetNode'

interface AssetDetailPanelProps {
  asset: AssetNodeData | null
  onClose: () => void
  isOpen: boolean
}

const ASSET_DESCRIPTIONS: Record<string, { full_name: string; description: string; output: string }> = {
  A1_engine:          { full_name: 'Engine Invocation',       description: 'Natal chart computed via Swiss Ephemeris for all 23 bodies × 5 ayanamshas in parallel.', output: 'Planetary positions, houses, dignities for each ayanamsha' },
  A2_forensic_render: { full_name: 'FORENSIC.md Render',      description: 'Deterministic markdown render of all chart sections. No narration — pure computed values.', output: '44 H2 sections, chunked and embedded for RAG' },
  A3_chart_facts:     { full_name: 'Chart Facts',             description: 'Atomic facts table. Every computed value as a queryable row with stable fact_id.', output: '~2,000-5,000 chart_facts rows per ayanamsha' },
  A4_panchanga:       { full_name: 'Panchanga',               description: 'Birth-day five-limbed almanac: tithi, vara, nakshatra, yoga, karana + full enrichment.', output: 'Panchanga row with Tara/Chandra bala, Choghadiya' },
  A5_sensitive_points: { full_name: 'Sensitive Points',        description: 'Upagrahas, special lagnas, Sahams, Arudhas, Jaimini karakas, midpoints.', output: '~150 sensitive point rows' },
  A6_vargas:          { full_name: 'Divisional Charts',       description: '30+ Parashari, supplementary, and Nadi divisional charts.', output: 'Per-varga lagna + 9 grahas, D1 through D2700' },
  A7_dashas:          { full_name: 'Dasha Systems',           description: '32 dasha systems: Vimshottari + Jaimini + Tajik. Depth: Sookshma.', output: 'Dasha timeline with current period at birth' },
  A8_t1_structural:   { full_name: 'T1 Structural Facts',     description: 'Aspect matrix, shadbala, ashtakavarga, yoga register, vimsopaka, avasthas.', output: 'Full structural analysis rows' },
  A9_sade_sati:       { full_name: 'Sade Sati Cycles',        description: 'Saturn–Moon natal relationship → all 7.5-year windows past+future with intensity.', output: 'Sade Sati period table' },
  A10_msr:            { full_name: 'Multi-System Register',   description: 'Every observable signal as a row. 800–1,500 signals. No threshold drop.', output: 'MSR rows with computed_salience scores' },
  A11_cdlm:           { full_name: 'Cross-Domain Linkage',    description: '9×9 domain matrix with computable shared-factor counts.', output: 'CDLM matrix' },
  A12_cgm:            { full_name: 'Chart Graph Model',       description: 'Nodes (grahas/houses/signs) + weighted structural edges.', output: 'Graph nodes + edges' },
  A13_rm:             { full_name: 'Resonance Map',           description: 'Weakest grahas → remedy candidates from classical library.', output: 'Spoke-structure RM' },
  A14_ucn_digest:     { full_name: 'UCN Digest',              description: 'Top-K signals by salience + dominant/weakest grahas + current dasha context.', output: 'Computed UCN signature' },
}

export default function AssetDetailPanel({ asset, onClose, isOpen }: AssetDetailPanelProps) {
  if (!isOpen || !asset) return null

  const desc = ASSET_DESCRIPTIONS[asset.asset_id]
  const timeElapsed = asset.started_at && asset.finished_at
    ? ((new Date(asset.finished_at).getTime() - new Date(asset.started_at).getTime()) / 1000).toFixed(1) + 's'
    : null

  return (
    <div
      className="fixed right-0 top-0 h-full w-80 bg-slate-900 border-l border-slate-700 shadow-2xl z-50 overflow-y-auto"
      data-testid="asset-detail-panel"
      data-asset-id={asset.asset_id}
    >
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b border-slate-700">
        <h2 className="font-semibold text-white text-sm">{desc?.full_name ?? asset.asset_label}</h2>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white text-xl leading-none"
          data-testid="detail-panel-close"
        >
          ×
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Status */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Status</span>
          <span className={`text-sm font-medium capitalize ${
            asset.state === 'complete' ? 'text-green-400' :
            asset.state === 'failed' ? 'text-red-400' :
            asset.state === 'running' ? 'text-blue-400' : 'text-slate-400'
          }`}>{asset.state}</span>
        </div>

        {/* Description */}
        {desc && (
          <div>
            <p className="text-xs text-slate-400 mb-1">Description</p>
            <p className="text-sm text-slate-300">{desc.description}</p>
          </div>
        )}

        {/* Output type */}
        {desc && (
          <div>
            <p className="text-xs text-slate-400 mb-1">Output</p>
            <p className="text-sm text-slate-300">{desc.output}</p>
          </div>
        )}

        {/* Metrics */}
        {asset.rows_written !== undefined && (
          <div>
            <p className="text-xs text-slate-400 mb-1">Rows Written</p>
            <p className="text-sm text-green-300 font-mono">{asset.rows_written.toLocaleString()}</p>
          </div>
        )}

        {timeElapsed && (
          <div>
            <p className="text-xs text-slate-400 mb-1">Duration</p>
            <p className="text-sm text-slate-300 font-mono">{timeElapsed}</p>
          </div>
        )}

        {/* Ayanamsha progress */}
        {asset.ayanamshas_total && asset.ayanamshas_total.length > 0 && (
          <div>
            <p className="text-xs text-slate-400 mb-2">Ayanamshas</p>
            <div className="space-y-1">
              {asset.ayanamshas_total.map(a => (
                <div key={a} className="flex items-center gap-2 text-xs">
                  <span className={`w-2 h-2 rounded-full ${
                    asset.ayanamshas_complete?.includes(a) ? 'bg-green-400' : 'bg-slate-600'
                  }`} />
                  <span className="text-slate-300 capitalize">{a.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error (L-7: Copy button + null-error fallback message) */}
        {asset.state === 'failed' && asset.error && (
          <div className="bg-red-900/30 rounded p-3">
            <p className="text-xs text-red-400 mb-1">Error</p>
            <div className="relative">
              <pre className="font-mono break-all text-xs text-red-300 whitespace-pre-wrap pr-14">
                {asset.error}
              </pre>
              <button
                onClick={() => navigator.clipboard.writeText(asset.error!)}
                className="absolute top-0 right-0 text-xs text-red-400 hover:text-red-200 px-2 py-1 rounded bg-red-900/40 hover:bg-red-900/70 transition-colors"
                title="Copy error to clipboard"
              >
                Copy
              </button>
            </div>
          </div>
        )}
        {asset.state === 'failed' && !asset.error && (
          <div className="bg-red-900/30 rounded p-3">
            <p className="text-xs text-red-400 italic">No error details available — check orchestrator logs.</p>
          </div>
        )}
      </div>
    </div>
  )
}
