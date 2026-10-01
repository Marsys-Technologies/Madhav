import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getFlag } from '@/lib/config'
import { AppShell } from '@/components/shared/AppShell'
import { BuildHeader } from '@/components/build/BuildHeader'
import { FreshnessIndicator } from '@/components/build/FreshnessIndicator'
import { fetchBuildState } from '@/lib/build/dataSource'

export default async function CockpitLayout({ children }: { children: React.ReactNode }) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.status !== 'active') redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')

  // Best-effort: if GCS is unavailable, freshness indicator is simply omitted
  let generatedAt: string | null = null
  try {
    const state = await fetchBuildState()
    generatedAt = state.generated_at
  } catch {
    // silently skip
  }

  return (
    <AppShell
      user={ctx.user}
      profile={ctx.profile}
      breadcrumb={[{ label: 'Cockpit', current: true }]}
    >
      <div className="min-h-full bg-[#0a0806]">
        <BuildHeader showAiConsole={getFlag('AI_CONSOLE_BYOK')} />
        {children}
        {generatedAt && (
          <footer className="flex justify-end border-t border-[#382b18] px-4 py-2">
            <FreshnessIndicator generatedAt={generatedAt} />
          </footer>
        )}
      </div>
    </AppShell>
  )
}
