'use client'

import { useState } from 'react'
import type { CallType, ModelStack } from '@/lib/models/registry'
import { CALL_TYPE_SPECS } from '@/lib/aiops/specs/call_type_specs'
import { ModelDropdown } from './ModelDropdown'
import { TestProbeInline } from './TestProbeInline'
import { ParamOverrideRow } from './ParamOverrideRow'

type ParamName = 'max_output_tokens' | 'temperature' | 'thinkingBudget' | 'timeout_ms'

interface RoutingState {
  primary:  string
  fallback: string
}

interface ParamValues {
  max_output_tokens: { current: number | string | null; default: number | string }
  temperature:       { current: number | string | null; default: number | string }
  thinkingBudget:    { current: number | string | null; default: number | string }
  timeout_ms:        { current: number | string | null; default: number | string }
}

interface InteractiveCallTypeRowProps {
  stack:       ModelStack
  callType:    CallType
  initialPrimary:  string
  initialFallback: string
}

const DEFAULT_PARAMS: ParamValues = {
  max_output_tokens: { current: null, default: 4096 },
  temperature:       { current: null, default: 1.0 },
  thinkingBudget:    { current: null, default: 0 },
  timeout_ms:        { current: null, default: 30000 },
}

export function InteractiveCallTypeRow({ stack, callType, initialPrimary, initialFallback }: InteractiveCallTypeRowProps) {
  const [routing, setRouting] = useState<RoutingState>({ primary: initialPrimary, fallback: initialFallback })
  const [params,  setParams]  = useState<ParamValues>(DEFAULT_PARAMS)
  const [saving,  setSaving]  = useState(false)

  const spec = CALL_TYPE_SPECS[callType]

  async function saveRouting(updated: Partial<RoutingState>) {
    const next = { ...routing, ...updated }
    setRouting(next)
    setSaving(true)
    try {
      await fetch(`/api/admin/aiops/routing/${stack}/${callType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ primary_model: next.primary, fallback_model: next.fallback }),
      })
    } catch { /* silently fail — state already updated optimistically */ }
    setSaving(false)
  }

  function handleParamUpdate(paramName: ParamName, value: number | string | null) {
    setParams(p => ({ ...p, [paramName]: { ...p[paramName], current: value } }))
  }

  return (
    <div className="border-b border-border py-3 last:border-0">
      <div className="grid grid-cols-[160px_1fr_1fr_auto] items-start gap-x-3">
        {/* Label */}
        <div>
          <p className="text-sm font-medium text-foreground">{callType}</p>
          {spec.notes && <p className="mt-0.5 text-xs text-muted-foreground">{spec.notes}</p>}
          {saving && <span className="text-[10px] text-muted-foreground">saving…</span>}
        </div>

        {/* Primary */}
        <div>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Primary</span>
          <ModelDropdown
            stack={stack}
            callType={callType}
            role="primary"
            value={routing.primary}
            onChange={v => saveRouting({ primary: v })}
          />
          <TestProbeInline stack={stack} callType={callType} role="primary" />
        </div>

        {/* Fallback */}
        <div>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Fallback</span>
          <ModelDropdown
            stack={stack}
            callType={callType}
            role="fallback"
            value={routing.fallback}
            onChange={v => saveRouting({ fallback: v })}
          />
          <TestProbeInline stack={stack} callType={callType} role="fallback" />
        </div>

        {/* Empty 4th col placeholder */}
        <div />
      </div>

      {/* Advanced params */}
      <ParamOverrideRow
        stack={stack}
        callType={callType}
        paramValues={params}
        onUpdate={handleParamUpdate}
      />
    </div>
  )
}
