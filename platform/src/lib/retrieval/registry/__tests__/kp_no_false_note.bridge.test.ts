/**
 * kp_no_false_note.bridge.test.ts — SS N-368 (1), the WEB BRIDGE half.
 *
 * `getToolByName().retrieve()` injects the Lahiri default when the caller named no ayanamsha. A KP read
 * (get_karakas system=kp / KP categories, get_nakshatra domain=kp / KP categories, get_dashas
 * system=vimshottari_kp, get_kp_cusps, chart_facts_query KP categories) must then NOT say "your requested
 * ayanamsha does not apply here": the caller asked for nothing. The bridge marks the injection with the
 * server-owned param `ayanamsha_injected: true` (handler args only: never in `invocation_params`, never
 * in a response, never bound to SQL); an EXPLICIT id (Lahiri included) or "all" keeps the note, and a
 * caller cannot forge the marker (the bridge strips a supplied one).
 *
 * The REAL handlers run (the handler is spied, not replaced) over disposable SQL simulators; no database.
 * get_kp_cusps is a KP-frame capability the bridge never injects into, so it receives no id at all.
 * This file FAILS on the pre-N-368 bridge/handlers (no marker; the injected Lahiri is "noted").
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createFiveAyanamshaFakeDb, KRISHNAMURTI_FIRST_FIXTURE_ORDER, type FixtureRow } from './helpers/five_ayanamsha_fake_db'
import { buildDashaFixture, createDashasFakeDb, installSigningKey } from './helpers/dashas_fake_db'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const KP_CATS = ['cusp_kp_lords', 'graha_kp_lords', 'kp_cuspal_significators', 'kp_house_significators', 'kp_planet_significations', 'kp_ruling_planets_natal']

function fixture(): FixtureRow[] {
  const rows: FixtureRow[] = []
  for (const ayanamsha_id of KRISHNAMURTI_FIRST_FIXTURE_ORDER) {
    for (const fact_category of [...KP_CATS, 'graha_position', 'karaka_chara']) {
      for (let i = 0; i < 2; i += 1) {
        rows.push({
          fact_id: `${ayanamsha_id}|${fact_category}|${i}`, chart_id: CHART_ID, ayanamsha_id, fact_category,
          fact_subject: 'SUBJ', fact_key: `k${i}`, formula_id: null, fact_value_text: 'x', fact_value_num: i,
          fact_value_jsonb: null, unit: null, verification_pass_status: 'single', citation_ref: 'c', citation_human: null,
        })
      }
    }
  }
  return rows
}

const five = createFiveAyanamshaFakeDb(fixture(), { applyCategoryFilter: true })
const dashas = createDashasFakeDb(buildDashaFixture())
vi.mock('@/lib/db/client', () => ({
  query: (sql: unknown, params: unknown) => {
    const s = String(sql)
    if (s.includes('chart_dashas') || s.includes('asset_provenance_receipts') || s.includes('FROM charts')) return dashas.query(sql, params)
    if (s.includes('graha_dignity_per_varga')) return Promise.resolve({ rows: [], rowCount: 0 })
    return five.query(sql, params)
  },
}))

import { getCapability } from '../index'
import { getCatalog } from '../catalog'
import { getToolByName } from '../tool_name_bridge'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import type { CapabilityDescriptor } from '../types'

type Content = Record<string, unknown>

let restoreKey: () => void
beforeEach(() => { five.reset(); dashas.reset(); restoreKey = installSigningKey() })
afterEach(() => { restoreKey(); vi.restoreAllMocks() })

const MARKER = 'ayanamsha_injected'

interface Run { received: Record<string, unknown>; content: Content; invocation: Record<string, unknown> }

async function viaBridge(uri: string, params: Record<string, unknown>): Promise<Run> {
  getCatalog() // populate the registry before the bridge resolves the URI
  const cap = (getCapability(uri as never) ?? getCatalog().find((c) => c.uri === uri)) as CapabilityDescriptor
  expect(cap, uri).toBeDefined()
  const spy = vi.spyOn(cap, 'handler') // call-through: the REAL handler runs
  const tool = getToolByName(uri)
  expect(tool, `getToolByName(${uri})`).toBeDefined()
  const bundle = await tool!.retrieve({ chart_id: CHART_ID }, params)
  expect(spy).toHaveBeenCalledTimes(1)
  const received = spy.mock.calls[0]![0] as Record<string, unknown>
  const result = (await spy.mock.results[0]!.value) as { content: Content; is_error?: boolean }
  expect(result.is_error, JSON.stringify(result.content).slice(0, 200)).not.toBe(true)
  spy.mockRestore()
  return { received, content: result.content, invocation: bundle.invocation_params as Record<string, unknown> }
}

const win = { window_start: '2000-01-01', window_end: '2100-01-01', limit: 50 }
const chartFactsQuery = () => getCatalog().find((c) => c.name === 'chart_facts_query')!.uri

/** [label, uri, params that make the call a KP read, injected?] — the four KP handlers' KP branches + KP categories. */
const cases: Array<[string, () => string, Record<string, unknown>, boolean]> = [
  ['get_karakas system=kp', () => 'marsys://tool/L1/get_karakas', { system: 'kp' }, true],
  ['get_karakas KP-only categories', () => 'marsys://tool/L1/get_karakas', { categories: ['kp_cuspal_significators'] }, true],
  ['get_karakas default (mixed) page', () => 'marsys://tool/L1/get_karakas', {}, true],
  ['get_nakshatra domain=kp', () => 'marsys://tool/L1/get_nakshatra', { domain: 'kp' }, true],
  ['get_nakshatra KP-only categories', () => 'marsys://tool/L1/get_nakshatra', { categories: ['cusp_kp_lords'] }, true],
  ['get_nakshatra default (mixed) page', () => 'marsys://tool/L1/get_nakshatra', {}, true],
  ['get_dashas system=vimshottari_kp', () => 'marsys://tool/L1/get_dashas', { system: 'vimshottari_kp', ...win }, true],
  ['get_dashas system=all (mixed)', () => 'marsys://tool/L1/get_dashas', { system: 'all', ...win }, true],
  ['get_kp_cusps (KP-frame capability: never injected)', () => 'marsys://tool/L1/get_kp_cusps', {}, false],
  ['chart_facts_query KP category', chartFactsQuery, { category: 'cusp_kp_lords', shape: 'rows' }, true],
  ['chart_facts_query mixed categories', chartFactsQuery, { category: 'cusp_kp_lords,graha_position', shape: 'rows' }, true],
]

/** The frame is ALWAYS reported, whatever the note does. */
function expectFrame(c: Content) {
  const frame = (c['kp_frame'] as Content | undefined) ?? c
  expect(frame['ayanamsha_id'] ?? c['kp_frame_ayanamsha_id']).toBe('krishnamurti')
  expect(frame['frame_label'] ?? c['kp_frame_label']).toBe(KP_FRAME_LABEL)
}

describe.each(cases)('%s', (_name, uriOf, kpParams, injects) => {
  it('only chart_id: the handler receives the injection marker (when the bridge injects) and emits NO note', async () => {
    const run = await viaBridge(uriOf(), kpParams)
    if (injects) {
      expect(run.received[MARKER]).toBe(true)
      expect(run.received['ayanamsha_id']).toBe(LAHIRI)
    } else {
      expect(run.received[MARKER]).toBeUndefined()
      expect(run.received['ayanamsha_id']).toBeUndefined()
    }
    expect(run.content['ayanamsha_note'], 'false note').toBeUndefined()
    expectFrame(run.content)
    // transport detail only: not echoed, not in the invocation record, not in SQL
    expect(JSON.stringify(run.content)).not.toContain(MARKER)
    expect(run.invocation).not.toHaveProperty(MARKER)
    expect([...five.statements, ...dashas.statements].flatMap((s) => s.params).flatMap((p) => (Array.isArray(p) ? p : [p]))).not.toContain(true)
  })

  it('an EXPLICIT Lahiri id: no marker reaches the handler, the note is emitted', async () => {
    const run = await viaBridge(uriOf(), { ...kpParams, ayanamsha_id: LAHIRI })
    expect(run.received[MARKER]).toBeUndefined()
    expect(run.received['ayanamsha_id']).toBe(LAHIRI)
    expect(String(run.content['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
    expect(String(run.content['ayanamsha_note'])).toContain(LAHIRI)
    expectFrame(run.content)
  })

  it('an alias spelling is still explicit', async () => {
    const run = await viaBridge(uriOf(), { ...kpParams, ayanamsha_id: 'LAHIRI' })
    expect(run.received[MARKER]).toBeUndefined()
    expect(String(run.content['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
  })

  it('"all" is explicit: no marker, the note is emitted', async () => {
    const run = await viaBridge(uriOf(), { ...kpParams, ayanamsha_id: 'all' })
    expect(run.received[MARKER]).toBeUndefined()
    expect(run.received['ayanamsha_scope']).toBe('all')
    expect(String(run.content['ayanamsha_note'])).toContain("'all'")
  })

  it('a caller-supplied marker is stripped: forging it cannot suppress the note of an explicit id', async () => {
    const run = await viaBridge(uriOf(), { ...kpParams, ayanamsha_id: LAHIRI, [MARKER]: true })
    expect(run.received[MARKER]).toBeUndefined()
    expect(String(run.content['ayanamsha_note'])).toContain(LAHIRI)
  })

  it('an explicit krishnamurti request is the canonical frame: no note, no marker', async () => {
    const run = await viaBridge(uriOf(), { ...kpParams, ayanamsha_id: 'krishnamurti' })
    expect(run.received[MARKER]).toBeUndefined()
    expect(run.content['ayanamsha_note']).toBeUndefined()
    expectFrame(run.content)
  })
})
