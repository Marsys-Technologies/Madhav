'use client'

import { useState } from 'react'
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

  const roleLabel: Record<string, string> = {
    super_admin: 'Super Admin',
    admin: 'Admin',
    client: 'Client',
  }

  return (
    <nav
      aria-label="Primary navigation"
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      onFocus={() => setExpanded(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setExpanded(false)
      }}
      className={cn(
        'absolute inset-y-0 left-0 z-50 hidden flex-col items-start border-r py-3 md:flex',
        'overflow-hidden transition-[width] duration-150 ease-in-out',
        expanded ? 'w-44' : 'w-14'
      )}
      style={{
        background: 'oklch(0.05 0.008 68 / 0.72)',
        backdropFilter: 'blur(16px) saturate(140%)',
        WebkitBackdropFilter: 'blur(16px) saturate(140%)',
        borderRightColor: 'color-mix(in oklch, var(--brand-gold) 14%, transparent)',
      }}
    >
      {/* Logo — links to Roster */}
      <Link
        href="/dashboard"
        aria-label="MARSYS-JIS — go to Roster"
        className="mb-4 flex w-full items-center gap-2.5 px-3"
      >
        <Logo size="sm" className="shrink-0" />
        {expanded && (
          <span className="flex min-w-0 flex-col items-start">
            <span className="truncate text-[13px] font-semibold leading-tight tracking-wide" style={{ color: 'var(--brand-gold-cream)' }}>
              MARSYS
            </span>
            <span className="truncate text-[10px] font-medium leading-tight tracking-[0.12em]" style={{ color: 'rgba(212,175,55,0.55)' }}>
              JIS
            </span>
          </span>
        )}
      </Link>

      {/* Nav links */}
      <div className="flex flex-1 flex-col gap-0.5 w-full px-2">
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
                'flex h-10 w-full items-center gap-3 rounded-md px-2 text-xs font-medium transition-colors',
                isActive
                  ? 'bg-[rgba(212,175,55,0.14)] border border-[rgba(212,175,55,0.28)] text-[var(--brand-gold)]'
                  : 'border border-transparent text-[rgba(212,175,55,0.55)] hover:bg-[rgba(212,175,55,0.08)] hover:text-[var(--brand-gold)]'
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {expanded && <span className="truncate tracking-wide">{label}</span>}
            </Link>
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
          {expanded && (
            <span className="flex min-w-0 flex-col items-start">
              <span className="truncate text-[11px] font-medium leading-tight">
                {user.name?.split(' ')[0] ?? user.email?.split('@')[0]}
              </span>
              <span className="truncate text-[10px] leading-tight" style={{ color: 'rgba(212,175,55,0.45)' }}>
                {roleLabel[profile.role] ?? profile.role}
              </span>
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
      </div>
    </nav>

  )
}
