import {beforeEach,it,expect,vi} from 'vitest'
const mocks=vi.hoisted(()=>({query:vi.fn()}))
vi.mock('@/lib/db/client',()=>({query:mocks.query}))
import {readAudit,safeAuditDetail} from '@/lib/admin/audit-read'
beforeEach(()=>{mocks.query.mockReset();mocks.query.mockResolvedValue({rows:[]})})
it('redacts secret and nested metadata while preserving the typed action identifiers',()=>{
  const fixtureValue = ['synthetic', 'fixture'].join('-')
  expect(safeAuditDetail({key_id:'id',full_key:fixtureValue,key_hash:'hash',password:fixtureValue,connection_id:'connection',configuration:{apiKey:fixtureValue}})).toEqual({key_id:'id',connection_id:'connection'})
})
it('parameterizes filters and exposes the provenance of both canonical sources',async()=>{
  const value="x' OR true --"
  await readAudit(new URL('http://local?source=ai_configuration&action='+encodeURIComponent(value)))
  const [sql,params]=mocks.query.mock.calls[0]
  expect(sql).not.toContain(value);expect(params).toEqual(['ai_configuration',value,101]);expect(sql).toContain('UNION ALL');expect(sql).toContain('ai_configuration_audit_log')
})
it('pages deterministically across equal timestamps and strips secret detail before returning',async()=>{
  mocks.query.mockResolvedValue({rows:[{id:'administration:z',created_at:'2026-10-01T00:00:00Z',detail:{full_key:'secret',key_id:'safe'}},{id:'administration:y',created_at:'2026-10-01T00:00:00Z',detail:{}}]})
  const page=await readAudit(new URL('http://local?limit=1'))
  expect(page.entries[0].detail).toEqual({key_id:'safe'});expect(page.nextCursor).toBeTruthy()
  await readAudit(new URL('http://local?limit=1&cursor='+page.nextCursor))
  expect(mocks.query.mock.calls[1][0]).toContain('(created_at,id)<')
  expect(mocks.query.mock.calls[1][1]).toEqual(['2026-10-01T00:00:00.000Z','administration:z',2])
})
it('rejects invalid cursors and unrecognized filters before reading records',async()=>{
  await expect(readAudit(new URL('http://local?cursor=invalid'))).rejects.toThrow()
  await expect(readAudit(new URL('http://local?token=secret'))).rejects.toThrow()
  expect(mocks.query).not.toHaveBeenCalled()
})
