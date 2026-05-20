'use client'

/**
 * Collapsible — accessible collapsible panel primitive.
 *
 * Headless implementation (no Radix dependency required — shadcn pattern via
 * useState + aria-expanded). Used by ChoghadiyaPanel and HoraPanel.
 *
 * Features:
 *   - Animated chevron (rotates 180° when open)
 *   - aria-expanded on trigger button
 *   - Smooth max-height transition for content reveal
 *   - Fully composable: CollapsibleRoot > CollapsibleTrigger > CollapsibleContent
 *
 * Phase: 4C-4-S3 (Item 4)
 */

import React, { createContext, useContext, useState } from 'react'

// ── Context ───────────────────────────────────────────────────────────────────

interface CollapsibleContextValue {
  open: boolean
  toggle: () => void
  id: string
}

const CollapsibleContext = createContext<CollapsibleContextValue | null>(null)

function useCollapsible() {
  const ctx = useContext(CollapsibleContext)
  if (!ctx) throw new Error('Collapsible components must be used within CollapsibleRoot')
  return ctx
}

// ── Root ──────────────────────────────────────────────────────────────────────

interface CollapsibleRootProps {
  defaultOpen?: boolean
  children: React.ReactNode
  className?: string
  id?: string
}

export function CollapsibleRoot({
  defaultOpen = false,
  children,
  className = '',
  id,
}: CollapsibleRootProps) {
  const [open, setOpen] = useState(defaultOpen)
  const panelId = id ?? React.useId()

  return (
    <CollapsibleContext.Provider value={{ open, toggle: () => setOpen((v) => !v), id: panelId }}>
      <div className={className}>{children}</div>
    </CollapsibleContext.Provider>
  )
}

// ── Trigger ───────────────────────────────────────────────────────────────────

interface CollapsibleTriggerProps {
  children: React.ReactNode
  className?: string
}

export function CollapsibleTrigger({ children, className = '' }: CollapsibleTriggerProps) {
  const { open, toggle, id } = useCollapsible()

  return (
    <button
      type="button"
      aria-expanded={open}
      aria-controls={`collapsible-content-${id}`}
      onClick={toggle}
      className={`flex w-full items-center justify-between text-left ${className}`}
    >
      {children}
      {/* Animated chevron */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        style={{
          transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 200ms ease',
          flexShrink: 0,
          color: 'rgba(212,175,55,0.45)',
        }}
      >
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>
  )
}

// ── Content ───────────────────────────────────────────────────────────────────

interface CollapsibleContentProps {
  children: React.ReactNode
  className?: string
}

export function CollapsibleContent({ children, className = '' }: CollapsibleContentProps) {
  const { open, id } = useCollapsible()

  return (
    <div
      id={`collapsible-content-${id}`}
      role="region"
      style={{
        overflow: 'hidden',
        maxHeight: open ? '9999px' : '0',
        opacity: open ? 1 : 0,
        transition: 'max-height 300ms ease, opacity 200ms ease',
        visibility: open ? 'visible' : 'hidden',
      }}
      aria-hidden={!open}
      className={className}
    >
      {children}
    </div>
  )
}
