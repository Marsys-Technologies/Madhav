/**
 * ayanamsha_parity.test.ts — platform / platform-mcp normaliser PARITY (SS N-342).
 *
 * platform and platform-mcp are separate packages (no cross-import in source), so the ayanamsha
 * normaliser is written twice:
 *   platform     : platform/src/lib/retrieval/chart_facts_helpers.ts
 *   platform-mcp : platform-mcp/src/lib/ayanamsha.ts
 * This test imports BOTH (test-only) and asserts identical behaviour on one shared table of
 * inputs, identical alias vocabularies, identical constants and identical error text. Any change
 * to one side that is not made to the other fails here.
 */
import { describe, it, expect } from 'vitest'
import * as platform from '../../chart_facts_helpers'
import * as mcp from '../../../../../../platform-mcp/src/lib/ayanamsha'

/** The shared input table: every alias and its case/whitespace variants, blanks, sentinels, junk. */
const SHARED_INPUTS: unknown[] = [
  undefined, null, '', ' ', '\t', '\n',
  'lahiri', 'LAHIRI', 'Lahiri', '  lahiri ', 'lahiri_chitra', 'lahiri_chitrapaksha', 'LAHIRI_CHITRAPAKSHA',
  'Lahiri Chitrapaksha', 'lahiri-chitrapaksha',
  'true_chitra', 'TRUE_CHITRA', 'true_citra', 'True_Citra', 'true_chitra_paksha', 'true_chitrapaksha', 'true-chitra',
  'chitra', 'chitrapaksha', 'CHITRA',
  'kp', 'KP', ' Kp ', 'krishnamurti', 'Krishnamurti', 'krishnamurti_paddhati',
  'raman', 'RAMAN',
  'surya_siddhanta', 'surya_siddhanta_classical', 'Surya Siddhanta', 'suryasiddhanta', 'ss', 'SS',
  'INVARIANT', 'invariant', 'Invariant',
  'all', 'ALL', ' All ',
  'nonsense', 'lahiri2', 'kp_newcomb', 'yukteshwar', '*', 'all,lahiri',
  42, 0, true, false, ['lahiri'], { id: 'lahiri' },
  // every alias key, as written and upper-cased
  ...platform.AYANAMSHA_ALIAS_KEYS,
  ...platform.AYANAMSHA_ALIAS_KEYS.map((k) => k.toUpperCase()),
  ...mcp.AYANAMSHA_ALIAS_KEYS,
]

describe('platform / platform-mcp ayanamsha parity', () => {
  it('constants are identical', () => {
    expect(mcp.PRIMARY_AYANAMSHA).toBe(platform.PRIMARY_AYANAMSHA)
    expect([...mcp.AYANAMSHA_SERVE_ORDER]).toEqual([...platform.AYANAMSHA_SERVE_ORDER])
    expect([...mcp.STORED_AYANAMSHA_IDS]).toEqual([...platform.STORED_AYANAMSHA_IDS])
    expect(mcp.INVARIANT_AYANAMSHA).toBe(platform.INVARIANT_AYANAMSHA)
    expect(mcp.AYANAMSHA_ALL).toBe(platform.AYANAMSHA_ALL)
  })

  it('the alias vocabularies are identical (same keys, same targets)', () => {
    expect([...mcp.AYANAMSHA_ALIAS_KEYS].sort()).toEqual([...platform.AYANAMSHA_ALIAS_KEYS].sort())
    for (const key of platform.AYANAMSHA_ALIAS_KEYS) {
      expect(mcp.resolveAyanamshaArg(key), key).toEqual(platform.resolveAyanamshaArg(key))
    }
  })

  it.each(SHARED_INPUTS.map((v) => [v]))('resolveAyanamshaArg(%j) is identical on both sides', (input) => {
    expect(mcp.resolveAyanamshaArg(input)).toEqual(platform.resolveAyanamshaArg(input))
  })

  it.each(SHARED_INPUTS.map((v) => [v]))('normalizeAyanamshaId(%j) returns/throws identically', (input) => {
    let p: unknown, m: unknown
    let pe: Error | undefined, me: Error | undefined
    try { p = platform.normalizeAyanamshaId(input) } catch (e) { pe = e as Error }
    try { m = mcp.normalizeAyanamshaId(input) } catch (e) { me = e as Error }
    expect(m).toEqual(p)
    expect(me?.message).toBe(pe?.message)
    expect(me?.name).toBe(pe?.name)
    expect((me as { code?: string } | undefined)?.code).toBe((pe as { code?: string } | undefined)?.code)
  })

  it('the rejection text is byte-identical and lists every stored id', () => {
    expect(mcp.invalidAyanamshaMessage('zzz')).toBe(platform.invalidAyanamshaMessage('zzz'))
    for (const id of platform.AYANAMSHA_SERVE_ORDER) expect(mcp.invalidAyanamshaMessage('zzz')).toContain(id)
  })

  it('the lenient MCP wrapper resolver agrees with the strict resolver wherever the id is valid, and passes unknown ids through', () => {
    for (const input of SHARED_INPUTS) {
      if (input !== undefined && typeof input !== 'string') continue
      const strict = platform.resolveAyanamshaArg(input)
      const lenient = mcp.resolveChartFactsAyanamsha(input as string | undefined)
      if (strict.ok) {
        expect(lenient, JSON.stringify(input)).toBe(strict.ayanamsha_id ?? 'all')
      } else {
        expect(lenient, JSON.stringify(input)).toBe(input)
      }
    }
  })
})
