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
      className="flex gap-1 border-b border-border px-4 pt-2"
    >
      {TABS.map(({ label, href }) => {
        const isActive = pathname.startsWith(href)
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? 'page' : undefined}
            className={[
              'rounded-t px-4 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'border border-b-0 border-border bg-background text-foreground'
                : 'text-muted-foreground hover:text-foreground',
            ].join(' ')}
          >
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
