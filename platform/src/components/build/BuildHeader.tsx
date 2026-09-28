'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Logo } from '@/components/brand/Logo'
import { RefreshButton } from './RefreshButton'

const NAV_LINKS = [
  { href: '/ai-console', label: 'AI Console', feature: 'aiConsole' as const },
  { href: '/observatory', label: 'Observatory' },
]

export function BuildHeader({ showAiConsole = false }: { showAiConsole?: boolean }) {
  const pathname = usePathname()
  const navLinks = NAV_LINKS.filter(link => link.feature !== 'aiConsole' || showAiConsole)

  return (
    <header className="border-b border-border bg-background">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-2">
        <div className="flex items-center gap-4">
          <Link href="/cockpit" className="flex items-center gap-2 shrink-0">
            <Logo size="sm" />
            <span className="font-serif text-sm font-medium tracking-[0.14em]">COCKPIT</span>
          </Link>
          <nav aria-label="Cockpit sections" className="flex items-center gap-0.5">
            {navLinks.map(({ href, label }) => {
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
