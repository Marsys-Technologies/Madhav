import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AppShell } from '@/components/shared/AppShell'

export const metadata: Metadata = {
  title: 'Performance Command Center — MARSYS-JIS',
}

export default async function PerformanceSectionLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
  if (ctx.profile.status !== 'active') redirect('/login')

  return (
    <AppShell
      user={ctx.user}
      profile={ctx.profile}
      breadcrumb={[
        { label: 'Roster', href: '/dashboard' },
        { label: 'Performance', href: '/performance', current: false },
      ]}
    >
      <div className="flex-1 overflow-auto">{children}</div>
    </AppShell>
  )
}
