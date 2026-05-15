'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  ArrowLeft,
  LayoutDashboard,
  ListOrdered,
  PiggyBank,
  Scale,
  Database,
  Gauge,
  LineChart,
  GitCompare,
  History,
  Sparkles,
} from 'lucide-react'

const MAIN_LINKS = [
  { href: '/observatory', label: 'Overview', exact: true, Icon: LayoutDashboard },
  { href: '/observatory/events', label: 'Events', exact: false, Icon: ListOrdered },
  { href: '/observatory/budgets', label: 'Budgets', exact: false, Icon: PiggyBank },
  { href: '/observatory/reconciliation', label: 'Reconcile', exact: false, Icon: Scale },
] as const

const ANALYTICS_LINKS = [
  { href: '/observatory/analytics/cache', label: 'Cache', Icon: Database },
  { href: '/observatory/analytics/cost-per-quality', label: 'Cost ↔ Quality', Icon: Gauge },
  { href: '/observatory/analytics/cost-arc', label: 'Cost arc', Icon: LineChart },
  { href: '/observatory/analytics/pricing-diff', label: 'Pricing diff', Icon: GitCompare },
  { href: '/observatory/analytics/replay', label: 'Replay', Icon: History },
  { href: '/observatory/analytics/anomaly', label: 'Anomaly', Icon: Sparkles },
] as const

export function ObservatorySubNav() {
  const pathname = usePathname()

  function isActive(href: string, exact: boolean) {
    return exact ? pathname === href : pathname.startsWith(href)
  }

  return (
    <nav
      aria-label="Observatory navigation"
      className="hidden w-52 shrink-0 flex-col gap-3 border-r border-[rgba(var(--brand-gold-rgb),0.12)] py-4 md:flex"
      style={{
        background: 'oklch(0.07 0.010 68 / 0.70)',
        backdropFilter: 'blur(16px) saturate(140%)',
        WebkitBackdropFilter: 'blur(16px) saturate(140%)',
      }}
    >
      {/* Back to Roster */}
      <Link
        href="/dashboard"
        className="mx-2 flex items-center gap-2 rounded-full px-3 py-1.5 bt-label bt-label-upper text-[rgba(212,175,55,0.45)] transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.08)] hover:text-[var(--brand-gold)]"
        aria-label="Back to Roster"
      >
        <ArrowLeft size={12} aria-hidden="true" />
        Roster
      </Link>

      <div className="mx-3 h-px bg-[rgba(var(--brand-gold-rgb),0.1)]" />

      <div className="flex flex-col gap-1 px-2">
        <p className="px-3 bt-label bt-label-upper text-[rgba(212,175,55,0.35)]">
          ॥ Observatory
        </p>
        {MAIN_LINKS.map(({ href, label, exact, Icon }) => {
          const active = isActive(href, exact)
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'group flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors',
                active
                  ? 'bg-[rgba(var(--brand-gold-rgb),0.14)] text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_rgba(var(--brand-gold-rgb),0.28),inset_0_0_24px_rgba(var(--brand-gold-rgb),0.08)]'
                  : 'text-[rgba(212,175,55,0.50)] hover:bg-[rgba(var(--brand-gold-rgb),0.07)] hover:text-[var(--brand-gold)]',
              )}
            >
              <Icon size={14} aria-hidden="true" className="shrink-0 opacity-90" />
              <span>{label}</span>
            </Link>
          )
        })}
      </div>

      <div className="mx-3 h-px bg-[rgba(var(--brand-gold-rgb),0.1)]" />

      <div className="flex flex-col gap-1 px-2">
        <p className="px-3 bt-label bt-label-upper text-[rgba(212,175,55,0.35)]">
          Analytics
        </p>
        {ANALYTICS_LINKS.map(({ href, label, Icon }) => {
          const active = pathname === href
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'group flex items-center gap-2.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors',
                active
                  ? 'bg-[rgba(var(--brand-gold-rgb),0.12)] text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_rgba(var(--brand-gold-rgb),0.22)]'
                  : 'text-[rgba(212,175,55,0.42)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[var(--brand-gold)]',
              )}
            >
              <Icon size={12} aria-hidden="true" className="shrink-0 opacity-80" />
              <span>{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
