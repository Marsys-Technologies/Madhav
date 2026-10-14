import { expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
const names = ['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'] as const
const manifest = { manifest_id: 'build', generation: '4.1' }
it.each(names)('%s binds SELECT and response to its own stored status, preserving contrary/missing proof', async name => {
  await import('./index')
  const { getCapability } = await import('../../index')
  const cap = getCapability(`marsys://tool/L3/${name}_read`)!
  const contract = cap.density_contract as typeof cap.density_contract & { stored_tier_columns: string[] }
  expect(contract.stored_tier_columns).toContain('kala_darshana.verification_pass_status')
  db.mockReset().mockResolvedValue({ rows: [{ manifest, coverage: [], sources: [{ table: 'kala_darshana', total: 6, rows: [
    { id: '6', generation: '4.1', verification_pass_status: 'single', assertion_id: 'a6', source_citation: 'fixture:6', assertion: { operator_role: 'scored', roots: { fact_ids: ['f'] } } },
    { id: '5', generation: '4.1', verification_pass_status: null, tier: 'confirmed' },
    { id: '4', generation: '4.1', verification_pass_status: 'PASS' },
    { id: '3', generation: null, verification_pass_status: 'two_pass_verified' },
    { id: '2', generation: '4.1', verification_pass_status: 'divergent_flagged' },
    // Synthetic stored verdict fixture, never an assertion about this producer's earnedness.
    { id: '1', generation: '4.1', verification_pass_status: 'two_pass_verified', assertion_id: 'a1' },
  ] }] }] })
  const result = await cap.handler!({ chart_id: 'chart', at: '2026-10-09T12:00:00Z',
    date_from: '2026-10-09T00:00:00Z', date_to: '2026-10-10T00:00:00Z', event_class: 'travel', assertion_id: 'a1' }, {})
  expect(result.content).toMatchObject({ density: { confirmed: 1, testimony: 0, catalog_only: 2, unknown: 3, context_only: 1 },
    catalog_only_rows_in_page: 5, rows: [
      { record_id: '1', density: 'confirmed' }, { record_id: '2', density: 'catalog_only' },
      { record_id: '6', density: 'catalog_only', verification: { column: 'kala_darshana.verification_pass_status', status: 'single', generation: '4.1', manifest_id: 'build' },
        data: { source_citation: 'fixture:6' }, drill: { args: { assertion_id: 'a6' } } },
      { record_id: '3', density: null, qualification: 'context_only' }, { record_id: '4', density: null }, { record_id: '5', density: null },
    ] })
  const sql = db.mock.calls[0][0]
  expect(sql).toContain("to_jsonb(s)->>'verification_pass_status'")
  expect(sql).not.toContain("s.assertion->>'operator_role'")
})
it('an unbound source cannot borrow verification from a sibling or a private generation', async () => {
  const { composeView } = await import('./view_common')
  const result = composeView('explain', 'chart', { manifest, coverage: [], sources: [
    { table: 'not_admitted', total: 1, rows: [{ id: '1', generation: '4.1', verification_pass_status: 'two_pass_verified' }] },
    { table: 'kala_darshana', total: 1, rows: [{ id: '2', generation: '9.9', verification_pass_status: 'two_pass_verified' }] },
  ] })
  expect(result.density.confirmed).toBe(0)
  expect(result.rows.every(row => row.density === null)).toBe(true)
})
it('a contact status cannot bind to a published label from another producer build', async () => {
  const { composeView } = await import('./view_common')
  const result = composeView('ahead', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_gochara_contacts', total: 2, rows: [
      { contact_id: 'bad', generation: '4.1', build_id: 'other-build', verification_pass_status: 'two_pass_verified' },
      { contact_id: 'good', generation: '4.1', build_id: 'build', verification_pass_status: 'single' },
    ] },
  ] })
  expect(result.rows).toMatchObject([
    { record_id: 'good', density: 'catalog_only' }, { record_id: 'bad', density: null, qualification: 'context_only' },
  ])
})
it.each(['kala_bhavishya','kala_convergence','kala_jivana_parva'])(
  '%s has no admitted producer generation binding, even if a later column shares the head label', async table => {
    const { composeView } = await import('./view_common')
    const result = composeView('explain','chart',{manifest,coverage:[],sources:[{table,total:1,rows:[
      {id:'1',generation:'4.1',verification_pass_status:'two_pass_verified'},
    ]}]})
    expect(result.rows[0]).toMatchObject({density:null,qualification:'context_only'})
  },
)

it.each(names)('%s keeps absent stored columns as unknown with catalog flags', async name => {
  await import('./index')
  const { getCapability } = await import('../../index')
  db.mockReset().mockResolvedValue({ rows: [{ manifest, coverage: [], sources: [{
    table: 'kala_darshana', total: 1, rows: [{ id: 'old', generation: '4.1',
      effective_score: 0.99, assertion: { operator_role: 'scored' } }],
  }] }] })
  const result = await getCapability(`marsys://tool/L3/${name}_read`)!.handler!({ chart_id: 'chart',
    at: '2026-10-09T12:00:00Z', date_from: '2026-10-09T00:00:00Z',
    date_to: '2026-10-10T00:00:00Z', event_class: 'travel', assertion_id: 'a1' }, {})
  expect(result.is_error).toBe(false)
  expect(result.content).toMatchObject({ density: { confirmed: 0, catalog_only: 0, unknown: 1 },
    catalog_only_rows_in_page: 1, rows: [{ density: null, verification: { status: null } }],
    judgment_flags: expect.arrayContaining(['catalog_only_rows_present', 'stored_tier_contract_unavailable']),
  })
  expect(db.mock.calls[0][0]).not.toMatch(/s\.verification_pass_status/)
})
