'use client'

import { useState, useRef } from 'react'
import type { CallType, ModelStack } from '@/lib/models/registry'

const PARAM_NAMES = ['max_output_tokens', 'temperature', 'thinkingBudget', 'timeout_ms'] as const
type ParamName = typeof PARAM_NAMES[number]

interface ParamValue {
  current: number | string | null  // null = using default
  default: number | string
}

interface ParamOverrideRowProps {
  stack:          ModelStack
  callType:       CallType
  paramValues:    Record<ParamName, ParamValue>
  onUpdate:       (paramName: ParamName, value: number | string | null) => void
}

export function ParamOverrideRow({ stack, callType, paramValues, onUpdate }: ParamOverrideRowProps) {
  const [expanded, setExpanded] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  async function setParam(paramName: ParamName, raw: string) {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      const numVal = parseFloat(raw)
      const value = isNaN(numVal) ? raw : numVal
      try {
        await fetch(`/api/admin/aiops/params/${stack}/${callType}/${paramName}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ param_value: value }),
        })
        onUpdate(paramName, value)
      } catch { /* silently fail — parent shows stale state */ }
    }, 500)
  }

  async function resetParam(paramName: ParamName) {
    try {
      await fetch(`/api/admin/aiops/params/${stack}/${callType}/${paramName}`, { method: 'DELETE' })
      onUpdate(paramName, null)
    } catch { /* silently fail */ }
  }

  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setExpanded(e => !e)}
        className="text-[10px] text-muted-foreground hover:text-foreground"
      >
        {expanded ? '▲ Hide params' : '▼ Advanced params'}
      </button>

      {expanded && (
        <div className="mt-2 rounded border border-border bg-muted/30 p-2">
          {PARAM_NAMES.map(paramName => {
            const pv = paramValues[paramName]
            const isOverridden = pv.current !== null
            return (
              <div key={paramName} className="mb-2 flex items-center gap-2 last:mb-0">
                <span className="w-36 shrink-0 text-[10px] font-mono text-muted-foreground">{paramName}</span>
                <span className="w-16 shrink-0 text-[10px] text-muted-foreground">
                  {isOverridden ? String(pv.current) : `(${String(pv.default)})`}
                </span>
                <input
                  type="text"
                  defaultValue={isOverridden ? String(pv.current) : ''}
                  placeholder={String(pv.default)}
                  onChange={e => setParam(paramName, e.target.value)}
                  className="w-24 rounded border border-border bg-card px-1.5 py-0.5 text-[10px] font-mono text-foreground"
                />
                {isOverridden && (
                  <button
                    type="button"
                    onClick={() => resetParam(paramName)}
                    className="text-[10px] text-destructive hover:underline"
                  >
                    reset
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
