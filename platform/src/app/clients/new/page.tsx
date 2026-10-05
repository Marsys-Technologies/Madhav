import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { JourneyShell } from '@/components/journey1/JourneyShell'
import { NewClientForm } from '@/components/clients/NewClientForm'

// Force server-side render on every request so Next never bakes a stale static
// document for this route after a deploy. /clients/new is an authenticated
// form page with no static content — there is no value in pre-rendering it.
export const dynamic = 'force-dynamic'

export const metadata = {
  title: 'New Chart — Madhav',
}

export default async function NewClientPage() {
  const ctx=await getServerUserWithProfile()
  if(!ctx||ctx.profile.status!=='active')redirect('/login')
  if(ctx.profile.role!=='super_admin')redirect('/dashboard')
  return <JourneyShell user={ctx.user} role={ctx.profile.role}><NewClientForm /></JourneyShell>
}
