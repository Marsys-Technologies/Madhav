/**
 * Dev route group — server-side super-admin gate.
 * All routes under /dev/* require super_admin role.
 * This follows the same pattern as the (super-admin) route group layouts.
 */
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'

export const dynamic = 'force-dynamic'

export default async function DevLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
  if (ctx.profile.status !== 'active') redirect('/login')

  return <>{children}</>
}
