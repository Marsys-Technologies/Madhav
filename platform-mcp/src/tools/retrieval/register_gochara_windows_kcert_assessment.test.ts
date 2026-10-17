import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchVerseRefs, enrichWindowsWithVerseRefs, type GocharaWindowRow } from './register_gochara_windows.js'
const principal = { user_uid: 'kcert-assessment', key_id: 'kcert-assessment', role: 'super_admin' as const }
afterEach(() => vi.restoreAllMocks())
const stored = [
 { citation_string: 'known', chunk_id: 'real-chunk', text_id: 'real-text', verse_ref: '1.2', status: 'resolved' },
 { citation_string: 'gap', chunk_id: 'CORPUS_GAP:gap', text_id: 'unknown', verse_ref: 'unresolved', status: 'unresolved' },
]
function proxy(rows: Record<string, unknown>[]) {
 const calls: {sql: string; params: unknown[]}[] = []
 vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
   const call = JSON.parse(String(init?.body)); calls.push(call)
   // Honor the real SELECT projection: dropping status must lose the stored value.
   const projection = /SELECT\s+([\s\S]*?)\s+FROM\s+bg_gochara_citation_resolution/i.exec(call.sql)?.[1]?.split(',').map(s => s.trim()) ?? []
   return { ok: true, json: async () => ({ rows: rows.map(r => Object.fromEntries(Object.entries(r).filter(([k]) => projection.includes(k)))) }) } as Response
 })
 return calls
}
function enrich(map: Awaited<ReturnType<typeof fetchVerseRefs>>, citations: string[]) {
 const row = { active_sentences: citations.map(c => ({ classical_citation: c })) } as GocharaWindowRow
 return enrichWindowsWithVerseRefs([row], [row], map)[0]!
}
describe('Independent bounded K-CERT assessment', () => {
 it('selects stored status and serves resolved, stored unresolved, and absent-row honest gap distinctly', async () => {
  const calls = proxy(stored)
  const map = await fetchVerseRefs(new Set(['known','gap','absent']), principal)
  expect(calls).toHaveLength(1)
  expect(calls[0]!.sql).toMatch(/SELECT\s+citation_string, chunk_id, text_id, verse_ref, status\s+FROM bg_gochara_citation_resolution/)
  expect(calls[0]!.params).toEqual(['known','gap','absent'])
  expect(calls[0]!.sql).not.toMatch(/WHERE[\s\S]*status\s*=/i)
  const result = enrich(map,['known','gap','absent'])
  expect(result.citation_verse_refs).toEqual([...stored,{citation_string:'absent',chunk_id:'CORPUS_GAP:absent',text_id:'unknown',verse_ref:'unresolved',status:'unresolved'}])
  expect(result.citation_resolution_note).toContain('1 citation(s) resolved')
  for (const ref of result.citation_verse_refs) {
   expect(ref).not.toHaveProperty('verification_pass_status')
   expect(ref).not.toHaveProperty('prose_verified')
   expect(ref).not.toHaveProperty('value_verified')
  }
 })
 it('preserves the returned stored resolved status through query projection', async () => {
  proxy(stored); const map=await fetchVerseRefs(new Set(['known','gap']),principal)
  expect(enrich(map,['known','gap']).citation_verse_refs.map(r=>r.status)).toEqual(['resolved','unresolved'])
 })
 it('all-unresolved rows earn the honest gap note; no citations earn empty refs and null note', async () => {
  proxy([stored[1]!]); const map = await fetchVerseRefs(new Set(['gap']), principal)
  const result = enrich(map,['gap','absent'])
  expect(result.citation_verse_refs.map(r=>r.status)).toEqual(['unresolved','unresolved'])
  expect(result.citation_resolution_note).toContain('none resolved to corpus chunks yet')
  expect(enrich(new Map(),[])).toMatchObject({citation_verse_refs:[],citation_resolution_note:null})
 })
 it('null/missing returned status stays unresolved and a query failure exposes an honest gap', async () => {
  proxy([{...stored[0],status:null}]); const map=await fetchVerseRefs(new Set(['known']),principal)
  expect(map.get('known')?.[0]?.status).toBe('unresolved')
  vi.restoreAllMocks();vi.spyOn(globalThis,'fetch').mockRejectedValue(new Error('fixture unavailable'))
  const unavailable=await fetchVerseRefs(new Set(['known']),principal)
  expect(unavailable.size).toBe(0)
  expect(enrich(unavailable,['known']).citation_verse_refs[0]).toMatchObject({status:'unresolved',chunk_id:'CORPUS_GAP:known'})
 })
})
