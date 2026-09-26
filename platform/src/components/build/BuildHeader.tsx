'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Logo } from '@/components/brand/Logo'
import { RefreshButton } from './RefreshButton'

const NAV_LINKS = [
  { href: '/cockpit', label: 'Cockpit' },
  { href: '/cockpit/plan', label: 'Plan' },
  { href: '/cockpit/sessions', label: 'Sessions' },
  { href: '/cockpit/registry', label: 'Registry' },
  { href: '/cockpit/interventions', label: 'Interventions' },
  { href: '/cockpit/parallel', label: 'Parallel' },
  { href: '/cockpit/health', label: 'Health' },
  { href: '/cockpit/activity', label: 'Activity' },
]

export function BuildHeader() {
  const pathname = usePathname()

  return (
    <header className="border-b border-border bg-background">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-2">
        <div className="flex items-center gap-4">
          <Link href="/cockpit" className="flex items-center gap-2 shrink-0">
            <Logo size="sm" />
            <span className="font-serif text-sm font-medium tracking-[0.14em]">COCKPIT</span>
          </Link>
          <nav className="hidden items-center gap-0.5 md:flex">
            {NAV_LINKS.map(({ href, label }) => {
              const isActive =
                href === '/cockpit' ? pathname === '/cockpit' : pathname.startsWith(href)
              return (
                <Link
                  key={href}
                  href={href}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <RefreshButton />
        </div>
      </div>
    </header>
  )
}
