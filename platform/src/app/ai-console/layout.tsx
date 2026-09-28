import type { Metadata } from 'next'
import { notFound, redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getFlag } from '@/lib/config'
import { AppShell } from '@/components/shared/AppShell'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { BuildHeader } from '@/components/build/BuildHeader'

export const metadata: Metadata = {
  title: 'AI Console — MARSYS-JIS',
}

export default async function AiConsoleLayout({ children }: { children: React.ReactNode }) {
  const ctx = await getServerUserWithProfile()
  if (!ctx || ctx.profile.status !== 'active') redirect('/login')
  if (!getFlag('AI_CONSOLE_BYOK')) notFound()

  return (
    <ZoneRoot zone="ink">
      <AppShell
        user={ctx.user}
        profile={ctx.profile}
        breadcrumb={ctx.profile.role === 'super_admin'
          ? [{ label: 'Cockpit', href: '/cockpit' }, { label: 'AI Console', current: true }]
          : [{ label: 'AI Console', current: true }]}
      >
        {ctx.profile.role === 'super_admin' && <BuildHeader showAiConsole />}
        {children}
      </AppShell>
    </ZoneRoot>
  )
}
