'use client'

import { useEffect } from 'react'

interface Bindings {
  onPalette?: () => void
  onNewChat?: () => void
  onToggleSidebar?: () => void
  onShortcutsHelp?: () => void
  onEscape?: () => void
}

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA') return true
  if (target.isContentEditable) return true
  return false
}

export function useHotkeys(bindings: Bindings) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const mod = e.metaKey || e.ctrlKey
      if (mod && e.key.toLowerCase() === 'k' && !e.shiftKey) {
        e.preventDefault()
        bindings.onPalette?.()
        return
      }
      if (mod && e.shiftKey && e.key.toLowerCase() === 'o') {
        e.preventDefault()
        bindings.onNewChat?.()
        return
      }
      if (mod && e.key.toLowerCase() === 'b' && !e.shiftKey) {
        if (isTypingTarget(e.target)) return
        e.preventDefault()
        bindings.onToggleSidebar?.()
        return
      }
      if (mod && e.key === '/') {
        e.preventDefault()
        bindings.onShortcutsHelp?.()
        return
      }
      if (e.key === 'Escape') {
        bindings.onEscape?.()
        return
      }

      if ((e.key === 'j' || e.key === 'k') && !e.metaKey && !e.ctrlKey && !e.altKey) {
        if (isTypingTarget(e.target)) return
        const rows = Array.from(
          document.querySelectorAll<HTMLElement>('[data-message-index]'),
        )
        if (rows.length === 0) return
        const active = document.activeElement as HTMLElement | null
        const currentIdx = rows.findIndex(r => r === active || r.contains(active))
        let nextIdx: number
        if (e.key === 'j') {
          nextIdx = currentIdx < 0 ? 0 : Math.min(currentIdx + 1, rows.length - 1)
        } else {
          nextIdx = currentIdx < 0 ? rows.length - 1 : Math.max(currentIdx - 1, 0)
        }
        e.preventDefault()
        rows[nextIdx]?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [bindings])
}
