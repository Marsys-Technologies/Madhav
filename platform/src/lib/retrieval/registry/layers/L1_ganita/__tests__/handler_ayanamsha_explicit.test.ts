/**
 * isExplicitAyanamshaRequest / kpFrameRequestedAs (SS N-368): the ONE place that decides whether a caller ASKED
 * for an ayanamsha, so a KP read notes "the requested ayanamsha does not apply" only for an explicit request,
 * never for an omitted id or the Lahiri default the web bridge injected (`ayanamsha_injected: true`).
 * Also pins the multi-system dasha predicate builder (`pushMixedKpSystemAyanamshaFilter`).
 */
import { describe, expect, it } from 'vitest'
import {
  isExplicitAyanamshaRequest,
  kpFrameRequestedAs,
  mixedKpFrameEcho,
  mixedKpSystemEcho,
  pushMixedKpSystemAyanamshaFilter,
  resolveKpFrameAyanamsha,
  resolveHandlerAyanamsha,
  planKpAwareRead,
} from '../../../handler_ayanamsha'

const LAHIRI = 'lahiri_chitrapaksha'

describe('isExplicitAyanamshaRequest', () => {
  it.each([
    ['no id', {}, false],
    ['null id', { ayanamsha_id: null }, false],
    ['blank id', { ayanamsha_id: '  ' }, false],
    ['the marker alone', { ayanamsha_injected: true }, false],
    ['the bridge-injected Lahiri default', { ayanamsha_id: LAHIRI, ayanamsha_injected: true }, false],
    ['explicit Lahiri (stored id)', { ayanamsha_id: LAHIRI }, true],
    ['explicit alias', { ayanamsha_id: 'LAHIRI' }, true],
    ['explicit krishnamurti', { ayanamsha_id: 'krishnamurti' }, true],
    ['raman', { ayanamsha_id: 'raman' }, true],
    ['"all"', { ayanamsha_id: 'all' }, true],
    ['scope "all" (the bridge spelling of "all")', { ayanamsha_scope: 'all' }, true],
    ['a nonsense id', { ayanamsha_id: 'zzz' }, true],
    ['marker false is not a marker', { ayanamsha_id: LAHIRI, ayanamsha_injected: false }, true],
    ['marker as a string is not a marker', { ayanamsha_id: LAHIRI, ayanamsha_injected: 'true' }, true],
    ['marker beside a non-primary id cannot mask the request', { ayanamsha_id: 'raman', ayanamsha_injected: true }, true],
    ['marker beside a non-primary alias cannot mask it either', { ayanamsha_id: 'kp', ayanamsha_injected: true }, true],
    ['an injected id never hides a scope "all" the caller passed', { ayanamsha_id: LAHIRI, ayanamsha_injected: true, ayanamsha_scope: 'all' }, true],
  ] as Array<[string, Record<string, unknown>, boolean]>)('%s -> %s', (_n, args, expected) => {
    expect(isExplicitAyanamshaRequest(args)).toBe(expected)
  })
})

describe('kpFrameRequestedAs follows it (note text names what was asked)', () => {
  it.each([
    ['no id', {}, null],
    ['injected Lahiri', { ayanamsha_id: LAHIRI, ayanamsha_injected: true }, null],
    ['explicit krishnamurti', { ayanamsha_id: 'krishnamurti' }, null],
    ['the alias kp', { ayanamsha_id: 'kp' }, null],
    ['explicit Lahiri', { ayanamsha_id: LAHIRI }, LAHIRI],
    ['raman', { ayanamsha_id: 'raman' }, 'raman'],
    ['"all"', { ayanamsha_id: 'all' }, 'all'],
    ['scope all', { ayanamsha_scope: 'all' }, 'all'],
    ['nonsense', { ayanamsha_id: 'zzz' }, 'zzz'],
    ['injected id + scope "all" asked by the caller', { ayanamsha_id: LAHIRI, ayanamsha_injected: true, ayanamsha_scope: 'all' }, 'all'],
  ] as Array<[string, Record<string, unknown>, string | null]>)('%s', (_n, args, expected) => {
    expect(kpFrameRequestedAs(args)).toBe(expected)
  })

  it('resolveKpFrameAyanamsha: frame always, note only when explicit', () => {
    const injected = resolveKpFrameAyanamsha({ ayanamsha_id: LAHIRI, ayanamsha_injected: true })
    expect(injected.aya.id).toBe('krishnamurti')
    expect(injected.echo.ayanamsha_id).toBe('krishnamurti')
    expect(injected.echo.frame_label).toBeTruthy()
    expect(injected.echo.ayanamsha_note).toBeUndefined()
    expect(resolveKpFrameAyanamsha({ ayanamsha_id: LAHIRI }).echo.ayanamsha_note).toContain(`'${LAHIRI}'`)
  })

  it('the mixed echoes (categories and systems) follow it too', () => {
    expect(mixedKpFrameEcho({ ayanamsha_id: LAHIRI, ayanamsha_injected: true }, ['cusp_kp_lords'], true).ayanamsha_note).toBeUndefined()
    expect(mixedKpFrameEcho({ ayanamsha_id: LAHIRI }, ['cusp_kp_lords'], true).ayanamsha_note).toContain(`'${LAHIRI}'`)
    expect(mixedKpSystemEcho({ ayanamsha_id: LAHIRI, ayanamsha_injected: true }, true).ayanamsha_note).toBeUndefined()
    expect(mixedKpSystemEcho({ ayanamsha_id: LAHIRI }, true).ayanamsha_note).toContain('applies to the other rows only')
    expect(mixedKpSystemEcho({ ayanamsha_id: LAHIRI }, false).ayanamsha_note).toBeUndefined() // no KP rows on the page
  })

  it('planKpAwareRead (typed readers, chart_facts_query): the echo follows it in KP-only and mixed mode', () => {
    const kpOnly = planKpAwareRead({ ayanamsha_id: LAHIRI, ayanamsha_injected: true }, ['cusp_kp_lords'])
    expect(kpOnly.echo([])['ayanamsha_note']).toBeUndefined()
    expect(kpOnly.echo([])['ayanamsha_id']).toBe('krishnamurti')
    expect(planKpAwareRead({ ayanamsha_id: LAHIRI }, ['cusp_kp_lords']).echo([])['ayanamsha_note']).toBeDefined()
    const rows = [{ frame_label: 'x' }]
    expect(planKpAwareRead({ ayanamsha_id: LAHIRI, ayanamsha_injected: true }, ['cusp_kp_lords', 'graha_position']).echo(rows)['ayanamsha_note']).toBeUndefined()
    expect(planKpAwareRead({ ayanamsha_id: LAHIRI }, ['cusp_kp_lords', 'graha_position']).echo(rows)['ayanamsha_note']).toBeDefined()
  })

  it('the non-KP path is unaffected by the marker (an injected id is still the id that is read)', () => {
    expect(resolveHandlerAyanamsha({ ayanamsha_id: LAHIRI, ayanamsha_injected: true }).id).toBe(LAHIRI)
    expect(planKpAwareRead({ ayanamsha_id: LAHIRI, ayanamsha_injected: true }, ['graha_position']).aya.id).toBe(LAHIRI)
  })
})

describe('pushMixedKpSystemAyanamshaFilter', () => {
  it('binds the non-KP ayanamsha only; the KP system and id are inlined code constants', () => {
    const params: unknown[] = ['chart', 11, 0]
    const sql = pushMixedKpSystemAyanamshaFilter({ id: LAHIRI, all: false, source: 'omitted' }, params, { column: 'd.ayanamsha_id', systemColumn: 'd.system_id' })
    expect(sql).toBe(" AND ((d.system_id = 'vimshottari_kp' AND d.ayanamsha_id = 'krishnamurti') OR (d.system_id IS DISTINCT FROM 'vimshottari_kp' AND d.ayanamsha_id = $4))")
    expect(params).toEqual(['chart', 11, 0, LAHIRI])
  })

  it('"all": the non-KP leg is unfiltered and nothing is bound', () => {
    const params: unknown[] = ['chart']
    const sql = pushMixedKpSystemAyanamshaFilter({ id: null, all: true, source: 'all' }, params)
    expect(sql).toBe(" AND ((system_id = 'vimshottari_kp' AND ayanamsha_id = 'krishnamurti') OR (system_id IS DISTINCT FROM 'vimshottari_kp'))")
    expect(params).toEqual(['chart'])
  })
})
