'use client'

import { useState } from 'react'
import type { CallType, ModelStack } from '@/lib/models/registry'
import { CALL_TYPE_SPECS } from '@/lib/aiops/specs/call_type_specs'
import { ModelDropdown } from './ModelDropdown'
import { TestProbeInline } from './TestProbeInline'
import { ParamOverrideRow } from './ParamOverrideRow'
import { useDirtyRows, dirtyKey } from './DirtyRowsContext'
import { InfoTooltip } from './InfoTooltip'
import { CALL_TYPE_DISPLAY } from './displayNames'

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
  const { isDirty, markDirty } = useDirtyRows()

  const spec = CALL_TYPE_SPECS[callType]

  const rowDirty =
    isDirty(dirtyKey(stack, callType, 'primary')) ||
    isDirty(dirtyKey(stack, callType, 'fallback')) ||
    isDirty(dirtyKey(stack, callType, 'param'))

  async function saveRouting(updated: Partial<RoutingState>, changedRole: 'primary' | 'fallback') {
    const next = { ...routing, ...updated }
    setRouting(next)
    setSaving(true)
    try {
      await fetch(`/api/admin/aiops/routing/${stack}/${callType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ primary_model: next.primary, fallback_model: next.fallback }),
      })
      markDirty(dirtyKey(stack, callType, changedRole))
    } catch { /* silently fail — state already updated optimistically */ }
    setSaving(false)
  }

  function handleParamUpdate(paramName: ParamName, value: number | string | null) {
    setParams(p => ({ ...p, [paramName]: { ...p[paramName], current: value } }))
    markDirty(dirtyKey(stack, callType, 'param', paramName))
  }

  return (
    <div
      className={[
        'border-b border-border py-3 last:border-0 transition-shadow',
        rowDirty ? 'aiops-row-dirty pl-3 -ml-1' : '',
      ].join(' ')}
    >
      <div className="grid grid-cols-[140px_minmax(0,1fr)_minmax(0,1fr)_auto] items-start gap-x-4">
        {/* Label */}
        <div>
          <div className="flex items-center gap-1.5">
            <p className="text-sm font-medium text-foreground">{CALL_TYPE_DISPLAY[callType] ?? callType}</p>
            {spec.notes && (
              <InfoTooltip text={spec.notes} ariaLabel={`About ${CALL_TYPE_DISPLAY[callType] ?? callType}`} />
            )}
            {rowDirty && (
              <span
                aria-label="Unsaved this session"
                title="Changed this session — propagating"
                className="inline-block size-1.5 rounded-full"
                style={{ background: 'var(--brand-gold)', boxShadow: '0 0 6px var(--brand-gold)' }}
              />
            )}
          </div>
          {saving && <span className="text-[10px] text-muted-foreground">saving…</span>}
        </div>

        {/* Primary — slightly elevated surface */}
        <div className="rounded-md bg-[rgba(var(--brand-gold-rgb),0.04)] p-1.5">
          <span className="flex items-center gap-1">
            <span
              className="bt-label bt-label-upper"
              style={{ color: 'var(--brand-gold)' }}
            >
              Primary
            </span>
            {spec.notes && (
              <InfoTooltip text={spec.notes} ariaLabel="Primary requirements" />
            )}
          </span>
          <ModelDropdown
            stack={stack}
            callType={callType}
            role="primary"
            value={routing.primary}
            onChange={v => saveRouting({ primary: v }, 'primary')}
          />
          <TestProbeInline stack={stack} callType={callType} role="primary" />
        </div>

        {/* Fallback — muted */}
        <div className="p-1.5">
          <span className="flex items-center gap-1">
            <span className="bt-label bt-label-upper">Fallback</span>
            {spec.notes && (
              <InfoTooltip text={spec.notes} ariaLabel="Fallback requirements" />
            )}
          </span>
          <ModelDropdown
            stack={stack}
            callType={callType}
            role="fallback"
            value={routing.fallback}
            onChange={v => saveRouting({ fallback: v }, 'fallback')}
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
