/**
 * PB-1 S-3: protocol adapter — internal citation events → lane S-1 wire shapes.
 *
 * Proves the mapping is faithful to S-1's vocabulary AND wire-safe: the leaked
 * internal token (a register_leak flag's `original`) and the audit-only fields
 * NEVER appear on any client-visible wire field.
 */

import { describe, it, expect } from 'vitest'
import { toWireEvents, toWireBatch } from '@/lib/pariprashna/citations'
import type {
  PariprashnaCitationEvent,
  CitationWireEvent,
} from '@/lib/pariprashna/citations'

function env() {
  let seq = 0
  return { nextSeq: () => seq++, t: 1000 }
}

describe('protocol adapter: citation.define → S-1 citation.define (reader_label + grade ride on the define)', () => {
  it('maps a resolved citation to a SINGLE define carrying reader_label + grade (no split grade event)', () => {
    const internal: PariprashnaCitationEvent = {
      type: 'citation.define',
      n: 3,
      reader_label: 'Mercury eight-system convergence',
      grade: 'primary',
      audit_detail: "resolved from bodha_msr_signals where signal_id='SIG.MSR.413'",
      ref: 'SIG.MSR.413',
    }
    const wire = toWireEvents(internal, env())
    // Reconciled: one event, not a define + a correlated grade event.
    expect(wire).toHaveLength(1)

    const define = wire.find((e) => e.type === 'citation.define')!
    expect(define).toMatchObject({
      type: 'citation.define',
      index: 3,
      signal_id: 'SIG.MSR.413',
      layer: 'L2.5',
      snippet: 'Mercury eight-system convergence',
      reader_label: 'Mercury eight-system convergence',
      grade: 'primary',
    })
    // Every wire event carries the S-1 envelope.
    expect(typeof define.seq).toBe('number')
    expect(typeof define.t).toBe('number')

    // No separate `grade` event is emitted for a citation any more — the only
    // event on the wire for a citation is the single citation.define.
    expect(wire.every((e) => e.type === 'citation.define')).toBe(true)
  })

  it('honors an explicit source layer on the internal event instead of the default', () => {
    const internal: PariprashnaCitationEvent = {
      type: 'citation.define',
      n: 1,
      reader_label: 'Saturn in the birth chart',
      grade: 'primary',
      audit_detail: 'resolved from chart_facts',
      ref: 'FACT.L1.001',
      layer: 'L1',
    }
    const wire = toWireEvents(internal, env())
    const define = wire.find((e) => e.type === 'citation.define')!
    expect(define).toMatchObject({ layer: 'L1' })
  })
})

describe('protocol adapter: flags → S-1 flag', () => {
  it('maps malformed_sentinel to a warn-level flag carrying only the reason', () => {
    const wire = toWireEvents(
      { type: 'flag', flag: 'malformed_sentinel', reason: 'timeout', raw: 'x' },
      env(),
    )
    expect(wire[0]).toMatchObject({ type: 'flag', code: 'malformed_sentinel', level: 'warn' })
  })

  it('maps normalization to an info-level flag', () => {
    const wire = toWireEvents(
      {
        type: 'flag',
        flag: 'normalization',
        original: '[[cite:X]]',
        normalized: '⟦cite: X⟧',
        note: 'square-bracket-variant',
      },
      env(),
    )
    expect(wire[0]).toMatchObject({ type: 'flag', code: 'citation_normalization', level: 'info' })
  })

  it('maps a REDACT register_leak to warn; a REWRITE to info', () => {
    const redact = toWireEvents(
      {
        type: 'flag',
        flag: 'register_leak',
        verdict: 'redact',
        pattern: 'table_name',
        original: 'bodha_msr_signals',
      },
      env(),
    )
    expect(redact[0]).toMatchObject({ code: 'register_leak:redact', level: 'warn' })

    const rewrite = toWireEvents(
      {
        type: 'flag',
        flag: 'register_leak',
        verdict: 'rewrite',
        pattern: 'asset_id',
        original: 'ga_positions',
        replacement: 'natal positions',
      },
      env(),
    )
    expect(rewrite[0]).toMatchObject({ code: 'register_leak:rewrite', level: 'info' })
  })
})

describe('protocol adapter: WIRE-SAFETY — leaked token never reaches the wire', () => {
  it('never places a register_leak `original` (the leaked id) on any wire field', () => {
    const leakedTokens = ['bodha_msr_signals', 'SIG.MSR.001', 'ga_positions', 'MSR']
    const internal: PariprashnaCitationEvent[] = leakedTokens.map((tok) => ({
      type: 'flag' as const,
      flag: 'register_leak' as const,
      verdict: 'redact' as const,
      pattern: 'table_name',
      original: tok,
    }))
    const wire: CitationWireEvent[] = toWireBatch(internal, env())
    const serialized = JSON.stringify(wire)
    for (const tok of leakedTokens) {
      expect(serialized, `leaked to wire: ${tok}`).not.toContain(tok)
    }
  })

  it('never places a citation `audit_detail`s table-name internals on the wire', () => {
    // audit_detail deliberately contains an internal table name AND a signal id.
    const internal: PariprashnaCitationEvent = {
      type: 'citation.define',
      n: 7,
      reader_label: 'Mercury eight-system convergence',
      grade: 'primary',
      audit_detail: "resolved from bodha_msr_signals where signal_id='SIG.MSR.413'",
      ref: 'SIG.MSR.413',
    }
    const wire = toWireBatch([internal], env())

    // The internal TABLE NAME must not survive onto ANY wire field. Reconciled
    // adapter does not forward audit_detail at all, so this holds by
    // construction — the guard stays as a permanent regression proof.
    const serialized = JSON.stringify(wire)
    expect(serialized, 'leaked table name to the wire').not.toContain('bodha_msr_signals')
    // The free-text audit sentence ("resolved from …") must not ship either.
    expect(serialized, 'leaked audit sentence to the wire').not.toContain('resolved from')

    // The signal id legitimately rides on citation.define.signal_id (S-1's
    // by-design reference field); the reader-safe label + grade still ship on
    // the same define event.
    const define = wire.find((e) => e.type === 'citation.define')!
    expect(define.signal_id).toBe('SIG.MSR.413')
    expect(define.snippet).toBe('Mercury eight-system convergence')
    expect(define.reader_label).toBe('Mercury eight-system convergence')
    expect(define.grade).toBe('primary')
  })

  it('a rewrite exposes only the clean replacement label, not the original id', () => {
    const wire = toWireEvents(
      {
        type: 'flag',
        flag: 'register_leak',
        verdict: 'rewrite',
        pattern: 'asset_id',
        original: 'ga_positions',
        replacement: 'natal positions',
      },
      env(),
    )
    const serialized = JSON.stringify(wire)
    expect(serialized).not.toContain('ga_positions')
    expect(serialized).toContain('natal positions')
  })
})
