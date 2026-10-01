'use client'
import { useState } from 'react'
import Link from 'next/link'
import { QueryClient,QueryClientProvider,useQuery,useInfiniteQuery } from '@tanstack/react-query'
import type { UsageEvent } from '@/lib/metering/queries'
type Totals=Record<string,number|string|null>
type Group=Totals & {name:string|null}
const field='w-full rounded-md border border-[rgba(var(--brand-gold-rgb),0.25)] bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[var(--brand-gold)]'
const button='rounded-md border border-[rgba(var(--brand-gold-rgb),0.35)] px-4 py-2 text-sm text-[var(--brand-gold)] hover:bg-[rgba(var(--brand-gold-rgb),0.08)] focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)] disabled:opacity-40'
const panel='rounded-xl border border-[rgba(var(--brand-gold-rgb),0.18)] bg-[rgba(var(--brand-gold-rgb),0.025)] p-4 sm:p-6'
const count=(v:unknown)=>v==null?'Unavailable':typeof v==='string'&&/^\d+$/.test(v)?BigInt(v).toLocaleString():Number(v).toLocaleString()
const money=(v:unknown)=>v==null?'Unavailable':`$${Number(v).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:8})}`
const today=()=>new Date().toISOString().slice(0,10)
const monthAgo=()=>new Date(Date.now()-29*86400000).toISOString().slice(0,10)
export function UsageDashboard({admin=false}:{admin?:boolean}) {
 const [client]=useState(()=>new QueryClient({defaultOptions:{queries:{retry:false,refetchOnWindowFocus:false}}}))
 return <QueryClientProvider client={client}><DashboardContent admin={admin}/></QueryClientProvider>
}
function DashboardContent({admin}:{admin:boolean}) {
 const endpoint=admin?'/api/admin/observatory/metering':'/api/usage'
 const [from,setFrom]=useState(monthAgo),[to,setTo]=useState(today)
 const [channel,setChannel]=useState(''),[purpose,setPurpose]=useState(''),[model,setModel]=useState(''),[user,setUser]=useState('')
 const [groupBy,setGroupBy]=useState('conversation'),[refresh,setRefresh]=useState(0)
 const params=new URLSearchParams({from:`${from}T00:00:00.000Z`,to:new Date(Date.parse(`${to}T00:00:00Z`)+86400000).toISOString(),groupBy})
 if(channel)params.set('channel',channel);if(purpose)params.set('purpose',purpose);if(model)params.set('model',model);if(admin&&user)params.set('userId',user)
 const query=params.toString()
 const [inspection,setInspection]=useState<{query:string;trace:string}|null>(null)
 const trace=inspection?.query===query?inspection.trace:''
 const [selected,setSelected]=useState<{query:string;event:UsageEvent}|null>(null)
 const detail=selected?.query===query?selected.event:null
 const setDetail=(event:UsageEvent|null)=>setSelected(event?{query,event}:null)
 const setTrace=(value:string)=>setInspection(value?{query,trace:value}:null)
 const get=async(view:string,signal:AbortSignal,cursor?:string|null,traceParam='')=>{
  const response=await fetch(`${endpoint}?${query}&view=${view}${cursor?`&cursor=${encodeURIComponent(cursor)}`:''}${traceParam?`&${traceParam}`:''}`,{signal,cache:'no-store'})
  if(!response.ok)throw new Error(response.status===404?'Usage metering is not enabled.':'Usage could not be loaded. Please retry.')
  return response.json()
 }
 const overview=useQuery({queryKey:[endpoint,query,refresh,'overview'],queryFn:async({signal})=>{
  const [summary,breakdown]=await Promise.all([get('summary',signal),get('breakdown',signal)])
  return {summary:summary as Totals,groups:breakdown.groups as Group[]}
 }})
 const calls=useInfiniteQuery({queryKey:[endpoint,query,trace,refresh,'calls'],initialPageParam:null as string|null,
  queryFn:({signal,pageParam})=>get(trace?'trace':'events',signal,pageParam,trace) as Promise<{events:UsageEvent[];nextCursor:string|null}>,
  getNextPageParam:page=>page.nextCursor??undefined})
 const operations=useQuery({queryKey:[endpoint,refresh,'operations'],enabled:admin,
  queryFn:async({signal})=>{const response=await fetch(`${endpoint}/manage`,{signal,cache:'no-store'});if(!response.ok)throw new Error('Unavailable')
   return response.json() as Promise<{rates:unknown[];recovery:{pending:number|null;configured:boolean}}>}})
 const summary=overview.data?.summary,groups=overview.data?.groups??[],events=calls.data?.pages.flatMap(page=>page.events)??[]
 const loading=overview.isPending||calls.isPending,error=overview.error?.message??calls.error?.message??''
 const cursor=calls.hasNextPage,moreLoading=calls.isFetchingNextPage,manage=operations.data
 const [action,setAction]=useState(''),[notice,setNotice]=useState(''),[rateJson,setRateJson]=useState('')
 const [connectionId,setConnectionId]=useState(''),[testModel,setTestModel]=useState(''),[charge,setCharge]=useState(false)
 async function runAction(name:string) {
  setAction(name);setNotice('')
  try {
   const body=name==='import_rate'?{action:name,card:JSON.parse(rateJson)}:name==='test'?{action:name,connectionId,modelId:testModel,acknowledgeCharge:charge}:{action:name}
   const response=await fetch(`${endpoint}/manage`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
   if(!response.ok)throw new Error();const result=await response.json()
   setNotice(name==='recover'?`Recovered ${result.recovered} receipts; ${result.failed} require attention.`:name==='sync_openrouter'?`Imported ${result.imported} rates; ${result.unchanged} unchanged; ${result.skipped} marked unsupported.`:name==='test'?`Test completed. Run: ${result.testRunId}`:'Rate evidence imported.')
   setRefresh(value=>value+1)
  }catch{setNotice('The action could not be completed. Check the supplied details and configuration.')}finally{setAction('')}
 }
 const rows=events
 return <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-8">
  <header className="flex flex-wrap items-start justify-between gap-4">
   <div><p className="text-xs uppercase tracking-[0.18em] text-[var(--brand-gold)]">{admin?'Observatory':'Account'}</p>
    <h1 className="font-display text-3xl text-[var(--brand-gold)]">{admin?'Consumption ledger':'My AI usage'}</h1>
    <p className="mt-2 max-w-2xl text-sm text-muted-foreground">Follow consumption from a conversation to each query, stage and model call. Missing evidence remains visible.</p></div>
   <div className="flex gap-2"><Link className={button} href={admin?'/usage':'/ai-console'}>{admin?'My usage':'AI Console'}</Link><button className={button} onClick={()=>setRefresh(v=>v+1)}>Refresh</button></div>
  </header>
  <section className={panel} aria-label="Usage filters"><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
   <label className="text-sm">From (UTC)<input className={field} type="date" value={from} max={to} onChange={e=>{if(e.target.value)setFrom(e.target.value)}}/></label>
   <label className="text-sm">Through (UTC)<input className={field} type="date" value={to} min={from} onChange={e=>{if(e.target.value)setTo(e.target.value)}}/></label>
   <label className="text-sm">Channel<select className={field} value={channel} onChange={e=>setChannel(e.target.value)}><option value="">All channels</option>{['web','mcp','api','backend','scheduled','unknown'].map(value=><option key={value}>{value}</option>)}</select></label>
   <label className="text-sm">Purpose<select className={field} value={purpose} onChange={e=>setPurpose(e.target.value)}><option value="">All purposes</option>{['customer','admin_test','validation','evaluation','background','legacy'].map(value=><option key={value}>{value}</option>)}</select></label>
   <label className="text-sm">Model<input className={field} value={model} placeholder="Exact model ID" onChange={e=>setModel(e.target.value)}/></label>
   <label className="text-sm">Analyse by<select className={field} value={groupBy} onChange={e=>setGroupBy(e.target.value)}>{['conversation','turn','model','provider','role','channel','purpose','day',...(admin?['user']:[])].map(value=><option key={value}>{value}</option>)}</select></label>
   {admin&&<label className="text-sm">Account<input className={field} value={user} placeholder="All accounts" onChange={e=>setUser(e.target.value)}/></label>}
   <a className={`${button} self-end text-center`} href={`${endpoint}?${query}&view=export&limit=1000`}>Export first 1,000 records</a>
  </div><p className="mt-3 text-xs text-muted-foreground">Periods are limited to 90 days. Export pagination is available through the API.</p></section>
  {loading&&<p role="status">Loading consumption…</p>}{error&&<p role="alert" className={panel}>{error}</p>}
  {summary&&<>
   <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Consumption summary">{[
    ['Provider attempts',count(summary.attempts)],['Input tokens',count(summary.input_tokens)],['Output tokens',count(summary.output_tokens)],['Calculated cost (USD)',money(summary.known_cost_usd)],
   ].map(([label,value])=><div className={panel} key={label}><p className="text-xs text-muted-foreground">{label}</p><p className="mt-2 text-2xl tabular-nums text-[var(--brand-gold)]">{value}</p></div>)}</section>
   <section className={panel} aria-label="Evidence completeness"><h2 className="text-lg">Evidence completeness</h2>
    <p className="mt-2 text-sm">{count(summary.unknown_usage)} attempts lack complete token counts. {count(summary.unpriced)} lack a complete calculated price. {count(summary.pending)} await a terminal record, including {count(summary.stale_pending)} older than 15 minutes.</p>
    <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3"><div><dt>Cached input read / written</dt><dd>{count(summary.cache_read_tokens)} / {count(summary.cache_write_tokens)}</dd></div><div><dt>Reasoning tokens (included in output)</dt><dd>{count(summary.reasoning_tokens)}</dd></div><div><dt>Provider-reported cost</dt><dd>{money(summary.provider_reported_cost_usd)}</dd></div><div><dt>Median / 95th percentile duration</dt><dd>{summary.p50_ms==null?'Unavailable':`${Math.round(Number(summary.p50_ms))} ms`} / {summary.p95_ms==null?'Unavailable':`${Math.round(Number(summary.p95_ms))} ms`}</dd></div><div><dt>CLI reported input / output</dt><dd>{count(summary.cli_input_tokens)} / {count(summary.cli_output_tokens)}</dd></div><div><dt>Historical records / estimated cost</dt><dd>{count(summary.legacy_records)} / {money(summary.legacy_estimate_usd)}</dd></div></dl>
    <p className="mt-4 text-xs text-muted-foreground">Calculated costs use the recorded rate version and may differ from invoices. Historical estimates and CLI subscription usage are shown separately. An external MCP assistant’s own generation is outside Madhav’s measured usage.</p>
   </section>
   <section className={panel}><h2 className="text-lg">Consumption by {groupBy}</h2><div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Usage grouped by {groupBy}; up to 200 groups</caption><thead><tr className="border-b border-[rgba(var(--brand-gold-rgb),0.2)]">{['Group','Attempts','Input','Output','Calculated USD','Unpriced'].map(t=><th className="p-2" key={t} scope="col">{t}</th>)}</tr></thead><tbody>{groups.map((group,i)=><tr className="border-b border-[rgba(var(--brand-gold-rgb),0.1)]" key={`${group.name}-${i}`}><td className="max-w-80 break-all p-2">{group.name&&(groupBy==='conversation'||groupBy==='turn')?<button className="text-[var(--brand-gold)] underline" onClick={()=>{setDetail(null);setTrace(`${groupBy==='conversation'?'conversationId':'turnId'}=${encodeURIComponent(group.name!)}`)}}>{group.name}</button>:group.name??'No conversation recorded'}</td>{['attempts','input_tokens','output_tokens','known_cost_usd','unpriced'].map(key=><td className="p-2 tabular-nums" key={key}>{key==='known_cost_usd'?money(group[key]):count(group[key])}</td>)}</tr>)}</tbody></table></div>{groups.length===0&&<p className="mt-4 text-sm text-muted-foreground">No consumption recorded for this period.</p>}<p className="mt-2 text-xs text-muted-foreground">Up to 200 groups. Filter to narrow the view.</p></section>
  </>}
  <section className={panel}><div className="flex flex-wrap justify-between gap-3"><h2 className="text-lg">{trace?'Conversation / query details':'Model calls'}</h2>{trace&&<button className={button} onClick={()=>{setTrace('');setDetail(null)}}>All calls</button>}</div>
   {trace&&calls.isPending&&<p role="status">Loading query details…</p>}
   <ol className="mt-4 space-y-3">{rows.map(event=><li key={event.id} className="rounded-md border border-[rgba(var(--brand-gold-rgb),0.15)] p-3"><button className="w-full text-left focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]" onClick={()=>setDetail(event)} aria-label={`Inspect ${event.role} call ${event.id}`}><span className="flex flex-wrap justify-between gap-2"><span className="font-medium">{event.role} · {event.model}</span><span>{event.status} · {event.evidence}</span></span><span className="mt-2 block text-xs text-muted-foreground">{new Date(event.started_at).toLocaleString()} · {event.channel} · {event.purpose} · Input {count(event.usage?.input)} · Output {count(event.usage?.output)} · {money(event.computed_cost_usd)}</span></button></li>)}</ol>
   {!loading&&rows.length===0&&<p className="mt-4 text-sm text-muted-foreground">No calls to display.</p>}
   {cursor&&<button className={`${button} mt-4`} disabled={moreLoading} onClick={()=>void calls.fetchNextPage()}>{moreLoading?'Loading…':'Load more calls'}</button>}

  </section>
  {detail&&<section className={panel} aria-label="Selected call"><div className="flex justify-between"><h2 className="text-lg">Call evidence</h2><button className={button} onClick={()=>setDetail(null)}>Close</button></div><dl className="mt-4 grid gap-3 break-all text-sm sm:grid-cols-2">{Object.entries({Attempt:detail.id,Conversation:detail.conversation_id,Query:detail.turn_id,Operation:detail.operation_id,Parent:detail.parent_operation_id,Provider:detail.provider,Connection:detail.connection_id,Snapshot:detail.snapshot_id,'Test run':detail.test_run_id,'Provider request':detail.provider_request_id,'Evidence source':detail.usage?.source,'Pricing state':detail.pricing_status,'Aggregation':detail.aggregation}).map(([key,value])=><div key={key}><dt className="text-muted-foreground">{key}</dt><dd>{value??'Unavailable'}</dd></div>)}</dl><details className="mt-4"><summary className="cursor-pointer text-sm text-[var(--brand-gold)]">Token and rate details</summary><pre className="mt-3 overflow-auto whitespace-pre-wrap break-all text-xs">{JSON.stringify({usage:detail.usage,pricing:detail.pricing_snapshot},null,2)}</pre></details></section>}
  {admin&&<section className={panel} aria-label="Metering administration"><h2 className="text-lg">Metering operations</h2><p className="mt-2 text-sm">Recovery storage: {manage?.recovery.configured?'configured':'unavailable'}. Buffered receipts: {count(manage?.recovery.pending)} (count capped at 501).</p><div className="mt-4 flex flex-wrap gap-3"><button className={button} disabled={!!action} onClick={()=>void runAction('recover')}>Recover buffered receipts</button><button className={button} disabled={!!action} onClick={()=>void runAction('sync_openrouter')}>Refresh OpenRouter rates</button></div>
   <details className="mt-6"><summary className="cursor-pointer">Import official rate evidence</summary><label className="mt-3 block text-sm">Rate card JSON<textarea className={`${field} mt-2`} rows={8} value={rateJson} onChange={e=>setRateJson(e.target.value)}/></label><button className={`${button} mt-3`} disabled={!!action||!rateJson} onClick={()=>void runAction('import_rate')}>Import rate</button><p className="mt-2 text-xs text-muted-foreground">New versions apply by effective date. Existing call receipts remain unchanged.</p></details>
   <details className="mt-6"><summary className="cursor-pointer">Metered administrator test</summary><p className="mt-3 text-sm">Runs a tiny generation on an owned, validated connection. Its provider charge is recorded as an administrator test.</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><label className="text-sm">Connection ID<input className={field} value={connectionId} onChange={e=>setConnectionId(e.target.value)}/></label><label className="text-sm">Model ID<input className={field} value={testModel} onChange={e=>setTestModel(e.target.value)}/></label></div><label className="mt-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={charge} onChange={e=>setCharge(e.target.checked)}/>I acknowledge the provider charge for this test.</label><button className={`${button} mt-3`} disabled={!!action||!charge||!connectionId||!testModel} onClick={()=>void runAction('test')}>Run metered test</button></details>
   {action&&<p className="mt-4" role="status">Working…</p>}{notice&&<p className="mt-4 text-sm" role="status">{notice}</p>}
  </section>}
 </div>
}
