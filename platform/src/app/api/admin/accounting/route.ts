import {NextResponse} from 'next/server'
import {guardObservatoryRoute} from '@/app/api/admin/observatory/_guard'
import {meteringEnabled} from '@/lib/metering/types'
import {accountingPeriod,monthlyAccounting} from '@/lib/admin/accounting'
export const dynamic='force-dynamic'
export async function GET(request:Request) {
  const auth=await guardObservatoryRoute();if(auth instanceof NextResponse)return auth
  if(!meteringEnabled())return NextResponse.json({error:'metering_not_enabled'},{status:404})
  const month=new URL(request.url).searchParams.get('month')??new Date().toISOString().slice(0,7)
  try {accountingPeriod(month)} catch {return NextResponse.json({error:'Choose a valid accounting month'},{status:400})}
  try {return NextResponse.json(await monthlyAccounting(month),{headers:{'Cache-Control':'private, no-store'}})}
  catch {return NextResponse.json({error:'Monthly accounting unavailable'},{status:503})}
}
