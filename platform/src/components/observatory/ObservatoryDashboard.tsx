'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useObservatoryScope } from './ObservatoryScope'

type View = 'overview' | 'analytics' | 'consumption'
type Totals = Record<string, number | string | null> & {
  transport_attempts: number; transport_success: number; transport_failed: number; transport_pending: number;
  complete_usage: number; transport_unpriced: number; input_tokens: string | null; output_tokens: string | null;
  known_transport_cost_usd: string | null; legacy_records: number; legacy_estimate_usd: string | null;
  p50_success_ms: number | null
}
type Group = Totals & { name: string | null }
type Conversation = {
  key: string; conversation_id: string | null; user_id: string; channel: string; purpose: string; model: string;
  first_at: string; last_at: string; turns: number; attempts: number; success: number; incomplete_usage: number;
  unpriced: number; input_tokens: string | null; output_tokens: string | null; known_cost_usd: string | null; snippet: string | null
}
type Attempt = {
  id: string; turn_id: string; operation_id: string; parent_operation_id: string | null;
  channel: string; purpose: string; provider: string; model: string; role: string; status: string; aggregation: string;
  evidence: string; started_at: string; finished_at: string | null; usage: { input?: number | null; output?: number | null;
    cacheRead?: number | null; cacheWrite?: number | null; reasoning?: number | null; source?: string } | null;
  computed_cost_usd: string | null; pricing_status: string | null; provider_request_id: string | null;
  pricing_snapshot: unknown
}
const nf = new Intl.NumberFormat('en-IN')
const money = (value: string | null | undefined) => value == null ? 'Not priced' : `$${Number(value).toFixed(4)}`
const number = (value: string | number | null | undefined) => value == null ? 'Not reported' : nf.format(Number(value))
const seconds = (ms: number | null | undefined) => ms == null ? 'Not reported' : `${(Number(ms) / 1000).toFixed(2)} s`
const date = (value: string) => new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
const card = 'rounded-xl border border-[#382b18] bg-[#14110b] p-5'
const eyebrow = 'text-xs uppercase tracking-[0.17em] text-[#ac8a48]'

function useMetering<T>(url: string | null) {
  const [result, setResult] = useState<{ url: string | null; data: T | null; error: string | null; revision: number }>({ url: null, data: null, error: null, revision: 0 })
  const retry = useCallback(() => setResult(current => ({ ...current, url: null, data: null, error: null, revision: current.revision + 1 })), [])
  useEffect(() => {
    if (!url) return
    const controller = new AbortController()
    fetch(url, { signal: controller.signal, cache: 'no-store' }).then(async response => {
      if (!response.ok) throw new Error(response.status === 404 ? 'Metering is not enabled.' : 'Activity could not be loaded.')
      return response.json() as Promise<T>
    }).then(data => setResult(current => ({ ...current, url, data, error: null })))
      .catch(error => { if (!controller.signal.aborted) setResult(current => ({ ...current, url, data: null, error: String(error.message) })) })
    return () => controller.abort()
  }, [url, result.revision])
  return { data: result.url === url ? result.data : null, error: result.url === url ? result.error : null,
    loading: Boolean(url && result.url !== url), retry }
}

function Trend({ groups, metric, label, secondaryMetric }: { groups: Group[]; metric: 'transport_attempts' | 'transport_success' | 'p50_success_ms'; label: string; secondaryMetric?: 'transport_success' }) {
  const sorted = groups.filter(group => Number(group.transport_attempts) > 0).sort((a, b) => String(a.name).localeCompare(String(b.name)))
  const values = sorted.map(group => Number(group[metric] ?? 0) / (metric === 'p50_success_ms' ? 1000 : 1))
  const secondary = secondaryMetric ? sorted.map(group => Number(group[secondaryMetric] ?? 0)) : []
  const max = Math.max(1, ...values, ...secondary)
  const points = values.map((value, index) => `${32 + (index * 620 / Math.max(1, values.length - 1))},${177 - (value / max) * 140}`).join(' ')
  const secondaryPoints = secondary.map((value, index) => `${32 + (index * 620 / Math.max(1, values.length - 1))},${177 - (value / max) * 140}`).join(' ')
  if (!sorted.length) return <p className="py-12 text-center text-sm text-[#a99c82]">No AI activity in this period.</p>
  return <div className="overflow-x-auto" role="img" aria-label={`${label} over time, from ${sorted[0].name} to ${sorted.at(-1)?.name}`}>
    <svg viewBox="0 0 684 215" className="min-w-[480px] w-full" aria-hidden="true">
      {[37, 107, 177].map(y => <line key={y} x1="32" x2="652" y1={y} y2={y} stroke="#382b18" />)}
      <polyline points={points} fill="none" stroke="#d2a23c" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      {secondaryMetric && <polyline points={secondaryPoints} fill="none" stroke="#8caa90" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />}
      {values.map((value, index) => <circle key={index} cx={32 + index * 620 / Math.max(1, values.length - 1)} cy={177 - value / max * 140} r="3" fill="#ecc56a"><title>{sorted[index].name}: {value.toFixed(metric === 'p50_success_ms' ? 2 : 0)}</title></circle>)}
      <text x="32" y="205" fill="#a99c82" fontSize="11">{sorted[0].name}</text>
      <text x="652" y="205" textAnchor="end" fill="#a99c82" fontSize="11">{sorted.at(-1)?.name}</text>
    </svg>
  </div>
}

function FilterBar({ view, channel, setChannel, provider, setProvider, model, setModel, purpose, setPurpose, customWindow, onPeriodChange }: {
  view: View; channel: string; setChannel: (value: string) => void; provider: string; setProvider: (value: string) => void;
  model: string; setModel: (value: string) => void; purpose: string; setPurpose: (value: string) => void;
  customWindow: boolean; onPeriodChange: (value: string) => void
}) {
  const scope = useObservatoryScope()
  return <div className="flex flex-wrap items-end gap-3 rounded-xl border border-[#382b18] bg-[#14110b] p-4">
    {scope.admin && <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">View
      <select aria-label="Activity scope" value={scope.scope} onChange={event => scope.setScope(event.target.value as 'mine' | 'portal' | 'user')} className="rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]">
        <option value="mine">My activity</option><option value="portal">Entire portal</option><option value="user">Select a user</option>
      </select></label>}
    {scope.admin && scope.scope === 'user' && <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">User
      <select aria-label="Select a user" value={scope.selectedUserId} onChange={event => scope.setSelectedUserId(event.target.value)} className="rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]">
        <option value="">Choose a user</option>{scope.users.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
      </select></label>}
    <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">Period
      <select aria-label="Period" value={customWindow ? 'custom' : scope.period} onChange={event => onPeriodChange(event.target.value)} className="rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]">
        {customWindow && <option value="custom">Bookmarked dates</option>}
        <option value="today">Today · UTC</option><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option>
      </select></label>
    {view !== 'overview' && <>
      <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">Channel<select aria-label="Channel" value={channel} onChange={event => setChannel(event.target.value)} className="rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]">
        <option value="">All channels</option>{['web', 'mcp', 'api', 'backend', 'scheduled', 'unknown'].map(value => <option key={value}>{value}</option>)}
      </select></label>
      <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">Provider<input aria-label="Provider" value={provider} onChange={event => setProvider(event.target.value)} placeholder="All providers" className="w-36 rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]" /></label>
      <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">Model<input aria-label="Model" value={model} onChange={event => setModel(event.target.value)} placeholder="All models" className="w-44 rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]" /></label>
      {view === 'consumption' && <label className="flex flex-col gap-1 text-xs text-[#ac8a48]">Purpose<select aria-label="Purpose" value={purpose} onChange={event => setPurpose(event.target.value)} className="rounded-md border border-[#4a381c] bg-[#0a0806] px-3 py-2 text-sm text-[#e8dfc9]">
        <option value="">All purposes</option>{['customer', 'admin_test', 'validation', 'evaluation', 'background', 'legacy'].map(value => <option key={value} value={value}>{value.replace('_', ' ')}</option>)}
      </select></label>}
    </>}
  </div>
}

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return <div className={card}><p className={eyebrow}>{label}</p><p className="mt-3 text-3xl text-[#ecc56a] tabular-nums" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>{value}</p>{note && <p className="mt-2 text-xs text-[#a99c82]">{note}</p>}</div>
}

interface InitialFilters { from?: string; to?: string; channel?: string; provider?: string; model?: string; purpose?: string }
export function ObservatoryDashboard({ view, initialFilters }: { view: View; initialFilters?: InitialFilters }) {
  const scope = useObservatoryScope()
  const [channel, setChannel] = useState(initialFilters?.channel ?? '')
  const [provider, setProvider] = useState(initialFilters?.provider ?? '')
  const [model, setModel] = useState(initialFilters?.model ?? '')
  const [purpose, setPurpose] = useState(initialFilters?.purpose ?? '')
  const [customWindow, setCustomWindow] = useState(initialFilters?.from && initialFilters?.to ? { from: initialFilters.from, to: initialFilters.to } : null)
  const onPeriodChange = (period: string) => {
    if (period === 'custom') return
    setCustomWindow(null)
    scope.setPeriod(period as 'today' | '7d' | '30d')
  }
  const params = useMemo(() => {
    const query = new URLSearchParams(scope.scopeParams)
    query.set('from', customWindow?.from ?? scope.from); query.set('to', customWindow?.to ?? scope.to)
    if (view !== 'overview') {
      if (channel) query.set('channel', channel)
      if (provider.trim()) query.set('provider', provider.trim())
      if (model.trim()) query.set('model', model.trim())
      if (purpose) query.set('purpose', purpose)
    }
    return query.toString()
  }, [scope.scopeParams, scope.from, scope.to, view, channel, provider, model, purpose, customWindow])
  const ready = scope.scope !== 'user' || Boolean(scope.selectedUserId)
  const url = (viewName: string, groupBy?: string) => ready ? `${scope.endpoint}?${params}&view=${viewName}${groupBy ? `&groupBy=${groupBy}` : ''}` : null
  const summary = useMetering<Totals>(url('summary'))
  const daily = useMetering<{ groups: Group[] }>(view !== 'consumption' ? url('breakdown', 'day') : null)
  const compare = useMetering<{ groups: Group[] }>(view === 'analytics' ? url('breakdown', 'model') : view === 'overview' ? url('breakdown', 'channel') : null)
  const conversationUrl = url('conversations')
  const conversations = useMetering<{ conversations: Conversation[]; nextCursor: string | null }>(view === 'consumption' && conversationUrl ? `${conversationUrl}&limit=25` : null)
  const title = view[0].toUpperCase() + view.slice(1)
  const noData = summary.data && summary.data.transport_attempts === 0 && (view !== 'consumption' || summary.data.legacy_records === 0)
  const loading = summary.loading || (view !== 'consumption' && daily.loading) || (view === 'consumption' && conversations.loading) || (view !== 'consumption' && compare.loading)
  const error = summary.error || (view === 'consumption' ? conversations.error : daily.error || compare.error)
  return <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-8">
    <div><p className={eyebrow}>AI operations · {scope.admin ? scope.scope === 'portal' ? 'Entire portal' : scope.scope === 'user' ? 'Selected user' : 'My activity' : 'My activity'}</p>
      <h1 className="mt-1 text-4xl text-[#d2a23c] sm:text-5xl" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif', fontVariant: 'small-caps', letterSpacing: '.05em' }}>{title}</h1>
      <p className="mt-2 text-sm text-[#a99c82]">{view === 'overview' ? 'A clear view of model activity and response health.' : view === 'analytics' ? 'Compare model activity and response time.' : 'Every recorded call, organized by conversation and question.'}</p></div>
    <FilterBar view={view} channel={channel} setChannel={setChannel} provider={provider} setProvider={setProvider} model={model} setModel={setModel} purpose={purpose} setPurpose={setPurpose} customWindow={Boolean(customWindow)} onPeriodChange={onPeriodChange} />
    {!ready && <div className={card}>Choose a user to see their activity.</div>}
    {ready && loading && <div className={card} role="status">Loading activity…</div>}
    {ready && !loading && error && <div className={card} role="alert"><p>{error}</p><button className="mt-3 rounded-md border border-[#a87c2a] px-3 py-2 text-sm text-[#ecc56a]" onClick={() => { summary.retry(); daily.retry(); compare.retry(); conversations.retry() }}>Try again</button></div>}
    {ready && !loading && !error && noData && <div className={card}><p className="text-lg text-[#ecc56a]">No AI activity in this period</p><p className="mt-1 text-sm text-[#a99c82]">Try a longer period or another scope.</p></div>}
    {ready && !loading && !error && summary.data && !noData && view === 'overview' && <>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Calls" value={number(summary.data.transport_attempts)} note="Provider attempts, including retries" />
        <Stat label="Success rate" value={`${Math.round(summary.data.transport_success / summary.data.transport_attempts * 100)}%`} note={`${number(summary.data.transport_success)} successful · ${number(summary.data.transport_pending)} pending`} />
        <Stat label="Median duration" value={seconds(summary.data.p50_success_ms)} note="Successful provider attempts" />
        <Stat label="Channels" value={number(compare.data?.groups.filter(group => Number(group.transport_attempts) > 0).length)} note="With recorded calls" />
      </div>
      <section className={card}><h2 className="text-xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Call activity · UTC</h2><p className="mt-1 text-xs text-[#a99c82]">Gold: all model calls · green: successful calls. Each recorded transport leaf is counted once.</p><Trend groups={daily.data?.groups ?? []} metric="transport_attempts" secondaryMetric="transport_success" label="Provider calls and successful calls" />
        <details className="text-xs text-[#c8bda6]"><summary className="cursor-pointer text-[#d2a23c]">View daily values</summary><table className="mt-2 w-full max-w-sm text-left"><thead><tr><th>Day · UTC</th><th>Calls</th><th>Successful</th></tr></thead><tbody>{(daily.data?.groups ?? []).filter(group => Number(group.transport_attempts) > 0).sort((a, b) => String(a.name).localeCompare(String(b.name))).map(group => <tr key={group.name}><td>{group.name}</td><td>{number(group.transport_attempts)}</td><td>{number(group.transport_success)}</td></tr>)}</tbody></table></details>
      </section>
      <section className={card}><h2 className="text-xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Channel distribution</h2><div className="mt-4 grid gap-3 sm:grid-cols-3">{(compare.data?.groups ?? []).filter(group => Number(group.transport_attempts)).map(group => <div key={group.name ?? 'unknown'} className="rounded-md border border-[#382b18] p-3"><p className={eyebrow}>{group.name || 'Unknown'}</p><p className="mt-1 text-2xl tabular-nums">{number(group.transport_attempts)}</p></div>)}</div></section>
    </>}
    {ready && !loading && !error && summary.data && !noData && view === 'analytics' && <>
      <div className="grid gap-3 sm:grid-cols-3"><Stat label="Calls" value={number(summary.data.transport_attempts)} /><Stat label="Successful" value={number(summary.data.transport_success)} /><Stat label="Median response" value={seconds(summary.data.p50_success_ms)} /></div>
      <section className={card}><h2 className="text-xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Median response time · seconds</h2><Trend groups={daily.data?.groups ?? []} metric="p50_success_ms" label="Median response time in seconds" /></section>
      <section className={`${card} overflow-x-auto`}><h2 className="mb-4 text-xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Models</h2><table className="w-full min-w-[600px] text-left text-sm"><thead className="border-b border-[#382b18] text-[#ac8a48]"><tr><th className="py-2">Model</th><th>Calls</th><th>Success</th><th>Median response</th><th>Incomplete usage</th></tr></thead><tbody>{(compare.data?.groups ?? []).filter(group => Number(group.transport_attempts)).map(group => <tr key={group.name ?? 'unknown'} className="border-b border-[#2d2416]"><td className="py-3">{group.name || 'Unknown'}</td><td>{number(group.transport_attempts)}</td><td>{number(group.transport_success)}</td><td>{seconds(group.p50_success_ms)}</td><td>{number(group.transport_attempts - group.complete_usage)}</td></tr>)}</tbody></table></section>
    </>}
    {ready && !loading && !error && summary.data && !noData && view === 'consumption' && <Consumption key={params} summary={summary.data} initial={conversations.data} baseUrl={`${scope.endpoint}?${params}`} portal={scope.scope === 'portal'} />}
  </main>
}

function Consumption({ summary, initial, baseUrl, portal }: { summary: Totals; initial: { conversations: Conversation[]; nextCursor: string | null } | null; baseUrl: string; portal: boolean }) {
  const { users } = useObservatoryScope()
  const [extra, setExtra] = useState<{ base: typeof initial; rows: Conversation[]; cursor: string | null } | null>(null)
  const rows = [...(initial?.conversations ?? []), ...(extra?.base === initial ? extra.rows : [])]
  const cursor = extra?.base === initial ? extra.cursor : initial?.nextCursor ?? null
  const [loadingMore, setLoadingMore] = useState(false)
  const complete = summary.transport_attempts ? Math.round(summary.complete_usage / summary.transport_attempts * 100) : 0
  const partial = summary.complete_usage < summary.transport_attempts || summary.transport_unpriced > 0
  async function more() {
    if (!cursor || loadingMore) return
    setLoadingMore(true)
    try {
      const response = await fetch(`${baseUrl}&view=conversations&limit=25&cursor=${encodeURIComponent(cursor)}`, { cache: 'no-store' })
      if (!response.ok) throw new Error('Could not load more conversations')
      const next = await response.json() as { conversations: Conversation[]; nextCursor: string | null }
      setExtra(current => ({ base: initial, rows: [...(current?.base === initial ? current.rows : []), ...next.conversations], cursor: next.nextCursor }))
    } catch { setExtra(current => ({ base: initial, rows: current?.base === initial ? current.rows : [], cursor: null })) } finally { setLoadingMore(false) }
  }
  return <>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Stat label="Recorded input" value={number(summary.input_tokens)} note={partial ? 'Partial where calls lack usage' : 'Tokens across provider calls'} />
      <Stat label="Recorded output" value={number(summary.output_tokens)} note={partial ? 'Partial where calls lack usage' : 'Tokens across provider calls'} />
      <Stat label="Known model cost" value={money(summary.known_transport_cost_usd)} note={summary.transport_unpriced ? `${summary.transport_unpriced} calls not priced` : 'Recorded provider calls'} />
      <Stat label="Complete call evidence" value={summary.transport_attempts ? `${complete}%` : 'No calls'} note={summary.transport_attempts ? `${summary.complete_usage} of ${summary.transport_attempts} calls have input and output` : 'Historical estimates are listed below'} />
    </div>
    {partial && <p className="rounded-md border border-[#604720] bg-[#20190d] px-4 py-3 text-sm text-[#e1c88b]">Totals include only reported tokens and priced calls. Calls without a usage receipt or applicable rate remain visible below.</p>}
    <section className="space-y-3"><div className="flex flex-wrap items-end justify-between gap-2"><h2 className="text-2xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Conversations and activity</h2><a className="text-xs text-[#d2a23c] underline" href={`${baseUrl}&view=export&limit=1000`}>Export visible scope · first 1,000 records</a></div>
      {rows.map(row => <ConversationRow key={`${row.user_id}:${row.key}`} row={row} baseUrl={baseUrl} portal={portal}
        ownerName={users.find(user => user.id === row.user_id)?.name || 'Member'} />)}
      {!rows.length && <div className={card}>No transport calls are recorded for this period. Older aggregate records are shown separately below.</div>}
      {cursor && <button onClick={more} disabled={loadingMore} className="rounded-md border border-[#a87c2a] px-4 py-2 text-sm text-[#ecc56a]">{loadingMore ? 'Loading…' : 'Show more activity'}</button>}
    </section>
    {summary.legacy_records > 0 && <section className={card}><h2 className="text-xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Historical estimates</h2><p className="mt-2 text-sm text-[#a99c82]">{number(summary.legacy_records)} older aggregate records are separate from the call totals above. Estimated cost: {money(summary.legacy_estimate_usd)}. These records may not include every provider call or token category.</p></section>}
  </>
}

function ConversationRow({ row, baseUrl, portal, ownerName }: { row: Conversation; baseUrl: string; portal: boolean; ownerName: string }) {
  const [open, setOpen] = useState(false)
  const [attempts, setAttempts] = useState<Attempt[] | null>(null)
  const [error, setError] = useState(false)
  async function toggle() {
    setOpen(current => !current)
    if (attempts || open) return
    try {
      const selector = row.conversation_id ? `conversationId=${encodeURIComponent(row.conversation_id)}` : `recordId=${encodeURIComponent(row.key)}`
      const response = await fetch(`${baseUrl}&view=trace&${selector}&limit=1000`, { cache: 'no-store' })
      if (!response.ok) throw new Error('Trace unavailable')
      const data = await response.json() as { events: Attempt[] }
      setAttempts(data.events.filter(event => event.evidence === 'metered' && event.aggregation === 'transport')
        .sort((a, b) => a.started_at.localeCompare(b.started_at) || a.id.localeCompare(b.id)))
    } catch { setError(true) }
  }
  const title = row.snippet || (portal ? 'Portal activity' : row.conversation_id ? 'Conversation activity' : `${row.purpose === 'admin_test' ? 'Admin test' : row.channel.toUpperCase() + ' activity'}`)
  const byTurn = new Map<string, Attempt[]>()
  for (const attempt of attempts ?? []) byTurn.set(attempt.turn_id, [...(byTurn.get(attempt.turn_id) ?? []), attempt])
  return <article className={card}>
    <button aria-expanded={open} onClick={toggle} className="flex w-full flex-wrap items-start justify-between gap-3 text-left"><span><span className="block text-base text-[#e8dfc9]">{title}</span><span className="mt-1 block text-xs text-[#a99c82]">{date(row.last_at)} · {row.channel} · {row.purpose}{portal ? ' · ' + ownerName : ''}</span></span><span className="text-xs text-[#d2a23c]">{open ? 'Hide details' : 'See questions and calls'}</span></button>
    <p className="mt-3 text-sm text-[#c8bda6]">{row.turns} questions · {row.attempts} calls · {number(row.input_tokens)} input · {number(row.output_tokens)} output · {money(row.known_cost_usd)}</p>
    {(row.incomplete_usage > 0 || row.unpriced > 0) && <p className="mt-2 text-xs text-[#d2b872]">{row.incomplete_usage > 0 && `${row.incomplete_usage} calls without complete usage`}{row.incomplete_usage > 0 && row.unpriced > 0 && ' · '}{row.unpriced > 0 && `${row.unpriced} calls not priced`}</p>}
    {open && <div className="mt-4 space-y-4 border-t border-[#382b18] pt-4">{error && <p role="alert">Call details could not be loaded.</p>}{!attempts && !error && <p>Loading calls…</p>}{[...byTurn.entries()].map(([turnId, calls], index) => <div key={turnId} className="rounded-md border border-[#382b18] p-3"><h3 className="text-sm text-[#ecc56a]">Question {index + 1} · {calls.length} model {calls.length === 1 ? 'call' : 'calls'}</h3>{calls.map(call => <div key={call.id} className="mt-3 border-l border-[#a87c2a] pl-3 text-xs text-[#c8bda6]"><p className="text-sm text-[#e8dfc9]">{call.provider} · {call.model} · {call.role} · {call.status}</p><p className="mt-1">{date(call.started_at)} · {number(call.usage?.input)} input · {number(call.usage?.output)} output · {money(call.computed_cost_usd)}</p><p className="mt-1">{call.usage?.source === 'unavailable' || !call.usage
      ? call.status === 'pending' ? 'The call is pending; usage has not yet arrived.'
        : call.status === 'success' ? 'The provider did not report usage for this call.'
          : `The call ended as ${call.status} without reported usage.`
      : `Usage source: ${call.usage.source || 'not reported'}`}{!call.computed_cost_usd ? call.usage?.input == null || call.usage?.output == null ? ' Cost cannot be calculated without complete usage.' : ' No applicable rate was recorded.' : ''}</p><details className="mt-2"><summary className="cursor-pointer text-[#ac8a48]">Technical details</summary><dl className="mt-2 grid gap-1"><div>Attempt: {call.id}</div><div>Turn: {call.turn_id}</div><div>Operation: {call.operation_id}</div>{call.provider_request_id && <div>Provider request: {call.provider_request_id}</div>}{call.pricing_status && <div>Pricing: {call.pricing_status}</div>}{call.usage && <div>Cache read {number(call.usage.cacheRead)} · cache write {number(call.usage.cacheWrite)} · reasoning {number(call.usage.reasoning)}</div>}{call.pricing_snapshot != null && <div>Rate snapshot: {JSON.stringify(call.pricing_snapshot)}</div>}</dl></details></div>)}</div>)}{attempts && attempts.length === 1000 && <p className="text-xs text-[#d2b872]">Showing the first 1,000 calls. Use the scoped export for a complete audit.</p>}</div>}
  </article>
}
