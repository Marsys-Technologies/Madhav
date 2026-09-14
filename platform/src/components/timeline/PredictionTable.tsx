'use client'

import { useState } from 'react'
import type { LELPrediction } from '@/lib/lel/parser'
import { cn } from '@/lib/utils'

type SortKey = 'made_at' | 'confidence' | 'status'

const STATUS_LABELS: Record<LELPrediction['status'], string> = {
  open: 'Open',
  observed_confirmed: 'Confirmed',
  observed_refuted: 'Refuted',
  expired: 'Expired',
}

const STATUS_COLORS: Record<LELPrediction['status'], string> = {
  open: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  observed_confirmed: 'bg-green-500/20 text-green-300 border-green-500/30',
  observed_refuted: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
  expired: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
}

interface PredictionTableProps {
  predictions: LELPrediction[]
  canWrite: boolean
  chartId: string
}

function SortHeader({
  k,
  label,
  sortKey,
  sortAsc,
  onSort,
}: {
  k: SortKey
  label: string
  sortKey: SortKey
  sortAsc: boolean
  onSort: (key: SortKey) => void
}) {
  return (
    <th
      className="cursor-pointer select-none whitespace-nowrap px-3 py-2 text-left text-xs font-medium text-muted-foreground hover:text-foreground"
      onClick={() => onSort(k)}
    >
      {label}
      {sortKey === k && <span className="ml-1 opacity-60">{sortAsc ? '↑' : '↓'}</span>}
    </th>
  )
}

export function PredictionTable({ predictions, canWrite, chartId }: PredictionTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('made_at')
  const [sortAsc, setSortAsc] = useState(false)

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  const sorted = [...predictions].sort((a, b) => {
    let cmp = 0
    if (sortKey === 'made_at') cmp = a.made_at.localeCompare(b.made_at)
    else if (sortKey === 'confidence') cmp = a.confidence - b.confidence
    else if (sortKey === 'status') cmp = a.status.localeCompare(b.status)
    return sortAsc ? cmp : -cmp
  })

  if (predictions.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
        <p className="text-sm">No predictions logged yet.</p>
        {canWrite && (
          <p className="text-xs opacity-70">
            Use &ldquo;Log prediction&rdquo; above to record a time-indexed prospective prediction.
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border/50">
      <table className="w-full text-sm">
        <thead className="bg-muted/20">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">ID</th>
            <SortHeader k="made_at" label="Made at" sortKey={sortKey} sortAsc={sortAsc} onSort={toggleSort} />
            <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Horizon</th>
            <SortHeader k="confidence" label="Confidence" sortKey={sortKey} sortAsc={sortAsc} onSort={toggleSort} />
            <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Body</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Falsifier</th>
            <SortHeader k="status" label="Status" sortKey={sortKey} sortAsc={sortAsc} onSort={toggleSort} />
            {canWrite && (
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Action</th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30">
          {sorted.map(pred => (
            <PredictionRow
              key={pred.id}
              pred={pred}
              canWrite={canWrite}
              chartId={chartId}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PredictionRow({
  pred,
  canWrite,
  chartId: _chartId,
}: {
  pred: LELPrediction
  canWrite: boolean
  chartId: string
}) {
  const statusColor = STATUS_COLORS[pred.status]

  return (
    <tr className="hover:bg-muted/10">
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{pred.id}</td>
      <td className="px-3 py-2 font-mono text-xs">{pred.made_at}</td>
      <td className="px-3 py-2 text-xs">{pred.horizon}</td>
      <td className="px-3 py-2 text-xs">
        <div className="flex items-center gap-1.5">
          <div
            className="h-1.5 w-1.5 rounded-full bg-amber-400"
            style={{ opacity: pred.confidence }}
          />
          {Math.round(pred.confidence * 100)}%
        </div>
      </td>
      <td className="max-w-xs px-3 py-2 text-xs text-foreground/80">
        <span className="line-clamp-2">{pred.body}</span>
      </td>
      <td className="max-w-[200px] px-3 py-2 text-xs text-muted-foreground">
        <span className="line-clamp-1">{pred.falsifier}</span>
      </td>
      <td className="px-3 py-2">
        <span
          className={cn(
            'rounded border px-1.5 py-0.5 text-xs font-medium',
            statusColor
          )}
        >
          {STATUS_LABELS[pred.status]}
        </span>
        {pred.outcome_logged_at && (
          <div className="mt-0.5 text-xs text-muted-foreground/60">
            {pred.outcome_logged_at}
          </div>
        )}
      </td>
      {canWrite && (
        <td className="px-3 py-2">
          {pred.status === 'open' && (
            <MarkOutcomeButton predId={pred.id} />
          )}
        </td>
      )}
    </tr>
  )
}

function MarkOutcomeButton({ predId: _predId }: { predId: string }) {
  // Outcome marking is wired through LogPredictionDialog on full click
  // This button is a placeholder that signals intent; the dialog handles the API call
  return (
    <button
      className="rounded border border-border/50 px-2 py-1 text-xs text-muted-foreground hover:border-amber-400/50 hover:text-amber-300"
      type="button"
    >
      Mark outcome
    </button>
  )
}
