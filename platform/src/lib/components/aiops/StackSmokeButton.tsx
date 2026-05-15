'use client'

import { useState } from 'react'
import type { ModelStack } from '@/lib/models/registry'
import type { ProbeResult } from '@/lib/aiops/probe/types'
import { STACK_DISPLAY, CALL_TYPE_DISPLAY, ROLE_DISPLAY, displayOf } from './displayNames'
import type { CallType } from '@/lib/models/registry'

interface SmokeResponse {
  stack:    ModelStack
  results:  ProbeResult[]
  all_pass: boolean
  summary:  { total: number; pass: number; fail: number }
}

interface StackSmokeButtonProps {
  stack: ModelStack
}

export function StackSmokeButton({ stack }: StackSmokeButtonProps) {
  const [running,  setRunning]  = useState(false)
  const [response, setResponse] = useState<SmokeResponse | null>(null)
  const [error,    setError]    = useState<string | null>(null)

  async function runSmoke() {
    setRunning(true)
    setResponse(null)
    setError(null)
    try {
      const res = await fetch(`/api/admin/aiops/smoke/${stack}`, { method: 'POST' })
      const data = await res.json() as SmokeResponse
      setResponse(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="my-3">
      <button
        type="button"
        onClick={runSmoke}
        disabled={running}
        className="rounded border border-border px-3 py-1 text-xs text-muted-foreground hover:border-primary hover:text-primary disabled:opacity-50"
      >
        {running ? 'Running smoke test…' : `Run ${STACK_DISPLAY[stack]} smoke test`}
      </button>

      {error && (
        <p className="mt-1 text-xs text-destructive">{error}</p>
      )}

      {response && (
        <div className="mt-2">
          <p className={['text-xs font-semibold', response.all_pass ? 'text-green-600' : 'text-red-600'].join(' ')}>
            {response.summary.pass}/{response.summary.total} PASS
          </p>
          <div className="mt-1 grid grid-cols-2 gap-1 sm:grid-cols-3 lg:grid-cols-4">
            {response.results.map((r, i) => (
              <div
                key={i}
                title={r.error ?? r.output_text}
                className={[
                  'rounded border px-2 py-1 text-[10px]',
                  r.status === 'pass'
                    ? 'border-green-500/30 bg-green-500/5 text-green-700'
                    : 'border-red-500/30 bg-red-500/5 text-red-700',
                ].join(' ')}
              >
                <p className="truncate">{displayOf(CALL_TYPE_DISPLAY, r.call_type as CallType)}</p>
                <p className="text-muted-foreground">{ROLE_DISPLAY[r.role as 'primary' | 'fallback'] ?? r.role} · {r.status}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
