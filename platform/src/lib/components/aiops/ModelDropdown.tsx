'use client'

import { useState, useEffect, useCallback } from 'react'
import type { CallType, ModelStack, Provider } from '@/lib/models/registry'
import { filterCatalogForCallType, CALL_TYPE_SPECS } from '@/lib/aiops/specs/call_type_specs'
import type { CatalogEntry, CatalogFetchResult } from '@/lib/aiops/catalog/types'

interface ModelDropdownProps {
  stack:    ModelStack
  callType: CallType
  role:     'primary' | 'fallback'
  value:    string
  onChange: (modelId: string) => void
}

// Providers to fetch depending on call type / stack
function providersFor(stack: ModelStack, callType: CallType): Provider[] {
  const crossStack = ['eval_judge', 'eval_generator', 'smoke_synth', 'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5']
  if (stack === 'marsys' || crossStack.includes(callType)) {
    return ['nvidia', 'google', 'deepseek', 'openai', 'anthropic']
  }
  const map: Record<ModelStack, Provider> = {
    gemini:    'google',
    nim:       'nvidia',
    deepseek:  'deepseek',
    gpt:       'openai',
    anthropic: 'anthropic',
    marsys:    'google',  // fallback; overridden above for marsys
  }
  return [map[stack]]
}

export function ModelDropdown({ stack, callType, role, value, onChange }: ModelDropdownProps) {
  const [entries, setEntries]     = useState<CatalogEntry[]>([])
  const [loading, setLoading]     = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [open, setOpen]           = useState(false)

  const spec = CALL_TYPE_SPECS[callType]

  const loadCatalog = useCallback(async (forceRefresh = false) => {
    const providers = providersFor(stack, callType)
    try {
      if (forceRefresh) {
        setRefreshing(true)
        await Promise.all(
          providers.map(p => fetch(`/api/admin/aiops/catalog/refresh/${p}`, { method: 'POST' })),
        )
        setRefreshing(false)
      }
      const results = await Promise.all(
        providers.map(p => fetch(`/api/admin/aiops/catalog/${p}`).then(r => r.json() as Promise<CatalogFetchResult>)),
      )
      const all: CatalogEntry[] = results.flatMap(r => r.models ?? [])
      const filtered = filterCatalogForCallType(all, callType)
      setEntries(filtered)
    } catch {
      // silently — entries stays empty, user sees empty dropdown
    } finally {
      setLoading(false)
    }
  }, [stack, callType])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { loadCatalog() }, [loadCatalog])

  const noteText = spec.notes

  // Split entries: pending at bottom, rest sorted as-is (filterCatalogForCallType sorted them)
  const ready   = entries.filter(e => !e.metadata_pending)
  const pending = entries.filter(e => e.metadata_pending)
  const all     = [...ready, ...pending]

  return (
    <div className="relative">
      {/* Trigger */}
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          className="flex min-w-0 flex-1 items-center justify-between rounded border border-border bg-card px-2 py-1 text-xs font-mono text-foreground hover:border-muted-foreground/50"
        >
          <span className="truncate">{value || '—'}</span>
          <span className="ml-1 text-muted-foreground">{open ? '▲' : '▼'}</span>
        </button>
        <button
          type="button"
          onClick={() => loadCatalog(true)}
          disabled={refreshing}
          title="Refresh catalog"
          className="shrink-0 rounded p-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          ↻
        </button>
      </div>

      {/* Spec note */}
      {noteText && (
        <p className="mt-0.5 text-[10px] text-muted-foreground">{noteText}</p>
      )}

      {/* Dropdown list */}
      {open && (
        <div className="absolute z-50 mt-1 max-h-64 w-72 overflow-y-auto rounded border border-border bg-popover shadow-md">
          {loading ? (
            <p className="p-2 text-xs text-muted-foreground">Loading…</p>
          ) : all.length === 0 ? (
            <p className="p-2 text-xs text-muted-foreground">No models available</p>
          ) : (
            all.map(e => (
              <button
                key={`${e.provider}-${e.model_id}`}
                type="button"
                onClick={() => { onChange(e.model_id); setOpen(false) }}
                className={[
                  'flex w-full items-center justify-between px-3 py-1.5 text-left text-xs hover:bg-accent',
                  e.model_id === value ? 'bg-primary/10 font-semibold' : '',
                  e.metadata_pending ? 'opacity-60' : '',
                ].join(' ')}
              >
                <span className="truncate font-mono">{e.model_id}</span>
                <span className="ml-2 shrink-0 text-[10px] text-muted-foreground">
                  {e.metadata_pending ? '[pending]' : e.provider}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
