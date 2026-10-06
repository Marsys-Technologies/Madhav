import {beforeEach,it,expect,vi} from 'vitest'
import {NextResponse} from 'next/server'
const mocks=vi.hoisted(()=>({context:vi.fn(),guard:vi.fn(),query:vi.fn(),transaction:vi.fn(),txQuery:vi.fn(),generate:vi.fn()}))
vi.mock('@/lib/auth/access-control',()=>({getServerUserWithProfile:mocks.context,requireSuperAdmin:mocks.guard}))
vi.mock('@/lib/db/client',()=>({query:mocks.query,withTransaction:mocks.transaction}))
vi.mock('@/lib/mcp/auth',()=>({generateMcpKey:mocks.generate,sanitizeModelFamily:()=>null}))
vi.mock('@/lib/mcp/rate_limiter',()=>({checkRateLimit:async()=>({allowed:true}),buildRateLimitErrorEnvelope:()=>({})}))
import {GET,POST} from '@/app/api/mcp/keys/route'
import {DELETE} from '@/app/api/mcp/keys/[key_id]/route'
const context=(role='guest',status='active')=>({user:{uid:'actor'},profile:{role,status}})
const post=()=>POST(new Request('http://local',{method:'POST',body:JSON.stringify({user_uid:'target'})}))
const revoke=()=>DELETE(new Request('http://local',{method:'DELETE'}),{params:Promise.resolve({key_id:'id'})})
beforeEach(()=>{vi.clearAllMocks();mocks.context.mockResolvedValue(context());mocks.guard.mockResolvedValue(context('super_admin'));mocks.query.mockResolvedValue({rows:[{id:'target',key_id:'id',user_uid:'actor',revoked_at:null}]});mocks.txQuery.mockResolvedValue({rowCount:1,rows:[{key_id:'id'}]});mocks.transaction.mockImplementation(async fn=>fn({query:mocks.txQuery}));mocks.generate.mockResolvedValue({key_id:'id',full_key:'one-time-secret',key_hash:'secret-hash'})})
it.each(['pending','disabled'])('denies key listing and revocation for %s accounts before reading keys',async status=>{mocks.context.mockResolvedValue(context('guest',status));expect((await GET()).status).toBe(403);expect((await revoke()).status).toBe(403);expect(mocks.query).not.toHaveBeenCalled()})
it('returns 401 before reading keys without a session',async()=>{mocks.context.mockResolvedValue(null);expect((await GET()).status).toBe(401);expect(mocks.query).not.toHaveBeenCalled()})
it('scopes ordinary-user listing to the actor and never selects the hash',async()=>{await GET();expect(mocks.query.mock.calls[0][0]).toContain('WHERE user_uid = $1');expect(mocks.query.mock.calls[0][1]).toEqual(['actor']);expect(mocks.query.mock.calls[0][0]).not.toContain('key_hash')})
it('denies revocation of another user’s key without a transaction',async()=>{mocks.query.mockResolvedValue({rows:[{key_id:'id',user_uid:'someone',revoked_at:null}]});expect((await revoke()).status).toBe(403);expect(mocks.transaction).not.toHaveBeenCalled()})
it('does not generate a key for an inactive or absent target',async()=>{mocks.query.mockResolvedValue({rows:[]});expect((await post()).status).toBe(404);expect(mocks.query.mock.calls[0][0]).toContain("status='active'");expect(mocks.generate).not.toHaveBeenCalled()})
it('keeps creation and its redacted audit record in one transaction and returns the full key only on creation',async()=>{const response=await post();expect(response.status).toBe(201);expect((await response.json()).full_key).toBe('one-time-secret');expect(mocks.transaction).toHaveBeenCalledOnce();expect(mocks.txQuery.mock.calls[0][0]).toContain('FOR SHARE');expect(mocks.txQuery.mock.calls[2][0]).toContain('admin_audit_log');expect(JSON.stringify(mocks.txQuery.mock.calls[2])).not.toMatch(/one-time-secret|secret-hash/);expect(response.headers.get('cache-control')).toContain('no-store')})
it('reports a failed atomic creation without exposing the generated key',async()=>{mocks.transaction.mockRejectedValue(Error('audit unavailable'));const response=await post();expect(response.status).toBe(500);expect(JSON.stringify(await response.json())).not.toContain('one-time-secret')})
it('audits revocation once and preserves already-revoked idempotence',async()=>{expect((await revoke()).status).toBe(200);expect(mocks.txQuery.mock.calls[1][0]).toContain('mcp_key_revoked');mocks.query.mockResolvedValue({rows:[{key_id:'id',user_uid:'actor',revoked_at:'yesterday'}]});mocks.transaction.mockClear();expect((await revoke()).status).toBe(200);expect(mocks.transaction).not.toHaveBeenCalled()})
it('does not write a duplicate audit after a concurrent revocation',async()=>{mocks.txQuery.mockResolvedValue({rowCount:0,rows:[]});await revoke();expect(mocks.txQuery).toHaveBeenCalledOnce()})
it('preserves creation’s administrator guard',async()=>{mocks.guard.mockResolvedValue(NextResponse.json({error:'forbidden'},{status:403}));expect((await post()).status).toBe(403);expect(mocks.generate).not.toHaveBeenCalled()})

it("rolls back issuance when target status changes before the issuance lock",async()=>{mocks.txQuery.mockResolvedValueOnce({rows:[],rowCount:0});expect((await post()).status).toBe(404);expect(mocks.txQuery).toHaveBeenCalledOnce()})
