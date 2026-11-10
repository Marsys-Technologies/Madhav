'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { signOut as firebaseSignOut } from 'firebase/auth'
import {
  ChartColumn,
  ChevronDown,
  FileSearch,
  Gauge,
  Info,
  LayoutGrid,
  Map,
  MenuIcon,
  Settings2,
  SlidersHorizontal,
  type LucideIcon,
} from 'lucide-react'
import { auth } from '@/lib/firebase/client'
import { Sigil } from '@/components/brand/Sigil'
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import {
  normalizeRole,
  isNavItemActive,
  visibleNavItems,
  visibleInformationNavItems,
} from '@/components/nav/role-gates'
import { cn } from '@/lib/utils'
import type React from 'react'

interface MobileNavSheetProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'guest'; status?: string }
}

// Lunar crescent SVG icon for Panchang — matches AppShellRail
function MoonCrescentIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.9-.1-1.35A7 7 0 0 1 12 3z" />
    </svg>
  )
}

const NAV_ICONS: Record<string, LucideIcon | React.ComponentType<{ className?: string }>> = {
  roster: LayoutGrid,
  panchang: MoonCrescentIcon,
  cockpit: Gauge,
  'ai-console': SlidersHorizontal,
  observatory: ChartColumn,
  audit: FileSearch,
  performance: ChartColumn,
  admin: Settings2,
}

export function MobileNavSheet({ user, profile }: MobileNavSheetProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [informationOpen, setInformationOpen] = useState(
    pathname.startsWith('/information')
  )

  async function handleSignOut() {
    await fetch('/api/auth/session', { method: 'DELETE' }).catch(() => {})
    await firebaseSignOut(auth).catch(() => {})
    router.push('/login')
    router.refresh()
  }

  const effectiveRole = normalizeRole(profile.role)
  const visibleItems = visibleNavItems(effectiveRole, {
    aiMetering: process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED === 'true',
    aiConsoleByok: process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true',
  })
  const informationItems = visibleInformationNavItems(effectiveRole)
  const informationActive = pathname.startsWith('/information')

  const userInitial = (user.name?.[0] ?? user.email?.[0] ?? 'U').toUpperCase()

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        aria-label="Open navigation menu"
        className="folio-nav-control flex w-11 shrink-0 items-center justify-center rounded md:hidden"
      >
        <MenuIcon className="size-5" aria-hidden="true" />
      </SheetTrigger>
      <SheetContent
        side="left"
        className="folio-nav-surface w-[min(17rem,100vw)] overflow-y-auto p-0 motion-reduce:transition-none"
      >
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <nav
          aria-label="Primary navigation"
          className="flex min-h-full flex-col items-start gap-1 px-3 py-3"
        >
          <Link
            href="/dashboard"
            aria-label="MARSYS-JIS — go to Jātakas"
            onClick={() => setOpen(false)}
            className="folio-nav-control mb-2 inline-flex items-center rounded px-2"
          >
            <Sigil size={28} />
          </Link>
          {visibleItems.map(({ key, href, label }) => {
            const Icon = NAV_ICONS[key]
            const isActive = isNavItemActive(key, href, pathname)
            return (
              <Link
                key={key}
                href={href}
                aria-current={isActive ? (pathname === href ? 'page' : 'location') : undefined}
                onClick={() => setOpen(false)}
                className="folio-nav-control flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium"
              >
                <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
                <span className="[overflow-wrap:anywhere]">{label}</span>
              </Link>
            )
          })}

          <div className="mt-auto w-full pt-2">
            {informationItems.length > 0 && (
              <div className="mb-2 w-full border-b border-[var(--folio-divider)] pb-2">
                <button
                  type="button"
                  aria-label="Information"
                  aria-expanded={informationOpen}
                  aria-controls={informationOpen ? 'mobile-information-menu' : undefined}
                  onClick={() => setInformationOpen((open) => !open)}
                  data-current={informationActive}
                  className="folio-nav-control flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium"
                >
                  <Info className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
                  <span className="flex-1 text-left">Information</span>
                  <ChevronDown
                    aria-hidden="true"
                    className={cn(
                      'h-3.5 w-3.5 transition-transform',
                      informationOpen && 'rotate-180'
                    )}
                  />
                </button>

                {informationOpen && (
                  <div
                    id="mobile-information-menu"
                    role="group"
                    aria-label="Information menu"
                    className="mt-1 pl-4"
                  >
                    {informationItems.map(({ href, label }) => {
                      const isActive = pathname.startsWith(href)
                      return (
                        <Link
                          key={href}
                          href={href}
                          aria-label={label}
                          aria-current={isActive ? (pathname === href ? 'page' : 'location') : undefined}
                          onClick={() => setOpen(false)}
                          className="folio-nav-control flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium"
                        >
                          <Map className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                          <span>{label}</span>
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )}

            <div className="flex w-full flex-wrap items-center gap-2 px-2 py-2">
              <span aria-hidden="true" className="grid size-8 shrink-0 place-items-center rounded-full border border-[var(--folio-boundary)] bg-[var(--folio-selected)] text-sm font-semibold">
                {userInitial}
              </span>
              <span className="folio-nav-identity flex-1 text-sm">
                {user.email ?? user.name}
              </span>
              <button
                type="button"
                onClick={handleSignOut}
                className="folio-nav-control rounded px-2 text-sm"
              >
                Sign out
              </button>
            </div>
          </div>
        </nav>
      </SheetContent>
    </Sheet>
  )
}
