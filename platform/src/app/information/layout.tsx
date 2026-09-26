import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AppShell } from '@/components/shared/AppShell'

export default async function InformationLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.status !== 'active') redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')

  return (
    <AppShell
      user={ctx.user}
      profile={ctx.profile}
      breadcrumb={[{ label: 'Information', current: true }]}
    >
      {children}
    </AppShell>
  )
}
