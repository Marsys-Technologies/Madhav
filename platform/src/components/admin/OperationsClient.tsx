'use client'
import Link from 'next/link'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PageTitle, type PageName } from '@/components/journey1/Titles'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import type { OperationSection, OperationsEvidence, EvidenceRow, EvidenceSource } from '@/lib/admin/operations'

const TITLES: Record<OperationSection, PageName> = { foundation:'systemFoundation', health:'mcpHealth', assets:'assetRegister', programme:'programmeRecord', learning:'learningReview' }
const display = (value: EvidenceRow[string]) => value == null ? 'Not reported' : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)
function SourceRecords({source,section}:{source:EvidenceSource;section:OperationSection}) {
  const [search,setSearch]=useState(''),[page,setPage]=useState(0)
  const filtered=source.rows.filter(row=>Object.values(row).some(value=>display(value).toLocaleLowerCase().includes(search.toLocaleLowerCase())))
  const currentPage=Math.min(page,Math.max(0,Math.ceil(filtered.length/25)-1))
  return <section className="j5-panel">
    <h2>{source.title}</h2><p className="j1-note">Source: {source.source}</p><p className="j1-note">{source.note}</p>
    {!source.available ? <p role="status">Unavailable</p> : source.rows.length===0 ? <p>No records returned by this source.</p> : <>
      {(source.rows.length>25 || search) && <label className="j6-search">Search {source.title}<input value={search} onChange={event=>{setSearch(event.target.value);setPage(0)}} /></label>}
      <p className="j1-note">{filtered.length} records in this returned result · showing {filtered.length?currentPage*25+1:0}–{Math.min((currentPage+1)*25,filtered.length)}</p>
      <div className="j6-records">{filtered.slice(currentPage*25,(currentPage+1)*25).map((row,index)=><article className="j6-record" key={index}><dl>
        {Object.entries(row).map(([key,value])=><div style={{display:'contents'}} key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{display(value)}</dd></div>)}
      </dl>{typeof row.chart_id==='string' && <Link href={`/clients/${encodeURIComponent(row.chart_id)}/${section==='learning'?'samiksha':'nirmana'}`}>Open chart {section==='learning'?'review':'preparation'}</Link>}</article>)}</div>
      {filtered.length>25 && <div className="j6-links"><button disabled={currentPage===0} onClick={()=>setPage(currentPage-1)}>Previous records</button><button disabled={(currentPage+1)*25>=filtered.length} onClick={()=>setPage(currentPage+1)}>Next records</button></div>}
    </>}
  </section>
}
export function OperationsClient({ section }: { section: OperationSection }) {
  const { userId } = useObservatoryScope()
  const state = useQuery({ queryKey:['admin',userId,'operations',section], queryFn:async () => {
    const response = await fetch(`/api/admin/operations/${section}`,{cache:'no-store'})
    if (!response.ok) throw Error('Operational evidence is unavailable.')
    return await response.json() as OperationsEvidence
  }})
  return <div className="j6-evidence">
    <PageTitle name={TITLES[section]} />
    <p className="j1-note">Portal scope · recorded evidence. Missing measurements remain unknown.</p>
    {section === 'health' && <Link href="/admin/trace">Inspect recorded query sessions and traces</Link>}
    {section === 'assets' && <Link href="/admin/tracker">Open retained build tracker detail</Link>}
    {section === 'programme' && <div className="j6-links"><Link href="/admin/nirmana-elevation">Historical elevation detail</Link><Link href="/cockpit">Operational cockpit</Link><Link href="/cockpit/command-center">Command centre</Link></div>}
    {state.isPending && <p role="status">Loading evidence…</p>}
    {state.isError && <div role="alert" className="j5-panel">Evidence could not be read. <button onClick={() => void state.refetch()}>Try again</button></div>}
    {state.data && !state.isError && <>
      <p className="j1-note">Read at {state.data.generatedAt} · this is the read time, not source refresh verification.</p>
      {state.data.notes.map(note => <p key={note} className="j1-note">{note}</p>)}
      {state.data.sources.map(source => <SourceRecords source={source} section={section} key={source.source} />)}
      <button className="j1-button" onClick={() => void state.refetch()}>Refresh evidence</button>
    </>}
  </div>
}
