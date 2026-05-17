'use client'

import { useCallback, useEffect, useState } from 'react'
import type { StyleId } from '@/components/chat/ModelStylePicker'
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
