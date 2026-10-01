import { afterEach,beforeEach,describe,expect,it,vi } from 'vitest'
const mocks=vi.hoisted(()=>({auth:vi.fn(),query:vi.fn()}))
vi.mock('@/lib/auth/access-control',()=>({getServerUserWithProfile:mocks.auth}))
vi.mock('@/lib/storage',()=>({getStorageClient:()=>({query:mocks.query})}))
import { GET } from '@/app/api/usage/route'
import { parseUsageFilter,usageCsv } from '../queries'
import { catalogCards } from '../catalog'
import { RecoveryEnvelopeSchema } from '../schema'
beforeEach(()=>{vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED','true');mocks.auth.mockReset();mocks.query.mockReset()})
afterEach(()=>vi.unstubAllEnvs())
describe('scoped usage API',()=>{
 it('rejects unauthenticated and inactive accounts before querying',async()=>{
  mocks.auth.mockResolvedValue(null);expect((await GET(new Request('http://localhost/api/usage'))).status).toBe(401)
  mocks.auth.mockResolvedValue({user:{uid:'alice'},profile:{status:'disabled'}})
  expect((await GET(new Request('http://localhost/api/usage'))).status).toBe(403);expect(mocks.query).not.toHaveBeenCalled()
 })
 it('pins a user to their own account and rejects attempts to override it',async()=>{
  mocks.auth.mockResolvedValue({user:{uid:'alice'},profile:{status:'active'}});mocks.query.mockResolvedValue({rows:[{}]})
  expect((await GET(new Request('http://localhost/api/usage?userId=bob'))).status).toBe(400);expect(mocks.query).not.toHaveBeenCalled()
  const response=await GET(new Request('http://localhost/api/usage'))
  expect(response.status).toBe(200);expect(mocks.query.mock.calls[0][1]).toContain('alice')
  expect(response.headers.get('Cache-Control')).toContain('no-store')
 })
 it('does not return database errors or provider data',async()=>{
  mocks.auth.mockResolvedValue({user:{uid:'alice'},profile:{status:'active'}});mocks.query.mockRejectedValue(new Error('password private'))
  const response=await GET(new Request('http://localhost/api/usage'));expect(response.status).toBe(503);expect(await response.text()).not.toContain('private')
 })
 it('bounds periods, dimensions and cursors',()=>{
  const scope={ownerId:'alice'}
  for(const query of ['from=2020-01-01T00:00:00Z','groupBy=user','groupBy=model;DROP TABLE profiles','limit=1001','view=trace','secret=x'])
   expect(()=>parseUsageFilter(new URL(`http://localhost/?${query}`),scope)).toThrow()
 })
 it('quotes CSV correctly and neutralizes formula values including whitespace',()=>{
  const csv=usageCsv([{id:'id',model:'  =2+2',role:'test,"quoted"',usage:{input:null}} as never])
  expect(csv).toContain("'  =2+2");expect(csv).toContain('test,""quoted""');expect(csv).not.toContain('undefined')
 })
 it('rejects recovery envelope extra fields before replay',()=>{
  expect(RecoveryEnvelopeSchema.safeParse({version:1,start:{credential:'private'},receipt:{}}).success).toBe(false)
 })
})
describe('official catalog conversion',()=>{
 it('uses decimal units and excludes non-token fees and dynamic routers',()=>{
  const result=catalogCards({data:[{id:'openai/example',pricing:{prompt:'0.0000003',completion:'0.000001',request:'0',input_cache_read:'0.0000001'}},
   {id:'extra',pricing:{prompt:'0.0001',completion:'0.0001',web_search:'0.01'}},
   {id:'openrouter/auto',pricing:{prompt:'0',completion:'0'}}]},new Date('2026-09-29T00:00:00Z'))
  expect(result.skipped).toBe(2);expect(result.cards[1].tokenPricingOnly).toBe(false);expect(result.cards[2].tokenPricingOnly).toBe(false);expect(result.cards[0].inputPerMillion).toBe('0.300000000000')
  expect(result.cards[0].effectiveFrom).toBe(result.cards[0].observedAt)
 })
})
