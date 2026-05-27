'use client'

/**
 * SettingsDropdown — R11.G (Toggle Redesign), 3.cutover (Selector Default Flip)
 *
 * Replaces the inline MultiProviderParityToggle with a polished gear-icon
 * dropdown. Two clearly labelled radio options let users choose their
 * chat shell experience without reloading the page.
 *
 * VISIBILITY: Hidden entirely when NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY
 * is false (build-time kill-switch). Only visible when operator enables the env-var.
 *
 * STATE: Reads from / writes to localStorage via useChatShellMode().
 *
 * BACKEND PIPELINE SELECTOR (3.cutover, G5b — 2026-05-28):
 *   Independent of this UI control. The new pipeline-selection seam at
 *   `@/lib/pipelines/selector.ts::isPipelineSelectorEnabled()` now defaults ON;
 *   operator opts out with `MARSYS_FLAG_PIPELINE_SELECTOR=false`. Adapter onFinish
 *   write-through reached parity with legacy via `runOnFinishWriteThrough`
 *   (proved by `onfinish_parity.golden.test.ts`). Legacy code path remains
 *   reachable behind the flag and is NOT deleted in this unit — that lands
 *   in 3.legacy_delete.
 *
 * CLOSE: Click outside the menu to dismiss (mousedown listener on document).
 */

import { useEffect, useRef, useState } from 'react'
import { Settings as SettingsIcon } from 'lucide-react'
import {
  useChatShellMode,
  PARITY_ENV_ENABLED,
} from '@/lib/chat-v2/useMultiProviderParity'

export function SettingsDropdown() {
  const [open, setOpen] = useState(false)
  const { mode, setMode } = useChatShellMode()
  const containerRef = useRef<HTMLDivElement>(null)

  // Close menu when user clicks outside
  useEffect(() => {
    if (!open) return
    function handleOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleOutside)
    return () => document.removeEventListener('mousedown', handleOutside)
  }, [open])

  // Hidden entirely when env-var kill-switch is false
  if (!PARITY_ENV_ENABLED) return null

  return (
    <div className="relative" data-testid="settings-dropdown" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-label="Settings"
        aria-expanded={open}
        className={[
          'flex items-center justify-center h-7 w-7 rounded-md transition-colors',
          'border border-zinc-700 text-zinc-400 hover:text-zinc-100 hover:border-zinc-500',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold/40',
          open ? 'bg-zinc-800 text-zinc-100 border-zinc-500' : 'bg-transparent',
        ].join(' ')}
        data-testid="settings-gear-button"
      >
        <SettingsIcon size={18} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-72 rounded-md border border-zinc-700 bg-popover p-3 shadow-md z-50"
          data-testid="settings-dropdown-menu"
        >
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            Chat experience
          </div>

          <label className="flex items-start gap-2 cursor-pointer p-2 rounded hover:bg-accent">
            <input
              type="radio"
              name="chat-shell"
              checked={mode === 'classic'}
              onChange={() => setMode('classic')}
              data-testid="chat-shell-classic"
              className="mt-1"
            />
            <div>
              <div className="font-medium text-sm">Classic Marsys</div>
              <div className="text-xs text-muted-foreground">
                Familiar interface with full Marsys branding.
              </div>
            </div>
          </label>

          <label className="flex items-start gap-2 cursor-pointer p-2 rounded hover:bg-accent">
            <input
              type="radio"
              name="chat-shell"
              checked={mode === 'multi-provider'}
              onChange={() => setMode('multi-provider')}
              data-testid="chat-shell-claude-style"
              className="mt-1"
            />
            <div>
              <div className="font-medium text-sm">Claude-style chat</div>
              <div className="text-xs text-muted-foreground">
                Conversational interface inspired by Claude.ai. Bubble-less, 768px reading column, serif body.
              </div>
            </div>
          </label>

          <div className="text-[10px] text-muted-foreground mt-2 pt-2 border-t border-zinc-700">
            Changing chat experience takes effect on next message.
          </div>
        </div>
      )}
    </div>
  )
}
