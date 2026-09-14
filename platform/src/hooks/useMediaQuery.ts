'use client'

import { useSyncExternalStore } from 'react'

const getServerSnapshot = () => false

function getMediaQuery(query: string): MediaQueryList | null {
  return typeof window.matchMedia === 'function' ? window.matchMedia(query) : null
}

export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const mediaQuery = getMediaQuery(query)
      if (!mediaQuery) return () => {}
      mediaQuery.addEventListener('change', onChange)
      return () => mediaQuery.removeEventListener('change', onChange)
    },
    () => getMediaQuery(query)?.matches ?? false,
    getServerSnapshot,
  )
}
