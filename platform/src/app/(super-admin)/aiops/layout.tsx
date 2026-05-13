import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AppShell } from '@/components/shared/AppShell'
import { AiopsTabs } from '@/lib/components/aiops/AiopsTabs'

export const metadata: Metadata = {
  title: 'AIOps — MARSYS-JIS',
}

export default async function AiopsLayout({
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
        { label: 'AIOps', href: '/aiops', current: false },
      ]}
    >
      <div className="flex h-full min-h-0 flex-col">
        <AiopsTabs />
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </AppShell>
  )
}
