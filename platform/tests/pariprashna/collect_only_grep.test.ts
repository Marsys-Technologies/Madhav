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

  it('G5: the spine-bundle chain is inside the gate (the four files it previously omitted)', () => {
    // G5's finding: the most calibration-adjacent serving chain in the estate — the one
    // that assembles a `calibration` section into a served payload — was the one chain the
    // grep gate did not scan. Asserted by name so a silent removal fails loudly rather than
    // shrinking coverage back to where the finding started.
    for (const rel of [
      'src/lib/retrieval/spine/compute_spine_bundle.ts',
      'src/lib/retrieval/spine/materialize.ts',
      'src/lib/retrieval/registry/layers/register_spine_bundle.ts',
      'src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts',
    ]) {
      expect(SERVING_PATH_FILES, `G5 serving-path file dropped from the manifest: ${rel}`).toContain(rel)
    }
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

// ── G5 (SAMĀPTI §8.1 / BRIEF_PB-3.1 G5) ──────────────────────────────────────────
describe('COLLECT-ONLY gate (b) — G5: the bare `calibration` key', () => {
  it('THROWS on a bare `calibration` object — the exact shape compute_spine_bundle.ts emits', () => {
    // Verbatim section shape from compute_spine_bundle.ts's return value. Before G5
    // widened CALIBRATION_LEAK_KEYS, this payload passed the guard untouched: every
    // pattern required a SUFFIX (calibration_badge / _annotation / _adjustment / …)
    // and the one real calibration payload in the estate carries none.
    const spineBundleShaped = {
      chart_id: 'c1',
      domain: 'career',
      signals: [{ signal_id: 's1' }],
      calibration: {
        verdict_distribution: [],
        reliability: [],
        multipliers: [],
        qa_fail_count: 0,
      },
    }
    expect(() => assertNoCalibrationLeak(spineBundleShaped, 'spine-bundle')).toThrow(CalibrationLeakError)
    expect(findCalibrationLeaks(spineBundleShaped).map((v) => v.path)).toContain('calibration')
  })

  it('catches the bare key at ANY depth, not just the envelope root', () => {
    expect(() =>
      assertNoCalibrationLeak({ results: [{ bundle: { calibration: { brier: 0.1 } } }] }),
    ).toThrow(CalibrationLeakError)
  })

  it('is ANCHORED — does NOT false-positive on `calibration_context_only` (a descriptor flag, not a result)', () => {
    // F-R7's flag is metadata ABOUT a capability, never a calibration result. A
    // substring match would have swept it up and made the guard unusable anywhere a
    // capability descriptor is echoed.
    expect(() => assertNoCalibrationLeak({ capability: { calibration_context_only: true } })).not.toThrow()
  })

  it('does NOT false-positive on other calibration-adjacent NON-result key names', () => {
    expect(() =>
      assertNoCalibrationLeak({ meta: { calibration_park_reason: 'parked', uncalibrated: true } }),
    ).not.toThrow()
  })
})

describe('COLLECT-ONLY gate (b) — G5: the guard has REAL production call sites', () => {
  // G5's finding was that `assertNoCalibrationLeak` had ZERO production call sites, so
  // "collect-only is enforced at runtime" described a function nobody called. This is the
  // detector for that claim: it fails if the wiring is ever removed, which is exactly the
  // regression that produced the finding. Bound: it asserts the call sites EXIST in the
  // named serving files; the behavioural proof that they fire is the mutation test the
  // verifier runs against the deployed route.
  const PRODUCTION_CALL_SITES: readonly string[] = [
    // Every Paripraśna reading-stream event crosses PariprashnaEmitter.write().
    'src/lib/pariprashna/protocol/emitter.ts',
    // The MCP reading envelope.
    'src/app/api/mcp/prashna_ask/route.ts',
  ]

  it.each(PRODUCTION_CALL_SITES)('%s calls assertNoCalibrationLeak', (rel) => {
    const abs = resolve(PLATFORM_ROOT, rel)
    expect(existsSync(abs), `production call site file missing: ${rel}`).toBe(true)
    const source = readFileSync(abs, 'utf8')
    // Must both import it and call it — an orphan import is not a call site.
    expect(source, `${rel} does not import assertNoCalibrationLeak`).toMatch(
      /import\s*\{[^}]*assertNoCalibrationLeak[^}]*\}/,
    )
    const callLines = source
      .split('\n')
      .filter((l) => !/^\s*(\/\/|\*\/?|\/\*)/.test(l))
      .filter((l) => /\bassertNoCalibrationLeak\s*\(/.test(l))
    expect(callLines.length, `${rel} imports the guard but never calls it`).toBeGreaterThan(0)
  })

  it('the byte-identity harness call site still exists (pre-existing, not replaced)', () => {
    const source = readFileSync(resolve(PLATFORM_ROOT, 'src/lib/pariprashna/no_leakage/byte_identity_probe.ts'), 'utf8')
    expect(source).toMatch(/\bassertNoCalibrationLeak\s*\(/)
  })
})
