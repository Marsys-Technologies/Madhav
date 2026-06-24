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
  Bot,
  ChartColumn,
  Settings2,
  type LucideIcon,
} from 'lucide-react'
import { normalizeRole } from '@/components/nav/role-gates'
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

interface NavItem {
  href: string
  label: string
  icon: LucideIcon | React.ComponentType<{ className?: string }>
  roles: readonly string[]
}

interface AppShellRailProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'guest'; status?: string }
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard',   label: 'Jātakas',     icon: LayoutGrid,       roles: ['super_admin', 'guest'] },
  { href: '/panchang',    label: 'Panchang',    icon: MoonCrescentIcon, roles: ['super_admin', 'guest'] },
  { href: '/cockpit',     label: 'Cockpit',     icon: Gauge,            roles: ['super_admin'] },
  { href: '/audit',       label: 'Audit',       icon: FileSearch,       roles: ['super_admin'] },
  { href: '/aiops',       label: 'AIOps',       icon: Bot,              roles: ['super_admin'] },
  { href: '/performance', label: 'Performance', icon: ChartColumn,      roles: ['super_admin'] },
  { href: '/admin',       label: 'Admin',       icon: Settings2,        roles: ['super_admin'] },
]

export function AppShellRail({ user, profile }: AppShellRailProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [expanded, setExpanded] = useState(false)
  const reducedMotion = useReducedMotion()

  async function handleSignOut() {
    await fetch('/api/auth/session', { method: 'DELETE' }).catch(() => {})
    await firebaseSignOut(auth).catch(() => {})
    router.push('/login')
    router.refresh()
  }

  // Normalize legacy 'client' → 'guest' (per Unit 2c) before role-gating.
  const effectiveRole = normalizeRole(profile.role)
  const visibleItems = NAV_ITEMS.filter((item) =>
    (item.roles as readonly string[]).includes(effectiveRole)
  )

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
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      onFocus={() => setExpanded(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setExpanded(false)
      }}
      animate={{ width: expanded ? 176 : 56 }}
      transition={springTransition}
      className="absolute inset-y-0 left-0 z-50 hidden flex-col items-start py-3 md:flex overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, rgba(6,6,8,0.30), rgba(2,2,4,0.20))',
        backdropFilter: 'blur(10px) saturate(125%)',
        WebkitBackdropFilter: 'blur(10px) saturate(125%)',
        borderRight: '1px solid rgba(212,175,55,0.14)',
        boxShadow: 'inset 0 1px 0 rgba(255,240,200,0.06), 8px 0 28px rgba(0,0,0,0.4)',
      }}
    >
      {/* Logo — links to Jātakas */}
      <Link
        href="/dashboard"
        aria-label="MARSYS-JIS — go to Jātakas"
        className="mb-4 flex w-full items-center gap-2.5 px-3"
      >
        <Logo size="sm" className="shrink-0" />
        <AnimatePresence>
          {expanded && (
            <motion.span
              key="wordmark"
              initial={reducedMotion ? {} : { opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={reducedMotion ? {} : { opacity: 0, x: -6 }}
              transition={labelTransition}
              className="truncate font-serif text-[13px] font-medium leading-none"
              style={{ color: 'var(--brand-gold-cream)' }}
            >
              MARSYS-JIS
            </motion.span>
          )}
        </AnimatePresence>
      </Link>

      {/* Nav links */}
      <div className="relative flex flex-1 flex-col gap-0.5 w-full px-2">
        {visibleItems.map(({ href, label, icon: Icon }, index) => {
          const isActive = href === '/dashboard'
            ? pathname === '/dashboard' || pathname === '/'
            : pathname.startsWith(href)
          return (
            <motion.div
              key={href}
              whileHover={reducedMotion ? {} : { x: 2 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              className="relative w-full"
            >
              {isActive && (
                <motion.div
                  layoutId="rail-active"
                  transition={reducedMotion ? { duration: 0 } : { type: 'spring', stiffness: 380, damping: 32 }}
                  className="absolute inset-0 rounded-lg"
                  style={{
                    background: 'rgba(212,175,55,0.14)',
                    boxShadow: 'inset 0 0 0 1px rgba(212,175,55,0.28), inset 0 0 24px rgba(212,175,55,0.08)',
                  }}
                />
              )}
              <Link
                href={href}
                aria-label={label}
                className={cn(
                  'relative flex h-10 w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors',
                  isActive
                    ? 'text-[var(--brand-gold)]'
                    : 'text-[rgba(212,175,55,0.50)] hover:bg-[rgba(212,175,55,0.07)] hover:text-[var(--brand-gold)]'
                )}
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

      {/* Avatar + sign-out */}
      <div className="w-full px-2">
        <DropdownMenu>
          <DropdownMenuTrigger
            aria-label="User menu"
            className="flex h-10 w-full items-center gap-3 rounded-md border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.06)] px-2 text-xs font-medium text-[rgba(212,175,55,0.70)] transition-colors hover:border-[rgba(212,175,55,0.35)] hover:bg-[rgba(212,175,55,0.12)] hover:text-[var(--brand-gold)]"
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full ring-1 ring-[rgba(212,175,55,0.35)] text-center text-[11px] font-semibold leading-7">
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
                  <span className="truncate text-[11px] font-medium leading-tight">
                    {user.name?.split(' ')[0] ?? user.email?.split('@')[0]}
                  </span>
                  <span className="truncate text-[10px] leading-tight" style={{ color: 'rgba(212,175,55,0.45)' }}>
                    {roleLabel[profile.role] ?? profile.role}
                  </span>
                </motion.span>
              )}
            </AnimatePresence>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="right" align="end">
            <div className="px-2 py-1.5 text-xs text-muted-foreground">
              {user.email ?? user.name}
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut}>Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </motion.nav>
  )
}
