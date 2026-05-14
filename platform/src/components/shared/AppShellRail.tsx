'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { signOut as firebaseSignOut } from 'firebase/auth'
import { auth } from '@/lib/firebase/client'
import { Sigil } from '@/components/brand/Sigil'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import {
  Users,
  Gauge,
  FileText,
  Bot,
  ChartColumn,
  Settings2,
  type LucideIcon,
} from 'lucide-react'

interface AppShellRailProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'admin' | 'client'; status?: string }
}

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon; roles: readonly string[] }[] = [
  { href: '/dashboard',   label: 'Roster',      icon: Users,       roles: ['super_admin', 'admin', 'client'] },
  { href: '/cockpit',     label: 'Cockpit',     icon: Gauge,       roles: ['super_admin'] },
  { href: '/audit',       label: 'Audit',       icon: FileText,    roles: ['super_admin'] },
  { href: '/aiops',       label: 'AIOps',       icon: Bot,         roles: ['super_admin'] },
  { href: '/performance', label: 'Performance', icon: ChartColumn, roles: ['super_admin'] },
  { href: '/admin',       label: 'Admin',       icon: Settings2,   roles: ['super_admin', 'admin'] },
]

export function AppShellRail({ user, profile }: AppShellRailProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [expanded, setExpanded] = useState(false)

  async function handleSignOut() {
    await fetch('/api/auth/session', { method: 'DELETE' }).catch(() => {})
    await firebaseSignOut(auth).catch(() => {})
    router.push('/login')
    router.refresh()
  }

  const visibleItems = NAV_ITEMS.filter((item) =>
    (item.roles as readonly string[]).includes(profile.role)
  )

  const userInitial = (
    user.name?.[0] ?? user.email?.[0] ?? 'U'
  ).toUpperCase()

  return (
    <nav
      aria-label="Primary navigation"
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      className={cn(
        'absolute inset-y-0 left-0 z-50 hidden flex-col items-center border-r border-sidebar-border bg-sidebar py-3 md:flex',
        'overflow-hidden transition-all duration-150 ease-in-out',
        expanded ? 'w-44' : 'w-14'
      )}
    >
      {/* Sigil — links to Roster */}
      <Link
        href="/dashboard"
        aria-label="MARSYS-JIS — go to Roster"
        className="mb-4 text-[var(--brand-gold)] transition-[filter] hover:drop-shadow-[0_0_6px_var(--brand-gold)]"
      >
        <Sigil size={28} />
      </Link>

      {/* Nav links */}
      <div className="flex flex-1 flex-col items-center gap-1">
        {visibleItems.map(({ href, label, icon: Icon }) => {
          const isActive = href === '/dashboard'
            ? pathname === '/dashboard' || pathname === '/'
            : pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              aria-label={label}
              className={cn(
                'flex h-11 w-full items-center gap-3 rounded px-3 text-xs font-medium transition-colors',
                isActive
                  ? 'bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]'
                  : 'text-[rgba(212,175,55,0.28)] hover:bg-[rgba(212,175,55,0.08)] hover:text-[#d4af37]'
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {expanded && <span className="truncate">{label}</span>}
            </Link>
          )
        })}
      </div>

      {/* Avatar + sign-out */}
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="User menu"
          className="flex h-11 w-full items-center gap-3 rounded-full border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.07)] px-3 text-xs font-medium text-[rgba(212,175,55,0.6)] transition-colors hover:bg-[rgba(212,175,55,0.12)]"
        >
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-center leading-7">
            {userInitial}
          </span>
          {expanded && (
            <span className="truncate text-xs">
              {user.name ?? user.email}
            </span>
          )}
        </DropdownMenuTrigger>
        <DropdownMenuContent side="right" align="end">
          <div className="px-2 py-1.5 text-xs text-muted-foreground">
            {user.email ?? user.name}
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleSignOut}>Sign out</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </nav>
  )
}
