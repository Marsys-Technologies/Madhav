'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const TABS = [
  { label: 'Control Panel', href: '/aiops/control' },
  { label: 'Observatory', href: '/observatory' },
] as const

export function AiopsTabs() {
  const pathname = usePathname()

  return (
    <nav
      aria-label="AIOps sections"
      className="flex gap-1 border-b border-border px-4 pt-3 pb-2"
    >
      {TABS.map(({ label, href }) => {
        const isActive = pathname.startsWith(href)
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? 'page' : undefined}
            className={[
              'rounded-full px-3.5 py-1.5 text-xs font-semibold uppercase tracking-wider transition-colors',
              isActive
                ? 'aiops-tab-active border border-[rgba(var(--brand-gold-rgb),0.6)]'
                : 'border border-transparent text-muted-foreground hover:text-foreground hover:border-[rgba(var(--brand-gold-rgb),0.20)]',
            ].join(' ')}
          >
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
