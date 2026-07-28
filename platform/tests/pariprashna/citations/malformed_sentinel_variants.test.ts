/**
 * PB-1 S-3 fixture (b): `malformed-sentinel-variants`.
 *
 * All tolerated grammar variants — square-bracket form, extra/missing spacing,
 * keyword case differences, mixed brackets — normalize to the same canonical
 * reference and resolve identically, logging (never dropping) the normalization.
 */

import { describe, it, expect } from 'vitest'
import { parseSentinel } from '@/lib/pariprashna/citations'
import { makeRewriter, runStream } from './fixtures'

describe('grammar: canonical + tolerant variants normalize to the same ref', () => {
  const cases: { raw: string; ref: string; label: string }[] = [
    { raw: '⟦cite: SIG.MSR.413⟧', ref: 'SIG.MSR.413', label: 'canonical' },
    { raw: '⟦cite:SIG.MSR.413⟧', ref: 'SIG.MSR.413', label: 'no space after colon' },
    { raw: '⟦ cite : SIG.MSR.413 ⟧', ref: 'SIG.MSR.413', label: 'spaces around keyword/colon' },
    { raw: '[[cite: SIG.MSR.413]]', ref: 'SIG.MSR.413', label: 'square-bracket variant' },
    { raw: '[[cite:SIG.MSR.413]]', ref: 'SIG.MSR.413', label: 'square, no spacing' },
    { raw: '⟦CITE: SIG.MSR.413⟧', ref: 'SIG.MSR.413', label: 'uppercase keyword' },
    { raw: '⟦Cite: SIG.MSR.413⟧', ref: 'SIG.MSR.413', label: 'titlecase keyword' },
    { raw: '⟦cItE:SIG.MSR.413⟧', ref: 'SIG.MSR.413', label: 'mixed case keyword' },
    { raw: '[[cite: SIG.MSR.413⟧', ref: 'SIG.MSR.413', label: 'mixed brackets' },
    { raw: '⟦cite:   SIG.MSR.413   ⟧', ref: 'SIG.MSR.413', label: 'excess interior spacing' },
  ]

  for (const c of cases) {
    it(`parses ${c.label}: ${c.raw}`, () => {
      const r = parseSentinel(c.raw)
      expect(r.ok, `expected ${c.raw} to parse`).toBe(true)
      if (r.ok) {
        expect(r.ref).toBe(c.ref)
        expect(r.canonical).toBe('⟦cite: SIG.MSR.413⟧')
      }
    })
  }

  it('the canonical form reports normalized=false; variants report normalized=true', () => {
    const canon = parseSentinel('⟦cite: SIG.MSR.413⟧')
    expect(canon.ok && canon.normalized).toBe(false)
    for (const c of cases.slice(1)) {
      const r = parseSentinel(c.raw)
      expect(r.ok && r.normalized, `${c.label} should be flagged normalized`).toBe(true)
    }
  })
})

describe('grammar: non-citations are rejected (emitted as prose, not swallowed)', () => {
  it('rejects a bare wiki-style [[link]] with no cite keyword', () => {
    expect(parseSentinel('[[SomePage]]').ok).toBe(false)
  })
  it('rejects an empty ref', () => {
    expect(parseSentinel('⟦cite: ⟧').ok).toBe(false)
  })
})

describe('rewriter: every variant resolves identically end-to-end', () => {
  const variants = [
    '⟦cite: SIG.MSR.413⟧',
    '[[cite:SIG.MSR.413]]',
    '⟦CITE :  SIG.MSR.413 ⟧',
    '⟦cItE:SIG.MSR.413⟧',
  ]

  for (const v of variants) {
    it(`emits one citation.define + a normalization flag (when applicable) for ${v}`, () => {
      const rw = makeRewriter()
      const { text, events } = runStream(rw, [`Mercury leads${v}, decisively.`])

      const defines = events.filter((e) => e.type === 'citation.define')
      expect(defines).toHaveLength(1)
      expect(defines[0]).toMatchObject({
        n: 1,
        ref: 'SIG.MSR.413',
        reader_label: 'Mercury eight-system convergence',
        grade: 'primary',
      })

      // Reader prose carries the clean numbered marker, never the raw sentinel
      // and never the internal id.
      expect(text).toBe('Mercury leads[1], decisively.')
      expect(text).not.toMatch(/SIG\.MSR/)
      expect(text).not.toContain('cite')

      // Non-canonical variants log a normalization; the canonical one does not.
      const norms = events.filter((e) => e.type === 'flag' && e.flag === 'normalization')
      if (v !== '⟦cite: SIG.MSR.413⟧') expect(norms.length).toBe(1)
      else expect(norms.length).toBe(0)
    })
  }
})

describe('rewriter: sentinel split across delta boundaries still resolves', () => {
  it('handles a sentinel arriving one code unit at a time', () => {
    const rw = makeRewriter()
    const full = 'A⟦cite:SIG.MSR.042⟧B'
    const deltas = Array.from(full) // char-by-char
    const { text, events } = runStream(rw, deltas, { perDeltaMs: 0 })
    expect(text).toBe('A[1]B')
    expect(events.filter((e) => e.type === 'citation.define')).toHaveLength(1)
  })

  it('handles the [[ opener split across two deltas', () => {
    const rw = makeRewriter()
    const { text } = runStream(rw, ['start [', '[cite:SIG.MSR.042]', ']end'], {
      perDeltaMs: 0,
    })
    expect(text).toBe('start [1]end')
  })
})
