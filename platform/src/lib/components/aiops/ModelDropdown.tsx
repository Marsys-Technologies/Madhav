'use client'

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import type { CallType, ModelStack, Provider } from '@/lib/models/registry'
import { MODELS } from '@/lib/models/registry'
import { filterCatalogForCallType } from '@/lib/aiops/specs/call_type_specs'
import type { CatalogEntry, CatalogFetchResult } from '@/lib/aiops/catalog/types'
import { HealthPip } from './HealthPip'
import { PROVIDER_DISPLAY, displayOf } from './displayNames'

// Synchronous fallback map — avoids flash of raw model IDs before catalog API responds
const STATIC_MODEL_MAP = new Map(
  MODELS.map(m => [m.id, { label: m.label, context_window: m.maxInputTokens ?? null, provider: m.provider }]),
)

interface ModelDropdownProps {
  stack:    ModelStack
  callType: CallType
  role:     'primary' | 'fallback'
  value:    string
  onChange: (modelId: string) => void
}

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
    marsys:    'google',
  }
  return [map[stack]]
}

function fmtCtx(n: number | null): string {
  if (!n) return ''
  if (n >= 1_000_000) return `${Math.round(n / 1_000_000)}M`
  return `${Math.round(n / 1_000)}K`
}

function displayLabel(e: { label: string; context_window: number | null; provider?: string } | undefined, fallback: string): string {
  if (!e) return fallback
  const ctx = fmtCtx(e.context_window)
  const prov = e.provider ? displayOf(PROVIDER_DISPLAY, e.provider) : null
  const parts: string[] = [e.label]
  if (ctx) parts.push(ctx)
  if (prov) parts.push(prov)
  return parts.join(' · ')
}

export function ModelDropdown({ stack, callType, value, onChange }: ModelDropdownProps) {
  const [allEntries, setAllEntries] = useState<CatalogEntry[]>([])
  const [entries,    setEntries]    = useState<CatalogEntry[]>([])
  const [loading,    setLoading]    = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [open,       setOpen]       = useState(false)
  const [query,      setQuery]      = useState('')
  const searchRef = useRef<HTMLInputElement | null>(null)

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
      const raw: CatalogEntry[] = results.flatMap(r => r.models ?? [])
      const seen = new Set<string>()
      const deduped = raw.filter(e => {
        const k = `${e.provider}|${e.model_id}`
        if (seen.has(k)) return false
        seen.add(k)
        return true
      })
      setAllEntries(deduped)
      setEntries(filterCatalogForCallType(deduped, callType))
    } catch {
      // silently — entries stays empty
    } finally {
      setLoading(false)
    }
  }, [stack, callType])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { loadCatalog() }, [loadCatalog])

  useEffect(() => {
    if (open) {
      const id = window.setTimeout(() => searchRef.current?.focus(), 0)
      return () => window.clearTimeout(id)
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setQuery('')
    }
  }, [open])

  // allEntries used for trigger label so a selected model outside the filtered list still resolves
  const allEntryMap = useMemo(() => new Map(allEntries.map(e => [e.model_id, e])), [allEntries])

  const ready   = entries.filter(e => !e.metadata_pending)
  const pending = entries.filter(e => e.metadata_pending)
  const filtered = useMemo(() => {
    const combined = [...ready, ...pending]
    if (!query.trim()) return combined
    const q = query.trim().toLowerCase()
    return combined.filter(e =>
      e.model_id.toLowerCase().includes(q) ||
      e.label.toLowerCase().includes(q) ||
      e.provider.toLowerCase().includes(q),
    )
  }, [ready, pending, query])

  const selectedEntry = allEntryMap.get(value)
  // Use catalog entry first; fall back to static registry map for zero-latency display before API responds
  const triggerLabel = displayLabel(selectedEntry ?? STATIC_MODEL_MAP.get(value), value)

  return (
    <div className="relative">
      {/* Trigger */}
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          title={value || undefined}
          className="flex min-w-0 flex-1 items-center justify-between rounded border border-border bg-card px-2 py-1 text-xs text-foreground hover:border-muted-foreground/50"
        >
          <span className="truncate">{triggerLabel || '—'}</span>
          <span className="ml-1 shrink-0 text-muted-foreground">{open ? '▲' : '▼'}</span>
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

      {/* Dropdown list */}
      {open && (
        <div className="absolute z-50 mt-1 min-w-[440px] overflow-hidden rounded border border-border bg-popover shadow-md">
          <div className="border-b border-border bg-popover p-1.5">
            <input
              ref={searchRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Escape') setOpen(false) }}
              placeholder="Filter by name, provider, or model ID…"
              className="w-full rounded border border-border bg-input/40 px-2 py-1 text-xs text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-1 focus:ring-[var(--brand-gold)]"
            />
          </div>
          <div className="max-h-64 overflow-y-auto">
            {loading ? (
              <p className="p-2 text-xs text-muted-foreground">Loading…</p>
            ) : filtered.length === 0 ? (
              <p className="p-2 text-xs text-muted-foreground">
                {query ? `No models match "${query}"` : 'No models available'}
              </p>
            ) : (
              filtered.map(e => (
                <button
                  key={`${e.provider}-${e.model_id}`}
                  type="button"
                  title={e.model_id}
                  onClick={() => { onChange(e.model_id); setOpen(false) }}
                  className={[
                    'flex w-full items-center justify-between px-3 py-2 text-left text-xs hover:bg-[rgba(var(--brand-gold-rgb),0.08)]',
                    e.model_id === value ? 'bg-[rgba(var(--brand-gold-rgb),0.10)] font-semibold' : '',
                    e.metadata_pending ? 'opacity-60' : '',
                  ].join(' ')}
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <HealthPip modelId={e.model_id} />
                    <span>{e.label}</span>
                    {e.context_window && (
                      <span className="text-[10px] text-muted-foreground">
                        {fmtCtx(e.context_window)}
                      </span>
                    )}
                  </span>
                  <span className="ml-3 shrink-0 text-[10px] text-muted-foreground">
                    {e.metadata_pending ? '[pending]' : displayOf(PROVIDER_DISPLAY, e.provider)}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
