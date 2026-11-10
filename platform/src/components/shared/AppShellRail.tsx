'use client'

import { useState } from 'react'
import type React from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { signOut as firebaseSignOut } from 'firebase/auth'
import { auth } from '@/lib/firebase/client'
import { Logo } from '@/components/brand/Logo'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import {
  LayoutGrid,
  Gauge,
  FileSearch,
  ChartColumn,
  ChevronDown,
  Info,
  Map,
  Settings2,
  SlidersHorizontal,
  type LucideIcon,
} from 'lucide-react'
import {
  normalizeRole,
  isNavItemActive,
  visibleNavItems,
  visibleInformationNavItems,
} from '@/components/nav/role-gates'
import {
  motion,
  AnimatePresence,
  useReducedMotion,
} from 'framer-motion'

// Lunar crescent SVG icon for Panchang nav entry — gold tint matching brand #fce29a
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

interface AppShellRailProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'guest'; status?: string }
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

export function AppShellRail({ user, profile }: AppShellRailProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [hovered, setHovered] = useState(false)
  const [focusWithin, setFocusWithin] = useState(false)
  const expanded = hovered || focusWithin
  const [informationOpen, setInformationOpen] = useState(
    pathname.startsWith('/information')
  )
  const reducedMotion = useReducedMotion()

  async function handleSignOut() {
    await fetch('/api/auth/session', { method: 'DELETE' }).catch(() => {})
    await firebaseSignOut(auth).catch(() => {})
    router.push('/login')
    router.refresh()
  }

  // Normalize legacy 'client' → 'guest' (per Unit 2c) before role-gating.
  const effectiveRole = normalizeRole(profile.role)
  const visibleItems = visibleNavItems(effectiveRole, {
    aiMetering: process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED === 'true',
    aiConsoleByok: process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true',
  })
  const informationItems = visibleInformationNavItems(effectiveRole)
  const informationActive = pathname.startsWith('/information')

  const userInitial = (
    user.name?.[0] ?? user.email?.[0] ?? 'U'
  ).toUpperCase()

  const roleLabel: Record<string, string> = {
    super_admin: 'Super Admin',
    admin: 'Admin',
    client: 'Client',
  }

  const springTransition = reducedMotion
    ? { duration: 0 }
    : { type: 'spring' as const, stiffness: 380, damping: 32 }

  const labelTransition = reducedMotion
    ? { duration: 0 }
    : { duration: 0.15 }

  return (
    <motion.nav
      aria-label="Primary navigation"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setFocusWithin(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setFocusWithin(false)
      }}
      animate={{ width: expanded ? 176 : 56 }}
      transition={springTransition}
      className="folio-nav-surface folio-nav-rail absolute inset-y-0 left-0 z-50 hidden flex-col items-start overflow-x-hidden overflow-y-auto border-r py-3 md:flex"
    >
      {/* Logo — links to Jātakas */}
      <Link
        href="/dashboard"
        aria-label="MARSYS-JIS — go to Jātakas"
        className="folio-nav-control mb-4 flex w-full shrink-0 items-center gap-2.5 px-2.5"
      >
        <Logo size="sm" className="shrink-0" priority />
        <AnimatePresence>
          {expanded && (
            <motion.span
              key="wordmark"
              initial={reducedMotion ? {} : { opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={reducedMotion ? {} : { opacity: 0, x: -6 }}
              transition={labelTransition}
              className="truncate folio-nav-wordmark text-sm font-semibold leading-none"
            >
              MARSYS-JIS
            </motion.span>
          )}
        </AnimatePresence>
      </Link>

      {/* Nav links */}
      <div className="relative flex flex-1 flex-col gap-0.5 w-full px-2">
        {visibleItems.map(({ key, href, label }, index) => {
          const Icon = NAV_ICONS[key]
          const isActive = isNavItemActive(key, href, pathname)
          return (
            <motion.div
              key={key}
              whileHover={reducedMotion ? {} : { x: 2 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              className="relative w-full"
            >
              <Link
                href={href}
                aria-label={label}
                aria-current={isActive ? (pathname === href ? 'page' : 'location') : undefined}
                className="folio-nav-control relative flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium"
              >
                <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
                <AnimatePresence>
                  {expanded && (
                    <motion.span
                      key={`label-${href}`}
                      initial={reducedMotion ? {} : { opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={reducedMotion ? {} : { opacity: 0, x: -6 }}
                      transition={reducedMotion ? { duration: 0 } : { duration: 0.12, delay: index * 0.025 }}
                      className="truncate tracking-wide"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            </motion.div>
          )
        })}
      </div>

      {/* Bottom navigation — Information stays immediately above the user menu. */}
      <div className="w-full shrink-0 space-y-1 px-2">
        {informationItems.length > 0 && (
          <div className="w-full">
            <div className="relative w-full">
              <button
                type="button"
                aria-label="Information"
                aria-expanded={expanded && informationOpen}
                aria-controls={expanded && informationOpen ? 'app-shell-information-menu' : undefined}
                data-current={informationActive}
                onClick={() => setInformationOpen((open) => !open)}
                className="folio-nav-control relative flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium"
              >
                <Info className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
                <AnimatePresence>
                  {expanded && (
                    <motion.span
                      key="information-label"
                      initial={reducedMotion ? {} : { opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={reducedMotion ? {} : { opacity: 0, x: -6 }}
                      transition={labelTransition}
                      className="flex min-w-0 flex-1 items-center justify-between"
                    >
                      <span className="truncate tracking-wide">Information</span>
                      <ChevronDown
                        aria-hidden="true"
                        className={cn(
                          'h-3.5 w-3.5 shrink-0 transition-transform',
                          informationOpen && 'rotate-180'
                        )}
                      />
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            </div>

            <AnimatePresence initial={false}>
              {expanded && informationOpen && (
                <motion.div
                  id="app-shell-information-menu"
                  role="group"
                  aria-label="Information menu"
                  initial={reducedMotion ? {} : { height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={reducedMotion ? {} : { height: 0, opacity: 0 }}
                  transition={reducedMotion ? { duration: 0 } : { duration: 0.16 }}
                  className="overflow-hidden pb-1 pl-3 pt-0.5"
                >
                  {informationItems.map(({ href, label }) => {
                    const isActive = pathname.startsWith(href)
                    return (
                      <Link
                        key={href}
                        href={href}
                        aria-label={label}
                        aria-current={isActive ? (pathname === href ? 'page' : 'location') : undefined}
                        className="folio-nav-control flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium"
                      >
                        <Map className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                        <span className="truncate">{label}</span>
                      </Link>
                    )
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Avatar + sign-out */}
        <DropdownMenu>
          <DropdownMenuTrigger
            aria-label="User menu"
            className="folio-nav-control flex w-full items-center gap-3 rounded-md px-1 text-sm font-medium"
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full ring-1 ring-[var(--folio-boundary)] text-center text-[11px] font-semibold leading-7">
              {userInitial}
            </span>
            <AnimatePresence>
              {expanded && (
                <motion.span
                  key="user-info"
                  initial={reducedMotion ? {} : { opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={reducedMotion ? {} : { opacity: 0, x: -6 }}
                  transition={labelTransition}
                  className="flex min-w-0 flex-col items-start"
                >
                  <span className="truncate text-sm font-medium leading-tight">
                    {user.name?.split(' ')[0] ?? user.email?.split('@')[0]}
                  </span>
                  <span className="folio-nav-identity truncate text-sm leading-tight">
                    {roleLabel[profile.role] ?? profile.role}
                  </span>
                </motion.span>
              )}
            </AnimatePresence>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="right" align="end" className="folio-nav-surface max-w-[min(24rem,85vw)]">
            <div className="folio-nav-identity px-2 py-1.5 text-sm">
              {user.email ?? user.name}
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="folio-nav-control" onClick={handleSignOut}>Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </motion.nav>
  )
}
