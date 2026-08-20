'use client'

import { useEffect, useRef, useState } from 'react'

const MOBILE_QUERY = '(max-width: 767px)' // §9.1 mobile breakpoint

function hasMatchMedia(): boolean {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
}

/** §9.2: "every disclosure that would displace settled content on mobile
 *  (citation card, probability detail, MODEL PICKER, audit) is a sheet."
 *  Below 768px this popover renders as a bottom sheet instead of an
 *  anchored dropdown — same list, same keyboard semantics, sheet chrome. */
function useIsMobileViewport(): boolean {
  const [isMobile, setIsMobile] = useState(() => (hasMatchMedia() ? window.matchMedia(MOBILE_QUERY).matches : false))
  useEffect(() => {
    if (!hasMatchMedia()) return
    const mql = window.matchMedia(MOBILE_QUERY)
    const onChange = () => setIsMobile(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])
  return isMobile
}

export interface PickerRow<T extends string> {
  value: T
  label: string
  detail?: string
  meta?: string
}

/**
 * Generic pill popover shared by Model/Depth/Length (§5.8, §6.11): one open
 * at a time, closes on outside click, keyboard-navigable rows, selected
 * row shows a check mark. Order on the composer is fixed: Model → Depth →
 * Length (§5.8.0 ruling 4).
 */
export function PickerPopover<T extends string>({
  eyebrow,
  valueLabel,
  tierNote,
  rows,
  selected,
  open,
  onOpenChange,
  onSelect,
}: {
  eyebrow?: string
  valueLabel: string
  tierNote?: string
  rows: PickerRow<T>[]
  selected: T
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelect: (value: T) => void
}) {
  const rootRef = useRef<HTMLDivElement | null>(null)
  const isMobile = useIsMobileViewport()

  useEffect(() => {
    if (!open) return
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) onOpenChange(false)
    }
    document.addEventListener('click', onDocClick)
    return () => document.removeEventListener('click', onDocClick)
  }, [open, onOpenChange])

  const optionRows = (
    <>
      {rows.map((row) => {
        const isSel = row.value === selected
        return (
          <div
            key={row.value}
            role="option"
            aria-selected={isSel}
            tabIndex={0}
            className="flex items-center gap-2.5 rounded-[7px] cursor-pointer"
            style={{ padding: '9px 11px' }}
            onClick={() => {
              onSelect(row.value)
              onOpenChange(false)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onSelect(row.value)
                onOpenChange(false)
              }
            }}
          >
            <span style={{ fontSize: 13, color: isSel ? 'var(--pp-gold)' : 'var(--pp-ink)', flex: 'none' }}>{row.label}</span>
            {row.detail && <span style={{ fontSize: 11, color: 'var(--pp-gold-tertiary)', flex: 1 }}>{row.detail}</span>}
            {row.meta && (
              <span
                className="font-mono flex-none"
                style={{ fontSize: 9, letterSpacing: '0.06em', color: 'var(--pp-gold-tertiary)', border: '1px solid var(--pp-rule)', padding: '2px 6px', borderRadius: 10 }}
              >
                {row.meta}
              </span>
            )}
            <span className="font-mono flex-none w-3" style={{ color: 'var(--pp-gold)', fontSize: 11, visibility: isSel ? 'visible' : 'hidden' }}>
              ✓
            </span>
          </div>
        )
      })}
    </>
  )

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        className="flex items-center gap-1.5 rounded-full"
        style={{
          fontSize: 11.5,
          color: 'var(--pp-ink-dim)',
          border: '1px solid var(--pp-rule)',
          background: 'none',
          padding: '5px 11px',
          cursor: 'pointer',
        }}
        onClick={(e) => {
          e.stopPropagation()
          onOpenChange(!open)
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {eyebrow && (
          <span style={{ fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}>{eyebrow}</span>
        )}
        <span style={{ color: 'var(--pp-ink)' }}>{valueLabel}</span>
        {tierNote && <span className="font-mono" style={{ fontSize: 9, color: 'var(--pp-gold-tertiary)' }}>{tierNote}</span>}
        <span style={{ color: 'var(--pp-gold-tertiary)', fontSize: 9 }}>▾</span>
      </button>
      {open && isMobile && (
        // §9.2: "every disclosure that would displace settled content on
        // mobile … (model picker …) is a sheet" — below 768px this is a
        // bottom sheet (reusing the citation card's `.pp-sheet` chrome),
        // never the anchored dropdown, which on a narrow viewport would
        // either overflow the screen edge or sit awkwardly over the
        // triggering pill.
        <>
          <div className="pp-sheet-scrim" onClick={() => onOpenChange(false)} />
          <div className="pp-sheet" role="listbox" aria-label={eyebrow ?? 'Options'}>
            <div className="mx-auto mb-3" style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--pp-rule-strong)' }} />
            {optionRows}
          </div>
        </>
      )}
      {open && !isMobile && (
        <div
          role="listbox"
          className="absolute z-10 rounded-[11px] p-1.5"
          style={{
            bottom: '135%',
            left: 0,
            minWidth: 220,
            background: 'var(--pp-raise)',
            border: '1px solid var(--pp-rule)',
            boxShadow: '0 20px 50px -12px rgba(0,0,0,0.9)',
          }}
        >
          {optionRows}
        </div>
      )}
    </div>
  )
}
