/**
 * PB-1 S-3 fixture (c): register-leak lint proof — "telemetry = 0 leaks".
 *
 * A comprehensive synthetic corpus of internal identifiers (signal ids, asset
 * ids, DB table names, register acronyms) is embedded in synthetic model prose.
 * The lint must catch and neutralize EVERY one so the reader-facing string never
 * contains a single internal token — while never throwing and never aborting.
 *
 * This is the mechanism proof; the wave's final gate runs the same lint against
 * real Q-1 readings.
 */

import { describe, it, expect } from 'vitest'
import {
  lintReaderProse,
  LINT_PATTERN_NAMES,
  CitationStreamRewriter,
} from '@/lib/pariprashna/citations'
import { makeFixtureResolver, makeRewriter, runStream } from './fixtures'

// Every hard token that MUST NOT survive into reader prose.
const HARD_TOKENS = [
  // signal ids
  'SIG.MSR.001',
  'SIG.CGM.42',
  'SIG.UCN.7',
  'SIG.CDLM.900',
  // asset ids (L0–L5 prefixes)
  'bo_laksana',
  'ga_positions',
  'ka_timeline',
  'ph_anchors',
  'mi_calibration',
  'bg_vastu_directions',
  // DB table names
  'bodha_msr_signals',
  'mimamsa_predictions',
  'kala_convergence',
  'phala_anchors',
  'ganita_dashas',
  'chart_facts',
  'asset_registry',
  'brahma_ontology',
  // register acronyms
  'MSR',
  'UCN',
  'CGM',
  'CDLM',
  'LEL',
]

describe('register-leak lint: 0 leaks over the synthetic corpus', () => {
  it('neutralizes every hard token — none survives into clean output', () => {
    const resolver = makeFixtureResolver()
    const corpus = [
      'The reading draws on ' + HARD_TOKENS.join(', ') + ' as its evidence base.',
      'Per MSR and the CGM graph, Mercury (SIG.MSR.001) governs; see bodha_msr_signals.',
      'Cross-checked against chart_facts and ganita_dashas via ga_positions.',
    ].join('\n')

    const { clean, flags, leakCount } = lintReaderProse(corpus, resolver)

    // The core assertion: NOT ONE hard token remains.
    for (const tok of HARD_TOKENS) {
      expect(clean, `leaked token: ${tok}`).not.toContain(tok)
    }
    // Every occurrence was accounted for (rewrite or redact), never dropped silently.
    expect(leakCount).toBeGreaterThanOrEqual(HARD_TOKENS.length)
    expect(flags.length).toBeGreaterThan(0)
  })

  it('applies REWRITE when an id-shaped token has a reader label', () => {
    const resolver = makeFixtureResolver()
    const { clean, flags } = lintReaderProse(
      'Grounded in ga_positions and bo_laksana.',
      resolver,
    )
    const rewrites = flags.filter((f) => f.verdict === 'rewrite')
    expect(rewrites.length).toBe(2)
    expect(clean).toContain('natal positions')
    expect(clean).toContain('core signal reading')
    expect(clean).not.toMatch(/ga_positions|bo_laksana/)
  })

  it('applies REDACT+FLAG when no reader label exists', () => {
    const resolver = makeFixtureResolver()
    const { clean, flags } = lintReaderProse(
      'Evidence: SIG.MSR.001 and mimamsa_predictions.',
      resolver,
    )
    const redacts = flags.filter((f) => f.verdict === 'redact')
    expect(redacts.length).toBeGreaterThanOrEqual(2)
    expect(clean).not.toMatch(/SIG\.MSR\.001|mimamsa_predictions/)
  })

  it('applies TELEMETRY (log-only, text unchanged) for near-misses', () => {
    const resolver = makeFixtureResolver()
    // lowercase register word + a partial signal id with NO numeric tail and a
    // non-register head (so neither hard pattern fires — pure near-miss).
    const input = 'the cgm view and a dangling SIG.FOO reference'
    const { clean, flags } = lintReaderProse(input, resolver)
    const telemetry = flags.filter((f) => f.verdict === 'telemetry')
    expect(telemetry.length).toBeGreaterThanOrEqual(2)
    // Near-miss text is NOT altered.
    expect(clean).toContain('the cgm view')
    expect(clean).toContain('SIG.FOO reference')
  })

  it('never throws; degrades to pass-through + telemetry on internal error', () => {
    // A pathological input should never throw.
    const big = 'x'.repeat(100000) + ' MSR ' + 'y'.repeat(100000)
    expect(() => lintReaderProse(big)).not.toThrow()
    const { clean } = lintReaderProse(big)
    expect(clean).not.toMatch(/\bMSR\b/)
  })

  it('exposes its full pattern inventory', () => {
    expect(LINT_PATTERN_NAMES).toEqual(
      expect.arrayContaining([
        'signal_id',
        'asset_id',
        'table_name',
        'register_acronym',
        'register_full_name',
        'fact_id_namespace',
        'partial_signal_id',
        'lowercase_register',
      ]),
    )
  })

  it('a truncated SIG reference (no numeric tail) stays a TELEMETRY-only near-miss, not a fact_id_namespace hard redact', () => {
    // fact_id_namespace's generic \b[A-Z]{2,6}\. shape would otherwise also
    // match "SIG.FOO" — it must defer to SIG's own dedicated signal_id /
    // partial_signal_id patterns instead of hard-redacting it.
    const { clean, flags } = lintReaderProse('a dangling SIG.FOO reference')
    expect(clean).toBe('a dangling SIG.FOO reference')
    expect(flags.some((f) => f.pattern === 'fact_id_namespace')).toBe(false)
  })
})

describe('register-leak lint: L1 fact_id / CGM node-id namespace codes', () => {
  // PB-2 hotfix #3 fixture: a real production reading (post hotfix #2) leaked
  // bare chart_facts.fact_id / CGM node-id codes (namespace.SUBJECT[.KEY],
  // per ganita/types.ts's own doc comment) — a different, more opaque leak
  // class than register acronyms, always appearing as a parenthetical aside,
  // often backtick-wrapped as inline code.

  const REAL_LEAKED_IDS = [
    'PLN.SUN',
    'PLN.MERCURY',
    'PLN.SATURN',
    'HSE.7',
    'HSE.10',
    'KRK.C8.AMATYA',
    'SEN.ARD.AL',
    'SEN.MISC.YOG_POINT',
    'SEN.SAH.PARADESA',
    'YGA.BUDH_ADITYA',
    'YGA.MERCURY_OPERATIONAL_SPINE',
  ]

  it('catches every real leaked fact_id / CGM node-id token', () => {
    for (const id of REAL_LEAKED_IDS) {
      const { clean, leakCount } = lintReaderProse(`Some text mentions ${id} here.`)
      expect(clean, `leaked token: ${id}`).not.toContain(id)
      expect(leakCount).toBeGreaterThanOrEqual(1)
    }
  })

  it('cleans a backtick-wrapped id inside parens to a grammatical, artifact-free sentence', () => {
    const { clean } = lintReaderProse(
      'Saturn (`PLN.SATURN`), the lord of your 10th house, is exalted in Libra in the 7th house (`HSE.7`). It is your Amatya Karaka (`KRK.C8.AMATYA`), the Jaimini significator.',
    )
    expect(clean).not.toMatch(/PLN\.SATURN|HSE\.7|KRK\.C8\.AMATYA/)
    expect(clean).not.toMatch(/`/) // no orphaned backticks
    expect(clean).toBe(
      'Saturn, the lord of your 10th house, is exalted in Libra in the 7th house. It is your Amatya Karaka, the Jaimini significator.',
    )
  })

  it('cleans a bare (non-backtick-wrapped) id inside parens with a trailing colon', () => {
    const { clean } = lintReaderProse('**The Career House (HSE.10):** Your 10th house of profession.')
    expect(clean).toBe('**The Career House:** Your 10th house of profession.')
  })

  it('does not touch legitimate jyotish shorthand that happens to share letters but has no dot (AL, AmK, 10H)', () => {
    const { clean, leakCount } = lintReaderProse(
      'Your professional reputation (AL in 10H) and your Amatya Karaka (AmK) are linked.',
    )
    expect(clean).toBe('Your professional reputation (AL in 10H) and your Amatya Karaka (AmK) are linked.')
    expect(leakCount).toBe(0)
  })
})

describe('register-leak lint: spelled-out full names + grammar-preserving redaction', () => {
  // PB-2 hotfix #2 fixture: a real production reading (post hotfix #1) still
  // leaked spelled-out register names the acronym-only pattern can't catch,
  // and the acronym pattern's naive delete-only redaction left subject-less
  // sentences ("The UCN concludes..." -> "The concludes...") whenever the
  // model used the acronym/full-name as a sentence's grammatical subject.

  it('catches spelled-out full register names, not just acronyms', () => {
    const { clean, leakCount } = lintReaderProse(
      'This draws on the Unified Chart Narrative and the Cross-Domain Linkage Matrix.',
    )
    expect(clean).not.toMatch(/Unified Chart Narrative|Cross-Domain Linkage/)
    expect(leakCount).toBeGreaterThanOrEqual(2)
  })

  it('preserves grammar when a leading article precedes a bare acronym subject', () => {
    const { clean } = lintReaderProse(
      'The UCN concludes that career is the organizing axis of your chart.',
    )
    expect(clean).toBe('This concludes that career is the organizing axis of your chart.')
  })

  it('preserves grammar when a leading article precedes a spelled-out full name subject', () => {
    const { clean } = lintReaderProse(
      'The Cross-Domain Linkage Matrix provides a precise map of how domains interact.',
    )
    expect(clean).toBe('This provides a precise map of how domains interact.')
  })

  it('lowercases the substitute when the leading article is mid-sentence lowercase', () => {
    const { clean } = lintReaderProse(
      'As detailed in the MSR, eight independent systems converge on Mercury.',
    )
    expect(clean).toBe('As detailed in this, eight independent systems converge on Mercury.')
  })

  it('does not leave an orphaned bare article when the acronym is redacted', () => {
    const { clean } = lintReaderProse(
      'The specific linkages in the CDLM, and the contradictions therein.',
    )
    expect(clean).not.toMatch(/\bthe,/)
    expect(clean).toBe('The specific linkages in this, and the contradictions therein.')
  })

  it('still redacts a bare parenthetical citation marker with no article exactly as before (no regression)', () => {
    const { clean } = lintReaderProse('(UCN §XX)')
    expect(clean).toBe('( §XX)')
  })

  it('the original real production leak string — a spelled-out name immediately followed by its own acronym in parens, both at sentence start with no leading article — comes out clean and grammatical', () => {
    const { clean } = lintReaderProse(
      'Cross-Domain Linkage Matrix (CDLM) quantifies this with a 0.92 strength score.',
    )
    expect(clean).not.toMatch(/Cross-Domain Linkage Matrix|CDLM/)
    expect(clean).toBe('This quantifies this with a 0.92 strength score.')
  })
})

describe('register-leak lint: airtight through the rewriter stream path', () => {
  it('no hard token reaches the wire even when embedded in normal prose deltas', () => {
    const rw = new CitationStreamRewriter({
      resolver: makeFixtureResolver(),
      modelId: 'leak-test',
    })
    // Split the corpus into arbitrary streaming deltas.
    const corpus =
      'Mercury (SIG.MSR.001) per MSR/CGM anchors the chart; ' +
      'sourced from bodha_msr_signals and chart_facts via ga_positions and bo_laksana.'
    const deltas: string[] = []
    for (let i = 0; i < corpus.length; i += 7) deltas.push(corpus.slice(i, i + 7))

    const { text } = runStream(rw, deltas, { perDeltaMs: 0 })
    for (const tok of HARD_TOKENS) {
      expect(text, `leaked via stream: ${tok}`).not.toContain(tok)
    }
    // The rewritten labels for id-shaped tokens still appear (data not dropped).
    expect(text).toContain('natal positions')
    expect(text).toContain('core signal reading')
  })
})

describe('rewriter: resolved / unresolved / dedup behavior', () => {
  it('resolved sentinel emits a graded define + a clean marker', () => {
    const rw = makeRewriter()
    const { text, events } = runStream(rw, ['X⟦cite:SIG.MSR.413⟧Y'])
    expect(text).toBe('X[1]Y')
    const def = events.find((e) => e.type === 'citation.define')
    expect(def).toMatchObject({ n: 1, grade: 'primary', ref: 'SIG.MSR.413' })
  })

  it('unresolvable ref → unverified grade + hallucination counter increments', () => {
    const rw = makeRewriter({ modelId: 'ghost-model' })
    const { text, events } = runStream(rw, ['Claim⟦cite:GHOST.1⟧.'])
    const def = events.find((e) => e.type === 'citation.define')
    expect(def).toMatchObject({ grade: 'unverified', ref: 'GHOST.1' })
    // reader marker is still emitted (data not dropped), but the label is safe.
    expect(text).toBe('Claim[1].')
    expect(rw.hallucinationCount()).toBe(1)
  })

  it('repeated refs reuse the same number and emit define only once', () => {
    const rw = makeRewriter()
    const { text, events } = runStream(rw, [
      'A⟦cite:SIG.MSR.413⟧ B⟦cite:SIG.MSR.042⟧ C⟦cite:SIG.MSR.413⟧',
    ])
    expect(text).toBe('A[1] B[2] C[1]')
    const defs = events.filter((e) => e.type === 'citation.define')
    expect(defs).toHaveLength(2) // 413 defined once, 042 once
  })

  it('a parse-failed bracket ([[wiki]]) is emitted as prose, not treated as a cite', () => {
    const rw = makeRewriter()
    const { text, events } = runStream(rw, ['see [[SomePage]] now'])
    expect(text).toBe('see [[SomePage]] now')
    expect(events.filter((e) => e.type === 'citation.define')).toHaveLength(0)
  })
})
