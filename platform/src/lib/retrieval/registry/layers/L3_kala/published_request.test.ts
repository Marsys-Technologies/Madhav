import { expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
const chart = '482012f1-710e-4a25-994a-93821f5871aa'
const manifest = { manifest_id: '22222222-2222-4222-8222-222222222222', generation: 'K9-final' }
const published_request = { at: '2026-10-16T12:00:00Z', date_from: '2026-10-16T00:00:00Z',
  date_to: '2026-10-17T00:00:00Z', event_class: 'travel', assertion_id: 'k9-sentinel', limit: 1 }
it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'])
  ('public %s resolves through the Vidhi bridge and serves an explicit published-stage request', async view => {
    await import('./index')
    const { getCatalog, getCapability } = await import('../../index')
    const { resolveWebToolBridge } = await import('../../../../../../scripts/manifest/web_tool_bridge_builder')
    const name = `kala_${view}_get`, uri = `marsys://tool/L3/${name}`
    expect(resolveWebToolBridge([name], getCatalog(), {}, {}, { canonical_faces: [], deprecated_aliases: {} }))
      .toEqual([{ name, uri, resolution_kind: 'catalog_name_direct', via: [] }])
    db.mockReset().mockResolvedValue({ rows: [{ manifest, coverage: [], sources: [{ table: 'kala_obstruction', total: 1,
      rows: [{ id: 1, generation: manifest.generation, assertion_id: 'k9-sentinel',
        assertion: { payload: { effective_state: 'information_unavailable', release: { kind: 'unknown', instant: null } } } }] }] }] })
    const result = await getCapability(uri)!.handler!({ chart_id: chart, published_request }, {})
    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ view, chart_id: chart, ...manifest, rows: [{ data: { assertion: {
      payload: { effective_state: 'information_unavailable', release: { instant: null } },
    } } }] })
    expect(db).toHaveBeenCalledTimes(1)
    expect(db.mock.calls[0][1][0]).toBe(chart)
    expect(db.mock.calls[0][1][1]).toBe(published_request.at)
  })
it.each([null, [], 'now', { chart_id: 'other' }, { at: '2026-10-16T12:00:00Z', extra: true }])
  ('refuses malformed explicit selectors without SQL: %j', async published_request => {
    const { makePublicView } = await import('./view_common')
    db.mockReset()
    const result = await makePublicView('now').handler!({ chart_id: chart, published_request }, {})
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>).empty_reason).toBe('invalid_request')
    expect(db).not.toHaveBeenCalled()
  })
it('never falls back to legacy, a candidate or evaluated silence when publication is absent or SQL fails', async () => {
  const { makePublicView } = await import('./view_common')
  db.mockReset().mockResolvedValueOnce({ rows: [{ manifest: null, coverage: [], sources: [] }] })
  expect((await makePublicView('now').handler!({ chart_id: chart, published_request }, {})).content)
    .toMatchObject({ manifest_id: null, empty_reason: 'unpublished', rows: [] })
  db.mockRejectedValueOnce(new Error('unavailable'))
  expect(await makePublicView('now').handler!({ chart_id: chart, published_request }, {}))
    .toMatchObject({ is_error: true, content: { manifest_id: null, empty_reason: 'query_failed' } })
})
