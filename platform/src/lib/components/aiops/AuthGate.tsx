import 'server-only'
import { getFlag } from '@/lib/config'
import { getServerUserWithProfile } from '@/lib/auth/access-control'

export async function AuthGate({ children }: { children: React.ReactNode }) {
  if (!getFlag('OBSERVATORY_ENABLED')) {
    return (
      <main role="alert" data-testid="aiops-disabled" className="p-8">
        <h1 className="text-xl font-semibold">AIOps is disabled</h1>
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
      <main role="alert" data-testid="aiops-unauthorized" className="p-8">
        <h1 className="text-xl font-semibold">Unauthorized</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          AIOps is restricted to super-admin accounts.
        </p>
      </main>
    )
  }

  return <>{children}</>
}
