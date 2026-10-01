import { afterEach,describe,expect,it,vi } from 'vitest'
import { render,screen,fireEvent,waitFor,cleanup } from '@testing-library/react'
import { UsageDashboard } from '../UsageDashboard'
const summary={attempts:1,input_tokens:'100',output_tokens:'10',known_cost_usd:null,unknown_usage:1,unpriced:1,pending:0,stale_pending:0,legacy_records:0}
const event={id:'attempt',user_id:'alice',conversation_id:'conversation',turn_id:'turn',operation_id:'op',channel:'mcp',purpose:'customer',provider:'openai',model:'test-model',role:'planner',started_at:'2026-09-29T00:00:00Z',status:'success',evidence:'metered',usage:{input:100,output:10,source:'provider_reported'},pricing_status:'rate_unavailable',computed_cost_usd:null}
afterEach(()=>{cleanup();vi.unstubAllGlobals()})
describe('usage reader',()=>{
 it('shows partial evidence and drills into the query without inventing costs',async()=>{
  const fetcher=vi.fn(async(url:string)=>Response.json(url.includes('view=summary')?summary:url.includes('view=breakdown')?{groups:[{name:'conversation',...summary}]}:{events:[event],nextCursor:null}))
  vi.stubGlobal('fetch',fetcher);render(<UsageDashboard/>)
  expect(screen.getByRole('status').textContent).toContain('Loading')
  await screen.findByText('Evidence completeness')
  expect(screen.getByText(/1 attempts lack complete token counts/)).toBeDefined()
  expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
  fireEvent.click(screen.getByRole('button',{name:'conversation'}))
  await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>url.includes('view=trace&conversationId=conversation'))).toBe(true))
  fireEvent.click(await screen.findByRole('button',{name:'Inspect planner call attempt'}))
  expect(await screen.findByText('Call evidence')).toBeDefined();expect(screen.getByText('rate_unavailable')).toBeDefined()
  expect(screen.queryByText('$0.00')).toBeNull()
 })
 it('renders a visible error without presenting stale success data',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:503})));render(<UsageDashboard/>)
  expect((await screen.findByRole('alert')).textContent).toContain('could not be loaded')
  expect(screen.queryByText('Evidence completeness')).toBeNull()
 })
 it('shows an honest empty period and bounded export',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>Response.json(url.includes('view=summary')?{attempts:0}:url.includes('view=breakdown')?{groups:[]}:{events:[],nextCursor:null})))
  render(<UsageDashboard/>);expect(await screen.findByText('No consumption recorded for this period.')).toBeDefined()
  expect(screen.getByRole('link',{name:'Export first 1,000 records'}).getAttribute('href')).toContain('limit=1000')
 })
})
