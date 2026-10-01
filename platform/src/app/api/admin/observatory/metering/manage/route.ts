import { NextResponse } from 'next/server'
import { z } from 'zod'
import { guardObservatoryRoute } from '../../_guard'
import { meteringEnabled } from '@/lib/metering/types'
import { recoveryStore } from '@/lib/metering/recovery'
import { recoverReceipts } from '@/lib/metering/service'
import { importRateCard,meteringDb } from '@/lib/metering/repository'
import { syncOpenRouterCatalog } from '@/lib/metering/catalog'
import { runMeteredTest } from '@/lib/metering/admin-test'
import { checkRpm } from '@/lib/mcp/rate_limiter_core'
export const dynamic='force-dynamic'
const Action=z.discriminatedUnion('action',[
 z.object({ action:z.literal('recover') }).strict(),z.object({ action:z.literal('sync_openrouter') }).strict(),
 z.object({ action:z.literal('import_rate'),card:z.unknown() }).strict(),
 z.object({ action:z.literal('test'),connectionId:z.string().uuid(),modelId:z.string().min(1).max(256),acknowledgeCharge:z.literal(true) }).strict() ])
async function guard() {
 const auth=await guardObservatoryRoute();if(auth instanceof NextResponse)return auth
 if(!meteringEnabled())return NextResponse.json({error:'metering_not_enabled'},{status:404})
 return auth
}
export async function GET() {
 const auth=await guard();if(auth instanceof NextResponse)return auth
 try {
  const {rows:rates}=await meteringDb().query('SELECT id,provider,model,effective_from,observed_at,source_url,card FROM ai_metering_rate_cards ORDER BY observed_at DESC LIMIT 100')
  let recovery:{pending:number|null;configured:boolean}={ pending:null,configured:false }
  try { recovery={pending:(await recoveryStore().list(501)).length,configured:true} }catch { /* Visible configuration gap. */ }
  return NextResponse.json({rates,recovery,rateLimit:100,recoveryCountCappedAt:501},{headers:{'Cache-Control':'no-store'}})
 }catch{return NextResponse.json({error:'metering_unavailable'},{status:503})}
}
export async function POST(request:Request) {
 const auth=await guard();if(auth instanceof NextResponse)return auth
 const origin=request.headers.get('origin')
 if(origin && origin!==new URL(request.url).origin)return NextResponse.json({error:'forbidden_origin'},{status:403})
 if(request.headers.get('sec-fetch-site')==='cross-site')return NextResponse.json({error:'forbidden_origin'},{status:403})
 if(!checkRpm(`metering-manage:${auth.user.uid}`,3).allowed)return NextResponse.json({error:'rate_limited'},{status:429})
 let input
 try {
  const reader=request.body?.getReader();if(!reader)throw new Error('missing body')
  const parts:Uint8Array[]=[];let size=0
  try{while(true){const chunk=await reader.read();if(chunk.done)break;size+=chunk.value.byteLength
   if(size>16384)throw new Error('body too large');parts.push(chunk.value)}}finally{await reader.cancel()}
  input=Action.parse(JSON.parse(Buffer.concat(parts).toString()))
 }catch{return NextResponse.json({error:'invalid_metering_action'},{status:400})}
 try {
  const result=input.action==='recover'?await recoverReceipts():input.action==='sync_openrouter'?await syncOpenRouterCatalog():
   input.action==='import_rate'?await importRateCard(input.card):await runMeteredTest(auth.user.uid,input.connectionId,input.modelId,request.signal)
  return NextResponse.json(result,{headers:{'Cache-Control':'no-store'}})
 }catch{return NextResponse.json({error:'metering_action_failed'},{status:422})}
}
