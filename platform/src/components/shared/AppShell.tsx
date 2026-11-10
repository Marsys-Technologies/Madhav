import type { ReactNode } from 'react'
import { AppShellRail } from './AppShellRail'
import { AppShellBreadcrumb, type BreadcrumbSegment } from './AppShellBreadcrumb'
import { MobileNavSheet } from './MobileNavSheet'

export type { BreadcrumbSegment }

interface AppShellProps {
  children?: ReactNode
  user: { uid: string; email?: string; name?: string }
  profile: { role: 'super_admin' | 'guest'; status?: string }
  breadcrumb?: BreadcrumbSegment[]
}

export function AppShell({ children, user, profile, breadcrumb = [] }: AppShellProps) {
  return (
    <div className="flex h-[100dvh] bg-background text-foreground">
      <a
        href="#main-content"
        className="folio-shell-skip sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded focus:bg-[var(--folio-panel)] focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-[var(--folio-ink)]"
      >
        Skip to main content
      </a>
      {/* Desktop sidebar rail — hidden on mobile. relative+w-14 gives the absolute nav a containing block; flex-stretch on the outer shell sets height to 100dvh. */}
      <div className="relative hidden w-14 shrink-0 md:block">
        <AppShellRail user={user} profile={profile} />
      </div>
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <AppShellBreadcrumb
          segments={breadcrumb}
          mobileNav={<MobileNavSheet user={user} profile={profile} />}
        />
        <main id="main-content" tabIndex={-1} className="page-ascend min-w-0 flex-1 overflow-auto motion-reduce:animate-none">{children}</main>
      </div>
    </div>
  )
}
