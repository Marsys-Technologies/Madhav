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
  if (pathname.includes('/build')) return null
  if (segments.length === 0) return null

  return (
    <nav
      aria-label="Breadcrumb"
      className="flex h-10 items-center gap-1.5 border-b border-[rgba(212,175,55,0.12)] bg-[rgba(8,5,2,0.5)] px-4 text-sm"
    >
      {mobileNav}
      {segments.map((seg, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && (
            <span aria-hidden="true" className="select-none text-[rgba(212,175,55,0.2)]">
              ·
            </span>
          )}
          {seg.href && !seg.current ? (
            <Link
              href={seg.href}
              className="text-[rgba(212,175,55,0.45)] transition-colors hover:text-[#fce29a]"
            >
              {seg.label}
            </Link>
          ) : (
            <span
              className={seg.current ? 'font-medium text-[#fce29a]' : 'text-[rgba(212,175,55,0.45)]'}
              aria-current={seg.current ? 'page' : undefined}
            >
              {seg.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  )
}
