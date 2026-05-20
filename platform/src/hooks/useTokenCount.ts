'use client'

import { useEffect, useRef, useState } from 'react'
import { stackPicker } from '@/lib/models/registry'

type EncodeFn = (text: string) => number[]

interface TokenCountResult {
  tokenCount: number | null
  contextWindowTokens: number
  pctUsed: number | null
}

export function useTokenCount(inputValue: string): TokenCountResult {
  const [encodeFn, setEncodeFn] = useState<EncodeFn | null>(null)
  const [tokenCount, setTokenCount] = useState<number | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const contextWindowTokens =
    stackPicker().find(s => s.isDefault)?.synthesisContextWindow ?? 128000

  useEffect(() => {
    if (typeof window === 'undefined') return
    import('gpt-tokenizer')
      .then(mod => {
        setEncodeFn(() => mod.encode as EncodeFn)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!encodeFn) return
    if (timerRef.current) clearTimeout(timerRef.current)

    const delay = inputValue.length > 50000 ? 500 : 200
    timerRef.current = setTimeout(() => {
      setTokenCount(encodeFn(inputValue).length)
    }, delay)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [inputValue, encodeFn])

  const pctUsed =
    tokenCount !== null
      ? Math.round((tokenCount / contextWindowTokens) * 100)
      : null

  return { tokenCount, contextWindowTokens, pctUsed }
}
