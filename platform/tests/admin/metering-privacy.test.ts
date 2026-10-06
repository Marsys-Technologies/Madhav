import {beforeEach,describe,expect,it,vi} from 'vitest'
import {NextResponse} from 'next/server'
const mocks=vi.hoisted(()=>({guard:vi.fn(),query:vi.fn()}))
vi.mock('@/app/api/admin/observatory/_guard',()=>({guardObservatoryRoute:mocks.guard}))
vi.mock('@/lib/storage',()=>({getStorageClient:()=>({query:mocks.query})}))
import {GET} from '@/app/api/admin/observatory/metering/route'
beforeEach(()=>{vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED','true');mocks.guard.mockResolvedValue({user:{uid:'actor'},profile:{role:'super_admin',status:'active'}});mocks.query.mockReset();mocks.query.mockResolvedValue({rows:[]})})
describe('operator conversation privacy',()=>{
 it.each(['userId=selected',''])('suppresses conversation text for portal or selected other-user scope: %s',async filter=>{
  expect((await GET(new Request(`http://localhost/?view=conversations&${filter}`))).status).toBe(200)
  expect(mocks.query.mock.calls[0][1]).toContain(false)
 })
 it('preserves the operator own conversation derivation',async()=>{
  expect((await GET(new Request('http://localhost/?view=conversations&userId=actor'))).status).toBe(200)
  expect(mocks.query.mock.calls[0][1]).toContain(true)
 })
 it.each(['userId=actor&userId=selected','userId=selected&userId=actor'])('rejects duplicated authority parameters before reading: %s',async filter=>{
  expect((await GET(new Request(`http://localhost/?view=conversations&${filter}`))).status).toBe(400)
  expect(mocks.query).not.toHaveBeenCalled()
 })
 it('does not read metering when the operator guard denies access',async()=>{
  mocks.guard.mockResolvedValue(NextResponse.json({error:'forbidden'},{status:403}))
  expect((await GET(new Request('http://localhost/?view=conversations&userId=actor'))).status).toBe(403)
  expect(mocks.query).not.toHaveBeenCalled()
 })
})
