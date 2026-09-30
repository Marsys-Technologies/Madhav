'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { selectionKey } from './model_options'
import type { AiChoiceOption, ConversationSelection } from '../hooks/useAiChoices'

const MOBILE_QUERY = '(max-width: 767px)'
const GROUPS = ['API providers', 'Custom API configurations', 'Local CLIs',
  'Custom CLI configurations', 'Earlier configurations'] as const

function useMobile(): boolean {
  const [mobile, setMobile] = useState(() => typeof window !== 'undefined'
    && typeof window.matchMedia === 'function' && window.matchMedia(MOBILE_QUERY).matches)
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const query = window.matchMedia(MOBILE_QUERY)
    const update = () => setMobile(query.matches)
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  return mobile
}

export function AiChoicePicker({
  options, selected, open, disabled, onOpenChange, onSelect, onRefresh,
}: {
  options: AiChoiceOption[]
  selected: ConversationSelection
  open: boolean
  disabled: boolean
  onOpenChange: (open: boolean) => void
  onSelect: (selection: ConversationSelection) => void | Promise<void>
  onRefresh: () => void
}) {
  const rootRef = useRef<HTMLDivElement | null>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)
  const mobile = useMobile()
  const selectedKey = selectionKey(selected)
  const selectedOption = options.find(option => option.key === selectedKey)
  const valueLabel = selectedOption?.label ?? 'Default'

  useEffect(() => {
    if (!open) return
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) onOpenChange(false)
    }
    document.addEventListener('mousedown', onPointer)
    return () => document.removeEventListener('mousedown', onPointer)
  }, [open, onOpenChange])

  useEffect(() => {
    if (!open) return
    const frame = requestAnimationFrame(() => {
      const selectedRow = listRef.current?.querySelector<HTMLElement>('[aria-selected="true"]:not([aria-disabled="true"])')
      ;(selectedRow ?? listRef.current?.querySelector<HTMLElement>('[role="option"]:not([aria-disabled="true"])'))?.focus()
    })
    return () => cancelAnimationFrame(frame)
  }, [open, disabled, options, selectedKey])

  const grouped = useMemo(() => GROUPS.map(group => ({ group, rows: options.filter(option => option.group === group) })), [options])
  const ungrouped = options.filter(option => option.group === null)

  function closeAndRestore() {
    onOpenChange(false)
    requestAnimationFrame(() => triggerRef.current?.focus())
  }

  function row(option: AiChoiceOption) {
    const selectedRow = option.key === selectedKey
    const rowDisabled = disabled || option.disabled
    return (
      <div
        key={option.key}
        role="option"
        aria-selected={selectedRow}
        aria-disabled={rowDisabled || undefined}
        aria-label={`${option.label}${option.detail ? ` — ${option.detail}` : ''}`}
        tabIndex={rowDisabled ? -1 : 0}
        className="flex items-center gap-2.5 rounded-[7px]"
        style={{ padding: '9px 11px', cursor: rowDisabled ? 'not-allowed' : 'pointer', opacity: rowDisabled ? 0.65 : 1 }}
        onClick={() => {
          if (rowDisabled) return
          void onSelect(option.selection)
          closeAndRestore()
        }}
        onKeyDown={event => {
          if (rowDisabled) return
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            void onSelect(option.selection)
            closeAndRestore()
          }
        }}
      >
        <span style={{ fontSize: 13, color: selectedRow ? 'var(--pp-gold)' : 'var(--pp-ink)', flex: 'none' }}>{option.label}</span>
        {option.detail && <span style={{ fontSize: 11, color: 'var(--pp-gold-tertiary)', flex: 1 }}>{option.detail}</span>}
        <span aria-hidden className="font-mono flex-none w-3" style={{ color: 'var(--pp-gold)', fontSize: 11, visibility: selectedRow ? 'visible' : 'hidden' }}>✓</span>
      </div>
    )
  }

  const list = (
    <div
      ref={listRef}
      role="listbox"
      aria-label="AI choices"
      onKeyDown={event => {
        if (event.key === 'Escape') {
          event.preventDefault()
          closeAndRestore()
        }
      }}
    >
      {ungrouped.map(row)}
      {grouped.map(({ group, rows }) => rows.length > 0 && (
        <div key={group} role="group" aria-label={group}>
          <div aria-hidden style={{ padding: '8px 11px 3px', fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}>
            {group}
          </div>
          {rows.map(row)}
        </div>
      ))}
    </div>
  )

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        data-control="ai"
        className="flex items-center gap-1.5 rounded-full"
        style={{ fontSize: 11.5, color: 'var(--pp-ink-dim)', border: '1px solid var(--pp-rule)', background: 'none', padding: '5px 11px', cursor: disabled ? 'not-allowed' : 'pointer' }}
        disabled={disabled}
        aria-label={`AI ${valueLabel}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={event => {
          event.stopPropagation()
          if (!open) onRefresh()
          onOpenChange(!open)
        }}
        onKeyDown={event => {
          if (event.key === 'Escape' && open) closeAndRestore()
        }}
      >
        <span style={{ fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}>AI</span>
        <span style={{ color: 'var(--pp-ink)' }}>{valueLabel}</span>
        <span aria-hidden style={{ color: 'var(--pp-gold-tertiary)', fontSize: 9 }}>▾</span>
      </button>
      {open && mobile && (
        <>
          <div className="pp-sheet-scrim" onClick={closeAndRestore} />
          <div className="pp-sheet">
            <div className="mx-auto mb-3" style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--pp-rule-strong)' }} />
            {list}
          </div>
        </>
      )}
      {open && !mobile && (
        <div className="absolute z-10 rounded-[11px] p-1.5" style={{ bottom: '135%', left: 0, minWidth: 300, maxHeight: 360, overflowY: 'auto', background: 'var(--pp-raise)', border: '1px solid var(--pp-rule)', boxShadow: '0 20px 50px -12px rgba(0,0,0,0.9)' }}>
          {list}
        </div>
      )}
    </div>
  )
}
