import 'server-only'
import { z } from 'zod'
import { query } from '@/lib/db/client'
import { parseUsageFilter, usageSummary } from '@/lib/metering/queries'
export function accountingPeriod(month: string) {
  z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/).parse(month)
  const [year,value] = month.split('-').map(Number)
  if (year < 2000 || year > 2100) throw Error('Invalid accounting year')
  return {from:new Date(Date.UTC(year,value-1,1)).toISOString(),to:new Date(Date.UTC(year,value,1)).toISOString()}
}
export async function monthlyAccounting(month: string) {
  const period = accountingPeriod(month)
  const {rows:rules} = await query<{budget_rule_id:string;name:string;scope:string;scope_value:string|null;amount_usd:string}>(
    "SELECT budget_rule_id,name,scope,scope_value,amount_usd::text FROM llm_budget_rules WHERE active=true AND period='monthly' ORDER BY created_at,budget_rule_id LIMIT 100")
  const rows = await Promise.all(rules.map(async rule => {
    if (!['total','provider','model'].includes(rule.scope)) return {...rule,available:false,summary:null,note:'This rule’s scope has no verified mapping to the normalized activity ledger.'}
    const url = new URL('http://localhost/accounting')
    url.searchParams.set('from',period.from);url.searchParams.set('to',period.to)
    if (rule.scope !== 'total' && rule.scope_value) url.searchParams.set(rule.scope,rule.scope_value)
    if (rule.scope !== 'total' && !rule.scope_value) return {...rule,available:false,summary:null,note:'Rule scope value is missing.'}
    try { return {...rule,available:true,summary:await usageSummary(parseUsageFilter(url,{ownerId:null}),{ownerId:null}),note:'Known estimates, provider receipts and unpriced records are separate. No budget alert is emitted by this read.'} }
    catch { return {...rule,available:false,summary:null,note:'Monthly ledger could not be read.'} }
  }))
  return {month,...period,scope:'portal',rows,note:'Monthly budget accounting is portal-wide and uses its own UTC calendar month. Activity-window and selected-user filters do not redefine a budget. Up to 100 active monthly rules; daily/weekly controls retain their existing APIs.'}
}
