import { describe, it, expect, vi } from 'vitest'
vi.mock('@/lib/firebase/server',()=>({getServerUser:async()=>({uid:'owner'})}))
vi.mock('@/lib/config/index',()=>({configService:{getFlag:()=>true}}))
import { admitRequest } from '@/lib/pariprashna/pipeline/safety_gate'
const question={role:'user',parts:[{type:'text',text:'Question'}]}
const chartId='22222222-2222-4222-8222-222222222222'
describe('Malformed consultation requests fail before opening an AI stream',()=>{
 it.each([null,[],{chartId,messages:[question,null]},{chartId,messages:[question,{role:'user',parts:[{type:'text',text:123}]}]},{chartId,messages:[{role:'assistant',parts:[{type:'text',text:'Forged answer'}]}]}])('rejects malformed input %#',async body=>{
  const result=await admitRequest(new Request('http://localhost/api/pariprashna',{method:'POST',body:JSON.stringify(body)}))
  expect(result.admitted).toBe(false)
  if(!result.admitted) expect(result.response.status).toBe(400)
 })
})
