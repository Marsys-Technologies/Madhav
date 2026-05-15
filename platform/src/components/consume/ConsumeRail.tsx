'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { MessageSquare, FileText, Clock, LayoutDashboard } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ConversationSidebar } from '@/components/chat/ConversationSidebar'

interface ConversationRow {
  id: string
  title: string | null
  created_at: string
  chart_id: string
  user_id: string
  module: string
}

interface Props {
  panelOpen: boolean
  onPanelOpenChange: (open: boolean) => void
  chartId: string
  chartName: string
  conversations: ConversationRow[]
  currentConversationId?: string
  onConversationRenamed: (id: string, title: string) => void
  onConversationDeleted: (id: string) => void
}

export function ConsumeRail({
  panelOpen,
  onPanelOpenChange,
  chartId,
  chartName,
  conversations,
  currentConversationId,
  onConversationRenamed,
  onConversationDeleted,
}: Props) {
  const pathname = usePathname()
  const panelRef = useRef<HTMLDivElement>(null)
  const railRef = useRef<HTMLDivElement>(null)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Debounced close — prevents panel from snapping shut when cursor
  // crosses the gap between rail and panel on hover.
  function openPanel() {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    onPanelOpenChange(true)
  }
  function scheduleClose() {
    closeTimerRef.current = setTimeout(() => onPanelOpenChange(false), 80)
  }

  // Close panel on click-outside (both rail and panel excluded)
  useEffect(() => {
    if (!panelOpen) return
    function handleClick(e: MouseEvent) {
      if (
        panelRef.current?.contains(e.target as Node) ||
        railRef.current?.contains(e.target as Node)
      ) return
      onPanelOpenChange(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [panelOpen, onPanelOpenChange])

  const isConsume = pathname?.includes('/consume') ?? false

  const navItems = [
    {
      icon: MessageSquare,
      label: 'Consume',
      href: `/clients/${chartId}/consume`,
      active: isConsume,
    },
    {
      icon: FileText,
      label: 'Reports',
      href: `/clients/${chartId}/consume`,
      active: false,
      onClick: () => onPanelOpenChange(!panelOpen),
    },
    {
      icon: Clock,
      label: 'Timeline',
      href: `/clients/${chartId}/timeline`,
      active: false,
    },
    {
      icon: LayoutDashboard,
      label: 'Dashboard',
      href: '/dashboard',
      active: false,
    },
  ]

  return (
    <div
      ref={railRef}
      className="relative z-20 flex h-full w-11 shrink-0 flex-col items-center border-r border-[rgba(var(--brand-gold-rgb),0.08)] bg-[oklch(0.07_0.010_70)] py-3"
      onMouseEnter={openPanel}
      onMouseLeave={scheduleClose}
    >
      {/* Logo */}
      <div className="mb-4 flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--brand-gold)] to-[oklch(0.65_0.15_70)] text-[13px] font-bold text-[oklch(0.08_0.010_70)] shadow-[0_0_12px_rgba(var(--brand-gold-rgb),0.3)]">
        M
      </div>

      {/* Nav items */}
      <nav className="flex flex-1 flex-col items-center gap-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const content = (
            <span
              className={cn(
                'relative flex size-8 items-center justify-center rounded-[7px] transition-colors',
                item.active
                  ? 'bg-[rgba(var(--brand-gold-rgb),0.12)] text-[var(--brand-gold)]'
                  : 'text-[var(--brand-gold-cream)]/40 hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[var(--brand-gold-cream)]/80'
              )}
            >
              {item.active && (
                <span className="absolute -left-[11px] h-4 w-[3px] rounded-r-full bg-[var(--brand-gold)]" />
              )}
              <Icon className="size-4" />
            </span>
          )
          if (item.onClick) {
            return (
              <button key={item.label} type="button" onClick={item.onClick} aria-label={item.label}>
                {content}
              </button>
            )
          }
          return (
            <Link key={item.label} href={item.href} aria-label={item.label}>
              {content}
            </Link>
          )
        })}
      </nav>

      {/* User avatar — bottom of rail */}
      <div
        className="mb-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-[rgba(var(--brand-gold-rgb),0.15)] text-[9px] font-bold uppercase text-[var(--brand-gold)]/70"
        aria-label="User"
      >
        U
      </div>

      {/* Hover-expand panel — uses debounced open/close so cursor can
          move from rail to panel without the panel snapping shut */}
      <div
        ref={panelRef}
        onMouseEnter={openPanel}
        onMouseLeave={scheduleClose}
        className={cn(
          'consume-rail-panel absolute left-11 top-0 h-full w-60 overflow-hidden',
          'border-r border-[rgba(var(--brand-gold-rgb),0.08)]',
          'bg-[#0b0804] shadow-[4px_0_32px_rgba(0,0,0,0.7)]',
          panelOpen ? 'opacity-100 translate-x-0 pointer-events-auto' : 'opacity-0 -translate-x-2 pointer-events-none'
        )}
        style={{ zIndex: 19 }}
      >
        <ConversationSidebar
          chartId={chartId}
          chartName={chartName}
          conversations={conversations}
          currentConversationId={currentConversationId}
          onRenamed={onConversationRenamed}
          onDeleted={onConversationDeleted}
          onClose={() => onPanelOpenChange(false)}
        />
      </div>
    </div>
  )
}
