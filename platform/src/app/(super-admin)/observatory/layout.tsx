import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getFlag } from '@/lib/config'
import { AppShell } from '@/components/shared/AppShell'
import { ObservatorySubNav } from '@/components/observatory/ObservatorySubNav'
import { ObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { BuildHeader } from '@/components/build/BuildHeader'

export const metadata: Metadata = { title: 'Observatory — MARSYS-JIS' }

export default async function ObservatorySectionLayout({ children }: { children: React.ReactNode }) {
  const ctx = await getServerUserWithProfile()
  if (!ctx || ctx.profile.status !== 'active') redirect('/login')
  const admin = ctx.profile.role === 'super_admin'
  return (
    <AppShell user={ctx.user} profile={ctx.profile} breadcrumb={admin
      ? [{ label: 'Cockpit', href: '/cockpit' }, { label: 'Observatory', href: '/observatory', current: true }]
      : [{ label: 'Observatory', href: '/observatory', current: true }]}>
      <div className="min-h-full bg-[#0a0806] text-[#e8dfc9]" style={{ fontFamily: 'var(--font-sans), sans-serif' }}>
        {admin && <BuildHeader showAiConsole={getFlag('AI_CONSOLE_BYOK')} />}
        <ObservatoryScope admin={admin} userId={ctx.user.uid}>
          <ObservatorySubNav />
          {children}
        </ObservatoryScope>
      </div>
    </AppShell>
  )
}
