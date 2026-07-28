/**
 * collect_only_grep.test.ts — PB-3 lane L-6 COLLECT-ONLY gate (§14.6 C1 / W-3),
 * BRIEF_PB-3 §G item 11 [integrity]: "collect-only: no code path from calibration
 * write to priors bump or serving annotation."
 *
 * Two halves, per the brief's "grep test + runtime assertion, not config":
 *
 *   (a) GREP GATE — scans every real serving-path source file and asserts NONE
 *       contains a calibration-write / priors-bump / serving-annotation code
 *       line. Demonstrated-can-fail: `scannerSelfProof` proves the detector both
 *       flags a real violation AND does not false-positive on an honest read or a
 *       documenting comment. A live red-then-green scratch cycle (a temporary
 *       violating line injected into a scratch copy) is recorded in REPORT_PB-3.
 *
 *   (b) RUNTIME ASSERTION — `assertNoCalibrationLeak` throws if a served payload
 *       carries calibration-derived fields. Proven can-fail here (clean payload
 *       passes; tainted payload throws).
 *
 * Anti-false-confidence (FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE): the gate
 * asserts each listed serving file physically resolves, so a rename that dropped
 * a file from coverage fails loudly rather than passing vacuously.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

import {
  SERVING_PATH_FILES,
  FORBIDDEN_PATTERNS,
  scanForForbidden,
  scannerSelfProof,
} from '@/lib/pariprashna/no_leakage/serving_path_manifest'
import {
  assertNoCalibrationLeak,
  findCalibrationLeaks,
  CalibrationLeakError,
} from '@/lib/pariprashna/no_leakage/calibration_leak_guard'

// platform/ package root, resolved from this test file's location
// (platform/tests/pariprashna/collect_only_grep.test.ts → up two dirs).
const PLATFORM_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

describe('COLLECT-ONLY gate (a) — grep over the real serving path', () => {
  it('every declared serving-path file physically exists (no vacuous coverage)', () => {
    for (const rel of SERVING_PATH_FILES) {
      const abs = resolve(PLATFORM_ROOT, rel)
      expect(existsSync(abs), `serving-path file missing: ${rel}`).toBe(true)
    }
  })

  it.each(SERVING_PATH_FILES)(
    'serving file has ZERO calibration-write / priors-bump / annotation code lines: %s',
    (rel) => {
      const source = readFileSync(resolve(PLATFORM_ROOT, rel), 'utf8')
      const hits = scanForForbidden(source)
      const report = hits.map((h) => `  ${rel}:${h.line} [${h.patternId}] ${h.excerpt}\n    → ${h.reason}`).join('\n')
      expect(hits, `COLLECT-ONLY violation(s) in ${rel}:\n${report}`).toEqual([])
    },
  )
})

describe('COLLECT-ONLY gate (a) — detector is demonstrated-can-fail', () => {
  const proof = scannerSelfProof()

  it('does NOT flag an honest priors_version READ (no false positive)', () => {
    expect(scanForForbidden(proof.readOnlyFixture)).toEqual([])
  })

  it('does NOT flag a comment that documents record_outcome() (comment-line skip)', () => {
    expect(scanForForbidden(proof.commentFixture)).toEqual([])
  })

  it('DOES flag a real priors_version bump', () => {
    const hits = scanForForbidden(proof.bumpFixture)
    expect(hits.map((h) => h.patternId)).toContain('priors-version-bump')
  })

  it('DOES flag a real mimamsa_calibration write', () => {
    const hits = scanForForbidden(proof.writeFixture)
    expect(hits.map((h) => h.patternId)).toContain('calibration-sql-write')
  })

  it('DOES flag a real serving-envelope calibration annotation', () => {
    const hits = scanForForbidden(proof.annotationFixture)
    expect(hits.map((h) => h.patternId)).toContain('serving-envelope-calibration-annotation')
  })

  it('has a non-empty forbidden-pattern set (guards against an emptied gate)', () => {
    expect(FORBIDDEN_PATTERNS.length).toBeGreaterThanOrEqual(5)
  })
})

describe('COLLECT-ONLY gate (b) — runtime assertion', () => {
  it('passes a clean served envelope (no calibration fields)', () => {
    const envelope = {
      verdict: { grade: 'B', bearing_yogas: [{ id: 'y1' }] },
      grounding: { facts: ['f1', 'f2'] },
      provenance: { build_id: 'b1', priors_version: 'v3', now_context_date: '2026-07-28' },
    }
    expect(() => assertNoCalibrationLeak(envelope, 'clean-envelope')).not.toThrow()
  })

  it('THROWS on an envelope carrying a Brier / calibration-derived field', () => {
    const tainted = {
      verdict: { grade: 'B' },
      calibration_badge: { brier_score: 0.12, priors_bumped: true },
    }
    expect(() => assertNoCalibrationLeak(tainted, 'tainted-envelope')).toThrow(CalibrationLeakError)
    const violations = findCalibrationLeaks(tainted)
    expect(violations.map((v) => v.path)).toEqual(
      expect.arrayContaining(['calibration_badge', 'calibration_badge.brier_score', 'calibration_badge.priors_bumped']),
    )
  })

  it('does NOT treat a plain priors_version audit field as a leak (matches the grep exemption)', () => {
    // Byte-identity harness runs this guard on every capture; a served envelope
    // MAY carry the D-16 provenance stamp's priors_version (audit metadata) —
    // that is not a calibration RESULT and must not trip the guard.
    expect(() => assertNoCalibrationLeak({ provenance: { priors_version: 'v3' } })).not.toThrow()
  })
})
