/**
 * review.test.ts — lane P4-J, §N.8 red-then-green proof for the review step.
 *
 * §N.8 / the P4-J charter: "the DD-1 feel-proxy battery fed a deliberately
 * register-broken reading and observed to fail it before its first real pass
 * counts." This file is that proof for THIS lane's review gate: every check
 * below first demonstrates the detector CAN fail (RED, a deliberately broken
 * fixture), then confirms a real, passing entry (GREEN). All three detectors
 * this pipeline relies on are exercised: the register-leak lint, the voice
 * lint, and this lane's own citation gate.
 */
import { describe, expect, it } from 'vitest'

import { loadReaderFacingCatalog } from '../catalog'
import { READER_TEXT_ENTRIES } from '../entries'
import { reviewEntry } from '../review'
import type { MsrSignal, ReaderTextEntry } from '../types'

const catalog = loadReaderFacingCatalog()
const signalsById = new Map<string, MsrSignal>(catalog.map((s) => [s.signal_id, s]))

function realSignal(id: string): MsrSignal {
  const s = signalsById.get(id)
  if (!s) throw new Error(`fixture signal ${id} not found in catalog — test setup bug`)
  return s
}

describe('reviewEntry — register-leak lint (RED then GREEN)', () => {
  it('RED: fails a deliberately register-leaking entry (bare signal id + register acronym)', () => {
    const broken: ReaderTextEntry = {
      signal_id: 'SIG.MSR.001',
      reader_text:
        'Per SIG.MSR.001 and the MSR register, Saturn is exalted in the seventh house, as confirmed by bo_laksana.',
      grade: 'primary',
      grounding_note: 'Classical basis: "BPHS Ch.26 Sl.19; Phaladeepika Ch.6 Sl.3 (Pancha Mahapurusha)"',
      catalog_discrepancy_note: '',
    }
    const result = reviewEntry(broken, realSignal('SIG.MSR.001'))
    expect(result.passed).toBe(false)
    expect(result.flags.some((f) => f.source === 'register_leak')).toBe(true)
    // The leak lint must have actually REDACTED the leaking tokens out of clean_text.
    expect(result.clean_text).not.toContain('SIG.MSR.001')
    expect(result.clean_text).not.toMatch(/\bMSR\b/)
  })

  it('GREEN: a real entry with no internal vocabulary passes the register-leak check', () => {
    const clean = READER_TEXT_ENTRIES.find((e) => e.signal_id === 'SIG.MSR.198')!
    const result = reviewEntry(clean, realSignal('SIG.MSR.198'))
    expect(result.flags.filter((f) => f.source === 'register_leak')).toHaveLength(0)
  })
})

describe('reviewEntry — voice lint (RED then GREEN)', () => {
  it('RED: fails (flags) a deliberately imperative remedy sentence', () => {
    const broken: ReaderTextEntry = {
      signal_id: 'SIG.MSR.001',
      reader_text: 'You must wear a ruby to strengthen this placement.',
      grade: 'primary',
      grounding_note: 'Classical basis: "BPHS Ch.26 Sl.19; Phaladeepika Ch.6 Sl.3 (Pancha Mahapurusha)"',
      catalog_discrepancy_note: '',
    }
    const result = reviewEntry(broken, realSignal('SIG.MSR.001'))
    expect(result.flags.some((f) => f.source === 'voice' && f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('GREEN: a real entry carries no imperative-remedy voice flag', () => {
    const clean = READER_TEXT_ENTRIES.find((e) => e.signal_id === 'SIG.MSR.198')!
    const result = reviewEntry(clean, realSignal('SIG.MSR.198'))
    expect(result.flags.filter((f) => f.source === 'voice')).toHaveLength(0)
  })
})

describe('reviewEntry — citation gate (RED then GREEN)', () => {
  it('RED: fails when the signal_id does not exist in the reader-facing catalog', () => {
    const broken: ReaderTextEntry = {
      signal_id: 'SIG.MSR.999999',
      reader_text: 'A perfectly clean, unrelated sentence about Saturn in the seventh house.',
      grade: 'primary',
      grounding_note: 'Classical basis: "BPHS Ch.26"',
      catalog_discrepancy_note: '',
    }
    const result = reviewEntry(broken, null)
    expect(result.passed).toBe(false)
    expect(result.flags.some((f) => f.source === 'citation_gate' && f.code === 'citation_gate_unknown_signal')).toBe(
      true,
    )
  })

  it('RED: fails when grounding_note is empty', () => {
    const broken: ReaderTextEntry = {
      signal_id: 'SIG.MSR.001',
      reader_text: 'Saturn is exalted in the seventh house, a classically strong placement.',
      grade: 'primary',
      grounding_note: '',
      catalog_discrepancy_note: '',
    }
    const result = reviewEntry(broken, realSignal('SIG.MSR.001'))
    expect(result.passed).toBe(false)
    expect(
      result.flags.some((f) => f.source === 'citation_gate' && f.code === 'citation_gate_no_grounding_note'),
    ).toBe(true)
  })

  it('RED: fails when grounding_note is grounded in a DIFFERENT signal\'s source (copy-paste class error)', () => {
    const broken: ReaderTextEntry = {
      signal_id: 'SIG.MSR.001', // Sasha Mahapurusha, classical_basis references BPHS Ch.26/Phaladeepika Ch.6
      reader_text: 'Saturn is exalted in the seventh house, a classically strong placement.',
      grade: 'primary',
      // Wrong source entirely — belongs to a Krishnamurti-technique signal, not this one.
      grounding_note: 'Classical basis: "Krishnamurti Paddhati (H11 significators)"',
      catalog_discrepancy_note: '',
    }
    const result = reviewEntry(broken, realSignal('SIG.MSR.001'))
    expect(result.passed).toBe(false)
    expect(
      result.flags.some((f) => f.source === 'citation_gate' && f.code === 'citation_gate_grounding_mismatch'),
    ).toBe(true)
  })

  it('GREEN: every real authored entry passes the citation gate against its own catalog signal', () => {
    for (const entry of READER_TEXT_ENTRIES) {
      const result = reviewEntry(entry, signalsById.get(entry.signal_id) ?? null)
      const gateFlags = result.flags.filter((f) => f.source === 'citation_gate' && f.level === 'error')
      expect(gateFlags, `${entry.signal_id}: ${JSON.stringify(gateFlags)}`).toHaveLength(0)
    }
  })
})

describe('reviewEntry — full real batch', () => {
  it('every entry in entries.ts passes review end to end (register-leak + voice + citation gate)', () => {
    const failures: string[] = []
    for (const entry of READER_TEXT_ENTRIES) {
      const result = reviewEntry(entry, signalsById.get(entry.signal_id) ?? null)
      if (!result.passed) failures.push(`${entry.signal_id}: ${JSON.stringify(result.flags)}`)
    }
    expect(failures).toEqual([])
  })
})
