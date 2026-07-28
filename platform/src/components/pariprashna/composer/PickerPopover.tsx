'use client'

import { useEffect, useRef } from 'react'

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

  useEffect(() => {
    if (!open) return
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) onOpenChange(false)
    }
    document.addEventListener('click', onDocClick)
    return () => document.removeEventListener('click', onDocClick)
  }, [open, onOpenChange])

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
      {open && (
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
        </div>
      )}
    </div>
  )
}
