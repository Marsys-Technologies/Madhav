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
  const [running, setRunning] = useState(false)
  const [result,  setResult]  = useState<ProbeResult | null>(null)

  async function runProbe() {
    setRunning(true)
    setResult(null)
    try {
      const res = await fetch('/api/admin/aiops/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stack, call_type: callType, role }),
      })
      setResult(await res.json() as ProbeResult)
    } catch (err) {
      setResult({
        model_id: '', stack, call_type: callType, role,
        status: 'fail', latency_ms: 0,
        input_tokens: null, output_tokens: null, output_text: '',
        finish_reason: null, cost_usd: null,
        error: err instanceof Error ? err.message : 'Network error',
      })
    } finally {
      setRunning(false)
    }
  }

  const indicator = result
    ? result.status === 'pass'    ? { glyph: '✓', color: 'var(--status-success)', title: `Pass · ${result.latency_ms}ms` }
    : result.status === 'timeout' ? { glyph: '⏱', color: 'var(--status-warn)',    title: `Timeout · ${result.latency_ms}ms` }
    :                               { glyph: '✗', color: 'var(--status-halt)',     title: result.error ?? 'Failed' }
    : null

  return (
    <div className="mt-1 flex items-center gap-2">
      <button
        type="button"
        onClick={runProbe}
        disabled={running}
        className="rounded border border-border px-2 py-0.5 text-[10px] text-muted-foreground hover:border-primary hover:text-primary disabled:opacity-50"
      >
        {running ? 'Running…' : 'Test'}
      </button>

      {indicator && (
        <span
          className="text-sm font-semibold leading-none"
          style={{ color: indicator.color }}
          title={indicator.title}
          aria-label={indicator.title}
        >
          {indicator.glyph}
        </span>
      )}
    </div>
  )
}
