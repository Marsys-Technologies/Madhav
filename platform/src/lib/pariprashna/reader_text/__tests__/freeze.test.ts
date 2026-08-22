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
 *
 * That proof runs on an IN-MEMORY fixture, and adversarial review pointed out
 * what it therefore does not establish: nothing anywhere opened the two
 * COMMITTED files and checked one against the other. The recorded sha256 was a
 * number in a file with no code path that could read it false — §N.8 exactly.
 * The final describe block below is that missing detector: it reads
 * `frozen/msr_reader_text_v1.json` and `frozen/msr_reader_text_v1.freeze.json`
 * off disk and runs `verifyFreeze` on the real pair.
 */
import { describe, expect, it } from 'vitest'

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { buildFreezeRecord, buildFrozenArtifact, canonicalSerialize, computeArtifactHash, verifyFreeze } from '../freeze'
import type { FreezeRecord, FrozenArtifact, ReaderTextEntry, ReviewedEntry, RankedMsrEntry, MsrSignal } from '../types'

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

function fixtureAuthored(): Map<string, ReaderTextEntry> {
  return new Map(
    (
      [
        ['SIG.MSR.001', 'primary'],
        ['SIG.MSR.002', 'supporting'],
        ['SIG.MSR.003', 'primary'],
      ] as const
    ).map(([id, grade]) => [
      id,
      {
        signal_id: id,
        reader_text: 'fixture reader text',
        grade,
        grounding_note: `fixture grounding note for ${id}`,
        catalog_discrepancy_note: '',
      } as ReaderTextEntry,
    ]),
  )
}

function fixtureRanked(): RankedMsrEntry[] {
  return [
    { signal: fixtureSignal('SIG.MSR.001'), citation_weight: 10, matched_entities: ['PLN.SATURN'] },
    { signal: fixtureSignal('SIG.MSR.002'), citation_weight: 5, matched_entities: ['PLN.SATURN'] },
  ]
}

describe('freeze — buildFrozenArtifact + canonicalSerialize', () => {
  it('includes only passed entries, ranked and weighted from the real ranking input', () => {
    const artifact = buildFrozenArtifact(fixtureReviewed(), fixtureRanked(), fixtureAuthored(), 573)
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
    const artifact = buildFrozenArtifact(reviewed, fixtureRanked(), fixtureAuthored(), 573)
    expect(artifact.entries.map((e) => e.signal_id)).not.toContain('SIG.MSR.003')
  })
})

describe('freeze — verifyFreeze mutate-and-catch proof (§N.8)', () => {
  const artifact = buildFrozenArtifact(fixtureReviewed(), fixtureRanked(), fixtureAuthored(), 573)
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
    const artifact2 = buildFrozenArtifact(fixtureReviewed(), fixtureRanked(), fixtureAuthored(), 573)
    // generated_at differs by wall-clock time between the two builds, so hashes
    // legitimately differ unless we pin generated_at — confirm the CONTENT
    // (entries) hashes identically when generated_at is held fixed.
    const pinned1 = { ...artifact, generated_at: 'FIXED' }
    const pinned2 = { ...artifact2, generated_at: 'FIXED' }
    expect(computeArtifactHash(pinned1)).toBe(computeArtifactHash(pinned2))
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// The detector the lane was missing: the COMMITTED artifact vs the COMMITTED
// record. Everything above this line runs on fixtures.
// ─────────────────────────────────────────────────────────────────────────────
const FROZEN_DIR = path.join(__dirname, '..', 'frozen')
const COMMITTED_ARTIFACT_PATH = path.join(FROZEN_DIR, 'msr_reader_text_v1.json')
const COMMITTED_RECORD_PATH = path.join(FROZEN_DIR, 'msr_reader_text_v1.freeze.json')

/** `generate_and_freeze.ts` writes `canonicalSerialize(artifact) + '\n'` but
 *  hashes the string WITHOUT that trailing newline, so the on-disk bytes are
 *  the hashed payload plus exactly one '\n'. Stripping precisely one newline
 *  (not `.trim()`, which would also swallow real content whitespace and hide a
 *  whole class of tampering) reconstructs what was hashed. */
function readHashedPayload(): string {
  const raw = readFileSync(COMMITTED_ARTIFACT_PATH, 'utf8')
  return raw.endsWith('\n') ? raw.slice(0, -1) : raw
}

describe('freeze — the COMMITTED artifact against the COMMITTED record (§N.8)', () => {
  const record = JSON.parse(readFileSync(COMMITTED_RECORD_PATH, 'utf8')) as FreezeRecord

  it('GREEN: the committed artifact hashes to the committed sha256', () => {
    const result = verifyFreeze(readHashedPayload(), record)
    expect(
      result.intact,
      `committed artifact does not match its committed freeze record.\n` +
        `  recorded:   ${result.recorded_sha256}\n` +
        `  recomputed: ${result.recomputed_sha256}\n` +
        `  If this is an intentional re-freeze, re-run generate_and_freeze.ts ` +
        `(see its header for the exact command) and commit BOTH files.`,
    ).toBe(true)
  })

  it('RED: a one-byte mutation of the committed artifact is caught', () => {
    const payload = readHashedPayload()
    const idx = payload.indexOf('"reader_text"')
    expect(idx).toBeGreaterThan(-1)
    const tampered = payload.slice(0, idx + 2) + 'X' + payload.slice(idx + 3)
    expect(tampered).not.toBe(payload)
    expect(tampered.length).toBe(payload.length)

    const result = verifyFreeze(tampered, record)
    expect(result.intact).toBe(false)
    expect(result.recomputed_sha256).not.toBe(result.recorded_sha256)
  })

  it('the record\'s entry_count agrees with the committed artifact it describes', () => {
    const artifact = JSON.parse(readFileSync(COMMITTED_ARTIFACT_PATH, 'utf8')) as FrozenArtifact
    expect(record.entry_count).toBe(artifact.entries.length)
    expect(artifact.signals_covered).toBe(artifact.entries.length)
    expect(record.frozen_at).toBe(artifact.generated_at)
  })

  it('the disclosures are INSIDE the freeze: every committed entry carries its grounding_note', () => {
    // grounding_note and catalog_discrepancy_note used to sit outside
    // FrozenArtifactEntry, unhashed and free to drift from the text they
    // explain. Four entries' honest-omission disclosures depend on them.
    const artifact = JSON.parse(readFileSync(COMMITTED_ARTIFACT_PATH, 'utf8')) as FrozenArtifact
    for (const entry of artifact.entries) {
      expect(entry.grounding_note, `${entry.signal_id} grounding_note`).toBeTruthy()
      expect(typeof entry.catalog_discrepancy_note, `${entry.signal_id} discrepancy note`).toBe('string')
    }
    const withDiscrepancy = artifact.entries.filter((e) => e.catalog_discrepancy_note.length > 0)
    expect(withDiscrepancy.map((e) => e.signal_id).sort()).toEqual(
      ['SIG.MSR.031', 'SIG.MSR.121', 'SIG.MSR.157', 'SIG.MSR.313', 'SIG.MSR.327', 'SIG.MSR.415'].sort(),
    )
  })
})
