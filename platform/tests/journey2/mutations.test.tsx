import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ResolveSection } from '@/components/pariprashna/samiksha/ResolveSection'
import { AwaitingSection } from '@/components/pariprashna/samiksha/AwaitingSection'
import { LogToSamiksha } from '@/components/pariprashna/samiksha/LogToSamiksha'
import { ShareButton } from '@/components/chat/ShareButton'
import { PariprashnaApp } from '@/components/pariprashna/PariprashnaApp'
import { type LedgerRow } from '@/lib/pariprashna/samiksha/schema'
afterEach(() => { cleanup(); vi.unstubAllGlobals(); localStorage.clear() })
const row = { id:'row',claim_text:'Synthetic prediction',window:'[2026-01-01,2026-02-01)',confidence:null,message_part_id:null } as LedgerRow
const candidate={claim_text:'Synthetic prediction',domain:null,window_start:null,window_end:null,direction:null,technique_refs:[],grounding_fact_ids:[],score:.8,horizon_text:null}
const resolveProps={rows:[row],turnAnchors:{},coverage:{resolvedCount:0,unverifiableCount:0,lapsedCount:1,coverageFraction:0}}
describe('Journey Two mutations keep failed work recoverable', () => {
  it('keeps batch selections after a rejected write', async () => {
    const save=vi.fn().mockRejectedValue(new Error('DB unavailable'))
    render(<ResolveSection {...resolveProps} onResolve={vi.fn()} onBatchResolve={save}/>)
    fireEvent.click(screen.getByRole('radio',{name:'Happened'}))
    fireEvent.click(screen.getByRole('button',{name:'Resolve marked (1)'}))
    await screen.findByRole('alert')
    expect(screen.getByRole('radio',{name:'Happened'})).toHaveAttribute('aria-checked','true')
    expect(screen.getByRole('button',{name:'Resolve marked (1)'})).toBeEnabled()
  })
  it('handles a single keyboard resolution failure without dropping its selection', async () => {
    render(<ResolveSection {...resolveProps} onResolve={vi.fn().mockRejectedValue(new Error('failure'))} onBatchResolve={vi.fn()}/>)
    fireEvent.click(screen.getByRole('radio',{name:'Happened'}))
    fireEvent.keyDown(screen.getByRole('listitem'),{key:'Enter'})
    await screen.findByRole('alert')
    expect(screen.getByRole('radio',{name:'Happened'})).toHaveAttribute('aria-checked','true')
  })
  it('keeps a failed candidate edit open with the draft intact', async () => {
    render(<AwaitingSection rows={[row]} turnAnchors={{}} onConfirm={vi.fn()} onDismiss={vi.fn()} onEdit={vi.fn().mockRejectedValue(new Error('stale'))}/>)
    fireEvent.click(screen.getByRole('button',{name:'Edit'}))
    fireEvent.change(screen.getByRole('textbox',{name:'Edit claim text'}),{target:{value:'My revised claim'}})
    fireEvent.click(screen.getByRole('button',{name:'Save edit'}))
    await screen.findByRole('alert')
    expect(screen.getByRole('textbox',{name:'Edit claim text'})).toHaveValue('My revised claim')
  })
  it('handles failed network confirmation with an actionable retry state', async () => {
    render(<LogToSamiksha chartId="chart" conversationId="conversation" messagePartId="part" candidate={candidate} post={vi.fn().mockRejectedValue(new Error('offline'))}/>)
    fireEvent.click(screen.getByRole('button',{name:/Log to Samīkṣā/}))
    fireEvent.click(screen.getByRole('button',{name:'Confirm'}))
    await screen.findByText('Could not log the prediction. Please try again.')
    expect(screen.queryByTestId('log-samiksha-done')).toBeNull()
  })
  it('does not report a failed revoke as successful and retains the link', async () => {
    vi.stubGlobal('fetch',vi.fn(async (_url: RequestInfo | URL,init?: RequestInit) => init?.method==='DELETE' ? Response.json({}, {status:503}) : Response.json({share:{slug:'existing-link'}})))
    render(<ShareButton conversationId="conversation" messageId="answer"/>)
    fireEvent.click(screen.getByRole('button',{name:'Share this answer'}))
    await screen.findByText(/existing-link/)
    fireEvent.click(screen.getByRole('button',{name:'Revoke link'}))
    fireEvent.click(screen.getByRole('button',{name:'Revoke'}))
    await screen.findByRole('alert')
    expect(screen.getByText(/existing-link/)).toBeVisible()
  })
  it('opens real-chart requests with the server BYOK choice even when public build flags are absent', async () => {
    const fetch=vi.fn(async (url: RequestInfo | URL,init?: RequestInit) => {
      if(String(url).includes('/api/pariprashna') && init?.method==='POST') return Response.json({},{status:400})
      if(String(url).endsWith('/api/ai-console')) return Response.json({
        connections:[{id:'test-connection',providerId:'openai',name:'Synthetic provider',validationState:'validated',confirmedValid:true,deletedAt:null}],
        models:[{connectionId:'test-connection',modelId:'test-model',displayName:'Synthetic model',compatibleRoles:['synthesizer','planner','deep_planner','worker'],available:true,userSelected:true,plainTestedAt:'2026-10-01T00:00:00Z'}],
        configurations:[],defaultChoice:{kind:'provider_model',connectionId:'test-connection',modelId:'test-model'}})
      return Response.json({clis:[],personas:[],conversations:[]})
    })
    vi.stubGlobal('fetch',fetch)
    render(<PariprashnaApp chartId="22222222-2222-4222-8222-222222222222" chartPin={{name:'Synthetic',bornLine:'Synthetic'}} byokEnabled={true}/>)
    fireEvent.change(screen.getByRole('textbox',{name:'Ask the chart'}),{target:{value:'My question'}})
    await waitFor(() => expect(screen.getByRole('button',{name:'Ask'})).toBeEnabled())
    fireEvent.click(screen.getByRole('button',{name:'Ask'}))
    await waitFor(() => expect(fetch.mock.calls.some(([url,init])=>String(url).includes('/api/pariprashna') && init?.method==='POST')).toBe(true))
    const call=fetch.mock.calls.find(([url,init])=>String(url).includes('/api/pariprashna') && init?.method==='POST')!
    expect(JSON.parse(call[1]!.body as string).ai_selection).toEqual({kind:'default'})
  })
  it('opens a source deep link and continues that exact saved conversation', async () => {
    const id='11111111-1111-4111-8111-111111111111', chart='22222222-2222-4222-8222-222222222222'
    const fetch=vi.fn(async (url: RequestInfo | URL,init?: RequestInit) => {
      if(String(url).endsWith(`/api/conversations/${id}/consultation`)) return Response.json({
        conversation:{id,chart_id:chart,title:'Saved source',tagged:false},readOnly:false,
        messages:[{id:'question',role:'user',created_at:'2026-10-01T00:00:00Z',schema_version:1,tagged:false,parts_json:[],metadata_json:{},canonical_parts:[{kind:'text',body:{text:'Original question'}}]},
          {id:'answer',role:'assistant',created_at:'2026-10-01T00:00:01Z',schema_version:1,tagged:false,parts_json:[],metadata_json:{},canonical_parts:[{kind:'text',body:{text:'Saved canonical answer'}}]}]})
      if(init?.method==='POST') return Response.json({},{status:400})
      return Response.json({conversations:[],personas:[]})
    })
    vi.stubGlobal('fetch',fetch)
    render(<PariprashnaApp chartId={chart} initialThread={id} chartPin={{name:'Synthetic',bornLine:'Synthetic'}} byokEnabled={false}/>)
    await screen.findByText('Original question')
    await screen.findByText('Saved canonical answer')
    // Legacy durable answers retain owner-scoped tags and sharing without a modern receipt.
    expect(screen.getByRole('button',{name:'Tag answer'})).toBeEnabled()
    expect(screen.getByRole('button',{name:'Share this answer'})).toBeEnabled()
    fireEvent.change(screen.getByRole('textbox',{name:'Ask the chart'}),{target:{value:'Follow-up'}})
    await waitFor(() => expect(screen.getByRole('button',{name:'Ask'})).toBeEnabled())
    fireEvent.click(screen.getByRole('button',{name:'Ask'}))
    await waitFor(() => expect(fetch.mock.calls.some(([,init])=>init?.method==='POST')).toBe(true))
    const call=fetch.mock.calls.find(([,init])=>init?.method==='POST')!
    expect(JSON.parse(call[1]!.body as string)).toMatchObject({conversationId:id,chartId:chart})
  })

})
