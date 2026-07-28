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
  S1WireEvent,
} from '@/lib/pariprashna/citations'

function env() {
  let seq = 0
  return { nextSeq: () => seq++, t: 1000 }
}

describe('protocol adapter: citation.define → S-1 citation.define + grade', () => {
  it('maps a resolved citation to a define (reader label as snippet) + a grade', () => {
    const internal: PariprashnaCitationEvent = {
      type: 'citation.define',
      n: 3,
      reader_label: 'Mercury eight-system convergence',
      grade: 'primary',
      audit_detail: "resolved from bodha_msr_signals where signal_id='SIG.MSR.413'",
      ref: 'SIG.MSR.413',
    }
    const wire = toWireEvents(internal, env())
    expect(wire).toHaveLength(2)

    const define = wire.find((e) => e.type === 'citation.define')!
    expect(define).toMatchObject({
      type: 'citation.define',
      index: 3,
      signal_id: 'SIG.MSR.413',
      layer: 'L2.5',
      snippet: 'Mercury eight-system convergence',
    })
    // Every wire event carries the S-1 envelope.
    expect(typeof define.seq).toBe('number')
    expect(typeof define.t).toBe('number')

    const grade = wire.find((e) => e.type === 'grade')!
    expect(grade).toMatchObject({
      type: 'grade',
      subject: 'citation:3',
      grade: 'primary',
    })
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
    const wire: S1WireEvent[] = toWireBatch(internal, env())
    const serialized = JSON.stringify(wire)
    for (const tok of leakedTokens) {
      expect(serialized, `leaked to wire: ${tok}`).not.toContain(tok)
    }
  })

  it('never places a citation `audit_detail`s table/fact-id internals on the wire', () => {
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

    // The internal TABLE NAME must not survive onto ANY wire field.
    const serialized = JSON.stringify(wire)
    expect(serialized, 'leaked table name to the wire').not.toContain('bodha_msr_signals')

    // grade.detail (a client-visible field) must be scrubbed of BOTH the table
    // name and the signal id that audit_detail carried.
    const grade = wire.find((e) => e.type === 'grade')!
    expect(grade.detail).not.toContain('bodha_msr_signals')
    expect(grade.detail).not.toContain('SIG.MSR.413')
    expect(grade.grade).toBe('primary')

    // The signal id legitimately rides on citation.define.signal_id (S-1's
    // by-design reference field), and the reader-safe label still ships.
    const define = wire.find((e) => e.type === 'citation.define')!
    expect(define.signal_id).toBe('SIG.MSR.413')
    expect(define.snippet).toBe('Mercury eight-system convergence')
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
