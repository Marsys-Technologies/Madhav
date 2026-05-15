'use client'

import { useEffect, useState } from 'react'
import { useDirtyRows } from './DirtyRowsContext'

interface CollapsibleSectionProps {
  /** Label shown in the collapsed/expanded header (uppercase eyebrow). */
  label: string
  /** Secondary descriptor rendered after the label (e.g. "6 cross-stack call types"). */
  hint?: string
  /** localStorage key for persisting open/closed state. */
  storageKey: string
  /** Default state when no localStorage entry exists. */
  defaultOpen?: boolean
  /** Dirty-key prefix used to surface a dirty-rows count badge on the collapsed header (e.g. "marsys:"). */
  dirtyKeyPrefix?: string
  children: React.ReactNode
}

export function CollapsibleSection({
  label,
  hint,
  storageKey,
  defaultOpen = false,
  dirtyKeyPrefix,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen)
  const [hydrated, setHydrated] = useState(false)
  const { dirtyCount } = useDirtyRows()

  // Hydration step: read persisted open/closed once on mount. Syncing with
  // an external system (localStorage) is exactly what useEffect is for.
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(storageKey)
      if (stored === 'open') {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setOpen(true)
      } else if (stored === 'closed') {
        setOpen(false)
      }
    } catch { /* localStorage unavailable */ }
    setHydrated(true)
  }, [storageKey])

  useEffect(() => {
    if (!hydrated) return
    try {
      window.localStorage.setItem(storageKey, open ? 'open' : 'closed')
    } catch { /* localStorage unavailable */ }
  }, [open, hydrated, storageKey])

  const dirty = dirtyKeyPrefix
    ? dirtyCount((key) => key.startsWith(dirtyKeyPrefix))
    : 0

  return (
    <section className="mt-6">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 rounded-md px-1 py-1 text-left hover:bg-[rgba(var(--brand-gold-rgb),0.06)]"
      >
        <span
          aria-hidden
          className="inline-block text-[var(--brand-gold)] transition-transform"
          style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }}
        >
          ▸
        </span>
        <span className="bt-label bt-label-upper">{label}</span>
        {hint && (
          <span className="bt-label normal-case tracking-normal text-[oklch(0.62_0.02_75)]">
            · {hint}
          </span>
        )}
        {dirty > 0 && (
          <span
            className="ml-2 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
            style={{ background: 'var(--brand-gold)', color: 'var(--brand-ink)' }}
            aria-label={`${dirty} unsaved changes`}
          >
            {dirty}
          </span>
        )}
      </button>

      {open && <div className="mt-2">{children}</div>}
    </section>
  )
}
