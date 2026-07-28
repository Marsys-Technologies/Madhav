'use client'

import { useEffect, useState } from 'react'

function hasMatchMedia(): boolean {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
}

function readPrefersReducedMotion(): boolean {
  if (!hasMatchMedia()) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** §5.7: `prefers-reduced-motion` degrades every fade/breathe/draw to instant. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(readPrefersReducedMotion)
  useEffect(() => {
    if (!hasMatchMedia()) return
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = () => setReduced(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])
  return reduced
}
