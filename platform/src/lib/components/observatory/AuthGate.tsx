import { FEATURE_FLAGS } from '@/lib/config/feature_flags'
import 'server-only'
import { getFlag } from '@/lib/config'
import { getServerUserWithProfile } from '@/lib/auth/access-control'

export async function AuthGate({ children }: { children: React.ReactNode }) {
  if (!getFlag(FEATURE_FLAGS.observatory)) {
    return (
      <main role="alert" data-testid="observatory-disabled" className="p-8">
        <h1 className="text-xl font-semibold">Observatory is disabled</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Set <code>MARSYS_FLAG_OBSERVATORY_ENABLED=true</code> in the environment to enable
          this surface.
        </p>
      </main>
    )
  }

  const ctx = await getServerUserWithProfile()
  const isSuperAdmin =
    ctx?.profile.role === 'super_admin' && ctx.profile.status === 'active'
  if (!isSuperAdmin) {
    return (
      <main role="alert" data-testid="observatory-unauthorized" className="p-8">
        <h1 className="text-xl font-semibold">Unauthorized</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The Observatory is restricted to super-admin accounts.
        </p>
      </main>
    )
  }

  return <>{children}</>
}
