import { existsSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, it } from 'vitest'
import { ArrivalLine } from '@/components/pariprashna/ArrivalLine'
const chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
const snapshot = (state: string) => ({ view: 'now', chart_id, manifest_id: 'manifest', generation: 'g1', empty_reason: null,
  manifest: { manifest_id: 'manifest', generation: 'g1' },
  rows: [{ source_table: 'kala_obstruction', qualification: 'published', data: { generation: 'g1', assertion: {
    payload: { effective_state: state, release: { kind: 'unknown', instant: null } },
  } } }], pagination: { more_available: false } })
it.each([['information_unavailable', 'information unavailable'], ['evaluated_silent', 'evaluated silence']])
  ('the unchanged ArrivalLine renders the honest planted %s without a release guess', async (state, label) => {
    expect(existsSync(new URL('./arrival_state.ts', import.meta.url))).toBe(true)
    const { arrivalFromPublishedNow } = await import('./arrival_state')
    const arrival = arrivalFromPublishedNow(chart_id, snapshot(state))
    expect(arrival).toMatchObject({ text: `Kāla · ${label}`, manifest_id: 'manifest', generation: 'g1', effective_states: [state] })
    const html=renderToStaticMarkup(createElement(ArrivalLine, { arrival }))
    expect(html).toContain(label)
    expect(html).not.toContain(state === 'information_unavailable' ? 'evaluated silence' : 'information unavailable')
    expect(html).not.toMatch(/release|2027|fourth year/)
  })
it.each(['wrong_chart','wrong_manifest','wrong_generation','context','empty','unknown','unpublished'])
  ('unusable %s stays an honest null in the Portal component', async mutation => {
    expect(existsSync(new URL('./arrival_state.ts', import.meta.url))).toBe(true)
    const { arrivalFromPublishedNow } = await import('./arrival_state')
    const data=snapshot('evaluated_silent')
    if(mutation==='wrong_chart') data.chart_id='other'
    if(mutation==='wrong_manifest') data.manifest.manifest_id='other'
    if(mutation==='wrong_generation') data.rows[0].data.generation='private'
    if(mutation==='context') data.rows[0].qualification='context_only'
    if(mutation==='empty') data.rows=[]
    if(mutation==='unknown') data.rows[0].data.assertion.payload.effective_state='unknown'
    if(mutation==='unpublished') data.empty_reason='unpublished' as never
    expect(arrivalFromPublishedNow(chart_id,data)).toBeNull()
    expect(renderToStaticMarkup(createElement(ArrivalLine,{arrival:arrivalFromPublishedNow(chart_id,data)}))).toBe('')
  })
