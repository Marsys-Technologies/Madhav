'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { signOut as firebaseSignOut } from 'firebase/auth'
import { MenuIcon } from 'lucide-react'
import { auth } from '@/lib/firebase/client'
import { Sigil } from '@/components/brand/Sigil'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'

interface MobileNavSheetProps {
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'admin' | 'client'; status?: string }
}

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Roster',      roles: ['super_admin', 'admin', 'client'] as const },
  { href: '/panchang',  label: 'Panchang',    roles: ['super_admin', 'admin', 'client'] as const },
  { href: '/cockpit',   label: 'Cockpit',     roles: ['super_admin'] as const },
  { href: '/audit',     label: 'Audit',       roles: ['super_admin'] as const },
  { href: '/aiops',     label: 'AIOps',       roles: ['super_admin'] as const },
  { href: '/performance', label: 'Performance', roles: ['super_admin'] as const },
  { href: '/admin',     label: 'Admin',       roles: ['super_admin', 'admin'] as const },
] satisfies { href: string; label: string; roles: readonly string[] }[]

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
      <SheetContent side="left" className="w-64 bg-sidebar p-0">
        <nav
          aria-label="Primary navigation"
          className="flex h-full flex-col items-start gap-1 px-3 py-4"
        >
          <Link
            href="/dashboard"
            aria-label="MARSYS-JIS — go to Roster"
            className="mb-4 ml-1 text-[var(--brand-gold)] transition-[filter] hover:drop-shadow-[0_0_6px_var(--brand-gold)]"
          >
            <Sigil size={28} />
          </Link>
          {visibleItems.map(({ href, label }) => {
            const isActive =
              href === '/dashboard'
                ? pathname === '/dashboard' || pathname === '/'
                : pathname.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex h-10 w-full items-center rounded px-3 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                {label}
              </Link>
            )
          })}
          <div className="mt-auto flex w-full items-center gap-3 px-3 py-2">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-border bg-muted text-xs font-medium text-foreground">
              {userInitial}
            </span>
            <span className="flex-1 truncate text-xs text-muted-foreground">
              {user.email ?? user.name}
            </span>
            <button
              onClick={handleSignOut}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Sign out
            </button>
          </div>
        </nav>
      </SheetContent>
    </Sheet>
  )
}
