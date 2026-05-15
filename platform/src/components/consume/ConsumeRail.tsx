'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  MessageSquare,
  FileText,
  Clock,
  LayoutDashboard,
  Sun,
  Moon,
  Monitor,
} from 'lucide-react'
import { useTheme } from 'next-themes'
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
  visible: boolean
  onVisibleChange: (visible: boolean) => void
  panelOpen: boolean
  onPanelOpenChange: (open: boolean) => void
  onOpenReportsPanel?: () => void
  chartId: string
  chartName: string
  conversations: ConversationRow[]
  currentConversationId?: string
  onConversationRenamed: (id: string, title: string) => void
  onConversationDeleted: (id: string) => void
}

export function ConsumeRail({
  visible,
  onVisibleChange,
  panelOpen,
  onPanelOpenChange,
  onOpenReportsPanel,
  chartId,
  chartName,
  conversations,
  currentConversationId,
  onConversationRenamed,
  onConversationDeleted,
}: Props) {
  const pathname = usePathname()
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Theme cycling (light → dark → system → light)
  const { theme, setTheme } = useTheme()
  const [themeMounted, setThemeMounted] = useState(false)
  useEffect(() => { setThemeMounted(true) }, [])
  const currentTheme = themeMounted ? (theme ?? 'system') : 'system'
  const ThemeIcon =
    currentTheme === 'light' ? Sun : currentTheme === 'dark' ? Moon : Monitor
  function cycleTheme() {
    const next =
      currentTheme === 'light' ? 'dark' : currentTheme === 'dark' ? 'system' : 'light'
    setTheme(next)
  }

  // Close on click-outside when visible
  useEffect(() => {
    if (!visible) return
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current?.contains(e.target as Node)) return
      onVisibleChange(false)
      onPanelOpenChange(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [visible, onVisibleChange, onPanelOpenChange])

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
      onClick: () => onOpenReportsPanel?.(),
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
      ref={wrapperRef}
      className={cn(
        'group absolute left-0 top-0 z-30 h-full transition-[translate] duration-200 ease-out',
        visible ? 'translate-x-0' : '-translate-x-full'
      )}
      onMouseLeave={() => {
        // Cursor left both rail and panel — close everything
        onVisibleChange(false)
        onPanelOpenChange(false)
      }}
    >
      {/* Rail icon strip (44px) */}
      <div className="relative z-20 flex h-full w-11 shrink-0 flex-col items-center border-r border-[rgba(var(--brand-gold-rgb),0.08)] bg-[oklch(0.07_0.010_70)] py-3">
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
                    : 'text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[color-mix(in_oklch,var(--brand-gold-cream)_80%,transparent)]'
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

        {/* Theme toggle — bottom of rail */}
        <button
          type="button"
          onClick={cycleTheme}
          aria-label={`Theme: ${currentTheme}. Click to cycle.`}
          title={`Theme: ${currentTheme}`}
          className="flex size-8 items-center justify-center rounded-[7px] text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[color-mix(in_oklch,var(--brand-gold-cream)_80%,transparent)]"
        >
          <ThemeIcon className="size-4" />
        </button>
      </div>

      {/* Conversation panel — slides out on hover, controlled by panelOpen for ⌘B */}
      <div
        className={cn(
          'consume-rail-panel absolute left-11 top-0 h-full w-[280px] overflow-hidden',
          'border-r border-[rgba(var(--brand-gold-rgb),0.08)]',
          'bg-[#0b0804] shadow-[4px_0_32px_rgba(0,0,0,0.7)]',
          panelOpen
            ? 'opacity-100 translate-x-0 pointer-events-auto'
            : 'opacity-0 -translate-x-2 pointer-events-none',
          'group-hover:opacity-100 group-hover:translate-x-0 group-hover:pointer-events-auto'
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
          onClose={() => {
            onPanelOpenChange(false)
            onVisibleChange(false)
          }}
          hideFooter
        />
      </div>
    </div>
  )
}
