import {beforeEach,it,expect,vi} from 'vitest'
const mocks=vi.hoisted(()=>({query:vi.fn(),summary:vi.fn()}))
vi.mock('@/lib/db/client',()=>({query:mocks.query}))
vi.mock('@/lib/metering/queries',async()=>{const actual=await vi.importActual<typeof import('@/lib/metering/queries')>('@/lib/metering/queries');return {...actual,usageSummary:mocks.summary}})
import {accountingPeriod,monthlyAccounting} from '@/lib/admin/accounting'
beforeEach(()=>{vi.clearAllMocks();mocks.query.mockResolvedValue({rows:[]});mocks.summary.mockResolvedValue({provider_transport_cost_usd:null,known_transport_cost_usd:'1.10',transport_unpriced:2})})
it('uses real UTC calendar boundaries including leap months and year rollover',()=>{
  expect(accountingPeriod('2024-02')).toEqual({from:'2024-02-01T00:00:00.000Z',to:'2024-03-01T00:00:00.000Z'})
  expect(accountingPeriod('2026-12').to).toBe('2027-01-01T00:00:00.000Z')
  expect(()=>accountingPeriod('2026-13')).toThrow();expect(()=>accountingPeriod('0099-01')).toThrow()
})
it('reads canonical monthly portal spending without changing rules or substituting an activity window',async()=>{
  mocks.query.mockResolvedValue({rows:[{budget_rule_id:'r',name:'Month',scope:'provider',scope_value:'openai',amount_usd:'10'}]})
  const result=await monthlyAccounting('2026-10')
  expect(mocks.summary.mock.calls[0][0]).toMatchObject({from:'2026-10-01T00:00:00.000Z',to:'2026-11-01T00:00:00.000Z',provider:'openai'})
  expect(mocks.summary.mock.calls[0][0].userId).toBeUndefined();expect(mocks.summary.mock.calls[0][1]).toEqual({ownerId:null})
  expect(result.rows[0].summary?.provider_transport_cost_usd).toBeNull();expect(result.rows[0].summary?.known_transport_cost_usd).toBe('1.10')
  expect(mocks.query.mock.calls[0][0]).not.toMatch(/\b(UPDATE|INSERT|DELETE)\b/)
})
it('does not invent an equivalent meaning for an unsupported pipeline-stage budget',async()=>{
  mocks.query.mockResolvedValue({rows:[{budget_rule_id:'r',name:'Stage',scope:'pipeline_stage',scope_value:'old-stage',amount_usd:'10'}]})
  expect((await monthlyAccounting('2026-10')).rows[0]).toMatchObject({available:false,summary:null});expect(mocks.summary).not.toHaveBeenCalled()
})
it('shows an unavailable monthly source rather than measured zero on a read failure',async()=>{
  mocks.query.mockResolvedValue({rows:[{budget_rule_id:'r',scope:'total',amount_usd:'10'}]});mocks.summary.mockRejectedValue(Error('private details'))
  const result=await monthlyAccounting('2026-10');expect(result.rows[0]).toMatchObject({available:false,summary:null});expect(JSON.stringify(result)).not.toContain('private details')
})
