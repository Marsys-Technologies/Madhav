'use client'

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

interface AppShellRailProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'admin' | 'client'; status?: string }
}

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Roster', roles: ['super_admin', 'admin', 'client'] as const },
  { href: '/cockpit', label: 'Cockpit', roles: ['super_admin'] as const },
  { href: '/audit', label: 'Audit', roles: ['super_admin'] as const },
  { href: '/aiops', label: 'AIOps', roles: ['super_admin'] as const },
  { href: '/performance', label: 'Perf', roles: ['super_admin'] as const },
  { href: '/admin', label: 'Admin', roles: ['super_admin', 'admin'] as const },
] satisfies { href: string; label: string; roles: readonly string[] }[]

export function AppShellRail({ user, profile }: AppShellRailProps) {
  const pathname = usePathname()
  const router = useRouter()

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
      className="hidden h-full w-14 shrink-0 flex-col items-center border-r border-sidebar-border bg-sidebar py-3 md:flex"
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
        {visibleItems.map(({ href, label }) => {
          const isActive = href === '/dashboard'
            ? pathname === '/dashboard' || pathname === '/'
            : pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              aria-label={label}
              className={cn(
                'flex h-11 w-11 items-center justify-center rounded text-xs font-medium transition-colors',
                isActive
                  ? 'bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]'
                  : 'text-[rgba(212,175,55,0.28)] hover:bg-[rgba(212,175,55,0.08)] hover:text-[#d4af37]'
              )}
            >
              {label.slice(0, 2)}
            </Link>
          )
        })}
      </div>

      {/* Avatar + sign-out */}
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="User menu"
          className="grid h-11 w-11 place-items-center rounded-full border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.07)] text-xs font-medium text-[rgba(212,175,55,0.6)] transition-colors hover:bg-[rgba(212,175,55,0.12)]"
        >
          {userInitial}
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
