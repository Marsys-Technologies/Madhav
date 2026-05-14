'use client'

import { useEffect, useCallback } from 'react'

export interface KeyboardShortcutBindings {
  /** Cmd/Ctrl+K — focus the composer (command palette or direct) */
  onCompose?: () => void
  /** Cmd/Ctrl+/ — show shortcuts help overlay */
  onShortcutsHelp?: () => void
  /** Cmd/Ctrl+Enter — submit the composer */
  onSubmit?: () => void
  /** Escape — collapse panels + return focus to composer */
  onEscape?: () => void
  /** Cmd/Ctrl+B — toggle sidebar */
  onToggleSidebar?: () => void
  /** Cmd/Ctrl+Shift+O — new chat */
  onNewChat?: () => void
}

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA') return true
  if (target.isContentEditable) return true
  return false
}

/**
 * useKeyboardShortcuts — CO.6 consolidated keyboard handler.
 *
 * Bindings:
 *   Cmd/Ctrl+K         → onCompose (focus composer)
 *   Cmd/Ctrl+/         → onShortcutsHelp
 *   Cmd/Ctrl+Enter     → onSubmit (even from within a typing target)
 *   Escape             → onEscape
 *   Cmd/Ctrl+B         → onToggleSidebar
 *   Cmd/Ctrl+Shift+O   → onNewChat
 *
 * Supersedes / consolidates useHotkeys for the flag-ON path.
 */
export function useKeyboardShortcuts(bindings: KeyboardShortcutBindings) {
  const stableBindings = bindings

  const onKey = useCallback(
    (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey

      if (mod && e.key.toLowerCase() === 'k' && !e.shiftKey) {
        e.preventDefault()
        stableBindings.onCompose?.()
        return
      }
      if (mod && e.key === '/') {
        e.preventDefault()
        stableBindings.onShortcutsHelp?.()
        return
      }
      if (mod && e.key === 'Enter') {
        // Submit fires even inside a textarea (composer submit behavior).
        e.preventDefault()
        stableBindings.onSubmit?.()
        return
      }
      if (mod && e.key.toLowerCase() === 'b' && !e.shiftKey) {
        if (isTypingTarget(e.target)) return
        e.preventDefault()
        stableBindings.onToggleSidebar?.()
        return
      }
      if (mod && e.shiftKey && e.key.toLowerCase() === 'o') {
        e.preventDefault()
        stableBindings.onNewChat?.()
        return
      }
      if (e.key === 'Escape') {
        stableBindings.onEscape?.()
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  useEffect(() => {
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onKey])
}
