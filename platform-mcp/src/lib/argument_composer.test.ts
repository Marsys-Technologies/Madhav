/**
 * argument_composer.test.ts — ṢAḌ-DARŚANA W0.3.
 * Covers: per-clause composition, full-argument assembly order, determinism (the B.10
 * compliance proof for a template-only file), coverage/freshness prose, and a literal
 * source-text guard asserting this file never grows a generative-call dependency.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import {
  composeThesis,
  composeEvidenceSentence,
  composeDissentSentence,
  composeVerdictSentence,
  composeFalsifierSentence,
  composeCoverageSentence,
  composeFreshnessSentence,
  composeArgument,
} from './argument_composer.js'
import type { ArgumentReading } from './kala_envelope.js'

const READING: ArgumentReading = {
  thesis: '  Mercury clears combustion this week.  ',
  evidence: [
    { claim: 'Mercury combust since 3 days ago', fact_ids: ['fact_1'], strength: 'strong' },
    { claim: 'no fact backing this one', fact_ids: [] },
  ],
  dissent: [{ claim: 'KP sub-lord still shows delay', fact_ids: ['fact_3'], source: 'KP sub-lord clock' }],
  verdict: { statement: 'Communication friction eases starting Thursday', tier: 'calibrated_provisional' },
  falsifier: { statement: 'no improvement felt by next new moon', resolves_by: '2026-08-13' },
}

describe('composeThesis', () => {
  it('trims the thesis', () => {
    expect(composeThesis(READING)).toBe('Mercury clears combustion this week.')
  })
})

describe('composeEvidenceSentence', () => {
  it('includes strength clause and fact count/ids when present', () => {
    const s = composeEvidenceSentence({ claim: 'x', fact_ids: ['f1', 'f2'], strength: 'strong' })
    expect(s).toBe('x — strong evidence (2 facts: f1, f2)')
  })

  it('singular "fact" for exactly one fact_id', () => {
    const s = composeEvidenceSentence({ claim: 'x', fact_ids: ['f1'], strength: 'moderate' })
    expect(s).toBe('x — moderate evidence (1 fact: f1)')
  })

  it('honestly marks uncited evidence rather than omitting the gap', () => {
    const s = composeEvidenceSentence({ claim: 'x', fact_ids: [] })
    expect(s).toBe('x (uncited)')
  })
})

describe('composeDissentSentence', () => {
  it('names the dissenting source', () => {
    const s = composeDissentSentence({ claim: 'delay likely', fact_ids: ['f1'], source: 'KP sub-lord clock' })
    expect(s).toBe('KP sub-lord clock dissents: delay likely (1 fact)')
  })

  it('marks uncited dissent honestly', () => {
    const s = composeDissentSentence({ claim: 'delay likely', fact_ids: [], source: 'KP sub-lord clock' })
    expect(s).toBe('KP sub-lord clock dissents: delay likely (uncited)')
  })
})

describe('composeVerdictSentence', () => {
  it.each([
    ['structural_prior', 'structural prior — pre-calibration'],
    ['calibrated_provisional', 'calibrated (provisional)'],
    ['calibrated', 'calibrated'],
    ['unresolved', 'unresolved'],
  ] as const)('states the %s tier inline', (tier, label) => {
    const s = composeVerdictSentence({ statement: 'X happens', tier })
    expect(s).toBe(`X happens [tier: ${label}]`)
  })
})

describe('composeFalsifierSentence', () => {
  it('null in, null out — an honest absence is never given filler prose', () => {
    expect(composeFalsifierSentence(null)).toBeNull()
  })

  it('states resolves_by when present', () => {
    expect(composeFalsifierSentence({ statement: 'no hit', resolves_by: '2026-08-13' })).toBe(
      'Falsified if: no hit (resolves by 2026-08-13)',
    )
  })

  it('marks open-ended when resolves_by is null', () => {
    expect(composeFalsifierSentence({ statement: 'no hit', resolves_by: null })).toBe(
      'Falsified if: no hit (open-ended)',
    )
  })
})

describe('composeCoverageSentence', () => {
  it('computed', () => {
    expect(composeCoverageSentence({ concept: 'c', state: 'computed' })).toBe('c: computed.')
  })
  it('honest_empty carries its reason', () => {
    expect(composeCoverageSentence({ concept: 'c', state: 'honest_empty', reason: 'no window found' })).toBe(
      'c: honestly empty — no window found.',
    )
  })
  it('not_in_corpus carries its reason', () => {
    expect(composeCoverageSentence({ concept: 'c', state: 'not_in_corpus', reason: 'no rule table' })).toBe(
      'c: not in corpus — no rule table.',
    )
  })
})

describe('composeFreshnessSentence', () => {
  it('current', () => {
    expect(
      composeFreshnessSentence({ ephemeris_version: 'v1', sweep_build_date: null, field_hash: null, stale: false, stale_reason: null }),
    ).toBe('Freshness: current.')
  })
  it('stale states its reason', () => {
    expect(
      composeFreshnessSentence({
        ephemeris_version: 'v1',
        sweep_build_date: null,
        field_hash: null,
        stale: true,
        stale_reason: 'horizon expired at 2026-07-01',
      }),
    ).toBe('Freshness: STALE — horizon expired at 2026-07-01.')
  })
})

describe('composeArgument', () => {
  it('assembles clauses in thesis → evidence → dissent → verdict → falsifier order', () => {
    const composed = composeArgument(READING)
    expect(composed.thesis_sentence).toBe('Mercury clears combustion this week.')
    expect(composed.evidence_sentences).toHaveLength(2)
    expect(composed.dissent_sentences).toHaveLength(1)
    expect(composed.verdict_sentence).toContain('[tier: calibrated (provisional)]')
    expect(composed.falsifier_sentence).toBe('Falsified if: no improvement felt by next new moon (resolves by 2026-08-13)')

    const fullTextOrder = [
      composed.thesis_sentence,
      ...composed.evidence_sentences,
      ...composed.dissent_sentences,
      composed.verdict_sentence,
      composed.falsifier_sentence,
    ].join(' ')
    expect(composed.full_text).toBe(fullTextOrder)
  })

  it('omits the falsifier clause from full_text (not a filler sentence) when null', () => {
    const composed = composeArgument({ ...READING, falsifier: null })
    expect(composed.falsifier_sentence).toBeNull()
    expect(composed.full_text.endsWith('[tier: calibrated (provisional)]')).toBe(true)
    expect(composed.full_text).not.toContain('Falsified')
  })

  it('is deterministic: identical input produces byte-identical output every call', () => {
    const a = composeArgument(READING)
    const b = composeArgument(READING)
    expect(a).toEqual(b)
    expect(JSON.stringify(a)).toBe(JSON.stringify(b))
  })
})

describe('B.10 hard rail — no generative call in this file, ever', () => {
  it('source text carries no LLM/model-client import or call pattern', () => {
    const here = fileURLToPath(new URL('./argument_composer.ts', import.meta.url))
    const source = readFileSync(here, 'utf8')
    const forbidden = [
      /anthropic/i,
      /openai/i,
      /\bfetch\(/,
      /\.messages\.create\(/,
      /generateText\(/,
      /require\(['"]https?:/,
    ]
    for (const pattern of forbidden) {
      expect(source, `argument_composer.ts must not match ${pattern}`).not.toMatch(pattern)
    }
  })
})
