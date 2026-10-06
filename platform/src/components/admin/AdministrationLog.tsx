'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { PageTitle } from '@/components/journey1/Titles'
import { AuditLogPanel } from './AuditLogPanel'
import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'
export function AdministrationLog() {
  const { userId } = useObservatoryScope()
  const [source,setSource] = useState('all'), [action,setAction] = useState(''), [cursor,setCursor] = useState('')
  const params = new URLSearchParams({source,limit:'50'})
  if (action.trim()) params.set('action',action.trim())
  if (cursor) params.set('cursor',cursor)
  const state = useQuery({ queryKey:['admin',userId,'audit',params.toString()], queryFn:async () => {
    const response = await fetch(`/api/admin/audit-log?${params}`,{cache:'no-store'})
    if (!response.ok) throw Error('Administration log is unavailable.')
    return await response.json() as {entries:AuditLogEntry[];nextCursor:string|null;coverage:string}
  }})
  return <div className="j6-evidence"><PageTitle name="administrationLog" />
    <p className="j1-note">Portal scope · administrative and AI configuration actions, newest first.</p>
    <div className="j6-scope"><label>Record source<select value={source} onChange={event => {setSource(event.target.value);setCursor('')}}><option value="all">All sources</option><option value="administration">Administration</option><option value="ai_configuration">AI configuration</option></select></label>
      <label>Exact action<input maxLength={128} value={action} onChange={event => {setAction(event.target.value);setCursor('')}} placeholder="All actions" /></label></div>
    {state.isPending && <p role="status">Loading records…</p>}
    {state.isError && <div role="alert">Could not read the log. <button onClick={() => void state.refetch()}>Try again</button></div>}
    {state.data && !state.isError && <><p className="j1-note">{state.data.coverage}</p><AuditLogPanel entries={state.data.entries} />
      <div className="j6-links">{cursor && <button onClick={() => setCursor('')}>Newest records</button>}{state.data.nextCursor && <button onClick={() => setCursor(state.data!.nextCursor!)}>Older records</button>}</div></>}
  </div>
}
