import {beforeEach,it,expect,vi} from 'vitest'
import {NextResponse} from 'next/server'
const mocks=vi.hoisted(()=>({guard:vi.fn(),read:vi.fn()}))
vi.mock('@/lib/auth/access-control',()=>({requireSuperAdmin:mocks.guard}))
vi.mock('@/lib/admin/operations',()=>({OPERATION_SECTIONS:['foundation','health','assets','programme','learning'],readOperations:mocks.read}))
import {GET} from '@/app/api/admin/operations/[section]/route'
beforeEach(()=>{mocks.guard.mockReset();mocks.read.mockReset();mocks.guard.mockResolvedValue({user:{uid:'admin'}});mocks.read.mockResolvedValue({sources:[]})})
const call=(section='assets')=>GET(new Request('http://local'),{params:Promise.resolve({section})})
it.each([401,403])('does not read operator evidence when authentication returns %s',async status=>{mocks.guard.mockResolvedValue(NextResponse.json({error:'denied'},{status}));expect((await call()).status).toBe(status);expect(mocks.read).not.toHaveBeenCalled()})
it('rejects an unknown section before a source read',async()=>{expect((await call('untrusted')).status).toBe(404);expect(mocks.read).not.toHaveBeenCalled()})
it('marks authorized responses private and uncached',async()=>{const response=await call();expect(response.status).toBe(200);expect(response.headers.get('cache-control')).toBe('private, no-store');expect(mocks.read).toHaveBeenCalledWith('assets')})
