import {redirect} from 'next/navigation'
import {getServerUserWithProfile} from '@/lib/auth/access-control'

export type ActivitySearch = Record<string,string|string[]|undefined>
export function activityDestination(admin:boolean,view:'observatory'|'consumption',raw:ActivitySearch):string {
  const params=new URLSearchParams()
  for(const key of ['from','to','channel','purpose','connectionId','provider','model','aggregation']) {
    const value=raw[key]
    if(typeof value==='string')params.set(key,value)
  }
  if(admin){
    const target=typeof raw.userId==='string'?raw.userId:''
    const scope=typeof raw.scope==='string'?raw.scope:target?'user':'mine'
    params.set('scope',scope)
    if(scope==='user'&&target)params.set('userId',target)
  }
  const path=admin?(view==='observatory'?'/admin/activity':'/admin/analytics'):`/account/ai-cockpit/${view}`
  return path+(params.size?'?'+params:'')
}
export async function redirectLegacyActivity(view:'observatory'|'consumption',raw:ActivitySearch){
  const ctx=await getServerUserWithProfile()
  if(!ctx||ctx.profile.status!=='active')redirect('/login')
  redirect(activityDestination(ctx.profile.role==='super_admin',view,raw))
}
