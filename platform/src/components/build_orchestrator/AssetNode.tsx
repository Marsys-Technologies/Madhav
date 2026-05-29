'use client'

export type AssetState = 'pending' | 'running' | 'complete' | 'failed' | 'cancelled' | 'skipped'

export interface AssetNodeData {
  asset_id: string       // e.g. 'A3_chart_facts'
  asset_label: string    // e.g. 'Chart Facts'
  state: AssetState
  rows_written?: number
  error?: string
  started_at?: string
  finished_at?: string
  ayanamshas_complete?: string[]  // which ayanamshas finished
  ayanamshas_total?: string[]
}

interface AssetNodeProps {
  data: AssetNodeData
  onClick?: (data: AssetNodeData) => void
  compact?: boolean  // compact=true for wheel overlay nodes, false for list view
}

const STATE_CONFIG: Record<AssetState, { color: string; icon: string; label: string }> = {
  pending:   { color: 'text-gray-400 border-gray-600',     icon: '○', label: 'Pending' },
  running:   { color: 'text-blue-400 border-blue-500',     icon: '◉', label: 'Building' },
  complete:  { color: 'text-green-400 border-green-600',   icon: '✓', label: 'Complete' },
  failed:    { color: 'text-red-400 border-red-600',       icon: '✗', label: 'Failed' },
  cancelled: { color: 'text-yellow-400 border-yellow-600', icon: '⊘', label: 'Cancelled' },
  skipped:   { color: 'text-gray-500 border-gray-700',     icon: '—', label: 'Skipped' },
}

// Short name mapping for compact display
const ASSET_SHORT: Record<string, string> = {
  A1_engine:          'ENG',
  A2_forensic_render: 'FOR',
  A3_chart_facts:     'CF',
  A4_panchanga:       'PAN',
  A5_sensitive_points:'SP',
  A6_vargas:          'VAR',
  A7_dashas:          'DAS',
  A8_t1_structural:   'T1',
  A9_sade_sati:       'SS',
  A10_msr:            'MSR',
  A11_cdlm:           'CDL',
  A12_cgm:            'CGM',
  A13_rm:             'RM',
  A14_ucn_digest:     'UCN',
}

export default function AssetNode({ data, onClick, compact = false }: AssetNodeProps) {
  const config = STATE_CONFIG[data.state]
  const shortName = ASSET_SHORT[data.asset_id] ?? data.asset_id.slice(0, 3).toUpperCase()

  if (compact) {
    return (
      <button
        onClick={() => onClick?.(data)}
        data-testid={`asset-node-${data.asset_id}`}
        data-state={data.state}
        className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-mono
          transition-all duration-300 ${config.color}
          ${data.state === 'running' ? 'animate-pulse' : ''}
        `}
        title={`${data.asset_label}: ${config.label}`}
      >
        {shortName}
      </button>
    )
  }

  return (
    <div
      onClick={() => onClick?.(data)}
      data-testid={`asset-node-${data.asset_id}`}
      data-state={data.state}
      className={`border rounded-lg p-3 cursor-pointer hover:opacity-80 transition-all
        ${config.color} ${data.state === 'running' ? 'animate-pulse' : ''}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm">{data.asset_label}</span>
        <span className="text-lg" aria-label={config.label}>{config.icon}</span>
      </div>
      <div className="text-xs mt-1 opacity-70">{config.label}</div>
      {data.state === 'complete' && data.rows_written !== undefined && (
        <div className="text-xs mt-1 text-green-300">{data.rows_written.toLocaleString()} rows</div>
      )}
      {data.state === 'failed' && data.error && (
        <div className="text-xs mt-1 text-red-300 truncate" title={data.error}>{data.error}</div>
      )}
      {data.state === 'running' && data.ayanamshas_total && (
        <div className="text-xs mt-1">
          {data.ayanamshas_complete?.length ?? 0}/{data.ayanamshas_total.length} ayanamshas
        </div>
      )}
    </div>
  )
}
