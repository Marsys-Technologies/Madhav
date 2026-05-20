'use client'

import { useCallback, useEffect, useState } from 'react'
import type { StyleId } from '@/components/chat/ModelStylePicker'

// ── useDraft ─────────────────────────────────────────────────────────────────

function draftKey(conversationId: string | null): string {
  return `madhav:draft:v1:${conversationId ?? '__new__'}`
}

/**
 * Per-conversation localStorage draft persistence (R7-S6).
 * Returns [draft, setDraft, clearDraft].
 * setDraft is a no-op for strings longer than 10 000 chars.
 * SSR-safe: all localStorage access is guarded by typeof window check.
 */
export function useDraft(
  conversationId: string | null,
): [string, (v: string) => void, () => void] {
  const key = draftKey(conversationId)

  const [draft, setDraftState] = useState<string>(() => {
    if (typeof window === 'undefined') return ''
    try { return localStorage.getItem(key) ?? '' } catch { return '' }
  })

  // AC-7: when conversationId changes, re-read from localStorage for the new key.
  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDraftState(localStorage.getItem(key) ?? '')
    } catch {
      setDraftState('')
    }
  }, [key])

  const setDraft = useCallback((v: string) => {
    if (v.length > 10000) return
    setDraftState(v)
    if (typeof window === 'undefined') return
    try { localStorage.setItem(key, v) } catch {}
  }, [key])

  const clearDraft = useCallback(() => {
    setDraftState('')
    if (typeof window === 'undefined') return
    try { localStorage.removeItem(key) } catch {}
  }, [key])

  return [draft, setDraft, clearDraft]
}
// ── useTextScale ─────────────────────────────────────────────────────────────

const TEXT_SCALE_KEY = 'marsys_chat_v2_text_scale'
const TEXT_SCALES = [0.875, 1.0, 1.125, 1.25] as const
export type TextScale = typeof TEXT_SCALES[number]

/**
 * X-S7: Global text-scale preference for the chat prose.
 * Persisted in localStorage. Returns [scale, increase, decrease].
 * Clamped — does not wrap around.
 */
export function useTextScale(): [TextScale, () => void, () => void] {
  const [scale, setScaleState] = useState<TextScale>(() => {
    if (typeof window === 'undefined') return 1.0
    try {
      const v = parseFloat(localStorage.getItem(TEXT_SCALE_KEY) ?? '')
      return (TEXT_SCALES as readonly number[]).includes(v) ? (v as TextScale) : 1.0
    } catch { return 1.0 }
  })

  const setScale = useCallback((next: TextScale) => {
    setScaleState(next)
    if (typeof window === 'undefined') return
    try { localStorage.setItem(TEXT_SCALE_KEY, String(next)) } catch {}
  }, [])

  const increase = useCallback(() => {
    setScaleState(cur => {
      const idx = TEXT_SCALES.indexOf(cur)
      const next = idx < TEXT_SCALES.length - 1 ? TEXT_SCALES[idx + 1] : cur
      if (next !== cur) {
        try { localStorage.setItem(TEXT_SCALE_KEY, String(next)) } catch {}
      }
      return next
    })
  }, [])

  const decrease = useCallback(() => {
    setScaleState(cur => {
      const idx = TEXT_SCALES.indexOf(cur)
      const next = idx > 0 ? TEXT_SCALES[idx - 1] : cur
      if (next !== cur) {
        try { localStorage.setItem(TEXT_SCALE_KEY, String(next)) } catch {}
      }
      return next
    })
  }, [])

  return [scale, increase, decrease]
}

export { TEXT_SCALES }

// ── useLastPrompt ─────────────────────────────────────────────────────────────

function lastPromptKey(conversationId: string | null): string {
  return `marsys_chat_v2_last_prompt_${conversationId ?? '__new__'}`
}

/**
 * X-S2: Per-conversation last-sent prompt cache in localStorage.
 * Returns [lastPrompt, saveLastPrompt] where:
 *   - lastPrompt: the most recently saved prompt for this conversation
 *   - saveLastPrompt: call with the sent text to persist it
 * SSR-safe: all localStorage access is guarded.
 */
export function useLastPrompt(conversationId: string | null): [string, (v: string) => void] {
  const key = lastPromptKey(conversationId)

  const [lastPrompt, setLastPrompt] = useState<string>(() => {
    if (typeof window === 'undefined') return ''
    try { return localStorage.getItem(key) ?? '' } catch { return '' }
  })

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLastPrompt(localStorage.getItem(key) ?? '')
    } catch {
      setLastPrompt('')
    }
  }, [key])

  const saveLastPrompt = useCallback((v: string) => {
    if (!v.trim()) return
    setLastPrompt(v)
    if (typeof window === 'undefined') return
    try { localStorage.setItem(key, v) } catch {}
  }, [key])

  return [lastPrompt, saveLastPrompt]
}

import {
  DEFAULT_STACK_ID,
  STACK_ROUTING,
  type ModelStack,
} from '@/lib/models/registry'

export type { ModelStack }

export type QueryType = 'deep' | 'study' | 'brief' | 'panel'

const DEFAULT_STACK: ModelStack = DEFAULT_STACK_ID
const DEFAULT_STYLE: StyleId = 'acharya'
const DEFAULT_QUERY_TYPE: QueryType = 'deep'
const DEFAULT_LEL_ENABLED = true

const VALID_STYLES: StyleId[] = ['acharya', 'brief', 'client']
const VALID_STACKS = Object.keys(STACK_ROUTING) as ModelStack[]
const VALID_QUERY_TYPES: QueryType[] = ['deep', 'study', 'brief', 'panel']

function keyFor(chartId: string) {
  return `marsys-jis:consume-prefs:${chartId}`
}

interface Prefs {
  stack: ModelStack
  style: StyleId
  queryType: QueryType
  lelEnabled: boolean
}

export function useChatPreferences(chartId: string) {
  const [prefs, setPrefs] = useState<Prefs>({
    stack: DEFAULT_STACK,
    style: DEFAULT_STYLE,
    queryType: DEFAULT_QUERY_TYPE,
    lelEnabled: DEFAULT_LEL_ENABLED,
  })

  useEffect(() => {
    try {
      const raw = localStorage.getItem(keyFor(chartId))
      if (!raw) return
      const parsed = JSON.parse(raw) as Partial<Prefs>
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPrefs({
        stack: parsed.stack && VALID_STACKS.includes(parsed.stack) ? parsed.stack : DEFAULT_STACK,
        style: VALID_STYLES.includes(parsed.style as StyleId) ? (parsed.style as StyleId) : DEFAULT_STYLE,
        queryType:
          parsed.queryType && VALID_QUERY_TYPES.includes(parsed.queryType)
            ? parsed.queryType
            : DEFAULT_QUERY_TYPE,
        lelEnabled: typeof parsed.lelEnabled === 'boolean' ? parsed.lelEnabled : DEFAULT_LEL_ENABLED,
      })
    } catch {}
  }, [chartId])

  const setStack = useCallback(
    (stack: ModelStack) => {
      setPrefs(cur => {
        const next = { ...cur, stack }
        try {
          localStorage.setItem(keyFor(chartId), JSON.stringify(next))
        } catch {}
        return next
      })
    },
    [chartId]
  )

  const setStyle = useCallback(
    (style: StyleId) => {
      setPrefs(cur => {
        const next = { ...cur, style }
        try {
          localStorage.setItem(keyFor(chartId), JSON.stringify(next))
        } catch {}
        return next
      })
    },
    [chartId]
  )

  const setQueryType = useCallback(
    (queryType: QueryType) => {
      setPrefs(cur => {
        const next = { ...cur, queryType }
        try {
          localStorage.setItem(keyFor(chartId), JSON.stringify(next))
        } catch {}
        return next
      })
    },
    [chartId]
  )

  const setLelEnabled = useCallback(
    (lelEnabled: boolean) => {
      setPrefs(cur => {
        const next = { ...cur, lelEnabled }
        try {
          localStorage.setItem(keyFor(chartId), JSON.stringify(next))
        } catch {}
        return next
      })
    },
    [chartId]
  )

  return {
    stack: prefs.stack,
    style: prefs.style,
    queryType: prefs.queryType,
    lelEnabled: prefs.lelEnabled,
    setStack,
    setStyle,
    setQueryType,
    setLelEnabled,
  }
}
