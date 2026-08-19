/**
 * Lane G1-G · PPR-13 item 4 — THE FOLD, AT THE COMMIT BOUNDARY.
 *
 * `entitlement_scan.test.ts` proves the RULES. This file proves the WIRING:
 * that `ReadingPartsAssembler.commitBlock()` — the path that produces the text
 * which is streamed to the wire AND persisted into `message_parts` — actually
 * runs the entitlement rules, and that arming them changes nothing for a caller
 * that did not.
 *
 * The commit path matters more than the stream path for this particular leak. A
 * streamed byte is gone in a second; a committed block is what the reader comes
 * back to next week, and it is what a future summarizer reads.
 */
import { describe, it, expect } from 'vitest'

import { ReadingPartsAssembler } from '@/lib/pariprashna/pipeline/reading_parts'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { buildEntitlementScanRules } from '../entitlement_scan'

const MINE = '482012f1-710e-4a25-994a-93821f5871aa'
const THEIRS = '1c826d5a-9f3b-4d21-8e77-0a5c4b2e91d0'
const RULES = buildEntitlementScanRules({ authorizedChartIds: [MINE] })
type PreWireRules = ReturnType<typeof buildEntitlementScanRules> | []

interface Recorded {
  flags: { code: string; level: string; detail?: string }[]
  commits: { block_id: string; text: string }[]
  deltas: { block_id: string; delta: string }[]
}

function fakeEmitter(): { em: PariprashnaEmitter; rec: Recorded } {
  const rec: Recorded = { flags: [], commits: [], deltas: [] }
  const em = {
    flag: (f: { code: string; level: string; detail?: string }) => rec.flags.push(f),
    blockOpen: () => {},
    blockDelta: (d: { block_id: string; delta: string }) => rec.deltas.push(d),
    blockCommit: (c: { block_id: string; text: string }) => rec.commits.push(c),
  } as unknown as PariprashnaEmitter
  return { em, rec }
}

function commitProse(
  text: string,
  mortalityEnabled: boolean,
  rules: ReturnType<typeof buildEntitlementScanRules> | [],
): { rec: Recorded; committed: string } {
  const { em, rec } = fakeEmitter()
  const a = new ReadingPartsAssembler(em, 1, mortalityEnabled, rules)
  a.appendProse(a.ensureBlock('prose'), text)
  a.commitBlock()
  return { rec, committed: rec.commits.at(-1)?.text ?? '' }
}

describe('the committed + persisted block is scanned', () => {
  it('redacts a foreign chart reference from the COMMITTED text', () => {
    const text = `Saturn is steady. The comparison chart ${THEIRS} differs. Mars is exalted.`
    const { rec, committed } = commitProse(text, false, RULES)

    expect(committed).not.toContain(THEIRS)
    expect(committed).toContain('Saturn is steady.')
    expect(committed).toContain('Mars is exalted.')
    expect(rec.flags.map((f) => f.code)).toContain('injection_entitlement_leak_redacted')
    expect(rec.flags.find((f) => f.code === 'injection_entitlement_leak_redacted')?.level).toBe('error')
  })

  it("the flag's detail carries a COUNT, never the identifier (gate 11 [integrity])", () => {
    const { rec } = commitProse(`Chart ${THEIRS} was consulted.`, false, RULES)
    const flag = rec.flags.find((f) => f.code === 'injection_entitlement_leak_redacted')!
    expect(flag.detail).toMatch(/^1 sentence\(s\)/)
    expect(JSON.stringify(flag)).not.toContain(THEIRS)
  })

  it('leaves an authorized-chart reading completely intact and emits NO flag', () => {
    const text = `This reading is scoped to chart ${MINE}. Saturn is steady.`
    const { rec, committed } = commitProse(text, false, RULES)
    expect(committed).toBe(text)
    expect(rec.flags).toEqual([])
  })
})

describe('the redaction reaches BOTH persisted copies', () => {
  // `appendProse` writes each delta into the block AND into `accumulated`, and
  // `accumulated` is what feeds the citation extractor, the prediction detector
  // and persistence. A commit-time redaction that rewrote only the block left a
  // second, unredacted copy behind.
  function assemble(text: string, mortality: boolean, rules: PreWireRules) {
    const { em, rec } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, mortality, rules)
    a.appendProse(a.ensureBlock('prose'), text)
    a.commitBlock()
    return { rec, committed: rec.commits.at(-1)?.text ?? '', accumulated: a.accumulatedText }
  }

  it('strips a foreign chart reference from accumulatedText, not just the block', () => {
    const r = assemble(`Saturn is steady. Chart ${THEIRS} differs. Mars is exalted.`, false, RULES)
    expect(r.committed).not.toContain(THEIRS)
    expect(r.accumulated).not.toContain(THEIRS)
    expect(r.accumulated).toBe(r.committed)
  })

  it('does the same for the mortality branch — the gap was there for both', () => {
    const r = assemble('Jupiter is strong. The native will meet death around 2047.', true, [])
    expect(r.committed).not.toContain('2047')
    expect(r.accumulated).not.toContain('2047')
  })

  it('leaves accumulatedText untouched when nothing was redacted', () => {
    const text = 'Saturn is steady. Mars is exalted.'
    const r = assemble(text, true, RULES)
    expect(r.accumulated).toBe(text)
  })
})

describe('non-regression: arming one class does not arm the other', () => {
  const MORTAL = 'The native will meet death around 2047.'
  const LEAK = `The comparison chart ${THEIRS} differs.`

  it('entitlement rules ON + mortality OFF leaves mortality prose alone', () => {
    const { rec, committed } = commitProse(MORTAL, false, RULES)
    expect(committed).toBe(MORTAL)
    expect(rec.flags).toEqual([])
  })

  it('mortality ON + no entitlement rules leaves a chart reference alone', () => {
    const { rec, committed } = commitProse(LEAK, true, [])
    expect(committed).toBe(LEAK)
    expect(rec.flags).toEqual([])
  })

  it('both armed → both redacted, with a separate flag for each', () => {
    const { rec, committed } = commitProse(`${MORTAL} ${LEAK} Jupiter is strong.`, true, RULES)
    expect(committed).not.toContain('2047')
    expect(committed).not.toContain(THEIRS)
    expect(committed).toContain('Jupiter is strong.')
    const codes = rec.flags.map((f) => f.code)
    expect(codes).toContain('safety_prewire_mortality_redacted')
    expect(codes).toContain('injection_entitlement_leak_redacted')
  })

  it('BOTH OFF is the default and is a pure pass-through (the flag-OFF production path)', () => {
    const text = `${MORTAL} ${LEAK}`
    const { em, rec } = fakeEmitter()
    // Three-arg construction: exactly how every pre-G1-G caller builds it.
    const a = new ReadingPartsAssembler(em, 1, false)
    a.appendProse(a.ensureBlock('prose'), text)
    a.commitBlock()
    expect(rec.commits.at(-1)?.text).toBe(text)
    expect(rec.flags).toEqual([])
  })
})
