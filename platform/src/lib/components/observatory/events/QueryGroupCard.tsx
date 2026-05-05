'use client'

import * as React from 'react'
import { colorForStage } from '../charts/utils'

export type GroupedRow = {
  conversation_id: string | null
  call_count: string
  total_cost_usd: string | null
  total_input_tokens: string | null
  total_output_tokens: string | null
  started_at: string | null
  finished_at: string | null
  stages: string[]
}

interface QueryGroupCardProps {
  row: GroupedRow
}

export function QueryGroupCard({ row }: QueryGroupCardProps): React.ReactElement {
  return (
    <div className="group flex items-center gap-4 rounded-lg border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)] px-4 py-3 transition-colors hover:bg-[rgba(212,175,55,0.04)] hover:border-[rgba(212,175,55,0.18)]">
      {/* Query ID */}
      <div className="min-w-0 flex-1">
        <span
          className="font-mono text-[10px] text-[rgba(212,175,55,0.50)]"
          title={row.conversation_id ?? '—'}
        >
          {row.conversation_id ? row.conversation_id.slice(0, 8) + '…' : '—'}
        </span>
      </div>

      {/* Cost */}
      <span className="tabular-nums text-sm font-semibold text-[#fce29a]">
        {row.total_cost_usd != null ? `$${Number(row.total_cost_usd).toFixed(6)}` : '—'}
      </span>

      {/* Calls badge */}
      <span className="rounded-full border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.08)] px-2 py-0.5 text-[10px] font-medium text-[#d4af37]">
        {row.call_count} calls
      </span>

      {/* Token split */}
      <span className="shrink-0 font-mono text-[10px] text-[rgba(212,175,55,0.45)]">
        {row.total_input_tokens ?? '—'} / {row.total_output_tokens ?? '—'}
      </span>

      {/* Stage mini-badges */}
      <div className="flex items-center gap-1">
        {(row.stages ?? []).slice(0, 4).map((stage) => (
          <span
            key={stage}
            className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
            style={{
              backgroundColor: `${colorForStage(stage)}22`,
              color: colorForStage(stage),
              border: `1px solid ${colorForStage(stage)}44`,
            }}
          >
            {stage}
          </span>
        ))}
        {(row.stages ?? []).length > 4 && (
          <span className="text-[9px] text-[rgba(212,175,55,0.35)]">
            +{row.stages.length - 4}
          </span>
        )}
      </div>

      {/* Timestamp */}
      <span className="shrink-0 font-mono text-[10px] text-[rgba(212,175,55,0.40)]">
        {row.started_at
          ? new Date(row.started_at).toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })
          : '—'}
      </span>

      {/* Expand chevron */}
      <span className="shrink-0 text-[rgba(212,175,55,0.25)]" aria-hidden="true">
        ›
      </span>
    </div>
  )
}
