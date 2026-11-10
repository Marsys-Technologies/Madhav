'use client'

import { useState } from 'react'
import type { TraceDocument } from '@/lib/admin/trace_assembler'

interface QueryHeaderStripProps {
  trace: TraceDocument
}

const HEALTH_STYLES: Record<TraceDocument['query']['health'], string> = {
  HEALTHY: 'bg-emerald-400/10 border border-emerald-400/30 text-emerald-400',
  DEGRADED: 'bg-amber-400/10 border border-amber-400/30 text-amber-400',
  FAILED: 'bg-red-400/10 border border-red-400/30 text-red-400',
  UNKNOWN: 'bg-zinc-400/10 border border-zinc-400/30 text-zinc-400',
}

function formatCost(usd: number | null) {
  if (usd === null) return '—'
  return `$${usd.toFixed(4)}`
}

function formatLatency(ms: number | null) {
  if (ms === null) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function QueryHeaderStrip({ trace }: QueryHeaderStripProps) {
  const [copied, setCopied] = useState(false)
  const q = trace.query

  const queryText = q.text ?? ''
  const truncated = queryText.length > 80 ? queryText.slice(0, 80) + '…' : queryText

  function handleCopyId() {
    void navigator.clipboard.writeText(q.id).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div
      data-testid="query-header-strip"
      className="flex min-h-14 flex-wrap items-center gap-x-3 gap-y-2 border-b border-[rgba(212,175,55,0.1)] px-4 py-2"
    >
      {/* Left: query text */}
      <p
        className="min-w-0 basis-full truncate text-sm text-zinc-200 sm:basis-auto sm:max-w-[50%]"
        title={queryText}
      >
        {truncated || <span className="text-zinc-500 italic">no query text</span>}
      </p>

      {/* Center: pills */}
      <div className="flex flex-1 flex-wrap items-center gap-2">
        {q.type && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-[rgba(212,175,55,0.08)] border border-[rgba(212,175,55,0.2)] text-[#d4af37]">
            {q.type}
            {q.confidence != null ? ` · ${q.confidence.toFixed(2)}` : ''}
          </span>
        )}
        <span className="text-xs text-zinc-400">{formatLatency(q.total_ms)}</span>
        <span className="text-xs text-zinc-400">{formatCost(q.total_cost_usd)}</span>
      </div>

      {/* Right: health badge and query id */}
      <div className="flex items-center gap-3 ml-auto">
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-semibold ${HEALTH_STYLES[q.health]}`}
          data-testid={`health-badge-${q.health}`}
        >
          {q.health}
        </span>

        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono text-zinc-500 select-all">{q.id.slice(0, 8)}…</span>
          <button
            onClick={handleCopyId}
            type="button"
            aria-label="Copy full query ID"
            className="min-h-11 min-w-11 text-sm text-zinc-300 hover:text-zinc-100"
            title="Copy full query ID"
          >
            {copied ? '✓' : '⎘'}
          </button>
        </div>

      </div>
    </div>
  )
}
