'use client'

import { useState } from 'react'
import type { CallType, ModelStack } from '@/lib/models/registry'
import type { ProbeResult } from '@/lib/aiops/probe/types'

interface TestProbeInlineProps {
  stack:    ModelStack
  callType: CallType
  role:     'primary' | 'fallback'
}

export function TestProbeInline({ stack, callType, role }: TestProbeInlineProps) {
  const [expanded, setExpanded] = useState(false)
  const [running,  setRunning]  = useState(false)
  const [result,   setResult]   = useState<ProbeResult | null>(null)

  async function runProbe() {
    setRunning(true)
    setResult(null)
    try {
      const res = await fetch('/api/admin/aiops/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stack, call_type: callType, role }),
      })
      const data = await res.json() as ProbeResult
      setResult(data)
    } catch (err) {
      setResult({
        model_id: '',
        stack,
        call_type: callType,
        role,
        status: 'fail',
        latency_ms: 0,
        input_tokens: null,
        output_tokens: null,
        output_text: '',
        finish_reason: null,
        cost_usd: null,
        error: err instanceof Error ? err.message : 'Network error',
      })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => {
          setExpanded(true)
          runProbe()
        }}
        disabled={running}
        className="rounded border border-border px-2 py-0.5 text-[10px] text-muted-foreground hover:border-primary hover:text-primary disabled:opacity-50"
      >
        {running ? 'Running…' : 'Test'}
      </button>

      {expanded && result && (
        <div className={[
          'mt-1 rounded border p-2 text-[10px]',
          result.status === 'pass'
            ? 'border-green-500/40 bg-green-500/5 text-green-700 dark:text-green-400'
            : 'border-red-500/40 bg-red-500/5 text-red-700 dark:text-red-400',
        ].join(' ')}>
          <div className="flex items-center gap-2 font-semibold">
            <span>{result.status === 'pass' ? '✓ PASS' : result.status === 'timeout' ? '⏱ TIMEOUT' : '✗ FAIL'}</span>
            {result.latency_ms > 0 && <span className="font-normal text-muted-foreground">{result.latency_ms}ms</span>}
            {result.input_tokens !== null && (
              <span className="font-normal text-muted-foreground">↑{result.input_tokens} ↓{result.output_tokens}</span>
            )}
            {result.cost_usd !== null && (
              <span className="font-normal text-muted-foreground">${result.cost_usd.toFixed(4)}</span>
            )}
          </div>
          {result.output_text && (
            <p className="mt-1 font-mono text-[9px] text-foreground/70 line-clamp-3">{result.output_text}</p>
          )}
          {result.error && <p className="mt-1 font-mono">{result.error}</p>}
        </div>
      )}
    </div>
  )
}
