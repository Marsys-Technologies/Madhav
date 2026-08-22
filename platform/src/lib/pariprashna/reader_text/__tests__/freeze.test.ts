/**
 * freeze.test.ts — lane P4-J, §N.8 red-then-green proof for the freeze step.
 *
 * "the freeze step's integrity claim needs a detector — show that a
 * tampered frozen artifact is caught by the hash check (mutate one byte,
 * observe the check fail, capture it verbatim)." This file is that proof:
 * build a small artifact, freeze it, mutate exactly one byte of its
 * serialized form, and show `verifyFreeze` reports `intact: false` with a
 * mismatched hash (RED) — then show the untampered serialization verifies
 * clean (GREEN).
 */
import { describe, expect, it } from 'vitest'

import { buildFreezeRecord, buildFrozenArtifact, canonicalSerialize, computeArtifactHash, verifyFreeze } from '../freeze'
import type { ReviewedEntry, RankedMsrEntry, MsrSignal } from '../types'

function fixtureSignal(id: string): MsrSignal {
  return {
    signal_id: id,
    native_id: 'abhisek_mohanty',
    domain: 'career',
    planet: 'SATURN',
    house: 7,
    nakshatra: null,
    dasha_lord: null,
    confidence: 0.95,
    significance: 0.9,
    is_forward_looking: false,
    claim_text: 'Fixture signal',
    classical_basis: 'BPHS Ch.26',
    falsifier: null,
    source_file: 'MSR_v5_0.md',
    source_version: '5.0',
    ingested_at: new Date().toISOString(),
  }
}

function fixtureReviewed(): ReviewedEntry[] {
  return [
    { signal_id: 'SIG.MSR.001', clean_text: 'Saturn is exalted in the seventh house.', passed: true, flags: [] },
    { signal_id: 'SIG.MSR.002', clean_text: 'A second fixture reading.', passed: true, flags: [] },
  ]
}

function fixtureRanked(): RankedMsrEntry[] {
  return [
    { signal: fixtureSignal('SIG.MSR.001'), citation_weight: 10, matched_entities: ['PLN.SATURN'] },
    { signal: fixtureSignal('SIG.MSR.002'), citation_weight: 5, matched_entities: ['PLN.SATURN'] },
  ]
}

describe('freeze — buildFrozenArtifact + canonicalSerialize', () => {
  it('includes only passed entries, ranked and weighted from the real ranking input', () => {
    const gradeById = new Map<string, 'primary' | 'supporting'>([
      ['SIG.MSR.001', 'primary'],
      ['SIG.MSR.002', 'supporting'],
    ])
    const artifact = buildFrozenArtifact(fixtureReviewed(), fixtureRanked(), gradeById, 573)
    expect(artifact.signals_covered).toBe(2)
    expect(artifact.entries[0].signal_id).toBe('SIG.MSR.001')
    expect(artifact.entries[0].rank).toBe(1)
    expect(artifact.entries[0].citation_weight).toBe(10)
    expect(artifact.entries[1].grade).toBe('supporting')
  })

  it('excludes failed-review entries from the frozen artifact entirely', () => {
    const reviewed: ReviewedEntry[] = [
      ...fixtureReviewed(),
      { signal_id: 'SIG.MSR.003', clean_text: 'should not appear', passed: false, flags: [] },
    ]
    const gradeById = new Map<string, 'primary' | 'supporting'>([
      ['SIG.MSR.001', 'primary'],
      ['SIG.MSR.002', 'primary'],
      ['SIG.MSR.003', 'primary'],
    ])
    const artifact = buildFrozenArtifact(reviewed, fixtureRanked(), gradeById, 573)
    expect(artifact.entries.map((e) => e.signal_id)).not.toContain('SIG.MSR.003')
  })
})

describe('freeze — verifyFreeze mutate-and-catch proof (§N.8)', () => {
  const gradeById = new Map<string, 'primary' | 'supporting'>([
    ['SIG.MSR.001', 'primary'],
    ['SIG.MSR.002', 'supporting'],
  ])
  const artifact = buildFrozenArtifact(fixtureReviewed(), fixtureRanked(), gradeById, 573)
  const serialized = canonicalSerialize(artifact)
  const record = buildFreezeRecord(artifact, 'fixture/path.json')

  it('GREEN: the untampered serialization verifies intact against its own recorded hash', () => {
    const result = verifyFreeze(serialized, record)
    expect(result.intact).toBe(true)
    expect(result.recomputed_sha256).toBe(record.sha256)
  })

  it('RED: mutating exactly one byte of the serialized artifact is caught by the hash check', () => {
    // Flip one character deep inside the reader_text of the first entry.
    const idx = serialized.indexOf('Saturn is exalted')
    expect(idx).toBeGreaterThan(-1)
    const tampered = serialized.slice(0, idx) + 'X' + serialized.slice(idx + 1)
    expect(tampered).not.toBe(serialized)
    expect(tampered.length).toBe(serialized.length) // one-byte substitution, not insertion

    const result = verifyFreeze(tampered, record)

    // Verbatim capture of the RED result, per the charter's "capture it verbatim" ask:
    expect(result.intact).toBe(false)
    expect(result.recomputed_sha256).not.toBe(result.recorded_sha256)
    expect(result.recorded_sha256).toBe(record.sha256)
  })

  it('sanity: computeArtifactHash is a pure, deterministic function of the artifact content', () => {
    const gradeById2 = new Map<string, 'primary' | 'supporting'>([
      ['SIG.MSR.001', 'primary'],
      ['SIG.MSR.002', 'supporting'],
    ])
    const artifact2 = buildFrozenArtifact(fixtureReviewed(), fixtureRanked(), gradeById2, 573)
    // generated_at differs by wall-clock time between the two builds, so hashes
    // legitimately differ unless we pin generated_at — confirm the CONTENT
    // (entries) hashes identically when generated_at is held fixed.
    const pinned1 = { ...artifact, generated_at: 'FIXED' }
    const pinned2 = { ...artifact2, generated_at: 'FIXED' }
    expect(computeArtifactHash(pinned1)).toBe(computeArtifactHash(pinned2))
  })
})
