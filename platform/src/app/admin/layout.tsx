import { Suspense } from 'react'
import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { JourneyShell } from '@/components/journey1/JourneyShell'
import { ObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { AdminNavigation } from '@/components/admin/AdminNavigation'
import { AdminQueryBoundary } from '@/components/admin/AdminQueryBoundary'
import '@/app/journey1.css'
import '@/app/account/account.css'
import './administration.css'

export const metadata: Metadata = {
  title: 'Admin — MARSYS-JIS',
}

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
  if (ctx.profile.status !== 'active') redirect('/login')

  return (
    <AdminQueryBoundary key={`${ctx.user.uid}:${ctx.profile.role}:${ctx.profile.status}`}>
    <JourneyShell user={ctx.user} role={ctx.profile.role}>
      <ObservatoryScope key={ctx.user.uid} admin userId={ctx.user.uid}>
        <div className="j5-account j6-administration">
          <Suspense><AdminNavigation /></Suspense>
          {children}
        </div>
      </ObservatoryScope>
    </JourneyShell>
    </AdminQueryBoundary>
  )
}
