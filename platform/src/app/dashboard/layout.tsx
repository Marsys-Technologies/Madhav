import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { JourneyShell } from '@/components/journey1/JourneyShell'

export const metadata: Metadata = {
  title: 'Jātakas — MARSYS-JIS',
}

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.status !== 'active') redirect('/login')

  return <JourneyShell user={ctx.user} role={ctx.profile.role}>{children}</JourneyShell>
}
