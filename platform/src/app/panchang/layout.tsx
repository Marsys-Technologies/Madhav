import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AppShell } from '@/components/shared/AppShell'
import { ZoneRoot } from '@/components/shared/ZoneRoot'

export const metadata: Metadata = {
  title: 'Panchang — MARSYS-JIS',
}

export default async function PanchangLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.status !== 'active') redirect('/login')

  return (
    <ZoneRoot zone="ink">
      <AppShell
        user={ctx.user}
        profile={ctx.profile}
        breadcrumb={[{ label: 'Panchang', current: true }]}
      >
        {children}
      </AppShell>
    </ZoneRoot>
  )
}
