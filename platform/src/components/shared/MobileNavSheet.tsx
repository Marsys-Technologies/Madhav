'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { signOut as firebaseSignOut } from 'firebase/auth'
import { MenuIcon, LayoutGrid, Gauge, FileSearch, Bot, ChartColumn, Settings2, type LucideIcon } from 'lucide-react'
import { auth } from '@/lib/firebase/client'
import { Sigil } from '@/components/brand/Sigil'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import type React from 'react'

interface MobileNavSheetProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'admin' | 'guest'; status?: string }
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

const NAV_ITEMS: {
  href: string
  label: string
  icon: LucideIcon | React.ComponentType<{ className?: string }>
  roles: readonly string[]
}[] = [
  { href: '/dashboard', label: 'Jātakas',    icon: LayoutGrid,  roles: ['super_admin', 'admin', 'guest'] },
  { href: '/panchang',  label: 'Panchang',   icon: MoonCrescentIcon, roles: ['super_admin', 'admin', 'guest'] },
  { href: '/cockpit',   label: 'Cockpit',    icon: Gauge,       roles: ['super_admin'] },
  { href: '/audit',     label: 'Audit',      icon: FileSearch,  roles: ['super_admin'] },
  { href: '/aiops',     label: 'AIOps',      icon: Bot,         roles: ['super_admin'] },
  { href: '/performance', label: 'Performance', icon: ChartColumn, roles: ['super_admin'] },
  { href: '/admin',     label: 'Admin',      icon: Settings2,   roles: ['super_admin', 'admin'] },
]

export function MobileNavSheet({ user, profile }: MobileNavSheetProps) {
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

  const userInitial = (user.name?.[0] ?? user.email?.[0] ?? 'U').toUpperCase()

  return (
    <Sheet>
      <SheetTrigger
        aria-label="Open navigation menu"
        className="flex h-10 w-10 items-center justify-center rounded text-muted-foreground hover:text-foreground md:hidden"
      >
        <MenuIcon className="size-5" aria-hidden="true" />
      </SheetTrigger>
      <SheetContent
        side="left"
        className="w-64 p-0"
        style={{
          background: 'linear-gradient(180deg, rgba(6,6,8,0.72), rgba(2,2,4,0.60))',
          backdropFilter: 'blur(10px) saturate(125%)',
          WebkitBackdropFilter: 'blur(10px) saturate(125%)',
          borderRight: '1px solid rgba(212,175,55,0.14)',
        }}
      >
        <nav
          aria-label="Primary navigation"
          className="flex h-full flex-col items-start gap-1 px-3 py-4"
        >
          <Link
            href="/dashboard"
            aria-label="MARSYS-JIS — go to Jātakas"
            className="mb-4 ml-1 text-[var(--brand-gold)] transition-[filter] hover:drop-shadow-[0_0_6px_var(--brand-gold)]"
          >
            <Sigil size={28} />
          </Link>
          {visibleItems.map(({ href, label, icon: Icon }) => {
            const isActive =
              href === '/dashboard'
                ? pathname === '/dashboard' || pathname === '/'
                : pathname.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex h-10 w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors',
                  isActive
                    ? 'bg-[rgba(212,175,55,0.14)] text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_rgba(212,175,55,0.28),inset_0_0_24px_rgba(212,175,55,0.08)]'
                    : 'text-[rgba(212,175,55,0.50)] hover:bg-[rgba(212,175,55,0.07)] hover:text-[var(--brand-gold)]'
                )}
              >
                <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
                <span className="truncate">{label}</span>
              </Link>
            )
          })}
          <div className="mt-auto flex w-full items-center gap-3 px-3 py-2">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.06)] text-xs font-medium text-[var(--brand-gold)]">
              {userInitial}
            </span>
            <span className="flex-1 truncate text-xs text-[rgba(212,175,55,0.55)]">
              {user.email ?? user.name}
            </span>
            <button
              onClick={handleSignOut}
              className="text-xs text-[rgba(212,175,55,0.45)] hover:text-[var(--brand-gold)]"
            >
              Sign out
            </button>
          </div>
        </nav>
      </SheetContent>
    </Sheet>
  )
}
