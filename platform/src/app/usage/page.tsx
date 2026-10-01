import { redirect,notFound } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { meteringEnabled } from '@/lib/metering/types'
import { AppShell } from '@/components/shared/AppShell'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { UsageDashboard } from '@/components/metering/UsageDashboard'
export const dynamic='force-dynamic'
export default async function UsagePage() {
 const ctx=await getServerUserWithProfile()
 if(!ctx||ctx.profile.status!=='active')redirect('/login')
 if(!meteringEnabled())notFound()
 return <ZoneRoot zone="ink"><AppShell user={ctx.user} profile={ctx.profile} breadcrumb={[{label:'My AI usage',current:true}]}><UsageDashboard/></AppShell></ZoneRoot>
}
