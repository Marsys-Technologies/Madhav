import { afterEach,beforeEach,describe,expect,it,vi } from 'vitest'
const mocks=vi.hoisted(()=>({guard:vi.fn(),run:vi.fn(),recover:vi.fn(),rate:vi.fn()}))
vi.mock('@/app/api/admin/observatory/_guard',()=>({guardObservatoryRoute:mocks.guard}))
vi.mock('../admin-test',()=>({runMeteredTest:mocks.run}))
vi.mock('../service',()=>({recoverReceipts:mocks.recover}))
vi.mock('@/lib/mcp/rate_limiter_core',()=>({checkRpm:()=>({allowed:true})}))
import { NextResponse } from 'next/server'
import { POST } from '@/app/api/admin/observatory/metering/manage/route'
beforeEach(()=>{vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED','true');mocks.guard.mockResolvedValue({user:{uid:'admin'},profile:{role:'super_admin',status:'active'}});mocks.run.mockReset();mocks.recover.mockReset()})
afterEach(()=>vi.unstubAllEnvs())
const request=(body:unknown,headers:Record<string,string>={})=>new Request('http://localhost/api/admin/observatory/metering/manage',{method:'POST',headers:{'Content-Type':'application/json',...headers},body:JSON.stringify(body)})
describe('administration boundary',()=>{
 it('does not run operations for denied accounts',async()=>{
  mocks.guard.mockResolvedValue(NextResponse.json({error:'forbidden'},{status:403}))
  expect((await POST(request({action:'recover'}))).status).toBe(403);expect(mocks.recover).not.toHaveBeenCalled()
 })
 it('rejects cross-origin operations',async()=>{
  expect((await POST(request({action:'recover'},{Origin:'https://attacker.invalid'}))).status).toBe(403)
  expect((await POST(request({action:'recover'},{Origin:'https://madhav.marsys.in','Sec-Fetch-Site':'cross-site'}))).status).toBe(403)
  expect(mocks.recover).not.toHaveBeenCalled()
 })
 it('accepts the production public origin behind a Cloud Run service URL',async()=>{
  mocks.recover.mockResolvedValue({recovered:2,failed:0})
  const proxied=new Request('https://amjis-web-example.a.run.app/api/admin/observatory/metering/manage',{
   method:'POST',headers:{Origin:'https://madhav.marsys.in','Content-Type':'application/json','Sec-Fetch-Site':'same-origin'},
   body:JSON.stringify({action:'recover'})})
  const response=await POST(proxied)
  expect(response.status).toBe(200)
  expect(await response.json()).toEqual({recovered:2,failed:0})
  expect(mocks.recover).toHaveBeenCalledOnce()
 })
 it('requires acknowledgement and derives the payer from the authenticated account',async()=>{
  const payload={action:'test',connectionId:'11111111-1111-4111-8111-111111111111',modelId:'model'}
  expect((await POST(request({...payload,acknowledgeCharge:false}))).status).toBe(400);expect(mocks.run).not.toHaveBeenCalled()
  mocks.run.mockResolvedValue({testRunId:'test',status:'completed'})
  expect((await POST(request({...payload,acknowledgeCharge:true}))).status).toBe(200)
  expect(mocks.run.mock.calls[0][0]).toBe('admin')
  expect((await POST(request({...payload,acknowledgeCharge:true,userId:'victim'}))).status).toBe(400)
 })
 it('bounds request bodies before parsing',async()=>{
  expect((await POST(request({action:'recover',extra:'x'.repeat(20000)}))).status).toBe(400)
 })
})
