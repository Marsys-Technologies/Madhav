'use client'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { PageTitle } from '@/components/journey1/Titles'
import type { AdminUser, AdminChartGrant } from './types'
async function read<T>(url:string):Promise<T> { const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw Error('User evidence unavailable');return response.json() }
export function UserDetails({selectedId}:{selectedId:string}) {
  const {userId} = useObservatoryScope()
  const state = useQuery({queryKey:['admin',userId,'user-details',selectedId],queryFn:()=>read<{users:AdminUser[]}>('/api/admin/users')})
  const grants = useQuery({queryKey:['admin',userId,'user-chart-grants',selectedId],queryFn:()=>read<{charts:AdminChartGrant[]}>(`/api/admin/users/${encodeURIComponent(selectedId)}/chart-grants`)})
  const user = state.data?.users.find(user=>user.id===selectedId)
  return <div className="j6-evidence"><PageTitle name="adminUsers" /><p className="j1-note">Selected user · account record and chart access. Viewing this record does not change their account.</p>
    {state.isPending ? <p role="status">Loading user…</p> : state.isError ? <p role="alert">User record unavailable.</p> : !user ? <p>User not found.</p> : <>
      <section className="j5-panel"><h2>{user.name ?? user.username ?? 'Member'}</h2><dl>{(['username','email','role','status','created_at','approved_at'] as const).map(key=><div style={{display:'contents'}} key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{user[key] ?? 'Not reported'}</dd></div>)}</dl></section>
      <div className="j6-links"><Link href={`/admin/activity?scope=user&userId=${encodeURIComponent(selectedId)}`}>View selected user activity</Link><Link href="/admin?tab=users">Manage user account</Link>{process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true' && <Link href="/admin?tab=ai-access">Review AI product grants</Link>}<Link href="/admin?tab=charts">Manage chart grants</Link></div>
      <section className="j5-panel"><h2>Charts and access</h2>{grants.isPending ? <p>Loading chart access…</p> : grants.isError ? <p role="alert">Chart access unavailable.</p> : grants.data?.charts.filter(chart=>chart.is_own||chart.granted).map(chart=><p key={chart.id}><Link href={`/clients/${chart.id}`}>{chart.subject_name ?? chart.id}</Link> · {chart.is_own ? 'Owner' : 'Granted access'}</p>)}{grants.data && !grants.isError && !grants.data.charts.some(chart=>chart.is_own||chart.granted) && <p>No chart ownership or grants recorded.</p>}</section>
    </>}
  </div>
}
