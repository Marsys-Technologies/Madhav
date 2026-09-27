'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { AiChoice } from '@/components/ai-console/types'
import {
  buildAiChoiceOptions, selectionKey, type AiChoicesAggregateDto, type AiChoicesCliDto,
} from '../composer/model_options'

export type ConversationSelection =
  | { kind: 'default' }
  | { kind: 'explicit'; choice: AiChoice }

export type SelectionAvailability = 'ready' | 'default_required' | 'selection_broken'

export interface SelectionView {
  selection: ConversationSelection
  availability: SelectionAvailability
  label: string
  resolvedLabel: string | null
  remediation: string | null
}

export interface AiChoiceOption {
  key: string
  group: 'Provider connections' | 'Custom configurations' | 'Local CLIs' | null
  label: string
  detail?: string
  selection: ConversationSelection
  disabled: boolean
}

export interface UseAiChoicesResult {
  enabled: boolean
  legacy: boolean
  selection: ConversationSelection
  options: AiChoiceOption[]
  availability: SelectionAvailability
  loading: boolean
  mutationPending: boolean
  canSubmit: boolean
  statusMessage: string
  select: (selection: ConversationSelection) => Promise<void>
  refresh: () => void
}

const DEFAULT_SELECTION: ConversationSelection = { kind: 'default' }
const EMPTY_OPTIONS: AiChoiceOption[] = []
const DEFAULT_REQUIRED = 'Choose a default in AI Console before asking a question.'
const BROKEN = 'This AI choice is unavailable. Repair it in AI Console or choose another available option.'

class FeatureDisabled extends Error {}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (response.status === 404 && url === '/api/ai-console') throw new FeatureDisabled()
  const payload = await response.json().catch(() => null) as { error?: unknown } | null
  if (!response.ok) throw new Error(typeof payload?.error === 'string' ? payload.error : 'request_failed')
  return payload as T
}

function localView(selection: ConversationSelection, aggregate: AiChoicesAggregateDto, clis: AiChoicesCliDto): SelectionView {
  const provisional: SelectionView = { selection, availability: 'ready', label: selection.kind === 'default' ? 'Default' : '', resolvedLabel: null, remediation: null }
  const options = buildAiChoiceOptions(aggregate, clis, provisional)
  const defaultOption = options.find(option => option.key === 'default')
  if (!aggregate.defaultChoice) return { ...provisional, availability: 'default_required', remediation: DEFAULT_REQUIRED }
  if (!defaultOption || defaultOption.disabled) return { ...provisional, availability: 'selection_broken', remediation: BROKEN }
  const selected = options.find(option => option.key === selectionKey(selection))
  if (!selected || selected.disabled) return { ...provisional, availability: 'selection_broken', label: selected?.label ?? 'Unavailable AI choice', remediation: BROKEN }
  return { ...provisional, label: selection.kind === 'default' ? 'Default' : selected.label,
    resolvedLabel: selection.kind === 'default' ? defaultOption.label.replace(/^Default — /, '') : null }
}

export function useAiChoices(conversationId: string | null, enabled: boolean): UseAiChoicesResult {
  const [legacy, setLegacy] = useState(!enabled)
  const [selection, setSelection] = useState<ConversationSelection>(DEFAULT_SELECTION)
  const selectionRef = useRef<ConversationSelection>(DEFAULT_SELECTION)
  const [view, setView] = useState<SelectionView>({ selection: DEFAULT_SELECTION, availability: 'default_required', label: 'Default', resolvedLabel: null, remediation: DEFAULT_REQUIRED })
  const [options, setOptions] = useState<AiChoiceOption[]>([])
  const [loading, setLoading] = useState(enabled)
  const [mutationPending, setMutationPending] = useState(false)
  const [loadFailed, setLoadFailed] = useState(false)
  const [statusMessage, setStatusMessage] = useState(enabled ? 'Loading AI choices…' : '')
  const [loadedConversationId, setLoadedConversationId] = useState<string | null | undefined>(undefined)
  const [refreshVersion, setRefreshVersion] = useState(0)
  const aggregateRef = useRef<AiChoicesAggregateDto | null>(null)
  const clisRef = useRef<AiChoicesCliDto | null>(null)
  const initialConversationIdRef = useRef(conversationId)
  const acknowledgedConversationIdRef = useRef<string | null>(null)

  const applyView = useCallback((nextView: SelectionView, aggregate: AiChoicesAggregateDto, clis: AiChoicesCliDto) => {
    selectionRef.current = nextView.selection
    setSelection(nextView.selection)
    setView(nextView)
    setOptions(buildAiChoiceOptions(aggregate, clis, nextView))
    setStatusMessage(nextView.remediation ?? '')
  }, [])

  const persist = useCallback(async (id: string, next: ConversationSelection): Promise<SelectionView> => {
    return getJson<SelectionView>(`/api/conversations/${encodeURIComponent(id)}/ai-selection`, {
      method: 'PUT', headers: { 'content-type': 'application/json' }, body: JSON.stringify(next),
    })
  }, [])

  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    const controller = new AbortController()
    queueMicrotask(() => {
      if (cancelled) return
      setLoading(true)
      setLoadFailed(false)
      setStatusMessage('Loading AI choices…')
    })
    void (async () => {
      try {
        // The aggregate route is the feature-discovery authority: a 404 here
        // alone activates legacy behavior. Do not let an unrelated CLI-route
        // 404 silently downgrade an enabled surface.
        const aggregate = await getJson<AiChoicesAggregateDto>('/api/ai-console', { signal: controller.signal })
        const clis = await getJson<AiChoicesCliDto>('/api/ai-console/clis', { signal: controller.signal })
        if (cancelled) return
        aggregateRef.current = aggregate
        clisRef.current = clis
        setLegacy(false)

        let nextView: SelectionView
        if (!conversationId) {
          nextView = localView(selectionRef.current, aggregate, clis)
        } else if (initialConversationIdRef.current === null
          && acknowledgedConversationIdRef.current !== conversationId) {
          setMutationPending(true)
          nextView = await persist(conversationId, selectionRef.current)
          acknowledgedConversationIdRef.current = conversationId
          if (!cancelled) setMutationPending(false)
        } else {
          nextView = await getJson<SelectionView>(`/api/conversations/${encodeURIComponent(conversationId)}/ai-selection`, { signal: controller.signal })
        }
        if (!cancelled) {
          applyView(nextView, aggregate, clis)
          setLoadedConversationId(conversationId)
        }
      } catch (error) {
        if (cancelled || (error as { name?: string }).name === 'AbortError') return
        setMutationPending(false)
        if (error instanceof FeatureDisabled) {
          setLegacy(true)
          setLoadFailed(false)
          setOptions([])
          setStatusMessage('')
        } else {
          setLoadFailed(true)
          setStatusMessage('AI choices could not be loaded. Try again or open AI Console.')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true; controller.abort() }
  }, [enabled, conversationId, refreshVersion, applyView, persist])

  useEffect(() => {
    if (!enabled || legacy) return
    const onFocus = () => setRefreshVersion(version => version + 1)
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [enabled, legacy])

  const select = useCallback(async (next: ConversationSelection) => {
    if (!enabled || legacy) return
    if (!conversationId) {
      selectionRef.current = next
      setSelection(next)
      const aggregate = aggregateRef.current
      const clis = clisRef.current
      if (aggregate && clis) applyView(localView(next, aggregate, clis), aggregate, clis)
      return
    }
    setMutationPending(true)
    setStatusMessage('Saving AI choice…')
    try {
      const nextView = await persist(conversationId, next)
      const aggregate = aggregateRef.current
      const clis = clisRef.current
      if (aggregate && clis) applyView(nextView, aggregate, clis)
    } catch {
      // Deliberately retain the last server-confirmed selection.
      setStatusMessage('The AI choice could not be saved. Your previous choice remains active.')
    } finally {
      setMutationPending(false)
    }
  }, [enabled, legacy, conversationId, applyView, persist])

  const effectiveLegacy = !enabled || legacy
  const effectiveLoading = enabled && !legacy && (loading || loadedConversationId !== conversationId)
  const effectiveMutationPending = enabled && mutationPending
  const effectiveOptions = enabled ? options : EMPTY_OPTIONS
  const effectiveStatusMessage = !enabled ? '' : effectiveLoading ? 'Loading AI choices…' : statusMessage
  const canSubmit = effectiveLegacy
    || (!effectiveLoading && !effectiveMutationPending && !loadFailed && view.availability === 'ready')
  return useMemo(() => ({ enabled, legacy: effectiveLegacy, selection, options: effectiveOptions, availability: view.availability,
    loading: effectiveLoading, mutationPending: effectiveMutationPending, canSubmit, statusMessage: effectiveStatusMessage, select,
    refresh: () => setRefreshVersion(version => version + 1),
  }), [enabled, effectiveLegacy, selection, effectiveOptions, view.availability, effectiveLoading,
    effectiveMutationPending, canSubmit, effectiveStatusMessage, select])
}
