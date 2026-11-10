'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'

export type BreadcrumbSegment = {
  label: string
  href?: string
  current?: boolean
}

export function AppShellBreadcrumb({
  segments,
  mobileNav,
}: {
  segments: BreadcrumbSegment[]
  mobileNav?: ReactNode
}) {
  const pathname = usePathname()
  // Consume and cockpit build have their own headers — breadcrumb is redundant there
  if (pathname.includes('/consume')) return null
  if (pathname.includes('/nirmana')) return null
  if (segments.length === 0 && !mobileNav) return null

  return (
    <header className={`folio-nav-surface flex min-h-11 shrink-0 items-center gap-2 border-b px-3 text-sm md:px-4 ${segments.length === 0 ? 'md:hidden' : ''}`}>
      {mobileNav}
      {segments.length > 0 && (
        <nav aria-label="Breadcrumb" className="min-w-0">
          <ol className="flex flex-wrap items-center gap-x-2">
            {segments.map((segment, index) => (
              <li key={index} className="flex min-w-0 items-center gap-2">
                {index > 0 && <span aria-hidden="true" className="text-[var(--folio-muted)]">·</span>}
                {segment.href && !segment.current ? (
                  <Link href={segment.href} className="flex min-h-11 items-center [overflow-wrap:anywhere] text-[var(--folio-action)] underline underline-offset-4">
                    {segment.label}
                  </Link>
                ) : (
                  <span
                    className="folio-nav-identity py-2 font-semibold"
                    aria-current={segment.current ? 'page' : undefined}
                  >
                    {segment.label}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}
    </header>
  )
}
