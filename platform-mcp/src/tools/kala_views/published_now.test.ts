import { expect, it } from 'vitest'
import { publishedNowDisclosure } from './published_now.js'

const chart = '11111111-1111-4111-8111-111111111111'
const at = '2026-10-09T12:00:00+05:30'
const manifest = { manifest_id: 'CODEX-build', generation: '4.1' }
const row = (state: string) => ({ source_table: 'kala_obstruction', record_id: state,
  density: 'catalog_only', qualification: 'published', data: {
    assertion_id: state, generation: '4.1', assertion: {
      payload: { effective_state: state, release: { kind: 'unknown', instant: null } },
      roots: { record_ids: ['CODEX-window'] },
    },
  } })
const snapshot = (rows: unknown[]) => ({ view: 'now', chart_id: chart,
  ...manifest, manifest, rows, empty_reason: null, coverage: [{ unsearched_reason: 'not_searched' }],
  pagination: { more_available: false }, density: { confirmed: 0, catalog_only: rows.length },
})

it.each(['information_unavailable', 'evaluated_silent', 'method_inapplicable', 'outside_risk_set',
  'obstruction_cancelled', 'obstruction_active'])('carries stored %s without a quiet/score substitution', state => {
  const source = snapshot([row(state)])
  expect(publishedNowDisclosure(chart, at, { ok: true, content: source }))
    .toMatchObject({ at, capability: 'marsys://tool/L3/now_read', status: 'published', empty_reason: null,
      snapshot: { rows: [{ data: { assertion: { payload: { effective_state: state,
        release: { kind: 'unknown', instant: null } }, roots: { record_ids: ['CODEX-window'] } } } }] } })
})
it('preserves contextual rows and null release when no judge window exists', () => {
  const context = { ...row('information_unavailable'), qualification: 'context_only' }
  const source = snapshot([context])
  expect(publishedNowDisclosure(chart, at, { ok: true, content: source }).snapshot)
    .toMatchObject({ rows: [{ qualification: 'context_only', data: context.data }] })
})
it.each([
  { ok: false, content: null },
  { ok: false, content: snapshot([row('evaluated_silent')]) },
  { ok: true, content: null },
  { ok: true, content: {} },
])('transport/error/malformed replies cannot become a quiet result: %j', response => {
  expect(publishedNowDisclosure(chart, at, response))
    .toMatchObject({ status: 'information_unavailable', snapshot: null })
})
it.each([
  { chart_id: 'another-chart' }, { view: 'ahead' }, { generation: 'private' },
  { manifest_id: null }, { manifest: null }, { rows: null },
  { manifest: { manifest_id: 'other', generation: '4.1' } },
  { empty_reason: 'query_failed' },
])('rejects incomplete or mismatched snapshot identity: %j', change => {
  expect(publishedNowDisclosure(chart, at, { ok: true, content: { ...snapshot([row('evaluated_silent')]), ...change } }))
    .toMatchObject({ status: 'information_unavailable', snapshot: null })
})
it('a published empty page is disclosed without inventing evaluated_silent', () => {
  const source = { ...snapshot([]), empty_reason: 'no_matching_rows' }
  expect(publishedNowDisclosure(chart, at, { ok: true, content: source }))
    .toMatchObject({ status: 'information_unavailable', empty_reason: 'no_matching_rows',
      snapshot: { manifest_id: 'CODEX-build', rows: [], coverage: source.coverage } })
})

it('inferred reader density cannot be promoted through the new public path before producer columns are pinned', () => {
  const source = { ...snapshot([{ ...row('obstruction_cancelled'), density: 'confirmed' }]),
    density: { confirmed: 1, testimony: 0, catalog_only: 0 } }
  expect(publishedNowDisclosure(chart, at, { ok: true, content: source }).snapshot)
    .toMatchObject({ density: null, density_reason: 'stored_tier_contract_unavailable', rows: [{
      density: null, density_reason: 'stored_tier_contract_unavailable',
      data: { assertion: { payload: { effective_state: 'obstruction_cancelled' } } },
    }] })
})
it('an unpublished manifest never carries candidate rows', () => {
  expect(publishedNowDisclosure(chart, at, { ok: true, content: {
    ...snapshot([row('evaluated_silent')]), manifest_id: null, manifest: null, empty_reason: 'unpublished',
  } })).toMatchObject({ status: 'information_unavailable', snapshot: null })
})
