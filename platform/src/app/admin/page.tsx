import { Suspense } from 'react'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { redirect } from 'next/navigation'
import { AdminClient } from '@/components/admin/AdminClient'

// The layout already gates super_admin + active. We re-fetch here just to pick
// up the current uid for the "you" badge in UsersTable.
export default async function AdminPage() {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  return (
    <Suspense>
      <AdminClient currentUserId={ctx.user.uid} />
    </Suspense>
  )
}
