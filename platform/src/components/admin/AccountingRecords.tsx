'use client'
import {useState} from 'react'
import {useQuery} from '@tanstack/react-query'
import {useObservatoryScope} from '@/components/observatory/ObservatoryScope'
import type {monthlyAccounting} from '@/lib/admin/accounting'
import type {ReconciliationHistoryResponse} from '@/lib/observatory/reconciliation/types'
async function read<T>(url:string):Promise<T>{const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw Error('Accounting records unavailable');return response.json()}
const amount=(value:string|number|null|undefined)=>value==null?'Not reported':`$${Number(value).toFixed(4)}`
export function AccountingRecords(){
  const {userId}=useObservatoryScope(),[month,setMonth]=useState(()=>new Date().toISOString().slice(0,7))
  const budgets=useQuery({queryKey:['admin',userId,'accounting',month],queryFn:()=>read<Awaited<ReturnType<typeof monthlyAccounting>>>(`/api/admin/accounting?month=${month}`)})
  const reconciliation=useQuery({queryKey:['admin',userId,'reconciliation-history'],queryFn:()=>read<ReconciliationHistoryResponse>('/api/admin/observatory/reconciliation/history?limit=25')})
  return <div className="j6-evidence">
    <section className="j5-panel"><h2>Monthly budget accounting</h2><div className="j6-scope"><label>Accounting month · UTC<input type="month" min="2000-01" max="2100-12" value={month} onChange={event=>{if(event.target.value)setMonth(event.target.value)}} /></label></div>
      {budgets.isPending?<p>Loading monthly records…</p>:budgets.isError?<p role="alert">Monthly accounting unavailable.</p>:<><p className="j1-note">{budgets.data?.note}</p>{budgets.data?.rows.length===0&&<p>No active monthly rules recorded.</p>}{budgets.data?.rows.map(row=><article className="j6-record" key={row.budget_rule_id}><h3>{row.name}</h3><p>Budget {amount(row.amount_usd)} · {row.scope} {row.scope_value}</p>{!row.available?<p>Unavailable</p>:<p>Provider receipts {amount(row.summary?.provider_transport_cost_usd)} · known API estimate {amount(row.summary?.known_transport_cost_usd)} · unpriced API calls {row.summary?.transport_unpriced??'Not reported'}</p>}<p className="j1-note">{row.note}</p></article>)}</>}
    </section>
    <section className="j5-panel"><h2>Recorded reconciliation runs</h2><p className="j1-note">Last 25 stored runs, with their original provider and accounting periods. These historical comparisons may use the older usage source; they are not proof that the current activity window is reconciled. Opening this view performs no provider call or invoice upload.</p>
      {reconciliation.isPending?<p>Loading reconciliation records…</p>:reconciliation.isError?<p role="alert">Reconciliation history unavailable.</p>:<>{reconciliation.data?.rows.length===0&&<p>No recorded reconciliation runs.</p>}{reconciliation.data?.rows.map(row=><article className="j6-record" key={row.reconciliation_id}><h3>{row.provider} · {row.status}</h3><p>{row.period_start} – {row.period_end} · recorded estimate {amount(row.computed_cost_usd)} · authoritative amount {amount(row.authoritative_cost_usd)}</p><p className="j1-note">Recorded at {row.created_at}</p></article>)}</>}
    </section>
    <div className="j5-panel"><h2>Quality coverage</h2><p className="j1-note">Quality measurements are unavailable. Recorded usage, spend or response times do not establish answer quality.</p></div>
  </div>
}
